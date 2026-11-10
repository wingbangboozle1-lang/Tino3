"""Rendering helpers and the official-source ledger for the published pages."""
from __future__ import annotations

import html

RETRIEVED = "2026-11-10"

# id: (publisher, title, url, how this session checked it)
READ = "Page read by this session"
EXCERPT = "Official page text read through a search excerpt"
LINK_ONLY = "Official starting point for manual review; this session could not read the value there"

SOURCES = {
    "IRS-ESTATE": ("Internal Revenue Service", "Estate tax (filing thresholds by year of death)", "https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax", READ),
    "IRS-NEW": ("Internal Revenue Service", "What's new: estate and gift tax", "https://www.irs.gov/businesses/small-businesses-self-employed/whats-new-estate-and-gift-tax", READ),
    "IRS-706": ("Internal Revenue Service", "Instructions for Form 706 (Rev. July 2026)", "https://www.irs.gov/pub/irs-pdf/i706.pdf", READ),
    "IRS-IR133": ("Internal Revenue Service", "IR-2026-133: inflation adjustments for tax year 2027", "https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts", READ),
    "IRS-RP2635": ("Internal Revenue Service", "Revenue Procedure 2026-35", "https://www.irs.gov/pub/irs-drop/rp-26-35.pdf", READ),
    "IRS-INHERIT": ("Internal Revenue Service", "FAQ: is money from the sale of inherited property taxable?", "https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances/gifts-inheritances", READ),
    "IRS-P551": ("Internal Revenue Service", "Publication 551, Basis of Assets", "https://www.irs.gov/publications/p551", READ),
    "IRS-T409": ("Internal Revenue Service", "Topic no. 409, Capital gains and losses", "https://www.irs.gov/taxtopics/tc409", READ),
    "IRS-T701": ("Internal Revenue Service", "Topic no. 701, Sale of your home", "https://www.irs.gov/taxtopics/tc701", READ),
    "IRS-T559": ("Internal Revenue Service", "Topic no. 559, Net investment income tax", "https://www.irs.gov/taxtopics/tc559", READ),
    "IRS-T414": ("Internal Revenue Service", "Topic no. 414, Rental income and expenses", "https://www.irs.gov/taxtopics/tc414", READ),
    "IRS-P527": ("Internal Revenue Service", "Publication 527, Residential Rental Property", "https://www.irs.gov/pub/irs-pdf/p527.pdf", EXCERPT),
    "IRS-RR232": ("Internal Revenue Service", "Revenue Ruling 2023-2 (Internal Revenue Bulletin 2023-16)", "https://www.irs.gov/irb/2023-16_IRB", EXCERPT),
    "IRS-1041": ("Internal Revenue Service", "Instructions for Form 1041", "https://www.irs.gov/instructions/i1041", EXCERPT),
    "IRS-OBBB": ("Internal Revenue Service", "One, Big, Beautiful Bill provisions", "https://www.irs.gov/obbb", LINK_ONLY),
    "BOE-P19": ("California State Board of Equalization", "Proposition 19: charts, FAQs, filing checklist", "https://www.boe.ca.gov/prop19/", READ),
    "BOE-LTA2509": ("California State Board of Equalization", "Letter to Assessors 2025/009: adjustment of the $1 million amount", "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf", READ),
    "BOE-LTA2626": ("California State Board of Equalization", "Letter to Assessors 2026/026: intergenerational transfer exclusion Q&A", "https://www.boe.ca.gov/proptaxes/pdf/lta26026.pdf", READ),
    "BOE-LTA2602": ("California State Board of Equalization", "Letter to Assessors 2026/002: 2026-27 inflation factor and history", "https://boe.ca.gov/proptaxes/pdf/lta26002.pdf", READ),
    "BOE-HOX": ("California State Board of Equalization", "Homeowners' Exemption", "https://www.boe.ca.gov/proptaxes/homeowners_exemption.htm", EXCERPT),
    "CA-RTC480": ("California Legislative Information", "Revenue and Taxation Code section 480", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=480", READ),
    "CA-PROB16061": ("California Legislative Information", "Probate Code section 16061.7", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PROB&sectionNum=16061.7", READ),
    "CA-RTC13301": ("California Legislative Information", "Revenue and Taxation Code section 13301", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=13301", EXCERPT),
    "CA-AB942": ("California Legislative Information", "AB 942 (2025-2026) bill status", "https://leginfo.legislature.ca.gov/faces/billStatusClient.xhtml?bill_id=202520260AB942", READ),
    "SCO-ESTATE": ("California State Controller", "California Estate Tax", "https://www.sco.ca.gov/ardtax_estate_tax.html", READ),
    "FTB-CG": ("California Franchise Tax Board", "Capital gains and losses", "https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html", READ),
    "FTB-RATES": ("California Franchise Tax Board", "2025 California Tax Rate Schedules", "https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf", READ),
    "FTB-541": ("California Franchise Tax Board", "Form 541 fiduciary income tax booklet (2019 edition)", "https://www.ftb.ca.gov/forms/2019/2019-541-booklet.html", EXCERPT),
    "CPUC-NEM": ("California Public Utilities Commission", "Net Energy Metering and Net Billing", "https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/demand-side-management/customer-generation/net-energy-metering-and-net-billing", READ),
    "SOS-FAIL": ("California Secretary of State", "CC/ROV memorandum 26138: initiative 1994 failed to qualify", "https://elections.cdn.sos.ca.gov/ccrov/2026/may/26138jh.pdf", READ),
    "SOS-RESULTS": ("California Secretary of State", "State ballot measures: unofficial results, 3 November 2026 election", "https://electionresults.sos.ca.gov/returns/ballot-measures", READ),
    "SOS-P3": ("California Secretary of State", "Official Voter Information Guide: Proposition 3", "https://voterguide.sos.ca.gov/propositions/3/", READ),
    "SOS-P42": ("California Secretary of State", "Official Voter Information Guide: Proposition 42", "https://voterguide.sos.ca.gov/propositions/42/", READ),
    "LAO-250017": ("California Legislative Analyst's Office", "Analysis of initiative A.G. File No. 25-0017", "https://lao.ca.gov/BallotAnalysis/Initiative/2025-017", EXCERPT),
    "SF-TAX": ("San Francisco Treasurer and Tax Collector", "Secured Property Taxes", "https://sftreasurer.org/property/secured-property-taxes", READ),
    "SF-FEES": ("San Francisco Assessor-Recorder", "Fees to record a document; transfer tax rates", "https://www.sf.gov/reports--march-2024--fees-record-document-san-francisco", READ),
    "SF-RENT": ("San Francisco Rent Board", "Current rates, including the allowable rent increase", "https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit", EXCERPT),
    "SF-EHT": ("San Francisco Treasurer and Tax Collector", "Empty Homes Tax", "https://sftreasurer.org/business/taxes-fees/empty-homes-tax-eht", EXCERPT),
    "SF-HEIRS": ("San Francisco Treasurer and Tax Collector", "Information for Heirs", "https://sftreasurer.org/property/information-heirs", LINK_ONLY),
    "SCC-DTT": ("Santa Clara County Clerk-Recorder", "Recording real estate: documentary transfer tax", "https://clerkrecorder.santaclaracounty.gov/recording-documents/recording-real-estate", EXCERPT),
    "CDI-TOOL": ("California Department of Insurance", "Homeowners Insurance Comparison Tool (2026)", "https://interactive.web.insurance.ca.gov/apex_extprd/f?p=111:20", READ),
    "CDI-DATA": ("California Department of Insurance", "Data and analysis on wildfires and insurance", "https://www.insurance.ca.gov/01-consumers/200-wrr/DataAnalysisOnWildfiresAndInsurance.cfm", READ),
    "NAIC-HO": ("National Association of Insurance Commissioners", "Homeowners report: data for 2023", "https://content.naic.org/sites/default/files/publication-hmr-zu-homeowners-report.pdf", READ),
    "FHFA-HPI": ("Federal Housing Finance Agency", "House Price Index quarterly report, 2026 second quarter", "https://www.fhfa.gov/document/d/hpi/fhfa-house-price-index-report-2026q2", READ),
    "UST-YIELD": ("U.S. Department of the Treasury", "Daily Treasury par yield curve rates, November 2026", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202611", READ),
    "SSA-TR": ("Social Security Administration", "2026 Trustees Report: long-range sensitivity analysis", "https://www.ssa.gov/oact/TR/2026/VI_D_LRsens.html", EXCERPT),
    "TSP-RET": ("Federal Retirement Thrift Investment Board", "Thrift Savings Plan rates of return", "https://www.tsp.gov/fund-performance/", READ),
    "HUD-FMR": ("U.S. Department of Housing and Urban Development", "Fair Market Rents", "https://www.huduser.gov/portal/datasets/fmr.html", LINK_ONLY),
    "CONG-S587": ("Congress.gov", "S.587, Death Tax Repeal Act of 2025", "https://www.congress.gov/bill/119th-congress/senate-bill/587", EXCERPT),
    "CONG-HR1301": ("Congress.gov", "H.R.1301, Death Tax Repeal Act", "https://www.congress.gov/bill/119th-congress/house-bill/1301", EXCERPT),
    "CRT-SELF": ("Judicial Branch of California", "Self-help guide: wills, estates and living trusts", "https://selfhelp.courts.ca.gov/wills-estates-probate/legal-documents", EXCERPT),
    "GH-REPO": ("GitHub", "This repository's pull requests and history", "https://github.com/wingbangboozle1-lang/Tino3/pulls", "Repository record read through the GitHub API"),
    "CRT-SCC": ("Superior Court of California, County of Santa Clara", "Living trusts", "https://santaclara.courts.ca.gov/self-help/self-help-probate/self-help-probate-medicalfinancialend-life-issues/living-trusts", EXCERPT),
}

OFFICIAL_DOMAINS = (
    "irs.gov", "boe.ca.gov", "leginfo.legislature.ca.gov", "sco.ca.gov", "ftb.ca.gov", "cpuc.ca.gov",
    "sos.ca.gov", "lao.ca.gov", "sf.gov", "sftreasurer.org", "santaclaracounty.gov", "insurance.ca.gov",
    "naic.org", "fhfa.gov", "treasury.gov", "ssa.gov", "tsp.gov", "huduser.gov", "congress.gov",
    "courts.ca.gov", "github.com",
)

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("decision.html", "Live, rent or sell"),
    ("projections.html", "Year-by-year projections"),
    ("property-a.html", "Property A"),
    ("property-b.html", "Property B"),
    ("insurance.html", "Insurance"),
    ("taxes.html", "Tax thresholds"),
    ("law-changes.html", "Law changes"),
    ("inheritance.html", "Trust process"),
    ("review.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("method.html", "Method and privacy"),
]

STATUS = {
    "verified": ("Verified", "Checked against the linked official source."),
    "owner": ("Owner-supplied", "From the owner's brief. The link shows where it can be confirmed; nobody has confirmed it."),
    "assumption": ("Assumption", "A planning assumption. The link is the official figure it leans on."),
    "model": ("Model output", "Calculated. The link is the official rule the calculation applies."),
    "unverified": ("Unverified", "No official figure could be confirmed. Left blank and listed on Flagged for Review."),
}


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def money(x) -> str:
    if x is None:
        return "—"
    return ("−$" if x < 0 else "$") + f"{abs(x):,.0f}"


def pct(x, digits=1) -> str:
    return f"{x * 100:.{digits}f}%"


def src(*ids) -> str:
    out = []
    for i in ids:
        pub, title, url, _ = SOURCES[i]
        out.append(f'<a class="src" href="{esc(url)}" rel="noopener" title="{esc(pub)}: {esc(title)}">{esc(i)}</a>')
    return " ".join(out)


def chip(status: str) -> str:
    label, tip = STATUS[status]
    return f'<span class="chip chip-{status}" title="{esc(tip)}">{label}</span>'


def table(headers, rows, caption=None, cls="") -> str:
    """rows: (cells, status, [source ids]) or (cells, status, [source ids], flag_id)."""
    h = "".join(f"<th scope=\"col\">{esc(x)}</th>" for x in list(headers) + ["Status", "Official source"])
    body = []
    for row in rows:
        cells, status, ids = row[0], row[1], row[2]
        flag = row[3] if len(row) > 3 else None
        tds = "".join(f"<td>{c}</td>" for c in cells)
        flag_link = f' <a class="flag" href="review.html#{flag}">{flag}</a>' if flag else ""
        body.append(f'<tr data-status="{status}">{tds}<td>{chip(status)}{flag_link}</td><td>{src(*ids)}</td></tr>')
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<div class="tw"><table class="{cls}">{cap}<thead><tr>{h}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def cards(items) -> str:
    return '<div class="cards">' + "".join(
        f'<div class="card"><p class="k">{esc(k)}</p><p class="v">{v}</p><p class="n">{n}</p></div>' for k, v, n in items) + "</div>"


def page(slug: str, title: str, lead: str, body: str) -> str:
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{current if href == slug else ""}>{esc(label)}</a>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{esc(title)} · Inherited property plan</title>
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<a class="brand" href="index.html">Inherited property plan</a>
<p class="tag">Property A and Property B · placeholders only · every amount in $10 steps</p>
</header>
<div class="shell">
<nav class="side" aria-label="Sections">{nav}</nav>
<main id="main">
<h1>{esc(title)}</h1>
<p class="lead">{lead}</p>
{body}
<footer>
<p>Reviewed {RETRIEVED}. General information for planning, not legal, tax or investment advice. Confirm every step with a California estate attorney and a tax adviser before acting.</p>
<p>Status labels: {" ".join(chip(s) for s in STATUS)}. Hover a label for its meaning. Source codes link to the official page; the full list is on <a href="sources.html">Sources</a>.</p>
</footer>
</main>
</div>
<script src="assets/site.js"></script>
</body>
</html>
"""


CSS = """
:root{--ink:#17202a;--mute:#5d6b7a;--line:#dfe5ec;--bg:#f5f7fa;--card:#fff;--brand:#0b5c8a;--ok:#1d7a46;--warn:#9a5b00;--bad:#a4262c;--own:#5b4bb5;--mod:#33566f}
*{box-sizing:border-box}html{font-size:16px}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}
a{color:var(--brand)}.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
.top{background:#fff;border-bottom:1px solid var(--line);padding:14px 24px;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
.brand{font-weight:700;font-size:1.1rem;text-decoration:none;color:var(--ink)}.tag{margin:0;color:var(--mute);font-size:.85rem}
.shell{display:grid;grid-template-columns:220px minmax(0,1fr);gap:24px;max-width:1280px;margin:0 auto;padding:24px}
.side{display:flex;flex-direction:column;gap:2px;position:sticky;top:16px;align-self:start}
.side a{padding:8px 12px;border-radius:8px;text-decoration:none;color:var(--ink);font-size:.93rem}
.side a:hover{background:#e8eef4}.side a[aria-current]{background:var(--brand);color:#fff}
main{min-width:0}h1{font-size:1.9rem;margin:.1em 0 .2em}h2{font-size:1.25rem;margin:1.8em 0 .5em}h3{font-size:1.02rem;margin:1.3em 0 .4em}
.lead{font-size:1.06rem;color:var(--mute);max-width:70ch;margin-top:0}p,li{max-width:80ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .k{margin:0;color:var(--mute);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
.card .v{margin:.15em 0;font-size:1.45rem;font-weight:700}.card .n{margin:0;color:var(--mute);font-size:.86rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:16px 0}
.tile{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--ink)}
.tile:hover{border-color:var(--brand)}.tile b{display:block;color:var(--brand)}.tile span{color:var(--mute);font-size:.88rem}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.9rem}caption{text-align:left;padding:10px 12px;font-weight:600}
th,td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{background:#eef2f6;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;color:var(--mute);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}td.num,table.nums td:not(:first-child):not(:nth-last-child(-n+2)){text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.74rem;font-weight:600;white-space:nowrap;border:1px solid}
.chip-verified{color:var(--ok);border-color:var(--ok);background:#eaf6ef}.chip-owner{color:var(--own);border-color:var(--own);background:#f0eefb}
.chip-assumption{color:var(--warn);border-color:var(--warn);background:#fdf3e2}.chip-model{color:var(--mod);border-color:var(--mod);background:#eaf1f6}
.chip-unverified{color:var(--bad);border-color:var(--bad);background:#fbecec}
.src{display:inline-block;font-size:.76rem;font-family:ui-monospace,Menlo,Consolas,monospace;margin:0 4px 2px 0;white-space:nowrap}
.flag{font-size:.76rem;font-weight:700;color:var(--bad);margin-left:4px}
.note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--brand);border-radius:8px;padding:10px 14px;margin:14px 0;max-width:86ch}
.note.warn{border-left-color:var(--warn)}.note.bad{border-left-color:var(--bad)}
.calc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;max-width:560px}
.calc label{display:block;font-size:.86rem;color:var(--mute);margin-top:8px}.calc input{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:8px;font-size:1rem}
.calc output{display:block;margin-top:10px;font-weight:700}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);color:var(--mute);font-size:.84rem}
@media(max-width:860px){.shell{grid-template-columns:1fr;padding:14px}.side{position:static;flex-direction:row;flex-wrap:wrap}.side a{padding:6px 10px}h1{font-size:1.5rem}}
@media print{.side,.skip{display:none}.shell{display:block}}
"""

JS = """
(function(){
  var f=document.getElementById('p19');if(!f)return;
  function n(id){return Math.max(0,parseFloat(document.getElementById(id).value)||0)}
  function r10(x){return Math.round(x/10)*10}
  function fmt(x){return '$'+r10(x).toLocaleString('en-US')}
  function go(){
    var mv=n('p19-mv'),bv=n('p19-bv'),add=n('p19-add'),rate=n('p19-rate')/100;
    var live=bv+Math.max(0,mv-(bv+add));
    document.getElementById('p19-out').innerHTML=
      'Taxable value if the heir lives there: '+fmt(live)+' (about '+fmt(live*rate)+' a year)<br>'+
      'Taxable value if nobody eligible lives there: '+fmt(mv)+' (about '+fmt(mv*rate)+' a year)<br>'+
      'Yearly difference: '+fmt((mv-live)*rate);
  }
  f.addEventListener('input',go);go();
})();
"""
