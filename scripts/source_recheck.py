"""Re-request every official source the published ledger cites.

The publication gate (scripts/verify.py) proves that each published table row carries a
link to an approved official host, that the link is https and that it resolves inside the
built artifact. It never asks the publisher's own server whether the page is still there.
This script does that second job: it re-reads assets/sources.json and requests each URL
the ledger already publishes, then reports what came back.

Design rules, chosen so that this can run on a schedule without ever becoming a hazard:

  * Report-only. A dead, moved, refused or unreachable source is a finding, not a build
    failure, so the default exit status is 0 even when everything is broken. `--strict`
    is available for a local check that is meant to fail.
  * It adds no host and no URL. It requests exactly the URLs in the ledger, which
    scripts/verify.py has already confined to the approved official host list.
  * A refused request (401, 403, 429) is reported separately from a missing page
    (404, 410). A bot policy is not evidence that a published page has vanished, and
    this script says so instead of collapsing the two into "dead link".
  * The "recorded read date" is the latest date written in the ledger's own `checked`
    field after parenthetical content is removed, because that field mixes read dates
    with content dates. When no date survives that rule the entry is reported as having
    no recorded read date rather than being assigned one.

Usage:
    python3 scripts/source_recheck.py                 # recheck the whole ledger
    python3 scripts/source_recheck.py --limit 5       # first five entries
    python3 scripts/source_recheck.py --host bls.gov  # one host only
    python3 scripts/source_recheck.py --probe URL     # single-URL connectivity test
    python3 scripts/source_recheck.py --strict        # exit 1 when a source is not reachable
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "assets" / "sources.json"

# Honest identification: a publisher that refuses this user agent is reported as
# refusing, not as missing. No personal or property identifier is carried.
USER_AGENT = "source-recheck/1.0 (scheduled link-integrity check; planning repository)"

TIMEOUT = 25
WORKERS = 8
READ_BYTES = 2048

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}

ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
PROSE_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(20\d{2})\b", re.I)
PARENTHETICAL = re.compile(r"\([^()]*\)")


def annotation_escape(text: str) -> str:
    """Escape a value for a GitHub Actions workflow-command annotation."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def recorded_read_date(checked: str) -> dt.date | None:
    """Latest date the `checked` field records as a read date, or None.

    Parenthetical content is removed first: the ledger's own field carries quoted
    data windows in parentheses, and those are content dates, not read dates.
    """
    stripped = PARENTHETICAL.sub(" ", checked or "")
    found: list[dt.date] = []
    for m in ISO_DATE.finditer(stripped):
        try:
            found.append(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            continue
    for m in PROSE_DATE.finditer(stripped):
        month = MONTHS[m.group(2).lower()]
        try:
            found.append(dt.date(int(m.group(3)), month, int(m.group(1))))
        except ValueError:
            continue
    return max(found) if found else None


def classify(status: int | None, error: str | None) -> str:
    if error:
        return "unreachable"
    if status is None:
        return "unreachable"
    if 200 <= status < 300:
        return "reachable"
    if status in (401, 403, 429, 407, 451):
        return "refused"
    if status in (404, 410, 451):
        return "missing"
    if 400 <= status < 600:
        return "error"
    return "reachable"


def fetch(url: str) -> dict:
    """Request one URL and return a flat result record. Never raises."""
    result = {
        "url": url,
        "status": None,
        "final_url": url,
        "outcome": "unreachable",
        "error": "",
        "bytes": 0,
    }
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
            body = response.read(READ_BYTES)
            result["status"] = getattr(response, "status", None) or response.getcode()
            result["final_url"] = response.geturl()
            result["bytes"] = len(body)
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        result["final_url"] = exc.url or url
        result["error"] = f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - every failure mode is a reported finding
        result["error"] = f"{type(exc).__name__}: {exc}"[:200]
    result["outcome"] = classify(result["status"], result["error"] or None)
    return result


def build_report(entries: list[dict], results: list[dict], stale_days: int,
                 today: dt.date) -> tuple[str, dict]:
    by_id = {r["url"]: r for r in results}
    hosts = sorted({urlsplit(e["url"]).netloc for e in entries})
    counts: dict[str, int] = {}
    attention: list[list[str]] = []
    recheck_due: list[list[str]] = []
    no_date = 0

    for entry in entries:
        r = by_id[entry["url"]]
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
        read_date = recorded_read_date(entry.get("checked", ""))
        if read_date is None:
            no_date += 1
            age = None
        else:
            age = (today - read_date).days
        moved = r["final_url"] != entry["url"]
        if r["outcome"] != "reachable" or moved:
            note = r["error"] or ("redirected" if moved else "")
            if moved:
                note = (note + "; final URL differs from the ledger" if note
                        else "redirected; final URL differs from the ledger")
            attention.append([
                str(entry.get("id", "")), str(entry.get("publisher", ""))[:44],
                str(r["status"] or "-"), r["outcome"],
                (r["final_url"] if moved else ""), note,
            ])
        if age is None or age > stale_days:
            recheck_due.append([
                str(entry.get("id", "")), str(entry.get("publisher", ""))[:44],
                read_date.isoformat() if read_date else "not recorded",
                str(age) if age is not None else "-",
                "no read date in the ledger's checked field" if age is None
                else f"last read {age} days ago",
            ])

    lines: list[str] = []
    lines.append("# Official source recheck")
    lines.append("")
    lines.append(f"- Run (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- Ledger entries requested: {len(entries)} of "
                 f"{len(json.loads(LEDGER.read_text(encoding='utf-8'))['sources'])}")
    lines.append(f"- Distinct hosts requested: {len(hosts)} (every host already on the "
                 "approved official list in scripts/verify.py; none added)")
    lines.append(f"- Recorded read date missing: {no_date} entries")
    lines.append("")
    lines.append("## What came back")
    lines.append("")
    lines.append("| Outcome | Entries | Meaning |")
    lines.append("|---|---|---|")
    meanings = {
        "reachable": "the publisher answered 2xx",
        "refused": "401/403/429: a bot policy, not evidence the page is gone",
        "missing": "404 or 410: the published URL no longer resolves",
        "error": "another 4xx/5xx from the publisher",
        "unreachable": "DNS, TLS, timeout or connection failure from this runner",
    }
    for key in ("reachable", "refused", "missing", "error", "unreachable"):
        lines.append(f"| {key} | {counts.get(key, 0)} | {meanings[key]} |")
    lines.append("")
    if attention:
        lines.append("## Sources needing a human look")
        lines.append("")
        lines.append("| Ledger id | Publisher | HTTP | Outcome | Final URL | Note |")
        lines.append("|---|---|---|---|---|---|")
        for row in attention:
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    lines.append(f"## Recheck due (no recorded read date, or older than {stale_days} days)")
    lines.append("")
    if recheck_due:
        lines.append("| Ledger id | Publisher | Recorded read date | Days ago | Note |")
        lines.append("|---|---|---|---|---|")
        for row in recheck_due:
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Limits of this run")
    lines.append("")
    lines.append("- A refused request means the publisher's bot policy, not a dead page: "
                 "open the URL in a browser before treating it as gone.")
    lines.append("- This checks availability only. It cannot tell whether the *content* of "
                 "a page changed; that still needs a person to re-read the document and "
                 "restate what it says, as the ledger's `checked` field records.")
    lines.append("- The run is report-only by design: no gate, build or deployment depends "
                 "on its result.")
    lines.append("")
    summary = {"requested": len(entries), "counts": counts,
               "attention": len(attention), "recheck_due": len(recheck_due),
               "no_recorded_date": no_date,
               "attention_ids": [row[0] for row in attention[:8]]}
    return "\n".join(lines), summary


def run_recheck(args: argparse.Namespace) -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = list(ledger["sources"])
    if args.host:
        entries = [e for e in entries if urlsplit(e["url"]).netloc == args.host]
        if not entries:
            print(f"No ledger entry publishes a URL on host {args.host}.", file=sys.stderr)
            return 1
    if args.limit:
        entries = entries[: args.limit]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(lambda e: fetch(e["url"]), entries))

    today = dt.date.today()
    report, summary = build_report(entries, results, args.stale_days, today)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
        print(f"(report written to {args.out})", file=sys.stderr)
    print(f"SUMMARY {json.dumps(summary, sort_keys=True)}", file=sys.stderr)
    if args.annotate:
        counts = summary["counts"]
        message = (
            f"requested={summary['requested']} "
            f"reachable={counts.get('reachable', 0)} "
            f"refused={counts.get('refused', 0)} "
            f"missing={counts.get('missing', 0)} "
            f"error={counts.get('error', 0)} "
            f"unreachable={counts.get('unreachable', 0)}; "
            f"needing a human look={summary['attention']}; "
            f"recheck due={summary['recheck_due']}; "
            f"no recorded read date={summary['no_recorded_date']}"
        )
        print(f"::notice title=Official source recheck::{annotation_escape(message)}")
        if summary["attention_ids"]:
            print("::warning title=Sources needing a human look::"
                  + annotation_escape(", ".join(summary["attention_ids"])))
    if args.strict and (summary["attention"] or summary["recheck_due"]):
        return 1
    return 0


def run_probe(args: argparse.Namespace) -> int:
    """Single-URL connectivity test, used to prove the fetch path where the
    sandbox's outbound allow-list reaches only a subset of the ledger's hosts."""
    result = fetch(args.probe)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] == "reachable" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=0, help="check only the first N entries")
    parser.add_argument("--host", default="", help="check only entries published on this host")
    parser.add_argument("--stale-days", type=int, default=180,
                        help="flag a recorded read date older than this many days")
    parser.add_argument("--out", default="", help="also write the Markdown report to this path")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when anything needs a human look")
    parser.add_argument("--annotate", action="store_true",
                        help="also emit GitHub Actions annotations, so the headline "
                             "counts are readable from the check run without "
                             "downloading the job log or the artifact")
    parser.add_argument("--probe", default="",
                        help="request this one URL instead of the ledger, then exit")
    args = parser.parse_args()
    if args.probe:
        return run_probe(args)
    return run_recheck(args)


if __name__ == "__main__":
    raise SystemExit(main())
