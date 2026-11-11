#!/usr/bin/env python3
"""Fail-closed GitHub Pages artifact: allowlisted evidence edition + retired-path notices.

The Pages setting must use build_type=workflow, not legacy main-branch publishing. Legacy
publishing could expose checked-in code and drafts even when the artifact is clean.
"""
from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
PAGES = [
    "index.html", "executive-summary.html", "property-a.html", "property-b.html",
    "projections.html", "decision.html", "black-swans.html", "taxes.html",
    "inheritance.html", "review.html", "methodology.html", "sources.html",
]
ASSETS = [
    "assets/style.css", "assets/sources.json", "assets/data/reference_replay.csv",
    "assets/data/official_hpi_q2.csv", "assets/data/boe_ccpi_factors.csv",
]
# URLs used by early editions that may not occur in the current tree.
EARLIER_URLS = """costs.html cupertino.html san-francisco.html decision-analysis.html
flagged.html flagged-review.html inheritance-process.html inheritance-steps.html
properties.html sources-verification.html taxes-estate.html audit.html stress.html
pages/costs.html pages/decision-analysis.html pages/executive-summary.html
pages/flagged.html pages/inheritance-tax.html pages/methodology.html pages/process.html
pages/properties.html pages/sources.html data/summary.json data/tax.json
assets/app.js assets/js/app.js assets/css/style.css script.js style.css
""".split()


def retired_paths() -> list[str]:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    allowed = set(PAGES + ASSETS)
    live_sources = ("public_site/", ".github/", "scripts/")
    suffixes = {".html", ".json", ".csv", ".js", ".css", ".py"}
    retired = set(EARLIER_URLS)
    for name in tracked:
        if name in allowed or name.startswith(live_sources):
            continue
        if Path(name).suffix in suffixes:
            retired.add(name)
    return sorted(retired - allowed)


def notice(name: str) -> str:
    rel = Path(name)
    if rel.suffix == ".html":
        home = "../" * (len(rel.parts) - 1) + "index.html"
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<meta name="robots" content="noindex"><meta name="referrer" content="no-referrer">'
                '<title>Publication withdrawn</title></head><body><main>'
                '<h1>Earlier publication withdrawn</h1>'
                '<p>This version was removed because private or unverified figures were published.</p>'
                f'<p><a href="{home}">Open the source-reviewed public planning dashboard</a></p>'
                '<p>PUBLICATION_WITHDRAWN</p></main></body></html>\n')
    if rel.suffix == ".json":
        return '{"status":"PUBLICATION_WITHDRAWN"}\n'
    if rel.suffix == ".csv":
        return 'status\nPUBLICATION_WITHDRAWN\n'
    if rel.suffix == ".py":
        return '"""PUBLICATION_WITHDRAWN: previous generator disabled."""\n'
    if rel.suffix in (".css", ".js"):
        return '/* PUBLICATION_WITHDRAWN: previous asset removed. */\n'
    return '# PUBLICATION_WITHDRAWN\n'


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    allowed = PAGES + ASSETS
    for name in allowed:
        source = ROOT / name
        if not source.is_file():
            raise SystemExit(f"Missing allowlisted output: {name}")
        dest = SITE / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    (SITE / ".nojekyll").touch()
    for name in retired_paths():
        dest = SITE / name
        if dest.exists():
            raise SystemExit(f"Retired path overlaps allowlist: {name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(notice(name), encoding="utf-8")
    published = {str(path.relative_to(SITE)) for path in SITE.rglob("*") if path.is_file()}
    expected = set(allowed) | set(retired_paths()) | {".nojekyll"}
    if published != expected:
        raise SystemExit(f"Artifact mismatch: unexpected {published - expected}, missing {expected - published}")
    print(f"Packaged {len(PAGES)} evidence pages, {len(ASSETS)} assets and "
          f"{len(expected) - len(allowed) - 1} privacy withdrawal notices.")


if __name__ == "__main__":
    main()
