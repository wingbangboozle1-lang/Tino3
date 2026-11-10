"""Checks run before every publication. Exits non-zero on the first category that fails.

1. Reproducible: rebuilding from plan/ gives byte-identical published files.
2. Sourced: every table row links to at least one official source.
3. Blank when unverified: an unverified row outside the review and source pages shows a dash and a flag.
4. Links: every internal link and anchor resolves; every external link is https and official.
5. Rounding: every dollar amount is a multiple of $10 (statutory rates and one statutory amount excepted).
6. Privacy: no postal code, no place name below county level, roll-derived inputs are coarse.
7. Local only: if private/inputs.json exists, none of its figures appears in any tracked file.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import build_site  # noqa: E402
import sitekit  # noqa: E402

ALLOWED_ODD_AMOUNTS = {"1,044,586", "0.55", "1.10", "3.75", "11.25"}
# Salted hashes of place names that must not appear (the names themselves are not stored here).
SALT = "tino3-plan"
FORBIDDEN_WORD_HASHES = {
    "a1152c936ca527bfee4e1ac24b0e9730146af45d4c1cf2afbff6fb3a3306f63d",
    "f2920c0f3bf7833c8768fcf4b2c4cb8224f38d2846cde835ff4e0ab027fde467",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def visible(html_text: str) -> str:
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return unescape(t)


def official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return url.startswith("https://") and any(host == d or host.endswith("." + d) for d in sitekit.OFFICIAL_DOMAINS)


def word_hash(w: str) -> str:
    return hashlib.sha256((SALT + w.lower()).encode()).hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "plan" / "data" / "manifest.json").read_text(encoding="utf-8"))
    published = manifest["published"]

    # 1. reproducible ---------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = build_site.build(Path(tmp))
        if rebuilt != published:
            fail("manifest differs from a fresh build")
        for name in rebuilt + ["plan/data/manifest.json", "plan/data/model_outputs.json"]:
            a, b = Path(tmp) / name, ROOT / name
            if not b.exists() or a.read_bytes() != b.read_bytes():
                fail(f"not reproducible: {name}")

    pages = [n for n in published if n.endswith(".html")]
    ids_by_page = {}
    for name in pages:
        ids_by_page[name] = set(re.findall(r'id="([^"]+)"', (ROOT / name).read_text(encoding="utf-8")))

    rows_total = 0
    for name in pages:
        text = (ROOT / name).read_text(encoding="utf-8")
        # 2 + 3. rows ----------------------------------------------------------------------
        for m in re.finditer(r'<tr data-status="([a-z]+)">(.*?)</tr>', text, flags=re.S):
            rows_total += 1
            status, row = m.group(1), m.group(2)
            links = re.findall(r'<a class="src" href="([^"]+)"', row)
            if not links or not all(official(unescape(u)) for u in links):
                fail(f"{name}: row without an official source: {visible(row)[:80]}")
            if status == "unverified" and name not in ("review.html", "sources.html"):
                if "<td>—</td>" not in row or 'class="flag"' not in row:
                    fail(f"{name}: unverified row must be blank and flagged: {visible(row)[:80]}")
        # 4. links ---------------------------------------------------------------------------
        for u in re.findall(r'(?:href|src)="([^"]+)"', text):
            u = unescape(u)
            if u.startswith("http"):
                if not official(u):
                    fail(f"{name}: external link is not an official https source: {u}")
                continue
            if u.startswith("#"):
                if u[1:] not in ids_by_page[name]:
                    fail(f"{name}: missing anchor {u}")
                continue
            target, _, anchor = u.partition("#")
            if target not in published:
                fail(f"{name}: broken link {u}")
            elif anchor and anchor not in ids_by_page.get(target, set()):
                fail(f"{name}: broken anchor {u}")
        # 5. rounding ------------------------------------------------------------------------
        vis = visible(text)
        for mm in re.finditer(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)", vis):
            amt = mm.group(1).rstrip(",")
            if amt in ALLOWED_ODD_AMOUNTS or vis[mm.end():mm.end() + 8].strip().startswith("million"):
                continue
            if "." in amt or int(amt.replace(",", "")) % 10:
                fail(f"{name}: amount not in $10 steps: ${amt}")
        # 6. privacy -------------------------------------------------------------------------
        for z in re.findall(r"(?<![\d,.$])9\d{4}(?![\d,])", vis):
            fail(f"{name}: five-digit number that looks like a postal code: {z}")
        for w in set(re.findall(r"[A-Za-z]{4,}", vis)):
            if word_hash(w) in FORBIDDEN_WORD_HASHES:
                fail(f"{name}: forbidden place name present")

    md = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    for amt in re.findall(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)", md):
        amt = amt.rstrip(",")
        if "." in amt or int(amt.replace(",", "")) % 10:
            fail(f"EXECUTIVE_SUMMARY.md: amount not in $10 steps: ${amt}")

    for name in [n for n in published if n.endswith(".csv")]:
        rdr = csv.DictReader(io.StringIO((ROOT / name).read_text(encoding="utf-8")))
        for rec in rdr:
            for k, v in rec.items():
                if "year" in k or not re.fullmatch(r"-?\d+", v or ""):
                    continue
                if int(v) % 10:
                    fail(f"{name}: {k}={v} is not in $10 steps")

    inp = json.loads((ROOT / "plan" / "data" / "inputs_public.json").read_text(encoding="utf-8"))
    for key in ("property_a", "property_b"):
        if inp[key]["assessed_value_base_year"] % 10000 or inp[key]["fixed_charges"] % 100:
            fail(f"inputs_public.json: {key} roll-derived inputs must be coarse (assessed value to $10,000, charges to $100)")

    # 7. local-only scan against the owner's exact figures ---------------------------------
    private = ROOT / "private" / "inputs.json"
    if private.exists():
        series = json.loads(private.read_text(encoding="utf-8")).get("_private_series", {})
        needles = set(series.get("strings", []))
        for key in ("a_assessed", "b_assessed"):
            for n in series.get(key, []):
                r = int((n + 5) // 10 * 10)
                needles |= {str(n), f"{n:,}", str(r), f"{r:,}"}
        for key in ("a_tax", "b_tax"):
            for n in series.get(key, []):
                if n % 10:
                    needles |= {str(n), f"{n:,}"}
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        for name in tracked:
            body = (ROOT / name).read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if re.search(r"(?<![\d,.])" + re.escape(needle) + r"(?![\d,])", body):
                    fail(f"{name}: contains a private figure or place name")
                    break
        print(f"local private scan: {len(needles)} needles checked against {len(tracked)} tracked files")

    if errors:
        print("\n".join("FAIL: " + e for e in errors[:60]))
        raise SystemExit(f"{len(errors)} check(s) failed")
    print(f"PASS: {len(pages)} pages, {rows_total} table rows each with an official source link, "
          f"{len(published)} published files reproducible, links, rounding and privacy rules hold.")


if __name__ == "__main__":
    main()
