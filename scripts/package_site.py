"""Build the published artifact.

Publication is an allowlist, not a copy of the repository. Only the pages, stylesheet and data
files named below can reach the deployed site. Every path that an older edition published is
overwritten with a content-free withdrawal notice, so a request for a stale URL cannot return
an old figure.
"""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"

PAGES = ["index.html", "executive-summary.html", "property-a.html", "property-b.html", "taxes.html",
         "projections.html", "decision.html", "inheritance.html", "review.html", "sources.html"]
ASSETS = ["assets/style.css", "assets/sources.json",
          "assets/data/model.json", "assets/data/property_a.csv",
          "assets/data/property_b.csv", "assets/data/decision.csv"]

# Paths that earlier editions published. They are withdrawn even though the files no longer
# exist in the repository, because the previous deployment still answers on those URLs.
RETIRED = """cupertino.html san-francisco.html costs.html decision-analysis.html flagged.html
flagged-review.html inheritance-process.html inheritance-steps.html methodology.html properties.html
sources-verification.html taxes-estate.html script.js assets/app.js assets/js/app.js
assets/css/style.css style.css pages/costs.html pages/decision-analysis.html
pages/executive-summary.html pages/flagged.html pages/inheritance-tax.html pages/methodology.html
pages/process.html pages/properties.html pages/sources.html data/costs.json data/properties.json
data/summary.json data/tax.json data/sources.json data/projections.csv data/sell_and_reinvest.csv
data/sf_rental_pl.csv data/estate_threshold.csv data/inheritance_scenarios.csv data/sources.csv""".split()

# Annex editions restored by final integration (arena-9233adb2-tino3): the owner-directed
# anonymized Decision Brief (placeholders, every figure $10-rounded, verified by
# decision-suite/scripts/verify_suite.py) plus the preserved research supplement and audit.
# They are published verbatim; the decision-suite/** paths were therefore removed from
# RETIRED above so no stale URL in that tree serves a notice over live content.
ANNEX = ["decision-suite", "verified-dashboard", "audit"]

NOTICE_HTML = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="robots" content="noindex">'
               '<title>Publication withdrawn</title><h1>Earlier publication withdrawn</h1>'
               '<p>Unverified property data is no longer published here. Use the reviewed planning edition.</p>'
               '<a href="{prefix}index.html">Open the reviewed edition</a></html>')


def write_notice(rel: Path) -> None:
    dest = SITE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefix = "../" if rel.parts and rel.parts[0] in {"pages", "data", "decision-suite", "assets"} else ""
    if rel.suffix == ".html":
        dest.write_text(NOTICE_HTML.format(prefix=prefix), encoding="utf-8")
    elif rel.suffix == ".json":
        dest.write_text('{"status":"withdrawn","reason":"privacy and verification review"}\n', encoding="utf-8")
    elif rel.suffix == ".csv":
        dest.write_text("status\nwithdrawn\n", encoding="utf-8")
    else:
        dest.write_text("/* Earlier publication withdrawn for privacy review. */\n", encoding="utf-8")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)

    for name in PAGES + ASSETS:                      # allowlist only
        src = ROOT / name
        if not src.exists():
            raise SystemExit(f"allowlisted file missing: {name}")
        dest = SITE / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    (SITE / ".nojekyll").touch()

    notices = 0
    for rel_str in RETIRED:                          # withdraw every retired path
        rel = Path(rel_str)
        if (SITE / rel).exists():
            continue
        write_notice(rel)
        notices += 1

    annex_files = []
    for name in ANNEX:                               # owner-directed annex editions
        src_dir = ROOT / name
        if src_dir.is_file():
            annex_files.append(name)
        else:
            annex_files.extend(sorted(str(p.relative_to(ROOT)) for p in src_dir.rglob("*")
                                      if p.is_file() and "__pycache__" not in p.parts))
    for rel_str in annex_files:
        rel = Path(rel_str)
        dest = SITE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)

    published = sorted(str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file())
    allowed = set(PAGES) | set(ASSETS) | {".nojekyll"} | set(annex_files)
    unexpected = [p for p in published if p not in allowed and p not in RETIRED]
    if unexpected:
        raise SystemExit(f"non-allowlisted file in artifact: {unexpected}")
    print(f"Packaged {len(PAGES)} pages and {len(ASSETS)} assets; "
          f"{notices} withdrawal notices at retired paths; no legacy data copied.")


if __name__ == "__main__":
    main()
