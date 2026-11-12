"""Verify that the deployable artifact contains only approved pages and generic notices."""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from package_site import ASSETS, NOJEKYLL, PAGES, SITE, notice_content, retired_paths

ROOT = Path(__file__).resolve().parents[1]

# Identifiers that must never be present in the public artifact. Their checks complement—not
# replace—the path allowlist: rounded figures are not treated as anonymous data.
FORBIDDEN = {
    "known local place name": re.compile(r"\b(Cupertino|San Francisco|Outer Sunset|Sunnyvale|Santa Clara)\b", re.I),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "postal code": re.compile(r"(?:\bCA\b|California|zip|postal code)\W{0,6}9\d{4}\b", re.I),
    "parcel or APN": re.compile(r"\b\d{3}-\d{2,3}-\d{2,3}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Way|Lane|Ln|Boulevard|Blvd|Court|Ct)\b"),
}
FORBIDDEN_ELEMENTS = re.compile(r"<(?:script|iframe|form|input|textarea|object|embed)\b", re.I)
CURRENCY_AMOUNT = re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?")
# Only general, officially sourced 2026/2027 federal thresholds are allowed in this edition.
# Add a future legal threshold only after checking its official source and scope.
ALLOWED_GENERAL_CURRENCY = {"$15,000,000", "$15,480,000", "$20,000"}


def artifact_files() -> set[str]:
    if not SITE.is_dir():
        raise SystemExit("_site is missing; run scripts/package_site.py before the privacy check")
    return {
        path.relative_to(SITE).as_posix()
        for path in SITE.rglob("*")
        if path.is_file()
    }


def verify() -> int:
    retired = retired_paths()
    expected = set(PAGES + ASSETS + retired + [NOJEKYLL])
    actual = artifact_files()
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected or missing:
        raise SystemExit(f"Artifact path boundary failed: unexpected={unexpected}, missing={missing}")

    if (SITE / NOJEKYLL).read_bytes() != b"":
        raise SystemExit(".nojekyll must be an empty marker file")

    for name in actual:
        for label, pattern in FORBIDDEN.items():
            if pattern.search(name):
                raise SystemExit(f"Possible {label} in public artifact path {name}")

    for name in retired:
        path = SITE.joinpath(*PurePosixPath(name).parts)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SystemExit(f"Withdrawal route is not readable text: {name}: {exc}") from exc
        if content != notice_content(PurePosixPath(name)):
            raise SystemExit(f"Retired path contains non-generic content: {name}")

    scanned = 0
    for name in PAGES + ASSETS:
        path = SITE / name
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SystemExit(f"Public allowlisted file is not readable text: {name}: {exc}") from exc
        scanned += 1
        for label, pattern in FORBIDDEN.items():
            match = pattern.search(content)
            if match:
                raise SystemExit(f"Possible {label} in public artifact {name}")
        for amount in CURRENCY_AMOUNT.findall(content):
            if amount.replace(" ", "") not in ALLOWED_GENERAL_CURRENCY:
                raise SystemExit(f"Unapproved monetary amount in public artifact {name}")
        if name.endswith(".html") and FORBIDDEN_ELEMENTS.search(content):
            raise SystemExit(f"Interactive or remote-code element found in public page {name}")

    print(
        f"PASS: {len(PAGES)} allowlisted pages and {len(ASSETS)} runtime asset scanned; "
        f"{len(retired)} non-allowlisted routes are exact content-free withdrawal notices."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(verify())
