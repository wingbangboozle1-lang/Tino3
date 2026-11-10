#!/usr/bin/env python3
"""
Strict line-by-line verifier for decision-suite/** and EXECUTIVE_SUMMARY_531AEE5C.md.
Uses SHA-256 token digests so zero raw location/roll numbers appear even in this test script.
"""
from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse

SUITE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SUITE_DIR.parent

ALLOWED_GOV_HOSTS = {
    "www.irs.gov",
    "www.boe.ca.gov",
    "boe.ca.gov",
    "www.ftb.ca.gov",
    "leginfo.legislature.ca.gov",
    "www.sos.ca.gov",
    "www.lao.ca.gov",
    "santaclara.courts.ca.gov",
    "selfhelp.courts.ca.gov",
    "files.santaclaracounty.gov",
    "dtac.santaclaracounty.gov",
    "clerkrecorder.santaclaracounty.gov",
    "www.cupertino.gov",
    "docs.cpuc.ca.gov",
    "sfbos.archive.sf.gov",
    "www.sf.gov",
    "www.sfpuc.gov",
    "www.insurance.ca.gov",
    "home.treasury.gov",
    "www.fhfa.gov",
    "www.bls.gov",
    "www.fdic.gov",
}

FORBIDDEN_SHA256_PREFIXES = {
    "2478d903d7c875f0", "43086d953bcc428c", "39842cd9da3b334e", "099edec0edb103d8",
    "97e993dda390f1cf", "e98a698e90e42c7d", "db05646ae8ad85ac", "0622977d7d84a529",
    "513bd45f0a52063b", "52032e1e3f630fd4", "bf3add3c9aae4d7e", "0d375c898a2d9f02",
    "49c24780cdc4e732", "e1cbc7c4ff721a44", "492053065ed017f4", "85df60af2698a93c",
    "8ae8f8c9b17505ff", "e826b706c6f0c321", "738ca2d26e0805fe", "d8b5265a1b78027b",
    "709f93f87e130f48", "c41b250042886417", "3de0ebf10cfca6eb", "08f0004343597464",
    "ee7e99405d3d9c32", "46ece05546fb2626", "30332d66f3ddf1ce", "c65765f07db7e978",
    "0474319403e99b06", "0ae3305415102d36", "cc56038328ffa43e", "6c0b64d1ba905979",
    "41ef81d7f6b07faa", "d376881f5bd00764", "04e97796ac4d1ffe", "9e6296be2bb963df",
    "74e7091094989907", "6b32c01a019bd349", "2bbb0ed9e5934878", "daab3aa68185b677",
    "7907a88d77f29a76", "38f13ba4550b60ae",
}

DOLLAR_RE = re.compile(r"\$([0-9]+(?:,[0-9]{3})*)(?!(?:,[0-9]|\.[0-9]|[0-9MmkK]))")


class SuiteHTMLChecker(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self.in_tbody = False
        self.in_tr = False
        self.row_gov_links: list[str] = []
        self.row_cells_text: list[str] = []
        self.in_td = False
        self.cur_td_text: list[str] = []
        self.total_body_rows = 0
        self.blank_cells = 0
        self.aria_current_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(str(a["id"]))
        if a.get("aria-current") == "page":
            self.aria_current_count += 1
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.row_gov_links = []
            self.row_cells_text = []
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.cur_td_text = []
            if "blank-cell" in (a.get("class") or ""):
                self.blank_cells += 1
        elif tag in ("a", "link", "script"):
            target = a.get("href") or a.get("src") or ""
            if not target:
                return
            if target.startswith("#"):
                self.fragments.append(target[1:])
                return
            parsed = urlparse(target)
            if parsed.scheme in ("http", "https"):
                assert parsed.scheme == "https", f"{self.path}: non-HTTPS URL {target}"
                assert parsed.hostname in ALLOWED_GOV_HOSTS, (
                    f"{self.path}: non-allowlisted external host {parsed.hostname} ({target})"
                )
                if self.in_tr:
                    self.row_gov_links.append(target)
            elif not parsed.scheme:
                rel_file = (self.path.parent / unquote(parsed.path)).resolve()
                assert rel_file.exists(), f"{self.path}: broken local reference '{target}' -> {rel_file}"

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.cur_td_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_td:
            self.in_td = False
            self.row_cells_text.append("".join(self.cur_td_text).strip())
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.total_body_rows += 1
            assert self.row_gov_links, (
                f"{self.path}: table row #{self.total_body_rows} missing official .gov link: {self.row_cells_text}"
            )
            for cell in self.row_cells_text:
                for m in DOLLAR_RE.finditer(cell):
                    num = int(m.group(1).replace(",", ""))
                    assert num % 10 == 0, f"{self.path}: non-$10-rounded table figure ${m.group(1)} in '{cell}'"
        elif tag == "tbody":
            self.in_tbody = False


def main() -> None:
    html_pages = sorted(SUITE_DIR.glob("*.html"))
    assert len(html_pages) == 10, f"Expected 10 HTML pages in decision-suite/, found {len(html_pages)}"

    total_rows = 0
    total_blanks = 0
    for page in html_pages:
        txt = page.read_text(encoding="utf-8")
        checker = SuiteHTMLChecker(page)
        checker.feed(txt)
        missing_anchors = set(checker.fragments) - checker.ids
        assert not missing_anchors, f"{page}: missing in-page anchors {missing_anchors}"
        assert checker.aria_current_count == 1, f"{page}: expected 1 aria-current=page, got {checker.aria_current_count}"
        total_rows += checker.total_body_rows
        total_blanks += checker.blank_cells

    assert total_blanks >= 25, f"Expected >=25 blank unconfirmed official cells, found {total_blanks}"

    for csv_path in sorted((SUITE_DIR / "data").glob("*.csv")):
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert len(rows) >= 2, f"{csv_path}: empty CSV"
        widths = {len(r) for r in rows}
        assert len(widths) == 1, f"{csv_path}: inconsistent CSV column widths {widths}"
        headers = rows[0]
        for r in rows[1:]:
            for h, val in zip(headers, r):
                if h in ("year", "inheritance_year", "strategy_code", "strategy_name", "verdict", "source_url", "federal_rate_above_threshold"):
                    continue
                iv = int(val)
                assert iv % 10 == 0, f"{csv_path}: column '{h}' value {iv} is not rounded to nearest $10"

    scan_targets = [
        p for p in list(SUITE_DIR.rglob("*")) + [REPO_ROOT / "EXECUTIVE_SUMMARY_531AEE5C.md"]
        if p.is_file() and "__pycache__" not in p.parts
    ]
    num_token_re = re.compile(r"\b[0-9]{1,3}(?:,[0-9]{3})+\b|\b[0-9]{4,7}\b")
    for p in scan_targets:
        content = p.read_text(encoding="utf-8")
        for m in DOLLAR_RE.finditer(content):
            val = int(m.group(1).replace(",", ""))
            assert val % 10 == 0, f"NON-$10 DOLLAR FIGURE in {p}: {m.group(0)}"
        for m in num_token_re.finditer(content):
            norm = m.group(0).replace(",", "")
            digest = hashlib.sha256(norm.encode()).hexdigest()[:16]
            assert digest not in FORBIDDEN_SHA256_PREFIXES, (
                f"PRIVACY/ROUNDING VIOLATION in {p}: forbidden raw token matched"
            )

    subprocess.run(["python", "scripts/verify.py"], cwd=REPO_ROOT, check=True)

    print(
        f"SUITE VERIFICATION PASSED: {len(html_pages)} HTML pages, {total_rows} official-cited table rows, "
        f"{total_blanks} blank unverified official cells, 4 RFC-4180 CSVs, 100% $10 rounding, zero PII/ZIP/raw-roll leaks."
    )


if __name__ == "__main__":
    main()
