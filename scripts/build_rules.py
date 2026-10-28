#!/usr/bin/env python3
"""Render pinned inputs; validate everything before replacing any output file."""
import argparse
import os
import tempfile
from pathlib import Path

from rule_sources import KIT, ROOT, expected_assets


def build(kit=KIT, source_root=ROOT, check=False):
    assets = expected_assets(source_root, kit)
    outdir = kit / "rules"
    existing = {path.name for path in outdir.glob("*.txt")}
    obsolete = existing - set(assets)
    if obsolete:
        raise ValueError(f"Obsolete assets require manual review: {sorted(obsolete)}")
    changed = [name for name, content in assets.items()
               if not (outdir / name).is_file() or (outdir / name).read_bytes() != content]
    if check:
        if changed:
            raise ValueError(f"Rebuild differs from committed assets: {changed}")
        return len(assets), 0
    # Hash/count/schema checks and obsolete-file detection finish before writes.
    # Stage every changed file first, then replace each target atomically.
    outdir.mkdir(parents=True, exist_ok=True)
    staged = []
    try:
        for name in changed:
            with tempfile.NamedTemporaryFile(dir=outdir, prefix=".stashkit-", delete=False) as handle:
                temporary = Path(handle.name)
                staged.append((temporary, outdir / name))
                handle.write(assets[name])
            temporary.chmod(0o644)
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return len(assets), len(changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify exact output bytes without writing")
    args = parser.parse_args()
    count, changed = build(check=args.check)
    if args.check:
        print(f"PASS: all {count} assets reproduce byte-for-byte from pinned inputs and reviewed adjustments")
    else:
        print(f"Generated {count} Stash-native rule sets; {changed} files changed")


if __name__ == "__main__":
    main()
