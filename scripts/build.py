"""Render the privacy-safe, static public edition.

This builder has no property model, user inputs, values, projections, analytics or network calls.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "assets" / "sources.json"
PAGES = [
    "index.html", "executive-summary.html", "decision.html", "property-a.html",
    "property-b.html", "costs.html", "projections.html", "stress.html", "taxes.html",
    "inheritance.html", "questions.html", "suggestions.html", "review.html", "audit.html",
    "sources.html",
]
NAV_GROUPS = [
    ("Start here", ["index.html", "executive-summary.html", "decision.html"]),
    ("Property paths", ["property-a.html", "property-b.html", "costs.html", "projections.html"]),
    ("Rules and risks", ["taxes.html", "inheritance.html", "stress.html"]),
    ("Review before deciding", ["questions.html", "suggestions.html", "review.html"]),
    ("Evidence", ["audit.html", "sources.html"]),
]

SOURCES_DOC = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
SOURCES = {item["id"]: item for item in SOURCES_DOC["sources"]}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def source_link(source_id: str, label: str | None = None) -> str:
    item = SOURCES[source_id]
    text = label or f"{item['publisher']} — {item['title']}"
    return (f'<a class="source-link" href="{esc(item["url"])}" '
            f'target="_blank" rel="noopener noreferrer">{esc(text)}</a>')


def list_html(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{item}</li>" for item in items) + f"</{tag}>"


def fact_table(caption: str, headers: list[str], rows: list[tuple[list[str], str | list[str]]]) -> str:
    """Render factual rows with one or more relevant official-source links."""
    head = "".join(f"<th scope=\"col\">{esc(value)}</th>" for value in headers)
    head += '<th scope="col">Official source</th>'
    body = []
    for cells, source_ids in rows:
        source_ids = [source_ids] if isinstance(source_ids, str) else source_ids
        assert source_ids and all(source_id in SOURCES for source_id in source_ids), source_ids
        rendered = "".join(f"<td>{cell}</td>" for cell in cells)
        links = "<br>".join(source_link(source_id) for source_id in source_ids)
        body.append(f'<tr class="fact-row">{rendered}<td>{links}</td></tr>')
    return (f'<div class="table-wrap"><table><caption>{esc(caption)}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def blank_table(caption: str, headers: list[str], rows: list[list[str]]) -> str:
    """Render a non-factual worksheet with deliberately blank value cells."""
    head = "".join(f"<th scope=\"col\">{esc(value)}</th>" for value in headers)
    body = []
    for cells in rows:
        rendered = []
        for cell in cells:
            text = str(cell)
            rendered.append(text if text.lstrip().startswith("<td") else f"<td>{text}</td>")
        body.append('<tr class="worksheet-row">' + "".join(rendered) + "</tr>")
    return (f'<div class="table-wrap"><table><caption>{esc(caption)}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def plain_table(
    caption: str,
    headers: list[str],
    rows: list[list[str]],
    row_class: str = "proposal-row",
) -> str:
    """Render a proposal or unresolved-item register, not a factual-claim table."""
    head = "".join(f"<th scope=\"col\">{esc(value)}</th>" for value in headers)
    body = []
    for cells in rows:
        body.append(f'<tr class="{esc(row_class)}">' + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return (f'<div class="table-wrap"><table><caption>{esc(caption)}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def card(title: str, text: str, href: str | None = None, link_text: str = "Open section") -> str:
    link = f'<a href="{esc(href)}">{esc(link_text)} →</a>' if href else ""
    return f'<article class="card"><h3>{esc(title)}</h3><p>{text}</p>{link}</article>'


def page_shell(filename: str, title: str, description: str, body: str) -> str:
    nav = []
    index = 0
    for group, members in NAV_GROUPS:
        nav.append(f'<div class="nav-group">{esc(group)}</div>')
        for href in members:
            index += 1
            label = next(
                label for name, label in [
                    ("index.html", "Overview"),
                    ("executive-summary.html", "Quick summary"),
                    ("decision.html", "Compare options"),
                    ("property-a.html", "Property A · inherited"),
                    ("property-b.html", "Property B · already owned"),
                    ("costs.html", "Running costs"),
                    ("projections.html", "Projection method"),
                    ("stress.html", "Economic stress cases"),
                    ("taxes.html", "Tax and law watch"),
                    ("inheritance.html", "Inheritance steps"),
                    ("questions.html", "Questions first"),
                    ("suggestions.html", "Suggestions for review"),
                    ("review.html", "Flagged items"),
                    ("audit.html", "Privacy and audit"),
                    ("sources.html", "Source library"),
                ] if name == href
            )
            current = ' aria-current="page"' if filename == href else ""
            nav.append(f'<a href="{esc(href)}"{current}><span>{index:02d}</span>{esc(label)}</a>')
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <title>{esc(title)} · Inherited Property Decision Guide</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <aside>
    <a class="brand" href="index.html">Property Decision Guide<small>Privacy-safe public edition</small></a>
    <nav aria-label="Main navigation">{"".join(nav)}</nav>
    <p class="aside-note">General framework only. Property-specific values and forecasts are intentionally not published.</p>
  </aside>
  <main id="main">
    <div class="top"><span>U.S. federal · California framework</span><span>Reviewed 12 November 2026</span></div>
    <header class="hero"><p class="eyebrow">Public edition · not a personalized recommendation</p><h1>{esc(title)}</h1><p>{esc(description)}</p></header>
    {body}
    <footer><span>Privacy-safe public edition · updated 12 November 2026</span><span><a href="audit.html">Privacy, source and scope limits</a></span></footer>
  </main>
</body>
</html>
'''


def build_pages() -> None:
    pages: dict[str, tuple[str, str, str]] = {}

    pages["index.html"] = (
        "Inherited Property A and already-owned Property B",
        "A concise framework for comparing the inherited asset with a separate property already owned by the recipient, without publishing property-specific inputs or projections.",
        '''<div class="privacy"><strong>Privacy boundary.</strong> Property A is treated as inherited. Property B is treated as already owned by the recipient. They are kept separate for ownership, rental income, occupancy, basis and tax analysis. This public edition contains no property addresses, locations, parcel records, owner values, rent, utility use, insurance estimates or individualized forecasts. Rounding alone is not treated as anonymization.</div>
<section><h2>Start with the distinction</h2><div class="cards">
''' + card("Property A · inherited", "Confirm the transfer, title, date-of-death value and any eligible family-home reassessment exclusion. Compare keeping for use, renting, selling or delaying a decision.", "property-a.html") +
        card("Property B · already owned", "Treat B's existing ownership and any rental income separately. Compare continuing to rent, changing occupancy or selling only after checking title, tenants, costs and tax basis.", "property-b.html") +
        card("Decision before calculation", "The public guide leaves unknown property-specific values blank. It organizes the evidence and stress cases needed for a private, independently checked comparison.", "decision.html") +
        '''</div></section>
<section><h2>A short route through the guide</h2>''' + list_html([
            'Confirm who owns each asset and when any transfer occurred. Start with <a href="questions.html">Questions first</a>.',
            'Calendar the trust, assessor, tax-return and claim steps on <a href="inheritance.html">Inheritance steps</a>.',
            'Collect actual bills, leases, quotes and repair records on the <a href="costs.html">Running costs</a> page; keep the values in a private record.',
            'Compare the options and time-varying stress cases without treating a smooth 50-year growth rate as a forecast.',
            'Review the separate <a href="suggestions.html">Suggestions for review</a> section; none of its proposals is automatically selected.'
        ], ordered=True) + '''</section>
<div class="note"><strong>History limitation.</strong> This refresh changes the current public edition. It does not certify that earlier Git commits, pull-request diffs, cached pages, forks, downloads or external copies have been erased.</div>'''
    )

    pages["executive-summary.html"] = (
        "Quick summary",
        "The public edition organizes the inherited-property decision without embedding a recommendation or any private property values.",
        '''<div class="answer"><strong>Decision status: open.</strong> No option is ranked here because verified title, property-specific financial records, local law and the recipient's priorities are not part of this public edition. Use this summary to outline important details and the route through the full guide.</div>
<section><h2>Keep two balance sheets</h2>''' + plain_table(
            "The two-property distinction used throughout this guide",
            ["Question", "Property A · inherited", "Property B · already owned"],
            [
                ["What is being decided?", "Accept, retain, rent, occupy or sell an inherited asset expected around 2040–2050 via trust.", "Whether to continue a rental use, change occupancy or sell an asset already owned by the recipient."],
                ["Income to compare", "Any later rent, sale proceeds or investment income under the applicable tax rules.", "Existing rental receipts and operating costs, kept separate from A's inheritance."],
                ["Tax and title boundary", "Confirm the estate/trust transfer, basis evidence and any property-tax exclusion.", "Verify B's existing title and tax records; do not assume A's inheritance changes B's ownership or basis."],
            ],
            row_class="framework-row",
        ) + '''</section>
<section><h2>Important details to organize</h2>''' + plain_table(
            "Evidence groups that drive the comparison",
            ["Area", "What to collect privately", "Why it matters"],
            [
                ["Title and transfer", "Recorded deed, trust/will, beneficiary records, transfer date", "Determines owner, basis, and deadline calendars"],
                ["Property tax", "Current roll, tax bill, any family-home exclusion filing, supplemental notices", "Tax can reset on inheritance; exclusion conditions are fact-specific"],
                ["Running costs", "Insurance, water, electricity/solar, maintenance, repairs, management", "Annual cash flow and reserve needs"],
                ["Rental and occupancy", "Leases, collected rent, vacancy, tenant obligations, personal-use plan", "Affects cash flow and whether B's rent stops if occupied"],
                ["Tax thresholds and basis", "Estate total, prior gifts, deductions, retirement accounts, basis records", "Determines filing, exclusions and gain on sale"],
                ["Law at decision date", "Federal, state and local rules rechecked when deciding", "Indexed amounts and proposals change"],
            ],
            row_class="framework-row",
        ) + '''</section>
<section><h2>Options compared side by side</h2>''' + plain_table(
            "Decision paths evaluated separately for each property",
            ["Path", "Property A · inherited", "Property B · already owned"],
            [
                ["Live in it", "Compare housing value and new carrying costs with rent or sale alternatives; check reassessment treatment", "Compare personal use with rental income that would stop or change"],
                ["Rent it", "Estimate achievable rent, vacancy, turnover, management, repairs, tax and insurance", "Keep current rental ledger; review lawful increases and turnover costs"],
                ["Sell and reinvest", "Verify inherited basis and sale costs; compare reinvestment to keeping; do not assume tax-free", "Use B's separate records; sale does not inherit A's basis"],
                ["Defer a change", "Track carrying costs and filing duties while administration is completed", "Track lease, tenant-notice and financing duties during a hold"],
            ],
            row_class="choice-row",
        ) + '''</section>
<section><h2>Five decision steps</h2>''' + list_html([
            'Verify title, transfer date, beneficiary designations and the controlling estate or trust documents.',
            'Calendar deadlines before comparing outcomes; some statutory periods are short and fact-dependent.',
            'Collect actual annual costs and one-time repair or transaction estimates. Keep them private.',
            "Compare A's use options separately from B's rental/occupancy choices, including the effect of lost or changed rent if B is occupied.",
            'Re-run the comparison under inflation shocks, falling asset prices, vacancy, insurance changes, major repairs and changes in law.'
        ], ordered=True) + '''</section>
<section><h2>How a trust inheritance around 2040–2050 would be sequenced</h2>''' + list_html([
            f'Confirm the trust terms, trustee and distribution provisions before the transfer; see {source_link("probate_16061_7", "trustee notice rule")}.',
            f'At death, record the date-of-death value and request assessor guidance; see {source_link("rtc_480", "change-in-ownership reporting")} and {source_link("rtc_63_2", "family-home exclusion")}.',
            f'Calendar the 60-day notice, 150-day assessor statement, one-year occupancy/exemption, three-year claim and nine-month estate-return periods; see <a href="inheritance.html">Inheritance steps</a>.',
            'Hold and then compare live, rent or sell using the private cost ledger and multiple economic paths rather than a single growth rate.',
            'Review <a href="questions.html">Questions first</a> and <a href="suggestions.html">Suggestions for review</a> before selecting any proposal or assumption.'
        ], ordered=True) + '''</section>
<section><h2>Why a single 50-year growth rate is not used</h2><p>Growth and inflation are uneven over long periods. The guide keeps a constant-rate illustration off the public pages and instead uses irregular historical episodes and a private irregular-path method. See <a href="stress.html">Economic stress cases</a> and <a href="projections.html">Projection method</a>.</p></section>
<section><h2>Comparison logic</h2><p>For a rental, start with collected rent minus vacancy/collection losses, operating costs, financing cash payments, major-repair reserves and applicable taxes. Keep taxable income separate from cash flow: a tax deduction is not the same as cash saved. For owner-occupancy, explicitly record housing value and any rental income that would stop or change.</p><p>For an inherited sale, obtain the basis evidence and sale costs; do not assume a sale is tax-free. See the <a href="taxes.html">Tax and law watch</a> and <a href="costs.html">Running costs</a>.</p></section>'''
    )

    pages["decision.html"] = (
        "Compare options",
        "A side-by-side decision structure for Property A (inherited) and Property B (already owned); no option is ranked without private evidence.",
        '''<div class="note"><strong>Not a recommendation.</strong> The table lists choices to evaluate. It does not predict returns or identify a winning option.</div>
<section><h2>Options by property</h2>''' + plain_table(
            "What each choice requires checking",
            ["Choice", "Property A · inherited", "Property B · already owned", "Key evidence"],
            [
                ["Keep for personal use", "Compare housing value, new running costs, insurance and eligibility for any family-home reassessment rule.", "Compare personal use with rental income that would stop or change; review existing tenants and occupancy rules.", "Actual costs, title, occupancy and applicable local law."],
                ["Rent or continue renting", "Estimate achievable collected rent, vacancy, tax, management, repairs, insurance and utilities.", "Record existing rental income and expenses separately; consider unit-by-unit occupancy and lease terms.", "Leases, statements, bills, local rules and tax records."],
                ["Sell", "Verify inherited basis, sale date, transaction costs and any applicable tax reporting.", "Use B's separate ownership and tax records; do not import A's inherited basis assumptions.", "Title, tax basis/depreciation records, sale estimate and local transfer-tax rules."],
                ["Defer or stage a change", "Check carrying costs, deadlines, insurance, security and any tax/assessor filing obligations during the holding period.", "Check lease, tenant-notice, operating and financing obligations before changing use.", "Calendar, policies, contracts and professional advice."],
            ],
            row_class="choice-row",
        ) + '''</section>
<section><h2>Choose criteria before looking at a winner</h2>''' + list_html([
            '<strong>Financial:</strong> after-tax cash flow, liquidity, one-time costs and sensitivity to alternative returns.',
            '<strong>Housing:</strong> whether either property is needed as a home, timing, accessibility and the cost of housing elsewhere.',
            '<strong>Risk:</strong> vacancy, repair, insurance availability, local tax/rental law and market drawdowns.',
            '<strong>Workload:</strong> management time, tenant obligations and the ability to fund unexpected work.',
            '<strong>Values:</strong> family continuity, flexibility, debt reduction, diversification or a planned transfer.'
        ]) + '''<p>Record which criteria matter most before selecting assumptions. A change to occupancy, title or local law can change the comparison; see <a href="questions.html">Questions first</a>.</p></section>'''
    )

    pages["property-a.html"] = (
        "Property A · inherited",
        "A framework for an inherited property, including title, basis, possible California family-home reassessment treatment and blank evidence fields.",
        '''<div class="privacy"><strong>Scope.</strong> Property A is the inherited asset in this guide. No property description, address, assessment, market value, tax bill, occupancy history, cost or projection is published.</div>
<section><h2>Rules to check</h2>''' + fact_table(
            "General rules relevant to inherited property",
            ["Issue", "General rule summary"],
            [
                (["Federal basis", "Basis is generally the fair market value at the decedent's date of death. An alternate valuation date is available only under specified estate-return and election rules; taxable gain may apply on a later sale."], "irs_inherited_basis"),
                (["California family-home exclusion", "A qualifying transfer must satisfy statutory relationship, property, occupancy, exemption and filing requirements. A transferee's principal-residence occupancy is generally required within one year for the family-home exclusion."], "rtc_63_2"),
                (["Filing periods", "The ordinary claim period is generally three years after transfer, before a third-party transfer, or when the eligible transferee stops occupying the residence, whichever is earlier; statutory and notice-related exceptions can change the deadline."], "rtc_63_2"),
                (["Change-of-ownership reporting", "California's statute sets different reporting steps for probate and non-probate transfers by death; obtain the current assessor form and calendar the applicable deadline."], "rtc_480"),
            ]) + '''</section>
<section><h2>Private evidence checklist</h2><p>These cells are blank by design. Keep records in a private working copy; do not put owner-supplied figures into this public site.</p>''' + blank_table(
            "Property A inputs — not collected or published here",
            ["Field", "Public value", "Evidence to obtain privately"],
            [
                ["Current title and transfer instrument", '<td class="blank">Not published</td>', "Recorded title, trust or estate documents"],
                ["Transfer/death date", '<td class="blank">Not published</td>', "Official record; use to calendar deadlines"],
                ["Date-of-death fair market value / basis records", '<td class="blank">Not published</td>', "Qualified valuation and estate/tax documents"],
                ["Assessed value, property-tax bill and supplemental notices", '<td class="blank">Not published</td>', "Current assessor roll and tax bill"],
                ["Insurance, water, electricity/solar, maintenance and repairs", '<td class="blank">Not published</td>', "Current policies, utility bills, inspections and invoices"],
                ["Sale costs, rent potential and personal-use plan", '<td class="blank">Not published</td>', "Written estimates, leases and household plan"],
            ]) + '''</section>
<section><h2>Choices to compare</h2><p>Keep for personal use, rent, sell, or defer a change while required administration is completed. Compare after-tax cash flow and housing value with the time, liquidity, insurance, maintenance and legal risks. See <a href="decision.html">Compare options</a> and <a href="costs.html">Running costs</a>.</p></section>'''
    )

    pages["property-b.html"] = (
        "Property B · already owned",
        "A separate framework for a property treated as already owned before Property A is inherited, including rental income and possible owner occupancy.",
        '''<div class="privacy"><strong>Ownership distinction.</strong> In this decision framework, Property B is already owned by the recipient; it is not treated as an asset newly inherited with A. Verify the deed, beneficial ownership and tax records before relying on that distinction.</div>
<section><h2>Keep B's income and use separate</h2><p>If B is rented, record collected rent, vacancy or non-payment, unit-level occupancy, operating costs, financing and taxes in its own ledger. If the recipient may occupy B, compare the housing value with rent that would stop or change, tenant/lease obligations and revised utility, insurance and maintenance costs. No rent or occupancy level is assumed here.</p>''' + fact_table(
            "General rules that can affect B",
            ["Topic", "What to verify"],
            [
                (["Rental income and expenses", "Federal rental reporting lists common expenses such as maintenance, insurance, taxes, repairs and utilities; personal use can change expense allocation and deductions."], "irs_rental"),
                (["Rent increases", "California's general statutory cap applies only to covered units; exceptions and local restrictions may change the rule. Confirm unit coverage and current local law before changing rent."], "civ_1947_12"),
                (["Ending a tenancy", "After 12 months of continuous lawful occupancy, covered tenancies generally require just cause stated in the written notice. For a no-fault termination, the owner must either provide relocation assistance equal to one month's rent within 15 calendar days or waive the final month's rent in writing before it is due; exemptions and local protections apply."], "civ_1946_2"),
                (["Insurance", "State premium-comparison surveys are not individualized quotes. Confirm rental, vacancy and owner-occupancy coverage directly with the insurer."], "cdi_premiums"),
                (["Solar / electricity", "Net-billing/export credits depend on the utility and the system's tariff/interconnection facts. Check the actual account bill and agreement."], "cpuc_solar"),
            ]) + '''</section>
<section><h2>Private evidence checklist</h2>''' + blank_table(
            "Property B inputs — not collected or published here",
            ["Field", "Public value", "Evidence to obtain privately"],
            [
                ["Current legal and beneficial ownership", '<td class="blank">Not published</td>', "Recorded title, agreements and tax records"],
                ["Existing basis and prior depreciation records", '<td class="blank">Not published</td>', "Prior returns, closing records and improvement records"],
                ["Collected rent, leases, vacancy and owner-occupancy plan", '<td class="blank">Not published</td>', "Rent ledger, leases, tenant notices and personal-use plan"],
                ["Property tax, insurance, water, electricity/solar", '<td class="blank">Not published</td>', "Current bills, policy declarations and system agreement"],
                ["Maintenance, repair and capital-work history", '<td class="blank">Not published</td>', "Inspection reports, invoices and forward repair estimates"],
            ]) + '''</section>
<section><h2>Separate tax ledgers</h2><p>Do not combine B's existing rental receipts with A's estate value, and do not assume A's inherited basis applies to B. A tax professional should identify ownership, basis, prior depreciation, income allocation and the effect of any occupancy change from the underlying records.</p></section>'''
    )

    pages["costs.html"] = (
        "Running costs",
        "A blank evidence template for property tax, insurance, water, electricity/solar, maintenance, repairs, rental income and transaction costs.",
        '''<div class="note"><strong>Every property-specific amount is intentionally blank.</strong> A rounded public figure can still identify a property. Use actual records and quotes in a private worksheet; the source links below describe rules, not the cost of either property.</div>
<section><h2>Annual and one-time items</h2>''' + blank_table(
            "Cost ledger — private inputs required for each property",
            ["Line item", "Property A", "Property B", "Evidence / official rule source"],
            [
                ["Property tax, assessments and supplemental notices", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Current assessor roll and tax bill; {source_link('boe_prop13', 'California property-tax framework')}"],
                ["Insurance premium, deductible and coverage limits", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Current policy and written quote; {source_link('cdi_premiums', 'CDI survey limitations')}"],
                ["Water, sewer and other service charges", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', "Actual service-provider bills; provider intentionally not identified"],
                ["Electricity, gas, solar loan/lease and export credits", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Actual bills and system agreement; {source_link('cpuc_solar', 'CPUC tariff overview')}"],
                ["Routine maintenance and management", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Invoices, service contracts and inspection; {source_link('irs_rental', 'IRS rental-expense categories')}"],
                ["Repairs, deferred work and capital improvements", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Inspection and contractor estimates; {source_link('irs_rental', 'IRS repair/improvement distinction')}"],
                ["Rental income, collection loss, vacancy and tenant expenses", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Leases, deposits, statements and records; {source_link('irs_rental', 'IRS rental reporting')}"],
                ["Financing cash payments and loan terms", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', "Loan statements and agreements; tax treatment requires separate review"],
                ["Selling costs, transfer tax and closing expenses", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', f"Written sale estimate and local ordinance; {source_link('rtc_11911', 'California transfer-tax authorization')}"],
            ]) + '''</section>
<section><h2>Keep cash flow and tax treatment separate</h2><p>For a rental, organize actual cash received and paid by year. Then separately determine taxable rental income and any allowed deductions. IRS Publication 527 distinguishes, among other things, routine repairs from capital improvements and discusses rental expenses; it does not establish a property's budget.</p><p>For personal occupancy, include the changed housing arrangement and any rental income lost or reduced. For an inherited sale, keep basis and transaction-cost documents separate. Do not substitute a statewide average, insurance comparison survey or property-tax rule for a property-specific bill or quote.</p></section>'''
    )

    pages["projections.html"] = (
        "Projection method — no personal forecast",
        "A reproducible, year-by-year method for private scenario comparisons without publishing owner inputs, property-specific projections or a smooth 50-year growth forecast.",
        '''<div class="privacy"><strong>No personalized projection is published.</strong> The public site contains no starting property value, rent, assessed value, owner-supplied input or calculated future outcome. A 50-year line based on a single growth rate would imply more certainty than the evidence supports.</div>
<section><h2>Build privately, in separate ledgers, year by year</h2>''' + list_html([
            'Start with verified title, current bills, rent records, basis/depreciation records, insurance and written repair estimates.',
            "Keep Property A's inheritance, basis, reassessment eligibility and use options separate from Property B's existing ownership and rental cash flow.",
            'Use annual time steps for cash receipts, expenses, tax rules and occupancy changes. Distinguish nominal dollars from inflation-adjusted purchasing power.',
            'Use multiple paths, not a constant growth rate: declines, rebounds, flat real prices, changing inflation, changing rates, vacancy, insurance repricing and major repair years.',
            'Show the assumptions and source for each input; leave unsupported inputs blank. Do not turn a scenario into a probability or recommendation without evidence.'
        ], ordered=True) + '''</section>
<section><h2>Year-by-year structure — what to project for each year</h2><p>Use one row per year from the inheritance year through the holding horizon. The formulas below are general rules; substitute the actual bill, quote or private assumption year by year. All private-year values remain blank on the public site.</p>''' + blank_table(
            "Private annual worksheet — one row per year, values blank here",
            ["Year", "Market value", "Assessed value", "Property tax", "Insurance, water, electricity/solar", "Maintenance / repairs", "Rental net", "Notes / source"],
            [
                ["Inheritance year", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', "Trust date, basis record, assessor filing; " + source_link('boe_prop13', 'Prop 13 framework') + " and " + source_link('boe_lta_2026_002', '2% cap letter')],
                ["Inheritance year +1", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', "Occupancy within one year if claiming family-home exclusion; " + source_link('rtc_63_2', 'RTC 63.2')],
                ["Each later year", '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', '<td class="blank">Not published</td>', "Use irregular paths from <a href=\"stress.html\">stress cases</a>; " + source_link('civ_1947_12', 'rent-cap rule') + " if covered"],
            ]) + '''</section>
<section><h2>Scenario dimensions</h2>''' + blank_table(
            "Private scenario matrix — no numeric assumptions supplied",
            ["Dimension", "Lower / adverse case", "Reference case", "Higher / favorable case", "Evidence needed"],
            [
                ["Home value path", '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', "Local appraisal and historical range; do not equate a broad index with a specific parcel"],
                ["Inflation and interest rates", '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', "Official time series and explicitly chosen stress assumptions"],
                ["Rent, vacancy and tenant turnover", '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', "Leases, lawful rent rules and actual collection history"],
                ["Insurance, utilities and repairs", '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', "Current quotes, actual bills, inspection and contractor estimates"],
                ["Tax law and occupancy", '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', '<td class="blank">Not supplied</td>', "Current federal, state and local law; recheck at the decision date"],
            ]) + '''</section>
<section><h2>Use horizons, not false precision</h2><p>For each chosen horizon, compare (1) after-tax net cash flow, (2) net sale proceeds or remaining asset value, (3) investment alternatives, (4) housing value and any rent foregone by occupying B, and (5) liquidity and management risk. A historical episode is a stress example, not a prediction. The <a href="stress.html">Economic stress cases</a> page documents the episodes used as reminders.</p></section>'''
    )

    pages["stress.html"] = (
        "Economic stress cases — black swans and irregular 50-year paths",
        "Official historical episodes and a private method for testing a 50-year horizon where growth and inflation are never even, instead of using one constant rate.",
        '''<div class="note"><strong>History is not a forecast.</strong> These episodes are anchors for stress testing, not return assumptions and not predictions for either property. The figures below are historical index/economic changes, not property-specific inputs.</div>
<section><h2>Why a smooth 50-year line misleads</h2><p>A constant-rate projection (for example, a steady 4% home-price and 2.5% inflation line for 50 years) implies a stability that long economic history does not show. Real decades contain booms, flat years and sharp falls in sequence. Use the episodes below and the private irregular-path method after them to mimic that unevenness rather than averaging it away.</p>''' + fact_table(
            "Official historical facts for scenario design — irregular, not smooth",
            ["Episode", "Official-source historical fact", "Why include it in a stress test"],
            [
                (["1929–1954 market drawdown and recovery", "The Dow fell 89% from its 1929 peak by July 1932 and did not return to its pre-crash nominal high until November 1954.", "Test a deep equity drawdown and a recovery period that lasts much longer than a typical forecast horizon."], "frh_1929"),
                (["1965–1982 Great Inflation", "Inflation rose from a little over 1% in 1964 to more than 14% in 1980, peaking near 15% in March 1980.", "Test whether fixed-dollar costs, nominal returns and purchasing power behave differently under high inflation."], "frh_great_inflation"),
                (["2007–2009 Great Recession", "Average U.S. home prices fell about 30%; the S&P 500 fell 57% peak-to-trough; unemployment reached 10% in October 2009.", "Test simultaneous housing, investment and rental-income stress rather than assuming assets move independently."], "frh_great_recession"),
                (["March 2020 market shock", "The S&P 500 was 34% below its February 2020 high by March 23; market-wide circuit breakers halted trading three times in March.", "Test a rapid shock, constrained liquidity and decisions made during a volatile market."], "nyfed_covid"),
                (["June 2022 inflation shock", "CPI-U increased 9.1% over the year ended June 2022; electricity prices increased 13.7% over the same period.", "Test a sudden rise in broad prices and a separate utility-cost shock."], "bls_2022_cpi"),
            ]) + '''</section>
<section><h2>Black-swan conditions to test separately</h2>''' + plain_table(
            "Irregular conditions that a constant rate hides — test each privately",
            ["Condition", "What to vary", "Example private stress"],
            [
                ["Stagflation decade", "High inflation with flat or falling real asset prices", "Home prices flat for years while costs rise; rent coverage falls even if nominal rent is capped"],
                ["Housing crash and rebound", "Sharp fall then uneven recovery, with tight sale timing", "Need to sell or refinance during the trough, not after recovery"],
                ["Deflation or low inflation", "Falling or near-zero prices with debt still due", "Nominal rent and property tax behavior under a capped assessed-value rule"],
                ["Insurance repricing or nonrenewal", "Higher premium, higher deductible or loss of coverage", "A major repair year coincides with a coverage gap or nonrenewal"],
                ["Law change mid-horizon", "Exemption, tax threshold, rent or transfer-tax change", "Family-home exclusion unavailable or a rate threshold moved before 2040–2050"],
            ],
            row_class="framework-row",
        ) + '''</section>
<section><h2>Private method: run a 50-year horizon year by year with irregular paths</h2><p>Build the private workbook with annual rows from the inheritance year to 50 years later. For each year record market value, assessed value (capped), property tax, insurance, utilities, maintenance, rent and net — but keep the figures private. Then test the same horizon three or more ways:</p>''' + list_html([
            'A baseline with documented, sourced assumptions — clearly labeled as an illustration, not a forecast.',
            'Two or more historical replays: take a real 10- to 20-year official stretch and repeat its year-by-year pattern.',
            'One or more random resamplings of official annual changes to produce many irregular 50-year paths and a distribution, not a single line.',
            'At least one adverse combination: low or negative home-price years, high-inflation years, a vacancy year, a major repair year and a law change year together.'
        ], ordered=True) + '''<p>See <a href="projections.html">Projection method</a> for the annual structure and <a href="costs.html">Running costs</a> for the line items. Do not publish the private values or treat any single path as a prediction.</p></section>
<section><h2>Stress the whole decision, not only asset growth</h2>''' + list_html([
            'Property A: falling market value, delayed sale, reassessment, insurance nonrenewal, major repair and a change in the planned occupancy date.',
            'Property B: rent interruption, tenant turnover, lawful rent limits, owner-occupancy change, higher service costs and repair concentration.',
            'Shared household: inflation spikes, deflation, job/income interruption, interest-rate shifts, market drawdowns and the need for liquidity.',
            'Law: an exemption, tax threshold, rent rule or local ordinance changes before the decision or holding period ends.'
        ]) + '''<p>Use separate private scenarios and show the source for each factual anchor. Do not project the historical return directly onto a specific house, rent stream or investment account.</p></section>'''
    )

    pages["taxes.html"] = (
        "Tax and law watch",
        "A source-linked overview of current federal and California rules, enacted changes, pending proposals and local questions that remain unresolved.",
        '''<div class="note"><strong>As-of date: November 12, 2026.</strong> Tax thresholds and statutes change. Confirm the applicable law and professional advice at the actual transfer, filing and decision dates; no local jurisdiction is identified in this public guide.</div>
<section><h2>Current rules to account for</h2>''' + fact_table(
            "General tax and property rules",
            ["Area", "General rule summary"],
            [
                (["Federal estate tax", "For 2026, the basic exclusion is $15,000,000. For 2027 deaths, the basic exclusion is $15,480,000. The estate-tax filing test depends on the gross estate and adjusted taxable gifts; portability for a surviving spouse has a timely-return requirement. Estate tax, if due, is the estate's liability, separate from the beneficiary's income tax."], ["irs_estate", "irs_estate_update", "irs_2027_adjustments", "irs_form706"]),
                (["Receiving inherited property", "The value of property acquired by inheritance is generally excluded from federal gross income; income later produced by that property is not excluded by this rule."], "uscode102"),
                (["Federal gifts", "The 2027 annual gift exclusion is $20,000 per recipient. Gift and estate rules interact; do not treat the annual exclusion as the full lifetime estate-tax exclusion."], "irs_2027_adjustments"),
                (["Inherited basis and sale", "Inherited-property basis is generally date-of-death fair market value, subject to exceptions and reporting rules. A later gain may be taxable; do not assume an inherited sale is tax-free."], "irs_inherited_basis"),
                (["California income tax", "The inheritance itself is not included in California income, but income later produced by inherited property may be taxable."], "ftb_inheritance"),
                (["California estate tax", "The State Controller says a California estate-tax return is not required for decedents dying on or after January 1, 2005; federal filing rules still apply."], "sco_estate"),
                (["California property tax", "The general Proposition 13 framework has a 1% base rate plus voter-approved indebtedness and generally limits annual assessed-value increases to 2%; changes in ownership, new construction and local levies matter."], "boe_prop13"),
                (["Family-home reassessment exclusion", "A qualifying intergenerational family-home transfer has relationship, occupancy, exemption, value-cap and filing conditions. A principal-residence occupancy and homeowner/disabled-veteran exemption are generally required within one year."], "rtc_63_2"),
                (["Rental income and expenses", "Rental income and expenses are reported under federal tax rules. Common expense categories include insurance, taxes, repairs and utilities, but personal use, capital improvements and limitations affect treatment."], "irs_rental"),
                (["Statewide rent limits", "For covered California residential units, the annual rent-increase cap is generally 5% plus the applicable cost-of-living change or 10%, whichever is lower. Exceptions and local protections apply; the current statute states an end date of January 1, 2030."], "civ_1947_12"),
                (["Just-cause tenancy protections", "For covered tenancies after 12 months of continuous lawful occupancy, the owner generally must state just cause in a written termination notice. A no-fault termination requires either one month's rent in relocation assistance within 15 calendar days or a written waiver of final-month rent before it is due; exemptions and local law matter."], "civ_1946_2"),
                (["Local transfer tax", "California law authorizes county and qualifying city documentary transfer taxes by local ordinance. A rate cannot be determined without the applicable jurisdiction and transaction facts."], "rtc_11911"),
                (["Insurance", "State premium surveys are comparison tools, not individual insurance quotes. Confirm coverage, use and price directly with an insurer."], "cdi_premiums"),
                (["Solar / electricity", "Export credits depend on the utility, tariff and system/interconnection facts. Check the actual bill and system agreement."], "cpuc_solar"),
            ]) + '''</section>
<section><h2>Current law changes and watch items</h2>''' + fact_table(
            "Legislation and future checks",
            ["Measure or issue", "Official status or review finding on November 12, 2026", "Practical treatment"],
            [
                (["H.R. 1301 — federal estate and GST tax proposal", "Introduced and referred to the House Committee on Ways and Means; not enacted.", "Do not model the proposal as current law. Recheck official status before a later decision."], "hr1301_status"),
                (["California SB 974, Chapter 665 (2026)", "The official status page marks this non-urgency bill as chaptered September 27, 2026. Its text amends Revenue and Taxation Code section 63.2 for specified special-needs-trust transfers; the current code page reviewed here does not yet show that amendment. The operative date and codification are unresolved in this guide.", "Do not use the change as a current eligibility rule without confirming its operative date and current statutory text with the assessor or counsel."], ["sb974_status", "sb974_text", "rtc_63_2"]),
                (["California AB 1157 rent-law proposal", "Died in the Legislature on January 31, 2026; it is not current law.", "Use the current statute and any applicable local ordinance, not the proposed bill text."], "ab1157_status"),
                (["Proposition 19 value-cap adjustment", "The Board's current letter schedules the next biennial adjustment for February 2027.", "Recheck the Board's latest letter; do not carry a current cap forward as a long-term assumption."], "boe_lta_2025_009"),
            ]) + '''</section>
<div class="privacy"><strong>Local-law limit.</strong> State statutes do not identify whether a particular rental unit is covered or whether a local ordinance imposes additional requirements. No local tax, rent cap, utility tariff or insurance availability conclusion is drawn here.</div>'''
    )

    pages["inheritance.html"] = (
        "Inheritance steps and deadlines",
        "A source-linked, step-by-step checklist for a trust inheritance expected around 2040–2050, including assessor reporting, property-tax claims, federal returns and beneficiary accounts.",
        '''<div class="note"><strong>Calendar from the triggering event.</strong> This general checklist is not a substitute for reading the actual trust, will, deed, notice and current forms. Probate, non-probate and trust transfers can have different procedures. For a 2040–2050 trust administration, recheck current law at that future date.</div>
<section><h2>How a trust inheritance around 2040–2050 would be sequenced — step by step</h2><p>Property A is treated as inherited by trust. The table below orders the work from before the transfer through the hold-or-decide period. No parcel or personal date is assumed.</p>''' + plain_table(
            "Step-by-step sequence for a trust transfer — no private dates published",
            ["Phase", "Timing", "Work to do", "Key rule to recheck at that time"],
            [
                ["1 · Before the transfer", "While the trust is in place", "Confirm trust terms, successor trustee, beneficiaries, distribution provisions and how property is titled; keep documents and contact list current", "Current trust and title records; no deadline yet"],
                ["2 · Death and immediate administration", "Days after the triggering death", "Secure property and records; identify the date of death for valuation; notify insurers, lenders, tenants and advisers; identify the trustee event for notice", f"Trustee notice rule; {source_link('probate_16061_7', 'Probate Code 16061.7: 60-day notice')}"],
                ["3 · Assessor and property-tax work", "Within months of the transfer", "File the change-in-ownership statement; request the current roll and supplemental notices; test family-home eligibility and claim before relying on it", f"{source_link('rtc_480', 'RTC 480: 150-day statement')} and {source_link('rtc_63_2', 'RTC 63.2: occupancy within one year, claim periods')}"],
                ["4 · Tax and beneficiary accounts", "Within months, before filing deadlines", "Gather date-of-death valuation for basis; calculate the estate filing test; contact retirement custodians; separate decedent, estate/trust and beneficiary income", f"{source_link('irs_inherited_basis', 'IRS inherited basis')} · {source_link('irs_form706', 'IRS Form 706: nine months')} · {source_link('irs_retirement_beneficiary', 'IRS beneficiary rules')}"],
                ["5 · Hold, maintain and decide", "Months to years after transfer", "Maintain, insure and collect rent if renting; then compare live, rent, sell-and-reinvest or defer using the private year-by-year workbook and irregular stress paths", "Current federal, state and local law; see <a href=\"projections.html\">Projection method</a> and <a href=\"stress.html\">Stress cases</a>"],
            ],
            row_class="framework-row",
        ) + '''</section>
<section><h2>Time-sensitive legal steps — deadlines to calendar</h2>''' + fact_table(
            "General California and federal deadlines",
            ["Step", "General rule summary", "Action"],
            [
                (["Trustee notice", "For specified events, including a revocable trust becoming irrevocable at death, California requires notice to specified beneficiaries/heirs; the statute generally sets 60 days with trigger, awareness and vacancy qualifications.", "Identify the event, trustee, notice recipients and actual service date from the trust and current statute."], "probate_16061_7"),
                (["Assessor change-in-ownership statement", "For a transfer by death outside probate, the trustee or transferee generally files within 150 days. If the property is subject to probate, the personal representative files before or with the inventory and appraisal.", "Obtain the current form and filing instructions from the proper county assessor; track each parcel privately."], "rtc_480"),
                (["Potential family-home exclusion", "For a qualifying family-home transfer, principal-residence occupancy and the homeowner/disabled-veteran exemption are generally required within one year. The ordinary claim period is generally three years after transfer, before a third-party transfer, or when the eligible transferee stops occupying the residence, whichever is earlier; statutory and notice-related exceptions may apply.", "Ask the assessor about eligibility, claim forms, supplemental notices and any exception before relying on an exclusion."], "rtc_63_2"),
                (["Federal estate-tax return", "Form 706 is generally due nine months after death when required. A portability election for a surviving spouse has a timely-return rule; extension rules are in current IRS instructions.", "Executor and tax adviser should calculate the filing test, gather valuations and calendar the applicable date."], "irs_form706"),
                (["Beneficiary retirement account", "For deaths in 2020 or later, a designated beneficiary who is not an eligible designated beneficiary generally follows a 10-year distribution rule; spouses and eligible designated beneficiaries may have different options. Taxable distributions generally enter gross income.", "Contact the custodian, confirm beneficiary status and plan terms, and verify current IRS rules; no account is assumed."], "irs_retirement_beneficiary"),
            ]) + '''</section>
<section><h2>Administration checklist</h2>''' + list_html([
            f"Identify the personal representative, trustee or successor fiduciary and read the governing documents. {source_link('irs_survivors', 'IRS Publication 559')}",
            'Secure the property and records; notify insurers, lenders, tenants, service providers and tax professionals as applicable.',
            'Separate the decedent’s final individual income from later estate/trust income and beneficiary income. Keep receipts, valuations and distributions.',
            'Record each property’s ownership, transfer date, use, income and expense trail separately. Do not combine Property B with Property A without title evidence.',
            'Recheck current federal, state and local law before making a sale, occupancy change or distribution — especially for a transfer expected in 2040–2050.'
        ]) + '''<p>Use the <a href="questions.html">Questions first</a> page to identify missing documents. This page deliberately contains no personal names, dates, forms completed or property-specific deadlines.</p></section>'''
    )

    pages["questions.html"] = (
        "Questions before deciding",
        "A clear list of questions, information and answers that need to be addressed before any decision can be reasonably made, and how to discover missing information.",
        '''<p>Keep answers and supporting documents in a private working file. The public cells below remain blank; no answer is requested or stored by this site. The list distinguishes what the public guide can answer from official sources and what must be verified privately.</p>
<section><h2>Resolve these questions first — have vs missing, answer, discovery</h2>''' + blank_table(
            "Private question register — blank until verified; information we have vs do not have",
            ["Order", "Question", "Public answer (official rule only)", "How to resolve / discover"],
            [
                ["1 · Ownership", "Who holds legal and beneficial title to A and B, and what transfers on death?", '<td class="blank">Not published</td>', "Recorded title, trust/will, beneficiary and estate records; verify who is trustee at death"],
                ["2 · Timing", "What event/date triggers notice, assessor, tax and claim deadlines?", '<td class="blank">Not published</td>', "Death/transfer documents and official notices; see <a href=\"inheritance.html\">Inheritance steps</a> for calendars"],
                ["3 · A's basis", "What is A's defensible date-of-death value and basis record?", '<td class="blank">Not published</td>', f"Independent valuation and estate records; {source_link('irs_inherited_basis', 'IRS inherited-basis rule')}"],
                ["4 · Property tax", "Does A qualify for a family-home exclusion, and were the occupancy/exemption/claim steps met?", '<td class="blank">Not published</td>', f"Current statute and assessor decision; {source_link('rtc_63_2', 'RTC section 63.2')} and {source_link('boe_prop19', 'BOE Prop 19 overview')}"],
                ["5 · B's income", "What rent was collected, what was vacant, and what expenses/depreciation are recorded?", '<td class="blank">Not published</td>', f"Leases, rent ledger, bills and prior returns; {source_link('irs_rental', 'IRS Publication 527')}"],
                ["6 · Occupancy", "Would the recipient use A or B as a home, and what rent or housing cost would change?", '<td class="blank">Not published</td>', "Personal housing plan, tenant/lease review and current costs; note B can be lived in without losing all rent only if a unit remains rentable"],
                ["7 · Running costs", "What are property tax, insurance, water, electricity/solar, maintenance and repair costs year by year?", '<td class="blank">Not published</td>', f"Actual bills, policy/utility agreements, inspections and estimates; {source_link('cdi_premiums', 'CDI survey limits')} and {source_link('cpuc_solar', 'CPUC tariff overview')}"],
                ["8 · Local law", "Which local rental, transfer-tax, property-tax and utility rules apply to each property?", '<td class="blank">Not published</td>', "Verify jurisdiction privately; check assessor, local ordinance and utility/provider records"],
                ["9 · Estate total and prior gifts", "What are the estate's total assets, deductions, prior gifts and elections against the federal threshold?", '<td class="blank">Not published</td>', f"Executor's records and current Form 706 instructions; {source_link('irs_estate', 'IRS estate-tax rules')} and {source_link('irs_2027_adjustments', 'IRS 2027 thresholds')}"],
                ["10 · Retirement accounts", "Are there retirement accounts or plans, who is designated as beneficiary, and what distribution rules apply?", '<td class="blank">Not published</td>', f"Latest beneficiary designation and current plan/IRS rules; {source_link('irs_retirement_beneficiary', 'IRS beneficiary rules')}"],
                ["11 · Cash inheritance", "How much liquid inheritance is expected and when will it be available?", '<td class="blank">Not published</td>', "Estate/trust account statements and distribution provisions; keep amount private"],
                ["12 · Solar and utility tariffs", "What are the solar system, interconnection, tariff and export-credit terms for A and B?", '<td class="blank">Not published</td>', f"System agreement, bill and provider; {source_link('cpuc_solar', 'CPUC tariff overview')}"],
                ["13 · Insurance and replacement", "Can each property be insured for its full value at the intended use and occupancy?", '<td class="blank">Not published</td>', f"Written quotes per occupancy; {source_link('cdi_premiums', 'CDI premium comparison limits')}"],
                ["14 · Risk and priorities", "What liquidity, workload, market, insurance and family-use risks matter most for this household?", '<td class="blank">Not published</td>', "Agree decision criteria and time horizon before choosing assumptions"],
            ]) + '''</section>
<section><h2>What the public guide already answers vs what must be discovered privately</h2>''' + plain_table(
            "Information status — official general rules vs private facts",
            ["Category", "What we have (official, source-linked)", "What is still missing (private, blank)"],
            [
                ["Federal estate and gift rules", "2026 and 2027 thresholds and filing rules from IRS", "Estate total, prior gifts, deductions, elections for this household"],
                ["California property tax", "Prop 13 1% base, 2% cap, reassessment and family-home statute", "Each property's roll, bill, supplemental notices and assessor decision"],
                ["Rental and tenancy", "Federal reporting, statewide cap and just-cause statutes", "Leases, lawful coverage, actual rent, vacancy and local ordinance"],
                ["Insurance and utilities", "Comparison-survey limits and tariff-source overview", "Quotes, coverage, deductibles, actual bills and system agreements"],
                ["Economic stress", "Five official historical episodes as anchors", "Household-specific income, repair lump sums and liquidity needs"],
            ],
            row_class="framework-row",
        ) + '''</section>
<section><h2>Suggestions to discover missing information</h2>''' + list_html([
            'Request current assessor roll and tax bill for each property and ask the assessor for written eligibility guidance before relying on any exclusion.',
            'Obtain a qualified date-of-death valuation and keep the appraisal with estate records for basis support.',
            'Reconcile rent ledgers, leases, deposits and vacancy month by month for B; do the same prospectively for any rent of A.',
            'Collect 12 months of actual water, electricity/solar, insurance and maintenance invoices; separate routine maintenance from capital work with contractor estimates.',
            'Contact each retirement custodian for the latest beneficiary designation and plan distribution rules; do not assume a ten-year or spouse rule without confirmation.',
            'Have a licensed professional review title, trust terms, tenant notices, coverage and local ordinances in private.',
            'Document decision criteria and then test each path under the irregular economic cases rather than a single growth rate.'
        ], ordered=True) + '''<div class="note"><strong>Privacy reminder.</strong> Do not paste deeds, tax bills, account numbers, exact assessments, quotes or other personal details into a public issue, pull request or website field. Keep them in the private workbook described on <a href="suggestions.html">Suggestions for review</a>.</div>'''
    )

    pages["suggestions.html"] = (
        "Suggestions for review",
        "Proposed improvements are kept separate from the public edition; no suggestion is selected or implemented automatically.",
        '''<div class="answer"><strong>Selection status: none recorded.</strong> This page is a review register, not a feature request form. Nothing listed below changes the site until it is separately reviewed and selected. Review each row, choose a path only after weighing privacy, cost and maintenance, then implement outside this page.</div>
<section><h2>Proposals — site and decision improvements</h2>''' + plain_table(
            "Suggestions kept separate for review — choose before implementing",
            ["ID", "Proposal", "Privacy / decision benefit", "Status"],
            [
                ["S-01", "Keep all property-specific inputs in an offline, access-controlled workbook.", "Avoids publishing or collecting figures; allows private records and supporting documents.", "Proposed — not selected or implemented."],
                ["S-02", "Maintain two ledgers: A as inherited, B as already owned, with separate title, basis, rent and operating-cost records.", "Preserves the ownership distinction and reduces accidental double-counting.", "Proposed — not selected or implemented."],
                ["S-03", "Have a qualified tax/legal professional review any future property-specific calculations before use.", "Checks title, local law, occupancy, basis, tax treatment and deadlines without publishing personal records.", "Proposed — not selected or implemented."],
                ["S-04", "Recheck official rules at the transfer date, before a sale or occupancy change, and after material law changes.", "Prevents stale federal, state and local assumptions from being treated as permanent.", "Proposed — not selected or implemented."],
                ["S-05", "If a calculator is later selected, make it local-only and show sources, blank unknowns and stress cases.", "Avoids transmitting private inputs; separates fact, assumption and computation.", "Proposed — not selected or implemented."],
                ["S-06", "Add a private, offline year-by-year projection workbook with irregular historical paths, not a constant rate.", "Mimics real-world uneven growth and inflation over 50 years; keep the constant-rate illustration off the public site.", "Proposed — not selected or implemented."],
                ["S-07", "Maintain a maintenance and capital-reserve schedule from inspection and contractor estimates, not averages alone.", "Surfaces a large, lumpy repair that an average hides; keep estimates private.", "Proposed — not selected or implemented."],
                ["S-08", "Verify insurance coverage, renewability and the state insurer-of-last-resort limit with written quotes per use.", "Confirms whether full replacement can be insured at the relevant value and occupancy.", "Proposed — not selected or implemented."],
                ["S-09", "Check city/county rental, transfer-tax and utility tariffs privately for each property.", "State rules alone do not establish local coverage or cost; verify jurisdiction before a rent or sale decision.", "Proposed — not selected or implemented."],
                ["S-10", "Record decision criteria and risk priorities before running any calculation.", "Prevents a presentation choice from driving the winner; criteria include cash flow, housing value, liquidity and workload.", "Proposed — not selected or implemented."],
            ]) + '''</section>
<section><h2>How to review a suggestion</h2>''' + list_html([
            'Read the proposal, its benefit and the private inputs it would require.',
            'Check whether it can be done without putting personal values, addresses or parcel records into a public page or artifact.',
            'Identify the official source that would support any new factual row before it is published.',
            'Decide whether to adopt, defer or reject; record the choice offline. The site does not collect a selection.',
            'If adopted, re-run <code>python3 scripts/build.py</code>, <code>python3 scripts/verify.py</code> and <code>python3 scripts/privacy_boundary.py</code> and confirm the artifact remains allowlisted.'
        ], ordered=True) + '''</section>
<section><h2>Selection gate</h2><p>Before any proposal is implemented, decide whether its benefit is worth the privacy and maintenance cost, define the inputs it would require, identify its official sources, and test that no private values enter a public artifact. The suggestions page itself does not collect a selection.</p><div class="note"><strong>Privacy reminder.</strong> Do not paste deeds, tax bills, rent ledgers, account numbers, exact assessments or quotes into a public issue, pull request or website field. Keep them in the private workbook described in S-01.</div></section>'''
    )

    pages["review.html"] = (
        "Flagged items — values left blank",
        "A public register of unverified or decision-sensitive facts. No property-specific amount is inferred, rounded or displayed.",
        '''<div class="privacy"><strong>Blank means unknown here.</strong> The public edition deliberately removes owner-derived inputs and calculated values. The flags below describe missing evidence, not any particular property's condition or amount.</div>
<section><h2>Items to resolve privately</h2>''' + plain_table(
            "Flag register — unresolved items, not factual claims",
            ["ID", "Unverified or sensitive item", "Why it matters", "Private resolution step"],
            [
                ["F-01", "A's title, transfer instrument and date", "Ownership determines transfer, basis and deadlines.", f"Review the recorded documents and estate/trust file; {source_link('rtc_480', 'change-in-ownership reporting')}"],
                ["F-02", "A's date-of-death value and basis", "Needed for tax reporting and sale comparison.", f"Obtain a qualified valuation and supporting estate records; {source_link('irs_inherited_basis', 'IRS basis guidance')}"],
                ["F-03", "A's assessed value, property-tax bill and any exclusion status", "Property tax can change after a transfer; claim conditions are fact-specific.", f"Request the current assessor roll and written eligibility guidance; {source_link('rtc_63_2', 'California family-home statute')}"],
                ["F-04", "B's ownership, basis and depreciation history", "B is treated as already owned, not inherited with A; records must substantiate that treatment.", f"Verify title and prior tax/closing records; {source_link('irs_rental', 'IRS rental-basis and depreciation guidance')}"],
                ["F-05", "B's rent, vacancy, collection and occupancy", "Rental cash flow and possible owner occupancy change the comparison.", f"Reconcile leases, deposits, rent receipts and tenant obligations; {source_link('irs_rental', 'IRS rental reporting')}"],
                ["F-06", "Insurance premiums, coverage and renewability", "A survey is not a property-specific quote and coverage may differ by use.", f"Obtain current written quotes and confirm occupancy/landlord coverage; {source_link('cdi_premiums', 'CDI survey limitations')}"],
                ["F-07", "Water, electricity, solar tariff and service costs", "Bills and credits depend on provider, system and tariff.", f"Review actual service bills and system/interconnection agreements; {source_link('cpuc_solar', 'CPUC tariff overview')}"],
                ["F-08", "Maintenance, repairs and major capital work", "Averages can hide a large irregular expense.", f"Obtain an inspection and written estimates; separate repair from improvement; {source_link('irs_rental', 'IRS repair/improvement guidance')}"],
                ["F-09", "Local rental, property-tax, transfer-tax and occupancy rules", "State rules alone do not establish local coverage or cost.", "Check current city/county ordinances, assessor records and provider rules privately; no jurisdiction is identified here."],
                ["F-10", "Estate total, prior gifts, deductions and election choices", "A property's value alone cannot establish federal estate-tax exposure.", f"Executor and tax adviser review the full estate and current filing test; {source_link('irs_estate', 'IRS estate-tax rules')}"],
                ["F-11", "Retirement accounts and beneficiary designations", "Distribution periods and tax treatment vary by account and relationship.", f"Contact each custodian and verify plan terms; {source_link('irs_retirement_beneficiary', 'IRS beneficiary overview')}"],
                ["F-12", "Future returns, inflation, law and decision date", "A long horizon is uncertain; one growth rate is not a reliable 50-year forecast.", 'Use multiple paths and update rules at decision time; see <a href="stress.html">historical stress cases</a>.' ],
            ],
            row_class="flag-row",
        ) + '''</section>
<p>No figure is inferred from a rounded assessment, public database, nearby property, online estimate or another edition. Property-specific monetary values remain unpublished; this register does not establish the condition or amount of any item.</p>'''
    )

    pages["audit.html"] = (
        "Privacy, source and audit limits",
        "The public edition is intentionally a general framework. This page records its evidence standard, current-tree scope and limits without reproducing private findings.",
        '''<section><h2>What this edition contains</h2>''' + list_html([
            'One clearly labelled public edition with the inherited Property A / already-owned Property B distinction.',
            'Source-linked federal and California rules, an inheritance checklist, blank cost fields, questions, flagged unknowns and general stress cases.',
            'No property-specific inputs, assessments, rent, utility use, insurance quote, owner-derived projections or individualized recommendation.',
            'A static, no-input site: no form, script, analytics, tracking pixel or third-party asset is included in the public pages.'
        ]) + '''</section>
<section><h2>Verification standard</h2><p>General legal and historical claims link directly to the official publisher. The source library states what each source supports, when it was checked and its limits. Generic public sources cannot verify a property's title, value, tax bill, rent, utility use, coverage or condition; those fields remain blank. Dollar thresholds shown are general rules, not owner-derived amounts. Rounding is not treated as anonymization, so property-specific amounts are omitted.</p><p>The economic examples are historical U.S. index or aggregate episodes, not property forecasts. Local law, current policy terms, utility tariffs, property condition and future tax law require a private, date-specific review.</p></section>
<section><h2>Current tree versus history</h2><p>This refresh replaces owner-derived material in the current public edition and retires non-allowlisted routes with content-free notices. It does not rewrite old commits, pull-request diffs, caches, forks, downloads or copies outside this repository. No claim of complete historical erasure is made.</p><p>The Pages workflow packages an explicit allowlist plus generic withdrawal notices. The deployment source and live artifact must be confirmed after merge; a successful local package check alone is not a deployment check.</p></section>
<section><h2>Reproducible local checks</h2><pre><code>python3 scripts/build.py
python3 scripts/verify.py
python3 scripts/package_site.py
python3 scripts/privacy_boundary.py</code></pre><p>These checks validate the current files and generated artifact; they cannot certify that old external copies were erased or that a private document is accurate.</p></section>'''
    )

    source_rows = []
    for item in SOURCES_DOC["sources"]:
        source_rows.append((
            [
                f"<strong>{esc(item['publisher'])}</strong><br>{esc(item['title'])}",
                esc(item["supports"]),
                esc(item["checked"]),
                esc(item["limits"]),
            ],
            item["id"],
        ))
    pages["sources.html"] = (
        "Official source library",
        "A line-by-line source ledger for the general legal rules and historical economic facts used in the public edition.",
        '''<p>Each factual row on the decision pages links to its official source. Sources below were opened on the publishing agency's domain on the date shown. Links verify the stated general rule or historical fact, not any private property value, title, tax result, bill or forecast.</p>
<section><h2>Evidence ledger</h2>''' + fact_table(
            "Official sources and verification limits",
            ["Publisher and document", "What the source supports", "Checked", "Limit"],
            source_rows) + '''</section>'''
    )

    for filename in PAGES:
        title, description, body = pages[filename]
        (ROOT / filename).write_text(page_shell(filename, title, description, body), encoding="utf-8")
    print(f"Rendered {len(PAGES)} privacy-safe public pages from official-source metadata; no property model loaded.")


if __name__ == "__main__":
    build_pages()
