#!/usr/bin/env python3
"""
Static Dashboard & Executive Summary Generator for Tino3 (Session arena-531aee5c-tino3).
Generates all 10 pages in decision-suite/*.html and EXECUTIVE_SUMMARY_531AEE5C.md.
"""
from __future__ import annotations

from html import escape as esc
import json
from pathlib import Path

from model_core import URLS, build_all_data, r10

SUITE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SUITE_DIR.parent
DATA_DIR = SUITE_DIR / "data"

PAGES = [
    ("index.html", "01", "Dashboard Overview"),
    ("executive-summary.html", "02", "Executive Summary"),
    ("property-a.html", "03", "[PROPERTY_A] Analysis"),
    ("property-b.html", "04", "[PROPERTY_B] Analysis"),
    ("taxes-and-laws.html", "05", "Tax & Inheritance Law"),
    ("projections.html", "06", "2026–2050 Projections"),
    ("decision-analysis.html", "07", "Live vs. Rent vs. Sell"),
    ("inheritance-process.html", "08", "Step-by-Step Process"),
    ("flagged-for-review.html", "09", "Flagged for Review"),
    ("sources-ledger.html", "10", "Official Sources Ledger"),
]


def usd(val: int | None) -> str:
    """Format an integer $10-rounded value as USD, or return empty string if None."""
    if val is None:
        return ""
    v = r10(val)
    if v < 0:
        return f"-${abs(v):,}"
    return f"${v:,}"


def badge(kind: str, label: str) -> str:
    cls = {
        "verified": "badge-verified",
        "unverified": "badge-unverified",
        "flagged": "badge-flagged",
        "modeled": "badge-modeled",
    }[kind]
    return f'<span class="badge {cls}">{esc(label)}</span>'


def src_link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} &#8599;</a>'


def render_table(
    headers: list[tuple[str, bool]],
    rows: list[dict],
    filter_group: str | None = None,
) -> str:
    """
    Render an accessible HTML table where EVERY row must carry an official .gov source link.
    headers: list of (column_title, is_numeric)
    rows: list of {"cells": [(value_html, is_blank_official, is_num), ...], "filter": optional_str}
    """
    thead = "".join(
        f'<th scope="col" class="{"num" if is_num else ""}">{esc(title)}</th>'
        for title, is_num in headers
    )
    tbody_parts = []
    for r in rows:
        f_attr = ""
        if filter_group and "filter" in r:
            f_attr = f' data-filter-target="{esc(filter_group)}" data-filter-item="{esc(str(r["filter"]))}"'
            if r.get("hidden_default"):
                f_attr += ' style="display:none;"'
        tds = []
        for cell_html, is_blank, is_num in r["cells"]:
            classes = []
            if is_num:
                classes.append("num")
            if is_blank:
                classes.append("blank-cell")
            c_attr = f' class="{" ".join(classes)}"' if classes else ""
            tds.append(f"<td{c_attr}>{cell_html}</td>")
        tbody_parts.append(f"<tr{f_attr}>{''.join(tds)}</tr>")
    return (
        f'<div class="table-scroll"><table>'
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(tbody_parts)}</tbody>"
        f"</table></div>"
    )


def wrap_page(filename: str, eyebrow: str, title: str, subtitle: str, body_html: str) -> str:
    nav_items = []
    for fname, num, label in PAGES:
        cur = ' aria-current="page"' if fname == filename else ""
        nav_items.append(
            f'<a class="nav-link" href="{esc(fname)}"{cur}>'
            f'<span class="nav-num">{esc(num)}</span><span>{esc(label)}</span></a>'
        )
    nav_html = "".join(nav_items)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <title>{esc(title)} — Verified Inheritance Decision Suite</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <aside class="sidebar">
    <div class="brand-box">
      <span class="brand-title">Inheritance Decision Suite</span>
      <span class="brand-sub">2040–2050 Trust &amp; Property Analysis · Anonymized &amp; $10-Rounded</span>
    </div>
    <div class="nav-group-label">Categories &amp; Verification</div>
    <nav class="nav-list" aria-label="Primary category navigation">
      {nav_html}
    </nav>
    <div class="sidebar-footer">
      <span class="privacy-pill">PRIVACY PROTECTED</span><br>
      Placeholders only (<code>[PROPERTY_A]</code>, <code>[PROPERTY_B]</code>, <code>[DECEDENT]</code>, <code>[BENEFICIARY]</code>). Zero addresses, APNs, names, or ZIPs. All figures rounded to nearest $10.
    </div>
  </aside>
  <main id="main" class="main-content">
    <div class="topbar-meta">
      <span><strong>Verification Standard:</strong> Line-by-line official <code>.gov</code> sources · Unconfirmed official fields left blank</span>
      <span><strong>As of:</strong> November 10, 2026 · Session <code>arena-531aee5c-tino3</code></span>
    </div>
    <header class="page-header">
      <div class="eyebrow">{esc(eyebrow)}</div>
      <h1>{esc(title)}</h1>
      <p>{esc(subtitle)}</p>
    </header>
    <div class="callout callout-privacy">
      <strong>Privacy &amp; Evidence Boundary:</strong> Personal, parcel, and location identifiers are strictly anonymized using placeholders. Every cost and projection is rounded to the nearest <strong>$10</strong>. Where an item cannot be confirmed from an official government source without private parcel/account records, the <em>Official Confirmed Value</em> cell is intentionally left blank and flagged on <a href="flagged-for-review.html">Flagged for Review</a>.
    </div>
    <div class="callout callout-privacy">
      <strong>How this annex relates to the integrated edition:</strong> This Decision Brief is the earlier full analysis, restored and published under the owner&rsquo;s anonymization and $10-rounding instruction. The repository&rsquo;s integrated edition (<a href="../index.html">planning dashboard</a>) is the current authoritative layer: its model is regenerated and re-verified on every CI run and its source ledger was re-checked against official pages on 10 November 2026. The two layers measure different things &mdash; this Brief reports strategy-level ten-year after-tax wealth contributions for the inherited-property decision, while the integrated edition reports household terminal net worth at 2055 including <code>[PROPERTY_B]</code> value and accumulated cash &mdash; so their figures are not interchangeable. Where the two differ, use the integrated edition&rsquo;s numbers and assumption register; use this Brief for the longer property-level series, the estate-headroom table and the step-by-step trust-inheritance walkthrough.
    </div>
    {body_html}
    <footer class="page-footer">
      <span>Verified Inheritance Decision Suite · Educational &amp; analytical modeling only — not legal, tax, or investment advice.</span>
      <span><a href="sources-ledger.html">Official Sources Ledger</a> · <a href="flagged-for-review.html">Flagged for Review</a> · <a href="../index.html">Repository Root</a></span>
    </footer>
  </main>
  <script src="assets/app.js"></script>
</body>
</html>
"""


def main() -> None:
    data = build_all_data()
    sources_json = json.loads((DATA_DIR / "official_sources.json").read_text(encoding="utf-8"))["sources"]
    audit_json = json.loads((DATA_DIR / "repo_audit.json").read_text(encoding="utf-8"))["findings"]

    a_proj = {r["year"]: r for r in data["prop_a_projections"]}
    b_proj = {r["year"]: r for r in data["prop_b_projections"]}
    dec_rows = data["decision_rows"]
    est_rows = {r["year"]: r for r in data["estate_rows"]}

    a2045 = a_proj[2045]
    b2045 = b_proj[2045]
    d2045 = {r["strategy_code"]: r for r in dec_rows if r["inheritance_year"] == 2045}
    e2045 = est_rows[2045]

    # =========================================================================
    # PAGE 1: index.html — Landing Dashboard
    # =========================================================================
    idx_snapshot_rows = [
        {
            "cells": [
                ("2026 Federal Estate Basic Exclusion (Single / Married DSUE)", False, False),
                ("<code>$15,000,000</code> / <code>$30,000,000</code>", False, False),
                ("<code>$15,000,000</code> / <code>$30,000,000</code>", False, False),
                (badge("verified", "VERIFIED STATUTE"), False, False),
                (src_link(URLS["irs_706"], "IRS Form 706 (Rev. 07/2026)"), False, False),
            ]
        },
        {
            "cells": [
                ("2027 Federal Estate Basic Exclusion &amp; Gift Exclusion", False, False),
                ("<code>$15,480,000</code> estate / <code>$20,000</code> gift", False, False),
                ("<code>$15,480,000</code> / <code>$20,000</code>", False, False),
                (badge("verified", "VERIFIED STATUTE"), False, False),
                (src_link(URLS["irs_2027"], "IRS IR-2026-133 (Nov 5, 2026)"), False, False),
            ]
        },
        {
            "cells": [
                ("California State &amp; Local Inheritance / Estate Tax", False, False),
                ("<code>$0</code>", False, False),
                ("<code>$0</code> (Prohibited by R&amp;TC §13301)", False, False),
                (badge("verified", "VERIFIED STATUTE"), False, False),
                (src_link(URLS["ca_rtc13301"], "CA R&TC §13301"), False, False),
            ]
        },
        {
            "cells": [
                ("Prop 19 Principal-Residence Value Cap (Feb 2025 – Feb 2027)", False, False),
                ("FBYV + <code>$1,044,590</code> (rounded $10)", False, False),
                ("FBYV + <code>$1,044,590</code>", False, False),
                (badge("verified", "VERIFIED BOE LTA"), False, False),
                (src_link(URLS["boe_lta25009"], "CA BOE LTA 2025/009"), False, False),
            ]
        },
        {
            "cells": [
                ("<code>[PROPERTY_A]</code> Nov 2026 Est. Value &amp; 2026 Roll", False, False),
                ("", True, False),
                ("<code>$3,100,000</code> FMV / <code>$550,540</code> roll", False, False),
                (badge("unverified", "UNVERIFIED INPUT"), False, False),
                (src_link(URLS["scc_dtac"], "Santa Clara County DTAC"), False, False),
            ]
        },
        {
            "cells": [
                ("<code>[PROPERTY_B]</code> Nov 2026 Est. Value &amp; 2-Unit Gross Rent", False, False),
                ("", True, False),
                ("<code>$1,800,000</code> FMV / <code>$85,800</code>/yr rent", False, False),
                (badge("unverified", "UNVERIFIED INPUT"), False, False),
                (src_link(URLS["sf_taxrate"], "SF BOS Res. 447-25"), False, False),
            ]
        },
        {
            "cells": [
                ("Liquid Cash Inheritance Amount", False, False),
                ("", True, False),
                ("<em>Undisclosed</em> — Modeled via headroom tiers", False, False),
                (badge("unverified", "UNVERIFIED — BLANK"), False, False),
                (src_link(URLS["irs_706"], "IRS Form 706 Instructions"), False, False),
            ]
        },
        {
            "cells": [
                ("Risk-Free U.S. Treasury Benchmark (Nov 9, 2026 Par Curve)", False, False),
                ("10-Yr: <code>4.88%</code> · 30-Yr: <code>5.26%</code> (0% CA tax)", False, False),
                ("<code>4.88%</code> 10-Yr CMT (CA-tax-exempt)", False, False),
                (badge("verified", "VERIFIED TREASURY"), False, False),
                (src_link(URLS["treasury"], "U.S. Treasury Daily Curve"), False, False),
            ]
        },
    ]

    idx_dec_rows = []
    for r in dec_rows:
        idx_dec_rows.append({
            "filter": str(r["inheritance_year"]),
            "hidden_default": r["inheritance_year"] != 2045,
            "cells": [
                (f"<strong>{r['inheritance_year']}</strong>", False, False),
                (esc(r["strategy_name"]), False, False),
                (usd(r["prop_a_fmv_at_death"]), False, True),
                (usd(r["yr1_prop_a_property_tax"]), False, True),
                (usd(r["yr1_combined_net_cash_flow"]), False, True),
                (f"<strong>{usd(r['ten_yr_after_tax_wealth'])}</strong>", False, True),
                (badge("modeled", r["verdict"].split(" (")[0]), False, False),
                (src_link(r["source_url"], "Official Statutory Rule"), False, False),
            ],
        })

    index_body = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Optimal Financial Plan (2045 Midpoint)</div>
        <div class="kpi-value">Sell [PROPERTY_A]</div>
        <div class="kpi-sub">Keep living in <code>[PROPERTY_B]</code> Unit 3 ($0 rent loss), capture IRC §1014 step-up ($0 cap-gains tax), &amp; invest <strong>{usd(d2045['S3A']['net_sale_proceeds_prop_a'])}</strong> net proceeds.</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">2045 10-Yr Wealth Advantage</div>
        <div class="kpi-value">+{usd(r10(d2045['S3A']['ten_yr_after_tax_wealth'] - d2045['S2']['ten_yr_after_tax_wealth']))}</div>
        <div class="kpi-sub">Sell &amp; Reinvest Equities (<strong>{usd(d2045['S3A']['ten_yr_after_tax_wealth'])}</strong>) vs. Renting <code>[PROPERTY_A]</code> (<strong>{usd(d2045['S2']['ten_yr_after_tax_wealth'])}</strong>).</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">2045 Prop 19 Reassessment Shock</div>
        <div class="kpi-value">{usd(a2045['tax_if_rented'])}/yr</div>
        <div class="kpi-sub"><code>[PROPERTY_A]</code> tax if rented (vs. <strong>{usd(a2045['tax_if_live_in'])}/yr</strong> if heir moves in within 1 yr, up from <strong>{usd(a2045['pre_inheritance_tax'])}/yr</strong> pre-death).</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">2045 Tax-Free Cash Headroom</div>
        <div class="kpi-value">{usd(e2045['cash_headroom_single_if_both_in_estate'])}</div>
        <div class="kpi-sub">Remaining single-decedent federal exclusion after both properties (<strong>{usd(e2045['cash_headroom_married_if_both_in_estate'])}</strong> with spousal DSUE portability; <strong>$0</strong> CA estate tax).</div>
      </div>
    </div>

    <section class="section-card">
      <h2>Executive Verdict at a Glance (2040–2050 Trust Inheritance)</h2>
      <p class="section-desc">Coordinated optimization of <code>[PROPERTY_A]</code> (inherited single-family home with solar) and <code>[PROPERTY_B]</code> (3-unit residence with 2 rented units generating $85,800/yr and 1 vacant unit available for primary occupancy).</p>
      <div class="callout callout-info">
        <strong>1. Maximize Profit &amp; Cash Flow (Recommended Default):</strong> Occupy <code>[PROPERTY_B]</code>'s available 3rd unit (preserving 100% of its 2-unit rental cash flow without triggering Prop 19 reassessment if already held), <strong>sell <code>[PROPERTY_A]</code> promptly after inheritance</strong> using the revocable trust's <strong>IRC §1014 date-of-death basis step-up ($0 federal and $0 California capital gains tax on pre-death appreciation)</strong>, and reinvest the <strong>{usd(d2045['S3A']['net_sale_proceeds_prop_a'])}</strong> (2045 base case) into a diversified equity/U.S. Treasury portfolio. Even a 100% sovereign U.S. Treasury ladder at verified Nov 2026 yields (<code>4.88%</code> 10-Yr CMT, <strong>0% California state tax</strong>) delivers <strong>{usd(d2045['S3B']['yr1_combined_net_cash_flow'])}/yr</strong> combined cash flow — nearly <strong>4&times;</strong> the net cash flow of renting out <code>[PROPERTY_A]</code>.<br><br>
        <strong>2. Conditional Lifestyle Exception (If Single-Family Occupancy Desired):</strong> Only if <code>[BENEFICIARY]</code> specifically desires to live in <code>[PROPERTY_A]</code> long-term should <code>[PROPERTY_A]</code> be retained: move in within <strong>1 year</strong> of death, file <code>BOE-266</code> within 1 year and <code>BOE-19-P</code> within 3 years to save <strong>{usd(r10(a2045['tax_if_rented'] - a2045['tax_if_live_in']))}/yr</strong> in 2045 property taxes. Under <strong>BOE Pub. 800-1</strong>, moving out later forfeits the Prop 19 cap on the next January 1 lien date.<br><br>
        <strong>3. Avoid Holding <code>[PROPERTY_A]</code> as a Rental:</strong> Full Prop 19 market-value reassessment (<strong>{usd(a2045['tax_if_rented'])}/yr</strong> tax in 2045), landlord insurance, capital repairs, loss of IRC §121 exclusion, and depreciation recapture make renting <code>[PROPERTY_A]</code> the lowest-yielding choice unless monthly rent exceeds <strong>{usd(d2045['S2']['breakeven_prop_a_rent_mo'])}/mo</strong> in 2045.
      </div>

      <div class="filter-bar" data-filter-group="idx-horizon">
        <span class="filter-label">Select Inheritance Year:</span>
        <button type="button" class="tab-btn" data-filter-value="2040">2040 (Early Window)</button>
        <button type="button" class="tab-btn active" data-filter-value="2045">2045 (Midpoint Base Case)</button>
        <button type="button" class="tab-btn" data-filter-value="2050">2050 (Late Window)</button>
        <button type="button" class="tab-btn" data-filter-value="all">Show All (2040 / 2045 / 2050)</button>
      </div>
      {render_table(
          [
              ("Year", False),
              ("Coordinated 2-Property Strategy", False),
              ("[PROPERTY_A] FMV", True),
              ("Yr-1 [PROPERTY_A] Tax", True),
              ("Yr-1 Combined Cash Flow", True),
              ("10-Yr Post-Inheritance Wealth", True),
              ("Ranking", False),
              ("Official Source", False),
          ],
          idx_dec_rows,
          filter_group="idx-horizon",
      )}
    </section>

    <section class="section-card">
      <h2>Verified Baseline vs. Modeling Inputs (All Dollars Rounded to $10)</h2>
      <p class="section-desc">Strict separation between confirmed government statutory facts and unverified owner-supplied modeling inputs (left blank in the Official Confirmed column).</p>
      {render_table(
          [
              ("Parameter / Requirement", False),
              ("Official Confirmed Value", False),
              ("Scenario Modeling Value ($10 Rounded)", False),
              ("Verification Status", False),
              ("Official Government Source", False),
          ],
          idx_snapshot_rows,
      )}
    </section>

    <section class="section-card">
      <h2>Explore Dashboard Categories</h2>
      <div class="cat-grid">
        <a class="cat-card" href="executive-summary.html"><h3>02 · Executive Summary</h3><p>Complete synthesis of findings, key drivers, privacy safeguards, and strategic recommendations.</p></a>
        <a class="cat-card" href="property-a.html"><h3>03 · [PROPERTY_A] Analysis</h3><p>2014–2026 BOE CCPI roll verification, tax decomposition, CDI HO-3/DP-3 insurance, water &amp; CPUC 20-yr solar NEM sunset.</p></a>
        <a class="cat-card" href="property-b.html"><h3>04 · [PROPERTY_B] Analysis</h3><p>3-unit P&amp;L, SF BOS Res. 447-25 1.1827% + parcel-charge proof, 2022 roll flag, SFPUC rates &amp; 1.6% Rent Board cap.</p></a>
        <a class="cat-card" href="taxes-and-laws.html"><h3>05 · Tax &amp; Inheritance Law</h3><p>Prop 13/19, IRC §1014 vs. Rev. Rul. 2023-2 trust trap, 2026/2027 IRS estate thresholds, cash headroom &amp; pending bills.</p></a>
        <a class="cat-card" href="projections.html"><h3>06 · 2026–2050 Projections</h3><p>Year-by-year $10-rounded projections of market value, assessed value, Prop 19 tax, utilities, insurance &amp; maintenance.</p></a>
        <a class="cat-card" href="decision-analysis.html"><h3>07 · Live vs. Rent vs. Sell</h3><p>Full 2040, 2045 &amp; 2050 decision matrix, equity vs. CA-tax-exempt Treasury reinvestment, break-even rent &amp; sensitivities.</p></a>
        <a class="cat-card" href="inheritance-process.html"><h3>08 · Step-by-Step Process</h3><p>12-step chronological trust administration checklist with statutory California &amp; IRS deadlines and forms.</p></a>
        <a class="cat-card" href="flagged-for-review.html"><h3>09 · Flagged for Review</h3><p>All 14 unverified items (blank official cells), mathematical roll anomalies, and repository audit findings RA-01..RA-08.</p></a>
        <a class="cat-card" href="sources-ledger.html"><h3>10 · Official Sources Ledger</h3><p>Line-by-line register of all 24 verified .gov primary authorities and downloadable RFC-4180 CSV datasets.</p></a>
      </div>
    </section>
    """
    (SUITE_DIR / "index.html").write_text(
        wrap_page(
            "index.html",
            "Overview & Decision Dashboard",
            "2040–2050 Trust Property Inheritance Decision Dashboard",
            "Clean, line-by-line official-source decision framework comparing Living, Renting, or Selling & Reinvesting across a two-property Northern California household portfolio.",
            index_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 2: executive-summary.html
    # =========================================================================
    exec_pillars = [
        {
            "cells": [
                ("1. Privacy &amp; Anonymization", False, False),
                ("Strict Placeholder Policy", False, False),
                ("Zero names, street addresses, APNs, utility accounts, or ZIP codes appear anywhere in this suite; all monetary numbers are rounded to the nearest $10 increment to prevent tax-roll fingerprinting.", False, False),
                (src_link(URLS["scc_dtac"], "County Public Roll Context"), False, False),
            ]
        },
        {
            "cells": [
                ("2. Property Tax Reassessment (Prop 19)", False, False),
                ("Primary Cost Driver", False, False),
                (f"Inheriting [PROPERTY_A] in 2045 raises property tax from {usd(a2045['pre_inheritance_tax'])}/yr to {usd(a2045['tax_if_live_in'])}/yr if [BENEFICIARY] moves in within 1 year, or {usd(a2045['tax_if_rented'])}/yr (+{usd(r10(a2045['tax_if_rented'] - a2045['tax_if_live_in']))}/yr penalty) if rented out.", False, False),
                (src_link(URLS["boe_lta25009"], "BOE LTA 2025/009 & R&TC §63.2"), False, False),
            ]
        },
        {
            "cells": [
                ("3. Income &amp; Capital Gains Step-Up", False, False),
                ("IRC §1014 vs. Rev. Rul. 2023-2", False, False),
                (f"Holding [PROPERTY_A] in a revocable living trust included in [DECEDENT]'s gross estate steps tax basis up to date-of-death FMV ({usd(a2045['mv_base_4pct'])} in 2045), allowing an immediate post-inheritance sale with $0 federal and $0 CA capital gains tax. Moving it to an estate-excluded irrevocable trust forfeits step-up.", False, False),
                (src_link(URLS["irs_rr2023_2"], "IRS Rev. Rul. 2023-2 & §1014"), False, False),
            ]
        },
        {
            "cells": [
                ("4. Coordinated [PROPERTY_B] Advantage", False, False),
                ("Zero-Rent-Loss Housing", False, False),
                (f"[PROPERTY_B] provides 2 rented units generating $85,800/yr today ({usd(b2045['gross_rent_2_units'])}/yr projected in 2045) PLUS a 3rd livable unit for [BENEFICIARY] without evicting tenants or losing rental income. Do not trigger an unexcluded reassessment on [PROPERTY_B].", False, False),
                (src_link(URLS["sf_rent"], "SF Rent Board Rules"), False, False),
            ]
        },
        {
            "cells": [
                ("5. Reinvestment Superiority", False, False),
                ("Equities or CA-Tax-Free Treasuries", False, False),
                (f"Selling [PROPERTY_A] in 2045 nets {usd(d2045['S3A']['net_sale_proceeds_prop_a'])}. Even 10-Yr U.S. Treasuries at 4.88% (exempt from 13.3% CA tax under 31 U.S.C. §3124) yield {usd(d2045['S3B']['yr1_portfolio_or_prop_a_return'])}/yr after federal tax vs. {usd(d2045['S2']['yr1_portfolio_or_prop_a_return'])}/yr from renting [PROPERTY_A].", False, False),
                (src_link(URLS["treasury"], "U.S. Treasury Par Curve"), False, False),
            ]
        },
        {
            "cells": [
                ("6. Liquid Cash Inheritance &amp; Estate Tax", False, False),
                ("0% CA Tax · 40% Federal Above Cap", False, False),
                (f"CA imposes $0 inheritance/estate tax (R&TC §13301). Federal exclusion is $15,000,000 in 2026 and $15,480,000 in 2027 (projected {usd(e2045['exemption_single'])} single / {usd(e2045['exemption_married_dsue'])} married in 2045), leaving {usd(e2045['cash_headroom_single_if_both_in_estate'])} single ({usd(e2045['cash_headroom_married_if_both_in_estate'])} married) cash headroom—but only {usd(e2045['cash_headroom_50pct_cut_if_both'])} if Congress halves the exemption.", False, False),
                (src_link(URLS["irs_2027"], "IRS IR-2026-133 & Form 706"), False, False),
            ]
        },
        {
            "cells": [
                ("7. Hidden Operating Cost Risks", False, False),
                ("Insurance &amp; Solar NEM Sunset", False, False),
                ("Owner's ~$1,500/yr insurance estimate is far below replacement-cost HO-3 (~$3,000/yr) and 3-unit landlord DP-3 (~$4,500/yr) levels; furthermore, CPUC legacy NEM 1.0/2.0 retail solar credits expire 20 years after interconnection (by or before 2046).", False, False),
                (src_link(URLS["cpuc_solar"], "CPUC D.22-12-056 & CDI"), False, False),
            ]
        },
    ]

    exec_body = f"""
    <section class="section-card">
      <h2>Executive Summary — Seven Core Findings</h2>
      <p class="section-desc">Structured synthesis guiding the 2040–2050 trust inheritance of <code>[PROPERTY_A]</code> alongside <code>[PROPERTY_B]</code> and liquid estate assets.</p>
      {render_table(
          [
              ("Decision Pillar", False),
              ("Headline Takeaway", False),
              ("Quantified Reasoning ($10 Rounded)", False),
              ("Primary Official Source", False),
          ],
          exec_pillars,
      )}
    </section>

    <section class="section-card">
      <h2>2045 Midpoint 10-Year Post-Inheritance Wealth Visual Comparison</h2>
      <p class="section-desc">Combined 10-year after-tax wealth contribution (2045–2055) from <code>[PROPERTY_A]</code> equity/proceeds plus <code>[PROPERTY_B]</code> net operating income.</p>
      <div class="bar-row">
        <div class="bar-meta"><span>Strategy 3A: Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] &rarr; Diversified Equities (7.0% Scenario)</span><span>{usd(d2045['S3A']['ten_yr_after_tax_wealth'])}</span></div>
        <div class="bar-track"><div class="bar-fill alt-green" style="width:100%"></div></div>
      </div>
      <div class="bar-row">
        <div class="bar-meta"><span>Strategy 3B: Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] &rarr; U.S. Treasuries (4.88% CMT, 0% CA Tax)</span><span>{usd(d2045['S3B']['ten_yr_after_tax_wealth'])}</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:86%"></div></div>
      </div>
      <div class="bar-row">
        <div class="bar-meta"><span>Strategy 2: Live in [PROPERTY_B] Unit 3 + Rent Out [PROPERTY_A] (Full Prop 19 Reassessment)</span><span>{usd(d2045['S2']['ten_yr_after_tax_wealth'])}</span></div>
        <div class="bar-track"><div class="bar-fill alt-amber" style="width:81%"></div></div>
      </div>
      <div class="bar-row">
        <div class="bar-meta"><span>Strategy 1: Live in [PROPERTY_A] (Prop 19 Move-In Cap) + Keep [PROPERTY_B] (2 Units Rented)</span><span>{usd(d2045['S1']['ten_yr_after_tax_wealth'])}</span></div>
        <div class="bar-track"><div class="bar-fill alt-slate" style="width:73%"></div></div>
      </div>
    </section>
    """
    (SUITE_DIR / "executive-summary.html").write_text(
        wrap_page(
            "executive-summary.html",
            "Category 02 · Executive Summary",
            "Executive Summary & Strategic Recommendations",
            "Clear, quantified reasoning across property taxes, income/estate taxes, operating costs, and portfolio reinvestment for the 2040–2050 inheritance horizon.",
            exec_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 3: property-a.html — [PROPERTY_A] Analysis
    # =========================================================================
    prop_a_hist_rows = []
    for r in data["prop_a_history"]:
        eff_pct = ""
        if r["reported_tax"] is not None and r["reported_av"]:
            eff_pct = f"{(r['reported_tax'] / r['reported_av']) * 100:.2f}%"
        prop_a_hist_rows.append({
            "cells": [
                (str(r["year"]), False, False),
                (usd(r["reported_tax"]) if r["reported_tax"] is not None else "", r["reported_tax"] is None, True),
                (esc(r["reported_tax_chg"]) if r["reported_tax_chg"] else "—", False, False),
                (usd(r["reported_av"]), False, True),
                (esc(r["reported_av_chg"]), False, False),
                (esc(r["boe_ccpi_factor"]), False, False),
                (eff_pct if eff_pct else "—", False, True),
                ("", True, False),
                (badge("unverified", r["status"]), False, False),
                (src_link(URLS["boe_lta26002"], "BOE LTA 2026/002"), False, False),
            ]
        })

    prop_a_cost_rows = [
        {
            "cells": [
                ("Estimated Market Value (Nov 2026)", False, False),
                ("", True, False),
                ("<code>$3,100,000</code>", False, True),
                (badge("unverified", "UNVERIFIED — Owner Est."), False, False),
                ("Requires licensed appraisal at death for IRC §1014 basis.", False, False),
                (src_link(URLS["irs_basis"], "IRS Basis FAQ"), False, False),
            ]
        },
        {
            "cells": [
                ("2025 Property Tax Decomposition", False, False),
                ("<code>1.00%</code> base + voter GO bonds", False, False),
                ("<code>$7,210</code>/yr (~1.18% ad valorem <code>$6,370</code> + <code>$840</code> flat parcel charges)", False, True),
                (badge("modeled", "VERIFIED RATE / UNVERIFIED BILL"), False, False),
                ("Flat parcel taxes do NOT scale with market value upon reassessment.", False, False),
                (src_link(URLS["scc_taxbook"], "Santa Clara Tax Rate Book"), False, False),
            ]
        },
        {
            "cells": [
                ("Water Utility (Monthly / Annual)", False, False),
                ("", True, False),
                ("<code>$100</code>–<code>$150</code>/mo (<code>$1,500</code>/yr midpoint)", False, True),
                (badge("unverified", "UNVERIFIED — Bills Needed"), False, False),
                ("Served by San Jose Water Co. (leased municipal system) or Cal Water; CPUC-regulated.", False, False),
                (src_link(URLS["cup_water"], "Cupertino General Plan Ch. 6"), False, False),
            ]
        },
        {
            "cells": [
                ("Electricity &amp; Rooftop Solar (NEM)", False, False),
                ("", True, False),
                ("<code>-$180</code>/yr pre-2040; <code>+$760</code>/yr in 2040 post-NEM sunset", False, True),
                (badge("flagged", "FLAGGED — 20-Yr NEM Sunset"), False, False),
                ("CPUC D.16-01-044 / D.22-12-056 ends retail NEM credits 20 yrs after interconnection; D.24-05-028 adds fixed monthly charges.", False, False),
                (src_link(URLS["cpuc_solar"], "CPUC Decision 22-12-056"), False, False),
            ]
        },
        {
            "cells": [
                ("Primary Residence Insurance (HO-3)", False, False),
                ("", True, False),
                ("Owner guess <code>$1,500</code>/yr vs. realistic <code>$3,000</code>/yr (2026$)", False, True),
                (badge("flagged", "FLAGGED — $1,500 Low vs CDI"), False, False),
                ("CDI statewide all-forms average is ~$2,340/yr; rebuilding a Silicon Valley home (~$1.0M–$1.5M Coverage A) typically exceeds $2,500–$3,500/yr.", False, False),
                (src_link(URLS["cdi_ins"], "CDI Residential Insurance Guide"), False, False),
            ]
        },
        {
            "cells": [
                ("Landlord Dwelling Fire Insurance (DP-3)", False, False),
                ("", True, False),
                ("<code>$3,600</code>/yr (2026$ realistic rental policy)", False, True),
                (badge("modeled", "MODELED BENCHMARK"), False, False),
                ("Required if [PROPERTY_A] is rented out; ~20% above HO-3 plus landlord liability.", False, False),
                (src_link(URLS["cdi_ins"], "CDI Home Insurance Finder"), False, False),
            ]
        },
        {
            "cells": [
                ("Regular Maintenance &amp; Capital Reserve", False, False),
                ("", True, False),
                ("<code>$15,500</code>/yr live (0.50% MV) / <code>$20,150</code>/yr rent (0.65% MV)", False, True),
                (badge("modeled", "SCENARIO ASSUMPTION"), False, False),
                ("Lower % of total value than [PROPERTY_B] because ~75% of [PROPERTY_A] value is land, not structure.", False, False),
                (src_link(URLS["irs_p527"], "IRS Pub. 527 Repairs vs. Improvements"), False, False),
            ]
        },
        {
            "cells": [
                ("County Documentary Transfer Tax (If Sold)", False, False),
                ("<code>0.11%</code> of sale price ($0 on inheritance)", False, False),
                ("<code>$3,410</code> at $3,100,000 / <code>$7,180</code> at 2045 FMV", False, True),
                (badge("verified", "VERIFIED COUNTY SCHEDULE"), False, False),
                ("General-law city has no separate city conveyance tax (unlike San Jose/Palo Alto/Mountain View).", False, False),
                (src_link(URLS["scc_dtt"], "Santa Clara Clerk-Recorder Fees"), False, False),
            ]
        },
    ]

    prop_a_body = f"""
    <section class="section-card">
      <h2><code>[PROPERTY_A]</code> Operating Cost, Utility, Solar &amp; Insurance Profile</h2>
      <p class="section-desc">Single-family residence with installed solar in Santa Clara County jurisdiction. Official parcel-specific fields remain blank until confirmed via private tax/utility bills or binding CDI insurer quotes.</p>
      {render_table(
          [
              ("Cost / Valuation Item", False),
              ("Official Confirmed Value", False),
              ("Modeling Baseline ($10 Rounded)", True),
              ("Status", False),
              ("Analytical Findings", False),
              ("Official Source", False),
          ],
          prop_a_cost_rows,
      )}
    </section>

    <section class="section-card">
      <h2><code>[PROPERTY_A]</code> Historical Assessment &amp; Tax Audit (2014–2026, Rounded to $10)</h2>
      <p class="section-desc">Every year-over-year assessment change reported by the owner (<code>+0.5%</code> in 2014, <code>+1.5%</code> in 2016, <code>+1%</code> in 2021, <code>+2%</code> in all other years) matches the exact California Board of Equalization Prop 13 CCPI factor to within one whole dollar of Assessor truncation. 2026 actual property tax was not supplied (<code>--</code>) and is left blank—never inferred.</p>
      {render_table(
          [
              ("Year", False),
              ("Owner-Reported Tax ($10)", True),
              ("Reported Tax %", False),
              ("Owner-Reported Roll ($10)", True),
              ("Reported Roll %", False),
              ("Official BOE CCPI Factor", False),
              ("Implied Bill / Roll", True),
              ("Official Confirmed Parcel Roll", False),
              ("Verification Status", False),
              ("Official BOE Source", False),
          ],
          prop_a_hist_rows,
      )}
    </section>
    """
    (SUITE_DIR / "property-a.html").write_text(
        wrap_page(
            "property-a.html",
            "Category 03 · [PROPERTY_A] Detail",
            "[PROPERTY_A] — Tax Roll Audit, Solar NEM, Insurance & Carrying Costs",
            "Line-by-line verification of historical Prop 13 assessments against official BOE CCPI factors, tax rate decomposition, water/solar utilities, and CDI primary vs. landlord insurance.",
            prop_a_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 4: property-b.html — [PROPERTY_B] Analysis
    # =========================================================================
    prop_b_hist_rows = []
    for r in data["prop_b_history"]:
        eff_pct = ""
        if r["reported_tax"] is not None and r["reported_av"]:
            eff_pct = f"{(r['reported_tax'] / r['reported_av']) * 100:.2f}%"
        b_kind = "flagged" if r["status"].startswith("FLAGGED") else "unverified"
        prop_b_hist_rows.append({
            "cells": [
                (str(r["year"]), False, False),
                (usd(r["reported_tax"]) if r["reported_tax"] is not None else "", r["reported_tax"] is None, True),
                (esc(r["reported_tax_chg"]) if r["reported_tax_chg"] else "—", False, False),
                (usd(r["reported_av"]) if r["reported_av"] is not None else "", r["reported_av"] is None, True),
                (esc(r["reported_av_chg"]) if r["reported_av_chg"] else "—", False, False),
                (esc(r["boe_ccpi_factor"]), False, False),
                (eff_pct if eff_pct else "—", False, True),
                ("", True, False),
                (badge(b_kind, r["status"]), False, False),
                (src_link(URLS["sf_taxrate"], "SF BOS Res. 447-25"), False, False),
            ]
        })

    prop_b_pl_rows = [
        {
            "cells": [
                ("Gross Rental Income (2 of 3 Units Rented; Unit 3 Vacant for Owner)", False, False),
                ("", True, False),
                ("<code>$85,800</code>/yr (<code>$7,150</code>/mo)", False, True),
                (usd(b2045["gross_rent_2_units"]), False, True),
                (badge("unverified", "UNVERIFIED — Leases Needed"), False, False),
                (src_link(URLS["sf_rent"], "SF Rent Board Current Rates (1.6% Cap)"), False, False),
            ]
        },
        {
            "cells": [
                ("Vacancy / Collection Allowance (4% Modeled)", False, False),
                ("", True, False),
                ("<code>-$3,430</code>/yr", False, True),
                (usd(r10(b2045["effective_rent_after_vacancy"] - b2045["gross_rent_2_units"])), False, True),
                (badge("modeled", "SCENARIO ASSUMPTION"), False, False),
                (src_link(URLS["ftb_rent"], "CA FTB Rental Income"), False, False),
            ]
        },
        {
            "cells": [
                ("Secured Property Tax (Held As-Is — No Reassessment)", False, False),
                ("<code>1.1827%</code> ad valorem + flat parcel charges", False, False),
                ("<code>-$2,490</code>/yr", False, True),
                (usd(-b2045["tax_held_as_is"]), False, True),
                (badge("verified", "VERIFIED AD VALOREM RATE"), False, False),
                (src_link(URLS["sf_taxrate"], "SF BOS Res. 447-25"), False, False),
            ]
        },
        {
            "cells": [
                ("3-Unit Habitational / Landlord Insurance (DP-3 / Commercial)", False, False),
                ("", True, False),
                ("<code>-$4,500</code>/yr realistic (owner guess <code>$1,500</code> flagged)", False, True),
                (usd(-b2045["ins_3unit_realistic"]), False, True),
                (badge("flagged", "FLAGGED — $1,500 Understated"), False, False),
                (src_link(URLS["cdi_ins"], "CDI Residential / Dwelling Fire"), False, False),
            ]
        },
        {
            "cells": [
                ("Water &amp; Wastewater (All 3 Units — SFPUC Schedule)", False, False),
                ("Multi-family water + 95% sewer return factor", False, False),
                ("<code>-$4,380</code>/yr (<code>$330</code>–<code>$400</code>/mo)", False, True),
                (usd(-b2045["water_sewer_sfpuc"]), False, True),
                (badge("verified", "VERIFIED TARIFF / UNVERIFIED BILL"), False, False),
                (src_link(URLS["sfpuc"], "SFPUC Prop 218 Rate Notice"), False, False),
            ]
        },
        {
            "cells": [
                ("Common-Area / Owner Electricity", False, False),
                ("", True, False),
                ("<code>-$600</code>/yr (<code>$30</code>–<code>$70</code>/mo)", False, True),
                (usd(-b2045["electricity_common"]), False, True),
                (badge("unverified", "UNVERIFIED — Bills Needed"), False, False),
                (src_link(URLS["cpuc_solar"], "CPUC Electric Rate Oversight"), False, False),
            ]
        },
        {
            "cells": [
                ("3-Unit Maintenance &amp; Capital Reserve (0.85% MV)", False, False),
                ("", True, False),
                ("<code>-$15,300</code>/yr", False, True),
                (usd(-b2045["maintenance_3unit"]), False, True),
                (badge("modeled", "SCENARIO ASSUMPTION"), False, False),
                (src_link(URLS["irs_p527"], "IRS Pub. 527 Rental Expenses"), False, False),
            ]
        },
        {
            "cells": [
                ("<strong>Net Operating Cash Flow (Held As-Is, Unit 3 Free for Owner)</strong>", False, False),
                ("", True, False),
                (f"<strong>{usd(b_proj[2026]['net_cash_flow_held_as_is'])}/yr</strong>", False, True),
                (f"<strong>{usd(b2045['net_cash_flow_held_as_is'])}/yr</strong>", False, True),
                (badge("modeled", "CASH-FLOW ENGINE"), False, False),
                (src_link(URLS["irs_p527"], "IRS Schedule E / Pub. 527"), False, False),
            ]
        },
        {
            "cells": [
                ("<em>Sensitivity: Net Cash Flow If [PROPERTY_B] Were Fully Reassessed</em>", False, False),
                ("2/3 rental share always reassessed on parent-child transfer", False, False),
                (f"<em>{usd(b_proj[2026]['net_cash_flow_if_reassessed'])}/yr</em>", False, True),
                (f"<em>{usd(b2045['net_cash_flow_if_reassessed'])}/yr</em>", False, True),
                (badge("flagged", "REASSESSMENT WARNING"), False, False),
                (src_link(URLS["boe_prop19"], "CA BOE Prop 19 Multi-Unit Rule"), False, False),
            ]
        },
    ]

    prop_b_body = f"""
    <section class="section-card">
      <h2>Forensic Resolution of the <code>[PROPERTY_B]</code> "2.14% Property Tax Anomaly"</h2>
      <div class="callout callout-warn">
        <strong>Why <code>$2,440</code> on a <code>$114,250</code> Roll Is NOT a 2.14% Ad Valorem Tax Rate:</strong><br>
        Under <strong>San Francisco Board of Supervisors Resolution No. 447-25</strong>, the official FY 2025-26 combined secured ad valorem tax rate is exactly <strong><code>1.18268325%</code></strong>. Multiplying <code>$114,250 &times; 1.18268325%</code> yields <strong><code>$1,350</code></strong> of ad valorem tax. The remaining <strong><code>~$1,090</code>/yr</strong> consists of <strong>flat per-parcel / per-unit voter-approved parcel taxes and direct charges</strong> (educator parcel taxes—explaining the <code>+18.4%</code> jump in 2018—plus local restoration/rent-board charges). Crucially, if <code>[PROPERTY_B]</code> is ever reassessed to <code>$1,800,000</code>, its tax becomes <code>$1,800,000 &times; 1.1827% + $1,110 = $22,400/yr</code> — <strong>NOT</strong> <code>$1,800,000 &times; 2.135% = $38,430/yr</code> (a <strong>$16,030/yr error</strong> in naive models).
      </div>
      {render_table(
          [
              ("Operating Line Item", False),
              ("Official Confirmed Rule / Tariff", False),
              ("2026 Modeled ($10)", True),
              ("2045 Projected ($10)", True),
              ("Status", False),
              ("Official Source", False),
          ],
          prop_b_pl_rows,
      )}
    </section>

    <section class="section-card">
      <h2><code>[PROPERTY_B]</code> Historical Assessment &amp; Tax Audit (2016–2026, Rounded to $10)</h2>
      <p class="section-desc">Line-by-line check against official BOE CCPI factors reveals a minor <strong>2022 roll irregularity</strong> (implied growth <code>~1.96%</code> vs. statutory <code>2.00%</code> cap, ~$50 below pure compounding) and missing 2026 figures (left blank).</p>
      {render_table(
          [
              ("Year", False),
              ("Owner-Reported Tax ($10)", True),
              ("Reported Tax %", False),
              ("Owner-Reported Roll ($10)", True),
              ("Reported Roll %", False),
              ("Official BOE CCPI Factor", False),
              ("Implied Bill / Roll", True),
              ("Official Confirmed Parcel Roll", False),
              ("Verification Status", False),
              ("Official Source", False),
          ],
          prop_b_hist_rows,
      )}
    </section>
    """
    (SUITE_DIR / "property-b.html").write_text(
        wrap_page(
            "property-b.html",
            "Category 04 · [PROPERTY_B] Detail",
            "[PROPERTY_B] — 3-Unit Cash-Flow Engine, Tax Rate Proof & Rent Control",
            "Detailed operating P&L, proof of ad valorem vs. flat parcel-tax mechanics, SFPUC water/wastewater tariff impact, and 1.6% SF Rent Ordinance growth constraints.",
            prop_b_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 5: taxes-and-laws.html — Tax & Inheritance Law + Cash Headroom
    # =========================================================================
    law_rows = [
        {
            "cells": [
                ("Federal Estate &amp; GST Tax (2026 / 2027)", False, False),
                ("<code>$15,000,000</code> (2026) · <code>$15,480,000</code> (2027) per decedent; <code>40%</code> top rate", False, False),
                ("Permanent under OBBBA / WFTC §70106 (IRC §2010(c)(3)), indexed annually from 2027. Married couples double headroom via timely Form 706 DSUE portability election.", False, False),
                (badge("verified", "VERIFIED IRS"), False, False),
                (src_link(URLS["irs_2027"], "IRS IR-2026-133 & Form 706"), False, False),
            ]
        },
        {
            "cells": [
                ("Federal Annual Gift Tax Exclusion", False, False),
                ("<code>$19,000</code> (2026) · <code>$20,000</code> (2027) per recipient/yr", False, False),
                ("Allows tax-free lifetime transfers of CASH without consuming unified estate exclusion. Never gift low-basis real estate during life (loses IRC §1014 step-up &amp; triggers Prop 19).", False, False),
                (badge("verified", "VERIFIED IRS"), False, False),
                (src_link(URLS["irs_2027"], "IRS IR-2026-133 & Form 709"), False, False),
            ]
        },
        {
            "cells": [
                ("California State &amp; Local Inheritance / Estate Tax", False, False),
                ("<code>$0</code> State Estate Tax · <code>$0</code> Inheritance Tax · <code>$0</code> Local Death Tax", False, False),
                ("CA R&amp;TC §13301 (Prop 6, 1982) bars state and local death/inheritance taxes; repealing §13301 requires a statewide voter ballot measure.", False, False),
                (badge("verified", "VERIFIED STATUTE"), False, False),
                (src_link(URLS["ca_rtc13301"], "CA R&TC §13301"), False, False),
            ]
        },
        {
            "cells": [
                ("Basis Step-Up vs. Irrevocable Trust Trap", False, False),
                ("100% FMV Step-Up if in Gross Estate (IRC §1014); <strong>No Step-Up</strong> if Excluded (Rev. Rul. 2023-2)", False, False),
                ("Revocable living trust real estate gets full date-of-death FMV basis ($0 pre-death cap gains). Moving [PROPERTY_A] into an estate-excluded irrevocable trust forfeits step-up!", False, False),
                (badge("verified", "VERIFIED IRS RULING"), False, False),
                (src_link(URLS["irs_rr2023_2"], "IRS Rev. Rul. 2023-2"), False, False),
            ]
        },
        {
            "cells": [
                ("Post-Inheritance Sale Capital Gains &amp; NIIT", False, False),
                ("Fed <code>0%/15%/20%</code> + <code>3.8%</code> NIIT + CA <code>1%–13.3%</code>", False, False),
                ("Applies ONLY to post-death appreciation above date-of-death FMV. IRC §121 excludes $250,000 single / $500,000 MFJ if heir occupies home 2 of 5 yrs before sale.", False, False),
                (badge("verified", "VERIFIED IRS & FTB"), False, False),
                (src_link(URLS["ftb_cg"], "FTB Capital Gains & IRS Topic 701"), False, False),
            ]
        },
        {
            "cells": [
                ("Proposition 19 Intergenerational Exclusion", False, False),
                ("Cap = FBYV + <code>$1,044,590</code> (Feb 2025–Feb 2027, rounded $10)", False, False),
                ("Requires BOTH transferor and transferee principal residence, move-in + BOE-266 within 1 yr, BOE-19-P within 3 yrs. Moving out later removes the exclusion on the next Jan 1 lien date.", False, False),
                (badge("verified", "VERIFIED BOE"), False, False),
                (src_link(URLS["boe_pub800"], "BOE Pub. 800-1 & LTA 2025/009"), False, False),
            ]
        },
        {
            "cells": [
                ("U.S. Treasury Interest State Tax Exemption", False, False),
                ("<code>0%</code> California State Income Tax on U.S. Treasury Interest", False, False),
                ("Under 31 U.S.C. §3124, U.S. Treasury bills/notes/bonds avoid up to 13.3% CA income tax, giving Treasuries a major after-tax edge over bank CDs/HYSA.", False, False),
                (badge("verified", "VERIFIED FEDERAL/CA"), False, False),
                (src_link(URLS["treasury"], "U.S. Treasury Curve & Federal Law"), False, False),
            ]
        },
        {
            "cells": [
                ("Pending Law Changes &amp; Ballot Initiatives", False, False),
                ("Initiative 25-0017 (Prop 19 Repeal Proposal); SB 293 / SB 974; CA Step-Up Reviews", False, False),
                ("Repeated initiatives to repeal Prop 19 have not been enacted into law as of Nov 2026; SB 974 / SB 293 refine special-needs trusts and wildfire rules without repealing Prop 19.", False, False),
                (badge("flagged", "MONITOR — NOT ENACTED"), False, False),
                (src_link(URLS["lao_250017"], "CA LAO Initiative 25-0017 Analysis"), False, False),
            ]
        },
    ]

    est_table_rows = []
    for yr in (2026, 2027, 2040, 2045, 2050):
        er = est_rows[yr]
        is_verified_yr = yr in (2026, 2027)
        est_table_rows.append({
            "cells": [
                (f"<strong>{yr}</strong>", False, False),
                (usd(er["exemption_single"]) if is_verified_yr else "", not is_verified_yr, True),
                (usd(er["exemption_single"]), False, True),
                (usd(er["exemption_married_dsue"]), False, True),
                (usd(er["both_properties_value"]), False, True),
                (f"<strong>{usd(er['cash_headroom_single_if_both_in_estate'])}</strong>", False, True),
                (f"<strong>{usd(er['cash_headroom_married_if_both_in_estate'])}</strong>", False, True),
                (usd(er["cash_headroom_50pct_cut_if_both"]), False, True),
                (badge("verified" if is_verified_yr else "modeled", "VERIFIED IRS" if is_verified_yr else "2.5% CPI PROJECTION"), False, False),
                (src_link(er["source_url"], "IRS Official Release"), False, False),
            ]
        })

    taxes_body = f"""
    <section class="section-card">
      <h2>Local, State &amp; Federal Tax Rules Governing the 2040–2050 Inheritance</h2>
      <p class="section-desc">Every statutory threshold, rate, filing deadline, and pending legislative proposal verified directly from primary government authorities.</p>
      {render_table(
          [
              ("Tax / Legal Domain", False),
              ("Verified Statutory Rule ($10 Rounded)", False),
              ("Strategic Impact on Decision", False),
              ("Status", False),
              ("Official Source", False),
          ],
          law_rows,
      )}
    </section>

    <section class="section-card">
      <h2>How Much Liquid Cash Can Be Inherited Tax-Free? (Headroom Projections 2026–2050)</h2>
      <p class="section-desc">Because the exact liquid cash inheritance amount is undisclosed (left blank on <a href="flagged-for-review.html">Flagged for Review</a>), this table shows the exact <strong>additional cash/securities</strong> that can pass free of the <code>40%</code> federal estate tax after subtracting projected real estate values—under both current law and a <strong>50% Congressional exemption rollback stress test</strong>.</p>
      <div class="callout callout-warn">
        <strong>Critical Estate-Tax Warning:</strong> Under current indexed law, a single decedent in 2045 can pass <strong>{usd(e2045['cash_headroom_single_if_both_in_estate'])}</strong> of liquid cash ON TOP OF both properties tax-free (or <strong>{usd(e2045['cash_headroom_married_if_both_in_estate'])}</strong> for a married couple electing DSUE portability). <strong>However, if Congress cuts the federal exclusion by 50% before 2045</strong> and both properties are in a single decedent's estate, tax-free cash headroom drops to just <strong>{usd(e2045['cash_headroom_50pct_cut_if_both'])}</strong> in 2045 (and <strong>{usd(est_rows[2050]['cash_headroom_50pct_cut_if_both'])}</strong> in 2050), with a <strong>40% tax</strong> on every dollar above that cap!
      </div>
      {render_table(
          [
              ("Year", False),
              ("Official Confirmed Single Exclusion", True),
              ("Modeled Single Exclusion", True),
              ("Married DSUE Exclusion", True),
              ("Combined [A]+[B] FMV", True),
              ("Tax-Free Cash Headroom (Single)", True),
              ("Tax-Free Cash Headroom (Married)", True),
              ("Cash Headroom If Congress Cuts 50%", True),
              ("Status", False),
              ("Official Source", False),
          ],
          est_table_rows,
      )}
    </section>
    """
    (SUITE_DIR / "taxes-and-laws.html").write_text(
        wrap_page(
            "taxes-and-laws.html",
            "Category 05 · Tax & Legal Framework",
            "Local, State & Federal Property, Capital Gains & Estate Tax Analysis",
            "Verified 2026–2027 IRS estate/gift thresholds, Prop 13 & Prop 19 formulas, IRC §1014 vs. Rev. Rul. 2023-2 trust rules, liquid inheritance headroom, and legislative risks.",
            taxes_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 6: projections.html — Year-by-Year 2026-2050 Projections
    # =========================================================================
    pa_table_rows = []
    for r in data["prop_a_projections"]:
        if r["year"] > 2050:
            continue
        yr = r["year"]
        grp = "key" if yr in (2026, 2030, 2035, 2040, 2045, 2050) else "detail"
        pa_table_rows.append({
            "filter": grp,
            "cells": [
                (f"<strong>{yr}</strong>", False, False),
                (usd(r["mv_low_3pct"]), False, True),
                (f"<strong>{usd(r['mv_base_4pct'])}</strong>", False, True),
                (usd(r["mv_high_5pct"]), False, True),
                (usd(r["prop13_fbyv"]), False, True),
                (usd(r["pre_inheritance_tax"]), False, True),
                (usd(r["prop19_cap_indexed"]), False, True),
                (usd(r["assessed_if_live_in"]), False, True),
                (usd(r["tax_if_live_in"]), False, True),
                (usd(r["tax_if_rented"]), False, True),
                (usd(r["total_carrying_live"]), False, True),
                (usd(r["total_carrying_rent"]), False, True),
                (src_link(URLS["boe_lta25009"], "BOE Prop 13/19"), False, False),
            ],
        })

    pb_table_rows = []
    for r in data["prop_b_projections"]:
        if r["year"] > 2050:
            continue
        yr = r["year"]
        pb_table_rows.append({
            "cells": [
                (f"<strong>{yr}</strong>", False, False),
                (usd(r["mv_base_3_5pct"]), False, True),
                (usd(r["prop13_fbyv"]), False, True),
                (usd(r["gross_rent_2_units"]), False, True),
                (usd(r["tax_held_as_is"]), False, True),
                (usd(r["ins_3unit_realistic"]), False, True),
                (usd(r["water_sewer_sfpuc"]), False, True),
                (usd(r["electricity_common"]), False, True),
                (usd(r["maintenance_3unit"]), False, True),
                (f"<strong>{usd(r['net_cash_flow_held_as_is'])}</strong>", False, True),
                (usd(r["net_cash_flow_if_reassessed"]), False, True),
                (src_link(URLS["sf_taxrate"], "SF BOS & SFPUC"), False, False),
            ]
        })

    proj_body = f"""
    <section class="section-card">
      <h2><code>[PROPERTY_A]</code> Year-by-Year Projections (2026–2050, Rounded to $10)</h2>
      <p class="section-desc">Shows projected market value (3%, 4% base, 5% scenarios), pre-inheritance Prop 13 assessed value and tax, biennially indexed Prop 19 exclusion cap, and Year-1 post-inheritance tax &amp; total carrying cost (property tax + CDI realistic insurance + water + solar/electric incl. 2040 NEM legacy sunset + maintenance) if inherited in each given year. Download CSV: <a href="data/property_a_projections_2026_2055.csv">property_a_projections_2026_2055.csv</a>.</p>
      <div class="filter-bar" data-filter-group="pa-rows">
        <span class="filter-label">Row Density:</span>
        <button type="button" class="tab-btn active" data-filter-value="all">All Years (2026–2050)</button>
        <button type="button" class="tab-btn" data-filter-value="key">Milestone Years Only (2026, 2030, 2035, 2040, 2045, 2050)</button>
      </div>
      {render_table(
          [
              ("Year", False),
              ("MV (3% Low)", True),
              ("MV (4% Base)", True),
              ("MV (5% High)", True),
              ("Prop 13 FBYV", True),
              ("Pre-Death Tax", True),
              ("Prop 19 Cap", True),
              ("New Roll (Live)", True),
              ("New Tax (Live)", True),
              ("New Tax (Rent)", True),
              ("Total Carry (Live)", True),
              ("Total Carry (Rent)", True),
              ("Official Formula", False),
          ],
          pa_table_rows,
          filter_group="pa-rows",
      )}
    </section>

    <section class="section-card">
      <h2><code>[PROPERTY_B]</code> Year-by-Year Cash-Flow Projections (2026–2050, Rounded to $10)</h2>
      <p class="section-desc">3-unit residence with 2 units rented (escalating at 1.8%/yr under SF Rent Board 60%-of-CPI cap; 1.6% in 2026–27) and Unit 3 preserved for primary occupancy. Download CSV: <a href="data/property_b_projections_2026_2055.csv">property_b_projections_2026_2055.csv</a>.</p>
      {render_table(
          [
              ("Year", False),
              ("MV (3.5% Base)", True),
              ("Prop 13 FBYV", True),
              ("2-Unit Gross Rent", True),
              ("Tax (Held As-Is)", True),
              ("3-Unit Insurance", True),
              ("SFPUC Water/Sewer", True),
              ("Common Electric", True),
              ("Maintenance", True),
              ("Net Cash Flow (As-Is)", True),
              ("Net CF If Reassessed", True),
              ("Official Source", False),
          ],
          pb_table_rows,
      )}
    </section>
    """
    (SUITE_DIR / "projections.html").write_text(
        wrap_page(
            "projections.html",
            "Category 06 · Multi-Decade Projections",
            "Year-by-Year Value, Tax Assessment & Cost Projections (2026–2050)",
            "Complete annual projections rounded to the nearest $10 for [PROPERTY_A] and [PROPERTY_B] under California Prop 13, Prop 19, utility tariffs, and inflation assumptions.",
            proj_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 7: decision-analysis.html — Live vs. Rent vs. Sell & Reinvest
    # =========================================================================
    dec_full_rows = []
    for r in dec_rows:
        dec_full_rows.append({
            "filter": str(r["inheritance_year"]),
            "cells": [
                (f"<strong>{r['inheritance_year']}</strong>", False, False),
                (f"<strong>{esc(r['strategy_code'])}</strong> · {esc(r['strategy_name'])}", False, False),
                (usd(r["prop_a_fmv_at_death"]), False, True),
                (usd(r["net_sale_proceeds_prop_a"]), False, True),
                (usd(r["yr1_prop_a_property_tax"]), False, True),
                (usd(r["yr1_combined_net_cash_flow"]), False, True),
                (f"<strong>{usd(r['ten_yr_after_tax_wealth'])}</strong>", False, True),
                (usd(r["breakeven_prop_a_rent_mo"]), False, True),
                (esc(r["verdict"]), False, False),
                (src_link(r["source_url"], "Primary Authority"), False, False),
            ],
        })

    sens_rows = [
        {
            "cells": [
                ("High Real-Estate Growth (5.0%/yr) vs. Modest Equities (6.0%/yr)", False, False),
                ("Narrows gap, but Selling + Equities/Treasuries still leads on risk-adjusted liquidity unless heir occupies [PROPERTY_A].", False, False),
                ("Renting [PROPERTY_A] still suffers immediate 100% Prop 19 tax reassessment + future 25%/13.3% depreciation/gain taxes.", False, False),
                (src_link(URLS["fhfa_hpi"], "FHFA CA HPI Series"), False, False),
            ]
        },
        {
            "cells": [
                ("100% Risk-Free Investor Preference (Zero Stock Market Volatility)", False, False),
                (f"Strategy S3B (U.S. Treasury Bond Ladder @ 4.88%–5.26%, 0% CA tax) yields {usd(d2045['S3B']['yr1_combined_net_cash_flow'])}/yr cash in 2045.", False, False),
                (f"Beats renting [PROPERTY_A] ({usd(d2045['S2']['yr1_combined_net_cash_flow'])}/yr) by +{usd(r10(d2045['S3B']['yr1_combined_net_cash_flow'] - d2045['S2']['yr1_combined_net_cash_flow']))}/yr in sovereign cash income.", False, False),
                (src_link(URLS["treasury"], "U.S. Treasury Daily Yields"), False, False),
            ]
        },
        {
            "cells": [
                ("Prop 19 Repeal Initiative Enacted Before 2040", False, False),
                (f"Would preserve [PROPERTY_A]'s low {usd(a2045['pre_inheritance_tax'])}/yr Prop 13 tax bill even if rented out (saving +{usd(r10(a2045['tax_if_rented'] - a2045['pre_inheritance_tax']))}/yr in 2045).", False, False),
                ("Re-evaluate Rent vs. Sell ONLY if voters pass a constitutional repeal of Prop 19 prior to death.", False, False),
                (src_link(URLS["lao_250017"], "LAO Initiative 25-0017 Brief"), False, False),
            ]
        },
        {
            "cells": [
                ("Heir Desires Silicon Valley Single-Family Living Over [PROPERTY_B]", False, False),
                (f"Move into [PROPERTY_A] within 1 yr (Strategy S1) to save {usd(r10(a2045['tax_if_rented'] - a2045['tax_if_live_in']))}/yr via Prop 19 cap; optionally lease [PROPERTY_B] Unit 3 under SF Rent Ordinance.", False, False),
                ("Leasing [PROPERTY_B] Unit 3 creates permanent SF just-cause tenancy—weigh carefully before signing a lease.", False, False),
                (src_link(URLS["sf_evict"], "SF Just Cause Evictions"), False, False),
            ]
        },
    ]

    dec_body = f"""
    <section class="section-card">
      <h2>Complete 2040, 2045 &amp; 2050 Decision Matrix (All Figures Rounded to $10)</h2>
      <p class="section-desc">Compares all four coordinated portfolio options after federal, state, and local property, transfer, income, dividend, and capital gains taxes. Download CSV: <a href="data/decision_comparison_2040_2045_2050.csv">decision_comparison_2040_2045_2050.csv</a>.</p>
      <div class="filter-bar" data-filter-group="dec-yr">
        <span class="filter-label">Filter Inheritance Year:</span>
        <button type="button" class="tab-btn active" data-filter-value="all">All Horizons (2040, 2045, 2050)</button>
        <button type="button" class="tab-btn" data-filter-value="2040">2040 Only</button>
        <button type="button" class="tab-btn" data-filter-value="2045">2045 Only</button>
        <button type="button" class="tab-btn" data-filter-value="2050">2050 Only</button>
      </div>
      {render_table(
          [
              ("Horizon", False),
              ("Strategy", False),
              ("[PROPERTY_A] FMV", True),
              ("Net Sale Proceeds", True),
              ("Yr-1 [A] Prop Tax", True),
              ("Yr-1 Combined Cash Flow", True),
              ("10-Yr Net Wealth", True),
              ("Break-Even [A] Rent/Mo", True),
              ("Strategic Verdict", False),
              ("Official Source", False),
          ],
          dec_full_rows,
          filter_group="dec-yr",
      )}
    </section>

    <section class="section-card">
      <h2>Economic, Legal &amp; Lifestyle Sensitivity Analysis</h2>
      <p class="section-desc">When could the ranking shift? Stress-testing appreciation, risk tolerance, ballot initiatives, and occupancy preferences.</p>
      {render_table(
          [
              ("Sensitivity Scenario", False),
              ("Quantified Effect", False),
              ("Decision Rule", False),
              ("Official Source", False),
          ],
          sens_rows,
      )}
    </section>
    """
    (SUITE_DIR / "decision-analysis.html").write_text(
        wrap_page(
            "decision-analysis.html",
            "Category 07 · Decision Optimization",
            "Live vs. Rent vs. Sell & Reinvest — Full After-Tax Decision Analysis",
            "Side-by-side comparison of post-inheritance cash flow, 10-year net worth, break-even rent, and U.S. Treasury vs. equity reinvestment across 2040, 2045, and 2050.",
            dec_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 8: inheritance-process.html — Step-by-Step Trust Process
    # =========================================================================
    steps = [
        ("Step 01 · Pre-Inheritance Trust &amp; Title Audit", "Now – Before 2040", "Confirm [PROPERTY_A] (and [PROPERTY_B] if applicable) is titled in [FAMILY_REVOCABLE_TRUST] (included in gross estate for IRC §1014 step-up—NOT an excluded irrevocable trust per Rev. Rul. 2023-2). Avoid California formal probate (9–18 months plus statutory Probate Code §§10800/10810 fees).", URLS["courts_trusts"], "Santa Clara Probate Trusts"),
        ("Step 02 · Death Certificates &amp; Trust Acceptance", "Days 1–30 After Death", "Obtain 10–15 certified death certificates; [SUCCESSOR_TRUSTEE] executes Acceptance of Trust, secures both properties, and verifies continuous HO-3 / landlord insurance coverage (notify insurer immediately of trustor's death to prevent vacancy/change-of-occupancy coverage gaps).", URLS["cdi_ins"], "CDI Residential Insurance"),
        ("Step 03 · Statutory Probate Code §16061.7 Notice", "Within 60 Days of Death", "[SUCCESSOR_TRUSTEE] must serve mandatory statutory Notification by Trustee under CA Probate Code §16061.7 on all beneficiaries and legal heirs, starting the strict 120-day trust contest limitation period (§16061.8).", URLS["ca_prob16061"], "CA Prob. Code §16061.7"),
        ("Step 04 · Trust EIN &amp; Fiduciary Banking", "Days 30–60 After Death", "Upon [DECEDENT]'s death, the revocable trust becomes irrevocable for tax purposes. Obtain an IRS Employer Identification Number (EIN) for the administrative trust and place liquid cash across FDIC-insured trust accounts ($250,000 per beneficiary/insurable capacity rules) or short-term U.S. Treasury bills.", URLS["fdic"], "FDIC Trust Deposit Rules"),
        ("Step 05 · Qualified Date-of-Death Real Estate Appraisal", "Months 1–4 After Death", "Hire a certified general real estate appraiser to document retrospective Date-of-Death Fair Market Value of [PROPERTY_A] (and [PROPERTY_B] if in estate). Essential both to substantiate IRC §1014 stepped-up tax basis ($0 pre-death gain) and to benchmark County Assessor Prop 19 valuation.", URLS["irs_basis"], "IRS Inherited Basis FAQ"),
        ("Step 06 · County Assessor Change in Ownership Statement", "Within 150 Days of Death", "File Form BOE-502-D (Change in Ownership Statement — Death of Real Property Owner) with the County Assessor pursuant to CA Revenue &amp; Taxation Code §480(b) to avoid statutory 10% tax penalties.", URLS["ca_rtc480"], "CA R&TC §480(b)"),
        ("Step 07 · Execute Live vs. Sell Decision Before 1-Year Clock", "Months 2–9 After Death", "Decide whether [BENEFICIARY] will live in [PROPERTY_A] long-term (Strategy S1) or sell [PROPERTY_A] tax-free under IRC §1014 while occupying [PROPERTY_B] Unit 3 (Strategies S3A/S3B). Note: Prop 19 reassessment applies from date of death until sold or exempted.", URLS["boe_prop19"], "CA BOE Prop 19 Portal"),
        ("Step 08 · IRS Form 706 Estate Tax Return / DSUE Portability", "Within 9 Months (+6-Mo Ext.)", "If gross estate + prior taxable gifts exceed the death-year federal basic exclusion ($15,000,000 in 2026; $15,480,000 in 2027; indexed in 2040s), file Form 706 and pay any 40% estate tax within 9 months (Form 4768 extends filing 6 months). File Form 706 on first spouse's death even below threshold to elect DSUE portability!", URLS["irs_706"], "IRS Form 706 Instructions"),
        ("Step 09 · If Living in [PROPERTY_A]: Move In + File BOE-266", "Strictly Within 1 Year of Death", "If Strategy S1 is chosen, [BENEFICIARY] must physically move into [PROPERTY_A] as principal residence AND file Form BOE-266 (Claim for Homeowners' Property Tax Exemption, $7,000) within 1 year of death to receive retroactive Prop 19 relief from date of death.", URLS["boe_lta25009"], "BOE LTA 2025/009"),
        ("Step 10 · File Prop 19 Claim (BOE-19-P / BOE-19-G)", "Within 3 Years (Before Any Sale)", "If claiming the Prop 19 family-home exclusion on [PROPERTY_A], submit Form BOE-19-P (parent-child) or BOE-19-G (grandparent-grandchild where qualifying parents are deceased) within 3 years of death and before transferring to any third party.", URLS["boe_pub800"], "BOE Pub. 800-1"),
        ("Step 11 · Record Affidavit of Death of Trustee &amp; Deed / Sale", "Months 4–12 After Death", "Record Affidavit of Death of Trustee + Preliminary Change of Ownership Report (PCOR BOE-502-A). Either close escrow on [PROPERTY_A] ($0 transfer tax on inheritance; 0.11% Santa Clara DTT on sale) and invest proceeds, or record Trust Transfer Deed to [BENEFICIARY].", URLS["scc_dtt"], "Santa Clara Clerk-Recorder"),
        ("Step 12 · Final Fiduciary Returns (Form 1041 / CA 541) &amp; Utility/Rent Compliance", "Following Tax Year", "File final individual Form 1040/540 for [DECEDENT] and fiduciary Form 1041 / CA Form 541 (issuing Schedule K-1 to [BENEFICIARY] for trust income/sale). Update water, CPUC solar interconnection, and SF Rent Board Housing Inventory filings for [PROPERTY_B].", URLS["ftb_gifts"], "CA FTB Inheritance & Trusts"),
    ]
    step_rows = [
        {
            "cells": [
                (f"<strong>{s[0]}</strong>", False, False),
                (f"<code>{s[1]}</code>", False, False),
                (s[2], False, False),
                (badge("verified", "STATUTORY STEP"), False, False),
                (src_link(s[3], s[4]), False, False),
            ]
        }
        for s in steps
    ]
    proc_body = f"""
    <section class="section-card">
      <h2>Chronological 12-Step Trust Inheritance Roadmap</h2>
      <p class="section-desc">Step-by-step execution timeline from pre-death trust verification through final distribution, statutory Assessor/BOE filings, and IRS/FTB tax compliance.</p>
      {render_table(
          [
              ("Phase & Step", False),
              ("Statutory Deadline", False),
              ("Required Action & Decision Gate", False),
              ("Status", False),
              ("Official Source", False),
          ],
          step_rows,
      )}
    </section>
    """
    (SUITE_DIR / "inheritance-process.html").write_text(
        wrap_page(
            "inheritance-process.html",
            "Category 08 · Execution Roadmap",
            "Step-by-Step Trust Property Inheritance Process & Deadlines",
            "Clear operational guide showing every California Probate Code, County Assessor, Board of Equalization, and IRS filing step upon inheriting by trust.",
            proc_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 9: flagged-for-review.html — Flagged for Review (Unverified + Irregularities + Repo Audit)
    # =========================================================================
    flags = [
        ("FL-01", "Liquid Cash / Financial Inheritance Amount", "", "Undisclosed ('considerable amount')", "Left blank per verification rule; modeled via exact tax-free headroom tiers ($14,151,790 single / $38,295,310 married in 2045; $2,080,030 if 50% cut).", URLS["irs_706"], "UNVERIFIED — BLANK"),
        ("FL-02", "[PROPERTY_A] 2026 Actual Property Tax Bill", "", "Not provided ('--')", "Left blank in historical table; never inferred or filled in.", URLS["scc_dtac"], "UNVERIFIED — BLANK"),
        ("FL-03", "[PROPERTY_B] 2026 Property Tax &amp; 2026 Assessment", "", "Not provided (2016–2025 only)", "Left blank in historical table; modeled 2026 Prop 13 roll labeled as scenario projection.", URLS["sf_taxrate"], "UNVERIFIED — BLANK"),
        ("FL-04", "[PROPERTY_B] 2.14% Implied Tax Ratio Distortion", "", "$2,440 bill on $114,250 roll", "Official SF FY25-26 ad valorem rate is 1.1827% ($1,350); remaining ~$1,090 is flat parcel charges (incl. +18.4% 2018 educator parcel-tax jump) that do NOT scale upon reassessment.", URLS["sf_taxrate"], "FLAGGED ANOMALY"),
        ("FL-05", "[PROPERTY_B] 2022 Roll Growth Deviation (~1.96% vs. 2.00%)", "", "$105,600 (2021) -> $107,660 (2022)", "Implied growth (~1.957%) is ~$50 below exact BOE 2.000% factor—indicates minor fixture/exemption adjustment or aggregator transcription variance.", URLS["boe_lta26002"], "FLAGGED ANOMALY"),
        ("FL-06", "Owner-Reported ~$1,500/yr Insurance Guess (Both Properties)", "", "$1,500/yr user estimate", "Confirmed official quote left blank; $1,500/yr is far below CDI statewide average (~$2,340/yr) and realistic $3.1M HO-3 (~$3,000/yr) or 3-unit SF landlord DP-3 (~$4,500/yr).", URLS["cdi_ins"], "FLAGGED UNDERSTATEMENT"),
        ("FL-07", "CPUC 20-Year Solar NEM Grandfathering Expiration", "", "-$10 to -$20/mo current credit", "Legacy NEM 1.0/2.0 retail export credits sunset 20 years after original interconnection (on or before 2046), shifting to Net Billing Tariff + monthly fixed charges.", URLS["cpuc_solar"], "FLAGGED TARIFF SUNSET"),
        ("FL-08", "Current Title, Trust Inclusion &amp; Transferor Principal Residence", "", "Not specified whether [PROPERTY_B] is already heir-owned or in trust", "Prop 19 applies ONLY to transferor's principal residence; IRC §1014 applies ONLY to assets included in decedent's gross estate (Rev. Rul. 2023-2).", URLS["irs_rr2023_2"], "UNVERIFIED LEGAL FACT"),
        ("FL-09", "[PROPERTY_A] &amp; [PROPERTY_B] Nov 2026 Market Values", "", "$3,100,000 & $1,800,000", "Owner estimates cannot be confirmed from an official government roll; date-of-death appraisal required.", URLS["irs_basis"], "UNVERIFIED INPUT"),
        ("FL-10", "Parcel-Specific Historical Assessments (2014–2026)", "", "Owner-supplied tables ($10 rounded)", "Official parcel roll lookup omitted to protect owner privacy; ratios verified against BOE CCPI factors.", URLS["boe_lta26002"], "UNVERIFIED ROLL"),
        ("FL-11", "[PROPERTY_A] Achievable Market Rent &amp; [PROPERTY_B] Unit 3 Rent", "", "Not provided", "Left blank in verified fact base; decision matrix reports exact break-even rent ($31,760/mo in 2045 vs. Treasuries).", URLS["irs_p527"], "UNVERIFIED — BLANK"),
        ("FL-12", "[PROPERTY_B] Lease Terms, Unit Legality &amp; Rent Board Registration", "", "$7,150/mo across 2 rented units", "Leases, certificate of occupancy for all 3 units, and SF Housing Inventory compliance unverified.", URLS["sf_rent"], "UNVERIFIED — REVIEW"),
        ("FL-13", "Utility Bills ([PROPERTY_A] Water $100–$150/mo; [PROPERTY_B] Water $330–$400/mo, Elec $30–$70/mo)", "", "Owner-supplied ranges", "Consistent with San Jose Water / SFPUC multi-family tariffs, but actual utility statements not inspected.", URLS["sfpuc"], "UNVERIFIED INPUT"),
        ("FL-14", "2040–2050 Future Tax Laws, Appreciation &amp; Market Returns", "", "Scenario parameters only", "Future HPI (3%/4%/5%), CPI (2.5%), equities (7.0%), and post-2027 tax brackets are non-guaranteed scenario assumptions.", URLS["lao_250017"], "SCENARIO BOUNDARY"),
    ]
    flag_rows = [
        {
            "cells": [
                (f"<strong>{f[0]}</strong>", False, False),
                (f[1], False, False),
                (f[2], True, False),
                (esc(f[3]), False, False),
                (esc(f[4]), False, False),
                (badge("flagged" if "FLAGGED" in f[6] else "unverified", f[6]), False, False),
                (src_link(f[5], "Official Authority"), False, False),
            ]
        }
        for f in flags
    ]

    audit_rows = [
        {
            "cells": [
                (f"<strong>{esc(a['id'])}</strong>", False, False),
                (esc(a["severity"]), False, False),
                (f"<code>{esc(a['target_files'])}</code>", False, False),
                (esc(a["issue"]), False, False),
                (esc(a["official_verification"]), False, False),
                (src_link(a["official_url"], "Official Verification Link"), False, False),
            ]
        }
        for a in audit_json
    ]

    flagged_body = f"""
    <section class="section-card">
      <h2>Part 1 · Unverified Items &amp; Property/Tax Irregularities (14 Items)</h2>
      <p class="section-desc">Every item that could not be independently confirmed from an official government source is left blank in the <em>Official Confirmed Value</em> column below and flagged for owner/professional review.</p>
      {render_table(
          [
              ("Flag ID", False),
              ("Item / Requirement", False),
              ("Official Confirmed Value", False),
              ("Owner / Prompt Input ($10)", False),
              ("Irregularity & Analytical Handling", False),
              ("Status", False),
              ("Official Source", False),
          ],
          flag_rows,
      )}
    </section>

    <section class="section-card">
      <h2>Part 2 · Line-by-Line Repository Audit Findings (<code>RA-01</code> – <code>RA-08</code>)</h2>
      <p class="section-desc">Results of auditing earlier parallel-session files in the repository without overwriting other sessions' owned files.</p>
      {render_table(
          [
              ("Audit ID", False),
              ("Severity", False),
              ("Reviewed Repo Files", False),
              ("Irregularity / Defect Identified", False),
              ("Official-Source Verification & Remediation", False),
              ("Official Source", False),
          ],
          audit_rows,
      )}
    </section>
    """
    (SUITE_DIR / "flagged-for-review.html").write_text(
        wrap_page(
            "flagged-for-review.html",
            "Category 09 · Quality Control & Audit",
            "Flagged for Review — Unverified Items, Roll Anomalies & Repo Audit",
            "Transparent register of all unconfirmed values (left blank), historical tax-roll anomalies, insurance/solar risks, and repository-wide verification findings.",
            flagged_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # PAGE 10: sources-ledger.html — Master Official Sources Ledger
    # =========================================================================
    src_rows = [
        {
            "cells": [
                (f"<code>{esc(s['id'])}</code>", False, False),
                (esc(s["jurisdiction"]), False, False),
                (esc(s["agency"]), False, False),
                (esc(s["title"]), False, False),
                (esc(s["verified_facts"]), False, False),
                (badge("verified", s["verified_date"]), False, False),
                (src_link(s["url"], "Open Official .gov Source"), False, False),
            ]
        }
        for s in sources_json
    ]

    csv_rows = [
        {
            "cells": [
                ('<a href="data/property_a_projections_2026_2055.csv">property_a_projections_2026_2055.csv</a>', False, False),
                ("30 annual rows (2026–2055) for [PROPERTY_A]: market value (3%/4%/5%), Prop 13 FBYV, Prop 19 cap, live vs. rent taxes, utilities, insurance, maintenance ($10 rounded).", False, False),
                (src_link(URLS["boe_lta25009"], "BOE Prop 13/19 Rules"), False, False),
            ]
        },
        {
            "cells": [
                ('<a href="data/property_b_projections_2026_2055.csv">property_b_projections_2026_2055.csv</a>', False, False),
                ("30 annual rows (2026–2055) for [PROPERTY_B]: 2-unit rent-controlled income, decomposed SF property tax, 3-unit insurance, SFPUC water/wastewater, NOI ($10 rounded).", False, False),
                (src_link(URLS["sf_taxrate"], "SF BOS Res. 447-25 & SFPUC"), False, False),
            ]
        },
        {
            "cells": [
                ('<a href="data/decision_comparison_2040_2045_2050.csv">decision_comparison_2040_2045_2050.csv</a>', False, False),
                ("12 strategy rows across 2040, 2045, and 2050 comparing Live (S1), Rent (S2), Sell->Equities (S3A), and Sell->U.S. Treasuries (S3B) ($10 rounded).", False, False),
                (src_link(URLS["irs_basis"], "IRS §1014 & U.S. Treasury"), False, False),
            ]
        },
        {
            "cells": [
                ('<a href="data/estate_tax_headroom_2026_2050.csv">estate_tax_headroom_2026_2050.csv</a>', False, False),
                ("Federal estate-tax thresholds & liquid cash inheritance headroom for 2026, 2027, 2040, 2045, and 2050 including 50% Congressional cut stress test ($10 rounded).", False, False),
                (src_link(URLS["irs_2027"], "IRS IR-2026-133 & Form 706"), False, False),
            ]
        },
    ]

    sources_body = f"""
    <section class="section-card">
      <h2>Master Official Primary-Source Verification Ledger ({len(sources_json)} Verified Authorities)</h2>
      <p class="section-desc">Zero commercial lead-generation sites or blogs are used anywhere in this suite. Every rule, rate, tariff, and statutory formula is verified from official federal, state, and local government records.</p>
      {render_table(
          [
              ("Ref ID", False),
              ("Jurisdiction", False),
              ("Government Agency", False),
              ("Official Publication / Statute", False),
              ("Verified Scope & Facts", False),
              ("Verified Date", False),
              ("Official Link", False),
          ],
          src_rows,
      )}
    </section>

    <section class="section-card">
      <h2>Reproducible Datasets (RFC-4180 Compliant CSVs, $10 Rounded)</h2>
      <p class="section-desc">Generated deterministically by <code>decision-suite/scripts/model_core.py</code>.</p>
      {render_table(
          [
              ("Dataset File", False),
              ("Contents & Scope", False),
              ("Primary Statutory Basis", False),
          ],
          csv_rows,
      )}
    </section>
    """
    (SUITE_DIR / "sources-ledger.html").write_text(
        wrap_page(
            "sources-ledger.html",
            "Category 10 · Primary Evidence",
            "Official Government Sources Ledger & Reproducible Datasets",
            "Complete line-by-line verification register linking every statutory rule, tax rate, utility schedule, and economic benchmark to official .gov authorities.",
            sources_body,
        ),
        encoding="utf-8",
    )

    # =========================================================================
    # Root Markdown Executive Summary (non-overlapping filename)
    # =========================================================================
    exec_md = f"""# Executive Summary — 2040–2050 Trust Property Inheritance Decision Analysis

**Session:** `arena-531aee5c-tino3` · **Reviewed Date:** November 10, 2026  
**Privacy Standard:** Strictly anonymized (`[PROPERTY_A]`, `[PROPERTY_B]`, `[DECEDENT]`, `[BENEFICIARY]`, `[SUCCESSOR_TRUSTEE]`). Zero names, street addresses, APNs, utility account numbers, or ZIP codes appear in this summary or in `decision-suite/`. Every dollar figure is rounded to the nearest **$10** increment. Unconfirmable parcel/cash figures are left blank in official-confirmed columns and published on `decision-suite/flagged-for-review.html`.

---

## 1. Bottom-Line Strategic Recommendation

1. **Keep `[PROPERTY_B]` (3-Unit Residence) Operating As-Is & Use Unit 3 as Primary Residence:**  
   `[PROPERTY_B]` generates **$85,800/yr** (`$7,150/mo`) today from 2 rented units (`{usd(b2045['gross_rent_2_units'])}/yr` projected in 2045 under the SF Rent Board's 60%-of-CPI cap; `1.6%` in 2026–27) and nets **`{usd(b_proj[2026]['net_cash_flow_held_as_is'])}/yr`** today (**`{usd(b2045['net_cash_flow_held_as_is'])}/yr`** in 2045) *while still providing a vacant 3rd unit for `[BENEFICIARY]` to live in at $0 lost rent*. Do not trigger an unexcluded reassessment on `[PROPERTY_B]`.
2. **Default Wealth-Maximizing Plan for `[PROPERTY_A]` (Single-Family Home with Solar): Sell Promptly After Inheritance & Reinvest (`Strategy S3A / S3B`):**  
   - **Zero Pre-Death Capital Gains Tax (`IRC §1014`):** Provided `[PROPERTY_A]` is held in a **revocable living trust** included in `[DECEDENT]`'s gross estate (and *not* an estate-excluded irrevocable grantor trust, which loses step-up under **IRS Rev. Rul. 2023-2**), its tax basis steps up to full Fair Market Value at death (`{usd(a2045['mv_base_4pct'])}` in the 2045 4%/yr base case). Selling promptly yields **`{usd(d2045['S3A']['net_sale_proceeds_prop_a'])}`** net cash in 2045 (`{usd(dec_rows[0]['net_sale_proceeds_prop_a'])}` in 2040; `{usd(dec_rows[8]['net_sale_proceeds_prop_a'])}` in 2050) after 5% selling costs and `0.11%` Santa Clara County Documentary Transfer Tax—with **$0 federal and $0 California capital gains tax** on pre-death appreciation.
   - **Superior After-Tax Return vs. Renting:** Reinvesting `{usd(d2045['S3A']['net_sale_proceeds_prop_a'])}` in a diversified equity portfolio (`7.0%` nominal scenario) reaches **`{usd(d2045['S3A']['ten_yr_after_tax_wealth'])}`** combined 10-year after-tax wealth (2045–2055), outperforming Renting `[PROPERTY_A]` (`{usd(d2045['S2']['ten_yr_after_tax_wealth'])}`) by **`+{usd(r10(d2045['S3A']['ten_yr_after_tax_wealth'] - d2045['S2']['ten_yr_after_tax_wealth']))}`**. Even a 100% sovereign **U.S. Treasury Bond Ladder** at verified Nov 9, 2026 yields (`4.88%` 10-Yr CMT, **100% exempt from California's up-to-13.3% state income tax** under `31 U.S.C. §3124`) produces **`{usd(d2045['S3B']['yr1_combined_net_cash_flow'])}/yr`** combined after-tax cash income vs. `{usd(d2045['S2']['yr1_combined_net_cash_flow'])}/yr` from renting `[PROPERTY_A]`.
3. **Conditional Lifestyle Alternative (`Strategy S1` — Live in `[PROPERTY_A]`):**  
   Retain `[PROPERTY_A]` *only* if `[BENEFICIARY]` genuinely wants `[PROPERTY_A]` as their long-term primary residence. Move in within **1 year** of death, file `BOE-266` (Homeowners' Exemption) within **1 year**, and file `BOE-19-P` within **3 years** to cap 2045 property taxes at **`{usd(a2045['tax_if_live_in'])}/yr`** instead of **`{usd(a2045['tax_if_rented'])}/yr`** (saving `{usd(r10(a2045['tax_if_rented'] - a2045['tax_if_live_in']))}/yr`). Moving out later terminates the Prop 19 cap on the next January 1 lien date (**BOE Pub. 800-1**).

---

## 2. Inheritance & Estate Tax Threshold Summary (Local, State & Federal)

| Jurisdiction / Scenario | 2026 Verified | 2027 Verified | 2040 Projected | 2045 Projected | 2050 Projected | Official Source |
|---|---:|---:|---:|---:|---:|---|
| Local & California Estate / Inheritance Tax | $0 | $0 | $0 | $0 | $0 | [CA R&TC §13301]({URLS['ca_rtc13301']}) |
| Federal Basic Exclusion (Single) | $15,000,000 | $15,480,000 | {usd(est_rows[2040]['exemption_single'])} | {usd(e2045['exemption_single'])} | {usd(est_rows[2050]['exemption_single'])} | [IRS IR-2026-133]({URLS['irs_2027']}) |
| Federal Married Exclusion (w/ DSUE Portability) | $30,000,000 | $30,960,000 | {usd(est_rows[2040]['exemption_married_dsue'])} | {usd(e2045['exemption_married_dsue'])} | {usd(est_rows[2050]['exemption_married_dsue'])} | [IRS Form 706]({URLS['irs_706']}) |
| Combined `[PROPERTY_A] + [PROPERTY_B]` Value | $4,900,000 | $5,087,000 | {usd(est_rows[2040]['both_properties_value'])} | {usd(e2045['both_properties_value'])} | {usd(est_rows[2050]['both_properties_value'])} | Scenario (4% / 3.5%) |
| **Tax-Free Cash Headroom (Single, Both Properties)** | **$10,100,000** | **$10,393,000** | **{usd(est_rows[2040]['cash_headroom_single_if_both_in_estate'])}** | **{usd(e2045['cash_headroom_single_if_both_in_estate'])}** | **{usd(est_rows[2050]['cash_headroom_single_if_both_in_estate'])}** | [IRS Form 706]({URLS['irs_706']}) |
| **Cash Headroom If Congress Cuts Exclusion 50%** | **$2,600,000** | **$2,653,000** | **{usd(est_rows[2040]['cash_headroom_50pct_cut_if_both'])}** | **{usd(e2045['cash_headroom_50pct_cut_if_both'])}** | **{usd(est_rows[2050]['cash_headroom_50pct_cut_if_both'])}** | [IRS Form 706 (40% above cap)]({URLS['irs_706']}) |

---

## 3. Key Forensic Findings & Flagged Irregularities

- **Resolution of `[PROPERTY_B]` 2.14% Tax Ratio:** Official SF BOS Res. 447-25 sets the FY 2025-26 secured rate at `1.18268325%` (`$1,350` on `$114,250`); the remaining `~$1,090/yr` is flat parcel taxes/assessments that do not multiply market value upon reassessment (preventing a `$16,030+/yr` tax overstatement).
- **`[PROPERTY_B]` 2022 Roll Deviation:** 2021–2022 assessment ratio (`~1.96%`) is `~$50` below the statutory `2.00%` BOE factor—flagged for parcel roll verification.
- **Insurance & Solar NEM Adjustments:** Owner's `~$1,500/yr` insurance estimate is flagged against CDI benchmarks (`~$3,000/yr` primary HO-3; `~$4,500/yr` 3-unit landlord policy), and `[PROPERTY_A]`'s legacy retail solar credit (`-$180/yr`) is modeled to sunset after its 20-year CPUC NEM grandfathering window (`D.22-12-056` / `D.24-05-028`).
"""
    (REPO_ROOT / "EXECUTIVE_SUMMARY_531AEE5C.md").write_text(exec_md, encoding="utf-8")
    print("Successfully generated all 10 HTML pages in decision-suite/ and EXECUTIVE_SUMMARY_531AEE5C.md.")


if __name__ == "__main__":
    main()
