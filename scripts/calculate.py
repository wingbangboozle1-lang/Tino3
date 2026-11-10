#!/usr/bin/env python3
"""
Reproducible projection model — Cupertino (95014) & San Francisco (94122)
All money outputs rounded to nearest $10 per project requirement.
ASSUMPTIONS are labelled; verified law/rate inputs cite official sources in data/sources.csv.
Run: python3 scripts/calculate.py
"""
import csv, json, math
from pathlib import Path

def r10(x): return int(round(x/10)*10)

# --- Verified / user-provided inputs (see sources.csv for citations) ---
cup = {"market_2026": 3_100_000, "assessed_2026": 550_537, "tax_2025": 7_207, "assessed_2025": 539_743}
sf  = {"market_2026": 1_800_000, "assessed_2025": 114_248, "tax_2025": 2_439}
cup_rate = cup["tax_2025"]/cup["assessed_2025"]   # 1.335% implied effective rate (user data)
sf_rate  = sf["tax_2025"]/sf["assessed_2025"]     # 2.135% implied — FLAGGED anomaly (see flagged-review)
PROP13_CAP = 0.02          # BOE: assessed growth cap 2%/yr
PROP19_CAP = 1_000_000     # BOE: $1M over factored base (biennially adjusted; model uses base $1M, conservative)
ESTATE_EXEMPTION_2026 = 15_000_000  # IRS Rev. Proc. 2025-32

# --- ASSUMPTIONS (not verified facts; sensitivity shown) ---
GROWTH_SCENARIOS = {"Low 2%":0.02, "Base 3%":0.03, "High 4%":0.04}
STOCK_SCENARIOS  = {"Savings 4%":0.04, "Stocks 7%":0.07, "Stocks 10%":0.10}
MAINT_CUP, MAINT_SF = 0.005, 0.01   # % of market value /yr — ASSUMPTION
INS_CUP, INS_SF = 2_340, 2_340      # CDI 2025 all-forms avg benchmark — quote needed, flagged
WATER_CUP_MO, WATER_SF_MO = 120, 365  # midpoints of user ranges ($100-150, $330-400)
ELEC_CUP_MO, ELEC_SF_MO = -10, 50     # Cupertino solar credit midpoint -$10/mo (user); SF $30-70 midpoint
SF_RENT_MO = 7_150
RENT_GROWTH = 0.03
SELL_COST_PCT = 0.06  # ASSUMPTION (agent + closing)

rows=[]
for year in range(2026, 2051):
    n = year-2026
    cup_assessed = cup["assessed_2026"]*(1+PROP13_CAP)**n
    sf_assessed  = sf["assessed_2025"]*(1+PROP13_CAP)**(year-2025)
    row={"year":year}
    for label,g in GROWTH_SCENARIOS.items():
        key=label.split()[0].lower()
        row[f"cup_market_{key}"]=r10(cup["market_2026"]*(1+g)**n)
        row[f"sf_market_{key}"]=r10(sf["market_2026"]*(1+g)**n)
    row["cup_assessed_no_transfer"]=r10(cup_assessed)
    row["sf_assessed_no_transfer"]=r10(sf_assessed)
    row["cup_tax_no_transfer"]=r10(cup_assessed*cup_rate)
    row["sf_tax_no_transfer"]=r10(sf_assessed*sf_rate)
    rows.append(row)

# Inheritance scenarios at 2040 / 2045 / 2050 (Base 3% growth)
inherit=[]
for Y in (2040,2045,2050):
    n=Y-2026
    for name,prop,rate in (("Cupertino",cup,cup_rate),("San Francisco",sf,sf_rate)):
        base_assessed = (prop["assessed_2026"]*(1.02**n) if name=="Cupertino" else prop["assessed_2025"]*(1.02**(Y-2025)))
        market = prop["market_2026"]*(1.03**n)
        movein_assessed = base_assessed + max(0, market-base_assessed-PROP19_CAP)
        inherit.append({
            "inherit_year":Y,"property":name,
            "market_at_inheritance":r10(market),
            "factored_base_no_transfer":r10(base_assessed),
            "assessed_if_move_in_prop19":r10(movein_assessed),
            "tax_if_move_in":r10(movein_assessed*rate),
            "assessed_if_rent_or_sell_full_reassess":r10(market),
            "tax_if_rent_full_reassess":r10(market*rate),
            "tax_if_no_transfer_hypothetical":r10(base_assessed*rate),
            "effective_rate_used":round(rate*100,3),
        })

# Cupertino annual carrying costs at inheritance (Base case) + break-even rent
carry=[]
for Y in (2040,2045,2050):
    n=Y-2026
    market=cup["market_2026"]*(1.03**n)
    base_assessed=cup["assessed_2026"]*(1.02**n)
    movein_assessed=base_assessed+max(0,market-base_assessed-PROP19_CAP)
    for scenario,assessed in (("Live in (Prop 19 move-in)",movein_assessed),("Rent (full reassessment)",market)):
        tax=assessed*cup_rate; ins=INS_CUP; water=WATER_CUP_MO*12; elec=ELEC_CUP_MO*12; maint=market*MAINT_CUP
        total=tax+ins+water+elec+maint
        carry.append({"year":Y,"scenario":scenario,"property_tax":r10(tax),"insurance":r10(ins),
                      "water":r10(water),"electricity_solar_credit":r10(elec),"maintenance_assumption":r10(maint),
                      "total_annual_cost":r10(total),"break_even_monthly_rent":r10(total/12)})

# SF rental P&L at inheritance (Base case)
sf_pl=[]
for Y in (2040,2045,2050):
    n=Y-2026
    market=sf["market_2026"]*(1.03**n)
    rent_yr=SF_RENT_MO*12*((1+RENT_GROWTH)**n)
    tax_full=market*sf_rate  # inherited rental = full reassessment (Prop 19 eliminates rental exclusion)
    costs=tax_full+INS_SF+WATER_SF_MO*12+ELEC_SF_MO*12+market*MAINT_SF
    sf_pl.append({"year":Y,"gross_rent":r10(rent_yr),"property_tax_full_reassess":r10(tax_full),
                  "insurance":r10(INS_SF),"water":r10(WATER_SF_MO*12),"electricity":r10(ELEC_SF_MO*12),
                  "maintenance_assumption":r10(market*MAINT_SF),"total_costs":r10(costs),
                  "net_before_income_tax":r10(rent_yr-costs)})

# Sell Cupertino at inheritance & reinvest 10 years (step-up basis => ~$0 gain if sold promptly; selling costs only)
reinvest=[]
for Y in (2040,2045,2050):
    market=cup["market_2026"]*(1.03**(Y-2026))
    net=market*(1-SELL_COST_PCT)
    for label,ret in STOCK_SCENARIOS.items():
        reinvest.append({"sell_year":Y,"net_proceeds_after_selling_costs":r10(net),
                         "return_assumption":label,"value_10y_later":r10(net*(1+ret)**10),
                         "value_20y_later":r10(net*(1+ret)**20)})

# Estate threshold check (houses only; cash inheritance amount UNVERIFIED/blank)
estate=[]
for Y in (2026,2040,2045,2050):
    n=Y-2026
    combined=cup["market_2026"]*(1.03**n)+sf["market_2026"]*(1.03**n)
    estate.append({"year":Y,"combined_house_market_base3":r10(combined),
                   "federal_exemption_2026_per_person":ESTATE_EXEMPTION_2026,
                   "headroom_houses_only":r10(ESTATE_EXEMPTION_2026-combined)})

Path("data").mkdir(exist_ok=True)
def write_csv(name, data):
    with open(f"data/{name}","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
write_csv("projections.csv",rows); write_csv("inheritance_scenarios.csv",inherit)
write_csv("cupertino_carrying_costs.csv",carry); write_csv("sf_rental_pl.csv",sf_pl)
write_csv("sell_and_reinvest.csv",reinvest); write_csv("estate_threshold.csv",estate)
summary={"cup_rate_pct":round(cup_rate*100,3),"sf_rate_pct":round(sf_rate*100,3),
         "inheritance":inherit,"carry":carry,"sf_pl":sf_pl,"reinvest":reinvest,"estate":estate}
json.dump(summary,open("data/summary.json","w"),indent=2)
print(f"Cupertino implied rate {cup_rate*100:.3f}% | SF implied rate {sf_rate*100:.3f}% (FLAGGED)")
for r in inherit: print(r)
for r in carry: print(r)
for r in sf_pl: print(r)
print("Wrote data/*.csv + data/summary.json")
