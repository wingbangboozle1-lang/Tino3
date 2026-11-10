"""Build the Pages artifact in _site/.

Publication is an allowlist. Only the files named in plan/data/manifest.json are copied; every path
an earlier edition published is answered with a content-free notice. The repository root holds the
same files, so GitHub's branch build and this artifact serve identical pages.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
sys.path.insert(0, str(ROOT / "scripts"))
from privacy_boundary import notice  # noqa: E402


def main() -> None:
    manifest = json.loads((ROOT / "plan" / "data" / "manifest.json").read_text(encoding="utf-8"))
    if SITE.exists():
        shutil.rmtree(SITE)
    for name in manifest["published"]:
        src = ROOT / name
        if not src.exists():
            raise SystemExit(f"published file missing: {name}")
        dest = SITE / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    notices = 0
    for name in manifest["retired"]:
        dest = SITE / name
        if dest.exists():
            raise SystemExit(f"retired path is also published: {name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(notice(name), encoding="utf-8")
        notices += 1
    allowed = set(manifest["published"]) | set(manifest["retired"])
    extra = [str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file() and str(p.relative_to(SITE)) not in allowed]
    if extra:
        raise SystemExit(f"unexpected files in artifact: {extra}")
    print(f"Packaged {len(manifest['published'])} current files and {notices} withdrawal notices.")


if __name__ == "__main__":
    main()
