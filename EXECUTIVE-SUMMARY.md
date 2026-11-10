# Executive summary — Cupertino and San Francisco house inheritance

**Internal working document.** Model v1.0.0, built 2026-11-10. All currency rounded to the nearest $10 except where a statutory amount is quoted verbatim. No personal identifying information is included. Not legal, tax or investment advice.

---

## 1. What is being inherited

| Property | ZIP | Estimated value, Nov 2026 | Assessed value | Current property tax | Basis |
|---|---|---|---|---|---|
| Cupertino single-family home | 95014 | $3,100,000 | $550,540 (2026) | $7,210 (2025-26) | owner estimate / tax bills |
| San Francisco 3-unit building (Outer Sunset) | 94122 | $1,800,000 | $114,250 (2025) | $2,440 (2025) | owner estimate / tax bills |

Two of the three San Francisco units are let for $7,150 a month combined; the third is vacant, which is what makes it possible to live there without displacing a tenant. A cash inheritance accompanies the real estate.

The brief does not say which house is the parents' principal residence. **That single fact decides which house can keep a low property-tax base.** The base case assumes Cupertino; every result is also produced with the assumption reversed.

## 2. The law that governs the transfer

| Question | Answer | Verified against |
|---|---|---|
| Is an inheritance taxable in California? | No state estate tax and no state inheritance tax. | LAO, California's Tax System: A Primer (S06); FTB bill analysis SB 378 (S07) |
| Is there a federal estate tax? | Yes, above $15,000,000 per person for 2026 ($30,000,000 for a married couple with portability), at 40%. | IRS IR-2025-103, Rev. Proc. 2025-32 (S03) |
| Does the property-tax base pass to the child? | Only for the parents' principal residence, only if the child moves in within one year, and only up to the base plus $1,044,586 for transfers from 16 February 2025 to 15 February 2027. | BOE Prop 19 guidance (S01); BOE LTA 2025/009 (S02) |
| Does the San Francisco rental qualify? | No. Prop 19 removed the exclusion for any property that is not a principal residence. | BOE Prop 19 guidance (S01) |
| Is the gain taxed when the child sells? | No, to the extent of the step-up: basis becomes date-of-death value. | IRS Publication 551 (S04), Publication 559 (S18) |
| How much advance appreciation escapes capital gains? | $5,423,560 between 2026 and 2045 on these two houses, equal to about $2,012,140 of tax at a 37.1% blended rate. | model |
| Is Prop 19 being repealed? | No. The 2026 repeal initiative failed to qualify; the Secretary of State recorded the failure on 18 May 2026. | CA Secretary of State memo 26138 (S12) |

**Three consequences drive everything else:**

1. The San Francisco rental receives no property-tax relief at all — it is reassessed to market value.
2. Cupertino's base is $550,540 against a value of $3,100,000. The Prop 19 allowance of roughly $1.04M is nowhere near that gap, so moving in saves money but does not restore the parents' bill.
3. Nothing is automatic. The relief is claimed on Form BOE-19-P, within three years, and it fails if the child does not occupy the house within one year and claim the homeowners' exemption.

## 3. What it costs after inheritance

Combined property tax goes from $9,700 a year today to **$103,970 a year** once both houses are reassessed in 2045 — a 10.7-fold increase. Running costs on top: water, electricity, insurance and maintenance.

Once reassessed, the two properties stop behaving alike:

| 2045, at 4%/yr | Cupertino | San Francisco |
|---|---|---|
| Value | $6,531,230 | $3,792,330 |
| Property tax after reassessment | $85,500 | $44,850 |
| Gross rent if let | $142,530 | $167,130 |
| Net cash yield on value | 0.49% | 2.02% |

The San Francisco building returns roughly four times as much on a house worth a little over half as much. That ratio, not price appreciation, is what decides the plan.

## 4. The six plans

| Plan | After-tax cash flow, year 1 | Property tax, year 1 | Terminal after-tax wealth, 2065 |
|---|---|---|---|
| **F.** Live in San Francisco; sell Cupertino | $11,020 | $44,770 | **$20,063,390** |
| **B.** Live in San Francisco (vacant unit); rent Cupertino | $43,060 | $130,270 | **$17,405,270** |
| **A.** Live in Cupertino; rent all three San Francisco units | −$9,540 | $103,970 | **$16,080,090** |
| **E.** Live in Cupertino; sell the San Francisco building | −$86,220 | $59,120 | **$15,541,700** |
| **D.** Sell both at inheritance; invest the net proceeds | −$163,080 | — | **$14,789,040** |
| **C.** Rent both houses; rent equivalent housing | −$54,360 | $130,350 | **$13,249,880** |

Method: 2045–2065, identical assumptions, all annual cash flows invested at 6% nominal, terminal sale of any remaining house at 2065 with 5% selling costs, transfer tax, capital-gains tax and depreciation recapture, then the portfolio liquidated and taxed on unrealised gains.

## 5. Recommendation

**Plan F — live in the San Francisco building, sell Cupertino at inheritance, invest the proceeds.**

Terminal after-tax wealth in 2065 of **$20,063,390**, against $16,080,090 for living in Cupertino and keeping both, and $14,789,040 for selling both and renting.

Why:

- Selling Cupertino immediately after death triggers almost no capital-gains tax: the basis steps up to $6,531,230, so the tax is $0. The frictions are 5% of selling costs and $7,180 of Santa Clara County transfer tax, leaving $6,197,490 to invest.
- It keeps the asset that actually produces cash: 2.0% net after reassessment, supported by two rent-controlled tenancies whose rents are real money.
- It avoids the low-yield, high-tax asset entirely. Occupying Cupertino costs $59,120 a year in property tax on a house that produces nothing.
- Housing is still free: occupying the vacant unit costs only the rent forgone on that one unit, not market rent on a whole house.

**Robustness.** Across nine combinations of house-price growth (3%, 4%, 5%) and portfolio return (4%, 6%, 8%), Plan F ranks first in eight and second in one — it loses only at a 4% portfolio return, where keeping and renting Cupertino edges ahead.

**It is not a recommendation to hold cash.** Plan F leaves roughly 76% in a diversified portfolio and 24% in one three-unit Bay Area building. Concentration is a real cost the model does not price.

## 6. What would change the answer

| Change | Effect |
|---|---|
| Portfolio returns 4% rather than 6% over 20 years | Keeping and renting Cupertino overtakes Plan F. This is the only single change in the tested range that reverses the ranking. |
| Bay Area prices grow 5% rather than 4% | The gap narrows; Plan F still leads. |
| The parents' principal residence is actually the San Francisco house | Results move by a few hundred thousand dollars; Plan F still leads ($20,974,800). |
| California repeals the step-up in basis (proposed in 2024, not enacted) | Plan F weakens materially, because it depends on selling at a stepped-up basis. |
| You do not want to be a landlord at all | The only plan that avoids tenants entirely is D, and it costs about $5,274,350 of terminal wealth. |

## 7. What to do before 2040

1. **Establish which house is the parents' principal residence, in writing.** The homeowners' exemption record on each parcel is the cleanest evidence. Every property-tax projection here depends on it.
2. **Do not take the houses as a lifetime gift.** A gift carries over the parents' basis and forfeits the step-up, costing roughly $2,012,140 in avoidable tax on the 2026–2045 appreciation alone.
3. **Review the trust instrument** for who takes title and whether a sub-trust holds the San Francisco building. It determines how fast the deed can be recorded, and the deed starts the assessor's clock.
4. **Get real insurance quotes for both ZIP codes.** The largest unresolved cost in the model.
5. **Confirm the actual ad valorem rate on each parcel.** Both owner-supplied tax series imply effective rates that differ from the published ones; the San Francisco difference is material.
6. **Decide the occupancy question on paper now.** The one-year move-in deadline and the BOE-19-P filing are the two that cannot be missed.

## 8. Flagged items, in one place

| Item | Severity | Why it matters |
|---|---|---|
| SF reported tax implies 2.13% effective rate vs 1.1827% published | Material | If the true ad valorem rate is 2.13%, every post-inheritance San Francisco tax figure is understated by roughly 45%. |
| Cupertino reported tax implies 1.309% vs 1.117% summed components | Low | About $1,060 a year at the 2026 base; probably an uncaptured bond series. |
| Which house is the parents' residence is unstated | High | Moves the Prop 19 exclusion between properties; does not change the ranking. |
| Insurance estimates unverified, likely understated | High | Largest unresolved cost input. |
| Solar net-metering tariff unverified | Medium | The credit is not modelled as permanent. |
| 4% growth and 6% return are assumptions, not verified | High | Most consequential unverified inputs; stress-tested and disclosed. |
| Prop 19 allowance beyond Feb 2027 not yet published | Medium | Assumed 3.5%/yr to 2045. |
| Market rent for the vacant SF unit assumed | Low | Affects plans A and B only. |
| Statewide insurance benchmark is second-hand | Medium | The CDI data file was not opened; every insurance row is labelled unverified. |
| Future property-tax rates held constant | Medium | Every post-inheritance tax figure would rise with new bond debt. |
| Santa Clara transfer-tax rate and no Cupertino city tax | Low | $7,180 on a $6.5M sale; stated as unverified rather than asserted. |
| Pending estate/wealth-tax bills not checked | Low | No figure depends on it. |

Full detail, with the source behind each and what would close it, is on the **Flagged for review** page of the site.

## 9. Sources

23 primary sources, all official: California State Board of Equalization (Prop 19 guidance and LTA 2025/009), Internal Revenue Service (Rev. Proc. 2025-32, Publications 551 and 559, Topic 701, net investment income tax), California Legislative Analyst's Office, California Franchise Tax Board, California Legislative Information (Revenue and Taxation Code §§51 and 218, and the text of Prop 19), California Secretary of State, County of Santa Clara Controller-Treasurer, City and County of San Francisco (Controller, Assessor-Recorder, Rent Board), California Department of Insurance, and the Federal Housing Finance Agency.

The full register, with a statement of what each source establishes, is in `data/sources.json` and on the site's Sources page. Every figure on every page carries a reference chip back to it.

---

*Rebuild with `python3 tools/model.py && python3 tools/build_site.py`. Model inputs are in a single dictionary at the top of `tools/model.py`, each labelled as verified, reported by the owner, or an assumption.*
