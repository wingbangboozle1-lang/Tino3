"""Fail closed: identifiers must not appear in the published edition, in data or in links.

The public pages use placeholders (Property A, Property B, County A, City B). A rounded figure is
not treated as anonymous, so the checks below look for the direct identifiers, for the specific
jurisdictions this household is in, and for URLs whose host or path would disclose them.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from package_site import ASSETS, NOJEKYLL, PAGES, SITE, notice_content, retired_paths

ROOT = Path(__file__).resolve().parents[1]

# Text patterns. These are direct identifiers or location clues.
FORBIDDEN = {
    "known local place name": re.compile(
        r"\b(?:Cupertino|San Francisco|San Jose|Sunnyvale|Santa Clara|Outer Sunset|Marin|Alameda)\b", re.I),
    # A bare five-digit number is a legitimate figure in the data files, so the postal-code
    # check needs a locational context rather than a bare digit run.
    "postal code": re.compile(r"(?:\bCA\b|California|\bzip\b|postal code)\W{0,8}9[45]\d{3}\b", re.I),
    "parcel or APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(
        r"\b\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}"),
}

# A URL is a disclosure too: its host or path can name the jurisdiction even when the page text
# does not. Only official publishers on these hosts may be linked, and none of them may carry a
# local-jurisdiction marker in the host name or path.
OFFICIAL_HOST_SUFFIXES = (
    ".gov", ".ca.gov", "ca.gov", "irs.gov", "fred.stlouisfed.org", "tsp.gov", "huduser.gov",
    "federalreservehistory.org", "newyorkfed.org", "leginfo.legislature.ca.gov", "govinfo.gov",
)
FORBIDDEN_URL_MARKERS = re.compile(
    r"(?:santaclara|sccgov|sfgov|sf\.gov|sftreasurer|sfbos|sanfrancisco|cupertino|sunnyvale|"
    r"ATNHPIUS41940|ATNHPIUS41884|41940|41884|95014|94122)", re.I)

# Elements that would make this an application rather than a static document.
FORBIDDEN_ELEMENTS = re.compile(r"<(?:script|iframe|form|input|textarea|object|embed)\b", re.I)


def is_official(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == suffix or host.endswith("." + suffix.lstrip(".")) or host.endswith(suffix)
               for suffix in OFFICIAL_HOST_SUFFIXES)


def scan(text: str, where: str) -> list[str]:
    problems = []
    for label, pattern in FORBIDDEN.items():
        match = pattern.search(text)
        if match:
            problems.append(f"possible {label} in {where}: {match.group(0)!r}")
    if FORBIDDEN_ELEMENTS.search(text):
        problems.append(f"interactive element in {where}")
    return problems


def urls_in(text: str) -> set[str]:
    return set(re.findall(r'href="(https?://[^"]+)"', text))


def verify() -> int:
    retired = retired_paths()
    expected = set(PAGES + ASSETS + retired + [NOJEKYLL])
    actual = {path.relative_to(SITE).as_posix() for path in SITE.rglob("*") if path.is_file()}
    if actual - expected or expected - actual:
        raise SystemExit(
            f"Artifact path boundary failed: unexpected={sorted(actual - expected)}, "
            f"missing={sorted(expected - actual)}")

    if (SITE / NOJEKYLL).read_bytes() != b"":
        raise SystemExit(".nojekyll must be an empty marker file")

    problems: list[str] = []
    for name in actual:
        problems += scan(name, f"artifact path {name}")

    # Retired routes must be byte-identical to the generic notice: no figures can survive there.
    for name in retired:
        path = SITE.joinpath(*name.split("/"))
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SystemExit(f"Withdrawal route is not readable text: {name}: {exc}") from exc
        if content != notice_content(__import__("pathlib").PurePosixPath(name)):
            raise SystemExit(f"Retired path contains non-generic content: {name}")

    linked: set[str] = set()
    for name in PAGES + ASSETS:
        path = SITE / name
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SystemExit(f"Public file is not readable text: {name}: {exc}") from exc
        problems += scan(content, name)
        for url in urls_in(content):
            linked.add(url)
            if not url.startswith("https://") or not is_official(url):
                problems.append(f"non-official host linked from {name}: {url}")
            if FORBIDDEN_URL_MARKERS.search(url):
                problems.append(f"jurisdiction-identifying URL in {name}: {url}")

    # The ledger is the single source of truth for citations, so it is held to the same rule.
    ledger = json.loads((ROOT / "assets" / "sources.json").read_text(encoding="utf-8"))
    for sid, source in ledger["sources"].items():
        if not is_official(source["url"]):
            problems.append(f"ledger entry is not an official publisher: {sid}")
        if FORBIDDEN_URL_MARKERS.search(source["url"]):
            problems.append(f"ledger URL identifies the jurisdiction: {sid}")

    if problems:
        print("FAIL")
        for item in dict.fromkeys(problems):
            print("  -", item)
        return 1
    print(
        f"PASS: {len(PAGES)} published pages and {len(ASSETS)} runtime assets scanned for identifiers; "
        f"{len(retired)} retired routes are exact content-free notices; {len(linked)} external links "
        f"and {len(ledger['sources'])} ledger entries are on official publishers with no local marker."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(verify())
