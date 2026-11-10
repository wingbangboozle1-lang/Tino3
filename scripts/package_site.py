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
# Explicitly overwrite old published entrypoints with safe withdrawal notices.
# No original legacy file content is read or copied.
for pattern in ('*.html','pages/*.html','data/*.json','data/*.csv','assets/app.js','assets/js/*.js','script.js'):
    for old in R.glob(pattern):
        relative=old.relative_to(R); dest=D/relative
        if dest.exists(): continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        if old.suffix=='.html':
            dest.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="robots" content="noindex"><title>Publication withdrawn</title><h1>Earlier publication withdrawn</h1><p>Unverified property data is no longer published here. Use the reviewed planning edition.</p><a href="'+('../' if str(relative).startswith('pages/') else '')+'index.html">Open reviewed edition</a></html>')
        elif old.suffix=='.json':dest.write_text('{"status":"withdrawn","reason":"privacy and verification review"}\n')
        elif old.suffix=='.csv':dest.write_text('status\nwithdrawn\n')
        else:dest.write_text('/* Earlier publication withdrawn for privacy review. */\n')
print('Packaged reviewed edition and content-free withdrawal notices at legacy URLs; no legacy data copied.')
