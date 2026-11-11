"""Ensure no formerly published, tracked file can be served with owner-specific data."""
from pathlib import Path
import importlib.util
import subprocess

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("package_site", Path(__file__).with_name("package_site.py"))
_pkg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pkg)

DOCS = {"COORDINATION.md", "README.md", "EXECUTIVE_SUMMARY.md", ".gitignore", ".nojekyll",
        ".github/workflows/pages.yml", ".github/workflows/verify.yml",
        "scripts/build.py", "scripts/model.py", "scripts/package_site.py",
        "scripts/privacy_boundary.py", "scripts/verify.py"}
# build.py and model.py are withdrawal notices rather than executable exceptions; never allow
# their previous contents back into the public branch.
DOCS.difference_update({"scripts/build.py", "scripts/model.py"})


def verify() -> None:
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    approved = set(_pkg.PAGES + _pkg.ASSETS) | DOCS
    for name in paths:
        if name in approved or name.startswith("public_site/"):
            continue
        content = (ROOT / name).read_text(encoding="utf-8")
        expected = _pkg.notice(name)
        if content != expected:
            raise AssertionError(f"Unapproved content at retired path {name}")
    print("PASS: every tracked legacy file is a content-free withdrawal notice.")


if __name__ == "__main__":
    verify()
