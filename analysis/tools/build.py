#!/usr/bin/env python3
"""Static HTML dashboard generator for the Ownership-Distinction & 50-Year Black-Swan Edition.

Generates 12 clean, zero-JS, CSP-hardened dashboard pages under analysis/ (or an optional target
directory passed as argv[1] for byte-identical reproducibility checks).
Every table row includes an explicit Basis badge and at least one official https:// source link.
Every unconfirmed official figure is left blank ("Not verified — left blank") and listed on flagged.html.
"""
from __future__ import annotations
import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sources import SOURCES, REVIEWED_ON, SESSION_ID  # noqa: E402
import model as mdl  # noqa: E402

NAV = [
    ("index.html", "Overview Dashboard"),
    ("executive-summary.html", "Executive Summary"),
    ("ownership-distinction.html", "Ownership Distinction"),
    ("properties.html", "Properties & Running Costs"),
    ("projections.html", "50-Year Projections"),
    ("black-swan.html", "Black-Swan Conditions"),
    ("decision.html", "Decision Analysis"),
    ("taxes-estate.html", "Taxes, Thresholds & Laws"),
    ("inheritance-steps.html", "Step-by-Step Inheritance"),
    ("repo-audit.html", "Repository Review"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Official Source Ledger"),
]

BADGES = {
    "V": ("b-v", "Verified"),
    "O": ("b-o", "Owner-supplied"),
    "A": ("b-a", "Assumption"),
    "C": ("b-c", "Computed"),
    "U": ("b-u", "Unverified"),
}

BLANK = ("blank", "Not verified &mdash; left blank")
e = html.escape


def usd(v: float | int) -> str:
    val = int(round(float(v)))
    assert val % 10 == 0, f"Unrounded dollar value: {val}"
    return f"&minus;${abs(val):,}" if val < 0 else f"${val:,}"


def N(v: float | int) -> tuple[str, str]:
    return ("n", usd(v))


def P(pct_val: float, digits: int = 2) -> tuple[str, str]:
    return ("n", f"{pct_val:.{digits}f}%")


def cite(*sids: str, extra_local: tuple[str, str] | None = None) -> str:
    parts = []
    for sid in sids:
        s = SOURCES[sid]
        parts.append(f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["short"])}</a>')
    if extra_local:
        href, label = extra_local
        parts.append(f'<a href="{e(href)}">{e(label)}</a>')
    return "".join(parts)


LEGEND_HTML = (
    '<div class="legend">'
    + "".join(f'<span class="b {cls}">{lbl}</span>' for cls, lbl in BADGES.values())
    + " <strong>Basis key:</strong> <strong>Verified</strong> = read directly from an official government or Federal Reserve page on "
    + REVIEWED_ON
    + ". <strong>Owner-supplied</strong> = generalized household input (not independently confirmed on public rolls). "
    "<strong>Assumption</strong> = transparent scenario parameter. <strong>Computed</strong> = deterministic $10-rounded model output. "
    "<strong>Unverified</strong> = cannot be confirmed from an official source and is intentionally left blank (never inferred).</div>"
)

PRIVACY_HTML = (
    '<div class="privacy-box"><strong>Strict Privacy &amp; Anonymization Boundary.</strong> '
    "All personal, parcel, and location identifiers are excluded. Properties appear solely as "
    "<strong>[PROPERTY_A]</strong> (single-family home in County A, being inherited via trust) and "
    "<strong>[PROPERTY_B]</strong> (3-unit residential property in City B, already owned by [BENEFICIARY]). "
    "Individuals appear solely as [GRANTOR], [SUCCESSOR_TRUSTEE], and [BENEFICIARY]. Public assessment-roll "
    "benchmarks are generalized ($10,000 assessed-value increments; $100 historical tax-bill increments) and "
    "every projected or modeled figure is rounded to the nearest $10 so no figure can be traced back to a parcel online.</div>"
)


def render_table(caption: str, headers: list[str], rows: list[tuple], cls: str = "") -> str:
    ths = "".join(f'<th scope="col">{h}</th>' for h in headers + ["Basis", "Official Source"])
    body = []
    for r in rows:
        cells, basis_code, src_html = r[0], r[1], r[2]
        row_cls = r[3] if len(r) > 3 else ""
        tds = []
        for c in cells:
            if isinstance(c, tuple):
                tds.append(f'<td class="{c[0]}">{c[1]}</td>')
            else:
                tds.append(f"<td>{c}</td>")
        b_cls, b_lbl = BADGES[basis_code]
        body.append(
            f'<tr class="{row_cls}">{"".join(tds)}'
            f'<td><span class="b {b_cls}">{b_lbl}</span></td>'
            f'<td class="src">{src_html}</td></tr>'
        )
    return (
        f'<div class="table-wrap"><table class="{cls}"><caption>{caption}</caption>'
        f"<thead><tr>{ths}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def wrap_page(filename: str, title: str, eyebrow: str, h1: str, lead: str, content: str) -> str:
    nav_links = []
    for idx, (href, label) in enumerate(NAV, 1):
        cur = ' aria-current="page"' if href == filename else ""
        nav_links.append(f'<a{cur} href="{href}"><span>{idx:02d}</span>{e(label)}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Anonymized inheritance decision &amp; 50-year black-swan economic dashboard for [PROPERTY_A] and [PROPERTY_B].">
<meta name="referrer" content="no-referrer">
<meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{e(title)} &middot; Inheritance &amp; Black-Swan Decision Suite</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<aside>
  <a class="brand" href="index.html">Inheritance &amp; Black-Swan Suite<small>[PROPERTY_A] (Inherited) &amp; [PROPERTY_B] (Owned)</small></a>
  <div class="nav-label">DASHBOARD CATEGORIES</div>
  <nav aria-label="Analysis navigation">{"".join(nav_links)}</nav>
  <div class="aside-links">
    <div class="nav-label">RELATED EDITIONS</div>
    <a href="../index.html">&larr; Main Overview Edition</a>
    <a href="../stress.html">&larr; Main Stress-Tests Page</a>
    <a href="../plan/index.html">&larr; Break-Even Cross-Check</a>
  </div>
  <div class="aside-note">100% Anonymized &middot; $10-Rounded &middot; {len(SOURCES)} Official Sources Opened {REVIEWED_ON}</div>
</aside>
<main id="main">
  <div class="topbar">
    <span>{e(eyebrow)} &middot; Session {e(SESSION_ID)}</span>
    <span>Verified {REVIEWED_ON} &middot; Zero PII / $10 Increments</span>
  </div>
  <div class="hero">
    <div class="eyebrow">{e(eyebrow)}</div>
    <h1>{h1}</h1>
    <p class="lead">{lead}</p>
  </div>
  {content}
  {PRIVACY_HTML}
  <footer>
    <span>Educational &amp; quantitative planning framework — not legal, tax, or investment advice.</span>
    <span>Downloads: <a href="data/projections_50yr.csv">50-Yr CSV</a> &middot; <a href="data/black_swan_regimes.csv">Black-Swan CSV</a> &middot; <a href="data/ownership_distinction.csv">Ownership CSV</a> &middot; <a href="data/decision_matrix.csv">Decision CSV</a></span>
  </footer>
</main>
</body>
</html>
"""


def bar_cell(val: int, max_val: int) -> tuple[str, str]:
    pct = max(4, min(100, int(round(100.0 * val / max_val)))) if max_val > 0 else 0
    return ("n", f'{usd(val)} <span class="bar-track"><span class="bar-fill" style="width:{pct}%"></span></span>')


def render_all(target_root: Path) -> dict[str, str]:
    m = mdl.build_all()
    b40 = next(b for b in m["decision_blocks"] if b["year"] == 2040 and abs(b["g"] - 0.04) < 1e-9)
    b45 = next(b for b in m["decision_blocks"] if b["year"] == 2045 and abs(b["g"] - 0.04) < 1e-9)
    b50 = next(b for b in m["decision_blocks"] if b["year"] == 2050 and abs(b["g"] - 0.04) < 1e-9)
    b45_low = next(b for b in m["decision_blocks"] if b["year"] == 2045 and abs(b["g"] - 0.03) < 1e-9)
    b45_high = next(b for b in m["decision_blocks"] if b["year"] == 2045 and abs(b["g"] - 0.055) < 1e-9)

    r45 = {r["option"]: r for r in b45["rows"]}
    od45 = next(x for x in m["ownership_distinction"] if x["year"] == 2045)
    od26 = next(x for x in m["ownership_distinction"] if x["year"] == 2026)
    be = m["breakevens_2045"]
    p26 = m["projections_50yr"][0]
    p45 = next(x for x in m["projections_50yr"] if x["year"] == 2045)
    p76 = m["projections_50yr"][-1]

    pages: dict[str, str] = {}

    # =========================================================================
    # 01. OVERVIEW DASHBOARD (index.html)
    # =========================================================================
    max45 = max(r["wealth_nominal"] for r in b45["rows"])
    ov_rows = []
    for r in b45["rows"]:
        ov_rows.append((
            [
                r["name"],
                bar_cell(r["wealth_nominal"], max45),
                N(r["wealth_real_2026"]),
                N(r["gap_vs_best"]),
                N(r["first_yr_cashflow"]),
                N(r["first_yr_tax_a"]),
            ],
            "C",
            cite("irs_basis", "rtc_63_2", "usc_3124", "rtc_17043", extra_local=("decision.html#assumptions", "Assumptions")),
            "best" if r["gap_vs_best"] == 0 else "",
        ))

    bs_summary_rows = []
    for bs in m["black_swan_regimes"]:
        bs_summary_rows.append((
            [
                f"<strong>{e(bs['id'])}</strong>: {e(bs['title'])}",
                e(bs["winner_label"]),
                N(bs["sell_stock"]),
                N(bs["sell_barbell"]),
                N(bs["sell_treasury"]),
                N(bs["rent_a"]),
                N(bs["live_a_rent_u3"]),
            ],
            "C",
            cite(bs["source_id"], "rtc_51", extra_local=("black-swan.html", "Regime Details")),
            "best" if bs["winner_key"].startswith("sell_") else "flag-row",
        ))

    pages["index.html"] = wrap_page(
        "index.html",
        "Overview Dashboard",
        "Executive Decision Dashboard",
        "Inheritance &amp; 50-Year Economic Decision Dashboard",
        "Streamlined, line-by-line verified analysis for inheriting [PROPERTY_A] by trust (2040&ndash;2050) while [BENEFICIARY] already owns [PROPERTY_B] &mdash; tested across 50-year baseline projections and nine real-world Black-Swan economic regimes.",
        f"""
        <div class="callout win">
          <p><strong>Recommended Plan: Retain already-owned [PROPERTY_B] (continuing primary-residence occupancy in Unit 3 + 2 rental units), sell [PROPERTY_A] shortly after trust transfer using the IRC &sect; 1014 date-of-death basis step-up, and deploy net proceeds via a diversified Equity + CA-Tax-Exempt U.S. Treasury Barbell (or 24&ndash;36 month Treasury-to-Equity glidepath).</strong></p>
          <p><strong>Single Tactical Exception (Black-Swan Rule BS-4):</strong> If [GRANTOR] passes away <em>at the bottom of a severe (&minus;30%+) California housing bust</em>, do <strong>not</strong> fire-sale [PROPERTY_A] into a depressed market; lock in the depressed Proposition 13 reassessed base year value (<a href="{e(SOURCES['rtc_51']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 51</a>), rent [PROPERTY_A] out during the recovery, and re-evaluate sale once prices normalize.</p>
        </div>

        <div class="cards">
          <div class="card win">
            <div class="k">Best 2045 Baseline Plan</div>
            <div class="v">{usd(r45['sell_stock']['wealth_nominal'])}</div>
            <p>Sell [PROPERTY_A] &rarr; S&amp;P 500 ({usd(r45['sell_barbell']['wealth_nominal'])} in 60/40 Barbell), beating Rent by {usd(-r45['rent_a']['gap_vs_best'])} and Move-In by {usd(-r45['live_a_rent_u3']['gap_vs_best'])}.</p>
          </div>
          <div class="card">
            <div class="k">Ownership-Distinction Gain</div>
            <div class="v">+{usd(od45['headroom_gain_from_distinction'])}</div>
            <p>Extra 2045 federal estate-tax headroom ({usd(od45['cash_headroom_true_single'])} total) because [PROPERTY_B] is <em>already owned</em> by [BENEFICIARY], plus {usd(od45['b_annual_tax_saved'])}/yr Prop 13 tax saved on [PROPERTY_B].</p>
          </div>
          <div class="card">
            <div class="k">[PROPERTY_A] 2045 Tax Reset</div>
            <div class="v">{usd(r45['rent_a']['first_yr_tax_a'])}/yr</div>
            <p>Full reassessment if rented ({usd(r45['live_a_rent_u3']['first_yr_tax_a'])}/yr if [BENEFICIARY] moves in under Prop 19), up from ~{usd(p26['a_tax_unchanged'])}/yr today.</p>
          </div>
          <div class="card">
            <div class="k">Black-Swan Scoreboard</div>
            <div class="v">8 of 10 Regimes</div>
            <p>Selling [PROPERTY_A] (Equities, CA-Tax-Exempt Treasuries, or 60/40 Barbell) beats keeping it in 8 of 10 regimes; Move-In wins 0 of 10.</p>
          </div>
        </div>

        <h2>1. Baseline 2045 Inheritance Decision Snapshot (10-Year Post-Tax Terminal Wealth)</h2>
        {render_table(
            "2045 Trust Inheritance of [PROPERTY_A] (4.0%/yr baseline housing growth; all options liquidated after full federal + CA RTC 17043 taxes in 2055)",
            ["Strategy", "2055 Net Wealth", "In 2026 Dollars", "Gap vs. Best", "Year-1 Cash Flow", "Year-1 [PROPERTY_A] Tax"],
            ov_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Black-Swan &amp; Real-World 50-Year Regime Scoreboard (2045 Anchor)</h2>
        <p>Constant growth and inflation never hold over a 50-year horizon. Below is the head-to-head outcome across actual historical California macro replays (<a href="black-swan.html">Section 06</a>) and severe tail shocks:</p>
        {render_table(
            "Summary of 10-Year Post-Tax Net Wealth Across Baseline, Actual Historical Replays, and Severe Black-Swan Shocks",
            ["Economic Regime", "Winning Strategy", "Sell: 100% Stock", "Sell: 60/40 Barbell", "Sell: US Treasuries", "Keep & Rent A", "Move Into A"],
            bs_summary_rows,
        )}

        <h2>3. Navigate by Category</h2>
        <div class="cards">
          <div class="card"><div class="k">02 &middot; Synthesis</div><p><a href="executive-summary.html">Executive Summary</a>: Key numbers, core reasoning, and immediate action items.</p></div>
          <div class="card"><div class="k">03 &middot; Crucial Distinction</div><p><a href="ownership-distinction.html">Ownership Distinction</a>: Why [PROPERTY_B] already belonging to [BENEFICIARY] transforms the math.</p></div>
          <div class="card"><div class="k">04 &middot; Operating Reality</div><p><a href="properties.html">Properties &amp; Running Costs</a>: Generalized rolls, solar 20-yr NEM sunset, water, CDI insurance &amp; FAIR Plan.</p></div>
          <div class="card"><div class="k">05 &middot; 50-Yr Baseline</div><p><a href="projections.html">50-Year Projections (2026&ndash;2076)</a>: Year-by-year property values, assessed values, taxes &amp; net rent.</p></div>
          <div class="card"><div class="k">06 &middot; Stress Testing</div><p><a href="black-swan.html">Black-Swan Conditions</a>: 1976&ndash;2026 CA macro replay, stagflation, 2008 crash, Prop 8 relief &amp; seismic risk.</p></div>
          <div class="card"><div class="k">07&ndash;12 &middot; Law &amp; Audit</div><p><a href="decision.html">Decision Matrix</a>, <a href="taxes-estate.html">Estate Tax &amp; Law Watch</a>, <a href="inheritance-steps.html">Trust Steps</a>, <a href="repo-audit.html">Repo Audit</a> &amp; <a href="flagged.html">Flagged Items</a>.</p></div>
        </div>
        """,
    )

    # =========================================================================
    # 02. EXECUTIVE SUMMARY (executive-summary.html)
    # =========================================================================
    exec_rows = [
        (["Inherited Asset ([PROPERTY_A], County A)", N(mdl.INPUTS["a_value_2026"]), N(p45["a_val_base"]), N(p76["a_val_base"]),
          "100% IRC § 1014 basis step-up at death (if revocable trust); Prop 19 reassessment applies"], "O", cite("irs_basis", "irs_rr2023_2", "boe_prop19")),
        (["Already-Owned Asset ([PROPERTY_B], City B, 3 Units)", N(mdl.INPUTS["b_value_2026"]), N(p45["b_val_base"]), N(p76["b_val_base"]),
          "Excluded from [GRANTOR] estate; zero Prop 19 reassessment; zero basis step-up at [GRANTOR]'s death"], "O", cite("irs_estate", "rtc_60", "irs_basis")),
        (["[PROPERTY_A] Annual Property Tax (Unchanged vs. 2045 Rent / Live)", N(p26["a_tax_unchanged"]), N(r45["rent_a"]["first_yr_tax_a"]), N(p76["a_tax_2045_rent"]),
          f"Resets in 2045 from {usd(p45['a_tax_unchanged'])} (unchanged) to {usd(r45['live_a_rent_u3']['first_yr_tax_a'])} (Move-In) or {usd(r45['rent_a']['first_yr_tax_a'])} (Rent)"], "C", cite("rtc_63_2", "boe_lta25009", "cnty_a_rates")),
        (["[PROPERTY_B] Annual Property Tax (Protected Prop 13 Base)", N(p26["b_tax_protected"]), N(p45["b_tax_protected"]), N(p76["b_tax_protected"]),
          f"Remains capped at <=2%/yr under RTC § 51; saves {usd(od45['b_annual_tax_saved'])}/yr in 2045 vs. estate reset"], "C", cite("rtc_51", "rtc_60", "cityb_rate")),
        (["[PROPERTY_B] Net Annual Cash Flow (2 Rented Units; Unit 3 Lived In)", N(p26["b_net_cashflow"]), N(p45["b_net_cashflow"]), N(p76["b_net_cashflow"]),
          "Gross rent $85,800/yr in 2026 rising at 60% of CPI (1.5%/yr) minus vacancy, tax, water, electric, insurance & repairs"], "C", cite("cityb_rent", "irs_p527")),
        (["Federal Estate Tax Basic Exclusion (Single / Married Portability)", N(mdl.VERIFIED["fed_excl_2026"]), N(od45["fed_excl_single"]), N(m["ownership_distinction"][-1]["fed_excl_single"]),
          "$15,000,000 verified for 2026; $15,480,000 verified for 2027 (IR-2026-133); couple 2x with timely Form 706"], "V", cite("irs_estate", "irs_2027", "irs_i706")),
        (["Cash/Financial Inheritance Allowed Before Federal Estate Tax (Single)", N(od26["cash_headroom_true_single"]), N(od45["cash_headroom_true_single"]), N(m["ownership_distinction"][-1]["cash_headroom_true_single"]),
          "Computed after subtracting ONLY [PROPERTY_A] (since [PROPERTY_B] is already owned by [BENEFICIARY]); 40% tax above cap"], "C", cite("irs_estate", "usc_2001")),
        (["California State & Local Estate / Inheritance Tax", N(0), N(0), N(0),
          "Eliminated statewide since Jan 1, 2005; prohibited by voter-enacted CA R&TC § 13301"], "V", cite("sco_estate", "rtc_13301")),
    ]

    horizon_rows = []
    for blk_label, blk in [("2040 Inheritance (4% base)", b40), ("2045 Inheritance (3% low)", b45_low),
                           ("2045 Inheritance (4% base)", b45), ("2045 Inheritance (5.5% CA hist.-anchored)", b45_high),
                           ("2050 Inheritance (4% base)", b50)]:
        rm = {x["option"]: x["wealth_nominal"] for x in blk["rows"]}
        horizon_rows.append((
            [
                blk_label,
                N(blk["fmv_a"]),
                N(rm["sell_stock"]),
                N(rm["sell_barbell"]),
                N(rm["sell_treasury"]),
                N(rm["rent_a"]),
                N(rm["live_a_rent_u3"]),
                e(blk["winner"].split(";")[0]),
            ],
            "C",
            cite("irs_basis", "rtc_63_2", "usc_3124", "rtc_17043", extra_local=("decision.html", "Full Matrix")),
            "best" if "S&P 500" in blk["winner"] else "",
        ))

    pages["executive-summary.html"] = wrap_page(
        "executive-summary.html",
        "Executive Summary",
        "02 · Executive Summary",
        "Executive Summary: Key Findings, Numbers &amp; Strategic Plan",
        "Complete synthesis of property, tax, utility, insurance, estate-threshold, and 50-year Black-Swan findings for [PROPERTY_A] and [PROPERTY_B].",
        f"""
        <div class="callout win">
          <p><strong>1. Core Decision:</strong> Sell <strong>[PROPERTY_A]</strong> upon trust distribution (2040&ndash;2050) while its tax basis is stepped up to date-of-death Fair Market Value (<a href="{e(SOURCES['irs_basis']['url'])}" target="_blank" rel="noopener noreferrer">IRC &sect; 1014</a>), keep living in and operating already-owned <strong>[PROPERTY_B]</strong>, and invest net proceeds ({usd(b45['net_sale_proceeds'])} in the 2045 baseline) into a diversified <strong>Equity + CA-Tax-Exempt U.S. Treasury portfolio</strong>.</p>
          <p><strong>2. Why Moving Into [PROPERTY_A] Underperforms in All 10 Regimes:</strong> Moving into [PROPERTY_A] still triggers a jump in [PROPERTY_A]'s property tax to {usd(r45['live_a_rent_u3']['first_yr_tax_a'])}/yr in 2045 (because Proposition 19 caps the exclusion at base value plus an indexed $1,044,590 allowance), forfeits {usd(b45['live_cost_mo_real_2026'])}/mo in 2026-dollar wealth relative to selling, and forces an irreversible choice on [PROPERTY_B] Unit 3: either leave Unit 3 vacant ({usd(r45['live_a_rent_u3']['wealth_nominal'] - r45['live_a_keep_u3']['wealth_nominal'])} extra 10-yr penalty) or rent Unit 3 under permanent City B rent control (60% of CPI cap + just-cause eviction restrictions).</p>
          <p><strong>3. Why Keeping [PROPERTY_B] Is Mandatory:</strong> Because [PROPERTY_B] is <em>already owned</em> by [BENEFICIARY], [GRANTOR]'s death neither reassesses [PROPERTY_B]'s ultra-low ~{usd(mdl.INPUTS['b_av_2025'])} assessment base nor steps up its income-tax basis. Selling [PROPERTY_B] in 2045 would forfeit {usd(od45['b_annual_tax_saved'])}/yr in Prop 13 tax savings and trigger ~{usd(od45['b_sale_tax_no_stepup'])} in combined federal + California capital gains and depreciation recapture taxes.</p>
        </div>

        <h2>Key Quantitative Benchmarks (2026, 2045 &amp; 2076)</h2>
        {render_table(
            "Master Executive Summary Table ($10-Rounded Figures & Verified Statutory Thresholds)",
            ["Metric / Rule", "2026", "2045 (Mid-Window)", "2076 (50-Yr End)", "Governing Rule & Decision Impact"],
            exec_rows,
        )}
        {LEGEND_HTML}

        <h2>Decision Robustness Across Inheritance Timing (2040, 2045, 2050) &amp; Appreciation Bands</h2>
        {render_table(
            "10-Year Post-Tax Wealth Across Inheritance Years and Appreciation Rates",
            ["Scenario Window", "[PROPERTY_A] Value at Death", "Sell -> 100% Stock", "Sell -> 60/40 Barbell", "Sell -> Treasuries", "Keep & Rent A", "Move Into A", "Optimal Choice"],
            horizon_rows,
        )}

        <h2>Four High-Priority Pre-Inheritance Checks for [GRANTOR] &amp; [BENEFICIARY]</h2>
        <div class="cards">
          <div class="card">
            <div class="k">Check 1 &middot; Trust Type</div>
            <div class="v">IRC &sect; 1014</div>
            <p>Confirm the trust holding [PROPERTY_A] is a <strong>revocable living trust</strong> included in [GRANTOR]'s gross estate. Under <a href="{e(SOURCES['irs_rr2023_2']['url'])}" target="_blank" rel="noopener noreferrer">IRS Rev. Rul. 2023-2</a>, an excluded irrevocable trust loses the basis step-up (a ~{usd(r45['sell_stock']['wealth_nominal'] - m['black_swan_regimes'][-1]['sell_stock'])} tax hit in BS-8).</p>
          </div>
          <div class="card">
            <div class="k">Check 2 &middot; Spousal Portability</div>
            <div class="v">Form 706</div>
            <p>If [GRANTOR] is a married couple, file IRS Form 706 within 9 months (+6-mo Form 4768 extension) of the first spouse's death to lock in DSUE portability &mdash; doubling estate-tax-free capacity to {usd(od45['fed_excl_couple'])} in 2045.</p>
          </div>
          <div class="card">
            <div class="k">Check 3 &middot; Solar NEM Date</div>
            <div class="v">20-Yr Sunset</div>
            <p>Record [PROPERTY_A]'s exact utility interconnection date. Under <a href="{e(SOURCES['cpuc_nem']['url'])}" target="_blank" rel="noopener noreferrer">CPUC D.14-03-041</a>, retail NEM credits expire 20 years after interconnection (by or before 2046), shifting electricity from a ~{usd(abs(mdl.INPUTS['a_solar_credit_yr']))}/yr credit to a net cost unless paired with battery storage.</p>
          </div>
          <div class="card">
            <div class="k">Check 4 &middot; Crash Playbook</div>
            <div class="v">60/40 or DCA</div>
            <p>Avoid deploying 100% of [PROPERTY_A] sale proceeds into equities on Day 1 at peak valuations. Holding 40% in CA-tax-exempt U.S. Treasuries (<a href="{e(SOURCES['usc_3124']['url'])}" target="_blank" rel="noopener noreferrer">31 U.S.C. &sect; 3124</a>) protects against a 2008-style sequence-of-returns crash (BS-3).</p>
          </div>
        </div>
        """,
    )

    # =========================================================================
    # 03. OWNERSHIP DISTINCTION (ownership-distinction.html)
    # =========================================================================
    dist_comp_rows = [
        (["Current Legal &amp; Beneficial Owner (2026)", "[GRANTOR] (held for trust transfer in 2040&ndash;2050)", "[BENEFICIARY] (already owned outright / outside [GRANTOR]'s trust)"], "O", cite("irs_estate", "rtc_60")),
        (["Included in [GRANTOR]'s Federal Gross Estate (IRC &sect; 2031)?", "<strong>Yes</strong> &mdash; consumes [GRANTOR]'s federal estate exclusion dollar-for-dollar at date-of-death FMV", "<strong>No ($0 included)</strong> &mdash; preserves full exclusion for [PROPERTY_A] + cash inheritance"], "V", cite("irs_estate", "usc_2001")),
        (["Change in Ownership at [GRANTOR]'s Death (CA R&amp;TC &sect; 60)?", "<strong>Yes</strong> &mdash; triggers 100% FMV reassessment if rented, or capped Prop 19 reassessment if occupied within 1 yr", "<strong>No</strong> &mdash; zero reassessment; ultra-low ~{0} assessment base continues at &le;2%/yr".format(usd(mdl.INPUTS["b_av_2025"]))], "V", cite("rtc_60", "rtc_63_2", "rtc_51")),
        (["Income-Tax Basis Step-Up at [GRANTOR]'s Death (IRC &sect; 1014)?", "<strong>Yes (100% FMV reset)</strong> if held in revocable trust &mdash; near-zero capital gains tax on immediate post-death sale", "<strong>No ($0 step-up)</strong> &mdash; selling [PROPERTY_B] triggers up to 37.1% LTCG + 42.1% &sect; 1250 recapture tax"], "V", cite("irs_basis", "irs_rr2023_2", "rtc_17043")),
        (["Primary-Residence &amp; Rent-Control Constraint", "Requires [BENEFICIARY] to move in within 1 yr &amp; file BOE-266 + BOE-19-P to save ~{0}/yr in 2045 tax".format(usd(r45["rent_a"]["first_yr_tax_a"] - r45["live_a_rent_u3"]["first_yr_tax_a"])), "Unit 3 already provides a primary residence while Units 1&ndash;2 generate $7,150/mo; renting Unit 3 triggers permanent City B rent control"], "V", cite("rtc_218", "rtc_63_2", "cityb_laws", "cityb_rent")),
        (["Optimal Portfolio Role Upon Inheritance", "<strong>Liquidate tax-free</strong> (except during a &minus;30%+ housing trough) and diversify into financial assets", "<strong>Retain long-term</strong> as tax-sheltered primary residence + cash-flowing Prop 13 income base"], "C", cite("irs_basis", "rtc_51", "usc_3124")),
    ]

    od_table_rows = []
    for r in m["ownership_distinction"]:
        od_table_rows.append((
            [
                str(r["year"]),
                N(r["fed_excl_single"]),
                N(r["val_a_in_estate"]),
                N(r["val_b_outside_estate"]),
                N(r["cash_headroom_true_single"]),
                N(r["cash_headroom_prior_both"]),
                N(r["b_tax_already_owned"]),
                N(r["b_tax_if_inherited"]),
                N(r["b_sale_tax_no_stepup"]),
            ],
            "C" if r["year"] > 2027 else "V",
            cite("irs_estate", "irs_2027", "rtc_60", "rtc_17043"),
            "best" if r["year"] == 2045 else "",
        ))

    pages["ownership-distinction.html"] = wrap_page(
        "ownership-distinction.html",
        "Ownership Distinction Analysis",
        "03 · Critical Ownership Asymmetry",
        "[PROPERTY_A] (Inherited) vs. [PROPERTY_B] (Already Owned by [BENEFICIARY])",
        "Factoring in that [BENEFICIARY] already owns [PROPERTY_B] resolves the single largest ambiguity in prior repo models — expanding federal estate-tax cash headroom by $1,800,000 to $12,800,000+ over 50 years and locking in asymmetric tax incentives.",
        f"""
        <div class="callout">
          <p><strong>Why This Distinction Drives the Entire Decision:</strong> Earlier editions treated [PROPERTY_B] as potentially passing in the same estate as [PROPERTY_A]. In fact, <strong>[PROPERTY_A] is being inherited via trust</strong> while <strong>[PROPERTY_B] is already owned by [BENEFICIARY]</strong>. Under federal and California tax law, those two properties sit on opposite sides of every statutory boundary: estate inclusion (<a href="{e(SOURCES['irs_estate']['url'])}" target="_blank" rel="noopener noreferrer">IRC &sect; 2031</a>), property-tax change in ownership (<a href="{e(SOURCES['rtc_60']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 60</a>), cost-basis step-up (<a href="{e(SOURCES['irs_basis']['url'])}" target="_blank" rel="noopener noreferrer">IRC &sect; 1014</a>), and municipal rent control (<a href="{e(SOURCES['cityb_laws']['url'])}" target="_blank" rel="noopener noreferrer">City B Rent Ordinance</a>).</p>
        </div>

        <h2>1. Side-by-Side Statutory &amp; Financial Asymmetry</h2>
        {render_table(
            "Legal, Tax, and Cash-Flow Comparison Between Inherited [PROPERTY_A] and Already-Owned [PROPERTY_B]",
            ["Dimension", "[PROPERTY_A] (County A — Inherited via Trust)", "[PROPERTY_B] (City B — Already Owned by [BENEFICIARY])"],
            dist_comp_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Quantified Impact Across 50 Years (2026&ndash;2076): Estate Headroom, Prop 13 Shield &amp; Locked-In Gain</h2>
        <p>Notice three decisive numbers in 2045 (4% baseline appreciation): (1) Single-grantor cash/financial inheritance capacity before incurring any federal estate tax rises from {usd(od45['cash_headroom_prior_both'])} (if both homes were in the estate) to <strong>{usd(od45['cash_headroom_true_single'])}</strong> (+{usd(od45['headroom_gain_from_distinction'])}); (2) [PROPERTY_B]'s annual property tax stays at <strong>{usd(od45['b_tax_already_owned'])}</strong> instead of resetting to {usd(od45['b_tax_if_inherited'])}; and (3) selling [PROPERTY_B] would incur ~<strong>{usd(od45['b_sale_tax_no_stepup'])}</strong> in non-stepped-up capital gains and depreciation recapture taxes, whereas selling [PROPERTY_A] at inheritance incurs <strong>$0</strong> capital gains tax.</p>
        {render_table(
            "50-Year Ownership-Distinction Quantification (4.0%/yr Baseline Appreciation; 2.5%/yr Post-2027 Exclusion Indexing)",
            ["Year", "Single Estate Exclusion", "[PROPERTY_A] (In Estate)", "[PROPERTY_B] (Outside Estate)", "True Cash Headroom", "Prior (2-Home) Headroom", "[PROPERTY_B] Tax (Owned)", "[PROPERTY_B] Tax (If Reset)", "Tax Cost If [PROPERTY_B] Sold"],
            od_table_rows,
        )}

        <h2>3. The [PROPERTY_B] Unit 3 Rent-Control Trap When Moving Into [PROPERTY_A]</h2>
        <p>[PROPERTY_B] has 3 livable units: 2 rented for $7,150/month ($85,800/year) and 1 unrented unit available for [BENEFICIARY] to live in without losing rental income. Under <a href="{e(SOURCES['rtc_218']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 218</a> and <a href="{e(SOURCES['rtc_63_2']['url'])}" target="_blank" rel="noopener noreferrer">&sect; 63.2</a>, [BENEFICIARY] can claim only <strong>one</strong> principal residence. Moving out of [PROPERTY_B] Unit 3 into [PROPERTY_A] creates a costly dilemma:</p>
        <ul>
          <li><strong>Sub-Option L1 (Move into [PROPERTY_A] &amp; rent out [PROPERTY_B] Unit 3):</strong> Generates initial market rent on Unit 3 (~$3,580/month in 2026 dollars), but if [PROPERTY_B] was built on or before June 13, 1979 (<a href="{e(SOURCES['cityb_laws']['url'])}" target="_blank" rel="noopener noreferrer">City B Rent Board</a>), renting Unit 3 permanently subjects it to annual rent caps of 60% of CPI and strict just-cause eviction rules &mdash; yet still finishes <strong>{usd(-r45['live_a_rent_u3']['gap_vs_best'])}</strong> behind selling [PROPERTY_A].</li>
          <li><strong>Sub-Option L2 (Move into [PROPERTY_A] &amp; keep [PROPERTY_B] Unit 3 unrented):</strong> Preserves Unit 3 free of tenant eviction restrictions, but costs an additional <strong>{usd(r45['live_a_rent_u3']['wealth_nominal'] - r45['live_a_keep_u3']['wealth_nominal'])}</strong> over 10 years &mdash; finishing <strong>{usd(-r45['live_a_keep_u3']['gap_vs_best'])}</strong> behind selling [PROPERTY_A].</li>
        </ul>
        """,
    )

    # =========================================================================
    # 04. PROPERTIES & RUNNING COSTS (properties.html)
    # =========================================================================
    prop_compare_rows = [
        (["Estimated Market Value (Nov 2026)", N(mdl.INPUTS["a_value_2026"]), N(mdl.INPUTS["b_value_2026"]), "Owner November 2026 market estimates"], "O", cite("fred_casthpi")),
        (["Generalized Assessed Value (2025 / 2026)", N(mdl.INPUTS["a_av_2026"]), N(mdl.INPUTS["b_av_2025"]), "Generalized to $10,000 for parcel privacy; reflects long-held Prop 13 base"], "O", cite("rtc_51", "boe_lta26002")),
        (["Generalized Annual Property Tax Bill (2025)", N(mdl.INPUTS["a_bill_2025"]), N(mdl.INPUTS["b_bill_2025"]), "Generalized to $100; 2026 tax bills not yet provided (flagged)"], "O", cite("cnty_a_rates", "cityb_res447")),
        (["Verified Local Ad Valorem Tax Rate", ("n", "1.1258%&ndash;1.2409%"), ("n", "1.1816% (FY26&ndash;27)"), "County A range across 816 TRAs (1.18% modeled); City B exact FY26-27 rate"], "V", cite("cnty_a_rates", "cityb_rate", "cityb_res447")),
        (["Implied Non-Ad-Valorem Fixed Parcel Charges (2025)", N(mdl.FIXED_CHARGES_A_2025), N(mdl.FIXED_CHARGES_B_2025), "Bill minus (ad valorem rate &times; assessed value); ~45% of [PROPERTY_B]'s bill!"], "C", cite("cnty_a_rates", "cityb_res447")),
        (["Verified Official Insurance Premium Quote", BLANK, BLANK, "CDI survey is not a quote; FAIR Plan caps combined residential coverage at $3,000,000"], "U", cite("cdi_compare", "cdi_tips", "ins_10081")),
        (["Insurance Scenario Allowance (2026 Base; Tested at 4x)", N(mdl.INPUTS["a_ins_placeholder"]), N(mdl.INPUTS["b_ins_placeholder"]), "Owner $1,500/yr placeholder; 3-unit DP-3 &amp; high-value HO-3 tested up to 4x ($6,000/yr) in BS-7"], "A", cite("cdi_compare", "cdi_tips", extra_local=("flagged.html", "FL-03"))),
        (["Annual Water Cost (2026 Midpoint)", N(mdl.INPUTS["a_water_yr"]), N(mdl.INPUTS["b_water_yr"]), "[PROPERTY_A]: $100&ndash;$150/mo ($1,500/yr); [PROPERTY_B] (3 units): $330&ndash;$400/mo ($4,380/yr)"], "O", cite("irs_p527")),
        (["Annual Electricity / Solar Net Cost (2026)", N(mdl.INPUTS["a_solar_credit_yr"]), N(mdl.INPUTS["b_elec_yr"]), "[PROPERTY_A] solar nets &minus;$10 to &minus;$20/mo (&minus;$180/yr) until 20-yr CPUC NEM sunset; [PROPERTY_B]: $30&ndash;$70/mo"], "O", cite("cpuc_nem")),
        (["Post-NEM-Sunset Electricity Scenario ([PROPERTY_A], post-2044)", N(mdl.INPUTS["a_post_nem_elec_yr"]), N(mdl.INPUTS["b_elec_yr"]), "CPUC D.14-03-041 ends retail NEM 20 yrs after interconnection; shifts to Net Billing (D.22-12-056)"], "A", cite("cpuc_nem")),
        (["Annual Routine Maintenance &amp; Repairs Allowance (2026)", N(mdl.BASE["maint_a_2026"]), N(mdl.BASE["maint_b_2026"]), "1.0% of building value on [PROPERTY_A] ($9,300) vs. 1.5% on 3-unit [PROPERTY_B] ($10,800)"], "A", cite("irs_p527")),
        (["Current Gross Annual Rental Income (2026)", N(0), N(mdl.INPUTS["b_rent_2units_mo"] * 12), "[PROPERTY_B]: 2 units rented at $7,150/mo ($85,800/yr) + 1 unrented unit for primary residence"], "O", cite("cityb_rent", "irs_p527")),
    ]

    roll_audit_rows = [
        (["2014 &rarr; 2015", ("n", "+2.00%"), ("n", "1.998%"), ("n", "1.01998"), "[PROPERTY_A] roll ratio matches BOE 2015-16 CCPI factor"], "V", cite("boe_lta26002")),
        (["2015 &rarr; 2016", ("n", "+1.53%"), ("n", "1.525%"), ("n", "1.01525"), "Sub-2% CCPI year: both [PROPERTY_A] and [PROPERTY_B] match BOE factor"], "V", cite("boe_lta26002")),
        (["2016 &rarr; 2020 (each year)", ("n", "+2.00%/yr"), ("n", "2.62%&ndash;3.85%"), ("n", "1.02000"), "Prop 13 2% cap binding; [PROPERTY_B] tax bill jumped +18.4% in 2018 due to fixed parcel levies (FL-09)"], "V", cite("boe_lta26002", "cityb_res447", extra_local=("flagged.html", "FL-09"))),
        (["2020 &rarr; 2021", ("n", "+1.04%"), ("n", "1.036%"), ("n", "1.01036"), "Pandemic low-CPI year: exact 1.01036 factor confirmed on both properties"], "V", cite("boe_lta26002")),
        (["2021 &rarr; 2025 (each year)", ("n", "+2.00%/yr"), ("n", "2.51%&ndash;7.27%"), ("n", "1.02000"), "Prop 13 2% cap shielded owners from 5.56% (2022-23) &amp; 7.27% (2023-24) CA inflation; one minor ~1.96% [PROPERTY_B] roll variance flagged (FL-10)"], "V", cite("boe_lta26002", extra_local=("flagged.html", "FL-10"))),
        (["2025 &rarr; 2026", ("n", "+2.00%"), ("n", "3.307% (Aug&ndash;Aug)"), ("n", "1.02000"), "BOE LTA 2026/002 used Aug 2024&ndash;Aug 2025 DIR data due to fall 2025 federal shutdown; 2026 tax bills not yet supplied (FL-08)"], "V", cite("boe_lta26002", extra_local=("flagged.html", "FL-08"))),
    ]

    pages["properties.html"] = wrap_page(
        "properties.html",
        "Properties, Utilities, Solar & Insurance",
        "04 · Property Profiles & Operating Costs",
        "[PROPERTY_A] &amp; [PROPERTY_B]: Roll Audit, Utilities, Solar NEM &amp; Insurance",
        "Line-by-line audit of historical Prop 13 roll factors, fixed parcel charges, water and solar electricity mechanics, and California residential vs. multi-unit landlord insurance constraints.",
        f"""
        <h2>1. Side-by-Side Property &amp; Operating Cost Profile (2026 Baseline)</h2>
        {render_table(
            "Generalized Property Baselines, Verified Local Tax Rates, and Operating Cost Structure",
            ["Item", "[PROPERTY_A] (County A, Inherited)", "[PROPERTY_B] (City B, Already Owned)", "Verification &amp; Modeling Notes"],
            prop_compare_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Line-by-Line Audit of Historical Assessment Growth Against Official BOE CCPI Factors</h2>
        <p>Exact parcel roll figures from the brief are withheld from public tables so neither parcel can be looked up on public county tax portals. However, auditing the year-over-year percentage ratios against <a href="{e(SOURCES['boe_lta26002']['url'])}" target="_blank" rel="noopener noreferrer">BOE Letter to Assessors 2026/002</a> confirms two critical technical facts:</p>
        <ul>
          <li><strong>Fact 1 &mdash; Exact BOE Factor Alignment &amp; Missing $7,000 Exemption Netting:</strong> [PROPERTY_A]'s year-over-year ratios match the state factor to five significant digits (e.g., 1.01036 in 2021 and 1.01525 in 2016), proving the supplied figures are un-netted Factored Base Year Values before any $7,000 <a href="{e(SOURCES['rtc_218']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 218</a> Homeowners' Exemption. Confirming whether [GRANTOR] currently has BOE-266 on file for [PROPERTY_A] is flagged as <strong>FL-06</strong> because principal-residence status of [GRANTOR] is a prerequisite for Proposition 19.</li>
          <li><strong>Fact 2 &mdash; Non-Ad-Valorem Parcel Charges Explain Tax Rate Overstatement:</strong> Dividing [PROPERTY_B]'s 2025 tax bill (~$2,400) by its assessed value (~$110,000) yields an apparent ~2.1% rate, nearly double City B's verified 1.18268325% ad valorem rate (<a href="{e(SOURCES['cityb_res447']['url'])}" target="_blank" rel="noopener noreferrer">Res. 447-25</a>). The ~{usd(mdl.FIXED_CHARGES_B_2025)} difference consists of flat voter-approved parcel taxes and per-unit fees that do <strong>not</strong> multiply when assessed value resets.</li>
        </ul>
        {render_table(
            "Verification of Owner-Supplied Assessment Roll Growth Against BOE LTA 2026/002",
            ["Roll Period", "Observed Assessment Change", "Official CA CPI Change", "Official BOE Roll Factor", "Line-by-Line Audit Finding"],
            roll_audit_rows,
        )}

        <h2>3. Primary-Residence (HO-3) vs. 3-Unit Rental (DP-3) Insurance &amp; Solar Tariff Findings</h2>
        <div class="cards">
          <div class="card">
            <div class="k">Insurance Quotes Left Blank</div>
            <div class="v">CDI Verified</div>
            <p>Per <a href="{e(SOURCES['cdi_compare']['url'])}" target="_blank" rel="noopener noreferrer">CDI's official disclaimer</a>, state premium surveys are hypothetical comparisons, exclude wildfire/underwriting surcharges, and cannot serve as parcel quotes. Official quote cells remain blank (<a href="flagged.html">FL-03</a>); the $1,500/yr owner estimate is tested up to <strong>4&times; ($6,000/yr in 2026$)</strong> in Black-Swan BS-7 without changing the sell recommendation.</p>
          </div>
          <div class="card">
            <div class="k">FAIR Plan $3,000,000 Cap</div>
            <div class="v">$3,000,000 Max</div>
            <p><a href="{e(SOURCES['cdi_tips']['url'])}" target="_blank" rel="noopener noreferrer">CDI Residential Tips #08</a> confirms the California FAIR Plan caps all combined residential coverages at $3,000,000 and covers only fire, lightning, smoke, and internal explosion &mdash; requiring a supplemental Difference in Conditions (DIC) policy and separate earthquake insurance (<a href="{e(SOURCES['ins_10081']['url'])}" target="_blank" rel="noopener noreferrer">CA Ins. Code &sect; 10081</a>).</p>
          </div>
          <div class="card">
            <div class="k">Solar 20-Yr NEM Sunset</div>
            <div class="v">D.14-03-041</div>
            <p><a href="{e(SOURCES['cpuc_nem']['url'])}" target="_blank" rel="noopener noreferrer">CPUC Net Metering rules</a> explain both why [PROPERTY_A] currently earns $10&ndash;$20/mo (annual surplus paid at 2&ndash;3 cents/kWh wholesale NSC) and why that retail-offset tariff ends <strong>20 years from interconnection</strong> (on or before 2046), moving the home onto Net Billing (D.22-12-056) right in the 2040&ndash;2050 inheritance window.</p>
          </div>
        </div>
        """,
    )

    # =========================================================================
    # 05. 50-YEAR BASELINE PROJECTIONS (projections.html)
    # =========================================================================
    proj_a_rows = []
    proj_b_rows = []
    for row in m["projections_50yr"]:
        yr = row["year"]
        rc = "best" if yr in (2026, 2040, 2045, 2050, 2076) else ""
        proj_a_rows.append((
            [
                str(yr),
                N(row["a_val_low"]),
                N(row["a_val_base"]),
                N(row["a_val_high"]),
                N(row["a_av_unchanged"]),
                N(row["a_tax_unchanged"]),
                N(row["a_tax_2045_live"]),
                N(row["a_tax_2045_rent"]),
                N(row["a_water"]),
                N(row["a_elec"]),
                N(row["a_ins_scen"]),
                N(row["a_maint"]),
            ],
            "C",
            cite("rtc_51", "rtc_63_2", "cpuc_nem", extra_local=("decision.html#assumptions", "Assumptions")),
            rc,
        ))
        proj_b_rows.append((
            [
                str(yr),
                N(row["b_val_base"]),
                N(row["b_av_protected"]),
                N(row["b_tax_protected"]),
                N(row["b_gross_rent"]),
                N(row["b_op_costs"]),
                N(row["b_net_cashflow"]),
            ],
            "C",
            cite("rtc_51", "rtc_60", "cityb_rate", "cityb_rent"),
            rc,
        ))

    pages["projections.html"] = wrap_page(
        "projections.html",
        "50-Year Baseline Projections (2026-2076)",
        "05 · Full 50-Year Baseline Horizon",
        "Year-by-Year 50-Year Baseline Projections (2026&ndash;2076)",
        "Complete 51-year annual schedule ($10-rounded) for [PROPERTY_A] (including pre-inheritance Prop 13 path, 2045 Prop 19 Move-In vs. Rental tax reset, and 2045 post-NEM solar transition) and already-owned [PROPERTY_B]. For non-uniform multi-cycle paths, see Section 06 (Black-Swan Conditions).",
        f"""
        <div class="callout warn">
          <p><strong>Baseline vs. Real-World Volatility:</strong> Smooth compounding over 50 years (3.0% / 4.0% / 5.5% housing, 2.5% CPI) is a clean reference yardstick, <em>not</em> a forecast. Notice two structural kinks even in the baseline: (1) in <strong>2045</strong>, [PROPERTY_A]'s property tax jumps from {usd(p45['a_tax_unchanged'])} (unchanged) to <strong>{usd(p45['a_tax_2045_live'])}</strong> (Move-In) or <strong>{usd(p45['a_tax_2045_rent'])}</strong> (Rent), and solar transitions past its 20-year CPUC NEM window; (2) on already-owned <strong>[PROPERTY_B]</strong>, because City B caps sitting-tenant rent growth at 60% of CPI (1.5%/yr) while operating expenses rise with full CPI (2.5%/yr), real net rental margin gradually compresses late in the 50-year horizon unless natural tenant turnover resets rents to market (<a href="{e(SOURCES['cityb_rent']['url'])}" target="_blank" rel="noopener noreferrer">City B Rent Board</a>).</p>
        </div>

        <h2>1. [PROPERTY_A] — 50-Year Value, Assessment, Tax Reset &amp; Carrying Cost Schedule (2026&ndash;2076)</h2>
        {render_table(
            "[PROPERTY_A] Annual Projections 2026-2076 ($10-Rounded; Highlighted Benchmark Years: 2026, 2040, 2045, 2050, 2076)",
            ["Year", "Value (3%)", "Value (4% Base)", "Value (5.5% High)", "AV (Unchanged)", "Tax (Unchanged)", "Tax (2045 Live)", "Tax (2045 Rent)", "Water", "Electric / Solar", "Ins. (Scen.)", "Maint."],
            proj_a_rows,
        )}
        {LEGEND_HTML}

        <h2>2. [PROPERTY_B] (Already Owned) — 50-Year Protected Prop 13 Tax &amp; 3-Unit Rental Cash Flow (2026&ndash;2076)</h2>
        {render_table(
            "[PROPERTY_B] Annual Projections 2026-2076 (Zero Reassessment at [GRANTOR]'s Death; 2 Units Rented + Unit 3 Owner-Occupied)",
            ["Year", "Value (4% Base)", "Protected Prop 13 AV", "Protected Tax", "Gross Rent (2 Units)", "Total Operating Costs", "Pre-Tax Net Cash Flow"],
            proj_b_rows,
        )}
        """,
    )

    # =========================================================================
    # 06. BLACK-SWAN & REAL-WORLD 50-YEAR ECONOMIC CONDITIONS (black-swan.html)
    # =========================================================================
    episodes_rows = [
        (["1929&ndash;1932 Stock Crash &amp; Great Depression", "Dow fell &minus;89% (381.17 &rarr; 41.22); 25 years (until Nov 1954) to regain nominal peak", "Motivates BS-6 (Lost Equity Decade) &amp; holding 40% principal-protected U.S. Treasuries"], "V", cite("fed_1929")),
        (["1965&ndash;1982 Great Inflation &amp; Energy Shocks", "U.S. CPI rose from ~1% to nearly 15% (Mar 1980); CA CPI hit 17.316% in FY 1980-81 while Prop 13 capped roll growth at 2.0%", "Motivates BS-1A &amp; BS-2: Prop 13's 2% cap shields reassessed owners during runaway inflation while 60%-CPI rent caps lag"], "V", cite("fed_gi", "boe_lta26002")),
        (["September 1981 Interest-Rate Regime Peak", "10-Year U.S. Treasury monthly yield hit 15.32% (vs. 0.62% Jul 2020 trough &amp; 4.98% on 10 Nov 2026)", "Motivates BS-1A &amp; BS-2: high-rate regimes allow state-tax-exempt Treasury rollovers to out-earn unlevered rental yields"], "V", cite("fred_gs10", "treasury_cmt", "usc_3124")),
        (["1990&ndash;1996 California 6-Year Housing Slump", "FHFA CA House Price Index fell &minus;13.2% nominally (229.96 in 1990 Q3 &rarr; 199.59 in 1995 Q1) and ~&minus;28% in real terms", "Motivates BS-5 (Regional Bust): California real estate can stagnate for nearly a decade even while U.S. equities boom"], "V", cite("fred_casthpi")),
        (["2006&ndash;2012 Global Financial Crisis &amp; CA Housing Crash", "S&amp;P 500 plunged &minus;57% (Oct 2007&ndash;Mar 2009); CA HPI plunged &minus;41.0% (646.07 &rarr; 380.93) and took 13 years (to 2019 Q2) to recover; FY 2010-11 Prop 13 factor went negative (&minus;0.237%)", "Motivates BS-1B, BS-3 &amp; BS-4: proves sequence-of-returns danger AND why CA R&amp;TC &sect; 51(a)(2) (Prop 8) matters"], "V", cite("fed_gr", "fred_casthpi", "boe_lta26002", "rtc_51")),
        (["2021&ndash;2023 Post-Pandemic Inflation Spike", "U.S. CPI surged +9.1% YoY (Jun 2022); CA CPI hit +5.56% (2022-23) &amp; +7.27% (2023-24); electricity +13.7%", "Demonstrates sudden inflation spikes within modern low-rate regimes"], "V", cite("bls_ted2022", "boe_lta26002")),
        (["California Insurance Nonrenewals &amp; Seismic Exposure", "FAIR Plan caps residential coverage at $3,000,000 (fire/smoke only); earthquake excluded from standard policies (CA Ins. Code &sect; 10081)", "Motivates BS-7: keeping both [PROPERTY_A] &amp; [PROPERTY_B] concentrates 100% of net worth on one regional fault system"], "V", cite("cdi_tips", "ins_10081")),
    ]

    bs_nom_rows = []
    bs_real_rows = []
    for bs in m["black_swan_regimes"]:
        bs_nom_rows.append((
            [
                f"<strong>{e(bs['id'])}</strong>: {e(bs['title'])}",
                N(bs["fmv_2045_start"]),
                ("n", str(bs["prop8_years_rent"])),
                N(bs["sell_stock"]),
                N(bs["sell_barbell"]),
                N(bs["sell_treasury"]),
                N(bs["rent_a"]),
                N(bs["live_a_rent_u3"]),
                e(bs["winner_label"]),
            ],
            "C",
            cite(bs["source_id"], "rtc_51", "usc_3124"),
            "best" if bs["winner_key"].startswith("sell_") else "flag-row",
        ))
        bs_real_rows.append((
            [
                f"<strong>{e(bs['id'])}</strong>",
                N(bs["sell_stock_real"]),
                N(bs["sell_barbell_real"]),
                N(bs["sell_treasury_real"]),
                N(bs["rent_a_real"]),
                N(bs["live_a_rent_u3_real"]),
                N(bs["barbell_vs_rent"]),
            ],
            "C",
            cite(bs["source_id"], "bls_mlr100", "boe_lta26002"),
            "best" if bs["barbell_vs_rent"] > 0 else "flag-row",
        ))

    replay_rows = []
    for hr in m["historical_replay_50yr"]:
        sy = hr["sim_year"]
        rc = "flag-row" if hr["a_prop8_reduced"] == "Yes" else ("best" if sy in (2045, 2076) else "")
        replay_rows.append((
            [
                f"{sy} (replays {hr['analog_hist_year']})",
                P(hr["ca_hpi_pct"], 2),
                P(hr["ca_cpi_pct"], 2),
                ("n", f"{hr['prop13_factor']:.5f}"),
                P(hr["tsy_10y_pct"], 2),
                N(hr["a_market_val"]),
                N(hr["a_taxable_av"]),
                e(hr["a_prop8_reduced"]),
                N(hr["a_tax"]),
                N(hr["b_tax_protected"]),
                N(hr["b_gross_rent"]),
            ],
            "C",
            cite("fred_casthpi", "boe_lta26002", "fred_gs10", "rtc_51"),
            rc,
        ))

    pages["black-swan.html"] = wrap_page(
        "black-swan.html",
        "Black-Swan & 50-Year Real-World Regimes",
        "06 · Non-Uniform 50-Year Macroeconomics & Tail Risk",
        "Black-Swan Economic Conditions &amp; 50-Year Historical California Replay",
        "Deep-think macroeconomic stress testing built directly from 50 years of official California FHFA house prices (1976&ndash;2026), BOE Consumer Price Index &amp; Prop 13 factors, Federal Reserve 10-Year Treasury yields, and statutory Proposition 8 decline-in-value rules.",
        f"""
        <div class="callout win">
          <p><strong>What Deep Thinking About 50-Year Real-World Regimes Reveals (That Constant-Rate Tables Miss):</strong></p>
          <p><strong>1. A 100%-Equity Lump Sum Has Sequence-of-Returns Vulnerability, Solved by the 60/40 Treasury Barbell:</strong> If a 2008-style crash (&minus;50% stocks, &minus;35% housing) strikes right after inheriting in 2045 (<strong>BS-3</strong> &amp; <strong>BS-1B</strong>), 100% stocks drops to {usd(m['black_swan_regimes'][4]['sell_stock'])}, losing slightly to renting [PROPERTY_A] ({usd(m['black_swan_regimes'][4]['rent_a'])}, aided by 9 years of <a href="{e(SOURCES['rtc_51']['url'])}" target="_blank" rel="noopener noreferrer">Proposition 8</a> tax cuts). Yet selling into <strong>CA-tax-exempt U.S. Treasuries ({usd(m['black_swan_regimes'][4]['sell_treasury'])}) or a 60/40 Stock-Treasury Barbell ({usd(m['black_swan_regimes'][4]['sell_barbell'])})</strong> beats keeping [PROPERTY_A] by {usd(m['black_swan_regimes'][4]['barbell_vs_rent'])} to {usd(m['black_swan_regimes'][4]['sell_treasury'] - m['black_swan_regimes'][4]['rent_a'])}!</p>
          <p><strong>2. Inheriting <em>During</em> a Housing Crash Flips the Optimal Decision (BS-4):</strong> If [GRANTOR] dies at the bottom of a &minus;35% California housing bust, selling locks in a depressed {usd(m['black_swan_regimes'][5]['fmv_2045_start'])} price, whereas holding [PROPERTY_A] permanently locks in a 35% lower Proposition 13 Base Year Value ahead of the recovery &mdash; making <strong>Keep &amp; Rent ({usd(m['black_swan_regimes'][5]['rent_a'])}) beat Selling ({usd(m['black_swan_regimes'][5]['sell_stock'])}) by {usd(m['black_swan_regimes'][5]['rent_a'] - m['black_swan_regimes'][5]['sell_stock'])}</strong>.</p>
          <p><strong>3. Geographic &amp; Seismic Concentration Risk (BS-5 &amp; BS-7):</strong> Because [BENEFICIARY] already owns [PROPERTY_B] in the same metropolitan seismic zone, holding [PROPERTY_A] leaves 100% of household wealth exposed to a single tech-corridor downturn (BS-5: &minus;{usd(m['black_swan_regimes'][6]['sell_barbell'] - m['black_swan_regimes'][6]['rent_a'])} loss vs. Barbell) or uninsured earthquake deductible shock (<a href="{e(SOURCES['ins_10081']['url'])}" target="_blank" rel="noopener noreferrer">CA Ins. Code &sect; 10081</a>, BS-7: &minus;{usd(m['black_swan_regimes'][8]['sell_barbell'] - m['black_swan_regimes'][8]['rent_a'])} loss vs. Barbell).</p>
        </div>

        <h2>1. Official Historical Dislocations Anchoring the Stress Regimes</h2>
        {render_table(
            "Verified Historical U.S. & California Macroeconomic Shocks (Opened Primary Sources)",
            ["Historical Episode", "Verified Official Magnitude", "Mechanism Modeled in Decision Engine"],
            episodes_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Ten-Regime Black-Swan Decision Matrix — Nominal 2055 Post-Tax Wealth (2045 Inheritance)</h2>
        {render_table(
            "10-Year Post-Tax Terminal Wealth Across Baseline, Official Historical Slices, and Tail Shocks ($10-Rounded)",
            ["Regime", "2045 Start FMV", "Prop 8 Relief Yrs", "Sell: 100% Stock", "Sell: 60/40 Barbell", "Sell: US Treasuries", "Keep & Rent A", "Move Into A", "Regime Winner"],
            bs_nom_rows,
        )}

        <h2>3. Real Purchasing-Power Comparison (Deflated to 2026 Dollars by Cumulative Regime CPI)</h2>
        {render_table(
            "Inflation-Adjusted 2055 Wealth in 2026 Purchasing Power Across All 10 Regimes",
            ["Regime", "100% Stock (2026$)", "60/40 Barbell (2026$)", "US Treasuries (2026$)", "Keep & Rent A (2026$)", "Move Into A (2026$)", "60/40 Barbell Minus Rent (Nominal)"],
            bs_real_rows,
        )}

        <h2>4. Full 50-Year Non-Uniform California Historical Replay (2027&ndash;2076 Replaying Actual 1977&ndash;2026 Official Data)</h2>
        <p>Instead of assuming constant 4% growth and 2.5% inflation, the schedule below replays 50 consecutive years of <strong>actual California FHFA house-price changes (<a href="{e(SOURCES['fred_casthpi']['url'])}" target="_blank" rel="noopener noreferrer">FRED CASTHPI</a>), actual California CPI and Proposition 13 roll factors (<a href="{e(SOURCES['boe_lta26002']['url'])}" target="_blank" rel="noopener noreferrer">BOE LTA 2026/002</a>), and actual 10-Year U.S. Treasury yields (<a href="{e(SOURCES['fred_gs10']['url'])}" target="_blank" rel="noopener noreferrer">FRED GS10</a>)</strong>, with inheritance of [PROPERTY_A] occurring in 2045. Rows shaded pink show years where <strong>Proposition 8 (<a href="{e(SOURCES['rtc_51']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 51(a)(2)</a>)</strong> automatically cuts [PROPERTY_A]'s taxable value below its reassessed Prop 13 cap during the 2008-analog housing crash (simulated years 2058&ndash;2065):</p>
        {render_table(
            "50-Year Non-Uniform Path Simulation (2027-2076 Mapped Year-by-Year to Verified 1977-2026 California Macro Data)",
            ["Sim Year (Hist. Analog)", "CA HPI YoY", "CA CPI YoY", "Prop 13 Factor", "10-Yr Tsy", "[PROPERTY_A] Market Value", "[PROPERTY_A] Taxable AV", "Prop 8 Active?", "[PROPERTY_A] Tax", "[PROPERTY_B] Protected Tax", "[PROPERTY_B] Gross Rent"],
            replay_rows,
        )}
        """,
    )

    # =========================================================================
    # 07. DECISION ANALYSIS (decision.html)
    # =========================================================================
    dec_sections = []
    for blk in m["decision_blocks"]:
        if abs(blk["g"] - 0.04) < 1e-9 or blk["year"] == 2045:
            rows = []
            for r in blk["rows"]:
                rows.append((
                    [
                        r["name"],
                        N(r["wealth_nominal"]),
                        N(r["wealth_real_2026"]),
                        N(r["gap_vs_best"]),
                        N(r["first_yr_cashflow"]),
                        N(r["ten_yr_cashflow"]),
                        N(r["first_yr_tax_a"]),
                    ],
                    "C",
                    cite("irs_basis", "rtc_63_2", "usc_3124", "rtc_17043"),
                    "best" if r["gap_vs_best"] == 0 else "",
                ))
            dec_sections.append(render_table(
                f"Inheritance in {blk['year']} · House Appreciation {blk['g']*100:.1f}%/yr · [PROPERTY_A] Death FMV {usd(blk['fmv_a'])} · Net Sale Proceeds {usd(blk['net_sale_proceeds'])}",
                ["Strategy", " Wealth After 10 Yrs", "In 2026 Dollars", "Gap vs. Best", "Year-1 Cash Flow", "10-Yr Cash Sum", "Year-1 Tax on A"],
                rows,
            ))

    be_rows = [
        (["Minimum S&amp;P 500 Annual Return Needed to Beat Renting [PROPERTY_A] (2045 Base)", P(be["stock_return_pct"], 2), "Compare against 7.00% baseline assumption &amp; 11.40% verified TSP C Fund 38.8-year lifetime return"], "C", cite("tsp_cfund", "irs_tc409")),
        (["Sustained Annual Appreciation Needed on [PROPERTY_A] for Renting to Beat 7% Stocks", P(be["house_growth_pct"], 2), "Requires ~7.0%/yr sustained compounding from 2026 through 2055 despite full Prop 19 tax reset"], "C", cite("fred_casthpi", "rtc_63_2")),
        (["2026-Equivalent Monthly Rent Needed on [PROPERTY_A] to Tie 100% Stocks (at 4% growth)", N(be["rent_a_mo_2026_vs_stock"]), f"More than double the {usd(mdl.BASE['rent_a_mo_2026'])}/mo baseline rent assumption"], "C", cite("irs_p527", "civ_1947_12")),
        (["2026-Equivalent Monthly Rent Needed on [PROPERTY_A] to Tie 60/40 Stock-Treasury Barbell", N(be["rent_a_mo_2026_vs_barbell"]), "Break-even monthly rent in 2026 dollars against the lower-volatility 60/40 Barbell"], "C", cite("usc_3124", "irs_p527")),
    ]

    asm_rows = [
        (["Baseline Home Appreciation Band", "3.0% / 4.0% (base) / 5.5% per year", "50-year CA FHFA HPI (1976&ndash;2026) compounded at 6.10% nominally, but 2025&ndash;2026 flattened (+0.9%)"], "A", cite("fred_casthpi")),
        (["Baseline General CPI Inflation", "2.50% per year", "Above Fed 2% PCE goal; keeps Prop 13 2% cap binding in baseline (variable in Black-Swan suite)"], "A", cite("boe_lta26002", "bls_ted2022")),
        (["County A Ad Valorem Rate ([PROPERTY_A])", "1.18% + $830 (2025$) fixed charges", "Midpoint of County A verified TRA band (1.1258%&ndash;1.2409%); fixed charges grow with CPI, not value"], "A", cite("cnty_a_rates")),
        (["Equity Total Return &amp; Dividend Yield", "7.00% total (1.50% dividend)", "Conservative scenario below TSP C Fund 11.40% lifetime average; dividends taxed annually at 28.1%"], "A", cite("tsp_cfund", "irs_tc409", "irs_tc559")),
        (["CA-Tax-Exempt U.S. Treasury Yield", "4.98% par yield (27.8% fed+NIIT tax)", "Exact 10 Nov 2026 10-Yr U.S. Treasury CMT yield; 0% CA tax under 31 U.S.C. &sect; 3124"], "V", cite("treasury_cmt", "usc_3124")),
        (["Top Capital Gains &amp; Recapture Tax Rates", "37.1% LTCG / 42.1% Sec. 1250 (> $1,000,000)", "20% (or 25% recap) Fed + 3.8% NIIT + 12.3% CA base + 1.0% CA R&amp;TC &sect; 17043 above $1,000,000"], "V", cite("irs_tc409", "irs_tc559", "ftb_cg", "rtc_17043")),
        (["Selling Transaction Cost ([PROPERTY_A])", "5.11% of sale price", "5.00% brokerage/closing/prep allowance + 0.11% verified County A documentary transfer tax"], "A", cite("rtc_11911", "cnty_a_recorder")),
        (["[PROPERTY_A] Market Rent &amp; Building Share", "$6,500/mo (2026$); 30% building / 70% land", "Single-family rental exempt from AB 1482 (Civ. Code &sect; 1947.12(d)(5)); building depreciated over 27.5 yrs"], "A", cite("civ_1947_12", "irs_p527")),
        (["[PROPERTY_B] Rent Growth &amp; Unit 3 Market Rent", "1.50%/yr (60% of CPI); $3,580/mo Unit 3", "Matches City B Rent Board 60%-of-CPI formula (1.6% actual for 2026&ndash;27); Unit 3 set to average of Units 1&ndash;2"], "A", cite("cityb_rent", "cityb_laws")),
    ]

    pages["decision.html"] = wrap_page(
        "decision.html",
        "Decision Analysis & Break-Evens",
        "07 · Comprehensive Strategy Comparison",
        "Live, Rent, or Sell &amp; Reinvest? Full Multi-Window Decision Matrix",
        "Apples-to-apples 10-year post-inheritance wealth comparison across 2040, 2045, and 2050 — liquidating every option after all federal and California taxes at the end of the comparison window.",
        f"""
        <h2>1. Break-Even Thresholds (2045 Inheritance Baseline)</h2>
        {render_table(
            "Exact Switch Points Required to Overturn the 'Sell [PROPERTY_A] & Keep [PROPERTY_B]' Recommendation",
            ["Break-Even Parameter", "Required Threshold", "Context Against Official Data"],
            be_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Complete Decision Tables Across Inheritance Windows (2040, 2045, 2050) &amp; Growth Rates</h2>
        {"".join(dec_sections)}

        <h2 id="assumptions">3. Transparent Assumption &amp; Statutory Rate Register</h2>
        {render_table(
            "Model Parameters Separating Verified Legal Rates from Scenario Assumptions",
            ["Parameter", "Modeled Value", "Basis &amp; Official Anchor"],
            asm_rows,
        )}
        """,
    )

    # =========================================================================
    # 08. TAXES, ESTATE THRESHOLDS & LAW WATCH (taxes-estate.html)
    # =========================================================================
    estate_rows = []
    for r in m["ownership_distinction"]:
        estate_rows.append((
            [
                str(r["year"]),
                N(r["fed_excl_single"]),
                N(r["fed_excl_couple"]),
                N(r["val_a_in_estate"]),
                N(r["cash_headroom_true_single"]),
                N(r["cash_headroom_couple"]),
                N(r["cash_headroom_50pct_cut_true"]),
            ],
            "V" if r["year"] <= 2027 else "C",
            cite("irs_estate", "irs_2027", "usc_2001", "irs_i706"),
            "best" if r["year"] in (2026, 2027, 2045) else "",
        ))

    law_watch_rows = [
        (["Federal Estate &amp; Gift Exclusion (P.L. 119-21 / IR-2026-133)", "Enacted &amp; Active", "$15,000,000 (2026) and $15,480,000 (2027) per person; 40% tax above threshold; annual gift exclusion $19,000 (2026) / $20,000 (2027)"], "V", cite("irs_estate", "irs_2027", "usc_2001")),
        (["California Estate &amp; Inheritance Tax Prohibition (CA R&amp;TC &sect; 13301)", "Constitutional / Initiative Lock", "$0 state or local inheritance/estate tax; changing requires statewide voter approval"], "V", cite("sco_estate", "rtc_13301")),
        (["Proposed Prop 19 Repeal Initiative (A.G. File 25-0017 / #1994)", "Failed (18 May 2026)", "Would have restored pre-2021 parent-child tax exclusions; officially failed for insufficient signatures per CA SOS Memo #26138"], "V", cite("lao_250017", "sos_memo")),
        (["CA Mental Health Services Surtax (CA R&amp;TC &sect; 17043)", "Active (Unindexed $1,000,000)", "Adds +1% CA income tax above $1,000,000 (13.3% top CA rate); unindexed threshold catches virtually all 2040&ndash;2050 home-sale gains lacking step-up"], "V", cite("rtc_17043", "ftb_cg")),
        (["Revocable vs. Irrevocable Grantor Trust Basis Rule (Rev. Rul. 2023-2)", "Active IRS Binding Ruling", "Assets in an irrevocable trust excluded from the gross estate do NOT receive an IRC &sect; 1014 basis step-up at death"], "V", cite("irs_rr2023_2", "irs_basis")),
        (["Inherited Retirement Accounts 10-Year Rule (SECURE Act)", "Active", "If part of the cash/financial inheritance sits in a Traditional IRA/401(k), adult child beneficiaries must withdraw 100% by Year 10 as taxable ordinary income"], "V", cite("irs_ira")),
        (["CA Tenant Protection Act (AB 1482 / Civ. Code &sect; 1947.12)", "Sunsets 1 Jan 2030", "Single-family homes ([PROPERTY_A]) are exempt with mandatory lease notice; statute repeals Jan 1, 2030 unless extended by Legislature"], "V", cite("civ_1947_12")),
        (["City B Proposed Banked Rent Cap (BOS File No. 261020)", "Pending (Not Enacted as of Nov 2026)", "Would cap combined banked + capital-improvement passthrough rent increases on rent-controlled City B units ([PROPERTY_B]) at 10%/yr"], "V", cite("cityb_rent")),
    ]

    pages["taxes-estate.html"] = wrap_page(
        "taxes-estate.html",
        "Taxes, Estate Thresholds & Law Watch",
        "08 · Local, State & Federal Tax Architecture",
        "Inheritance Tax Thresholds, Cash Headroom &amp; Legislative Watch",
        "Exact federal, California, and local tax thresholds governing both [PROPERTY_A] and the 'considerable amount of money' included in the trust inheritance.",
        f"""
        <div class="callout">
          <p><strong>How Much Money Can Be Inherited Alongside [PROPERTY_A] Without Incurring Estate or Inheritance Tax?</strong></p>
          <p><strong>At the Local &amp; California State Level: Unlimited ($0 tax).</strong> Neither California nor County A / City B imposes any estate, inheritance, or death transfer tax (<a href="{e(SOURCES['rtc_13301']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 13301</a>; <a href="{e(SOURCES['sco_estate']['url'])}" target="_blank" rel="noopener noreferrer">CA Controller</a>; <a href="{e(SOURCES['rtc_11930']['url'])}" target="_blank" rel="noopener noreferrer">CA R&amp;TC &sect; 11930</a>), and inherited cash is not taxable income (<a href="{e(SOURCES['ftb_inh']['url'])}" target="_blank" rel="noopener noreferrer">FTB</a>) &mdash; <em>except</em> pre-tax Traditional IRAs/401(k)s, which are taxed as ordinary income when distributed over 10 years (<a href="{e(SOURCES['irs_ira']['url'])}" target="_blank" rel="noopener noreferrer">IRS</a>).</p>
          <p><strong>At the Federal Level:</strong> In 2026, a single decedent transfers up to <strong>$15,000,000</strong> tax-free (<strong>$15,480,000</strong> in 2027 per <a href="{e(SOURCES['irs_2027']['url'])}" target="_blank" rel="noopener noreferrer">IR-2026-133</a>; double with spousal portability on Form 706), with a <strong>40% tax</strong> (<a href="{e(SOURCES['usc_2001']['url'])}" target="_blank" rel="noopener noreferrer">26 U.S.C. &sect; 2001</a>) on excess value. Because <strong>[PROPERTY_B] is already owned by [BENEFICIARY]</strong>, ONLY [PROPERTY_A] counts against [GRANTOR]'s threshold &mdash; leaving <strong>{usd(od26['cash_headroom_true_single'])}</strong> of tax-free cash headroom in 2026 and <strong>{usd(od45['cash_headroom_true_single'])}</strong> (single) / <strong>{usd(od45['cash_headroom_couple'])}</strong> (married couple with portability) in the 2045 baseline!</p>
        </div>

        <h2>1. Federal Estate-Tax Threshold &amp; Additional Cash Inheritance Headroom (2026&ndash;2076)</h2>
        {render_table(
            "Maximum Cash & Financial Assets Inheritable Alongside [PROPERTY_A] Before Incurring 40% Federal Estate Tax",
            ["Year", "Single Exclusion", "Couple (Portability)", "[PROPERTY_A] Value", "Tax-Free Cash Room (Single)", "Tax-Free Cash Room (Couple)", "Cash Room If Congress Halves Exclusion (Single)"],
            estate_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Current &amp; Proposed Tax/Property Law Watch</h2>
        {render_table(
            "Verified Status of Federal, State, and Local Tax, Property, Solar & Rent Laws (Checked 11 Nov 2026)",
            ["Statute / Proposal", "Verified Status", "Impact on Decision &amp; Inheritance"],
            law_watch_rows,
        )}
        """,
    )

    # =========================================================================
    # 09. STEP-BY-STEP TRUST INHERITANCE PROCESS (inheritance-steps.html)
    # =========================================================================
    step_rows = [
        (["Pre-Transfer (2026&ndash;2040)", "Confirm revocable trust inclusion, non-pro-rata distribution power, BOE-266 on [PROPERTY_A], solar interconnection date, and Form 706 portability if a first spouse has died", "None (proactive)", "Preserves 100% IRC &sect; 1014 basis step-up (<a href='flagged.html'>FL-05</a>) and doubles estate exclusion"], "V", cite("irs_rr2023_2", "boe_lta26026", "irs_i706")),
        (["Step 1 &middot; Days 1&ndash;30", "Obtain certified death certificates; [SUCCESSOR_TRUSTEE] accepts trust administration, secures [PROPERTY_A] insurance continuation, and obtains a Trust EIN (IRS Form SS-4)", "Immediate", "Prevents coverage lapse as revocable trust becomes irrevocable"], "V", cite("prob_16061_7", "cdi_tips")),
        (["Step 2 &middot; Within 60 Days", "[SUCCESSOR_TRUSTEE] serves mandatory statutory Notification by Trustee on all beneficiaries and legal heirs", "<strong>60 days</strong> from death", "Required by CA Probate Code &sect; 16061.7; starts 120-day contest limitation window"], "V", cite("prob_16061_7")),
        (["Step 3 &middot; Date-of-Death Valuation", "Order a qualified date-of-death real-estate appraisal of [PROPERTY_A] (and inventory trust cash/securities); leave already-owned [PROPERTY_B] out of gross estate", "Within 3&ndash;6 months", "Establishes stepped-up basis under IRC &sect; 1014 &amp; evaluates BS-4 trough rule"], "V", cite("irs_basis", "irs_estate")),
        (["Step 4 &middot; Within 150 Days", "File County A Death of Real Property Owner Change in Ownership Statement (BOE-502-D) for [PROPERTY_A]", "<strong>150 days</strong> from death", "Mandatory under CA R&amp;TC &sect; 480; penalty of $100 or 10% of reassessed tax (up to $5,000) if ignored after assessor demand"], "V", cite("rtc_480")),
        (["Step 5 &middot; Strategic Branch Decision", "Compare [PROPERTY_A] appraisal against market cycle: (A) Normal/peak market &rarr; prepare [PROPERTY_A] for trust sale; (B) Severe &minus;30%+ trough &rarr; hold &amp; rent under depressed Prop 13 base; (C) Only if moving in &rarr; occupy within 1 yr", "Months 3&ndash;9", "Locks in tax-free sale proceeds or low-trough base year value"], "C", cite("irs_basis", "rtc_51", "rtc_63_2")),
        (["Step 6 &middot; Within 9 Months", "File IRS Form 706 if gross estate ([PROPERTY_A] + trust financial assets) exceeds federal exclusion OR to elect spousal DSUE portability; file Form 4768 for automatic 6-month filing extension; issue Form 8971 Schedule A basis statements if required", "<strong>9 months</strong> (+6-mo ext.)", "Avoids 40% estate-tax late penalties and preserves consistent-basis reporting"], "V", cite("irs_estate", "irs_i706")),
        (["Step 7 &middot; Within 1 Year (Only If Moving In)", "Move into [PROPERTY_A] as principal residence, file BOE-266 Homeowners' Exemption within 1 year, and file BOE-19-P within 3 years (note: terminates BOE-266 on [PROPERTY_B])", "<strong>1 year</strong> (occupancy &amp; BOE-266)", "Missing 1-year occupancy forfeits Prop 19 exclusion; late claim grants prospective relief only"], "V", cite("rtc_63_2", "boe_prop19", "boe_lta26026", "rtc_218")),
        (["Step 8 &middot; Deed Recording or Trust Sale", "Record Affidavit of Death of Trustee + Grant Deed (citing CA R&amp;TC &sect; 11930 for $0 transfer tax) or close sale directly from trust (paying 0.11% County A transfer tax on sale) and deploy proceeds into 60/40 Barbell / Treasury-to-Equity ladder", "Months 4&ndash;12", "Completes transfer; files Form 1041 / Schedule D reporting stepped-up basis"], "V", cite("rtc_11930", "cnty_a_recorder", "irs_basis", "usc_3124")),
        (["Step 9 &middot; Years 1&ndash;10", "Pay prorated SB 813 supplemental property tax bills (Dec 10 / Apr 10 regular cutoffs, 10% penalty); if Traditional IRAs were inherited, complete full distribution by Dec 31 of Year 10", "Up to <strong>End of Year 10</strong>", "Prevents property-tax delinquency and SECURE Act RMD penalties"], "V", cite("cnty_a_rates", "irs_ira")),
    ]

    pages["inheritance-steps.html"] = wrap_page(
        "inheritance-steps.html",
        "Step-by-Step Trust Inheritance Process",
        "09 · Operational & Statutory Execution Guide",
        "Step-by-Step Trust Inheritance Roadmap &amp; Statutory Deadlines",
        "Chronological execution checklist from pre-inheritance trust audit through post-death filings, property-tax notices, federal returns, and portfolio deployment.",
        f"""
        <h2>Complete Chronological Checklist &amp; Statutory Deadlines</h2>
        {render_table(
            "Step-by-Step California Revocable Trust Real-Property & Financial Inheritance Process",
            ["Stage / Window", "Required Action", "Statutory Deadline", "Financial / Legal Consequence"],
            step_rows,
        )}
        {LEGEND_HTML}
        """,
    )

    # =========================================================================
    # 10. REPOSITORY REVIEW & AUDIT (repo-audit.html)
    # =========================================================================
    audit_rows = [
        (["RA-01 &middot; Ownership Distinction Omitted in Existing Estate &amp; Reset Tables", "Root <code>scripts/model.py</code> &amp; <code>index.html</code>",
          f"Subtracted both [PROPERTY_A] and [PROPERTY_B] from [GRANTOR]'s estate exclusion and listed [PROPERTY_B]'s title as unknown, understating 2045 single estate-tax cash headroom by <strong>{usd(od45['headroom_gain_from_distinction'])}</strong>.", "Corrected in <code>analysis/</code> (<a href='ownership-distinction.html'>Section 03</a>); logged as CR-C02-1"], "V", cite("irs_estate", "rtc_60")),
        (["RA-02 &middot; CA Mental Health Services Surtax (+1% Over $1,000,000) Omitted", "Root <code>scripts/model.py</code>",
          "Used 12.3% top CA rate (36.1% combined LTCG) instead of 13.3% (37.1% LTCG / 42.1% Sec. 1250 recapture) under CA R&amp;TC &sect; 17043 on multi-million-dollar terminal sales.", "Corrected in <code>analysis/tools/model.py</code>"], "V", cite("rtc_17043", "ftb_cg")),
        (["RA-03 &middot; Proposition 8 Decline-in-Value Rule (CA R&amp;TC &sect; 51(a)(2)) Absent", "Root &amp; Cross-Check Stress Models",
          "Kept assessed value rising during housing crashes instead of capping taxable value at current FMV, overstating property taxes in severe housing busts (active in 9 of 10 years in BS-1B &amp; BS-3).", "Implemented year-by-year in <code>analysis/tools/model.py</code>"], "V", cite("rtc_51")),
        (["RA-04 &middot; 31 U.S.C. &sect; 3124 U.S. Treasury CA Tax Exemption Left Unverified", "Root <code>scripts/model.py</code>",
          "Noted Treasury state-tax exemption as 'assumed, not re-verified'; 10 Nov 2026 Treasury curve (4.98% 10-Yr) also superseded 9 Nov 2026 (4.88%).", "Directly opened &amp; verified on govinfo.gov and home.treasury.gov"], "V", cite("usc_3124", "treasury_cmt")),
        (["RA-05 &middot; Perpetual Solar Credit Assumed Through 2060", "Root <code>scripts/model.py</code>",
          "Held &minus;$180/yr solar profit constant through 2060, omitting CPUC D.14-03-041's mandatory 20-year legacy NEM sunset (which expires on or before 2046).", "Modeled explicitly in 50-year schedule"], "V", cite("cpuc_nem")),
        (["RA-06 &middot; Official Long-Run S&amp;P 500 &amp; Treasury Fund Returns Marked Unreadable", "Root <code>assets/sources.json</code>",
          "Reported that TSP C Fund's long-run average could not be read on <code>tsp.gov/fund-performance/</code>; opening <code>tsp.gov/c-fund/</code> &amp; <code>/g-fund/</code> provides official lifetime returns (11.40% C Fund since 1988; 4.65% G Fund since 1987).", "Opened &amp; verified directly"], "V", cite("tsp_cfund", "tsp_gfund")),
        (["RA-07 &middot; Twelve Excerpt-Only Citations in Earlier Source Ledger", "Root <code>assets/sources.json</code> (FL-23)",
          "Twelve entries relied on search-result snippets rather than opened pages.", f"All {len(SOURCES)} sources in <code>analysis/tools/sources.py</code> opened directly on official domains"], "V", cite("irs_i706", "irs_p527", "cityb_rent")),
    ]

    pages["repo-audit.html"] = wrap_page(
        "repo-audit.html",
        "Line-by-Line Repository Review",
        "10 · Independent Repository Verification",
        "Line-by-Line Repository Review &amp; Technical Audit Findings",
        "Results of auditing the existing repository scripts, source ledgers, and published tables line by line against primary federal, state, and local authorities.",
        f"""
        <h2>1. Verified Repository Audit Findings (RA-01 through RA-07)</h2>
        {render_table(
            "Line-by-Line Discrepancies and Omissions Identified Across Prior Repository Editions",
            ["Audit ID &amp; Issue", "Repository Location", "Verified Technical Finding", "Resolution in This Edition"],
            audit_rows,
        )}
        {LEGEND_HTML}

        <h2>2. Repository &amp; Privacy Governance Notes</h2>
        <ul>
          <li><strong>Non-Overlapping Multi-Session Coordination:</strong> Six concurrent 11 November 2026 branches modified overlapping root files; building this edition under <code>analysis/**</code> preserved 100% of prior sessions' pages (including root <code>stress.html</code> and <code>plan/**</code>) with zero destructive overwrites.</li>
          <li><strong>Historical Git Commit Disclosure:</strong> As documented on <code>COORDINATION.md</code> (R-13 / CR-5), commits from early sessions prior to PR #17 placed unrounded figures and postal codes into Git history; current served paths and allowlisted artifacts are sanitized, while destructive Git history rewriting remains an owner-only decision.</li>
        </ul>
        """,
    )

    # =========================================================================
    # 11. FLAGGED FOR REVIEW (flagged.html)
    # =========================================================================
    flag_rows = [
        (["FL-01", "[GRANTOR] Liquid / Financial Estate Balance ('Considerable Amount of Money')", BLANK,
          "Exact dollar balance not supplied; needed to test against single ({0} in 2045) or couple ({1}) estate headroom".format(usd(od45["cash_headroom_true_single"]), usd(od45["cash_headroom_couple"]))], "U", cite("irs_estate", "irs_2027")),
        (["FL-02", "Share of Financial Inheritance Held in Pre-Tax Traditional IRAs / 401(k)s", BLANK,
          "Pre-tax retirement accounts face mandatory 10-year taxable withdrawal under the SECURE Act in addition to estate inclusion"], "U", cite("irs_ira")),
        (["FL-03", "Parcel-Specific Homeowners (HO-3) &amp; 3-Unit Landlord (DP-3) Insurance Quotes", BLANK,
          "CDI survey is not an underwriting quote; $1,500/yr owner placeholder is unverified (tested at 4&times; = $6,000/yr in BS-7 with unchanged winner)"], "U", cite("cdi_compare", "cdi_tips")),
        (["FL-04", "Earthquake Insurance Policy Status &amp; Deductible on [PROPERTY_A] and [PROPERTY_B]", BLANK,
          "Excluded from standard policies under CA Ins. Code &sect; 10081; modeled as uninsured 20% building shock in BS-7"], "U", cite("ins_10081")),
        (["FL-05", "Trust Instrument Revocability &amp; Non-Pro-Rata Distribution Clauses", BLANK,
          "Must be revocable / estate-included for IRC &sect; 1014 step-up (Rev. Rul. 2023-2) and authorize non-pro-rata allocation if multiple beneficiaries exist"], "U", cite("irs_rr2023_2", "boe_lta26026")),
        (["FL-06", "[GRANTOR] Principal-Residence &amp; BOE-266 Status on [PROPERTY_A]", BLANK,
          "Roll ratios show un-netted FBYV; Prop 19 requires [PROPERTY_A] to be [GRANTOR]'s principal residence at transfer"], "U", cite("rtc_63_2", "rtc_218")),
        (["FL-07", "Exact County A Tax Rate Area (TRA) &amp; Solar Interconnection Date on [PROPERTY_A]", BLANK,
          "County A has 816 TRAs (1.1258%&ndash;1.2409%); solar interconnection year sets exact 20-year CPUC NEM 2.0 expiration date"], "U", cite("cnty_a_rates", "cpuc_nem")),
        (["FL-08", "2026 Secured Property Tax Bills for [PROPERTY_A] and [PROPERTY_B]", BLANK,
          "2026 tax bill was marked '--' for [PROPERTY_A] and omitted for [PROPERTY_B]; 2026 taxes in model are computed from verified roll rules"], "U", cite("cnty_a_rates", "cityb_rate")),
        (["FL-09", "[PROPERTY_B] Parcel-Tax Breakdown (~45% Fixed Charges &amp; +18.4% One-Year Jump)", BLANK,
          "~{0}/yr of [PROPERTY_B]'s ~{1} bill exceeds ad valorem tax; itemized secured bill needed to verify parcel-tax sunset dates".format(usd(mdl.FIXED_CHARGES_B_2025), usd(mdl.INPUTS["b_bill_2025"]))], "U", cite("cityb_res447", "cityb_rate")),
        (["FL-10", "Assessor Land vs. Improvement Split &amp; [PROPERTY_B] Certificate of Occupancy Date", BLANK,
          "Needed for exact 27.5-year MACRS rental depreciation and to confirm pre-June 13, 1979 City B rent-control coverage on Unit 3"], "U", cite("irs_p527", "cityb_laws")),
        (["FL-11", "Independent Market Rent Appraisal for [PROPERTY_A]", BLANK,
          "No parcel-specific official rent schedule exists; $6,500/mo scenario is paired with exact break-even ({0}/mo vs. stocks)".format(usd(be["rent_a_mo_2026_vs_stock"]))], "U", cite("civ_1947_12", "irs_p527")),
        (["FL-12", "[BENEFICIARY] Historical Cost Basis &amp; Prior Depreciation on Already-Owned [PROPERTY_B]", BLANK,
          "Needed only if [BENEFICIARY] ever considers selling [PROPERTY_B]; keeping [PROPERTY_B] avoids triggering this tax"], "U", cite("irs_tc409", "rtc_17043")),
    ]

    pages["flagged.html"] = wrap_page(
        "flagged.html",
        "Flagged for Review",
        "11 · Unverified Items & Irregularities",
        "Flagged for Review: Unverified Values (Left Blank) &amp; Roll Irregularities",
        "Every item that could not be confirmed from an official primary source is left blank below (never inferred) and paired with the governing official link for manual owner/advisor review.",
        f"""
        <div class="callout warn">
          <p><strong>Non-Blocking Review Policy:</strong> None of the twelve items below alters the baseline or Black-Swan default recommendation under tested sensitivity bands, unless (a) the trust holding [PROPERTY_A] is an excluded irrevocable trust (<strong>FL-05</strong>) or (b) [GRANTOR]'s financial estate exceeds the federal estate exclusion and requires liquidity planning (<strong>FL-01</strong>).</p>
        </div>

        <h2>Unverified Parcel, Trust &amp; Household Inputs (Intentionally Left Blank)</h2>
        {render_table(
            "Items Requiring Private Documents, Insurer Quotes, or Tax Advisor Confirmation",
            ["Flag ID", "Item", "Confirmed Official Value", "Why Flagged &amp; Decision Sensitivity"],
            flag_rows,
        )}
        {LEGEND_HTML}
        """,
    )

    # =========================================================================
    # 12. OFFICIAL SOURCE LEDGER (sources.html)
    # =========================================================================
    src_rows = []
    for idx, (sid, s) in enumerate(SOURCES.items(), 1):
        src_rows.append((
            [
                f"<code>{e(sid)}</code>",
                e(s["publisher"]),
                e(s["title"]),
                e(s["verifies"]),
                f"&ldquo;{e(s['quote'])}&rdquo;",
            ],
            "V",
            cite(sid),
        ))

    pages["sources.html"] = wrap_page(
        "sources.html",
        "Official Source Ledger",
        "12 · Primary Verification Library",
        f"Official Source Ledger ({len(SOURCES)} Primary Authorities Opened Directly)",
        f"Every authority below (IRS, U.S. Code, U.S. Treasury, Federal Reserve / FRED, TSP, BLS, CA Legislature, BOE, State Controller, FTB, CPUC, CDI, SOS, LAO, County A, and City B) was fetched and read directly on {REVIEWED_ON}.",
        f"""
        {render_table(
            f"Complete Primary-Source Verification Register ({len(SOURCES)} Sources, 100% Directly Opened on Official Domains)",
            ["ID", "Official Publisher", "Document / Section", "What It Verifies in This Edition", "Verified Excerpt"],
            src_rows,
        )}
        {LEGEND_HTML}
        """,
    )

    target_root.mkdir(parents=True, exist_ok=True)
    for fname, html_text in pages.items():
        (target_root / fname).write_text(html_text, encoding="utf-8")
    return pages


if __name__ == "__main__":
    dest = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent
    built = render_all(dest)
    print(f"Rendered {len(built)} HTML pages into {dest}")
