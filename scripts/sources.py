"""Single source of truth for the source ledger.

Every URL in this file was opened and read during this review (2026-11-10).
`status` is one of:
  VERIFIED      - the exact figure/text was read on the page
  OFFICIAL-DATA - official publisher, machine series read through a mirror
  SCOPE         - page read, but it does not itself publish the number cited
Flags and gaps live on the Flagged for Review page.
"""

SOURCES = {
    "IRS-ESTATE": dict(
        title="IRS — Estate tax (filing threshold table)",
        url="https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="2026 filing threshold $15,000,000; estate tax is a tax on the right to "
                 "transfer property at death (paid by the estate, not the heir).",
    ),
    "IRS-2027": dict(
        title="IRS IR-2026-133 — 2027 inflation adjustments (Rev. Proc. 2026-35)",
        url="https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="2027 basic exclusion $15,480,000; 2027 annual gift exclusion $20,000; "
                 "absolute amounts are indexed annually from 2027.",
    ),
    "IRS-BASIS": dict(
        title="IRS FAQ — gifts & inheritances (basis of inherited property)",
        url="https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances/gifts-inheritances",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="Basis of inherited property is generally fair market value at date of death "
                 "(step-up); gain above that basis is taxable on sale.",
    ),
    "IRS-T409": dict(
        title="IRS Topic 409 — capital gains and losses",
        url="https://www.irs.gov/taxtopics/tc409",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="Long-term capital gain rates 0/15/20%; unrecaptured section 1250 gain "
                 "maximum 25%; net investment income tax reference.",
    ),
    "IRS-T701": dict(
        title="IRS Topic 701 — sale of your home",
        url="https://www.irs.gov/taxtopics/tc701",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="Section 121 exclusion of up to $250,000 ($500,000 joint) with 2-of-5-year "
                 "ownership and use tests.",
    ),
    "IRS-P527": dict(
        title="IRS Publication 527 — residential rental property",
        url="https://www.irs.gov/publications/p527",
        publisher="Internal Revenue Service",
        status="VERIFIED",
        supports="Residential rental building depreciated straight-line over 27.5 years (GDS); "
                 "land is not depreciable.",
    ),
    "BOE-P19": dict(
        title="BOE — Proposition 19 (comparison charts, filing periods, RTC 63.2/69.6)",
        url="https://www.boe.ca.gov/prop19/",
        publisher="California State Board of Equalization",
        status="VERIFIED",
        supports="Parent-child exclusion limited to a principal residence of BOTH transferor and "
                 "transferee, capped at taxable value plus an adjusted $1,000,000; exclusion for "
                 "other real property eliminated; claim within 3 years, homeowners' exemption "
                 "within 1 year.",
    ),
    "BOE-CAP": dict(
        title="BOE NR 25-02 — 2025 Proposition 19 exclusion adjustment",
        url="https://www.boe.ca.gov/news/2025/NR-25-02.htm",
        publisher="California State Board of Equalization",
        status="VERIFIED",
        supports="Excludable amount for transfers from 16 Feb 2025 through 15 Feb 2027 is "
                 "factored base year value plus $1,044,586 (adjusted every two years).",
    ),
    "SCC-ASSESSOR": dict(
        title="Santa Clara County Assessor — 2026 Assessment Information booklet",
        url="https://files.santaclaracounty.gov/exjcpb1521/2026-04/assessment-information-2026-booklet-english-3-23-26-web.pdf",
        publisher="Office of the Assessor, County of Santa Clara",
        status="VERIFIED",
        supports="Typical tax rate area = $1.1488 per $100 of assessed value (1% base + county, "
                 "school and water bonds); homeowners' exemption $7,000; inheritance from an "
                 "estate or living trust is reassessed as of the date of death, not distribution; "
                 "supplemental assessment mechanics.",
    ),
    "SF-TTC": dict(
        title="SF Treasurer & Tax Collector — Secured property taxes",
        url="https://sftreasurer.org/property/secured-property-taxes",
        publisher="City and County of San Francisco",
        status="VERIFIED",
        supports="Secured property tax rate for fiscal year 2026-27 is 1.18162182%; reassessment "
                 "and supplemental/escape assessment mechanics after a change in ownership.",
    ),
    "SF-PARCEL": dict(
        title="SF Treasurer & Tax Collector — parcel taxes and special assessments",
        url="https://sftreasurer.org/property/parcel-tax-exemptions-and-special-assessments",
        publisher="City and County of San Francisco",
        status="VERIFIED",
        supports="FY2025-26 parcel charges: School Parcel Tax of 2020 $334.38; SFUSD Facilities "
                 "District $43.00 per single-family parcel and $21.50 per dwelling unit on "
                 "multi-family parcels; SFUSD Teacher Support $319.34; CCSF Parcel Tax $99; "
                 "Bay Restoration Authority $12 (all inflation-adjusted annually).",
    ),
    "SF-RENT": dict(
        title="SF Rent Board — allowable annual rent increase",
        url="https://www.sf.gov/departments--rent-board",
        publisher="City and County of San Francisco, Rent Board",
        status="VERIFIED",
        supports="Allowable rent increase for covered units is 1.6% for increases effective "
                 "1 Mar 2026 through 28 Feb 2027 (Rent Ordinance sec. 37.3(a)(1)).",
    ),
    "SFPUC": dict(
        title="SFPUC — proposed water and sewer rate adjustments (Rate Fairness Board)",
        url="https://www.sfpuc.gov/sites/default/files/agendas-minutes-rate-fairness-board/6a-Rates-Presentation.pdf",
        publisher="San Francisco Public Utilities Commission",
        status="VERIFIED",
        supports="Water +7.0% effective 1 Jul 2026 and +7.0% 1 Jul 2027; sewer +15.0% and +14.5%; "
                 "average single-family combined monthly bill $189 (FY2027) and $212 (FY2028).",
    ),
    "CPUC-NEM": dict(
        title="CPUC — customer-sited renewable generation / net billing tariff",
        url="https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/demand-side-management/net-energy-metering",
        publisher="California Public Utilities Commission",
        status="VERIFIED",
        supports="Net energy metering tariffs are closed to new enrollments; interconnections from "
                 "15 Apr 2023 take the net billing tariff under D.22-12-056, which pays export "
                 "credits at avoided-cost value rather than retail rate.",
    ),
    "CDI-SIS": dict(
        title="CDI — Sustainable Insurance Strategy market snapshot",
        url="https://www.insurance.ca.gov/01-consumers/180-climate-change/sustainable-insurance-strategy.Cfm",
        publisher="California Department of Insurance",
        status="VERIFIED",
        supports="Average California homeowner premium $1,571 vs national $1,512 (NAIC data); "
                 "8,300,730 homeowner policies; 677,449 FAIR Plan residential policies.",
    ),
    "CDI-2026": dict(
        title="CDI — 2026 market alert (rate filings and FAIR Plan growth)",
        url="https://www.insurance.ca.gov/0400-news/0102-alerts/2026/Momentum-continues-to-build-under-Insura.cfm",
        publisher="California Department of Insurance",
        status="VERIFIED",
        supports="Insurers covering about one-third of California homes sought increases of about "
                 "6.9%; FAIR Plan added about 16,000 residential policies in Q1 2026 (2.4%).",
    ),
    "RTC-13301": dict(
        title="California Revenue & Taxation Code sec. 13301",
        url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=13301",
        publisher="California Legislative Information",
        status="VERIFIED",
        supports="Neither the state nor any political subdivision may impose any gift, "
                 "inheritance, succession, legacy, income, or estate tax on gifts or on an "
                 "estate or inheritance, or on any transfer by reason of death.",
    ),
    "RTC-51": dict(
        title="California Revenue & Taxation Code sec. 51 (Prop 13 taxable value)",
        url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=51",
        publisher="California Legislative Information",
        status="VERIFIED",
        supports="Taxable value is the lesser of factored base year value or full cash value; the "
                 "annual inflation factor may not exceed 2 percent.",
    ),
    "RTC-480": dict(
        title="California Revenue & Taxation Code sec. 480 (change in ownership statement)",
        url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=480",
        publisher="California Legislative Information",
        status="VERIFIED",
        supports="For a transfer by reason of death through a trust, the trustee must file a change "
                 "in ownership statement within 150 days after the date of death; penalty for "
                 "failure to file on request is the greater of $100 or 10% of the new tax, capped "
                 "at $5,000.",
    ),
    "PROB-16061": dict(
        title="California Probate Code sec. 16061.7 (notification by trustee)",
        url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PROB&sectionNum=16061.7",
        publisher="California Legislative Information",
        status="VERIFIED",
        supports="Trustee must serve the notification by trustee on each beneficiary and heir no "
                 "later than 60 days after the event (death) that makes the trust irrevocable.",
    ),
    "FTB-RATES": dict(
        title="FTB — 2025 California tax rate schedules",
        url="https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf",
        publisher="California Franchise Tax Board",
        status="VERIFIED",
        supports="Marginal rates 1% to 12.3%; Schedule X top bracket above $742,953. A separate "
                 "1% Behavioral Health Services Tax applies above $1,000,000 (see flag F-09).",
    ),
    "TREASURY": dict(
        title="U.S. Treasury — daily par yield curve, November 2026",
        url="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202611",
        publisher="U.S. Department of the Treasury",
        status="VERIFIED",
        supports="10-year constant-maturity par yield 4.88% on 9 Nov 2026 (4.84% on 5 Nov 2026).",
    ),
    "BLS-CPI": dict(
        title="BLS — CPI summary, September 2026",
        url="https://www.bls.gov/news.release/cpi.nr0.htm",
        publisher="U.S. Bureau of Labor Statistics",
        status="VERIFIED",
        supports="CPI-U up 3.7% over the 12 months to September 2026; core 2.6%; electricity "
                 "4.4%; shelter 3.2%.",
    ),
    "OWNER": dict(
        title="Owner-supplied figures (internal note)",
        url="sources.html#owner-inputs",
        publisher="This project",
        status="NOT-VERIFIABLE",
        supports="Figures the property owner supplied and which no public record was retrieved for: "
                 "market values, roll history, rent roll, utility ranges and insurance estimates.",
    ),
    "COMPUTED": dict(
        title="Computed by this project's model (internal note)",
        url="sources.html#computed",
        publisher="This project",
        status="COMPUTED",
        supports="Arithmetic produced by scripts/model.py from the cited official rates and the "
                 "owner-supplied figures, not a published statistic.",
    ),
    "FHFA-HPI": dict(
        title="FHFA/FRED — All-Transactions House Price Index for California (CASTHPI)",
        url="https://fred.stlouisfed.org/series/CASTHPI",
        publisher="Federal Housing Finance Agency series served by the Federal Reserve Bank of St. Louis",
        status="OFFICIAL-DATA",
        supports="California all-transactions HPI change from a year earlier was +0.9% at 2026Q2 "
                 "(+1.8% at 2026Q1) — the short-run appreciation benchmark used here.",
    ),
}

# Values transcribed from the sources above (so the model has one place to read them).
V = {
    "scc_advalorem": 0.011488,     # SCC-ASSESSOR typical tax rate area, per $100 = $1.1488
    "scc_ho_exempt": 7000,         # SCC-ASSESSOR homeowners' exemption
    "sf_advalorem": 0.0118162182,  # SF-TTC FY2026-27 secured rate
    "prop13_cap": 0.02,            # RTC-51
    "prop19_cap_2025": 1044586,    # BOE-CAP (16 Feb 2025 - 15 Feb 2027)
    "fed_excl_2026": 15000000,     # IRS-ESTATE
    "fed_excl_2027": 15480000,     # IRS-2027
    "fed_gift_2026": 19000,        # IRS-2027 (prior year amount stated in release)
    "ca_top_bracket": 0.123,       # FTB-RATES Schedule X top marginal
    "ca_behavioral_health": 0.01,  # FTB-RATES / flag F-09
    "fed_ltcg_top": 0.20,          # IRS-T409
    "niit": 0.038,                 # IRS-T409
    "unrecaptured_1250": 0.25,     # IRS-T409
    "sec121_single": 250000,       # IRS-T701
    "sec121_joint": 500000,        # IRS-T701
    "depr_years": 27.5,            # IRS-P527
    "treasury_10y": 0.0488,        # TREASURY (9 Nov 2026)
    "cpi_latest": 0.037,           # BLS-CPI
    "cpi_core": 0.026,             # BLS-CPI
    "electricity_cpi": 0.044,      # BLS-CPI
    "sf_rent_cap_2026": 0.016,     # SF-RENT
    "sf_parcel_2025": 829.22,      # SF-PARCEL (334.38 + 3x21.50 + 319.34 + 99 + 12)
    "sf_parcel_unit": 21.50,       # SF-PARCEL SFUSD facilities district, per unit
    "cdi_avg_premium": 1571,       # CDI-SIS
    "cdi_recent_filings": 0.069,   # CDI-2026
    "sfpuc_water_fy27": 0.07,      # SFPUC
    "fhfa_ca_1y": 0.009,           # FHFA-HPI
}
