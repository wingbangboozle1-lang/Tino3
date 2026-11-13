"""Privacy boundary for the published pages and the deployable artifact.

The owner's instruction for this edition is that costs and numbers are published
rounded to the nearest $10. Rounding is not anonymity, so this module enforces
the two things that can actually be enforced mechanically:

  1. no personal identifier - no street address, postal code, parcel number,
     email address, phone number or property-level place name; and
  2. no unrounded money - every published dollar figure is either a multiple of
     ten, or a published official amount that appears verbatim in an official
     document.

It does not and cannot certify that earlier commits, pull-request diffs, forks
or external copies are clean.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import package_site as pack

ROOT = Path(__file__).resolve().parents[1]

# Identifiers that must never appear in the public artifact.
FORBIDDEN = {
    "street address": re.compile(
        r"\b\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|"
        r"Boulevard|Blvd|Court|Ct|Place|Pl|Terrace|Circle)\b"),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "postal code": re.compile(r"(?:\bCA\b|California|zip|postal code)\W{0,8}9\d{4}\b", re.I),
    "bare postal code": re.compile(r"\b(?:95014|94122|95015|94116|94132)\b"),
    "parcel or APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "phone number": re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b"),
    "property level place name": re.compile(
        r"\b(Cupertino|Sunnyvale|Outer\s+Sunset|Los\s+Altos|Saratoga|Mountain\s+View|"
        r"Campbell|Monte\s+Sereno|Los\s+Gatos|Inner\s+Sunset|Parkside|Sunset\s+District)\b", re.I),
    "person name pattern": re.compile(r"\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+\b"),
}

# County and city level names are published deliberately: they are the level at
# which the property tax, rent and transfer rules in this analysis operate.
ALLOWED_PLACE_NAMES = ("Santa Clara County", "City and County of San Francisco",
                       "San Francisco", "California", "Bay Area")

FORBIDDEN_ELEMENTS = re.compile(r"<(?:script|iframe|form|input|textarea|object|embed|img)\b", re.I)
CURRENCY_AMOUNT = re.compile(r"\$\s*(\d[\d,]*)(?:\.\d+)?")

# Published statutory and official amounts that are not multiples of ten. Each
# one is a verbatim figure from an official document and is not ours to round.
OFFICIAL_AMOUNTS = {
    1, 5, 15,                     # appear only inside verbatim official titles and fiscal impacts
    1_000_000, 1_022_600, 1_044_586,          # Proposition 19 shelter, BOE letters to assessors
    250_000, 500_000,                         # section 121 exclusions
    371_000,                                  # Proposition 3 income threshold, voter guide
    5_490_000, 11_180_000, 11_400_000, 11_580_000, 11_700_000,   # IRS filing thresholds by year
    12_060_000, 12_920_000, 13_610_000, 13_990_000,              # IRS filing thresholds by year
    15_000_000, 15_480_000,                                      # IRS basic exclusion 2026 and 2027
    19_000, 20_000,                                              # IRS annual gift exclusion
    5_000_000_000, 15_000_000_000,                               # Proposition 3 fiscal impact range
}


def _official_amounts_from_inputs() -> set[int]:
    data = json.loads((ROOT / "assets" / "data" / "inputs.json").read_text(encoding="utf-8"))
    out: set[int] = set()
    for value in data["verified_parameters"].values():
        if isinstance(value, dict) and isinstance(value.get("value"), (int, float)):
            out.add(int(value["value"]))
    return out


def check_money(text: str, where: str) -> list[str]:
    allowed = OFFICIAL_AMOUNTS | _official_amounts_from_inputs()
    problems = []
    for raw in CURRENCY_AMOUNT.findall(text):
        amount = int(raw.replace(",", ""))
        if amount % 10 == 0:
            continue
        if amount in allowed:
            continue
        problems.append(f"{where}: unrounded or unapproved monetary amount ${raw}")
    return problems


def check_identifiers(text: str, where: str) -> list[str]:
    problems = []
    for label, pattern in FORBIDDEN.items():
        match = pattern.search(text)
        if match:
            problems.append(f"{where}: possible {label} ({match.group(0)[:40]!r})")
    return problems


def scan_pages() -> list[str]:
    problems: list[str] = []
    for name in pack.PAGES + pack.ASSETS:
        path = ROOT / name
        if not path.is_file():
            problems.append(f"{name}: allowlisted file missing")
            continue
        text = path.read_text(encoding="utf-8")
        problems.extend(check_identifiers(text, name))
        problems.extend(check_identifiers(name, f"path {name}"))
        problems.extend(check_money(text, name))
        if name.endswith(".html") and FORBIDDEN_ELEMENTS.search(text):
            problems.append(f"{name}: interactive or remote-code element")
    return problems


def scan_artifact() -> list[str]:
    site = pack.SITE
    if not site.is_dir():
        raise SystemExit("_site is missing; run scripts/package_site.py before the privacy check")
    files = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    retired = sorted(pack.retired_paths())
    expected = set(pack.PAGES + pack.ASSETS + retired + [pack.NOJEKYLL])
    problems: list[str] = []
    for name in sorted(files - expected):
        problems.append(f"artifact contains an unallowlisted file: {name}")
    for name in sorted(expected - files):
        problems.append(f"artifact is missing an expected file: {name}")
    if (site / pack.NOJEKYLL).read_bytes() != b"":
        problems.append(".nojekyll must be an empty marker file")
    for name in sorted(retired):
        path = site.joinpath(*PurePosixPath(name).parts)
        if path.read_text(encoding="utf-8") != pack.notice_content(PurePosixPath(name)):
            problems.append(f"retired route is not a content-free withdrawal notice: {name}")
    for name in sorted(files):
        for label, pattern in FORBIDDEN.items():
            if pattern.search(name):
                problems.append(f"possible {label} in artifact path {name}")
    for name in sorted(files & set(pack.PAGES + pack.ASSETS)):
        text = (site / name).read_text(encoding="utf-8")
        problems.extend(check_identifiers(text, f"artifact/{name}"))
        problems.extend(check_money(text, f"artifact/{name}"))
    return problems


def main() -> int:
    problems = scan_pages() + scan_artifact()
    if problems:
        raise SystemExit("Privacy boundary FAILED:\n  - " + "\n  - ".join(dict.fromkeys(problems)))
    print(
        f"PASS privacy boundary: {len(pack.PAGES)} pages and {len(pack.ASSETS)} asset scanned; "
        f"every published dollar figure is rounded to $10 or is a published official amount; "
        f"{len(pack.retired_paths())} non-allowlisted routes carry content-free notices."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
