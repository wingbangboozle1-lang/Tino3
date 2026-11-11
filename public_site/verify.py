#!/usr/bin/env python3
"""Check reproducibility, exact source-to-row mapping, site links and public-data boundary.

Offline CI checks *pinned* data and citations; they cannot prove a future law or privately
verify a parcel. Publisher pages were opened manually on 11 November 2026 (ledger).
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = build.ROOT
PAGES = [x[0] for x in build.NAV]
ASSETS = ["assets/style.css", "assets/sources.json", "assets/data/reference_replay.csv",
          "assets/data/official_hpi_q2.csv", "assets/data/boe_ccpi_factors.csv"]
OFFICIAL_HOSTS = {
    "www.irs.gov", "leginfo.legislature.ca.gov", "www.sco.ca.gov", "www.ftb.ca.gov",
    "www.boe.ca.gov", "files.santaclaracounty.gov", "sftreasurer.org", "www.sf.gov",
    "www.insurance.ca.gov", "interactive.web.insurance.ca.gov", "www.cpuc.ca.gov",
    "fred.stlouisfed.org", "www.federalreserve.gov", "www.federalreservehistory.org",
    "www.bls.gov", "www.fdic.gov", "www.sfpuc.gov",
}
DOLLAR = re.compile(r"\$(\d{1,3}(?:,\d{3})+|\d+)(\.\d{1,2})?")
IDENTIFIERS = {
    "postal identifier": re.compile(r"\b9[45]\d{3}\b"),
    "parcel format": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "email address": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b", re.I),
    "specific place name": re.compile(r"\b(Cupertino|San Francisco|Outer Sunset|Santa Clara County)\b", re.I),
}


class Page(HTMLParser):
    def __init__(self, path: Path, ledger: dict):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ledger = ledger
        self.main = self.title = self.current = self.rows = 0
        self.in_tbody = False
        self.row_links: list[tuple[str, str]] | None = None
        self.errors: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag in {"script", "iframe", "form", "input", "textarea", "object", "embed"}:
            self.errors.append(f"forbidden element: {tag}")
        if tag == "main":
            self.main += 1
        if tag == "title":
            self.title += 1
        if a.get("aria-current") == "page":
            self.current += 1
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row_links = []
        if tag == "th" and a.get("scope") != "col":
            self.errors.append("table header without scope=col")
        if "src" in a:
            self.errors.append(f"embedded asset (none permitted): {a['src']}")
        if tag not in {"a", "link"}:
            return
        href = a.get("href", "") or ""
        parsed = urlparse(href)
        if parsed.scheme:
            if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
                self.errors.append(f"not an approved official HTTPS link: {href}")
            if tag == "a" and self.row_links is not None:
                sid = a.get("data-source", "") or ""
                if sid not in self.ledger or self.ledger.get(sid, {}).get("url") != href:
                    self.errors.append(f"table source id does not match ledger: {sid} {href}")
                self.row_links.append((sid, href))
            if tag == "a" and a.get("target") == "_blank" and not {"noopener", "noreferrer"}.issubset(
                (a.get("rel") or "").split()):
                self.errors.append("external tab without noopener noreferrer")
        else:
            target = (self.path.parent / unquote(parsed.path)).resolve() if parsed.path else self.path.resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                self.errors.append(f"missing or escaping local target: {href}")
            else:
                self.links.append((str(target), parsed.fragment))

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.row_links is not None:
            if not self.row_links:
                self.errors.append("table row without a linked official source")
            self.rows += 1
            self.row_links = None
        if tag == "tbody":
            self.in_tbody = False

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def check() -> None:
    problems: list[str] = []
    ledger = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))["sources"]
    if ledger != build.SOURCES:
        problems.append("compiled source ledger differs from original pinned ledger")
    for sid, source in ledger.items():
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
            problems.append(f"source {sid}: not a government/regulator/Federal Reserve publisher")
        if not source.get("checked") or not source.get("evidence"):
            problems.append(f"source {sid}: no checked evidence annotation")
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run([sys.executable, "public_site/build.py", temp], cwd=ROOT,
                       check=True, capture_output=True, text=True)
        for name in PAGES + ASSETS:
            if (ROOT / name).read_bytes() != (Path(temp) / name).read_bytes():
                problems.append(f"stale generated file: {name}")

    parsed_pages: dict[str, Page] = {}
    row_count = 0
    for name in PAGES:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        pg = Page(path, ledger)
        pg.feed(text)
        parsed_pages[str(path.resolve())] = pg
        row_count += pg.rows
        if (pg.main, pg.title, pg.current) != (1, 1, 1):
            problems.append(f"{name}: main/title/active-navigation counts {pg.main}/{pg.title}/{pg.current}")
        problems += [f"{name}: {err}" for err in pg.errors]
        # Scan *visible* page text, not official URLs whose path contains jurisdiction names.
        visible = ' '.join(pg.text)
        for label, pattern in IDENTIFIERS.items():
            if pattern.search(visible):
                problems.append(f"{name}: {label} in visible text")
        for match in DOLLAR.finditer(visible):
            amount = int(match.group(1).replace(",", ""))
            if match.group(2) or amount % 10:
                problems.append(f"{name}: unrounded dollar amount {match.group()}")
        # No embedded external assets, data collection, or browser-requesting scripts.
        if re.search(r"(?:<script|<form|<iframe)", text, re.I):
            problems.append(f"{name}: unexpected interactive element")
    for name, pg in parsed_pages.items():
        for target, fragment in pg.links:
            if fragment and target in parsed_pages and fragment not in parsed_pages[target].ids:
                problems.append(f"{name}: broken local fragment #{fragment} at {target}")

    # Check all 51 public replay rows and their source links; personal fields MUST be empty.
    with (ROOT / "assets/data/reference_replay.csv").open(newline="", encoding="utf-8") as f:
        recorded = list(csv.DictReader(f))
    expected = build.load_reference()
    if len(recorded) != 51:
        problems.append("50-year replay must contain 51 date labels including the baseline")
    for i, (row, ref) in enumerate(zip(recorded, expected)):
        for col, val in ref.items():
            if str(row[col]) != str(val):
                problems.append(f"replay row {i + 1}: {col} differs from pinned official inputs")
        if any(row[k] != "" for k in row if k.startswith("property_")):
            problems.append(f"replay row {i + 1}: household-specific amount filled")
        if row["hpi_source"] != ledger["fhfa_hpi"]["url"] or row["factor_source"] != ledger["ca_assess_history"]["url"]:
            problems.append(f"replay row {i + 1}: wrong official source link")
        for k in ("illustrative_assessed_per_million", "illustrative_one_percent_tax"):
            if int(row[k]) % 10:
                problems.append(f"replay row {i + 1}: {k} not $10 rounded")
    # Independently spot-check selected official observations; all other rows verified manually
    # against the original linked tables on 11 November 2026, not by extrapolation.
    hpi = {int(x["year"]): x["q2_index"] for x in csv.DictReader((ROOT / "assets/data/official_hpi_q2.csv").open())}
    factors = {int(x["assessment_year"]): (x["ccpi_pct"], x["factor"]) for x in csv.DictReader((ROOT / "assets/data/boe_ccpi_factors.csv").open())}
    if {y: hpi[y] for y in (1976, 1996, 2006, 2012, 2026)} != {
        1976: "50.31", 1996: "200.89", 2006: "643.96", 2012: "381.57", 2026: "974.97"}:
        problems.append("pinned official HPI checkpoint mismatch")
    if {y: factors[y] for y in (1980, 1983, 1995, 2010, 2021, 2026)} != {
        1980: ("17.316", "1.02"), 1983: ("1.033", "1.01"),
        1995: ("1.194", "1.0119"), 2010: ("-0.237", "0.99763"),
        2021: ("1.036", "1.01036"), 2026: ("3.307", "1.02")}:
        problems.append("pinned official BOE factor checkpoint mismatch")
    # All published assets must be free of identifiers; source URLs are public jurisdiction
    # references, so exclude them from place-name checks and never use a household ZIP.
    for name in ASSETS:
        text = (ROOT / name).read_text(encoding="utf-8")
        without_urls = re.sub(r"https://[^\s,\"<>]+", "", text)
        for label, pattern in IDENTIFIERS.items():
            if pattern.search(without_urls):
                problems.append(f"{name}: {label} in asset")
    # Source book may mention official exact public values; private values are never ingested.
    subprocess.run([sys.executable, "scripts/privacy_boundary.py"], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    subprocess.run([sys.executable, "scripts/package_site.py"], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("site_package", ROOT / "scripts/package_site.py")
    pkg = module_from_spec(spec)
    spec.loader.exec_module(pkg)
    allowed = set(PAGES + ASSETS) | set(pkg.retired_paths()) | {".nojekyll"}
    for p in (ROOT / "_site").rglob("*"):
        if not p.is_file():
            continue
        name = str(p.relative_to(ROOT / "_site"))
        if name not in allowed:
            problems.append(f"non-allowlisted file deployed: {name}")
        if name in pkg.retired_paths() and p.read_text(encoding="utf-8") != pkg.notice(name):
            problems.append(f"old URL not withdrawn: {name}")
    if problems:
        raise AssertionError("Verification failed:\n - " + "\n - ".join(dict.fromkeys(problems)))
    print(f"PASS: {len(PAGES)} reproducible pages, {row_count} individually cited rows, "
          f"{len(recorded)} normalized historical rows, {len(ledger)} manually opened official sources; "
          "blank household columns, $10 rounding, links, privacy boundary and Pages artifact clean.")
    print("Scope: this verifies pinned public evidence and site structure, not an unknown parcel, "
          "a future law or whether previous Git history has been removed.")


if __name__ == "__main__":
    check()
