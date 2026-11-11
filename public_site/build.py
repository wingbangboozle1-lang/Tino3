#!/usr/bin/env python3
"""Build an evidence-only, privacy-safe public planning edition.

No owner-supplied valuation, assessment, rent, tax bill, expense, ZIP, or identity is a model
input. The 50-year reference is a replay of *published statewide history*, not a forecast
of either home. A blank means not independently confirmed by an official source.
"""
from __future__ import annotations

import csv
import html
import json
import shutil
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
DATA = HERE / "data"
LEDGER = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
SOURCES = LEDGER["sources"]

NAV = [
    ("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
    ("property-a.html", "Property A"), ("property-b.html", "Property B"),
    ("projections.html", "50-year reference"), ("decision.html", "Decision framework"),
    ("black-swans.html", "Black swans"), ("taxes.html", "Taxes & law"),
    ("inheritance.html", "Trust process"), ("review.html", "Flagged for review"),
    ("methodology.html", "Methodology"), ("sources.html", "Source library"),
]


def r10(value: Decimal | int | float) -> int:
    value = Decimal(str(value))
    return int((value / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 10)


def money(value: Decimal | int | float) -> str:
    return f"${r10(value):,}"


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def cite(*ids: str) -> str:
    if not ids:
        raise ValueError("An evidence row needs an official reference")
    return " · ".join(
        f'<a href="{e(SOURCES[sid]["url"])}" target="_blank" rel="noopener noreferrer" '
        f'data-source="{e(sid)}">{e(SOURCES[sid]["publisher"])} ↗</a>'
        for sid in ids
    )


def cell(value: object) -> str:
    if value is None:
        return '<span class="blank" aria-label="Not independently verified">—</span>'
    text = str(value)
    if text == "Not verified":
        return '<span class="tag unverified">Not verified</span>'
    if text == "Official rule":
        return '<span class="tag verified">Official rule</span>'
    if text in ("Illustrative", "Historical replay"):
        return f'<span class="tag illustrative">{e(text)}</span>'
    return e(text)


def table(headers: list[str], rows: list[tuple[list[object], tuple[str, ...]]], caption: str = "") -> str:
    if not rows:
        raise ValueError("An evidence table must not be empty")
    if any(len(values) != len(headers) - 1 for values, _ in rows):
        raise ValueError(f"Table cell mismatch: {headers}")
    h = ''.join(f'<th scope="col">{e(x)}</th>' for x in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{cell(v)}</td>' for v in values) +
                   f'<td class="source-cell">{cite(*src)}</td></tr>' for values, src in rows)
    cap = f'<caption>{e(caption)}</caption>' if caption else ''
    return f'<div class="table-scroll"><table>{cap}<thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'


def section(title: str, intro: str, content: str, *, id: str = "") -> str:
    attr = f' id="{e(id)}"' if id else ''
    return f'<section class="panel"{attr}><div class="section-head"><h2>{e(title)}</h2><p>{e(intro)}</p></div>{content}</section>'


def note(title: str, text: str, kind: str = "note") -> str:
    return f'<aside class="callout {e(kind)}"><strong>{e(title)}</strong><p>{e(text)}</p></aside>'


def page(filename: str, title: str, subtitle: str, contents: str, *, eyebrow: str = "EVIDENCE-FIRST PLANNING") -> str:
    nav = ''.join(f'<a href="{e(path)}"' + (' aria-current="page"' if path == filename else '') +
                  f'>{e(label)}</a>' for path, label in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An anonymized, source-linked guide to evaluating a future trust inheritance and an already-held residence.">
<meta name="referrer" content="no-referrer"><title>{e(title)} · Inheritance Atlas</title>
<link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#content">Skip to content</a>
<div class="layout"><aside class="sidebar" aria-label="Site navigation">
<a class="brand" href="index.html"><span class="brand-symbol" aria-hidden="true">◈</span><span>INHERITANCE<br><b>ATLAS</b></span></a>
<p class="sidebar-caption">PUBLIC PLANNING EDITION</p><nav aria-label="Sections">{nav}</nav>
<div class="sidebar-foot">No addresses · no parcel values · no tracking<br>Reviewed 11 Nov 2026</div></aside>
<div class="main-wrap"><header class="topline"><span>Trust planning / public edition</span><a href="review.html">Evidence gaps <span aria-hidden="true">↗</span></a></header>
<main id="content"><div class="page-title"><p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lead">{e(subtitle)}</p></div>{contents}
<footer><span>Planning guide, not legal, tax, appraisal or investment advice. Rules checked 11 November 2026.</span>
<span><a href="sources.html">Official sources</a> · <a href="review.html">Open items</a></span></footer>
</main></div></div></body></html>\n'''


def load_reference() -> list[dict]:
    with (DATA / "official_hpi_q2.csv").open(newline="", encoding="utf-8") as f:
        hp = list(csv.DictReader(f))
    with (DATA / "boe_ccpi_factors.csv").open(newline="", encoding="utf-8") as f:
        cc = list(csv.DictReader(f))
    if [int(x["year"]) for x in hp] != list(range(1976, 2027)):
        raise ValueError("Official HPI fixture must have every Q2 from 1976 to 2026")
    if [int(x["assessment_year"]) for x in cc] != list(range(1977, 2027)):
        raise ValueError("Official BOE fixture must have every factor from 1977 to 2026")
    if any(x["source"] != SOURCES["fhfa_hpi"]["url"] for x in hp):
        raise ValueError("HPI rows must cite the actual official series")
    if any(x["source"] != SOURCES["ca_assess_history"]["url"] for x in cc):
        raise ValueError("Assessment-factor rows must cite the official BOE table")
    if (hp[0]["q2_index"], hp[-1]["q2_index"]) != ("50.31", "974.97"):
        raise ValueError("Historical official-series endpoints changed: reverify before publishing")
    out = []
    baseline = Decimal(hp[0]["q2_index"])
    assessed_unit = Decimal(1_000_000)  # one illustrative unit, NOT an assessed value for either home
    cost_index = Decimal(100)
    for i, h in enumerate(hp):
        hist_year = int(h["year"])
        c = cc[i - 1] if i else None
        if c:
            factor = Decimal(c["factor"])
            if factor <= 0 or factor > Decimal("1.02"):
                raise ValueError("Historical factor outside statute: check official table")
            assessed_unit *= factor
            cost_index *= 1 + Decimal(c["ccpi_pct"]) / 100
        index = Decimal(h["q2_index"])
        out.append({
            "scenario_year": hist_year + 50, "replayed_year": hist_year,
            "official_hpi_q2": f"{index:.2f}",
            "hpi_index_base_100": f"{(100 * index / baseline):.2f}",
            "ccpi_pct": c["ccpi_pct"] if c else "",
            "official_factor": c["factor"] if c else "",
            "illustrative_assessed_per_million": r10(assessed_unit),
            "illustrative_one_percent_tax": r10(assessed_unit / 100),
            "illustrative_cost_index": f"{cost_index:.2f}",
            "property_a_value": "", "property_a_assessed": "", "property_a_tax": "",
            "property_a_insurance": "", "property_a_water": "", "property_a_electricity": "",
            "property_a_maintenance": "",
            "property_b_value": "", "property_b_assessed": "", "property_b_tax": "",
            "property_b_rent": "", "property_b_insurance": "", "property_b_water": "",
            "property_b_electricity": "", "property_b_maintenance": "",
            "hpi_source": SOURCES["fhfa_hpi"]["url"],
            "factor_source": SOURCES["ca_assess_history"]["url"],
            "status": "historical replay, not property forecast",
        })
    return out


def overview(ref: list[dict]) -> str:
    stats = '<div class="stat-grid">' + ''.join(
        f'<div class="stat"><small>{e(label)}</small><strong>{e(value)}</strong><span>{e(desc)}</span>{cite(src)}</div>'
        for label, value, desc, src in [
            ("Federal estate exclusion · 2026", "$15,000,000", "Per decedent, not a cash gift cap", "irs_estate"),
            ("Family-home add-on · now", "$1,044,590", "Rounded; conditional and only until Feb 2027", "ca_prop19_limit"),
            ("Base assessment factor · 2026", "1.02", "Not a promise of future annual increases", "ca_assess_history"),
            ("Long-run study window", "50 years", "Official statewide history replayed, not forecast", "fhfa_hpi"),
        ]) + '</div>'
    rows = [
        (["Property A", "Future trust transfer", "Inherited-property basis and property-tax reassessment depend on the deed, trust and use at transfer.", "Not verified"], ("irs_trust_basis", "ca_prop19_law")),
        (["Property B", "Already held by beneficiary", "A different person's death does not itself transfer B; do not count B as newly inherited without evidence of a retained interest.", "Official rule"], ("irs_estate", "ca_change")),
        (["Decision now", "Keep options open", "No official appraisal, rental quote, insurance price or cash balance supports a property-specific winner today.", "Not verified"], ("irs_basis", "cdi_survey")),
    ]
    links = '<div class="link-cards">' + ''.join(
        f'<a class="link-card" href="{e(path)}"><span>{e(n)}</span><strong>{e(t)}</strong><small>{e(d)} →</small></a>'
        for n, t, d, path in [
            ("01 / COMPARE", "The decision", "Sell, rent, occupy — conditional comparison", "decision.html"),
            ("02 / TIME", "50-year reference", "Real non-uniform history, no private dollars", "projections.html"),
            ("03 / RISK", "Black swans", "Inflation, housing and equity drawdowns", "black-swans.html"),
            ("04 / PROCESS", "Inheritance steps", "Deadlines and documents to verify privately", "inheritance.html"),
        ]) + '</div>'
    return page("index.html", "Clarity before a future inheritance", "One home may transfer through a trust. A separate residence is already owned and can continue producing rental income. This public edition keeps household finances off the web.",
        stats + section("What changes — and what does not", "The ownership distinction is the first decision gate, not an assumption that both properties enter one estate.",
                        table(["Asset", "Situation", "Planning consequence", "Status", "Official reference"], rows)) +
        section("Explore the plan", "Move from verified rules to clearly marked decision limits.", links) +
        note("Privacy over false precision", "The privately supplied property history and household amounts are withheld. An official county rule can explain a calculation, but it cannot verify a particular parcel without its records. Those dollar cells stay blank.", "warning"))


def summary() -> str:
    rows = [
        (["Sell A promptly", "Consider if after-tax proceeds exceed risk-adjusted rental/occupancy value.", "Near-death sale may have limited gain if §1014 applies; selling costs and possible estate tax still matter.", None], ("irs_basis", "irs_trust_basis", "irs_capital")),
        (["Rent A", "Consider if verified net rent plus expected appreciation beats after-tax reinvestment.", "Prop 19 family-home exclusion generally requires heir occupancy; letting instead can trigger market-value reassessment.", None], ("ca_prop19_law", "irs_rental")),
        (["Occupy A", "Consider for housing needs or if the family-home exclusion is actually available.", "Owner-occupied B space may be released for rent, but B stays already owned; lawful local tenancy rules still matter.", None], ("ca_prop19", "local_b_scope")),
        (["Keep B under current title", "Separate the existing rental's income, costs and basis from A's estate analysis.", "No automatic §1014 basis reset or property-tax transfer merely from A's future inheritance.", None], ("irs_estate", "ca_change", "irs_trust_basis")),
    ]
    benchmarks = [
        (["2026 federal estate exclusion", "$15,000,000", "Official rule"], ("irs_estate",)),
        (["2027 federal estate exclusion", "$15,480,000", "Official rule"], ("irs_2027",)),
        (["Current family-home limit add-on", "$1,044,590", "Official rule"], ("ca_prop19_limit",)),
        (["One-percent levy per illustrative $1,000,000 assessed", "$10,000 / year", "Illustrative"], ("local_a_tax",)),
        (["City B FY2026–27 rate per illustrative $1,000,000 assessed", "$11,820 / year", "Illustrative"], ("local_b_tax",)),
        (["Actual household net wealth under each option", None, "Not verified"], ("irs_basis", "cdi_survey")),
    ]
    return page("executive-summary.html", "Executive summary", "A conditional recommendation, the official numbers available today and the missing evidence that prevents a defensible property-specific winner.",
        note("Recommended next decision", "Do not sell the already-owned residence merely to acquire the future home. Keep its separate ownership and rental stream in the comparison. At inheritance, choose A only after a current appraisal, trust/basis review, insurance quotes, rental terms and 2040–2050 tax law are known.", "positive") +
        section("Four choices, one honest constraint", "There is no officially verified future sale price, rental yield, tax bill or estate size; no option can be ranked numerically for this household today.",
                table(["Path", "When it may win", "Tax / cash-flow pivot", "Personal result", "Official reference"], rows)) +
        section("Numbers that can be published", "Rates and normalized arithmetic only; the home-specific fields remain blank.",
                table(["Measure", "Amount", "Evidence level", "Official reference"], benchmarks)) +
        note("What would reverse a decision", "A different trust structure, a property-value decline, loss of insurance, local rent rules, mortgage payoff, changed inheritance law or large retirement-account distribution can change the answer. The 50-year historical replay shows why a constant return cannot be relied upon.", "warning"))


def prop_a() -> str:
    history = [([str(y), None, None, "Not verified"], ("local_a_tax", "ca_assess")) for y in range(2014, 2027)]
    costs = [
        (["Appraised market value / death-date basis", None, "No identifying parcel lookup or appraisal", "Not verified"], ("irs_basis",)),
        (["Yearly assessed value and tax bill", None, "Parcel-specific roll and tax-area charges withheld", "Not verified"], ("local_a_tax",)),
        (["Annual primary-residence insurance", None, "Regulator survey is not a property quote", "Not verified"], ("cdi_survey",)),
        (["Monthly water and sewer", None, "Serving utility, meter and use not independently confirmed", "Not verified"], ("water_a",)),
        (["Monthly electricity / solar credit", None, "Solar tariff, interconnection date and annual true-up unknown", "Not verified"], ("cpuc_solar",)),
        (["Annual repairs / reserves", None, "Inspection and documented repair history required", "Not verified"], ("irs_rental",)),
        (["2040 / 2045 / 2050 cash cost", None, "Future rates and the actual tax base remain unknown", "Not verified"], ("ca_assess", "cdi_home")),
    ]
    gates = [
        (["If inherited and rented", "Generally reassess at the then market value; the family-home exclusion ordinarily does not apply to rental use.", None], ("ca_prop19", "ca_prop19_law")),
        (["If inherited and lived in", "Eligible parent-child transfer may preserve part of the factored base year value, only when both principal-residence and filing conditions hold.", None], ("ca_prop19_law", "ca_prop19_limit")),
        (["If sold soon after death", "Basis may generally be death-date fair market value when §1014 applies. Gain, costs and estate-tax exposure still require a calculation.", None], ("irs_basis", "irs_trust_basis")),
    ]
    return page("property-a.html", "Property A · the future inheritance", "Private amounts are omitted. Below are the full year labels supplied for review, each marked blank until an official record can be checked without public disclosure.",
        section("Historical property record", "Neither assessment history nor annual bills are independently verified. Local rules linked at right do not validate a particular parcel.",
                table(["Year", "Property tax", "Assessed value", "Status", "Official method (not parcel proof)"], history)) +
        section("Cost inventory", "These costs must enter a private underwriting worksheet at the actual transfer date. An online premium survey does not substitute for a bound quote.",
                table(["Input", "Household amount", "Why blank", "Status", "Official reference"], costs)) +
        section("Three tax paths", "Occupation, rent and sale can create very different reassessment and income-tax outcomes.",
                table(["Use", "Current rule", "Verified personal amount", "Official reference"], gates)) +
        note("Current value limit is not a future estimate", "The 2025–27 family-home add-on is about $1,044,590 after $10 rounding. The actual 2040–2050 limit, eligibility and tax-area levy cannot be confirmed in 2026.", "warning"))


def prop_b() -> str:
    history = [([str(y), None, None, "Not verified"], ("local_b_tax", "ca_assess")) for y in range(2016, 2027)]
    costs = [
        (["Existing monthly rental receipts", None, "Tenancy documents and payments stay private", "Not verified"], ("irs_rental",)),
        (["Current assessed value / property tax", None, "Government rate does not validate this parcel's roll", "Not verified"], ("local_b_tax",)),
        (["Annual landlord / multi-unit insurance", None, "Homeowners comparison is not a rental-coverage quote", "Not verified"], ("cdi_home", "cdi_survey")),
        (["Monthly water / sewer", None, "Consumption and meter details are not publicly verified", "Not verified"], ("water_b",)),
        (["Monthly electricity", None, "Bills and service allocation are not verified", "Not verified"], ("cpuc_solar",)),
        (["Annual repairs and vacancy", None, "Actual maintenance, turnover and legal unit status unknown", "Not verified"], ("irs_rental", "local_b_scope")),
        (["Cost basis if independently sold", None, "This home is not newly inherited from A's transfer", "Not verified"], ("irs_basis", "irs_trust_basis")),
    ]
    rules = [
        (["Ownership event", "Already held by the beneficiary; A's trust transfer does not itself transfer B.", "No automatic reset merely because A changes hands"], ("ca_change", "irs_estate")),
        (["FY2026–27 ad valorem rate", "1.18162182% of assessed value; other charges can apply.", "$11,820 per illustrative $1,000,000 of assessed value"], ("local_b_tax",)),
        (["Covered tenancy increase", "1.6% Mar 2026–Feb 2027 if local rules apply; not an automatic rise for every unit.", None], ("local_b_rent", "local_b_scope")),
        (["Owner-occupied space", "Existing rental income may continue while living at B, subject to actual leases and local status.", None], ("local_b_scope", "irs_rental")),
    ]
    return page("property-b.html", "Property B · already owned", "This asset is not part of the planned new inheritance under the stated ownership arrangement. Its ongoing rent remains a separate baseline, without publicizing tenant or household amounts.",
        section("Historical property record", "A posted local rate is not an independent verification of an individual tax bill.",
                table(["Year", "Property tax", "Assessed value", "Status", "Official method (not parcel proof)"], history)) +
        section("Ongoing rental economics", "The public site cannot establish net operating income or the right policy type without the private documents.",
                table(["Input", "Household amount", "Why blank", "Status", "Official reference"], costs)) +
        section("Rules that change the comparison", "The published example is for one normalized assessed-value unit, not this building.",
                table(["Rule", "Verified / conditional finding", "Number or consequence", "Official reference"], rules)) +
        note("Do not double-count the estate", "Do not add B to the other owner's gross estate or claim a new basis adjustment merely from A's trust inheritance. A title or retained-interest review may change that legal assessment.", "warning"))


def taxes() -> str:
    thresholds = [
        (["2026", "$15,000,000", "Federal basic exclusion / filing threshold, subject to gifts and deductions", "Official rule"], ("irs_estate",)),
        (["2027", "$15,480,000", "Federal basic exclusion for deaths in 2027", "Official rule"], ("irs_2027",)),
    ] + [([str(y), None, "Not published for that death year as of this review", "Not verified"], ("irs_2027",)) for y in (2040, 2045, 2050)]
    taxes_rows = [
        (["Federal estate tax", "The decedent's taxable estate plus adjusted lifetime gifts is tested against the available credit; it is not a per-beneficiary inheritance allowance.", None], ("irs_estate", "irs_706")),
        (["California / local inheritance tax", "California law prohibits a state or local gift, inheritance or estate tax under the cited provision; current state estate return not required for recent deaths.", "$0 inheritance levy under present law"], ("ca_no_tax", "ca_estate")),
        (["Inherited cash and later income", "Inheritance itself is not California income; subsequent interest, dividends, rent or gain can be taxable.", None], ("ftb_inherit",)),
        (["Inherited property sale", "Basis generally FMV on the applicable valuation date; revocable and irrevocable trust treatment can differ.", None], ("irs_basis", "irs_trust_basis")),
        (["Primary home sale", "If ownership and use tests are met, up to $250,000 single / $500,000 joint of gain may be excluded.", "$250,000 / $500,000 current statutory limits"], ("irs_home_sale",)),
        (["Rental income / depreciation", "Report rent and expenses; 27.5-year building depreciation commonly applies under GDS, but land is not depreciated.", None], ("irs_rental",)),
        (["Extra federal investment tax", "3.8% NIIT may apply to rent and gains when income thresholds are met; not automatic for every heir.", None], ("irs_niit",)),
        (["Traditional retirement accounts", "Some inherited IRA beneficiaries face a 10-year distribution rule and taxable withdrawals; cash and retirement accounts must not be treated identically.", None], ("irs_ira",)),
    ]
    watch = [
        (["Federal exclusion", "2025 law raised the 2026 base to $15,000,000; the IRS announced 2027. No 2040–2050 dollar limit has been announced.", "Future amount blank"], ("irs_law2025", "irs_2027")),
        (["Family-home add-on", "Currently adjusted every other February from the FHFA index; the next published figure is needed for later transfers.", "2040–2050 amount blank"], ("ca_prop19_limit",)),
        (["Local rental amendment", "File 261020 was described by the Rent Board as proposed and not enacted on 9 Nov 2026; do not model it as law.", "Pending"], ("local_b_rent",)),
        (["Solar tariff", "Legacy NEM term can expire after 20 years; whether a given account remains eligible is unknown.", "Date and credit blank"], ("cpuc_solar",)),
    ]
    return page("taxes.html", "Taxes & changing law", "Inheriting an asset, its estate-tax treatment, the property-tax assessment and later income are four different questions.",
        section("Federal estate threshold by death year", "The exclusion applies to the decedent's estate and adjusted gifts, not automatically to the amount one beneficiary receives.",
                table(["Death year", "Basic exclusion", "Meaning", "Status", "Official reference"], thresholds)) +
        section("Current tax rules", "Conditional rules only; personal headroom, filing obligation and tax due are blank without the estate inventory, trust and return.",
                table(["Topic", "Rule", "Public numerical result", "Official reference"], taxes_rows)) +
        section("Law watch through the inheritance window", "A proposal, a rate or a 2026 statute must not be presented as a 2045 guarantee.",
                table(["Change", "Verified current status", "Future amount / effect", "Official reference"], watch)) +
        note("Estate headroom cannot be computed here", "Needed privately: decedent's includible assets and beneficial interests, debts, adjusted lifetime gifts, marital/charitable deductions, any surviving-spouse portability election and the law in the death year. B is already held separately under the stated title but a retained-interest exception remains possible.", "warning"))


def projections(ref: list[dict]) -> str:
    highlights = [
        ([str(y), f'{float(ref[y-2026]["hpi_index_base_100"]):,.2f}',
          money(ref[y-2026]["illustrative_assessed_per_million"]),
          money(ref[y-2026]["illustrative_one_percent_tax"]),
          None, "Historical replay"], ("fhfa_hpi", "ca_assess_history")) for y in (2026, 2040, 2045, 2050, 2076)
    ]
    details = []
    for row in ref:
        details.append(([str(row["scenario_year"]), str(row["replayed_year"]),
                         row["hpi_index_base_100"], row["ccpi_pct"] + "%" if row["ccpi_pct"] else "—",
                         row["official_factor"] or "—", row["illustrative_cost_index"],
                         money(row["illustrative_assessed_per_million"]),
                         money(row["illustrative_one_percent_tax"]), None, None, None, None, None, None],
                        ("fhfa_hpi", "ca_assess_history")))
    return page("projections.html", "50-year reference · 2026–2076", "Real historical volatility replayed forward as a stress reference. The property-specific market values, assessments and tax bills are deliberately blank, not forecasts disguised as facts.",
        note("How to read this", "Start with a purely illustrative $1,000,000 assessed-value unit in 2026, then apply the BOE's actual 1977–2026 annual assessment factors to 2027–2076. Reindex FHFA's statewide Q2 price index to 100.00 at 2026. This repeats history; it does not predict an address or its tax bill.", "positive") +
        section("Decision-year checkpoints", "The dollar columns show a normalized assessment unit at the constitutional 1% base levy, excluding bonds, charges, reassessment, new construction and Proposition 8 relief.",
                table(["Scenario year", "Statewide HPI index", "Illustrative assessed unit", "1% levy on unit", "Property A/B value", "Status", "Official inputs"], highlights)) +
        section("Every year, independently sourced", "Historical CCPI and factor are taken from the official BOE annual table; HPI Q2 entries from the FHFA series hosted by FRED. A/B amounts have no official verification.",
                table(["Future label", "History used", "HPI index", "CCPI", "Factor", "Cost index", "Assessed unit", "1% unit levy", "A value", "A assessed", "A tax", "B value", "B assessed", "B tax", "Official input rows"], details), id="yearly") +
        '<p class="download">Download the <a href="assets/data/reference_replay.csv">50-year reference CSV</a>, '
        '<a href="assets/data/official_hpi_q2.csv">official HPI fixture</a> or '
        '<a href="assets/data/boe_ccpi_factors.csv">official assessment factors</a>. Blank property columns are blank in the downloads too.</p>' +
        note("Why real bills will differ", "A and B have different tax-rate areas and base years; a death-time change in ownership can reset A, while B is already owned. Official factors alone cannot recover a parcel's assessed value. During a price crash, Proposition 8 may temporarily reduce the enrolled value.", "warning"))


def decision() -> str:
    options = [
        (["Sell A → diversified investments", "Market sale price − actual closing costs − actual debt − applicable gain/estate taxes", "Only consider when net after-tax alternative beats keeping A with comparable risk; stocks are volatile.", None], ("irs_basis", "irs_capital", "irs_estate")),
        (["Sell A → insured savings", "After-tax proceeds; allocate across insured ownership categories and banks where relevant.", "FDIC limit is not a guaranteed yield; account rate and income tax vary.", "$250,000 deposit insurance baseline"], ("fdic", "ftb_inherit")),
        (["Sell A → Treasury securities", "After-tax proceeds × market yield at purchase; price risk if sold before maturity.", "The 9 Nov 2026 10-year constant-maturity yield is historical, not a 2045 quote.", "4.88% observed; $48,800 per $1,000,000 before tax for one year, NOT a promise"], ("fred_yield", "irs_capital")),
        (["Rent A, remain in B", "Collected rent − vacancy − property tax after transfer − insurance − upkeep − utilities − income taxes", "Property-tax exclusion ordinarily unavailable when A is not the heir's principal residence.", None], ("ca_prop19_law", "irs_rental")),
        (["Occupy A, keep B rental", "Housing benefit + lawful added B rent − both properties' costs and taxes", "Only compare after verifying A's Prop 19 eligibility and B's actual local tenancy constraints.", None], ("ca_prop19", "local_b_scope")),
    ]
    keys = [
        (["Date-of-death fair value and basis of A", None, "Appraisal, trust instrument and title determine sale-gain starting point"], ("irs_basis", "irs_trust_basis")),
        (["Actual A annual market rent", None, "No official household-specific rent confirmation"], ("irs_rental",)),
        (["Coverage/premium for both uses", None, "Regulator survey is hypothetical, not a bound policy"], ("cdi_survey",)),
        (["Future local tax and exclusions", None, "Ad valorem and special charges change; occupancy conditions matter"], ("local_a_tax", "ca_prop19_law")),
        (["B leases and eligible units", None, "Occupancy choice may affect only lawfully available space"], ("local_b_scope",)),
        (["Estate size and asset types", None, "Financial assets, debts, gifts and IRAs can change tax and liquidity"], ("irs_estate", "irs_ira")),
    ]
    return page("decision.html", "Sell, rent or live in A?", "This is a decision rule, not a fabricated winner. B remains separately owned in every branch of the comparison.",
        section("Compare on equal terms", "A sale has immediate liquidity; a rental has operating and tail risk; personal use has housing value. Apply the same 2040–2050 date, tax law and risk allowance.",
                table(["Path", "Net-value framework", "Decision trigger", "Public dollar marker", "Official method"], options)) +
        section("Missing inputs block a numerical ranking", "Each owner-specific amount is left blank by design, rather than reverse-matching a private tax roll.",
                table(["Missing input", "Verified household figure", "Why it matters", "Official method"], keys)) +
        note("Avoid the tempting error", "Do not subtract B's entire market value from the other person's estate and simultaneously claim a new B basis: B is already held. Conversely, do not assume A's low historical assessed value survives a rental transfer. Verify title and trust before deciding.", "warning"))


def swans(ref: list[dict]) -> str:
    shocks = [
        (["Great Inflation", "1965–1982", "CPI exceeded 14% in 1980; high rates and repeated recessions", "A $10,000 illustrative annual cost becomes at least $11,400 under a single 14% jump; not an annual forecast.", "Protect liquidity and check insurance/utility escalation."], ("fed_inflation",)),
        (["Great Recession", "2006–2009", "US home prices ≈−30%; S&P 500 ≈−57% across different peak-to-trough windows", "$1,000,000 house index example → $700,000; $1,000,000 equity index → $430,000 before tax and dividends.", "Avoid a forced sale in a simultaneous downturn."], ("fed_recession",)),
        (["Stock-market crash", "1929–1932", "Dow price index ≈−89%; prior high not regained until Nov 1954", "$1,000,000 price-only example → $110,000 at the trough; total-return experience differs.", "Diversify and maintain a cash runway."], ("fed_1929",)),
        (["Inflation & energy spike", "June 2021–June 2022", "All-items CPI +9.1%; energy +41.6%; electricity +13.7%", "$10,000 illustrative non-specific cost basket × 1.091 → $10,910; actual utility mix unknown.", "Do not apply a flat CPI to each utility."], ("bls_2022",)),
        (["Housing slump & assessment relief", "Any lien date", "Market below factored base can trigger Proposition 8 reduction; rebound may then exceed 2% in a year.", "Property-specific reassessment: blank.", "Retain documentation for an assessor review."], ("ca_decline",)),
        (["Solar/insurance tail risk", "Unknown transfer date", "NEM 2.0 20-year term; insurer survey excludes property-specific eligibility and surcharges.", "Premium / net credit: blank.", "Re-quote and verify the interconnection date."], ("cpuc_solar", "cdi_survey")),
    ]
    inf = next(x for x in ref if x["scenario_year"] == 2045)
    return page("black-swans.html", "Black-swan economic conditions", "Growth and inflation do not advance in a straight line for 50 years. Historical episodes show why a winner under one smooth forecast can fail under the next regime.",
        section("The actual episode record", "Different indexes, jurisdictions and measurement windows are explicitly not treated as one synchronized property-specific outcome.",
                table(["Regime", "Observed period", "Verified historical condition", "Illustrative normalized effect", "Response to test", "Official source"], shocks)) +
        section("A non-uniform 50-year replay", "The statewide FHFA series fell during housing slumps and rose quickly in booms; assessment factors and CCPI likewise varied. This is historical analogy only.",
                table(["Scenario date", "Historical year replayed", "Statewide HPI index (2026=100)", "Official CCPI change", "Actual A/B outcome", "Official rows"],
                      [([str(y), str(ref[y-2026]["replayed_year"]), ref[y-2026]["hpi_index_base_100"],
                         ref[y-2026]["ccpi_pct"] + "%" if ref[y-2026]["ccpi_pct"] else "—", None],
                        ("fhfa_hpi", "ca_assess_history")) for y in (2026, 2035, 2040, 2045, 2050, 2055, 2065, 2076)])) +
        note("The 2045 replay is not a price forecast", f'At the 2045 label the replay uses an actual past statewide HPI observation and an official assessment factor. Its normalized HPI index is {inf["hpi_index_base_100"]}; neither home’s 2045 dollar value or rent has an official source. See the full year-by-year table.', "warning") +
        '<p class="action-link"><a href="projections.html#yearly">Explore all 51 reference rows →</a></p>')


def inheritance() -> str:
    steps = [
        (["Before death", "Keep the trust, deeds, beneficiary designations, account classifications and insurance documents together privately; identify the successor trustee.", "No public deadline; confirm governing documents", "Not verified"], ("irs_estate", "irs_trust_basis")),
        (["At death", "Trustee confirms whether A passed from the decedent and whether B is independently titled; inventory the actual estate and other financial assets.", "Date of death is the valuation reference unless alternate date validly elected", "Official rule"], ("irs_estate", "irs_basis")),
        (["Within statutory notice period", "When a revocable trust becomes irrevocable, successor/continuing trustee serves notice to covered beneficiaries and heirs.", "Generally within 60 days, subject to statutory exceptions", "Official rule"], ("ca_trust_notice",)),
        (["County reporting", "For a death-related real-property interest transferred via trust, trustee/transferee files change-in-ownership statement with the assessor or recorder.", "Generally within 150 days after death (non-probate trust transfer)", "Official rule"], ("ca_death_report",)),
        (["Establish value and basis", "Obtain a qualified appraisal where appropriate; retain basis and trust inclusion evidence before setting a sale price or rental depreciation.", "Personal figure blank", "Not verified"], ("irs_basis", "irs_trust_basis")),
        (["Consider family-home claim", "If legally eligible and choosing to occupy A, file homeowners exemption and parent-child exclusion claim within BOE deadlines.", "Exemption generally within 1 year; claim within 3 years or before third-party sale", "Official rule"], ("ca_prop19", "ca_prop19_law")),
        (["Federal estate return", "Executor determines filing need using year-of-death estate threshold, gifts and elections; timely portability filing may matter.", "Generally 9 months; 6-month filing extension if timely requested", "Official rule"], ("irs_filing", "irs_706")),
        (["Retirement assets / final choice", "Check inherited-IRA beneficiary rules and later taxable distributions, then compare post-tax sale, rent and occupancy with current quotes.", "Amounts and 2040–2050 law blank", "Not verified"], ("irs_ira", "irs_capital")),
    ]
    return page("inheritance.html", "Trust inheritance · step by step", "A practical sequence for a trust transfer, with deadlines verified against current statutes. Dates must be rechecked in the actual inheritance year.",
        section("Timeline and responsibilities", "Statutory time limits can start before the property decision is made. Trust terms and the deed remain private and unverified here.",
                table(["When", "Action", "Current time rule", "Status", "Official source"], steps)) +
        note("Keep all evidence off the site", "Deeds, tax bills, trust documents, insurance applications, tenant records and appraisals belong in a private attorney/trustee workspace. This dashboard has no forms, uploads or analytics.", "positive"))


def review() -> str:
    flags = [
        (["P-01 · Publication history", "Earlier public repository revisions and deployments contained household-specific financial inputs. The current site cannot erase cached or historical copies.", None, "Repository owner / host must evaluate history and visibility separately."], ("irs_estate",)),
        (["P-02 · A source of truth", "The 2026 owner-provided values and year-by-year tax history were not independently verified from official parcel records and could permit matching.", None, "Private assessor record and professional appraisal; do not publish identifiers."], ("local_a_tax", "irs_basis")),
        (["P-03 · B source of truth", "Existing title, tax roll, leases, building configuration and present rent were not independently reviewed.", None, "Private deed, assessor records and lease review."], ("local_b_tax", "local_b_scope")),
        (["P-04 · Trust & estate", "Trust revocability, retained interests, financial assets, debts, gifts, portability and retirement account types are unconfirmed.", None, "Trust counsel and complete estate inventory."], ("irs_estate", "irs_trust_basis", "irs_ira")),
        (["P-05 · Insurance", "No 2026 address-specific primary-home or landlord quote verified; published regulator examples cannot price either home.", None, "Bound quotes with correct occupancy and coverage limits."], ("cdi_survey", "cdi_home")),
        (["P-06 · Utilities and repairs", "Water provider/use, electric tariff, solar interconnection and actual repair reserves are unconfirmed.", None, "Private bills, solar contract, engineer inspection."], ("water_a", "water_b", "cpuc_solar")),
        (["P-07 · A transfer tax", "The actual tax-rate area, parent-child eligibility and owner occupancy at transfer are unverified.", None, "Private title/assessment review and BOE claim."], ("local_a_tax", "ca_prop19")),
        (["P-08 · B tenancy", "Whether any units are covered by the local rent ordinance cannot be resolved without building and tenancy records.", None, "Private occupancy/permit records and Rent Board guidance."], ("local_b_scope",)),
        (["P-09 · Future law", "2040–2050 federal exclusions, local taxes, tenant rules and solar tariffs are not yet published.", None, "Recheck official issuances near the actual death/transfer."], ("irs_2027", "ca_prop19_limit", "local_b_rent")),
        (["P-10 · Earlier claims", "Prior site editions offered a definitive winner and exact after-tax wealth from unconfirmed inputs; those conclusions are withdrawn.", None, "Recalculate privately once appraisal, title, rent, insurance and tax data are verified."], ("irs_basis", "irs_estate")),
        (["P-11 · Broken sources replaced", "A previously cited property-tax FAQ and a prior Treasury page returned not-found in this review; they are not cited as evidence in this edition.", None, "Use BOE §51/decline-in-value and FRED DGS10 instead."], ("ca_assess", "fred_yield")),
        (["P-12 · Competing session", "An old unmerged PR conflicts with the newer integrated public edition and requires a fresh privacy/evidence audit before use.", None, "Do not overwrite the privacy-safe release with stale numeric outputs."], ("irs_estate",)),
    ]
    return page("review.html", "Flagged for review", "Flags are published, not silently filled. A missing personal value is an intentional blank, not zero.",
        section("Evidence and privacy register", "Needs review does not block a sourced public page; it does block a trustworthy property-specific profit claim.",
                table(["Flag", "What could not be confirmed", "Public value", "Safe resolution", "Related official source"], flags)) +
        note("What a PR cannot undo", "Rewriting Git history, deleting cached pages and changing repository visibility are separate host-owner decisions. We do not claim that removing current site content erases material previously made public.", "warning"))


def methodology(ref: list[dict]) -> str:
    methods = [
        (["Evidence tier · official", "Current law or observed macro series opened on its publisher domain and linked in each row.", "Not a property record"], ("irs_estate", "fhfa_hpi")),
        (["Evidence tier · illustrative", "Arithmetic on an explicitly normalized $1,000,000 assessed-value unit or $10,000 hypothetical cost basket.", "Never an actual property figure"], ("local_a_tax", "bls_2022")),
        (["Evidence tier · blank", "Parcel values, insurance premiums, maintenance and 2040–2050 statutes need evidence that is unavailable or cannot safely be published.", "Displayed as an em dash; never estimated"], ("irs_basis", "cdi_survey")),
        (["50-year reference", "Future label Y replays actual Q2 FHFA index and BOE CCPI/factor from historical year Y−50; index resets to 100 in 2026.", "An analogy, not a forecast"], ("fhfa_hpi", "ca_assess_history")),
        (["Rounding", "All displayed monetary examples rounded to the nearest $10, half up; official percentages/series retain published precision.", "Privacy still requires withholding private bases"], ("ca_prop19_limit", "local_b_tax")),
        (["Assessments", "In normal conditions §51 uses the lower of factored base or market value; the reference shows factors on an arbitrary starting unit, not actual taxable property.", "Bonds and special charges excluded from the 1% example"], ("ca_assess", "ca_decline", "local_a_tax")),
    ]
    return page("methodology.html", "Methodology & repo audit", "Reproducible, bounded arithmetic with no parcel data. A source link verifies a rule or historical observation, never a future outcome.",
        section("Data provenance", "Pinned agency tables can be checked row by row. The release verifier checks row-source mapping, deterministic regeneration and no private figures in the deployment.",
                table(["Method", "What is done", "Limit", "Official source"], methods)) +
        section("Known source and model corrections", "The prior definitive recommendation and identical assumed growth over decades are withdrawn. The public version instead exposes every unresolved data gate.",
                table(["Correction", "Why it matters", "Current treatment", "Official reference"], [
                    (["Already-held B", "A transfer does not automatically change title or basis of another property.", "Separate estate and rental baseline"], ("irs_estate", "ca_change")),
                    (["Prop 19 eligibility", "An inherited rental and an heir-occupied family home have different exclusions.", "Occupancy and claim shown as conditions"], ("ca_prop19_law",)),
                    (["Constant returns", "Historic housing, inflation and equity outcomes include deep drawdowns.", "50-year historical replay and stress examples"], ("fhfa_hpi", "fed_recession")),
                    (["Insurance assumption", "A state premium comparison is not an individual binding quote.", "Both personal premiums blank"], ("cdi_survey",)),
                ])) +
        '<p class="download">Reproduce locally with <code>python3 public_site/build.py</code> and '
        '<code>python3 public_site/verify.py</code>. Source fixtures: '
        '<a href="assets/data/official_hpi_q2.csv">HPI Q2 CSV</a> · '
        '<a href="assets/data/boe_ccpi_factors.csv">BOE factor CSV</a>.</p>')


def sources() -> str:
    rows = [([sid, src["title"], src["evidence"], src["checked"]], (sid,))
            for sid, src in SOURCES.items()]
    return page("sources.html", "Official source library", f'{len(rows)} opened government, regulator or Federal Reserve publisher pages. Each evidence row throughout the dashboard links directly to the pertinent original.',
        section("Verification ledger · 11 November 2026", "Publisher pages are living documents. Check the linked text again in the actual inheritance year. A link is not independent confirmation of a private parcel value.",
                table(["ID", "Official document", "What it confirms", "How checked", "Open original"], rows)) +
        note("Source review standard", "Two previously cited pages returned a not-found response during this review and were replaced. No source is used to certify a home-specific cost, appraisal or future law without the necessary record.", "positive"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ref = load_reference()
    content = {
        "index.html": overview(ref), "executive-summary.html": summary(),
        "property-a.html": prop_a(), "property-b.html": prop_b(),
        "projections.html": projections(ref), "decision.html": decision(),
        "black-swans.html": swans(ref), "taxes.html": taxes(),
        "inheritance.html": inheritance(), "review.html": review(),
        "methodology.html": methodology(ref), "sources.html": sources(),
    }
    if set(content) != {x[0] for x in NAV}:
        raise ValueError("Navigation and rendered pages disagree")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, markup in content.items():
        (OUT / name).write_text(markup, encoding="utf-8")
    (OUT / "assets").mkdir(exist_ok=True)
    shutil.copyfile(HERE / "style.css", OUT / "assets" / "style.css")
    shutil.copyfile(DATA / "sources.json", OUT / "assets" / "sources.json")
    dst = OUT / "assets" / "data"
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("official_hpi_q2.csv", "boe_ccpi_factors.csv"):
        shutil.copyfile(DATA / name, dst / name)
    write_csv(dst / "reference_replay.csv", ref)
    print(f"Built {len(content)} privacy-safe pages, {len(ref)} year labels and {len(SOURCES)} official-source entries in {OUT}")


if __name__ == "__main__":
    main()
