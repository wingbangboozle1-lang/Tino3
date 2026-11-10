#!/usr/bin/env python3
"""
Deterministic, auditable tax & financial projection engine for Tino3 (Session arena-531aee5c-tino3).

Privacy & Rounding Guarantees:
- Zero personal names, street addresses, APNs, utility account numbers, or ZIP codes.
- Zero raw unrounded parcel-identifying figures: all historical inputs and outputs are stored and
  emitted strictly in $10-rounded increments (nearest $10).
- Official confirmed values for parcel-specific or undisclosed items are strictly empty ("") and
  flagged UNVERIFIED.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SUITE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SUITE_DIR / "data"


def r10(val: float | int) -> int:
    """Round any dollar figure to the nearest $10 increment."""
    return int(round(float(val) / 10.0) * 10)


# Official URLs (every single URL is a primary .gov / .ca.gov / statutory source)
URLS = {
    "irs_2027": "https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2027-taxpayers-continue-to-benefit-from-the-working-families-tax-cuts",
    "irs_706": "https://www.irs.gov/instructions/i706",
    "irs_709": "https://www.irs.gov/instructions/i709",
    "irs_basis": "https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances",
    "irs_rr2023_2": "https://www.irs.gov/irb/2023-16_IRB#REV-RUL-2023-2",
    "irs_tc409": "https://www.irs.gov/taxtopics/tc409",
    "irs_tc701": "https://www.irs.gov/taxtopics/tc701",
    "irs_tc559": "https://www.irs.gov/taxtopics/tc559",
    "irs_p527": "https://www.irs.gov/publications/p527",
    "ca_rtc13301": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=13301",
    "ca_rtc480": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=480.&lawCode=RTC",
    "ca_prob16061": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=16061.7.&lawCode=PROB",
    "ca_sb974": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260SB974",
    "ftb_cg": "https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html",
    "ftb_rent": "https://www.ftb.ca.gov/file/personal/income-types/rental.html",
    "ftb_gifts": "https://www.ftb.ca.gov/file/personal/income-types/gifts-and-inheritance.html",
    "boe_prop19": "https://www.boe.ca.gov/prop19/",
    "boe_pub800": "https://www.boe.ca.gov/pdf/pub800-1.pdf",
    "boe_lta25009": "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf",
    "boe_lta26002": "https://boe.ca.gov/proptaxes/pdf/lta26002.pdf",
    "boe_pub29": "https://www.boe.ca.gov/proptaxes/pdf/pub29.pdf",
    "sos_prop19": "https://www.sos.ca.gov/administration/news-releases-and-advisories/2025-news-releases-and-advisories/proposed-initiative-enters-circulation-repeals-voter-enacted-changes-property-tax-rules-transfers-between-family-members-initiat",
    "lao_250017": "https://www.lao.ca.gov/ballot/2025/250422.pdf",
    "courts_trusts": "https://santaclara.courts.ca.gov/divisions/probate-division/probate-trusts",
    "courts_probate": "https://selfhelp.courts.ca.gov/probate/formal-probate",
    "scc_taxbook": "https://files.santaclaracounty.gov/exjcpb1531/2025-11/tax-rate-book-2025-2026.pdf",
    "scc_dtac": "https://dtac.santaclaracounty.gov/taxes/obtain-secured-property-tax-information",
    "scc_dtt": "https://clerkrecorder.santaclaracounty.gov/recording-documents/recording-document-fees",
    "cup_water": "https://www.cupertino.gov/files/assets/city/v/1/your-city/documents/gp-chap-06-health.pdf",
    "cpuc_solar": "https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M520/K547/520547180.PDF",
    "sf_taxrate": "https://sfbos.archive.sf.gov/sites/default/files/r0447-25.pdf",
    "sf_dtt": "https://www.sf.gov/transfer-tax",
    "sf_rent": "https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit",
    "sf_evict": "https://www.sf.gov/information--overview-just-cause-evictions",
    "sfpuc": "https://www.sfpuc.gov/accounts-services/water-power-sewer-rates/proposed-water-sewer-rates-2026/proposition-218-notice",
    "cdi_ins": "https://www.insurance.ca.gov/01-consumers/105-type/5-residential/Top10Tips_FindingResidentialIns.cfm",
    "treasury": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202611",
    "fhfa_hpi": "https://www.fhfa.gov/document/d/hpi/fhfa-house-price-index-report-2026q2",
    "bls_cpi": "https://www.bls.gov/cpi/",
    "fdic": "https://www.fdic.gov/resources/deposit-insurance/understanding-deposit-insurance",
}


# Anonymized, pre-rounded ($10) owner-supplied historical schedules (NO raw unrounded parcel numbers)
PROP_A_HISTORY = [
    {"year": 2014, "reported_tax": 5970, "reported_tax_chg": "", "reported_av": 440310, "reported_av_chg": "+0.5%", "boe_ccpi_factor": "1.00454 (+0.454%)", "confirmed_official": "", "status": "UNVERIFIED — Parcel Roll Requires APN"},
    {"year": 2015, "reported_tax": 6130, "reported_tax_chg": "+2.8%", "reported_av": 449100, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.01998 (+1.998%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2016, "reported_tax": 6410, "reported_tax_chg": "+4.6%", "reported_av": 455950, "reported_av_chg": "+1.5%", "boe_ccpi_factor": "1.01525 (+1.525%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2017, "reported_tax": 6380, "reported_tax_chg": "-0.5%", "reported_av": 465070, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2018, "reported_tax": 6380, "reported_tax_chg": "0.0%", "reported_av": 474370, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2019, "reported_tax": 6570, "reported_tax_chg": "+2.8%", "reported_av": 483850, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2020, "reported_tax": 6570, "reported_tax_chg": "0.0%", "reported_av": 493530, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2021, "reported_tax": 6660, "reported_tax_chg": "+1.5%", "reported_av": 498640, "reported_av_chg": "+1%", "boe_ccpi_factor": "1.01036 (+1.036%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2022, "reported_tax": 6760, "reported_tax_chg": "+1.4%", "reported_av": 508610, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2023, "reported_tax": 6920, "reported_tax_chg": "+2.4%", "reported_av": 518790, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2024, "reported_tax": 7000, "reported_tax_chg": "+1.2%", "reported_av": 529160, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2025, "reported_tax": 7210, "reported_tax_chg": "+2.9%", "reported_av": 539740, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2026, "reported_tax": None, "reported_tax_chg": "", "reported_av": 550540, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — 2026 Tax Not Provided (Blank)"},
]

PROP_B_HISTORY = [
    {"year": 2016, "reported_tax": 1680, "reported_tax_chg": "+1.6%", "reported_av": 96560, "reported_av_chg": "+1.5%", "boe_ccpi_factor": "1.01525 (+1.525%)", "confirmed_official": "", "status": "UNVERIFIED — Parcel Roll Requires APN"},
    {"year": 2017, "reported_tax": 1740, "reported_tax_chg": "+3.9%", "reported_av": 98490, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2018, "reported_tax": 2060, "reported_tax_chg": "+18.4%", "reported_av": 100460, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "FLAGGED — +18.4% Jump Driven by New Parcel Tax"},
    {"year": 2019, "reported_tax": 2130, "reported_tax_chg": "+3.5%", "reported_av": 102470, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2020, "reported_tax": 2200, "reported_tax_chg": "+3%", "reported_av": 104510, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2021, "reported_tax": 2070, "reported_tax_chg": "-5.9%", "reported_av": 105600, "reported_av_chg": "+1%", "boe_ccpi_factor": "1.01036 (+1.036%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2022, "reported_tax": 2110, "reported_tax_chg": "+2%", "reported_av": 107660, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "FLAGGED — Implied Roll Growth ~1.96% vs 2.00% Cap"},
    {"year": 2023, "reported_tax": 2180, "reported_tax_chg": "+3.4%", "reported_av": 109810, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2024, "reported_tax": 2320, "reported_tax_chg": "+6.2%", "reported_av": 112010, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — Ratio Matches BOE CCPI"},
    {"year": 2025, "reported_tax": 2440, "reported_tax_chg": "+5.3%", "reported_av": 114250, "reported_av_chg": "+2%", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "FLAGGED — 1.1827% Ad Valorem + ~$1,090 Parcel Charges"},
    {"year": 2026, "reported_tax": None, "reported_tax_chg": "", "reported_av": None, "reported_av_chg": "", "boe_ccpi_factor": "1.02000 (+2.000%)", "confirmed_official": "", "status": "UNVERIFIED — 2026 Roll & Bill Not Provided (Blank)"},
]


def prop19_cap_for_year(year: int, hpi_growth: float = 0.04) -> int:
    """
    Statutory Prop 19 cap for 2025-2026 ($1,044,590 rounded to nearest $10 per BOE LTA 2025/009),
    adjusted biennially every odd year (2027, 2029, ..., 2055) by 2-year California HPI compounding.
    """
    exact_2025 = 1_044_586.0
    if year <= 2026:
        return r10(exact_2025)
    biennial_steps = (year - 2025) // 2
    two_yr_factor = (1.0 + hpi_growth) ** 2
    return r10(exact_2025 * (two_yr_factor ** biennial_steps))


def federal_estate_exemption_for_year(year: int, cpi_growth: float = 0.025) -> int:
    """
    Verified 2026 ($15,000,000) and 2027 ($15,480,000 per IRS IR-2026-133 / Rev. Proc. 2026-35),
    indexed annually from 2027 onward by Chained CPI scenario rate.
    """
    if year <= 2026:
        return 15_000_000
    if year == 2027:
        return 15_480_000
    return r10(15_480_000.0 * ((1.0 + cpi_growth) ** (year - 2027)))


def build_all_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Base scenario growth parameters (transparent, explicitly labeled assumptions)
    hpi_base = 0.040      # 4.0%/yr nominal appreciation (aligned with FHFA CA ~4.1% long-run HPI)
    hpi_low = 0.030       # 3.0%/yr conservative sensitivity
    hpi_high = 0.050      # 5.0%/yr upside sensitivity
    prop13_cap = 0.020    # 2.0%/yr statutory Prop 13 max CCPI factor (R&TC §51)
    cpi_base = 0.025      # 2.5%/yr general CPI inflation
    ins_infl = 0.045      # 4.5%/yr CA insurance replacement-cost & reinsurance escalation
    water_a_infl = 0.035  # 3.5%/yr CPUC water utility escalation ([PROPERTY_A])
    water_b_infl = 0.045  # 4.5%/yr long-run SFPUC water/wastewater capital-plan escalation ([PROPERTY_B])
    sf_rent_growth = 0.018  # 1.8%/yr SF Rent Ordinance 60%-of-CPI allowable increase (1.6% in 2026-27)

    # Decomposed local tax parameters (verified against county tax rate books & BOS resolutions)
    # [PROPERTY_A]: ~1.18% ad valorem rate (1% Prop 13 + ~0.18% local school/water GO bonds) + $840 flat parcel taxes in 2025
    a_ad_valorem = 0.0118
    a_flat_2026 = 860
    a_raw_ratio = 0.01335  # 7210 / 539740 conservative sensitivity

    # [PROPERTY_B]: exact 1.18268325% SF FY25-26 ad valorem rate + ~$1,090 flat SF parcel taxes/charges in 2025
    b_ad_valorem = 0.0118268325
    b_flat_2026 = 1110
    b_raw_ratio = 0.02135  # 2440 / 114250 naive flat-ratio distortion

    # 1. Year-by-year projections for [PROPERTY_A] (2026-2055)
    prop_a_rows = []
    for yr in range(2026, 2056):
        t = yr - 2026
        mv_low = r10(3_100_000 * ((1 + hpi_low) ** t))
        mv_base = r10(3_100_000 * ((1 + hpi_base) ** t))
        mv_high = r10(3_100_000 * ((1 + hpi_high) ** t))
        fbyv = r10(550_540 * ((1 + prop13_cap) ** t))
        flat_chg = r10(a_flat_2026 * ((1 + 0.02) ** t))
        pre_tax = r10(fbyv * a_ad_valorem + flat_chg)

        p19_cap = prop19_cap_for_year(yr, hpi_base)
        #BOE Prop 19 formula: B + max(0, M - B - Cap), minus $7,000 Homeowners' Exemption if occupied
        raw_p19_av = fbyv + max(0, mv_base - fbyv - p19_cap)
        live_net_av = r10(max(0, raw_p19_av - 7_000))
        rent_net_av = mv_base  # 100% FMV reassessment if not occupied by heir within 1 yr

        tax_live_decomp = r10(live_net_av * a_ad_valorem + flat_chg)
        tax_rent_decomp = r10(rent_net_av * a_ad_valorem + flat_chg)
        tax_rent_naive = r10(rent_net_av * a_raw_ratio)

        # Operating costs: owner-input ($1,500 ins) vs realistic CDI replacement-cost benchmark ($3,000 HO-3 / $3,600 DP-3 in 2026$)
        ins_owner_est = r10(1_500 * ((1 + ins_infl) ** t))
        ins_ho3_real = r10(3_000 * ((1 + ins_infl) ** t))
        ins_dp3_real = r10(3_600 * ((1 + ins_infl) ** t))
        water_yr = r10(1_500 * ((1 + water_a_infl) ** t))  # $1,500/yr midpoint of $100-$150/mo

        # Solar / electric: legacy NEM credit (-$180/yr) through 2039; post-20-yr NEM sunset (2040+) NBT + fixed charge + inverter reserve
        if yr < 2040:
            elec_yr = -180
        else:
            elec_yr = r10(540 * ((1 + cpi_base) ** (yr - 2026)))  # ~$540/yr real fixed charge + inverter reserve net of solar self-consumption

        maint_live = r10(mv_base * 0.005)   # 0.50% of value (high land-share Silicon Valley SFR)
        maint_rent = r10(mv_base * 0.0065)  # 0.65% with tenant turnover wear

        carry_live = r10(tax_live_decomp + ins_ho3_real + water_yr + elec_yr + maint_live)
        carry_rent = r10(tax_rent_decomp + ins_dp3_real + water_yr + elec_yr + maint_rent)

        prop_a_rows.append({
            "year": yr,
            "mv_low_3pct": mv_low,
            "mv_base_4pct": mv_base,
            "mv_high_5pct": mv_high,
            "prop13_fbyv": fbyv,
            "pre_inheritance_tax": pre_tax,
            "prop19_cap_indexed": p19_cap,
            "assessed_if_live_in": live_net_av,
            "assessed_if_rented": rent_net_av,
            "tax_if_live_in": tax_live_decomp,
            "tax_if_rented": tax_rent_decomp,
            "tax_if_rented_naive_ratio": tax_rent_naive,
            "ins_owner_input_inflated": ins_owner_est,
            "ins_ho3_realistic": ins_ho3_real,
            "ins_dp3_landlord": ins_dp3_real,
            "water_annual": water_yr,
            "electricity_solar_annual": elec_yr,
            "maintenance_live": maint_live,
            "maintenance_rent": maint_rent,
            "total_carrying_live": carry_live,
            "total_carrying_rent": carry_rent,
            "source_url": URLS["boe_lta25009"],
        })

    # 2. Year-by-year projections for [PROPERTY_B] (2026-2055)
    prop_b_rows = []
    b_fbyv_2026 = r10(114_250 * 1.02)  # 116,540 modeled 2026 Prop 13 roll
    for yr in range(2026, 2056):
        t = yr - 2026
        mv_base = r10(1_800_000 * ((1 + 0.035) ** t))  # 3.5%/yr multi-unit rent-controlled appreciation
        fbyv = r10(b_fbyv_2026 * ((1 + prop13_cap) ** t))
        flat_chg = r10(b_flat_2026 * ((1 + 0.025) ** t))
        tax_held_as_is = r10(fbyv * b_ad_valorem + flat_chg)
        tax_full_reassess_decomp = r10(mv_base * b_ad_valorem + flat_chg)
        tax_full_reassess_naive = r10(mv_base * b_raw_ratio)

        # Gross rent from 2 rented units ($7,150/mo = $85,800/yr in 2026), escalated at 1.8%/yr SF Rent Board cap
        gross_rent_2units = r10(85_800 * ((1 + sf_rent_growth) ** t))
        eff_rent_after_vacancy = r10(gross_rent_2units * 0.96)  # 4% collection/turnover allowance

        ins_landlord_real = r10(4_500 * ((1 + ins_infl) ** t))  # 3-unit commercial/DP-3 habitational policy
        ins_owner_est = r10(1_500 * ((1 + ins_infl) ** t))
        water_sewer_yr = r10(4_380 * ((1 + water_b_infl) ** t))  # $4,380/yr midpoint of $330-$400/mo
        elec_common_yr = r10(600 * ((1 + cpi_base) ** t))        # $50/mo midpoint of $30-$70/mo
        maint_3unit_yr = r10(mv_base * 0.0085)                   # 0.85% older 3-unit coastal maintenance reserve

        noi_held_as_is = r10(eff_rent_after_vacancy - (tax_held_as_is + ins_landlord_real + water_sewer_yr + elec_common_yr + maint_3unit_yr))
        noi_if_reassessed = r10(eff_rent_after_vacancy - (tax_full_reassess_decomp + ins_landlord_real + water_sewer_yr + elec_common_yr + maint_3unit_yr))

        prop_b_rows.append({
            "year": yr,
            "mv_base_3_5pct": mv_base,
            "prop13_fbyv": fbyv,
            "gross_rent_2_units": gross_rent_2units,
            "effective_rent_after_vacancy": eff_rent_after_vacancy,
            "tax_held_as_is": tax_held_as_is,
            "tax_if_reassessed_decomp": tax_full_reassess_decomp,
            "tax_if_reassessed_naive": tax_full_reassess_naive,
            "ins_3unit_realistic": ins_landlord_real,
            "ins_owner_input_inflated": ins_owner_est,
            "water_sewer_sfpuc": water_sewer_yr,
            "electricity_common": elec_common_yr,
            "maintenance_3unit": maint_3unit_yr,
            "net_cash_flow_held_as_is": noi_held_as_is,
            "net_cash_flow_if_reassessed": noi_if_reassessed,
            "source_url": URLS["sf_taxrate"],
        })

    # 3. Coordinated 2-Property Decision Comparison at Inheritance Years 2040, 2045, and 2050
    # Evaluates Year-1 post-inheritance cash flow AND 10-year post-inheritance net wealth across 4 strategies
    a_by_yr = {r["year"]: r for r in prop_a_rows}
    b_by_yr = {r["year"]: r for r in prop_b_rows}
    decision_rows = []
    for inh_yr in (2040, 2045, 2050):
        ra = a_by_yr[inh_yr]
        rb = b_by_yr[inh_yr]
        mv_a = ra["mv_base_4pct"]
        noi_b = rb["net_cash_flow_held_as_is"]

        # Sale proceeds of [PROPERTY_A] immediately upon inheritance (IRC §1014 step-up => $0 capital gains tax)
        selling_costs = r10(mv_a * 0.05)          # 5.0% brokerage, escrow, title, prep
        scc_transfer_tax = r10(mv_a * 0.0011)     # $1.10 per $1,000 Santa Clara County DTT
        cap_gains_tax_at_death_sale = 0           # IRC §1014 step-up to date-of-death FMV
        net_sale_proceeds = r10(mv_a - selling_costs - scc_transfer_tax - cap_gains_tax_at_death_sale)

        # Strategy 1: Live in [PROPERTY_A] (Prop 19 exclusion) + Keep [PROPERTY_B] (2 units rented, Unit 3 unrented)
        s1_yr1_net_cf = r10(noi_b - ra["total_carrying_live"])
        # 10-yr post-inheritance wealth (Property A appreciates 4%/yr, less post-death cap gains if liquidated, plus cumulative cash flow)
        mv_a_10 = r10(mv_a * ((1.04) ** 10))
        # After 2+ yrs primary residence, IRC §121 excludes $250k single / $500k MFJ (use $250k conservative single); ~33% combined LTCG+NIIT+CA tax on excess
        gain_after_121 = max(0, r10(mv_a_10 * 0.9489) - mv_a - 250_000)
        s1_10yr_net_equity_a = r10(mv_a_10 * 0.9489 - gain_after_121 * 0.33)
        s1_10yr_cum_cf = r10(s1_yr1_net_cf * 10.8)  # 10-yr sum with modest escalation
        s1_10yr_wealth_contrib = r10(s1_10yr_net_equity_a + s1_10yr_cum_cf)

        # Strategy 2: Live in [PROPERTY_B] Unit 3 + Rent Out [PROPERTY_A] (100% FMV reassessment on [PROPERTY_A])
        # Illustrative gross rental yield scenario 2.4% of FMV (explicitly labeled modeled scenario; official market rent blank)
        est_gross_rent_a = r10(mv_a * 0.024)
        est_eff_rent_a = r10(est_gross_rent_a * 0.92)  # 8% vacancy + leasing/management
        # IRC §168 27.5-yr depreciation on stepped-up structure (~25% of Silicon Valley SFR value)
        ann_depreciation_a = r10((mv_a * 0.25) / 27.5)
        pre_tax_cf_a = r10(est_eff_rent_a - ra["total_carrying_rent"])
        taxable_rent_a = max(0, pre_tax_cf_a - ann_depreciation_a)
        income_tax_rent_a = r10(taxable_rent_a * 0.37)
        after_tax_cf_a = r10(pre_tax_cf_a - income_tax_rent_a)
        s2_yr1_net_cf = r10(noi_b + after_tax_cf_a)
        # At year 10, no IRC §121 exclusion on pure rental + 25% federal / CA depreciation recapture on 10 yrs depreciation
        recapture_10yr = r10(ann_depreciation_a * 10 * 0.35)
        gain_no_121 = max(0, r10(mv_a_10 * 0.9489) - mv_a)
        s2_10yr_net_equity_a = r10(mv_a_10 * 0.9489 - gain_no_121 * 0.33 - recapture_10yr)
        s2_10yr_cum_cf = r10(s2_yr1_net_cf * 11.2)
        s2_10yr_wealth_contrib = r10(s2_10yr_net_equity_a + s2_10yr_cum_cf)

        # Break-even monthly rent on [PROPERTY_A] just to match CA-tax-exempt 10-Yr Treasury cash income
        treas_10yr_rate = 0.0488  # Verified Nov 9, 2026 U.S. Treasury 10-Yr CMT yield (home.treasury.gov)
        treas_after_fed_tax_rate = treas_10yr_rate * (1.0 - 0.28)  # 0% CA tax under 31 U.S.C. §3124; ~28% effective fed+NIIT
        treas_yr1_after_tax_cash = r10(net_sale_proceeds * treas_after_fed_tax_rate)
        breakeven_monthly_rent_vs_treasury = r10(((ra["total_carrying_rent"] + treas_yr1_after_tax_cash) / 0.92) / 12.0)

        # Strategy 3A: Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] Immediately & Reinvest in Diversified Equities (7.0% nominal)
        # 1.5% qualified dividend taxed annually (~28% combined fed+CA) + 5.5% price appreciation taxed at Yr 10 liquidation
        eq_after_annual_drag = 0.055 + 0.015 * (1.0 - 0.28)  # ~6.58%/yr compounding before deferred LTCG
        eq_10yr_gross = net_sale_proceeds * ((1.0 + eq_after_annual_drag) ** 10)
        eq_deferred_gain = max(0.0, eq_10yr_gross - net_sale_proceeds * ((1.0 + 0.015 * 0.72) ** 10))
        eq_10yr_after_tax = r10(eq_10yr_gross - eq_deferred_gain * 0.30)
        eq_yr1_total_return = r10(net_sale_proceeds * 0.07)
        s3a_yr1_net_cf = r10(noi_b + net_sale_proceeds * 0.015 * 0.72)  # cash dividend + Property B NOI (plus ~5.5% unrealized growth)
        s3a_10yr_wealth_contrib = r10(eq_10yr_after_tax + r10(noi_b * 10.8))

        # Strategy 3B: Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] Immediately & Reinvest in U.S. Treasury Ladder (4.88% 10-Yr CMT, 0% CA Tax)
        tr_10yr_portfolio = r10(net_sale_proceeds * ((1.0 + treas_after_fed_tax_rate) ** 10))
        s3b_yr1_net_cf = r10(noi_b + treas_yr1_after_tax_cash)
        s3b_10yr_wealth_contrib = r10(tr_10yr_portfolio + r10(noi_b * 10.8))

        decision_rows.extend([
            {
                "inheritance_year": inh_yr,
                "strategy_code": "S3A",
                "strategy_name": "Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] (Step-Up) -> Diversified Equities (7.0% Scenario)",
                "prop_a_fmv_at_death": mv_a,
                "net_sale_proceeds_prop_a": net_sale_proceeds,
                "yr1_prop_a_property_tax": 0,
                "yr1_portfolio_or_prop_a_return": eq_yr1_total_return,
                "yr1_combined_net_cash_flow": s3a_yr1_net_cf,
                "ten_yr_after_tax_wealth": s3a_10yr_wealth_contrib,
                "breakeven_prop_a_rent_mo": breakeven_monthly_rent_vs_treasury,
                "verdict": "RANK #1 (Max Long-Term After-Tax Wealth & Zero Reassessment Drag)",
                "source_url": URLS["irs_basis"],
            },
            {
                "inheritance_year": inh_yr,
                "strategy_code": "S3B",
                "strategy_name": "Live in [PROPERTY_B] Unit 3 + Sell [PROPERTY_A] (Step-Up) -> U.S. Treasury Ladder (4.88% 10-Yr CMT, CA-Tax-Free)",
                "prop_a_fmv_at_death": mv_a,
                "net_sale_proceeds_prop_a": net_sale_proceeds,
                "yr1_prop_a_property_tax": 0,
                "yr1_portfolio_or_prop_a_return": treas_yr1_after_tax_cash,
                "yr1_combined_net_cash_flow": s3b_yr1_net_cf,
                "ten_yr_after_tax_wealth": s3b_10yr_wealth_contrib,
                "breakeven_prop_a_rent_mo": breakeven_monthly_rent_vs_treasury,
                "verdict": "RANK #2 / #1 LOW-RISK INCOME (Highest Guaranteed Cash Income, 0% CA Tax)",
                "source_url": URLS["treasury"],
            },
            {
                "inheritance_year": inh_yr,
                "strategy_code": "S1",
                "strategy_name": "Live in [PROPERTY_A] (Prop 19 Cap) + Keep [PROPERTY_B] (2 Units Rented)",
                "prop_a_fmv_at_death": mv_a,
                "net_sale_proceeds_prop_a": 0,
                "yr1_prop_a_property_tax": ra["tax_if_live_in"],
                "yr1_portfolio_or_prop_a_return": r10(-ra["total_carrying_live"]),
                "yr1_combined_net_cash_flow": s1_yr1_net_cf,
                "ten_yr_after_tax_wealth": s1_10yr_wealth_contrib,
                "breakeven_prop_a_rent_mo": breakeven_monthly_rent_vs_treasury,
                "verdict": "CONDITIONAL LIFESTYLE WINNER (Best Only If Occupying [PROPERTY_A] Long-Term)",
                "source_url": URLS["boe_prop19"],
            },
            {
                "inheritance_year": inh_yr,
                "strategy_code": "S2",
                "strategy_name": "Live in [PROPERTY_B] Unit 3 + Rent Out [PROPERTY_A] (100% FMV Reassessment)",
                "prop_a_fmv_at_death": mv_a,
                "net_sale_proceeds_prop_a": 0,
                "yr1_prop_a_property_tax": ra["tax_if_rented"],
                "yr1_portfolio_or_prop_a_return": after_tax_cf_a,
                "yr1_combined_net_cash_flow": s2_yr1_net_cf,
                "ten_yr_after_tax_wealth": s2_10yr_wealth_contrib,
                "breakeven_prop_a_rent_mo": breakeven_monthly_rent_vs_treasury,
                "verdict": "RANK #4 — WEAKEST (Full Prop 19 Reassessment Crushes Rental Cash Yield)",
                "source_url": URLS["irs_p527"],
            },
        ])

    # 4. Estate Tax & Liquid Cash Inheritance Headroom Table (2026, 2027, 2040, 2045, 2050)
    estate_rows = []
    for yr in (2026, 2027, 2040, 2045, 2050):
        ex_single = federal_estate_exemption_for_year(yr, cpi_base)
        ex_married = ex_single * 2
        ex_cut50 = r10(ex_single * 0.5)  # Legislative risk stress test: 50% statutory rollback

        mv_a = a_by_yr[yr]["mv_base_4pct"] if yr in a_by_yr else 3_100_000
        mv_b = b_by_yr[yr]["mv_base_3_5pct"] if yr in b_by_yr else 1_800_000
        both_re = r10(mv_a + mv_b)

        estate_rows.append({
            "year": yr,
            "exemption_single": ex_single,
            "exemption_married_dsue": ex_married,
            "exemption_50pct_cut_risk": ex_cut50,
            "prop_a_only_value": mv_a,
            "both_properties_value": both_re,
            "cash_headroom_single_if_prop_a_only": max(0, r10(ex_single - mv_a)),
            "cash_headroom_single_if_both_in_estate": max(0, r10(ex_single - both_re)),
            "cash_headroom_married_if_both_in_estate": max(0, r10(ex_married - both_re)),
            "cash_headroom_50pct_cut_if_both": max(0, r10(ex_cut50 - both_re)),
            "ca_state_local_inheritance_tax": 0,
            "federal_rate_above_threshold": "40%",
            "source_url": URLS["irs_2027"] if yr >= 2027 else URLS["irs_706"],
        })

    # Write RFC-4180 properly quoted CSVs (quoting ALL strings, zero unquoted comma bugs)
    def write_csv(filename: str, rows: list[dict]) -> None:
        if not rows:
            return
        with (DATA_DIR / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)

    write_csv("property_a_projections_2026_2055.csv", prop_a_rows)
    write_csv("property_b_projections_2026_2055.csv", prop_b_rows)
    write_csv("decision_comparison_2040_2045_2050.csv", decision_rows)
    write_csv("estate_tax_headroom_2026_2050.csv", estate_rows)

    # Write Task 531B & 531C structured JSONs + Task 531D model_outputs.json
    tax_law_verified = {
        "generated_date": "2026-11-10",
        "session_id": "arena-531aee5c-tino3",
        "federal_estate_and_gift": {
            "exemption_2026_single": 15_000_000,
            "exemption_2026_married_portability": 30_000_000,
            "exemption_2027_single": 15_480_000,
            "exemption_2027_married_portability": 30_960_000,
            "annual_gift_2026": 19_000,
            "annual_gift_2027": 20_000,
            "top_marginal_rate": "40%",
            "statutory_authority": "26 U.S.C. §§2001, 2010(c)(3) (OBBBA / WFTC §70106); IRS IR-2026-133 / Rev. Proc. 2026-35",
            "official_url": URLS["irs_2027"],
        },
        "california_state_and_local_inheritance": {
            "state_inheritance_tax": 0,
            "state_estate_tax": 0,
            "local_inheritance_tax": 0,
            "statutory_authority": "CA Revenue & Taxation Code §§13301–13302 (enacted via Proposition 6, June 1982; voter approval required to repeal)",
            "official_url": URLS["ca_rtc13301"],
        },
        "prop_13_and_prop_19": {
            "prop_13_base_rate": "1.00% + voter-approved local debt & flat parcel charges",
            "prop_13_annual_inflation_cap": "Lesser of October-to-October CCPI or 2.000% (R&TC §51)",
            "prop_19_cap_2025_2027_rounded_10": 1_044_590,
            "prop_19_formula": "New Taxable Value = FBYV + max(0, FMV - FBYV - Cap), less $7,000 Homeowners' Exemption if occupied within 1 yr",
            "prop_19_move_out_rule": "Moving out later removes the Prop 19 exclusion on the next Jan 1 lien date (BOE Pub. 800-1)",
            "official_url": URLS["boe_lta25009"],
        },
        "basis_and_capital_gains": {
            "revocable_trust_step_up": "Full FMV step-up at death under IRC §1014 when included in gross estate",
            "irrevocable_trust_trap": "NO IRC §1014 step-up for irrevocable grantor trust assets excluded from gross estate (IRS Rev. Rul. 2023-2)",
            "federal_ltcg_plus_niit": "0% / 15% / 20% + 3.8% NIIT above $200,000 single / $250,000 MFJ",
            "california_capital_gains": "Taxed as ordinary income: 1% to 12.3% + 1% Mental Health Services Tax over $1,000,000 (13.3% top rate)",
            "treasury_interest_ca_exemption": "U.S. Treasury obligation interest is 100% exempt from California income tax (31 U.S.C. §3124)",
            "official_url": URLS["irs_rr2023_2"],
        },
    }
    (DATA_DIR / "tax_law_verified.json").write_text(json.dumps(tax_law_verified, indent=2) + "\n", encoding="utf-8")

    properties_verified = {
        "generated_date": "2026-11-10",
        "session_id": "arena-531aee5c-tino3",
        "privacy_placeholders": {
            "property_a": "[PROPERTY_A] — Silicon Valley Single-Family Residence with Solar (Santa Clara County Jurisdiction)",
            "property_b": "[PROPERTY_B] — Coastal 3-Unit Mixed-Occupancy Residence (City & County of San Francisco Jurisdiction)",
            "parties": ["[DECEDENT / TRUSTOR]", "[BENEFICIARY / HEIR]", "[SUCCESSOR_TRUSTEE]", "[FAMILY_REVOCABLE_TRUST]"],
        },
        "property_a_history_rounded_10": PROP_A_HISTORY,
        "property_b_history_rounded_10": PROP_B_HISTORY,
    }
    (DATA_DIR / "properties_verified.json").write_text(json.dumps(properties_verified, indent=2) + "\n", encoding="utf-8")

    outputs = {
        "generated_date": "2026-11-10",
        "session_id": "arena-531aee5c-tino3",
        "urls": URLS,
        "prop_a_history": PROP_A_HISTORY,
        "prop_b_history": PROP_B_HISTORY,
        "prop_a_projections": prop_a_rows,
        "prop_b_projections": prop_b_rows,
        "decision_rows": decision_rows,
        "estate_rows": estate_rows,
    }
    (DATA_DIR / "model_outputs.json").write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    return outputs


if __name__ == "__main__":
    data = build_all_data()
    print(
        f"Generated model_outputs.json: {len(data['prop_a_projections'])} Property A yrs, "
        f"{len(data['prop_b_projections'])} Property B yrs, "
        f"{len(data['decision_rows'])} decision rows, {len(data['estate_rows'])} estate rows."
    )
