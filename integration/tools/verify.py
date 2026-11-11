#!/usr/bin/env python3
"""Fail-closed verification for the requirements-traceability edition.

Checks:
 1. Reproducible build: re-running integration/tools/build.py must not change a byte.
 2. Structure: title, one main, exactly one aria-current, no scripts/forms/remote assets.
 3. Links: internal targets exist; every external host is on the official allowlist.
 4. Citations: every table row links to an official publisher on the host allowlist.
    The source ledger must say how each source was checked and use an allowed host.
 5. Privacy: no ZIP code, parcel number, street address, city/county name, owner name or e-mail.
 6. Rounding: every dollar amount displayed is a multiple of $10.
 7. Coverage: all requirement rows, summary rows and flags cite existing ledger sources.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
PAGES = ["index.html", "executive-summary.html", "findings.html", "flagged.html"]
CSVS = ["requirements.csv", "summary.csv", "findings.csv", "flagged.csv"]
STATIC = ["README.md", "tools/build.py", "tools/verify.py"]
JSONS = ["sources.json", "requirements.json", "summary.json", "flags.json", "categories.json", "publication.json"]

ALLOWED_HOSTS = {
    # federal
    "www.irs.gov", "irs.gov", "home.treasury.gov", "www.tsp.gov", "www.huduser.gov",
    "fred.stlouisfed.org", "www.federalreserve.gov", "federalreserve.gov",
    "www.federalreservehistory.org", "www.bls.gov", "bls.gov", "www.cbo.gov", "cbo.gov",
    "www.ssa.gov", "ssa.gov", "www.govinfo.gov", "libertystreeteconomics.newyorkfed.org",
    # state
    "www.boe.ca.gov", "boe.ca.gov", "leginfo.legislature.ca.gov", "www.ftb.ca.gov", "ftb.ca.gov",
    "www.cpuc.ca.gov", "cpuc.ca.gov", "www.insurance.ca.gov", "www.lao.ca.gov", "www.sos.ca.gov",
    "www.sco.ca.gov", "elections.cdn.sos.ca.gov", "electionresults.sos.ca.gov",
    # local (jurisdictions are generic on the page; the publisher domains remain official)
    "sftreasurer.org", "www.sf.gov", "files.santaclaracounty.gov", "clerkrecorder.santaclaracounty.gov",
    # platform documentation
    "docs.github.com", "github.com",
}

# The privacy scanner never writes a place name in clear text. It stores salted SHA-256
# digests of lowercase one-, two- and three-word sequences and compares token windows.
SALT = b"requirements-scan-v1:"
PLACE_DIGESTS = {
    "2683adc4d970ad41151be1ba61030eda2a13be18508fd845dbea16f051009cba",
    "b66d077c098244ecc740cc9547d1cac0a9e0e422ac3e04e6c3c4fb7130f0f8f4",
    "e005290caf8e35941a5bdb3c73a430ae8a17308d0c25617a5941e4667dd7c5eb",
    "2773e77d41bd88d53fb31272363730d42184426402255dff5aed807d1a485c5e",
    "c3819b93b75d6fc5578d219390a7cfab740827a18fecdf7a30b600cf7d87f156",
    "fd047b79d82540196bfd459ea280f441d69ae4311d4306de2779299da9c33a62",
    "2843bb2c8766d1b2b42b6e8bac1119a74eb4f00f18725299d1dff82fbb4e945d",
    "06003179e7572db8ba4669dceb7072889bf91be1a6bea35f063e40bf676b2524",
    "f41f11d8f7e6f6c9468d72deb16803ea817417592d41f9b2d8e4279feb9a737b",
    "d2ab679a96b13f37464360691fafb9ea4450830c20a2b031f4f08556a6db08b2",
    "bf855420490ea72882439e503e30585fe1cd3a5c0b833ff5a90ab1d5aec93522",
}
WORD = re.compile(r"[A-Za-z]+")
# Official publisher URLs necessarily contain their hosts and sometimes a place name in a slug.
# Those links are required for manual review, so the place-name scan reads the remaining text.
URL_OR_HOST = re.compile(r"(?:https?://|www\.)\S+|(?<!@)\b[\w.-]+\.(?:gov|org|com|net|edu)\b", re.I)


def visible_text(text: str) -> str:
    return URL_OR_HOST.sub(" ", text)


def place_name_hits(text: str):
    words = [w.lower() for w in WORD.findall(text)]
    for i, word in enumerate(words):
        for n in (1, 2, 3):
            seq = " ".join(words[i:i + n])
            if len(words[i:i + n]) == n and hashlib.sha256(SALT + seq.encode()).hexdigest() in PLACE_DIGESTS:
                yield seq


FORBIDDEN = {
    "ZIP code": re.compile(r"(?:\bCA\b|California|zip|postal code)\W{0,6}9\d{4}\b", re.I),
    "parcel/APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "double-escaped entity": re.compile(r"&amp;(?:ndash|rsquo|mdash|middot|minus|nbsp|hellip);"),
}
DECIMAL_AMOUNT = re.compile(r"\$[1-9][\d,]*\.\d{1,2}(?![\d])")
DOLLAR = re.compile(r"\$(\d{1,3}(?:,\d{3})+|\d+)(?![\d.,])(\s*(?:million|billion|trillion|thousand|per)\b)?", re.I)


class Page(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.row = None
        self.header = False
        self.rows = 0
        self.cited_rows = 0
        self.main = 0
        self.title = 0
        self.current = 0
        self.errors = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "iframe", "form", "input", "textarea", "object", "embed"}:
            self.errors.append(f"forbidden element <{tag}>")
        if tag == "main":
            self.main += 1
        if tag == "title":
            self.title += 1
        if tag == "tr":
            self.row = []
            self.header = False
        if tag == "th":
            self.header = True
            if a.get("scope") != "col":
                self.errors.append("th without scope=col")
        if a.get("aria-current") == "page":
            self.current += 1
        if "src" in a and urlparse(a["src"]).netloc:
            self.errors.append(f"remote asset {a['src']}")
        if tag in {"a", "link"}:
            href = a.get("href", "")
            p = urlparse(href)
            if p.scheme:
                if p.scheme != "https":
                    self.errors.append(f"non-https link {href}")
                if p.hostname not in ALLOWED_HOSTS:
                    self.errors.append(f"non-official host {href}")
                if self.row is not None:
                    self.row.append(href)
                return
            if href and not href.startswith("#"):
                target = (self.path.parent / unquote(p.path)).resolve()
                if not target.exists():
                    self.errors.append(f"broken local link {href}")
                if self.row is not None:
                    self.row.append(href)

    def handle_endtag(self, tag):
        if tag == "tr":
            if not self.header:
                if not self.row:
                    self.errors.append("uncited table row")
                elif any(urlparse(h).scheme for h in self.row):
                    self.cited_rows += 1
                else:
                    self.errors.append("table row without a link to an official publisher")
                self.rows += 1
            self.row = None


def scan_text(name: str, text: str, failures: list[str]) -> None:
    for label, rx in FORBIDDEN.items():
        for m in rx.finditer(text):
            failures.append(f"{name}: possible {label}: {m.group(0)!r}")
    for hit in place_name_hits(visible_text(text)):
        failures.append(f"{name}: possible place name: {hit!r}")
    for m in DECIMAL_AMOUNT.finditer(text):
        failures.append(f"{name}: amount with cents {m.group(0)}")
    for m in DOLLAR.finditer(text):
        if m.group(2):
            continue
        raw = m.group(1).replace(",", "")
        if int(raw) % 10 != 0:
            failures.append(f"{name}: unrounded amount {m.group(0)}")


def main() -> int:
    failures: list[str] = []
    generated = [ROOT / p for p in PAGES] + [ROOT / "data" / c for c in CSVS]
    before = {p: p.read_bytes() for p in generated}
    subprocess.run([sys.executable, "integration/tools/build.py"], cwd=REPO, check=True, capture_output=True)
    after = {p: p.read_bytes() for p in generated}
    stale = [str(p.relative_to(REPO)) for p in generated if before[p] != after[p]]
    if stale:
        failures.append(f"generated output was stale: {stale}")

    total_rows = total_cited = 0
    for name in PAGES:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        pg = Page(path)
        pg.feed(text)
        if pg.errors:
            failures.extend(f"{name}: {x}" for x in pg.errors[:12])
        if pg.main != 1 or pg.title != 1:
            failures.append(f"{name}: main/title count {pg.main}/{pg.title}")
        if pg.current != 1:
            failures.append(f"{name}: aria-current count {pg.current}")
        total_rows += pg.rows
        total_cited += pg.cited_rows
        scan_text(name, text, failures)

    for rel in STATIC:
        path = ROOT / rel
        if not path.exists():
            failures.append(f"missing {rel}")
        else:
            scan_text(rel, path.read_text(encoding="utf-8"), failures)
    for name in JSONS + CSVS:
        path = ROOT / "data" / name
        if not path.exists():
            failures.append(f"missing data/{name}")
            continue
        scan_text(f"data/{name}", path.read_text(encoding="utf-8"), failures)

    sources = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    src = sources["sources"]
    for sid, s in src.items():
        host = urlparse(s["url"]).hostname
        if host not in ALLOWED_HOSTS:
            failures.append(f"sources.json: {sid} is not on an official host ({host})")
        if not s["url"].startswith("https://"):
            failures.append(f"sources.json: {sid} is not https")
        if not s.get("checked"):
            failures.append(f"sources.json: {sid} does not say how it was checked")
        for key in ("publisher", "title", "quote", "supports", "status", "category"):
            if not s.get(key):
                failures.append(f"sources.json: {sid} missing {key}")

    reqs = json.loads((ROOT / "data" / "requirements.json").read_text(encoding="utf-8"))["requirements"]
    expected = [f"R-{i:02d}" for i in range(1, len(reqs) + 1)]
    if [r["id"] for r in reqs] != expected:
        failures.append("requirements.json: IDs are not sequential R-01..")
    for r in reqs:
        if not r["sources"] or any(s not in src for s in r["sources"]):
            failures.append(f"requirements.json: {r['id']} has a missing official source")
        for p in r["pages"]:
            if not (ROOT / p).exists() and not (REPO / p).exists():
                failures.append(f"requirements.json: {r['id']} has a broken answer page {p}")

    for key in ("summary.json", "flags.json"):
        obj = json.loads((ROOT / "data" / key).read_text(encoding="utf-8"))
        rows = obj.get("summary") or obj.get("flags")
        for row in rows:
            if not row["sources"] or any(s not in src for s in row["sources"]):
                failures.append(f"{key}: a row has a missing official source")

    pub = json.loads((ROOT / "data" / "publication.json").read_text(encoding="utf-8"))
    for key in ("edition", "session", "privacy", "verification", "site", "coordination"):
        if not pub.get(key):
            failures.append(f"publication.json: missing {key}")

    if failures:
        print("FAIL")
        for f in dict.fromkeys(failures):
            print("  -", f)
        return 1
    print(f"PASS: {len(PAGES)} reproducible pages; {total_rows} table rows "
          f"(all {total_cited} link to an official publisher); {len(src)} ledger sources; "
          f"{len(reqs)} requirements; links, official hosts, privacy scan and $10 rounding all clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
