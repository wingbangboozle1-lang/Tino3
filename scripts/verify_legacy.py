"""Fail closed for the repository-root GitHub Pages/Jekyll publishing path.

GitHub Pages can still be configured to build the main-branch root independently of
our allowlisted Actions artifact. The source guard checks every tracked path; CI also
runs the real GitHub Jekyll action and checks its output. Neither check sanitizes the
repository itself or removes sensitive material from Git history and external copies.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import build
import package_site as pack
import privacy_boundary

ROOT = Path(__file__).resolve().parents[1]
# Exact, deliberately narrow exclusions. Adding a tracked, non-public path without
# adding an exclusion is an error instead of silently making it publicly accessible.
EXCLUDED = (
    "analysis", "plan", "scripts", "assets/data", "assets/privacy.json", "assets/sources.json",
    "COORDINATION.md", "EXECUTIVE_SUMMARY.md", "README.md",
)
CONFIG = (
    "# Safety boundary for GitHub Pages when its source is the repository root.\n"
    "# The Actions artifact uses a separate allowlist; this excludes all other tracked material\n"
    "# from the legacy Jekyll publisher until the repository setting can be changed.\n"
    "theme: null\n"
    "exclude:\n" + "".join(f"  - {entry}\n" for entry in EXCLUDED)
)
PUBLIC_FILES = set(build.PAGES + build.ASSETS)


def excluded_from_legacy(name: str) -> bool:
    parts = Path(name).parts
    # Jekyll's documented default: files/dirs starting with underscore, dot or hash,
    # or ending in tilde, are not rendered. The config guard forbids include overrides.
    if any(part.startswith(("_", ".", "#")) or part.endswith("~") for part in parts):
        return True
    return any(name == entry or name.startswith(entry + "/") for entry in EXCLUDED)


def check_source() -> None:
    if (ROOT / ".nojekyll").exists():
        raise SystemExit("Unsafe legacy source: .nojekyll disables Jekyll exclusions")
    if (ROOT / "_config.yml").read_text(encoding="utf-8") != CONFIG:
        raise SystemExit("Unsafe or unexpected Jekyll configuration; review and update the guard")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    unexpected = sorted(name for name in tracked
                        if name and name not in PUBLIC_FILES and not excluded_from_legacy(name))
    if unexpected:
        raise SystemExit(f"Tracked paths would bypass the legacy site allowlist: {unexpected}")
    missing = sorted(name for name in PUBLIC_FILES
                     if not (ROOT / name).exists())
    if missing:
        raise SystemExit(f"Public pages or assets are missing from the working tree: {missing}")
    print(f"PASS: legacy Jekyll source is guarded; {len(PUBLIC_FILES)} public files allowed.")


def check_output(destination: Path) -> None:
    from verify import OFFICIAL_HOSTS, PageAudit  # late import: verify.py also runs the artifact build

    if not destination.is_dir():
        raise SystemExit(f"Legacy site directory does not exist: {destination}")
    links = [path for path in destination.rglob("*") if path.is_symlink()]
    if links:
        raise SystemExit("Legacy site contains symlinks")
    files = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()}
    unexpected, missing = sorted(files - PUBLIC_FILES), sorted(PUBLIC_FILES - files)
    if unexpected or missing:
        raise SystemExit(f"Legacy output boundary failed: unexpected={unexpected}, missing={missing}")

    failures: list[str] = []
    for name in sorted(files):
        path = destination / name
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            failures.append(f"{name}: cannot read public file as UTF-8")
            continue
        failures.extend(privacy_boundary.check_identifiers(text, name))
        failures.extend(privacy_boundary.check_identifiers(name, f"path {name}"))
        failures.extend(privacy_boundary.check_money(text, name))
        if name.endswith(".html"):
            if privacy_boundary.FORBIDDEN_ELEMENTS.search(text):
                failures.append(f"{name}: interactive or remote-code element")
            audit = PageAudit(path)
            audit.feed(text)
            failures.extend(f"{name}: {error}" for error in audit.errors)
            for row in audit.rows:
                if not any(h.startswith("https://") for h in row["hrefs"]) \
                        and "review.html#register" not in row["hrefs"]:
                    failures.append(f"{name}: a table row has no source link")
            for _tag, href in audit.links:
                if href.startswith("https://"):
                    from urllib.parse import urlsplit
                    host = urlsplit(href).netloc
                    if host not in OFFICIAL_HOSTS:
                        failures.append(f"{name}: external host not approved: {host}")
    if failures:
        raise SystemExit("Legacy output verification failed:\n  - " + "\n  - ".join(dict.fromkeys(failures)))
    print(f"PASS: actual legacy build contains only {len(files)} audited public pages/assets.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-only", action="store_true",
                        help="check source configuration and tracked paths only")
    parser.add_argument("--site", default="_legacy_site",
                        help="actual Jekyll output directory to audit")
    args = parser.parse_args()
    check_source()
    if not args.config_only:
        check_output((ROOT / args.site).resolve())


if __name__ == "__main__":
    main()
