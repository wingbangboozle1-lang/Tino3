"""Publish allowlist only: do not deploy legacy financial data or repository files."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1]
D=R/'_site'
if D.exists():shutil.rmtree(D)
for name in ('index.html','taxes.html','decision.html','costs.html','projections.html','inheritance.html','review.html','sources.html','assets/style.css','assets/sources.json'):
    dest=D/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,dest)
(D/'.nojekyll').touch()
assert len(list(D.rglob('*.*')))==11
print('Packaged only 8 reviewed pages, 2 assets, and .nojekyll; legacy data excluded.')
