"""Package reviewed pages and sanitized legacy paths. Never read household datasets."""
from pathlib import Path
import shutil
from privacy_boundary import ROOT, PAGES, ASSETS, tracked, notice, verify
verify()
D = ROOT / '_site'
if D.exists():
    shutil.rmtree(D)
for name in (*PAGES, *ASSETS):
    dest = D / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, dest)
(D / '.nojekyll').touch()
for name in tracked():
    if name in PAGES or name in ASSETS or Path(name).suffix not in ('.html','.json','.csv','.js'):
        continue
    dest = D / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(notice(name))
print('Packaged reviewed dashboard and withdrawal notices; no legacy financial content.')
