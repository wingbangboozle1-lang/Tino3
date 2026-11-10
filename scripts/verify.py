"""Structural, citation, privacy-boundary and reproducible-build checks."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, subprocess
R=Path(__file__).resolve().parents[1]
allowed={'www.lao.ca.gov','www.boe.ca.gov','www.irs.gov','www.sco.ca.gov','www.ftb.ca.gov','www.insurance.ca.gov','leginfo.legislature.ca.gov','www.fdic.gov','www.sf.gov','sftreasurer.org'}
class Check(HTMLParser):
    def __init__(self,path):
        super().__init__(convert_charrefs=True);self.path=path;self.row=None;self.header=False;self.rows=0;self.main=False;self.title=False;self.current=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr':self.row=[];self.header=False
        if tag=='th':self.header=True;assert a.get('scope')=='col'
        if tag=='main':self.main=True
        if tag=='title':self.title=True
        assert tag not in {'script','iframe','form','input'},f'{self.path}: forbidden collection/embed'
        if 'src' in a:assert not urlparse(a['src']).netloc
        if a.get('aria-current')=='page':self.current+=1
        if tag in {'a','link'}:
            u=a.get('href','');p=urlparse(u)
            if p.scheme:
                assert p.scheme=='https' and p.hostname in allowed,u
                if self.row is not None:self.row.append(u)
            elif u and not u.startswith('#'):
                assert (self.path.parent/unquote(p.path)).exists(),f'Broken local link: {u}'
    def handle_endtag(self,tag):
        if tag=='tr':
            if not self.header:assert self.row,f'Uncited table row in {self.path}';self.rows+=1
            self.row=None
count=0
files=list(R.glob('*.html'))
assert len(files)==8
before={f:f.read_bytes() for f in files}
subprocess.run(['python','scripts/build.py'],cwd=R,check=True)
assert before=={f:f.read_bytes() for f in files},'Generated output is stale'
for f in files:
    text=f.read_text();c=Check(f);c.feed(text)
    assert c.main and c.title and c.current==1
    # No address/ZIP/private-record data structures are permitted in public source.
    assert 'localStorage' not in text and 'google-analytics' not in text
    count+=c.rows
sources=json.loads((R/'assets/sources.json').read_text())
assert len(sources)==23
for s in sources.values():assert urlparse(s['url']).hostname in allowed
print(f'PASS: {len(files)} reproducible pages; {count} cited data rows; internal links, source domains, navigation, no forms/scripts/remote assets.')
print('Scope: structural checks do not prove legal completeness or external-link availability. See source ledger for human review scope.')
