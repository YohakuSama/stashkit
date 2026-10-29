"""Pinned, offline replacement for GeoSite private, including single-label names."""
import hashlib
import json
from pathlib import Path

from rule_sources import valid_domain

ROOT = Path(__file__).resolve().parents[1]
NAME = "Private-local"
SOURCE_SINGLE_LABEL = r"^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
# DNS labels are limited to 63 bytes by the protocol; use a linear, comma-free
# form for valid single-label DNS names inside a Stash classical row.
SINGLE_LABEL = r"^[a-z]([a-z0-9-]*[a-z0-9])?$"


def private_provider(root=ROOT):
    lock = json.loads((root / "build/private-domains-lock.json").read_text())
    if lock["schema_version"] != 1 or lock["repository"] != "v2fly/domain-list-community":
        raise ValueError("Unexpected private-domain source")
    for path_key, hash_key in (("source_path", "source_sha256"), ("license_path", "license_sha256")):
        path = (root / lock[path_key]).resolve()
        if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != lock[hash_key]:
            raise ValueError("Private-domain source or license SHA mismatch")
    payload = []
    for raw in (root / lock["source_path"]).read_text().splitlines():
        row = raw.strip()
        if not row or row.startswith("#"):
            continue
        if row.startswith("regexp:"):
            if row != "regexp:" + SOURCE_SINGLE_LABEL:
                raise ValueError("Unreviewed private-domain regular expression")
            payload.append("DOMAIN-REGEX," + SINGLE_LABEL)
            continue
        kind, value = ("DOMAIN", row[5:]) if row.startswith("full:") else ("DOMAIN-SUFFIX", row)
        valid_domain(value)
        payload.append(kind + "," + value)
    if len(payload) != lock["rule_count"] or len(payload) != len(set(payload)):
        raise ValueError("Private-domain count or duplicates changed")
    return {"type": "inline", "behavior": "classical", "payload": payload}
