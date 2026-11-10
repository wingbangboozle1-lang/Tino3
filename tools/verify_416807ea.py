"""Check the research supplement's citation and privacy boundaries, without network access.

Privacy note (final integration, arena-9233adb2-tino3): the original version of this
script listed forbidden private fragments as plaintext literals, which re-exposed the
very values it guarded whenever the script itself was served by GitHub Pages. The
literals are now SHA-256 digest prefixes (same technique as
decision-suite/scripts/verify_suite.py), so this file is safe to publish. The
supplement page itself is held to the strictest standard: none of the owner-derived
identifier tokens may appear in any form.
"""
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

FORBIDDEN_SHA256_PREFIXES = {
    "2478d903d7c875f0", "43086d953bcc428c", "099edec0edb103d8", "492053065ed017f4",
    "02cf62656564decc", "e8537c60cf3ce941", "37bf94938358f1fd",
}
NUM_TOKEN_RE = re.compile(r"\b[0-9]{1,3}(?:,[0-9]{3})+\b|\b[0-9]{4,7}\b")

class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.row = None; self.data = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr': self.row = []; self.data = False
        if tag == 'td' and self.row is not None: self.data = True
        if tag == 'a':
            url = attrs.get('href', ''); host = urlparse(url).hostname or ''
            if self.row is not None and (host == 'gov' or host.endswith('.gov')):
                self.row.append(url)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            if self.data: assert self.row, 'Data row missing an official .gov link'
            self.row = None

p = Path(__file__).resolve().parents[1] / 'verified-dashboard/index.html'
text = p.read_text(); parser = Check(); parser.feed(text)
for m in NUM_TOKEN_RE.finditer(text):
    norm = m.group(0).replace(',', '')
    digest = hashlib.sha256(norm.encode()).hexdigest()[:16]
    assert digest not in FORBIDDEN_SHA256_PREFIXES, 'Private input token found in supplement'
print('Supplement: all data rows cite a .gov host; owner-derived identifier tokens absent (digest-checked). URL availability and substantive accuracy require separate review.')
