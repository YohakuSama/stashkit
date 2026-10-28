"""Pinned input validation and deterministic Stash rule rendering."""
import hashlib
import ipaddress
import json
import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT / "upstream" / "loonkit"
SUPPORTED = {"DOMAIN", "DOMAIN-SUFFIX", "IP-CIDR", "IP-CIDR6", "IP-ASN"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_domain(value):
    require(isinstance(value, str) and 0 < len(value) <= 253, f"Invalid domain length: {value}")
    require(all(label and len(label) <= 63 and re.fullmatch(r"[A-Za-z0-9_-]+", label)
                for label in value.split(".")), f"Invalid domain: {value}")


def lines_from(path):
    return [row.strip() for row in path.read_text(encoding="utf-8").splitlines()
            if row.strip() and not row.lstrip().startswith("#")]


def generate_source_sets(path):
    buckets = {"domain": [], "ipcidr": [], "asn": []}
    raw = lines_from(path)
    require(len(raw) == len(set(raw)), f"Duplicated LoonKit source entries: {path}")
    for row in raw:
        pieces = row.split(",")
        require(len(pieces) >= 2 and pieces[0] in SUPPORTED, f"Unsupported source rule: {path}: {row}")
        kind, value, *opts = pieces
        if kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
            require(not opts, f"Unexpected domain options: {row}")
            valid_domain(value)
            buckets["domain"].append(value if kind == "DOMAIN" else "+." + value)
        elif kind in {"IP-CIDR", "IP-CIDR6"}:
            require(opts == ["no-resolve"], f"Missing no-resolve: {row}")
            network = ipaddress.ip_network(value, strict=False)
            require(network.version == (4 if kind == "IP-CIDR" else 6), f"Wrong address family: {row}")
            buckets["ipcidr"].append(value)
        else:
            require(opts == ["no-resolve"] and value.isdigit(), f"Invalid ASN rule: {row}")
            buckets["asn"].append(row)
    return buckets, len(raw)


def load_source_lock(kit=KIT):
    lock = json.loads((kit / "build/source-lock.json").read_text(encoding="utf-8"))
    require(lock["schema_version"] == 1, "Unknown source lock schema")
    require(lock["repository"] == "YohakuSama/loonkit", "Unexpected source repository")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", lock["commit"])), "Invalid source commit")
    for key in ("manifest_sha256", "profile_sha256"):
        require(bool(re.fullmatch(r"[0-9a-f]{64}", lock[key])), f"Invalid {key}")
    return lock


def checked_path(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"Source path escapes checkout: {relative}")
    require(path.is_file(), f"Missing source file: {relative}")
    return path


def load_baseline(source_root=ROOT, kit=KIT):
    """Validate the manifest, profile and *all* source hashes before rendering."""
    lock = load_source_lock(kit)
    frozen = (kit / "build/release_manifest.json").read_bytes()
    require(hashlib.sha256(frozen).hexdigest() == lock["manifest_sha256"], "Frozen manifest SHA mismatch")
    upstream = (source_root / "build/release_manifest.json").read_bytes()
    require(upstream == frozen, "Upstream manifest differs from the pinned snapshot")
    manifest = json.loads(frozen)
    profile = (source_root / "LoonKit.lcf").read_bytes()
    require(hashlib.sha256(profile).hexdigest() == lock["profile_sha256"], "Source profile SHA mismatch")
    require(manifest["profile_sha256"]["LoonKit.lcf"] == lock["profile_sha256"], "Manifest profile SHA mismatch")
    resources = manifest["runtime_resources"]
    require(len(resources) == manifest["remote_subscription_count"], "Source subscription count mismatch")
    require(len({item["path"] for item in resources}) == len(resources), "Duplicate source paths")
    for item in resources:
        source = checked_path(source_root, item["path"])
        require(hashlib.sha256(source.read_bytes()).hexdigest() == item["sha256"],
                f"Source SHA mismatch: {item['path']}")
    return manifest, profile.decode("utf-8")


def load_adjustments(kit=KIT):
    data = json.loads((kit / "build/adjustments.json").read_text(encoding="utf-8"))
    require(data["schema_version"] == 1, "Unknown adjustment schema")
    require(data["source_commit"] == load_source_lock(kit)["commit"], "Adjustment source commit mismatch")
    changes = data["changes"]
    require(len({(c["source"], c["behavior"]) for c in changes}) == len(changes), "Duplicate adjustments")
    return data


def apply_adjustments(base, buckets, adjustments):
    for change in adjustments["changes"]:
        if change["source"] != base:
            continue
        require(change["behavior"] == "domain", "Only reviewed domain adjustments are supported")
        require(bool(change["reason"].strip()), "Adjustments need a reason")
        values = buckets["domain"]
        for value in change["remove"]:
            require(value in values, f"{base}: missing removal {value}")
            values.remove(value)
        for value in change["add"]:
            valid_domain(value[2:] if value.startswith("+.") else value)
            require(value not in values, f"{base}: duplicated addition {value}")
            values.append(value)
    return buckets


def render_asset(base, kind, values, label):
    return (f"# StashKit {base} {kind} from LoonKit {label}\n" + "\n".join(values) + "\n").encode("utf-8")


def expected_assets(source_root=ROOT, kit=KIT):
    manifest, _ = load_baseline(source_root, kit)
    adjustments = load_adjustments(kit)
    resources = manifest["runtime_resources"]
    bases = {Path(item["path"]).stem for item in resources}
    require({change["source"] for change in adjustments["changes"]} <= bases, "Unknown adjustment source")
    assets, source_count, generated_count = {}, 0, 0
    for item in resources:
        source = checked_path(source_root, item["path"])
        buckets, count = generate_source_sets(source)
        require(count == item["matcher_count"], f"Source count mismatch: {source}")
        source_count += count
        apply_adjustments(source.stem, buckets, adjustments)
        for kind, values in buckets.items():
            if not values:
                continue
            filename = f"{source.stem}.{kind}.txt"
            require(filename not in assets, f"Colliding source stems: {filename}")
            require(len(values) == len(set(values)), f"Duplicate generated entries: {filename}")
            assets[filename] = render_asset(source.stem, kind, values, manifest["label"])
            generated_count += len(values)
    require(source_count == manifest["remote_rule_count"], "Total source rule count mismatch")
    require(generated_count == adjustments["expected_generated_rule_count"], "Total generated rule count mismatch")
    return assets
