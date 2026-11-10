"""Fail closed: every tracked file is either part of the current edition or a content-free notice.

The current edition is defined by plan/data/manifest.json (written by plan/model/build_site.py).
Anything else that is tracked must be byte-identical to the withdrawal notice for its file type,
so that neither GitHub's branch build nor the Actions artifact can serve an older figure.

    python scripts/privacy_boundary.py            # check
    python scripts/privacy_boundary.py --retire PATH [PATH ...]   # turn files into notices
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "PUBLICATION_WITHDRAWN"
INFRA = {".gitignore", "COORDINATION.md", "README.md", ".github/workflows/pages.yml",
         ".github/workflows/verify.yml", "scripts/package_site.py", "scripts/verify.py",
         "scripts/privacy_boundary.py"}


def tracked() -> list[str]:
    return subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()


def approved() -> set[str]:
    manifest = json.loads((ROOT / "plan" / "data" / "manifest.json").read_text(encoding="utf-8"))
    return set(manifest["published"]) | INFRA


def notice(name: str) -> str:
    path = Path(name)
    if path.suffix == ".html":
        home = "../" * (len(path.parts) - 1) + "index.html"
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<meta name="robots" content="noindex"><title>Publication withdrawn</title></head>'
                '<body><main><h1>Earlier publication withdrawn</h1>'
                '<p>Unverified financial content was withdrawn for privacy and evidence review.</p>'
                f'<p><a href="{home}">Open the reviewed planning dashboard</a></p>'
                f'<p>{MARKER}</p></main></body></html>\n')
    if path.suffix == ".json":
        return '{"status":"' + MARKER + '"}\n'
    if path.suffix == ".csv":
        return "status\n" + MARKER + "\n"
    if path.suffix == ".py":
        return f'"""{MARKER}: legacy generator disabled to prevent republication."""\n'
    if path.suffix in (".js", ".css"):
        return f"/* {MARKER}: earlier content removed. */\n"
    return f"# {MARKER}\n\nEarlier content withdrawn for privacy and evidence review.\n"


def verify() -> None:
    ok = approved()
    bad = [n for n in tracked()
           if n not in ok and not n.startswith("plan/")
           and (ROOT / n).read_text(encoding="utf-8", errors="replace") != notice(n)]
    if bad:
        raise SystemExit("Tracked files that are neither current nor withdrawal notices:\n  " + "\n  ".join(bad))
    print("PASS: every tracked file is part of the current edition or a content-free notice.")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--retire":
        for name in sys.argv[2:]:
            (ROOT / name).write_text(notice(name), encoding="utf-8")
            print("retired", name)
    else:
        verify()
