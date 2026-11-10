"""Fail closed: legacy paths must contain only withdrawal notices, not household data."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html','taxes.html','decision.html','costs.html','projections.html','inheritance.html','review.html','sources.html')
ASSETS = ('assets/style.css','assets/sources.json')
APPROVED = set(PAGES + ASSETS + (
    '.gitignore','.nojekyll','COORDINATION.md','README.md',
    '.github/workflows/pages.yml','.github/workflows/verify.yml',
    'scripts/build.py','scripts/package_site.py','scripts/verify.py','scripts/privacy_boundary.py',
))
MARKER = 'PUBLICATION_WITHDRAWN'

def tracked():
    return subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()

def notice(name):
    path = Path(name)
    if path.suffix == '.html':
        home = '../' * (len(path.parts)-1) + 'index.html'
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<meta name="robots" content="noindex"><title>Publication withdrawn</title></head>'
                '<body><main><h1>Earlier publication withdrawn</h1>'
                '<p>Unverified financial content was withdrawn for privacy and evidence review.</p>'
                f'<p><a href="{home}">Open the reviewed planning dashboard</a></p>'
                f'<p>{MARKER}</p></main></body></html>\n')
    if path.suffix == '.json':
        return '{"status":"' + MARKER + '"}\n'
    if path.suffix == '.csv':
        return 'status\n' + MARKER + '\n'
    if path.suffix == '.py':
        return f'"""{MARKER}: legacy generator disabled to prevent republication."""\n'
    if path.suffix in ('.js','.css'):
        return f'/* {MARKER}: earlier content removed. */\n'
    return f'# {MARKER}\n\nEarlier content withdrawn for privacy and evidence review.\n'

def verify():
    for name in tracked():
        if name not in APPROVED:
            assert (ROOT/name).read_text() == notice(name), f'Unapproved publication: {name}'
    print('PASS: all tracked non-allowlisted files are content-free withdrawal notices.')

if __name__ == '__main__':
    verify()
