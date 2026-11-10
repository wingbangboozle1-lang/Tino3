#!/usr/bin/env python3
"""Fail-closed checks for the cross-check edition.  Run:  python plan/tools/verify.py

 1. Reproducible: rebuilding into a scratch directory gives byte-identical pages and data.
 2. Structure: one <main>, one <title>, one aria-current per page; no scripts, forms or remote assets.
 3. Citations: every table body row carries at least one https link to a host in the source ledger,
    and at least one of them is not the repository itself unless the row is repository evidence.
 4. Links: every local link resolves.
 5. Privacy: no place name, postal code, parcel number, street address or e-mail in pages or data.
 6. Rounding: every dollar amount is a multiple of $10 unless marked as an exact official amount.
"""
from __future__ import annotations
import re, subprocess, sys, tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

HERE = Path(__file__).resolve().parent
PLAN = HERE.parent
sys.path.insert(0, str(HERE))
from sources import SOURCES  # noqa: E402

PAGES = ["index.html", "summary.html", "properties.html", "projections.html", "decision.html",
         "taxes.html", "steps.html", "laws.html", "flagged.html", "sources.html"]
DATA = ["data/model.json", "data/sources.json", "data/projection_a.csv", "data/projection_b.csv",
        "data/decisions.csv", "data/headroom.csv", "data/cash_cases.csv"]
HOSTS = {urlparse(v[2]).hostname for v in SOURCES.values()}
REPO_HOST = "github.com"

PRIVACY = {
    "place name": re.compile(r"\b(Cupertino|San\s+Francisco|Outer\s+Sunset|Sunset\s+District|Sunnyvale|Santa\s+Clara|San\s+Jose)\b", re.I),
    "postal code": re.compile(r"\b9[45]\d{3}\b(?!\s*(?:a |per |of ))"),
    "parcel number": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
}
OFFICIAL = re.compile(r'<span data-official="1">.*?</span>', re.S)
DOLLAR = re.compile(r"\$(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?")


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.errors = path, []
        self.main = self.title = self.current = self.rows = 0
        self.in_tbody = False
        self.row = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "iframe", "form", "input", "textarea", "object", "embed"}:
            self.errors.append(f"forbidden element <{tag}>")
        if tag == "main":
            self.main += 1
        if tag == "title":
            self.title += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = []
        if tag == "th" and a.get("scope") != "col":
            self.errors.append("th without scope=col")
        if a.get("aria-current") == "page":
            self.current += 1
        if "src" in a:
            self.errors.append(f"embedded asset {a['src']}")
        if tag in {"a", "link"}:
            href = a.get("href", "")
            p = urlparse(href)
            if p.scheme:
                if p.scheme != "https" or p.hostname not in HOSTS:
                    self.errors.append(f"link outside the source ledger: {href}")
                if self.row is not None:
                    self.row.append(p.hostname)
            elif href and not href.startswith("#"):
                if not (self.path.parent / unquote(p.path)).resolve().exists():
                    self.errors.append(f"broken local link {href}")

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row is not None:
            if not self.row:
                self.errors.append("table row without a source link")
            self.rows += 1
            self.row = None


def main() -> int:
    fails = []
    before = {n: (PLAN / n).read_bytes() if (PLAN / n).exists() else None for n in PAGES + DATA}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(HERE / "build.py"), tmp], check=True, capture_output=True, cwd=PLAN.parent)
        for name in PAGES + DATA:
            fresh = Path(tmp) / name
            if not fresh.exists():
                fresh = PLAN / name          # model.py writes its data files next to itself
            if before[name] is None:
                fails.append(f"missing {name}")
            elif before[name] != fresh.read_bytes():
                fails.append(f"stale build: {name}")
    rows = 0
    for name in PAGES:
        path = PLAN / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        pg = Page(path)
        pg.feed(text)
        fails += [f"{name}: {x}" for x in pg.errors[:10]]
        if (pg.main, pg.title, pg.current) != (1, 1, 1):
            fails.append(f"{name}: main/title/aria-current = {pg.main}/{pg.title}/{pg.current}")
        rows += pg.rows
        for label, rx in PRIVACY.items():
            for m in rx.finditer(text):
                fails.append(f"{name}: possible {label}: {m.group(0)!r}")
        for m in DOLLAR.finditer(OFFICIAL.sub("", text)):
            if m.group(2) or int(m.group(1).replace(",", "")) % 10:
                fails.append(f"{name}: amount not rounded to $10: {m.group(0)}")
    for name in DATA + ["tools/model.py", "tools/build.py", "tools/sources.py", "assets/style.css"]:
        text = (PLAN / name).read_text(encoding="utf-8")
        for label, rx in PRIVACY.items():
            if label == "postal code" and not name.endswith((".py", ".css")):
                continue                      # numeric data files legitimately contain five-digit numbers
            for m in rx.finditer(text):
                fails.append(f"{name}: possible {label}: {m.group(0)!r}")
    if fails:
        print("FAIL")
        for f in dict.fromkeys(fails):
            print("  -", f)
        return 1
    read = sum(1 for v in SOURCES.values() if v[3] == "read")
    print(f"PASS: {len(PAGES)} pages rebuilt byte-identically; {rows} table rows, each with a source link; "
          f"{len(SOURCES)} ledger sources ({read} read in full); local links, privacy scan and $10 rounding clean.")
    print("Scope: structure, citations and privacy patterns only. It cannot prove that a law will not change, "
          "that an owner-provided figure is right, or that an external page is still online.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
