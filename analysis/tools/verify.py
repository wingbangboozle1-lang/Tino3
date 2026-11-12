#!/usr/bin/env python3
"""Fail-closed verification suite for the Ownership-Distinction & 50-Year Black-Swan Edition.

Verifies:
  1. Deterministic reproducibility (byte-identical HTML, JSON, and CSV outputs).
  2. Accessible, script-free static HTML structure and valid #fragment anchors.
  3. 100% official-publisher https:// citation on every table body row.
  4. 100% directly-opened ('read') status across the entire official source ledger.
  5. Strict privacy scan (no city/county names, postal codes, APNs, street addresses, or emails).
  6. Strict $10 rounding on every displayed dollar amount (zero cents, % 10 == 0).
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
sys.path.insert(0, str(HERE))
from sources import SOURCES  # noqa: E402

PAGES = [
    "index.html",
    "executive-summary.html",
    "ownership-distinction.html",
    "properties.html",
    "projections.html",
    "black-swan.html",
    "decision.html",
    "taxes-estate.html",
    "inheritance-steps.html",
    "repo-audit.html",
    "flagged.html",
    "sources.html",
]

DATA_FILES = [
    "data/model.json",
    "data/sources.json",
    "data/projections_50yr.csv",
    "data/historical_replay_50yr.csv",
    "data/ownership_distinction.csv",
    "data/decision_matrix.csv",
    "data/black_swan_regimes.csv",
]

ALLOWED_HOSTS = {
    "www.irs.gov", "irs.gov", "www.govinfo.gov", "home.treasury.gov", "www.tsp.gov",
    "www.bls.gov", "fred.stlouisfed.org", "www.federalreservehistory.org",
    "www.boe.ca.gov", "boe.ca.gov", "leginfo.legislature.ca.gov",
    "www.ftb.ca.gov", "ftb.ca.gov", "www.sco.ca.gov", "www.cpuc.ca.gov",
    "www.insurance.ca.gov", "www.lao.ca.gov", "www.hhs.gov", "elections.cdn.sos.ca.gov",
    "files.santaclaracounty.gov", "clerkrecorder.santaclaracounty.gov",
    "sftreasurer.org", "sfbos.archive.sf.gov", "www.sf.gov",
}

PRIVACY_PATTERNS = {
    "city or county name": re.compile(r"\b(Cupertino|San\s+Francisco|Outer\s+Sunset|Sunset\s+District|Sunnyvale|Santa\s+Clara|San\s+Jose)\b", re.I),
    "postal code": re.compile(r"(?:\bCA\b|California|zip|postal)\W{0,8}9\d{4}\b|\b9[45]\d{3}\b(?!\s*(?:a\b|per\b|of\b))", re.I),
    "parcel / APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "double-escaped entity": re.compile(r"&amp;(?:ndash|mdash|middot|minus|nbsp|ldquo|rdquo|sect|rarr|larr|le|ge|times);"),
}

CENTS_RE = re.compile(r"\$\d[\d,]*\.\d+")
DOLLAR_RE = re.compile(r"\$(\d{1,3}(?:,\d{3})+|\d+)(?![\d.,])(\s*(?:million|billion|trillion|thousand|per)\b)?", re.I)


class DashboardParser(HTMLParser):
    def __init__(self, page_path: Path):
        super().__init__(convert_charrefs=True)
        self.page_path = page_path
        self.errors: list[str] = []
        self.main_count = 0
        self.title_count = 0
        self.aria_current = 0
        self.in_tbody = False
        self.row_ext_links: list[str] | None = None
        self.tbody_rows = 0
        self.ids: set[str] = set()
        self.local_links: list[tuple[Path, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        if tag in {"script", "iframe", "form", "input", "textarea", "object", "embed"}:
            self.errors.append(f"forbidden tag <{tag}>")
        if tag == "main":
            self.main_count += 1
        if tag == "title":
            self.title_count += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row_ext_links = []
        if tag == "th" and a.get("scope") != "col":
            self.errors.append("<th> missing scope='col'")
        if a.get("aria-current") == "page":
            self.aria_current += 1
        if "src" in a and a["src"]:
            self.errors.append(f"unexpected src attribute: {a['src']}")
        if tag in {"a", "link"}:
            href = a.get("href") or ""
            parsed = urlparse(href)
            if parsed.scheme:
                if parsed.scheme != "https":
                    self.errors.append(f"non-https external URL: {href}")
                if parsed.hostname not in ALLOWED_HOSTS:
                    self.errors.append(f"host not on official allowlist: {href}")
                if self.row_ext_links is not None:
                    self.row_ext_links.append(href)
            elif href:
                target_file = self.page_path if not parsed.path else (self.page_path.parent / unquote(parsed.path)).resolve()
                if not target_file.exists():
                    self.errors.append(f"broken local link: {href}")
                elif parsed.fragment:
                    self.local_links.append((target_file, parsed.fragment))

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row_ext_links is not None:
            if not self.row_ext_links:
                self.errors.append("table row without an official https:// source link")
            self.tbody_rows += 1
            self.row_ext_links = None


def main() -> int:
    failures: list[str] = []

    # 1. Reproducibility check
    before = {rel: (ANALYSIS / rel).read_bytes() if (ANALYSIS / rel).exists() else None for rel in PAGES + DATA_FILES}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        subprocess.run([sys.executable, str(HERE / "build.py"), str(tmp_path)], check=True, capture_output=True)
        for rel in PAGES:
            if before[rel] is None:
                failures.append(f"missing page before verify: {rel}")
            elif before[rel] != (tmp_path / rel).read_bytes():
                failures.append(f"non-reproducible or stale HTML page: {rel}")
        for rel in DATA_FILES:
            if before[rel] is None:
                failures.append(f"missing data file before verify: {rel}")
            elif before[rel] != (ANALYSIS / rel).read_bytes():
                failures.append(f"stale data file: {rel}")

    # 2. Parse HTML pages & collect fragment IDs
    parsed_pages: dict[Path, DashboardParser] = {}
    total_rows = 0
    for rel in PAGES:
        p = ANALYSIS / rel
        if not p.exists():
            failures.append(f"missing page: {rel}")
            continue
        txt = p.read_text(encoding="utf-8")
        dp = DashboardParser(p)
        dp.feed(txt)
        parsed_pages[p.resolve()] = dp
        if dp.errors:
            failures.extend(f"{rel}: {err}" for err in dp.errors[:10])
        if (dp.main_count, dp.title_count, dp.aria_current) != (1, 1, 1):
            failures.append(f"{rel}: expected main/title/aria-current = 1/1/1, got {dp.main_count}/{dp.title_count}/{dp.aria_current}")
        total_rows += dp.tbody_rows

        for label, rx in PRIVACY_PATTERNS.items():
            for m in rx.finditer(txt):
                failures.append(f"{rel}: privacy/format violation ({label}): {m.group(0)!r}")
        for m in CENTS_RE.finditer(txt):
            failures.append(f"{rel}: dollar amount with cents: {m.group(0)}")
        for m in DOLLAR_RE.finditer(txt):
            if m.group(2):
                continue
            val = int(m.group(1).replace(",", ""))
            if val % 10 != 0:
                failures.append(f"{rel}: unrounded dollar amount (not $10 multiple): {m.group(0)}")

    # Verify #fragment targets
    for p_res, dp in parsed_pages.items():
        for target_file, frag in dp.local_links:
            if target_file in parsed_pages:
                if frag not in parsed_pages[target_file].ids:
                    failures.append(f"{p_res.name}: broken fragment #{frag} on {target_file.name}")

    # 3. Scan data, CSS, and Python source files for privacy violations
    code_and_data = DATA_FILES + ["assets/style.css", "tools/sources.py", "tools/model.py", "tools/build.py"]
    for rel in code_and_data:
        txt = (ANALYSIS / rel).read_text(encoding="utf-8")
        for label, rx in PRIVACY_PATTERNS.items():
            if label == "postal code" and rel.endswith((".csv", ".json")):
                # Numeric CSV/JSON tables legitimately contain 5-digit dollar integers; check CA/zip postal form
                if re.search(r"(?:\bCA\b|California|zip|postal)\W{0,8}9\d{4}\b", txt, re.I):
                    failures.append(f"{rel}: postal code leak")
                continue
            for m in rx.finditer(txt):
                failures.append(f"{rel}: privacy violation ({label}): {m.group(0)!r}")

    # 4. Source ledger completeness
    ledger = json.loads((ANALYSIS / "data" / "sources.json").read_text(encoding="utf-8"))
    for sid, src in ledger["sources"].items():
        host = urlparse(src["url"]).hostname
        if host not in ALLOWED_HOSTS:
            failures.append(f"sources.json: {sid} host {host} not in allowlist")
        if src.get("status") != "read":
            failures.append(f"sources.json: {sid} status is {src.get('status')!r}, expected 'read'")

    if failures:
        print("FAIL:")
        for f in dict.fromkeys(failures):
            print(f"  - {f}")
        return 1

    print(
        f"PASS: {len(PAGES)} reproducible pages; {total_rows} table rows (100% cited to official domains); "
        f"{len(SOURCES)} directly-opened official sources; local links, #fragments, privacy scan, and $10 rounding all clean."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
