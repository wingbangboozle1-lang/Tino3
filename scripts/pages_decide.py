"""Decision analysis, inheritance process, laws, flags, sources, privacy."""
from webbuild import exact, DATA, money, pct, table, section, callout, links, link, esc, NAV
from sources import SOURCES

O = DATA["owner"]
A = DATA["assumptions"]
V = DATA["values"]
D = DATA["decisions"]
D40, D45, D50 = D["2040"], D["2045"], D["2050"]
REC = DATA["reconcile"]

PAGES = []

LABELS = ["Sell, reinvest at Treasury yield", "Sell, reinvest in equities (7%)",
          "Live in it (full reassessment)", "Live in it, Prop 19 exclusion applied",
          "Rent it out (indicative rent)", "Rent it out (rent 30% lower)"]


def opt_table(T) -> str:
    T = int(T)
    K = str(T)
    rows = []
    for i, r in enumerate(D[K]["rows"]):
        rows.append([LABELS[i], money(r["terminal"]),
                     money(r.get("cash")) if r.get("cash") not in (None, 0.0) else "&mdash;",
                     money(r.get("tax_paid")) or "&mdash;",
                     money(r.get("cg_tax")) or "&mdash;",
                     ["TREASURY", "IRS-T409", "COMPUTED"]])
    return table(["Path", "After-tax wealth at the end of the horizon", "Cumulative net cash flow",
                  "Property tax paid", "Capital-gains tax at exit", "Source"],
                 rows, note=f"Inheritance year {T}, horizon {T + 20}. All figures nominal and net of selling costs.")


summary = table(["Inheritance year", "Property A market value", "Sell at Treasury yield", "Rent (indicative)", "Live in it", "Rent needed to match selling", "Source"],
                [[str(T), money(D[T]['market_T']), money(D[T]['sell_treasury']), money(D[T]['rows'][4]['terminal']),
                  money(D[T]['live_base']), money(D[T]['breakeven_month']), ["TREASURY", "COMPUTED"]]
                 for T in ("2040", "2045", "2050")],
                note="The ordering is the same at all three inheritance years: selling leads, renting is second, occupancy is last.")

sens_t = table(["Change to the base case", "Sell at Treasury yield", "Rent", "Live in it", "Does the ranking change?", "Source"],
               [[s["label"], money(s["sell"]), money(s["rent"]), money(s["live"]),
                 ("No" if s["sell"] >= max(s["rent"], s["live"]) else "Yes &mdash; holding leads"),
                 ["BLS-CPI", "TREASURY", "COMPUTED"]] for s in DATA['sensitivity']],
               note="2045 inheritance. Appreciation and inflation are the two assumptions that could reverse the answer; "
                    "inflation barely matters, appreciation almost does.")

inv = table(["Reinvestment assumption", "After-tax wealth 20 years after selling", "What it is", "Source"],
            [[s["label"], money(s["terminal"]),
              ("A real market return is not guaranteed and can be negative in any given decade" if "7.00" in s["label"]
               else "Interest is taxed federally at the assumed marginal rate; California exempts U.S. obligations (F-11)"
               if "4.88" in s["label"] else "Sensitivity only"),
              ["TREASURY", "IRS-T409"]] for s in DATA['invest_sens']],
            note="The 4.88% row is the only one backed by an observed market price on the review date.")

break_even = table(["Inheritance year", "Indicative rent (derived)", "Rent needed to match selling at 4.88%", "Rent needed to match selling into equities at 7%", "Appreciation that makes renting match selling", "Appreciation that makes living match selling", "Source"],
                   [[str(T), money(D[T]['rent_base_month']), money(D[T]['breakeven_month']),
                     money(D[T]['breakeven_month_vs_equity']), pct(D[T]['crossover_rent'], 1),
                     pct(D[T]['crossover_live'], 1), ["COMPUTED", "TREASURY", "FHFA-HPI"]]
                    for T in ("2040", "2045", "2050")],
                   note="Indicative rent is derived, not quoted: it applies the gross yield the owner actually achieves "
                        "on Property B (4.77%) to Property A's market value and is labelled UNVERIFIED-derived (F-06).")

PAGES.append(("decision-analysis.html", "Decision analysis", f"""
<h1>Decision analysis</h1>
<p class="lede">Three paths, one method: hold everything else constant, tax everything that is taxed, and
compare what you would actually own twenty years after the death.</p>

{section("What is compared, and what is not", f'''
<p><b>Compared:</b> Property A only. Every path starts the day you inherit it and ends twenty years later,
after selling costs, capital-gains tax, property tax, insurance, water, electricity and repairs &mdash; all of
which are separately projected on the other pages.</p>
<p><b>Not compared:</b> Property B's value, which is identical in every path. The one difference is its
owner-occupied unit: if you move to Cupertino that unit can be let, so the live-in path is credited with
{money(DATA['rent_a']['unit_rent_b'])} a month of rent (derived from the owner's own rent roll, F-07).</p>
<p><b>Deliberately excluded:</b> mortgage financing (none assumed), passive-activity loss limits, the
alternative minimum tax, and any income tax on retirement accounts. They are listed as flags rather than
assumed away.</p>
''')}

{section("The comparison, 2045 inheritance", opt_table(2045),
         sub="Base case: 3.0% appreciation, 3.0% inflation, 4.88% risk-free reinvestment.")}

{section("All three inheritance years", summary,
         sub="Same method, three start dates. The conclusion does not depend on the year within your window.")}

{section("Break-even points", break_even,
         sub="The two numbers that would change the answer, stated as thresholds instead of guesses.")}

{callout("good", "The decision rule", f'''
<p><b>Sell.</b> The measured outcome is better than every alternative in the base case, and selling is the only
path whose return does not depend on a rent forecast or a 20-year appreciation assumption &mdash; it converts
the house into a verified 4.88% yield on the day you inherit it.</p>
<p><b>Rent instead only if two things are true:</b> two written rental appraisals clear
{money(D45['breakeven_month'])} a month in 2045 dollars, <em>and</em> you expect Cupertino values to compound at
{pct(D45['crossover_rent'],1)} or better. At the 2026 one-year reading of +0.9%, that is a big assumption.</p>
<p><b>Live in it only as a lifestyle decision.</b> It is the weakest financial path by about
{money((D45['sell_treasury'] - D45['live_base']) / 20)} a year at the base case. If living in that house is worth
that to you, take it &mdash; but take it knowing the price.</p>''')}

{section("Sensitivity: what could reverse the ranking", sens_t)}

{section("Where the sale proceeds go", inv,
         sub="The reinvestment side of the sell path, priced four ways.")}

{section("Risks that are not in the numbers", table(
    ["Risk", "Effect", "Mitigation", "Source"],
    [
        ["Tenant law", "San Francisco rent control caps increases at 1.6% and constrains termination; a long tenancy below market is a real cost if you ever sell with tenants in place.", "Model rent at the cap, and price vacant possession before listing.", ["SF-RENT"]],
        ["Reassessment timing", "The supplemental bill for the new taxable value lands after the death and is prorated from the date of death.", "Reserve cash in year one.", ["SCC-ASSESSOR"]],
        ["Insurance availability", "California's admitted market is stressed; 677,449 homes are on the FAIR Plan, whose policies cover fire and not much else.", "Get a quote before you decide to hold, not after.", ["CDI-SIS"]],
        ["Solar tariff", "The net-metering credit may end with the tariff term, turning a small credit into a small cost.", "Ask the utility for the interconnection date and tariff.", ["CPUC-NEM"]],
        ["Law change", "The federal exclusion is statutory, not constitutional, and can be changed by any future Congress.", "Do not build a plan that only works above the current exclusion.", ["IRS-ESTATE"]],
        ["Market return", "A 7% equity assumption is not a promise; the 2000s delivered a negative decade.", "Compare against the verified Treasury yield, which is what the base case does.", ["TREASURY"]],
    ]))}
""", "decision-analysis.html", "After-tax comparison of living in, renting, or selling the inherited house."))

# =====================================================================
# INHERITANCE PROCESS
# =====================================================================
steps = [
    ["1", "The death", "Date of death is the valuation date for your basis and for the county's reassessment. Nothing can be backdated later.", "Immediately", "Date-of-death appraisal ordered; death certificates obtained", ["IRS-BASIS", "SCC-ASSESSOR"]],
    ["2", "Successor trustee accepts", "The trustee named in the trust takes over, or declines and a successor is appointed under the document.", "Immediately", "Written acceptance; trustee's attorney engaged", ["PROB-16061"]],
    ["3", "Notification by trustee", "The trustee must serve notice on every beneficiary and heir. This starts the clock on the period to contest the trust.", "Within 60 days", "Notice served; proof of service kept", ["PROB-16061"]],
    ["4", "Change in ownership statement", "For property held in trust, the trustee files a change in ownership statement with the county assessor or recorder in each county.", "Within 150 days of death", "Penalty is the greater of $100 or 10% of the new tax, capped at $5,000", ["RTC-480"]],
    ["5", "Reassessment of the house", "The assessor sets a new base-year value as of the date of death. This is the event that resets the property tax.", "At death, processed within months", "Notice of assessed value; then a supplemental bill", ["SCC-ASSESSOR", "SF-TTC"]],
    ["6", "Prop 19 claim, if it applies", "Only for a principal residence used by both the transferor and you. Claim with the assessor; the deadline is generous but the exemption deadline is not.", "Exclusion within 3 years; homeowners' exemption within 1 year", "Claim filed; occupancy documented", ["BOE-P19"]],
    ["7", "Homeowners' Exemption", "If you occupy the house as your principal residence, claim the exemption on the new assessment.", "Within 1 year of transfer", "About $70 to $80 a year of tax saved", ["SCC-ASSESSOR"]],
    ["8", "Title and trust administration", "The trustee distributes, or holds, per the trust. Confirm the property insurance and title are in the right name from the date of death &mdash; a gap in coverage is a real exposure.", "Before distribution", "Trustee deed or distribution; new insurance binder", ["PROB-16061"]],
    ["9", "Federal estate tax, if required", "A Form 706 filing is required only if the gross estate plus adjusted taxable gifts exceeds the year-of-death exclusion. Portability for a surviving spouse must be elected on that return.", "Per IRS filing rules", "Form 706 prepared only if the estate is near the threshold", ["IRS-ESTATE", "IRS-2027"]],
    ["10", "Trust income tax returns", "The trust becomes its own taxpayer for its final years; income is reported and the trustee accounts to the beneficiaries.", "Annual", "Form 1041 and a trust accounting", ["PROB-16061"]],
    ["11", "Decide &mdash; live, rent or sell", "The cheapest moment to sell is before the house has appreciated further and before depreciation reduces your basis. This is the decision modelled on this site.", "Within 12 months of death", "Appraisal, rental appraisals, written decision", ["IRS-BASIS", "IRS-T409"]],
    ["12", "If you sell", "Selling costs and the capital-gains computation, with the stepped-up basis documented.", "After the decision", "Settlement statement; gain reported on Schedule D", ["IRS-BASIS", "IRS-T409"]],
]
step_t = table(["#", "Step", "What happens", "Deadline", "Watch out for", "Source"],
               [[s[0], f"<b>{s[1]}</b>", s[2], s[3], s[4], s[5]] for s in steps])

PAGES.append(("inheritance-process.html", "Inheritance process", f"""
<h1>How the inheritance actually works</h1>
<p class="lede">Twelve steps from the death to a decision. Three of them carry deadlines with penalties, and one
of them &mdash; the valuation date &mdash; fixes both your income-tax basis and the county's new assessed value.</p>

{callout("warn", "The two dates that matter most", f'''<p><b>The date of death</b> is simultaneously your basis in
the property (fair market value, {link('IRS-BASIS')}) and the date the county reassesses it
({link('SCC-ASSESSOR')}). <b>The 150th day after death</b> is when the change in ownership statement is due
({link('RTC-480')}); missing the assessor's request for it carries a penalty of the greater of $100 or 10% of the
new tax, capped at $5,000.</p>''')}

{section("Step by step", step_t,
         sub="Timing assumes the property is held in a trust, which is the premise of this project. Probate is not modelled because a trust avoids it for trust assets.")}

{section("Common ways this goes wrong", table(
    ["Mistake", "Consequence", "Prevention", "Source"],
    [
        ["No date-of-deathappraisal", "Your basis is undocumented; an audit becomes an argument.", "Order a retrospective appraisal in the first 90 days.", ["IRS-BASIS"]],
        ["Assuming the trust protects the property tax", "The exclusion is about occupancy and value, not about the trust. A rented house is reassessed.", "Read the Prop 19 conditions before assuming a lower bill.", ["BOE-P19"]],
        ["Missing the 1-year homeowners' exemption", "The exclusion claim survives, but the exemption does not.", "Calendar the date at the death, not at the distribution.", ["BOE-P19"]],
        ["Letting the insurance lapse", "An uninsured gap between death and retitling.", "Notify the insurer in writing in the first week.", ["CDI-SIS"]],
        ["Waiting years to decide", "Depreciation reduces the basis and converts part of the gain into 25% recapture; the property tax at the new base is paid every year in the meantime.", "Decide within twelve months.", ["IRS-P527", "IRS-T409"]],
    ]))}
""", "inheritance-process.html", "Step-by-step trust inheritance process with statutory deadlines."))

# =====================================================================
# LAWS
# =====================================================================
laws = [
    ["Federal estate tax exclusion", "Set at $15,000,000 for 2026 and indexed from 2027 ($15,480,000).", "<span class='tag ver'>ENACTED</span>", "Lowers the chance of any federal estate tax on this estate.", ["IRS-2027"]],
    ["Proposition 19 (2021)", "Parent-child exclusion limited to a principal residence, capped at taxable value plus an adjusted $1,000,000; exclusion for other real property removed.", "<span class='tag ver'>ENACTED</span>", "Drives the entire property-tax side of this decision.", ["BOE-P19"]],
    ["Prop 19 cap re-indexing", "BOE must re-adjust the $1,044,586 amount every two years. The next adjustment applies from 16 Feb 2027.", "<span class='tag ver'>SCHEDULED</span>; amount for 2027 onward not published", "A larger cap protects more value; it is modelled as growing with inflation (F-02).", ["BOE-CAP"]],
    ["Net billing tariff (D.22-12-056)", "New solar interconnections since 15 Apr 2023 are paid for exports at value-of-generation, not retail; the legacy net-metering tariffs are closed.", "<span class='tag ver'>ENACTED</span>", "Weakens the solar credit over time; it is the reason the electricity line is modelled as shrinking.", ["CPUC-NEM"]],
    ["San Francisco rent ordinance", "Annual allowable increase for covered units is 1.6% for March 2026 to February 2027, reset annually.", "<span class='tag ver'>IN FORCE</span>", "Caps the growth of the rent you already collect on Property B.", ["SF-RENT"]],
    ["SFPUC rate steps", "+7.0% water and +15.0% sewer on 1 July 2026; +7.0% and +14.5% on 1 July 2027.", "<span class='tag ver'>ADOPTED</span>", "Sets the near-term water escalation; later years are assumed.", ["SFPUC"]],
    ["San Francisco parcel taxes", "Five named parcel taxes, inflation-adjusted annually, including a per-unit charge on multi-family parcels.", "<span class='tag ver'>IN FORCE</span>", "Explains most of Property B's flat charges.", ["SF-PARCEL"]],
    ["Insurance market reform", "Sustainable Insurance Strategy: rate filings averaging about 6.9% and slower FAIR Plan growth in Q1 2026.", "<span class='tag ver'>IN PROGRESS</span>", "Supports a 6% insurance escalation rather than the double-digit years.", ["CDI-2026", "CDI-SIS"]],
    ["A California wealth tax", "Constitutional amendments have been introduced that would let the Legislature tax all forms of personal property or wealth; FTB analyses exist for earlier versions.", "<span class='tag gap'>PROPOSED &mdash; not law; current status not verified</span>", "If ever enacted it would be a new recurring cost on holdings, not on an inheritance.", ["FTB-RATES"]],
    ["A California estate or inheritance tax", "California has none, and Revenue and Taxation Code 13301 forbids one without a constitutional change.", "<span class='tag ver'>NOT LAW &mdash; PROHIBITED</span>", "No state death tax is budgeted, correctly.", ["RTC-13301"]],
    ["Federal estate tax repeal or cut", "Any future Congress can change the exclusion; it is statutory, not constitutional.", "<span class='tag gap'>UNKNOWN</span>", "Do not build a plan that depends on the exclusion staying where it is.", ["IRS-ESTATE"]],
    ["Property tax reform (split roll, Prop 13 changes)", "Recurring statewide proposals would change assessment rules for non-residential property or for inherited property.", "<span class='tag gap'>UNKNOWN &mdash; no enacted change identified in this review</span>", "Would change the holding case more than the selling case, which is another argument for selling.", ["RTC-51"]],
]
laws_t = table(["Measure or rule", "What it does", "Status", "Effect on this decision", "Source"],
               [[l[0], l[1], l[2], l[3], l[4]] for l in laws])

PAGES.append(("laws-watch.html", "Laws & watch list", f"""
<h1>Laws, and what is being discussed</h1>
<p class="lede">Everything below is separated into what is enacted, what is scheduled, and what is merely
proposed. A proposal is not a rule and is not priced into any projection on this site.</p>

{callout("warn", "How to read the status column", '''<p><span class="tag ver">ENACTED</span> and
<span class="tag ver">IN FORCE</span> rows are law today and are priced into the model.
<span class="tag ver">SCHEDULED</span> rows are law but the amount is not yet published &mdash; those are flagged.
<span class="tag gap">PROPOSED</span> and <span class="tag gap">UNKNOWN</span> rows are <em>not</em> priced in.
No claim is made here about the current status of any pending bill beyond what the cited official page states.</p>''')}

{section("The list", laws_t)}

{section("Three things that would change the answer", f'''
<ol>
<li><b>A California wealth or holding tax.</b> It would be a recurring cost on ownership and would
strengthen the case for selling, because the sale converts a taxable holding into a smaller, movable one.</li>
<li><b>Any weakening of the step-up in basis.</b> The sell-early conclusion depends on a sale near the
date-of-death value producing no gain. If basis step-up were repealed, an immediate sale would carry a large
tax and the arithmetic would change substantially.</li>
<li><b>A sharp rise in long-run appreciation expectations.</b> Renting overtakes selling at about
{pct(D45['crossover_rent'],1)} a year, which is above the 2026 one-year reading but not far above the long-run
California trend. This is the most plausible way the recommendation flips.</li>
</ol>''')}
""", "laws-watch.html", "Enacted, scheduled and proposed rules affecting the inheritance decision."))

# =====================================================================
# FLAGGED
# =====================================================================
flags = [
    ["F-01", "Cash and other assets in the estate", "Not supplied. The federal estate test cannot be completed without it.", "Ask the trustee for a current inventory and total.", "High", ["IRS-ESTATE", "OWNER"]],
    ["F-02", "Prop 19 cap for 2027 and later", "Only the 16 Feb 2025 - 15 Feb 2027 amount ($1,044,586) is published. The amounts that will apply in 2040-2050 do not exist yet.", "Modelled as inflating at 3.0%; re-check the BOE announcement each biennium.", "Medium", ["BOE-CAP"]],
    ["F-03", "Property B tax history anomalies", "2018 tax rose 18.4% against a 2% assessment change; 2021 tax fell 5.9% against a 1% rise.", "Obtain the 2018 and 2021 bills and the rate history.", "Medium", ["OWNER"]],
    ["F-04", "Unidentified San Francisco charges", "The five named parcel taxes total $829; the owner's bill implies about $1,090.", "A current itemised tax bill would settle it.", "Low", ["SF-PARCEL", "SF-TTC"]],
    ["F-05", "Solar tariff vintage and term", "The net-metering term and interconnection date are unknown, so the credit's expiry cannot be dated.", "Request the interconnection agreement from the utility.", "Medium", ["CPUC-NEM"]],
    ["F-06", "Market rent for Property A", "No official rent figure exists for the property. The indicative figure is derived from the owner's own yield on Property B, not quoted.", "Two written rental appraisals in the inheritance year.", "High", ["OWNER", "COMPUTED"]],
    ["F-07", "Value of the freed San Francisco unit", "Credited at the average of the two let units; the third unit may differ in size or condition.", "A rental appraisal for that unit.", "Medium", ["OWNER"]],
    ["F-08", "Water provider and escalation for Property A", "Cupertino is not an SFPUC customer, so SFPUC steps are a proxy only.", "The utility bill of record, and the tariff schedule.", "Low", ["SFPUC"]],
    ["F-09", "1% Behavioral Health Services Tax", "The extra 1% above $1,000,000 of taxable income is documented in FTB's filing instructions, but the specific dollar threshold was read from a secondary summary in this review.", "Verify on the FTB 540 instructions before using the 13.3% top rate.", "Low", ["FTB-RATES"]],
    ["F-10", "Insurance premiums for both addresses", "Both are owner estimates. The CDI publishes a statewide average, not a quote, and coverage amounts are unknown.", "Two broker quotes per property, with the dwelling limit stated.", "High", ["CDI-SIS", "OWNER"]],
    ["F-11", "California treatment of Treasury interest", "The model assumes California does not tax interest on U.S. obligations, which is the conventional position but was not re-verified in this review.", "Confirm with the FTB instructions or a tax adviser.", "Low", ["TREASURY"]],
    ["F-12", "Rental expense and loss limitations", "Passive-activity loss limits, the 27.5-year mid-month convention detail, and state/federal AMT are not modelled.", "A tax projection for the inheritance year.", "Medium", ["IRS-P527"]],
    ["F-13", "Top federal estate tax rate", "The IRS estate tax page states the filing threshold but not the rate schedule; the 40% top rate is therefore not quoted anywhere on this site.", "Form 706 instructions.", "Low", ["IRS-ESTATE"]],
    ["F-14", "Retirement accounts in the inheritance", "If any of the inherited money is pre-tax retirement savings, it is taxed as income to the beneficiary on a compressed schedule. That is outside this model and would change the after-tax comparison.", "Confirm the asset composition.", "High", ["IRS-ESTATE"]],
    ["F-15", "Market values for both houses", "Both are owner estimates, not appraisals or public records.", "Date-of-death appraisal; the assessor's notice is the second opinion.", "High", ["OWNER", "SCC-ASSESSOR"]],
]
flags_t = table(["ID", "Item", "Why it is flagged", "What would settle it", "Impact", "Source"],
                [[f[0], f"<b>{f[1]}</b>", f[2], f[3],
                  f'<span class="tag {"gap" if f[4] == "High" else ("unv" if f[4] == "Medium" else "asm")}">{f[4]}</span>',
                  f[5]] for f in flags])

PAGES.append(("flagged-for-review.html", "Flagged for review", f"""
<h1>Flagged for review</h1>
<p class="lede">Everything on this site that is not verified against an official source, is an assumption, or
is simply missing. Nothing here has been quietly filled in.</p>

{callout("warn", "The rule applied", '''<p>A value that could not be confirmed from an official source was left
blank and listed here. Where a computation needed a number that does not exist, the assumption is printed next
to the result rather than buried. Four items carry High impact: the estate's cash (F-01), the market rent for
Property A (F-06), insurance (F-10), and whether any of the inheritance is pre-tax retirement money (F-14).</p>''')}

{section("The register", flags_t,
         sub="Impact means: how much the conclusion could move if the item resolved differently.")}

{section("What is verified, and how", table(
    ["Claim", "How it was verified", "Source"],
    [
        ["2026 federal exclusion is $15,000,000", "Read on the IRS estate tax page's filing-threshold table.", ["IRS-ESTATE"]],
        ["2027 exclusion is $15,480,000", "Read in IRS news release IR-2026-133.", ["IRS-2027"]],
        ["California imposes no inheritance or estate tax", "Read the statutory text of Revenue and Taxation Code 13301.", ["RTC-13301"]],
        ["Prop 19 protects only a principal residence, capped", "Read the BOE's comparison charts and its 2025 adjustment release.", ["BOE-P19", "BOE-CAP"]],
        ["Santa Clara typical rate is $1.1488 per $100", "Read in the Assessor's 2026 booklet, with a worked example.", ["SCC-ASSESSOR"]],
        ["San Francisco rate is 1.18162182% for FY2026-27", "Read on the Tax Collector's secured property tax page.", ["SF-TTC"]],
        ["San Francisco parcel taxes total $829 for three units", "Summed the five named charges on the Tax Collector's page.", ["SF-PARCEL"]],
        ["10-year Treasury yielded 4.88% on 9 Nov 2026", "Read the Treasury's daily par yield curve for November 2026.", ["TREASURY"]],
        ["CPI was 3.7% over the year to September 2026", "Read the BLS CPI news release.", ["BLS-CPI"]],
        ["The model reproduces both 2025 tax bills", "Recomputed each bill from the official rate and the assessed value; see the reconciliation table.", ["COMPUTED"]],
    ]))}
""", "flagged-for-review.html", "Unverified values, assumptions and gaps, with what would resolve each one."))


# =====================================================================
# SOURCES
# =====================================================================
def ledger_rows():
    rows = []
    for key, s in SOURCES.items():
        status = {"VERIFIED": '<span class="tag ver">VERIFIED</span>',
                  "OFFICIAL-DATA": '<span class="tag ver">OFFICIAL DATA</span>',
                  "NOT-VERIFIABLE": '<span class="tag unv">OWNER</span>',
                  "COMPUTED": '<span class="tag asm">COMPUTED</span>'}.get(s["status"], esc(s["status"]))
        rows.append([f"<code>{key}</code>", s["title"], s["publisher"], status, s["supports"],
                     f'<a href="{s["url"]}">{s["url"]}</a>'])
    return rows


ledger = table(["Key", "Document", "Publisher", "Status", "What it supports here", "Link"],
               ledger_rows(), cls="ledger",
               note="Every link was opened during the review on 10 November 2026. A link existing is not a claim that "
                    "the page will say the same thing later; government pages are revised.")

PAGES.append(("sources.html", "Source library", f"""
<h1>Source library</h1>
<p class="lede">Twenty-four official references and two internal categories. Each one says exactly what it was
used for, so any figure can be checked in one click.</p>

{section("The ledger", ledger)}

<section id="owner-inputs">
  <h2>Owner-supplied figures</h2>
  <p>These come from you and are not verified against a public record: both market values, both roll histories,
  both tax bills, the rent roll, the utility ranges and both insurance estimates. They are used as given,
  rounded to the nearest $10 for display, and are marked <span class="tag unv">UNVERIFIED</span> wherever they appear.</p>
</section>

<section id="computed">
  <h2>Computed by this project</h2>
  <p>Everything in the model that is arithmetic rather than published: the residual flat charges, the assessed-value
  and tax projections, the running-cost projections, the after-tax decision comparison, the break-even rent and the
  attribution of the estate headroom. The code is <code>scripts/model.py</code> and the outputs are the CSV files in
  <code>data/</code>. Every assumption used is printed on the <a href="projections.html">projections</a> page.</p>
</section>

{section("How verification was done", f'''
<ul>
<li>Each official page was opened and read for the specific sentence or table relied on, on 10 November 2026.</li>
<li>Where a page published a worked example (Santa Clara's $1,000,000 illustration), the model's formula was
checked against it.</li>
<li>Both owner-supplied 2025 bills were reproduced from the official rate and the assessed value to within a few
dollars before any forward projection was run.</li>
<li>Where an official page did not publish a number, the number was left blank and flagged &mdash; never filled in
from a listing site, a news article or a comparable sale.</li>
<li>Two secondary sources are used only to corroborate, and are named as such: the FTB bill analyses for the
wealth-tax discussion, and the FHFA series served through the Federal Reserve Bank of St. Louis.</li>
</ul>''')}

{callout("warn", "Scope limit", '''<p>This is a documented review of the specific rules the decision turns on. It is
not a legal opinion, and it is not a line-by-line verification of the Revenue and Taxation Code. Statutes and
county rates change; re-run the check before relying on any figure in 2040.</p>''')}
""", "sources.html", "Every official source used, with the scope of what it supports."))

# =====================================================================
# PRIVACY
# =====================================================================
PAGES.append(("privacy.html", "Privacy", f"""
<h1>Privacy</h1>
<p class="lede">You asked for personal information to be excluded from the published site and replaced with
placeholders. This page states exactly what that meant in practice, and where the line was drawn.</p>

{section("Withheld from every page", table(
    ["Category", "Treatment", "Why"],
    [
        ["Names of any person", "Removed and never reproduced. Roles only: transferor, trustee, beneficiary.", "Directly identifying"],
        ["Street addresses", "Removed. Property A and Property B only.", "Directly identifying a household"],
        ["Assessor's parcel numbers", "Removed.", "Identifies a single parcel"],
        ["ZIP codes", "Removed, including the two you supplied. City and county are kept.", "Coarse but combinable; the tax rates used are county-level, so the ZIP is not needed for any figure here."],
        ["Trust name, trust date, attorney, trustee institutions", "Removed.", "Identifies the estate"],
        ["Account, loan and policy numbers", "Never collected and never published.", "Directly identifying"],
        ["Occupancy, tenancy and household details beyond unit counts", "Reduced to unit counts and a rent roll total.", "Indirectly identifying"],
    ], cls="policy"))}

{section("Published, on purpose", f'''
<p>The financial figures you supplied &mdash; two market values, both roll histories, both tax bills, the rent roll,
the utility ranges and the insurance estimates &mdash; are published. They are what makes the analysis
checkable, and without them the site would be the empty framework it should not be. They are also published
with the identifiers stripped, and every one of them is labelled
<span class="tag unv">UNVERIFIED</span> because none came from a public record.</p>
<p>If you would rather the figures were not public either, that is a single-point change: the model reads its
inputs from <code>scripts/model.py</code>, and the pages can be regenerated with the amounts suppressed while
keeping every rule and every projection method.</p>
''')}

{section("How the site itself behaves", table(
    ["Property", "Status"],
    [
        ["Analytics, trackers, pixels", "None."],
        ["Cookies or local storage", "None."],
        ["Forms or data collection of any kind", "None."],
        ["Third-party scripts, fonts or images", "None; one local stylesheet and one local script for the mobile menu."],
        ["Outbound links", "Ordinary links with <code>rel='noopener noreferrer'</code> and a no-referrer policy."],
        ["Hosting", "GitHub Pages, which necessarily logs requests as any web server does."],
    ], cls="policy"))}

{section("One honest caveat about history", '''
<p>This repository was built by several automated sessions before this one. Earlier versions of the site were
published from the repository root at various points, and Git history is public. Those earlier versions did not
contain names, addresses or parcel numbers, but some did contain the two ZIP codes and property figures. Removing
a file from the latest commit does not remove it from history, and this project has not rewritten history. If
complete removal matters, that is a separate, deliberate operation on the repository itself.</p>
''')}
""", "privacy.html", "What personal information was withheld from the published site and why."))
