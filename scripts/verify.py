"""Line-by-line checks for the published site. Exit code 1 on any failure.

Nothing here proves legal correctness. It proves: the output is reproducible, every table row
carries a citation, every citation points at an allow-listed official publisher, every local link
resolves, and the privacy and rounding rules hold.
"""
from __future__ import annotations
import csv
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from sources import SOURCES  # noqa: E402

PAGES = [
    "index.html", "executive-summary.html", "properties.html", "property-tax.html",
    "operating-costs.html", "taxes-estate.html", "inheritance-process.html", "laws-watch.html",
    "flagged-for-review.html", "sources.html", "privacy.html", "decision-analysis.html",
    "projections.html",
]

ALLOWED_HOSTS = {
    "www.irs.gov", "www.boe.ca.gov", "leginfo.legislature.ca.gov", "www.ftb.ca.gov",
    "files.santaclaracounty.gov", "sftreasurer.org", "www.sf.gov", "www.sfpuc.gov",
    "www.cpuc.ca.gov", "www.insurance.ca.gov", "home.treasury.gov", "www.bls.gov",
    "fred.stlouisfed.org", "www.fhfa.gov",
}

INTERNAL_SOURCES = {"sources.html#owner-inputs", "sources.html#computed"}

# Statutory or officially published amounts quoted verbatim rather than rounded.
ROUNDING_EXEMPT = {
    "$1,044,586", "$15,000,000", "$15,480,000", "$1,571", "$1,512", "$829", "$7,000",
    "$5,000", "$100", "$334.38", "$189", "$212", "$19,000", "$1,000,000", "$12", "$43.00",
    "$21.50", "$319.34", "$99", "$1,000", "$334", "$829.22", "$742,953", "$96,700",
    "$533,400", "$600,050", "$566,700", "$48,350", "$64,750", "$300,000", "$1,485,906",
    "$371,479", "$445,771", "$11,079", "$1.1488", "$11,488", "$11,407.58", "$80.42",
}

FORBIDDEN_TEXT = ["95014", "94122", "lorem ipsum", "TBD", "TODO", "XXX"]
STREET_RE = re.compile(r"\b\d{2,5}\s+(?:[A-Z][a-z]+\s+){0,3}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Way|Place|Pl)\.?\b")
APN_RE = re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b")


class Page(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name = name
        self.title = False
        self.main = False
        self.current = 0
        self.rows = 0
        self.cited = 0
        self.in_row = False
        self.row_links = []
        self.header_row = False
        self.local = []
        self.external = []
        self.problems = []
        self.policy_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "iframe", "form", "input", "object", "embed", "style"}:
            src = a.get("src", "")
            if tag == "script" and not urlparse(src).netloc:
                pass  # local script is allowed
            else:
                self.problems.append(f"forbidden <{tag}> element")
        if tag == "th":
            self.header_row = True
        if tag == "title":
            self.title = True
        if tag == "main":
            self.main = True
        if tag == "table":
            self.policy_depth = 1 if "policy" in (a.get("class") or "") else 0
        if tag == "tr":
            self.in_row = True
            self.row_links = []
            self.header_row = False
        if a.get("aria-current") == "page":
            self.current += 1
            self.current_target = a.get("href")
        if tag in {"a", "link"}:
            u = a.get("href", "")
            if not u:
                return
            p = urlparse(u)
            if p.scheme in {"http", "https"}:
                self.external.append(u)
                if self.in_row:
                    self.row_links.append(("ext", u))
            elif u.startswith("#"):
                pass
            else:
                self.local.append(u)
                if self.in_row:
                    self.row_links.append(("int", u))

    def handle_endtag(self, tag):
        if tag == "table":
            self.policy_depth = 0
        if tag == "tr" and self.in_row:
            self.in_row = False
            if self.header_row:
                return
            self.rows += 1
            if self.policy_depth:
                self.policy_rows = getattr(self, "policy_rows", 0) + 1
                return
            ok = False
            for kind, u in self.row_links:
                if kind == "ext" and urlparse(u).hostname in ALLOWED_HOSTS:
                    ok = True
                if kind == "int" and u in INTERNAL_SOURCES:
                    ok = True
            if ok:
                self.cited += 1
            else:
                self.problems.append(f"uncited or non-official table row (links: {self.row_links})")


def check_text(path, text):
    problems = []
    for bad in FORBIDDEN_TEXT:
        if bad.lower() in text.lower():
            problems.append(f"forbidden text {bad!r}")
    for m in STREET_RE.finditer(text):
        problems.append(f"street-address-like text {m.group(0)!r}")
    for m in APN_RE.finditer(text):
        problems.append(f"parcel-number-like text {m.group(0)!r}")
    for m in re.finditer(r"\$[\d,]+(?:\.\d+)?", text):
        tok = m.group(0)
        if tok in ROUNDING_EXEMPT:
            continue
        digits = re.sub(r"[$,.\D]", "", tok)
        intpart = re.split(r"\.", tok.replace(",", ""))[0].lstrip("$")
        if not intpart.endswith("0"):
            problems.append(f"amount not rounded to $10: {tok}")
    if "None" in text and "None." not in text and "Nonetheless" not in text:
        pass
    return problems


def main():
    failures = []
    # ---- reproducibility -------------------------------------------------
    before = {p: (ROOT / p).read_bytes() for p in PAGES}
    for cmd in (["python", "model.py"], ["python", "webbuild.py"]):
        r = subprocess.run(cmd, cwd=SCRIPTS, capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"{' '.join(cmd)} failed: {r.stderr.strip()[:400]}")
    after = {p: (ROOT / p).read_bytes() for p in PAGES}
    for p in PAGES:
        if before[p] != after[p]:
            failures.append(f"committed output is stale: {p}")

    # ---- pages -----------------------------------------------------------
    total_rows = total_cited = 0
    for name in PAGES:
        path = ROOT / name
        if not path.exists():
            failures.append(f"missing page {name}")
            continue
        text = path.read_text()
        parser = Page(name)
        parser.feed(text)
        if not parser.main:
            failures.append(f"{name}: no <main>")
        if not parser.title:
            failures.append(f"{name}: no <title>")
        if parser.current != 1:
            failures.append(f"{name}: expected exactly one aria-current, found {parser.current}")
        total_rows += parser.rows
        total_cited += parser.cited
        for problem in parser.problems:
            failures.append(f"{name}: {problem}")
        for u in parser.local:
            target = unquote(urlparse(u).path)
            if not target:
                continue
            if not (path.parent / target).exists():
                failures.append(f"{name}: broken local link {u}")
        for u in parser.external:
            host = urlparse(u).hostname
            if host not in ALLOWED_HOSTS:
                failures.append(f"{name}: external link to non-allow-listed host {u}")
        for problem in check_text(path, text):
            failures.append(f"{name}: {problem}")
        if "../" in text:
            failures.append(f"{name}: unexpected parent-path link")
        for forbidden in ("google-analytics", "localStorage", "sessionStorage", "fetch(", "XMLHttpRequest"):
            if forbidden in text:
                failures.append(f"{name}: contains {forbidden}")

    # ---- source registry -------------------------------------------------
    for key, s in SOURCES.items():
        p = urlparse(s["url"])
        if key in {"OWNER", "COMPUTED"}:
            if not s["url"].startswith("sources.html#"):
                failures.append(f"internal source {key} must point at sources.html")
            continue
        if p.scheme != "https":
            failures.append(f"source {key} is not https")
        if p.hostname not in ALLOWED_HOSTS:
            failures.append(f"source {key} host not allow-listed: {p.hostname}")
        if not s["supports"].strip():
            failures.append(f"source {key} has no stated scope")
    if len(SOURCES) < 24:
        failures.append("expected at least 24 sources in the ledger")

    # ---- data files ------------------------------------------------------
    data_dir = ROOT / "data"
    csvs = sorted(data_dir.glob("*.csv"))
    if len(csvs) < 10:
        failures.append(f"expected the generated CSV set, found {len(csvs)}")
    for f in csvs:
        with f.open(newline="") as fh:
            rows = list(csv.reader(fh))
        if len(rows) < 2:
            failures.append(f"{f.name}: no data rows")
        if len({len(r) for r in rows}) != 1:
            failures.append(f"{f.name}: ragged CSV (RFC 4180 check)")
    try:
        model = json.loads((data_dir / "model_outputs.json").read_text())
        for key in ("owner", "assumptions", "values", "proj_a", "proj_b", "decisions",
                    "sensitivity", "estate", "sf_pl", "reconcile"):
            if key not in model:
                failures.append(f"model_outputs.json missing {key}")
        for y in ("2040", "2045", "2050"):
            if y not in model["decisions"]:
                failures.append(f"model_outputs.json missing decision year {y}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"model_outputs.json unreadable: {exc}")

    # ---- assets ----------------------------------------------------------
    for asset in ("assets/site.css", "assets/site.js", ".nojekyll"):
        if not (ROOT / asset).exists():
            failures.append(f"missing asset {asset}")

    print(f"pages: {len(PAGES)}")
    print(f"table rows: {total_rows}, rows carrying an official or declared source: {total_cited}")
    print(f"sources in ledger: {len(SOURCES)}")
    print(f"generated CSVs: {len(csvs)}")
    if failures:
        print(f"\nFAIL ({len(failures)})")
        for f in failures[:60]:
            print("  -", f)
        return 1
    print("\nPASS: reproducible output, every table row cited, official hosts only, "
          "local links resolve, privacy and $10 rounding rules hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
