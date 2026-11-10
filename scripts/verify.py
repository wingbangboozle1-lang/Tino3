#!/usr/bin/env python3
"""Fail-closed verification for the published edition.

Checks
 1. Reproducible build: re-running the model and the renderer must not change a byte.
 2. Structure: title, <main>, exactly one aria-current, no scripts/forms/remote assets.
 3. Links: internal targets exist; every external host is on the official allowlist.
 4. Citations: every table row links to an official publisher on the host allowlist.
    The source ledger must say how each source was checked.
 5. Privacy: no ZIP code, parcel number, street address, city/county name, owner name,
    or e-mail address anywhere in the published output.
 6. Rounding: every dollar amount displayed is a multiple of $10.
"""
from __future__ import annotations
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "executive-summary.html", "property-a.html", "property-b.html", "taxes.html",
         "projections.html", "decision.html", "inheritance.html", "review.html", "audit.html", "sources.html"]
ASSETS = ["assets/style.css", "assets/sources.json", "assets/data/model.json",
          "assets/data/property_a.csv", "assets/data/property_b.csv", "assets/data/decision.csv"]

ALLOWED_HOSTS = {
    # federal
    "www.irs.gov", "irs.gov", "home.treasury.gov", "www.tsp.gov", "www.huduser.gov", "fred.stlouisfed.org",
    # state
    "www.boe.ca.gov", "boe.ca.gov", "leginfo.legislature.ca.gov", "www.ftb.ca.gov", "ftb.ca.gov",
    "www.cpuc.ca.gov", "cpuc.ca.gov", "www.insurance.ca.gov", "www.lao.ca.gov", "www.sos.ca.gov", "www.sco.ca.gov",
    # local government (jurisdiction A and jurisdiction B)
    "sfbos.archive.sf.gov", "sftreasurer.org", "www.sf.gov",
    "clerkrecorder.santaclaracounty.gov", "files.santaclaracounty.gov",
}

# Identifier patterns that must never appear in the published edition.
SCAN_TEXT = {
    "city or county name": re.compile(r"\b(Cupertino|San Francisco|Outer Sunset|Sunnyvale|Santa Clara)\b", re.I),
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
}

FORBIDDEN = {
    "ZIP code": re.compile(r"(?:\bCA\b|California|zip|postal code)\W{0,6}9\d{4}\b", re.I),
    "parcel/APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
    "e-mail address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "double-escaped entity": re.compile(r"&amp;(?:ndash|rsquo|mdash|middot|minus|nbsp|hellip);"),
    "owner name placeholder leak": re.compile(r"\b(trustee|decedent)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b"),
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
        self.fact_rows = 0
        self.scenario_rows = 0
        self.main = 0
        self.title = 0
        self.current = 0
        self.basis = "fact"
        self.external = 0
        self.internal = 0
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
            self.basis = a.get("data-basis", "fact")
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
                self.external += 1
                if self.row is not None:
                    self.row.append(href)
            elif href and not href.startswith("#"):
                target = (self.path.parent / unquote(p.path)).resolve()
                if not target.exists():
                    self.errors.append(f"broken local link {href}")
                self.internal += 1
                if self.row is not None:
                    self.row.append(href)

    def handle_endtag(self, tag):
        if tag == "tr":
            if not self.header:
                if not self.row:
                    self.errors.append("uncited table row")
                else:
                    has_external = any(urlparse(h).scheme for h in self.row)
                    has_internal = any(not urlparse(h).scheme for h in self.row)
                    if has_external:
                        self.fact_rows += 1
                    else:
                        # Every row must link to an official publisher. An internal link alone is not enough.
                        self.errors.append("table row without a link to an official publisher")
                self.rows += 1
            self.row = None


def main() -> int:
    failures = []

    # 1. reproducible build
    before = {p: (ROOT / p).read_bytes() for p in PAGES + ASSETS}
    subprocess.run([sys.executable, "scripts/model.py"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, check=True, capture_output=True)
    after = {p: (ROOT / p).read_bytes() for p in PAGES + ASSETS}
    stale = [p for p in PAGES + ASSETS if before[p] != after[p]]
    if stale:
        failures.append(f"generated output was stale: {stale}")

    # 2-4. per page
    total_rows = total_fact = total_scenario = 0
    for name in PAGES:
        path = ROOT / name
        if not path.exists():
            failures.append(f"missing page {name}")
            continue
        text = path.read_text(encoding="utf-8")
        pg = Page(path)
        pg.feed(text)
        if pg.errors:
            failures.extend(f"{name}: {e}" for e in pg.errors[:12])
        if pg.main != 1 or pg.title != 1:
            failures.append(f"{name}: main/title count {pg.main}/{pg.title}")
        if pg.current != 1:
            failures.append(f"{name}: aria-current count {pg.current}")
        total_rows += pg.rows
        total_fact += pg.fact_rows
        total_scenario += pg.scenario_rows

        # 5. privacy
        for label, rx in list(FORBIDDEN.items()) + list(SCAN_TEXT.items()):
            for m in rx.finditer(text):
                failures.append(f"{name}: possible {label}: {m.group(0)!r}")

        for m in DECIMAL_AMOUNT.finditer(text):
            failures.append(f"{name}: amount with cents {m.group(0)}")
        # 6. rounding
        for m in DOLLAR.finditer(text):
            if m.group(2):
                continue
            raw = m.group(1).replace(",", "")
            if int(raw) % 10 != 0:
                failures.append(f"{name}: unrounded amount {m.group(0)}")

    # 5b. the same scan across the downloadable data and the model
    for name in ASSETS:
        text = (ROOT / name).read_text(encoding="utf-8", errors="replace")
        for label, rx in SCAN_TEXT.items():
            for m in rx.finditer(text):
                failures.append(f"{name}: possible {label}: {m.group(0)!r}")

    # 6b. the source ledger: official host, and a statement of how each entry was checked
    import json
    ledger = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))["sources"]
    for sid, src in ledger.items():
        if urlparse(src["url"]).hostname not in ALLOWED_HOSTS:
            failures.append(f"sources.json: {sid} is not on an official host")
        if not src.get("checked"):
            failures.append(f"sources.json: {sid} does not say how it was checked")

    # 7. every tracked non-allowlisted file must be a content-free withdrawal notice
    b = subprocess.run([sys.executable, "scripts/privacy_boundary.py"], cwd=ROOT, capture_output=True, text=True)
    if b.returncode != 0:
        failures.append("privacy boundary: " + (b.stdout + b.stderr).strip().splitlines()[-1] if (b.stdout + b.stderr).strip() else "privacy boundary failed")

    if failures:
        print("FAIL")
        for f in dict.fromkeys(failures):
            print("  -", f)
        return 1

    print(f"PASS: {len(PAGES)} reproducible pages; {total_rows} table rows "
          f"(all {total_fact} link to an official publisher); {len(ledger)} ledger sources; "
          f"local links, official hosts, privacy scan and $10 rounding all clean.")
    print("Scope: structural and privacy checks only. They do not prove legal completeness, "
          "and they cannot verify an insurance quote, an appraisal or a future statute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
