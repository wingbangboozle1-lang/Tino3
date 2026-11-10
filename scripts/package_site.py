"""Assemble the publication directory.

GitHub Pages for this repository is configured to publish the branch root ("legacy" build type),
so the repository root *is* the site. This script therefore mirrors the whole tracked tree into
`_site/` and the Actions artifact matches what the branch publisher serves, so the two paths can
never disagree about content. Only `.git`, `.github`, `_site` and caches are excluded.
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
SKIP = {".git", ".github", "_site", "__pycache__", ".pytest_cache", "node_modules"}

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()

count = 0
for path in sorted(ROOT.rglob("*")):
    rel = path.relative_to(ROOT)
    if any(part in SKIP for part in rel.parts):
        continue
    dest = OUT / rel
    if path.is_dir():
        dest.mkdir(parents=True, exist_ok=True)
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, dest)
    count += 1

(OUT / ".nojekyll").touch()

required = [
    "index.html", "executive-summary.html", "properties.html", "property-tax.html",
    "operating-costs.html", "taxes-estate.html", "inheritance-process.html", "laws-watch.html",
    "flagged-for-review.html", "sources.html", "privacy.html", "decision-analysis.html",
    "projections.html", "assets/site.css", "assets/site.js", "data/model_outputs.json",
]
missing = [r for r in required if not (OUT / r).exists()]
assert not missing, f"publication is missing: {missing}"
print(f"packaged {count} files into _site (root-mirroring publication)")
