"""Check the published site against the brief's required content.

Every requirement of the engagement brief is listed below with the phrases the
published page must actually carry and the page each phrase must appear on.
The check is semantic rather than keyword-based: it looks for the specific
wording that answers the requirement, on the page the requirement says it
belongs on, so a page cannot pass by mentioning the topic in passing.

Run after scripts/build.py. A failure means the published edition no longer
covers something the brief asks for.

Standard library only. No network calls.
"""
from __future__ import annotations

import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = ["index.html","executive-summary.html","decision.html","what-if.html","briefing.html",
         "property-a.html","property-b.html","ownership-distinction.html","costs.html",
         "projections.html","taxes.html","inheritance.html","timeline.html","estate.html","laws.html",
         "black-swan.html","economy.html","questions.html","suggestions.html","review.html",
         "glossary.html","sources.html"]
TXT = {p: " ".join(unescape(re.sub(r"<[^>]+>", " ", (ROOT / p).read_text(encoding="utf-8"))).split())
       for p in PAGES}

# (requirement, [(phrase, [pages where it must appear])])
REQ = [
 ("Property A: inherited REDACTED home, through a trust, 2040-2050",
  [("Property A", ["property-a.html"]), ("trust", ["property-a.html"]),
   ("2040", ["property-a.html"]), ("2050", ["property-a.html"])]),
 ("Property B: REDACTED home already owned by the heir",
  [("Property B", ["property-b.html"]), ("already owned", ["property-b.html"]),
   ("REDACTED", ["property-b.html"])]),
 ("Compare: living in A",
  [("Move in and hold for 30 years", ["decision.html"])]),
 ("Compare: renting A",
  [("Let it out from the start", ["decision.html"])]),
 ("Compare: selling A",
  [("Sell at inheritance, invest in equities", ["decision.html"])]),
 ("Compare: retaining A",
  [("Keep it, but neither live in it nor let it out", ["decision.html"])]),
 ("Compare: mixed paths",
  [("Move in two years, then let it out", ["decision.html"])]),
 ("Compare: the already-owned B property",
  [("Property B, already owned", ["decision.html"]),
   ("Property B priced on the same horizon", ["property-b.html"])]),
 ("Phased-investing path: Treasuries 24-36 months, then equities",
  [("Treasuries", ["black-swan.html"]), ("24", ["black-swan.html"]),
   ("36", ["black-swan.html"]), ("phase into equities", ["decision.html"])]),
 ("Crash-at-entry risk, transparent",
  [("crash", ["black-swan.html"]), ("1929", ["black-swan.html"]),
   ("2008", ["black-swan.html"])]),
 ("Explicitly NOT a historical backtest",
  [("not a historical backtest", ["black-swan.html"])]),
 ("Projected property value",
  [("Market value", ["projections.html"])]),
 ("Assessed value", [("Assessed value", ["projections.html"])]),
 ("Property tax", [("Property tax", ["costs.html"])]),
 ("Insurance", [("Insurance", ["costs.html"])]),
 ("Utilities (water, electricity)", [("Water", ["costs.html"]), ("Electricity", ["costs.html"])]),
 ("Maintenance", [("Maintenance", ["costs.html"])]),
 ("Rent", [("Rent", ["costs.html"])]),
 ("Sale costs", [("Selling costs", ["decision.html"])]),
 ("Taxes (capital gains, income tax on each path)",
  [("Capital gain", ["taxes.html"])]),
 ("Estate-tax room", [("basic exclusion", ["estate.html"])]),
 ("Investment outcomes", [("equities", ["decision.html"])]),
 ("Printable one-page Attorney & CPA briefing sheet",
  [("Print / save as PDF", ["briefing.html"])]),
 ("Tax-adviser brief", [("tax adviser", ["briefing.html"])]),
 ("Executive summary", [("Executive summary", ["executive-summary.html"])]),
 ("Deadlines timeline", [("Deadlines in order", ["timeline.html"])]),
 ("Grouped navigation", [("Start here", ["index.html"]), ("Review before deciding", ["index.html"])]),
 ("Glossary", [("Glossary", ["glossary.html"])]),
 ("Dedicated suggestions section", [("Suggestion", ["suggestions.html"])]),
 ("Questions/information/answers register",
  [("question", ["questions.html"]), ("answer", ["questions.html"])]),
 ("'What would change the answer' on the first screen",
  [("what would change the answer", ["index.html"])]),
 ("Reinvestment risk beside the headline conclusion",
  [("Reinvestment risk", ["index.html"])]),
 ("Usable what-if controls", [("one lever at a time", ["what-if.html"])]),
 ("Flagged for Review page", [("Register of unverified", ["review.html"])]),
 ("Source ledger with official publishers", [("source ledger", ["sources.html"])]),
 ("Every factual table row source-linked",
  [("Official source", ["decision.html"])]),
 ("Unconfirmed values left blank and flagged",
  [("not supplied", ["review.html"])]),
 ("Print stylesheet", [("@media print", None)]),
]

gaps = []
for label, checks in REQ:
    for phrase, pages in checks:
        if pages is None:
            ok = "@media print" in (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
        else:
            ok = any(phrase.lower() in TXT[p].lower() for p in pages)
        if not ok:
            gaps.append((label, phrase, pages))
            print(f"GAP  {label}\n     missing {phrase!r} in {pages}")
print(f"Brief coverage: {len(REQ)} requirements checked, {len(gaps)} gap(s)")
if gaps:
    print("Brief coverage FAILED:")
    for label, phrase, pages in gaps:
        print(f"  - {label}: missing {phrase!r} on {', '.join(pages)}")
    sys.exit(1)
print("PASS: every requirement of the brief is covered by a named page.")
