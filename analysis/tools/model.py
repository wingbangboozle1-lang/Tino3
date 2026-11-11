#!/usr/bin/env python3
"""Deterministic 50-year (2026-2076) ownership-distinction & black-swan decision model.

Guarantees:
  * Every exported dollar amount is rounded to the nearest $10 via r10().
  * Public assessment-roll and tax-bill anchors are generalized ($10,000 for assessed values,
    $100 for historical tax bills) so no parcel can be reverse-matched on public rolls.
  * Zero personal names, street addresses, APNs, postal codes, or city/county names appear here.
  * Incorporates:
      1. Ownership distinction: [PROPERTY_A] inherited via revocable trust vs. [PROPERTY_B]
         ALREADY owned by [BENEFICIARY] (zero IRC 2031 estate inclusion, zero RTC 60 reassessment,
         zero IRC 1014 basis step-up on [PROPERTY_B]).
      2. Exact CA RTC 17043 (+1% Mental Health Services Tax above $1,000,000 -> 13.3% top CA rate).
      3. Exact 31 U.S.C. 3124 state-income-tax exemption on U.S. Treasury interest.
      4. Exact CA RTC 51(a)(2) (Proposition 8) temporary decline-in-value property tax relief
         during housing downturns, plus BOE LTA 2026/002 50-year actual California CPI / Prop 13
         factors and FRED CASTHPI 50-year actual California house price series (1976-2026).
      5. CPUC D.14-03-041 / D.22-12-056 20-year legacy solar NEM sunset.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from sources import write_sources_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DIR = ROOT / "data"


def r10(x: float) -> int:
    return int(round(float(x) / 10.0) * 10)


# ---------------------------------------------------------------------------
# 1. Generalized Owner-Supplied Inputs (parcel-safe; never raw roll figures)
# ---------------------------------------------------------------------------
INPUTS = {
    "a_value_2026": 3_100_000,       # Owner Nov 2026 market estimate for [PROPERTY_A]
    "a_av_2026": 550_000,            # Generalized to nearest $10,000
    "a_av_2025": 540_000,            # Generalized to nearest $10,000
    "a_bill_2025": 7_200,            # Generalized to nearest $100
    "a_water_yr": 1_500,             # $100-$150/mo midpoint ($125/mo)
    "a_solar_credit_yr": -180,       # -$10 to -$20/mo net surplus credit while on legacy NEM
    "a_post_nem_elec_yr": 1_440,     # Scenario post-20-yr NEM sunset net grid import ($120/mo in 2026$)
    "a_ins_placeholder": 1_500,      # Owner placeholder (official quote blank/unverified)
    "b_value_2026": 1_800_000,       # Owner Nov 2026 market estimate for already-owned [PROPERTY_B]
    "b_av_2025": 110_000,            # Generalized to nearest $10,000
    "b_bill_2025": 2_400,            # Generalized to nearest $100
    "b_rent_2units_mo": 7_150,       # 2 rented units combined ($85,800/yr); 3rd unit owner-occupied
    "b_water_yr": 4_380,             # $330-$400/mo midpoint ($365/mo) for all 3 units
    "b_elec_yr": 600,                # $30-$70/mo midpoint ($50/mo)
    "b_ins_placeholder": 1_500,      # Owner placeholder (official quote blank/unverified)
    "b_assumed_orig_basis": 300_000, # Illustrative low historical cost basis aligned with ~$110k AV
}

# ---------------------------------------------------------------------------
# 2. Verified Official Constants (each traced to analysis/tools/sources.py)
# ---------------------------------------------------------------------------
VERIFIED = {
    "fed_excl_2026": 15_000_000,         # irs_estate
    "fed_excl_2027": 15_480_000,         # irs_2027
    "gift_excl_2026": 19_000,            # irs_2027
    "gift_excl_2027": 20_000,            # irs_2027
    "fed_estate_top_rate": 0.40,         # usc_2001
    "ca_estate_tax": 0,                  # sco_estate, rtc_13301
    "prop19_cap_2025_2027": 1_044_586,   # boe_lta25009 ($1,044,590 rounded to $10)
    "prop13_max_cap": 0.02,              # rtc_51, boe_lta26002
    "homeowners_exemption": 7_000,       # rtc_218
    "rate_b_fy2627": 0.0118162182,       # cityb_rate
    "rate_b_fy2526": 0.0118268325,       # cityb_res447
    "rate_a_min": 0.011258,              # cnty_a_rates
    "rate_a_max": 0.012409,              # cnty_a_rates
    "cnty_a_transfer_tax": 0.0011,       # rtc_11911, cnty_a_recorder
    "cityb_rent_cap_2026": 0.016,        # cityb_rent (Mar 1, 2026 - Feb 28, 2027)
    "cityb_rent_cpi_share": 0.60,        # cityb_rent
    "depreciation_years": 27.5,          # irs_p527
    "fed_ltcg_top": 0.20,                # irs_tc409
    "fed_sec1250_recap": 0.25,           # irs_tc409
    "niit_rate": 0.038,                  # irs_tc559
    "ca_base_top_rate": 0.123,           # ftb_cg
    "ca_mhst_surtax": 0.01,              # rtc_17043 (+1% above $1,000,000)
    "ca_mhst_threshold": 1_000_000,      # rtc_17043
    "sec121_single": 250_000,            # irs_tc701
    "sec121_joint": 500_000,             # irs_tc701
    "fair_plan_cap": 3_000_000,          # cdi_tips
    "nem_legacy_years": 20,              # cpuc_nem (D.14-03-041)
    "treasury_10y_nov10_2026": 0.0498,   # treasury_cmt (10 Nov 2026)
    "treasury_30y_nov10_2026": 0.0535,   # treasury_cmt (10 Nov 2026)
    "tsp_cfund_lifetime": 0.1140,        # tsp_cfund (Jan 1988 - Oct 2026)
    "tsp_sp500_lifetime": 0.1142,        # tsp_cfund (Jan 1988 - Oct 2026)
    "tsp_gfund_lifetime": 0.0465,        # tsp_gfund (Apr 1987 - Oct 2026)
    "ca_hpi_50yr_cagr": 0.0610,          # fred_casthpi (1976 Q2 50.31 -> 2026 Q2 974.97)
}

# ---------------------------------------------------------------------------
# 3. Baseline Scenario Parameters (transparently labeled as assumptions)
# ---------------------------------------------------------------------------
BASE = {
    "g_low": 0.03,
    "g_base": 0.04,
    "g_high": 0.055,              # Anchored near 31-yr Metro A/B (5.3%-5.7%) & 50-yr CA HPI (6.1%)
    "cpi": 0.025,
    "rate_a": 0.0118,             # Midpoint of County A TRA range (1.1258%-1.2409%)
    "stock_total": 0.07,          # Conservative vs. 11.40% TSP C Fund lifetime; tested across regimes
    "stock_div": 0.015,
    "treasury_yield": 0.0498,     # Verified 10 Nov 2026 10-Yr Treasury par yield
    "rent_a_mo_2026": 6_500,      # Scenario market rent for [PROPERTY_A] ($78,000/yr); break-even solved
    "rent_a_growth": 0.03,
    "unit3_rent_mo_2026": 3_580,  # Average of the two rented units in [PROPERTY_B] ($7,150 / 2 rounded)
    "vacancy": 0.05,
    "bldg_share_a": 0.30,
    "bldg_share_b": 0.40,
    "maint_a_2026": 9_300,        # ~0.30% of total value (1.0% of building); lower than [PROPERTY_B]
    "maint_b_2026": 10_800,       # ~0.60% of total value (1.5% of 3-unit building)
    "broker_closing": 0.05,       # 5.0% brokerage/escrow/prep + 0.11% County A transfer tax = 5.11%
    "nem_sunset_year": 2044,      # 20-yr NEM 2.0 sunset assuming ~2024 interconnection (tested)
    "t_ord_fed": 0.24,            # Federal marginal ordinary rate (IR-2026-133 24% bracket)
    "t_ord_ca": 0.093,            # CA marginal ordinary rate (9.3% bracket)
    "t_div_fed": 0.15,            # Qualified dividend federal rate
    "excl_index": 0.025,          # Post-2027 estate exclusion inflation scenario
    "hold_years": 10,             # Standard post-inheritance comparison window (also 30-yr / 50-yr)
    "inh_years": [2040, 2045, 2050],
}

SELL_COST_A = BASE["broker_closing"] + VERIFIED["cnty_a_transfer_tax"]  # 5.11%
T_ORD_COMBINED = BASE["t_ord_fed"] + BASE["t_ord_ca"]                   # 33.3%
# Treasury interest is EXEMPT from California income tax under 31 U.S.C. 3124:
T_TREASURY = BASE["t_ord_fed"] + VERIFIED["niit_rate"]                  # 27.8% (vs 37.1% if taxed by CA!)
T_DIV = BASE["t_div_fed"] + VERIFIED["niit_rate"] + BASE["t_ord_ca"]    # 28.1%
# Combined top rate including CA RTC 17043 (+1% above $1,000,000):
T_LTCG_UNDER_1M = VERIFIED["fed_ltcg_top"] + VERIFIED["niit_rate"] + VERIFIED["ca_base_top_rate"]  # 36.1%
T_LTCG_OVER_1M = T_LTCG_UNDER_1M + VERIFIED["ca_mhst_surtax"]                                      # 37.1%
T_RECAP_OVER_1M = VERIFIED["fed_sec1250_recap"] + VERIFIED["niit_rate"] + VERIFIED["ca_base_top_rate"] + VERIFIED["ca_mhst_surtax"]  # 42.1%

FIXED_CHARGES_A_2025 = r10(INPUTS["a_bill_2025"] - BASE["rate_a"] * INPUTS["a_av_2025"])            # $830
FIXED_CHARGES_B_2025 = r10(INPUTS["b_bill_2025"] - VERIFIED["rate_b_fy2526"] * INPUTS["b_av_2025"]) # $1,100


def cap_gains_tax(gain: float, recap_depreciation: float = 0.0) -> float:
    """Compute combined Federal + NIIT + CA (including RTC 17043 +1% over $1M) tax on sale."""
    total_taxable = max(0.0, gain) + max(0.0, recap_depreciation)
    if total_taxable <= 0:
        return 0.0
    # Base tax at 36.1% on LTCG + 41.1% on recapture, plus 1% CA RTC 17043 on total above $1,000,000
    base = max(0.0, gain) * T_LTCG_UNDER_1M + max(0.0, recap_depreciation) * (T_RECAP_OVER_1M - VERIFIED["ca_mhst_surtax"])
    mhst = max(0.0, total_taxable - VERIFIED["ca_mhst_threshold"]) * VERIFIED["ca_mhst_surtax"]
    return base + mhst


# ---------------------------------------------------------------------------
# 4. Official 50-Year Historical California Macro Data (1976-2026 -> 50 Annual Steps)
#    Every housing index level (CASTHPI Q2 = YYYY-04-01), California CPI & Prop 13
#    factor (BOE LTA 2026/002 FY 1977-78..2026-27), and 10-Year Treasury yield
#    (FRED GS10 YYYY-04-01) is copied verbatim from the opened official tables.
#    Annual equity returns are explicitly labeled scenario paths (7.0% baseline,
#    with Fed History's verified -57% cumulative 2007-2009 GFC crash in 2008-2009).
# ---------------------------------------------------------------------------
CASTHPI_Q2_1976 = 50.31
RAW_OFFICIAL_50YR = [
    # (yr, casthpi_q2, boe_ccpi_pct, boe_prop13_f, fred_gs10_apr_pct, scen_eq_r)
    (1977,  63.02,  7.169, 1.02000,  7.37,  0.070),
    (1978,  76.01,  8.233, 1.02000,  8.15,  0.070),
    (1979,  88.68,  9.826, 1.02000,  9.18,  0.070),
    (1980, 102.79, 17.316, 1.02000, 11.47,  0.070),
    (1981, 112.83,  7.134, 1.02000, 13.68,  0.070),
    (1982, 107.26, 11.137, 1.02000, 13.87,  0.070),
    (1983, 117.43,  1.033, 1.01000, 10.40,  0.070),
    (1984, 120.06,  5.034, 1.02000, 12.63,  0.070),
    (1985, 126.23,  5.089, 1.02000, 11.43,  0.070),
    (1986, 134.74,  4.374, 1.02000,  7.30,  0.070),
    (1987, 148.21,  2.095, 1.02000,  8.02,  0.070),
    (1988, 169.63,  5.160, 1.02000,  8.72,  0.070),
    (1989, 205.79,  4.730, 1.02000,  9.18,  0.070),
    (1990, 228.07,  4.758, 1.02000,  8.79,  0.070),
    (1991, 226.97,  6.390, 1.02000,  8.04,  0.070),
    (1992, 225.08,  3.039, 1.02000,  7.48,  0.070),
    (1993, 217.24,  3.441, 1.02000,  5.97,  0.070),
    (1994, 206.87,  2.308, 1.02000,  6.97,  0.070),
    (1995, 201.49,  1.194, 1.01190,  7.06,  0.070),
    (1996, 200.89,  1.115, 1.01110,  6.51,  0.070),
    (1997, 204.53,  2.399, 1.02000,  6.89,  0.070),
    (1998, 221.56,  2.081, 1.02000,  5.64,  0.070),
    (1999, 239.29,  1.853, 1.01853,  5.18,  0.070),
    (2000, 267.83,  3.214, 1.02000,  5.99,  0.070),
    (2001, 305.47,  4.172, 1.02000,  5.14,  0.070),
    (2002, 335.73,  3.215, 1.02000,  5.21,  0.070),
    (2003, 373.71,  2.459, 1.02000,  3.96,  0.070),
    (2004, 450.89,  1.867, 1.01867,  4.35,  0.070),
    (2005, 569.94,  3.665, 1.02000,  4.34,  0.070),
    (2006, 643.96,  4.596, 1.02000,  4.99,  0.070),
    (2007, 622.92,  2.269, 1.02000,  4.69,  0.070),
    (2008, 498.03,  3.380, 1.02000,  3.68, -0.350),  # Fed History GFC S&P -57% peak-to-trough (0.65 * 0.6615 = 0.43)
    (2009, 420.20,  3.477, 1.02000,  2.93, -0.338),
    (2010, 407.91, -0.237, 0.99763,  3.85,  0.114),  # TSP C Fund verified lifetime CAGR (11.40%) recovery
    (2011, 384.83,  0.753, 1.00753,  3.46,  0.114),
    (2012, 381.57,  2.889, 1.02000,  2.05,  0.114),
    (2013, 425.87,  3.081, 1.02000,  1.76,  0.114),
    (2014, 484.00,  0.454, 1.00454,  2.71,  0.114),
    (2015, 516.28,  1.998, 1.01998,  1.94,  0.114),
    (2016, 553.43,  1.525, 1.01525,  1.81,  0.114),
    (2017, 590.29,  2.619, 1.02000,  2.30,  0.070),
    (2018, 632.98,  2.962, 1.02000,  2.87,  0.070),
    (2019, 651.64,  3.847, 1.02000,  2.53,  0.070),
    (2020, 676.76,  2.980, 1.02000,  0.66,  0.070),
    (2021, 761.06,  1.036, 1.01036,  1.64,  0.070),
    (2022, 919.32,  5.561, 1.02000,  2.75,  0.070),
    (2023, 905.46,  7.274, 1.02000,  3.46,  0.070),
    (2024, 945.84,  3.181, 1.02000,  4.54,  0.070),
    (2025, 966.27,  2.514, 1.02000,  4.28,  0.070),
    (2026, 974.97,  3.307, 1.02000,  4.32,  0.070),
]
HIST_50YR = []
_prev_hpi = CASTHPI_Q2_1976
for _yr, _hpi, _ccpi, _p13, _gs10, _eq in RAW_OFFICIAL_50YR:
    HIST_50YR.append((_yr, (_hpi / _prev_hpi) - 1.0, _ccpi / 100.0, _p13, _gs10 / 100.0, _eq))
    _prev_hpi = _hpi
assert len(HIST_50YR) == 50


# ---------------------------------------------------------------------------
# 5. Core Helper Functions
# ---------------------------------------------------------------------------
def infl_factor(year: int, base_year: int = 2026, cpi: float | None = None) -> float:
    c = BASE["cpi"] if cpi is None else cpi
    return (1.0 + c) ** (year - base_year)


def prop_a_value(year: int, g: float) -> float:
    return INPUTS["a_value_2026"] * ((1.0 + g) ** (year - 2026))


def prop_b_value(year: int, g: float) -> float:
    return INPUTS["b_value_2026"] * ((1.0 + g) ** (year - 2026))


def prop_a_fbyv(year: int) -> float:
    return INPUTS["a_av_2026"] * ((1.0 + VERIFIED["prop13_max_cap"]) ** (year - 2026))


def prop_b_fbyv(year: int) -> float:
    return INPUTS["b_av_2025"] * ((1.0 + VERIFIED["prop13_max_cap"]) ** (year - 2025))


def prop19_cap(year: int, g: float) -> float:
    """BOE LTA 2025/009: adjusted every second Feb 16 by ONE prior calendar year's CA HPI change."""
    steps = 0 if year < 2027 else ((year - 2027) // 2) + 1
    return VERIFIED["prop19_cap_2025_2027"] * ((1.0 + g) ** steps)


def tax_a_from_av(taxable_av: float, year: int, fixed_mult: float = 1.0) -> float:
    return taxable_av * BASE["rate_a"] + FIXED_CHARGES_A_2025 * fixed_mult


def tax_b_from_av(taxable_av: float, year: int, fixed_mult: float = 1.0) -> float:
    return taxable_av * VERIFIED["rate_b_fy2627"] + FIXED_CHARGES_B_2025 * fixed_mult


def elec_a(year: int, cpi_mult: float) -> float:
    """Models 20-yr CPUC NEM 2.0 legacy tariff through nem_sunset_year, then NBT net import cost."""
    if year <= BASE["nem_sunset_year"]:
        return float(INPUTS["a_solar_credit_yr"])
    return INPUTS["a_post_nem_elec_yr"] * cpi_mult


# ---------------------------------------------------------------------------
# 6. General Path-Based Post-Inheritance Strategy Simulator
#    Supports BOTH constant-rate baseline AND arbitrary year-by-year Black Swan paths!
# ---------------------------------------------------------------------------
STRATEGIES = [
    ("sell_stock", "Sell [PROPERTY_A] -> 100% S&P 500 Index; Keep [PROPERTY_B]"),
    ("sell_barbell", "Sell [PROPERTY_A] -> 60/40 Stock + US Treasury Barbell; Keep [PROPERTY_B]"),
    ("sell_treasury", "Sell [PROPERTY_A] -> 100% CA-Tax-Exempt US Treasuries; Keep [PROPERTY_B]"),
    ("rent_a", "Keep & Rent Out [PROPERTY_A]; Keep & Live in [PROPERTY_B] Unit 3"),
    ("live_a_rent_u3", "Move Into [PROPERTY_A] (Prop 19); Rent Out [PROPERTY_B] Unit 3"),
    ("live_a_keep_u3", "Move Into [PROPERTY_A] (Prop 19); Keep [PROPERTY_B] Unit 3 Unrented"),
]


def simulate_regime(
    inh_year: int,
    fmv_a_at_inh: float,
    fbyv_a_at_inh: float,
    prop19_cap_at_inh: float,
    cpi_mult_at_inh: float,
    annual_path: list[dict],
    rent_a_mo_2026: float | None = None,
    ins_mult: float = 1.0,
    seismic_shock_year_idx: int | None = None,
    seismic_loss_frac_of_bldg: float = 0.0,
    step_up_repealed: bool = False,
    law_restored: bool = False,
) -> dict[str, dict]:
    """Simulate all 6 strategies over len(annual_path) years starting at inh_year.

    Each element of annual_path is a dict:
      {"g_a": float, "cpi": float, "prop13_f": float, "r_stock": float, "r_tsy": float, "rent_a_g": float}
    Enforces CA RTC 51(a)(2) (Proposition 8) every year: taxable_av = min(fbyv, current_fmv).
    Every option is liquidated/cashed out after all taxes at the end of the horizon for apples-to-apples wealth.
    Note: Because [PROPERTY_B]'s 2 already-rented units are identical across all 6 strategies (already owned
    by [BENEFICIARY]), we track incremental wealth from [PROPERTY_A] + [PROPERTY_B] Unit 3 housing choice.
    """
    n = len(annual_path)
    rent_mo_base = BASE["rent_a_mo_2026"] if rent_a_mo_2026 is None else rent_a_mo_2026

    # Initial sale proceeds if [PROPERTY_A] is sold immediately upon inheritance
    gross_sale_0 = fmv_a_at_inh * (1.0 - SELL_COST_A)
    if step_up_repealed:
        # Black-swan fiscal shock: carryover grantor basis (~fbyv_a_at_inh) instead of IRC 1014 step-up
        init_sale_tax = cap_gains_tax(max(0.0, gross_sale_0 - fbyv_a_at_inh))
    else:
        init_sale_tax = 0.0
    net_invest_0 = gross_sale_0 - init_sale_tax

    # 1. Pure Equity Strategy
    eq_val = net_invest_0
    eq_basis = net_invest_0
    for step in annual_path:
        div = eq_val * BASE["stock_div"]
        div_tax = div * T_DIV
        eq_val = eq_val * (1.0 + step["r_stock"]) - div_tax
        eq_basis += (div - div_tax)
    eq_end = eq_val - cap_gains_tax(max(0.0, eq_val - eq_basis))

    # 2. Pure CA-Tax-Exempt U.S. Treasury Rollover Strategy (31 U.S.C. 3124)
    tsy_val = net_invest_0
    for step in annual_path:
        after_tax_yield = step["r_tsy"] * (1.0 - T_TREASURY)
        tsy_val *= (1.0 + after_tax_yield)
    tsy_end = tsy_val

    # 3. 60/40 Equity + CA-Tax-Exempt Treasury Rebalanced Barbell
    b_eq = 0.60 * net_invest_0
    b_eq_basis = b_eq
    b_tsy = 0.40 * net_invest_0
    for step in annual_path:
        div = b_eq * BASE["stock_div"]
        div_tax = div * T_DIV
        b_eq = b_eq * (1.0 + step["r_stock"]) - div_tax
        b_eq_basis += (div - div_tax)
        b_tsy *= (1.0 + step["r_tsy"] * (1.0 - T_TREASURY))
        tot = b_eq + b_tsy
        target_eq = 0.60 * tot
        if target_eq < b_eq and b_eq > 0:
            # Trim equity gains to rebalance
            sell_amt = b_eq - target_eq
            gain_ratio = max(0.0, (b_eq - b_eq_basis) / b_eq)
            rebal_gain = sell_amt * gain_ratio
            tax_rebal = rebal_gain * T_LTCG_UNDER_1M
            b_eq -= sell_amt
            b_eq_basis *= (b_eq / (b_eq + sell_amt))
            b_tsy += (sell_amt - tax_rebal)
        elif target_eq > b_eq:
            buy_amt = target_eq - b_eq
            b_tsy -= buy_amt
            b_eq += buy_amt
            b_eq_basis += buy_amt
    barbell_end = (b_eq + b_tsy) - cap_gains_tax(max(0.0, b_eq - b_eq_basis))

    # Reinvestment rate path for annual real-estate cash flows (uses 60/40 after-tax annual return)
    reinv_rates = [0.60 * (s["r_stock"] - BASE["stock_div"] * T_DIV) + 0.40 * (s["r_tsy"] * (1.0 - T_TREASURY))
                   for s in annual_path]

    # Reassessed Prop 13 Base Year Value at inheritance
    if law_restored:
        base_av_live = fbyv_a_at_inh
        base_av_rent = fbyv_a_at_inh
    else:
        base_av_live = fbyv_a_at_inh + max(0.0, fmv_a_at_inh - fbyv_a_at_inh - prop19_cap_at_inh)
        base_av_rent = fmv_a_at_inh
        # Apply $7,000 Homeowners' Exemption (CA RTC 218) when [BENEFICIARY] occupies [PROPERTY_A]
        base_av_live = max(0.0, base_av_live - VERIFIED["homeowners_exemption"])

    results = {
        "sell_stock": {"wealth": eq_end, "first_cash": 0.0, "cash_sum": 0.0, "tax_first": 0.0, "prop8_years": 0},
        "sell_barbell": {"wealth": barbell_end, "first_cash": 0.0, "cash_sum": 0.0, "tax_first": 0.0, "prop8_years": 0},
        "sell_treasury": {"wealth": tsy_end, "first_cash": 0.0, "cash_sum": 0.0, "tax_first": 0.0, "prop8_years": 0},
    }

    basis_a_at_death = fbyv_a_at_inh if step_up_repealed else fmv_a_at_inh
    dep_annual = BASE["bldg_share_a"] * basis_a_at_death / VERIFIED["depreciation_years"]

    for opt_key in ("rent_a", "live_a_rent_u3", "live_a_keep_u3"):
        cur_fmv = fmv_a_at_inh
        cur_fbyv = base_av_rent if opt_key == "rent_a" else base_av_live
        cur_cpi_mult = cpi_mult_at_inh
        # Initial market rent at inh_year
        cur_rent_a_yr = rent_mo_base * 12.0 * ((1.0 + BASE["rent_a_growth"]) ** (inh_year - 2026))
        cur_u3_rent_yr = BASE["unit3_rent_mo_2026"] * 12.0 * ((1.0 + BASE["rent_a_growth"]) ** (inh_year - 2026))

        flows = []
        tax_first = 0.0
        prop8_years = 0

        for t, step in enumerate(annual_path):
            y = inh_year + t
            if t > 0:
                cur_fmv *= (1.0 + step["g_a"])
                cur_fbyv *= step["prop13_f"]
                cur_cpi_mult *= (1.0 + step["cpi"])
                cur_rent_a_yr *= (1.0 + step["rent_a_g"])
                # City B rent control caps sitting-tenant increases at 60% of CPI (min 0%)
                u3_cap = max(0.0, VERIFIED["cityb_rent_cpi_share"] * step["cpi"])
                cur_u3_rent_yr *= (1.0 + u3_cap)

            # CA RTC 51(a)(2) Proposition 8: taxable value is LESSER of factored base year value or current FMV
            if cur_fmv + 1.0 < cur_fbyv:
                taxable_av = cur_fmv
                prop8_years += 1
            else:
                taxable_av = cur_fbyv

            ptax = tax_a_from_av(taxable_av, y, fixed_mult=cur_cpi_mult)
            if t == 0:
                tax_first = ptax

            ins = INPUTS["a_ins_placeholder"] * ins_mult * cur_cpi_mult
            maint = BASE["maint_a_2026"] * cur_cpi_mult
            if seismic_shock_year_idx is not None and t == seismic_shock_year_idx:
                # Uninsured earthquake deductible/repair shock (CA Ins. Code 10081)
                maint += seismic_loss_frac_of_bldg * (BASE["bldg_share_a"] * cur_fmv)

            if opt_key == "rent_a":
                eff_rent = cur_rent_a_yr * (1.0 - BASE["vacancy"])
                # Tenant pays water/electricity; owner pays tax, landlord insurance, maintenance
                noi = eff_rent - ptax - ins - maint
                income_tax = T_ORD_COMBINED * (noi - dep_annual)
                cf = noi - income_tax
            elif opt_key == "live_a_rent_u3":
                # [BENEFICIARY] lives in [PROPERTY_A] and rents out [PROPERTY_B] Unit 3 under City B rent control
                u3_after_tax = cur_u3_rent_yr * (1.0 - BASE["vacancy"]) * (1.0 - T_ORD_COMBINED)
                water_a = INPUTS["a_water_yr"] * cur_cpi_mult
                el_a = elec_a(y, cur_cpi_mult)
                cf = u3_after_tax - (ptax + ins + maint + water_a + el_a)
            else:
                # [BENEFICIARY] lives in [PROPERTY_A] and keeps [PROPERTY_B] Unit 3 unrented (avoids rent control)
                water_a = INPUTS["a_water_yr"] * cur_cpi_mult
                el_a = elec_a(y, cur_cpi_mult)
                cf = -(ptax + ins + maint + water_a + el_a)

            flows.append(cf)

        # Compound annual cash flows forward to end of horizon
        fv_flows = 0.0
        for t, cf in enumerate(flows):
            comp = 1.0
            for k in range(t + 1, n):
                comp *= (1.0 + reinv_rates[k])
            fv_flows += cf * comp

        # End-of-window terminal sale after one final year's appreciation
        final_fmv = cur_fmv * (1.0 + annual_path[-1]["g_a"]) if n == 0 else cur_fmv
        # Note: in loop above, t=0 uses inh_year FMV and t=n-1 reflects n-1 steps; advance 1 final year to inh_year+n:
        if n > 0:
            final_fmv = fmv_a_at_inh
            for step in annual_path:
                final_fmv *= (1.0 + step["g_a"])

        net_sale = final_fmv * (1.0 - SELL_COST_A)
        if opt_key == "rent_a":
            accum_dep = dep_annual * n
            # Adjusted basis = basis_a_at_death - accum_dep; gain above basis_a_at_death is LTCG, accum_dep is Sec 1250
            econ_gain = max(0.0, net_sale - basis_a_at_death)
            recap = min(accum_dep, max(0.0, net_sale - (basis_a_at_death - accum_dep)))
            end_tax = cap_gains_tax(econ_gain, recap)
        else:
            # Owner-occupied: IRC 121 excludes $500,000 joint gain
            taxable_gain = max(0.0, net_sale - basis_a_at_death - VERIFIED["sec121_joint"])
            end_tax = cap_gains_tax(taxable_gain, 0.0)

        terminal_equity = net_sale - end_tax
        results[opt_key] = {
            "wealth": terminal_equity + fv_flows,
            "terminal_asset": terminal_equity,
            "first_cash": flows[0],
            "cash_sum": sum(flows),
            "tax_first": tax_first,
            "prop8_years": prop8_years,
        }

    return results


def constant_path(n: int, g_a: float, cpi: float = BASE["cpi"], r_stock: float = BASE["stock_total"],
                  r_tsy: float = BASE["treasury_yield"], rent_a_g: float = BASE["rent_a_growth"]) -> list[dict]:
    p13 = 1.0 + min(VERIFIED["prop13_max_cap"], max(-0.05, cpi))
    return [{"g_a": g_a, "cpi": cpi, "prop13_f": p13, "r_stock": r_stock, "r_tsy": r_tsy, "rent_a_g": rent_a_g}
            for _ in range(n)]


def bisect_root(fn, lo: float, hi: float) -> float:
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        if fn(mid) < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# 7. Build Complete Dataset & CSVs
# ---------------------------------------------------------------------------
def build_all() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_sources_json(DATA_DIR / "sources.json")

    g = BASE["g_base"]
    n = BASE["hold_years"]

    # --- A. 50-Year Baseline Year-by-Year Projections (2026 - 2076, 51 years) ---
    proj_50yr = []
    # Also compute 2045 inheritance branch inside the 50-year table so users see pre & post-2045 side by side
    fbyv_2045 = prop_a_fbyv(2045)
    fmv_2045 = prop_a_value(2045, g)
    cap_2045 = prop19_cap(2045, g)
    av_2045_live = max(0.0, fbyv_2045 + max(0.0, fmv_2045 - fbyv_2045 - cap_2045) - VERIFIED["homeowners_exemption"])
    av_2045_rent = fmv_2045

    for y in range(2026, 2077):
        cm = infl_factor(y, 2026)
        cm_b = infl_factor(y, 2025)
        av_a_unch = prop_a_fbyv(y)
        tax_a_unch = tax_a_from_av(av_a_unch, y, fixed_mult=cm_b)

        if y < 2045:
            av_a_post_live = av_a_unch
            tax_a_post_live = tax_a_unch
            av_a_post_rent = av_a_unch
            tax_a_post_rent = tax_a_unch
        else:
            f_post = (1.0 + VERIFIED["prop13_max_cap"]) ** (y - 2045)
            av_a_post_live = av_2045_live * f_post
            tax_a_post_live = tax_a_from_av(av_a_post_live, y, fixed_mult=cm_b)
            av_a_post_rent = av_2045_rent * f_post
            tax_a_post_rent = tax_a_from_av(av_a_post_rent, y, fixed_mult=cm_b)

        el_a = elec_a(y, cm)
        wat_a = INPUTS["a_water_yr"] * cm
        ins_a = INPUTS["a_ins_placeholder"] * cm
        mnt_a = BASE["maint_a_2026"] * cm

        # [PROPERTY_B]: ALREADY OWNED -> zero Prop 19 reset in 2045 or ever!
        av_b = prop_b_fbyv(y)
        tax_b = tax_b_from_av(av_b, y, fixed_mult=cm_b)
        rent_b_gross = INPUTS["b_rent_2units_mo"] * 12.0 * ((1.0 + VERIFIED["cityb_rent_cpi_share"] * BASE["cpi"]) ** (y - 2026))
        rent_b_eff = rent_b_gross * (1.0 - BASE["vacancy"])
        wat_b = INPUTS["b_water_yr"] * cm
        el_b = INPUTS["b_elec_yr"] * cm
        ins_b = INPUTS["b_ins_placeholder"] * cm
        mnt_b = BASE["maint_b_2026"] * cm
        noi_b = rent_b_eff - tax_b - wat_b - el_b - ins_b - mnt_b

        proj_50yr.append({
            "year": y,
            "a_val_low": r10(prop_a_value(y, BASE["g_low"])),
            "a_val_base": r10(prop_a_value(y, BASE["g_base"])),
            "a_val_high": r10(prop_a_value(y, BASE["g_high"])),
            "a_av_unchanged": r10(av_a_unch),
            "a_tax_unchanged": r10(tax_a_unch),
            "a_av_2045_live": r10(av_a_post_live),
            "a_tax_2045_live": r10(tax_a_post_live),
            "a_av_2045_rent": r10(av_a_post_rent),
            "a_tax_2045_rent": r10(tax_a_post_rent),
            "a_water": r10(wat_a),
            "a_elec": r10(el_a),
            "a_ins_scen": r10(ins_a),
            "a_maint": r10(mnt_a),
            "b_val_base": r10(prop_b_value(y, BASE["g_base"])),
            "b_av_protected": r10(av_b),
            "b_tax_protected": r10(tax_b),
            "b_gross_rent": r10(rent_b_gross),
            "b_op_costs": r10(tax_b + wat_b + el_b + ins_b + mnt_b + (rent_b_gross - rent_b_eff)),
            "b_net_cashflow": r10(noi_b),
        })

    # --- B. 50-Year Actual California Historical Cycle Replay (2026-2076) ---
    hist_replay_rows = []
    cur_val_a = float(INPUTS["a_value_2026"])
    cur_fbyv_a = float(INPUTS["a_av_2026"])
    cur_val_b = float(INPUTS["b_value_2026"])
    cur_fbyv_b = float(INPUTS["b_av_2025"]) * 1.02
    cur_cpi_idx = 1.0
    cur_rent_b = INPUTS["b_rent_2units_mo"] * 12.0
    # Suppose inheritance occurs at 2045 (index 19 in 2026..2075)
    reassessed_fbyv_a_rent = None
    for idx, (h_yr, h_g, h_cpi, h_p13, h_gs10, h_sp) in enumerate(HIST_50YR):
        sim_yr = 2027 + idx
        cur_val_a *= (1.0 + h_g)
        cur_val_b *= (1.0 + h_g)
        cur_cpi_idx *= (1.0 + h_cpi)
        cur_fbyv_a *= h_p13
        cur_fbyv_b *= h_p13
        cur_rent_b *= (1.0 + max(0.0, VERIFIED["cityb_rent_cpi_share"] * h_cpi))

        if sim_yr == 2045:
            reassessed_fbyv_a_rent = cur_val_a
        elif sim_yr > 2045 and reassessed_fbyv_a_rent is not None:
            reassessed_fbyv_a_rent *= h_p13

        eff_av_a = min(cur_val_a, reassessed_fbyv_a_rent if reassessed_fbyv_a_rent is not None else cur_fbyv_a)
        prop8_active = reassessed_fbyv_a_rent is not None and (cur_val_a + 1.0 < reassessed_fbyv_a_rent)
        tax_a_sim = tax_a_from_av(eff_av_a, sim_yr, fixed_mult=cur_cpi_idx)
        eff_av_b = min(cur_val_b, cur_fbyv_b)
        tax_b_sim = tax_b_from_av(eff_av_b, sim_yr, fixed_mult=cur_cpi_idx)

        hist_replay_rows.append({
            "sim_year": sim_yr,
            "analog_hist_year": h_yr,
            "ca_hpi_pct": round(h_g * 100.0, 2),
            "ca_cpi_pct": round(h_cpi * 100.0, 2),
            "prop13_factor": h_p13,
            "tsy_10y_pct": round(h_gs10 * 100.0, 2),
            "a_market_val": r10(cur_val_a),
            "a_taxable_av": r10(eff_av_a),
            "a_prop8_reduced": "Yes" if prop8_active else "No",
            "a_tax": r10(tax_a_sim),
            "b_market_val": r10(cur_val_b),
            "b_tax_protected": r10(tax_b_sim),
            "b_gross_rent": r10(cur_rent_b),
        })

    # --- C. Ownership-Distinction Quantitative Proof (2026 - 2076) ---
    ownership_rows = []
    for yy in (2026, 2027, 2035, 2040, 2045, 2050, 2060, 2076):
        if yy == 2026:
            excl = float(VERIFIED["fed_excl_2026"])
        else:
            excl = VERIFIED["fed_excl_2027"] * ((1.0 + BASE["excl_index"]) ** (yy - 2027))
        va = prop_a_value(yy, g)
        vb = prop_b_value(yy, g)
        # True single-property estate ([PROPERTY_A] only) vs erroneous two-property estate
        headroom_true_single = excl - va
        headroom_wrong_both = excl - (va + vb)
        headroom_true_couple = 2.0 * excl - va
        headroom_half_cut_true = (0.5 * excl) - va
        headroom_half_cut_wrong = (0.5 * excl) - (va + vb)

        # Property B annual tax preserved because already owned vs hypothetical estate reset
        cm_b = infl_factor(yy, 2025)
        tax_b_kept = tax_b_from_av(prop_b_fbyv(yy), yy, fixed_mult=cm_b)
        tax_b_if_reset = tax_b_from_av(vb, yy, fixed_mult=cm_b)

        # Embedded capital gains tax locked inside already-owned [PROPERTY_B] if sold (no IRC 1014 step-up)
        # 1/3 owner-occupied (eligible for Sec 121 joint $500k), 2/3 rental (no Sec 121 + depreciation recapture)
        net_b_sale = vb * (1.0 - 0.05 - (0.0225 if vb >= 5_000_000 else 0.0075))
        gain_b_total = max(0.0, net_b_sale - INPUTS["b_assumed_orig_basis"])
        gain_b_owner_third = max(0.0, gain_b_total / 3.0 - VERIFIED["sec121_joint"])
        gain_b_rental_twothirds = gain_b_total * (2.0 / 3.0)
        recap_b = (2.0 / 3.0) * BASE["bldg_share_b"] * INPUTS["b_assumed_orig_basis"]
        tax_if_sell_b = cap_gains_tax(gain_b_owner_third + gain_b_rental_twothirds, recap_b)

        ownership_rows.append({
            "year": yy,
            "status": "Verified" if yy <= 2027 else "Scenario",
            "fed_excl_single": r10(excl),
            "fed_excl_couple": r10(2.0 * excl),
            "val_a_in_estate": r10(va),
            "val_b_outside_estate": r10(vb),
            "cash_headroom_true_single": r10(headroom_true_single),
            "cash_headroom_prior_both": r10(headroom_wrong_both),
            "headroom_gain_from_distinction": r10(vb),
            "cash_headroom_couple": r10(headroom_true_couple),
            "cash_headroom_50pct_cut_true": r10(headroom_half_cut_true),
            "cash_headroom_50pct_cut_both": r10(headroom_half_cut_wrong),
            "b_tax_already_owned": r10(tax_b_kept),
            "b_tax_if_inherited": r10(tax_b_if_reset),
            "b_annual_tax_saved": r10(tax_b_if_reset - tax_b_kept),
            "b_sale_tax_no_stepup": r10(tax_if_sell_b),
        })

    # --- D. Standard Decision Tables (2040, 2045, 2050 x 3%, 4%, 5.5%) ---
    decision_blocks = []
    decision_csv_rows = []
    for y0 in BASE["inh_years"]:
        for gg in (BASE["g_low"], BASE["g_base"], BASE["g_high"]):
            fmv0 = prop_a_value(y0, gg)
            fbyv0 = prop_a_fbyv(y0)
            cap0 = prop19_cap(y0, gg)
            cm0 = infl_factor(y0, 2026)
            res = simulate_regime(y0, fmv0, fbyv0, cap0, cm0, constant_path(n, gg))
            best_w = max(v["wealth"] for v in res.values())
            defl_end = infl_factor(y0 + n, 2026)
            rows = []
            for skey, sname in STRATEGIES:
                rv = res[skey]
                row = {
                    "option": skey,
                    "name": sname,
                    "wealth_nominal": r10(rv["wealth"]),
                    "wealth_real_2026": r10(rv["wealth"] / defl_end),
                    "gap_vs_best": r10(rv["wealth"] - best_w),
                    "gap_real_2026": r10((rv["wealth"] - best_w) / defl_end),
                    "first_yr_cashflow": r10(rv["first_cash"]),
                    "ten_yr_cashflow": r10(rv["cash_sum"]),
                    "first_yr_tax_a": r10(rv["tax_first"]),
                }
                rows.append(row)
                decision_csv_rows.append({"inheritance_year": y0, "house_growth": gg, **row})
            winner_key = max(res, key=lambda k: res[k]["wealth"])
            live_cost_mo_real = ((best_w - res["live_a_rent_u3"]["wealth"]) / (12.0 * n)) / defl_end
            decision_blocks.append({
                "year": y0,
                "g": gg,
                "fmv_a": r10(fmv0),
                "net_sale_proceeds": r10(fmv0 * (1.0 - SELL_COST_A)),
                "prop19_cap": r10(cap0),
                "winner": dict(STRATEGIES)[winner_key],
                "live_cost_mo_real_2026": r10(live_cost_mo_real),
                "rows": rows,
            })

    # --- E. Break-Evens for 2045 Baseline ---
    fmv45 = prop_a_value(2045, g)
    fbyv45 = prop_a_fbyv(2045)
    cap45 = prop19_cap(2045, g)
    cm45 = infl_factor(2045, 2026)

    be_stock_vs_rent = bisect_root(
        lambda rs: simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g, r_stock=rs))["sell_stock"]["wealth"]
        - simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g, r_stock=rs))["rent_a"]["wealth"],
        0.0, 0.20,
    )
    be_house_g_vs_stock = bisect_root(
        lambda gx: simulate_regime(2045, prop_a_value(2045, gx), fbyv45, prop19_cap(2045, gx), cm45, constant_path(n, gx))["rent_a"]["wealth"]
        - simulate_regime(2045, prop_a_value(2045, gx), fbyv45, prop19_cap(2045, gx), cm45, constant_path(n, gx))["sell_stock"]["wealth"],
        0.0, 0.15,
    )
    be_rent_mo_vs_stock = bisect_root(
        lambda rm: simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g), rent_a_mo_2026=rm)["rent_a"]["wealth"]
        - simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g))["sell_stock"]["wealth"],
        2_000.0, 50_000.0,
    )
    be_rent_mo_vs_barbell = bisect_root(
        lambda rm: simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g), rent_a_mo_2026=rm)["rent_a"]["wealth"]
        - simulate_regime(2045, fmv45, fbyv45, cap45, cm45, constant_path(n, g))["sell_barbell"]["wealth"],
        2_000.0, 50_000.0,
    )
    breakevens = {
        "stock_return_pct": round(be_stock_vs_rent * 100.0, 2),
        "house_growth_pct": round(be_house_g_vs_stock * 100.0, 2),
        "rent_a_mo_2026_vs_stock": r10(be_rent_mo_vs_stock),
        "rent_a_mo_2026_vs_barbell": r10(be_rent_mo_vs_barbell),
    }

    # --- F. Dedicated 10-Regime Black-Swan & Historical Multi-Cycle Stress Suite (2045 Anchor) ---
    # Build realistic year-by-year 10-year paths anchored to verified historical dislocations:
    def hist_slice_path(start_idx: int, length: int = 10) -> list[dict]:
        out = []
        for i in range(length):
            _, hg, hcpi, hp13, hgs10, hsp = HIST_50YR[(start_idx + i) % len(HIST_50YR)]
            out.append({"g_a": hg, "cpi": hcpi, "prop13_f": hp13, "r_stock": hsp, "r_tsy": hgs10, "rent_a_g": max(-0.05, hcpi)})
        return out

    # BS-0: Smooth Baseline (4% house, 2.5% CPI, 7% stock, 4.98% Treasury)
    p_bs0 = constant_path(10, BASE["g_base"])

    # BS-1a: Actual Historical 1977-1986 Stagflation + Volcker Disinflation Replay (exact FRED/BOE series)
    p_bs1a = hist_slice_path(0, 10)   # 1977..1986

    # BS-1b: Actual Historical 2007-2016 Great Recession & Housing Crash Replay (exact FRED/BOE series: -41% CA HPI, -37% S&P 2008, -0.24% Prop 13 deflation 2010)
    p_bs1b = hist_slice_path(30, 10)  # 2007..2016

    # BS-2: Prolonged 1970s-Style Stagflation Wave (CPI 9%-12%, 10-Yr Tsy 9.5%, Stocks 2% nominal yrs 1-5 then 7%, Housing 6% nominal, Prop 13 2% cap binding)
    p_bs2 = [
        {"g_a": 0.06, "cpi": 0.095, "prop13_f": 1.02, "r_stock": -0.08, "r_tsy": 0.085, "rent_a_g": 0.075},
        {"g_a": 0.07, "cpi": 0.115, "prop13_f": 1.02, "r_stock": -0.04, "r_tsy": 0.098, "rent_a_g": 0.085},
        {"g_a": 0.065, "cpi": 0.105, "prop13_f": 1.02, "r_stock": 0.04, "r_tsy": 0.105, "rent_a_g": 0.080},
        {"g_a": 0.055, "cpi": 0.085, "prop13_f": 1.02, "r_stock": 0.05, "r_tsy": 0.095, "rent_a_g": 0.065},
        {"g_a": 0.045, "cpi": 0.065, "prop13_f": 1.02, "r_stock": 0.06, "r_tsy": 0.085, "rent_a_g": 0.050},
    ] + [{"g_a": 0.045, "cpi": 0.040, "prop13_f": 1.02, "r_stock": 0.075, "r_tsy": 0.065, "rent_a_g": 0.040} for _ in range(5)]

    # BS-3: Immediate Sequence-of-Returns Crash Right After Inheritance (-50% stocks & -35% housing over Yrs 1-2, Prop 8 tax relief active, slow recovery)
    p_bs3 = [
        {"g_a": -0.20, "cpi": 0.015, "prop13_f": 1.015, "r_stock": -0.35, "r_tsy": 0.045, "rent_a_g": -0.08},
        {"g_a": -0.1875, "cpi": -0.005, "prop13_f": 0.995, "r_stock": -0.23, "r_tsy": 0.032, "rent_a_g": -0.05},
        {"g_a": 0.00, "cpi": 0.010, "prop13_f": 1.010, "r_stock": 0.12, "r_tsy": 0.030, "rent_a_g": 0.00},
        {"g_a": 0.04, "cpi": 0.020, "prop13_f": 1.020, "r_stock": 0.11, "r_tsy": 0.035, "rent_a_g": 0.025},
    ] + [{"g_a": 0.045, "cpi": 0.025, "prop13_f": 1.020, "r_stock": 0.085, "r_tsy": 0.042, "rent_a_g": 0.030} for _ in range(6)]

    # BS-4: Inheritance *AT* a -35% Housing Trough (2045 FMV depressed -35% -> low Prop 13 base year locked in forever, followed by +7.5%/yr CA housing rebound & +7.5% stocks)
    p_bs4 = [
        {"g_a": 0.085, "cpi": 0.020, "prop13_f": 1.02, "r_stock": 0.075, "r_tsy": 0.040, "rent_a_g": 0.04}
        for _ in range(5)
    ] + [
        {"g_a": 0.065, "cpi": 0.025, "prop13_f": 1.02, "r_stock": 0.070, "r_tsy": 0.045, "rent_a_g": 0.035}
        for _ in range(5)
    ]

    # BS-5: Localized County A Tech-Corridor Bust (1990-96 / 2000-03 Regional Analogue: -35% local home price & -20% local rent, while diversified US stocks/Treasuries earn normal returns)
    p_bs5 = [
        {"g_a": -0.18, "cpi": 0.025, "prop13_f": 1.02, "r_stock": 0.065, "r_tsy": 0.0498, "rent_a_g": -0.12},
        {"g_a": -0.15, "cpi": 0.025, "prop13_f": 1.02, "r_stock": 0.070, "r_tsy": 0.0498, "rent_a_g": -0.10},
        {"g_a": -0.06, "cpi": 0.025, "prop13_f": 1.02, "r_stock": 0.070, "r_tsy": 0.0498, "rent_a_g": 0.00},
    ] + [{"g_a": 0.025, "cpi": 0.025, "prop13_f": 1.02, "r_stock": 0.070, "r_tsy": 0.0498, "rent_a_g": 0.025} for _ in range(7)]

    # BS-6: Lost Equity Decade & Deflationary Japan/1930s-Lite Slump (0% annual stock return for 10 yrs, 1.0% CPI, 2.5% housing, 3.8% initial -> 2.5% Treasury)
    p_bs6 = [{"g_a": 0.025, "cpi": 0.010, "prop13_f": 1.010, "r_stock": 0.00, "r_tsy": 0.032, "rent_a_g": 0.015} for _ in range(10)]

    # BS-7: California Insurance Crisis (4x Premiums) + Major Uninsured Year-4 Seismic Event (20% of Building Value Repair/Deductible under CA Ins. Code 10081, -15% temporary local price shock)
    p_bs7 = constant_path(10, BASE["g_base"])
    p_bs7[3] = {"g_a": -0.15, "cpi": 0.035, "prop13_f": 1.02, "r_stock": 0.06, "r_tsy": 0.0498, "rent_a_g": 0.00}
    p_bs7[4] = {"g_a": 0.08, "cpi": 0.030, "prop13_f": 1.02, "r_stock": 0.07, "r_tsy": 0.0498, "rent_a_g": 0.04}

    # BS-8: Federal Fiscal/Tax Cliff Shock (IRC 1014 Step-Up Repealed at Death -> Carryover Basis Taxed at 37.1% + Higher Rate Regime 6.5% Tsy)
    p_bs8 = constant_path(10, BASE["g_base"], r_tsy=0.062)

    raw_regimes = [
        ("BS-0", "Smooth Baseline Reference (4% housing, 2.5% CPI, 7% stock, 4.98% Tsy)", "fred_casthpi", fmv45, p_bs0, {}),
        ("BS-1A", "Actual Historical Replay: 1977-1986 Stagflation & Rate Peak (17.3% CA CPI, 13.9% Tsy)", "boe_lta26002", fmv45, p_bs1a, {}),
        ("BS-1B", "Actual Historical Replay: 2007-2016 Great Recession Crash (-41% CA HPI, -37% S&P, Prop 8)", "fred_casthpi", fmv45, p_bs1b, {}),
        ("BS-2", "1970s-Style Stagflation Wave (8.5%-11.5% CPI, Prop 13 2% Cap vs 60%-CPI Rent Squeeze)", "fed_gi", fmv45, p_bs2, {}),
        ("BS-3", "Sequence-of-Returns Crash Right After Inheritance (-50% Stocks, -35% Housing, Prop 8 Relief)", "fed_gr", fmv45, p_bs3, {}),
        ("BS-4", "Inheritance AT a -35% Housing Trough (Low Reassessed Prop 13 Base + +7.5%/yr Recovery)", "rtc_51", fmv45 * 0.65, p_bs4, {}),
        ("BS-5", "Localized County A Tech-Corridor Bust (-35% Local Price / -20% Rent; Normal National Markets)", "fred_casthpi", fmv45, p_bs5, {}),
        ("BS-6", "Lost Equity Decade & Deflationary Slump (0% 10-Yr Stock Return, 1% CPI, Sub-2% Prop 13)", "fed_1929", fmv45, p_bs6, {}),
        ("BS-7", "CA Insurance Crisis (4x Premium) + Uninsured Year-4 Seismic Shock (20% Bldg Loss)", "ins_10081", fmv45, p_bs7, {"ins_mult": 4.0, "seismic_shock_year_idx": 3, "seismic_loss_frac_of_bldg": 0.20}),
        ("BS-8", "Fiscal Cliff Tax Shock: IRC 1014 Basis Step-Up Repealed at Death (Carryover Basis Taxed)", "irs_rr2023_2", fmv45, p_bs8, {"step_up_repealed": True}),
    ]

    black_swan_results = []
    black_swan_csv = []
    for rid, rtitle, rsrc, fmv_init, rpath, extra_kw in raw_regimes:
        sim = simulate_regime(2045, fmv_init, fbyv45, cap45, cm45, rpath, **extra_kw)
        cum_cpi = infl_factor(2045, 2026)
        for s in rpath:
            cum_cpi *= (1.0 + s["cpi"])
        best_key = max(sim, key=lambda k: sim[k]["wealth"])
        best_val = sim[best_key]["wealth"]
        entry = {
            "id": rid,
            "title": rtitle,
            "source_id": rsrc,
            "fmv_2045_start": r10(fmv_init),
            "prop8_years_rent": sim["rent_a"]["prop8_years"],
            "winner_key": best_key,
            "winner_label": dict(STRATEGIES)[best_key].split(";")[0],
            "sell_stock": r10(sim["sell_stock"]["wealth"]),
            "sell_barbell": r10(sim["sell_barbell"]["wealth"]),
            "sell_treasury": r10(sim["sell_treasury"]["wealth"]),
            "rent_a": r10(sim["rent_a"]["wealth"]),
            "live_a_rent_u3": r10(sim["live_a_rent_u3"]["wealth"]),
            "live_a_keep_u3": r10(sim["live_a_keep_u3"]["wealth"]),
            "sell_stock_real": r10(sim["sell_stock"]["wealth"] / cum_cpi),
            "sell_barbell_real": r10(sim["sell_barbell"]["wealth"] / cum_cpi),
            "sell_treasury_real": r10(sim["sell_treasury"]["wealth"] / cum_cpi),
            "rent_a_real": r10(sim["rent_a"]["wealth"] / cum_cpi),
            "live_a_rent_u3_real": r10(sim["live_a_rent_u3"]["wealth"] / cum_cpi),
            "barbell_vs_rent": r10(sim["sell_barbell"]["wealth"] - sim["rent_a"]["wealth"]),
        }
        black_swan_results.append(entry)
        black_swan_csv.append(entry)

    # --- G. Write Clean RFC-4180 CSVs & JSON ---
    def write_csv(filename: str, rows: list[dict]) -> None:
        with (DATA_DIR / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv("projections_50yr.csv", proj_50yr)
    write_csv("historical_replay_50yr.csv", hist_replay_rows)
    write_csv("ownership_distinction.csv", ownership_rows)
    write_csv("decision_matrix.csv", decision_csv_rows)
    write_csv("black_swan_regimes.csv", black_swan_csv)

    payload = {
        "generated_by": "analysis/tools/model.py",
        "reviewed_on": "2026-11-11",
        "inputs": {k: (r10(v) if isinstance(v, (int, float)) and abs(v) >= 10 else v) for k, v in INPUTS.items()},
        "fixed_charges_2025": {"a": FIXED_CHARGES_A_2025, "b": FIXED_CHARGES_B_2025},
        "rates": {
            "sell_cost_a_pct": round(SELL_COST_A * 100.0, 2),
            "t_ord_pct": round(T_ORD_COMBINED * 100.0, 2),
            "t_treasury_pct": round(T_TREASURY * 100.0, 2),
            "t_div_pct": round(T_DIV * 100.0, 2),
            "t_ltcg_under_1m_pct": round(T_LTCG_UNDER_1M * 100.0, 2),
            "t_ltcg_over_1m_pct": round(T_LTCG_OVER_1M * 100.0, 2),
            "t_recap_over_1m_pct": round(T_RECAP_OVER_1M * 100.0, 2),
        },
        "breakevens_2045": breakevens,
        "ownership_distinction": ownership_rows,
        "decision_blocks": decision_blocks,
        "black_swan_regimes": black_swan_results,
        "projections_50yr": proj_50yr,
        "historical_replay_50yr": hist_replay_rows,
    }
    (DATA_DIR / "model.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    m = build_all()
    print("=== 2045 Baseline (4% housing, 10-yr horizon) ===")
    b45 = next(b for b in m["decision_blocks"] if b["year"] == 2045 and abs(b["g"] - 0.04) < 1e-9)
    for r in b45["rows"]:
        print(f"  {r['option']:16s} nominal={r['wealth_nominal']:>12,d}  real2026={r['wealth_real_2026']:>11,d}  tax_y1={r['first_yr_tax_a']:>8,d}")
    print("=== Break-evens (2045) ===", m["breakevens_2045"])
    print("=== Black-Swan Regime Winners ===")
    for bs in m["black_swan_regimes"]:
        print(f"  {bs['id']:6s} winner={bs['winner_key']:16s} stock={bs['sell_stock']:>11,d} barbell={bs['sell_barbell']:>11,d} tsy={bs['sell_treasury']:>11,d} rent={bs['rent_a']:>11,d} live={bs['live_a_rent_u3']:>11,d} (Prop8 yrs={bs['prop8_years_rent']})")
