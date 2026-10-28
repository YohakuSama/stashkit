#!/usr/bin/env python3
"""Generate a reproducible Stash local-resource bundle, avoiding first-run Raw downloads.

An offline ZIP is not a one-tap Stash import: rules files must be copied into
the Stash-managed provider resource directory (see official rule-set docs).
"""
import argparse
import hashlib
import io
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL_LINE = re.compile(r"^    url: https://raw\.githubusercontent\.com/YohakuSama/stashkit/[0-9a-f]{40}/rules/[A-Za-z0-9_.-]+\.txt\n", re.M)
INTERVAL_LINE = re.compile(r"^    interval: 86400\n", re.M)


def local_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = re.sub(r"^# StashKit v0\.1\.3.*$", "# StashKit v0.1.3 — LOCAL/OFFLINE rule providers: place rules/ in Stash managed resource directory", content, count=1, flags=re.M)
    content, urls = URL_LINE.subn("", content)
    content, intervals = INTERVAL_LINE.subn("", content)
    if (urls, intervals) != (54, 54):
        raise ValueError(f"Expected 54 URL/interval replacements, got {urls}/{intervals}")
    if len(re.findall(r"^    path: \./rules/[\w.-]+\.txt$", content, re.M)) != 54:
        raise ValueError("Expected 54 local rule provider paths")
    return content


def make_zip(root=ROOT):
    profile = local_profile((root / "StashKit.yaml").read_text(encoding="utf-8")).encode("utf-8")
    committed = (root / "StashKit-Local.yaml").read_bytes()
    if profile != committed:
        raise ValueError("StashKit-Local.yaml is out of sync with main profile")
    assets = sorted((root / "rules").glob("*.txt"))
    if len(assets) != 54:
        raise ValueError(f"Expected 54 rule assets, got {len(assets)}")
    files = {"StashKit-Local.yaml": profile}
    for path in assets:
        files["rules/v0.1.3/" + path.name] = path.read_bytes()
    manifest = "\n".join(hashlib.sha256(data).hexdigest() + "  " + name
                         for name, data in sorted(files.items())) + "\n"
    files["SHA256SUMS.txt"] = manifest.encode()
    files["README-OFFLINE.txt"] = (
        "StashKit v0.1.3 — offline provider bundle\n"
        "1) StashKit-Local.yaml uses 54 path-only rule-providers.\n"
        "2) Copy rules/v0.1.3/*.txt into the Stash-managed versioned resource directory.\n"
        "3) Import StashKit-Local.yaml locally and apply your own proxy provider.\n"
        "4) Stash does NOT automatically install provider paths when importing a ZIP.\n"
        "5) Confirm all 54 rules load; otherwise do not use this as an active profile.\n"
        "6) StashKit.yaml is the online profile with immutable pinned URLs and cache.\n"
    ).encode("utf-8")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist/StashKit-v0.1.3-offline.zip")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = make_zip()
    if args.check:
        assert result == make_zip(), "Offline zip creation is not deterministic"
        print("PASS: offline resource bundle reproducible with all 54 assets")
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        print(f"PASS: generated {output}, {len(result):,} bytes, 54 local providers")


if __name__ == "__main__":
    main()
