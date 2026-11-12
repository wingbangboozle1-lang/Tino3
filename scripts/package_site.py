"""Build the deployable site from an explicit public-edition allowlist.

Only the privacy-safe pages and stylesheet are copied verbatim. Every other tracked path is
replaced in the artifact with a generic withdrawal notice, including the old model/data,
secondary editions, repository tools and source documents. The working tree remains available
for audit; Git history and copies outside this artifact are not erased.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"

from build import PAGES  # noqa: E402

ASSETS = ["assets/style.css"]
NOJEKYLL = ".nojekyll"
LEGACY_URLS = [
    "black-swans.html", "decision-analysis.html", "flagged.html", "flagged-review.html",
    "inheritance-process.html", "inheritance-steps.html", "methodology.html", "properties.html",
    "sources-verification.html", "taxes-estate.html", "script.js", "style.css",
    "assets/app.js", "assets/js/app.js", "assets/css/style.css",
    "pages/costs.html", "pages/decision-analysis.html", "pages/executive-summary.html",
    "pages/flagged.html", "pages/inheritance-tax.html", "pages/methodology.html",
    "pages/process.html", "pages/properties.html", "pages/sources.html",
    "data/costs.json", "data/properties.json", "data/summary.json", "data/tax.json",
    "data/sources.json", "data/projections.csv", "data/sell_and_reinvest.csv",
    "data/estate_threshold.csv", "data/inheritance_scenarios.csv", "data/sources.csv",
    "decision-suite/index.html", "decision-suite/executive-summary.html",
    "decision-suite/property-a.html", "decision-suite/property-b.html",
    "decision-suite/taxes-and-laws.html", "decision-suite/projections.html",
    "decision-suite/decision-analysis.html", "decision-suite/inheritance-process.html",
    "decision-suite/flagged-for-review.html", "decision-suite/sources-ledger.html",
    "decision-suite/assets/app.js", "decision-suite/assets/style.css",
]


def tracked_paths() -> list[str]:
    return subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()


def retired_paths() -> list[str]:
    """Return every legacy URL plus every tracked path outside the publication allowlist."""
    allowed = set(PAGES + ASSETS + [NOJEKYLL])
    paths = set(LEGACY_URLS)
    paths.update(name for name in tracked_paths() if name not in allowed)
    paths.difference_update(allowed)
    return sorted(paths)


def notice_content(rel: PurePosixPath) -> str:
    """Return a content-free notice tailored to the route's file type."""
    if rel.suffix == ".html":
        prefix = "../" * len(rel.parts[:-1])
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex"><title>Publication retired</title></head>'
            '<body><main><h1>Earlier publication retired</h1>'
            '<p>This route no longer contains the earlier edition.</p>'
            f'<p><a href="{prefix}index.html">Open the current public edition</a></p>'
            '</main></body></html>\n'
        )
    if rel.suffix == ".json":
        return '{"status":"PUBLICATION_WITHDRAWN"}\n'
    if rel.suffix == ".csv":
        return "status\nPUBLICATION_WITHDRAWN\n"
    if rel.suffix == ".py":
        return '"""PUBLICATION_WITHDRAWN: source route retired."""\n'
    if rel.suffix in {".js", ".css"}:
        return "/* PUBLICATION_WITHDRAWN */\n"
    return "PUBLICATION_WITHDRAWN\n"


def write_notice(rel: PurePosixPath) -> None:
    destination = SITE.joinpath(*rel.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(notice_content(rel), encoding="utf-8")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)

    for name in PAGES + ASSETS:
        source = ROOT / name
        if not source.is_file():
            raise SystemExit(f"allowlisted file missing: {name}")
        destination = SITE / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    retired = retired_paths()
    for name in retired:
        write_notice(PurePosixPath(name))

    (SITE / NOJEKYLL).touch()
    present = {str(path.relative_to(SITE)) for path in SITE.rglob("*") if path.is_file()}
    allowed = set(PAGES + ASSETS + retired + [NOJEKYLL])
    unexpected = sorted(present - allowed)
    missing = sorted(allowed - present)
    if unexpected or missing:
        raise SystemExit(f"artifact boundary failed: unexpected={unexpected}, missing={missing}")
    print(
        f"Packaged {len(PAGES)} public pages, {len(ASSETS)} runtime asset and "
        f"{len(retired)} content-free withdrawal routes."
    )


if __name__ == "__main__":
    main()
