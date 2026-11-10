"""Check this supplement's citation and privacy boundaries, without network access."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

class Check(HTMLParser):
    def __init__(self):
        super().__init__(); self.row = None; self.data = False; self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr': self.row = []; self.data = False
        if tag == 'td' and self.row is not None: self.data = True
        if tag == 'a':
            url = attrs.get('href', ''); self.links.append(url)
            host = urlparse(url).hostname or ''
            if self.row is not None and (host == 'gov' or host.endswith('.gov')):
                self.row.append(url)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            if self.data: assert self.row, 'Data row missing an official .gov link'
            self.row = None

p = Path(__file__).resolve().parents[1] / 'verified-dashboard/index.html'
text = p.read_text(); parser = Check(); parser.feed(text)
for private_fragment in ('95014', '94122', '539,743', '114,248', '7,150', '3,100,000', '1,800,000'):
    assert private_fragment not in text, 'Private input found'
print('Supplement: all data rows cite a .gov host; selected private inputs absent. URL availability and substantive accuracy require separate review.')
