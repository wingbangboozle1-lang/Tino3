# Executive summary

Built 13 November 2026 from the same deterministic model as the site. Every dollar figure is rounded to the nearest $10. Anonymised throughout: **Property A** is the single-family home being inherited through a trust, in Santa Clara County; **Property B** is the three-unit building the heir already owns, in the City and County of San Francisco. No name, street address, postal parcel number, postal code, trust term or utility account appears here or on the site.

Planning analysis, not legal, tax or investment advice.

## The recommendation

**Sell Property A soon after it is inherited, unless the heir genuinely wants to live in that house.** Selling leads in the baseline, in 9 of the 9 sensitivity combinations and in 4 of the 6 stress regimes, and it is the only path that does not depend on the heir wanting that house, being able to hold it as a principal residence, or finding a tenant at an implausible rent.

## One condition outranks every number below

The intergenerational exclusion in Revenue and Taxation Code section 63.2 applies **only** where the transfer is between a parent and a child, or between a grandparent and a grandchild whose parent has died. That is a condition of the exclusion, not a detail. If the relationship is different, no exclusion is available, the property is reassessed to full market value, every shelter figure below disappears, and the case for selling gets stronger. The trust document is the only thing that settles it and this analysis has not seen it. **Question A-1 on the questions page.**

## Terminal value after thirty years

Selling and investing the proceeds, against keeping the house. Baseline: house prices 4.0% a year, inflation 2.5%, equities 7.0% gross of a 0.7% tax drag, Treasuries 4.7%, selling costs 5.5%.

| Inherited | Sell, equities | Sell, Treasuries | Live in it | Let it out |
|---|---|---|---|---|
| 2040 | $31,714,550 | $20,121,530 | $12,433,650 | $10,575,840 |
| 2045 | $38,585,540 | $24,480,880 | $15,107,350 | $12,867,130 |
| 2050 | $46,945,240 | $29,784,760 | $18,360,300 | $15,654,830 |

The letting paths are credited with **no rent**, because no market rent for Property A has been supplied and no official source publishes one for a specific home. Read them as a floor, not as a comparison.

## The numbers that drive it

- **The tax cliff.** The Property A bill is about $7,360 today. If the heir inherits in 2045 and does not move in, it becomes about $79,330. If the heir moves in and claims the exclusion, it becomes about $57,060.
- **The shelter is smaller than the growth.** On a 2045 inheritance the exclusion shelters the old taxable value plus $1,886,640 against a market value of $6,531,230. Everything above the sum is reassessed.
- **The tax-free window.** Property acquired from a decedent takes a basis equal to its value at death, so a sale soon afterwards pays about zero capital gains tax. In the 2045 baseline a $6,531,230 sale carries $0 of tax.
- **What waiting costs.** Hold the same house thirty years and the tax on the eventual sale is about $4,910,950 after the section 121 exclusion; let it out as well and depreciation recapture pushes that to about $7,151,170.
- **The break-even.** Keeping the home beats selling only if it appreciates 7.72% a year for thirty years. The verified index for this area compounded at 6.9% over fifty years and 3.3% over the last twenty.
- **The break-even rent.** Letting would need about $30,180 a month, $362,120 a year, in 2045, to match selling and investing.

## The black swans, and what they do to the answer

Real economies do not grow at a constant rate. In the verified record used here, annual consumer price inflation ran from minus 0.3% to plus 13.5%, and annual house price growth in Property A's area from minus 12.3% to plus 30.2%. The regimes below replay the worst stretches of that record against a 2045 inheritance over thirty years.

| Regime | Inflation | House growth | Treasury | Best path |
|---|---|---|---|---|
| Great Inflation repeat | 9.8% | 18.9% | 10.13% | Live in it |
| A long house price slump | 3.4% | -0.2% | 7.06% | Sell, reinvest in Treasuries |
| A financial crisis crash | 2.2% | -5.6% | 3.51% | Sell, invest in equities |
| A fast inflation burst then a rate shock | 5.6% | 8.3% | 2.78% | Live in it |
| House prices flat for the whole horizon | 2.5% | 0.0% | 4.7% | Sell, invest in equities |
| Low inflation and falling nominal house prices | 0.5% | -1.0% | 2.0% | Sell, invest in equities |

Sold into equities or Treasuries wins five of the six. The exception is a repeat of the 1965-1982 Great Inflation or the 2021-2023 burst, where nominal house prices outran everything else. That is a bet on one neighbourhood repeating its best decades, not a plan.

## Estate and inheritance tax

- California has no estate tax and no inheritance tax. No California estate tax return is required for a death on or after 1 January 2005, and an inheritance is not California income.
- The federal exclusion is $15,000,000 per person for 2026 and $15,480,000 for 2027. Portability lets a surviving spouse use a deceased spouse's unused exclusion if a timely return is filed.
- Above the exclusion the federal rate reaches 40%. The tax is on the estate, not on the heir, and is due with Form 706 nine months after death, with an extension available.
- The cash inheritance is deliberately not published and not modelled as a figure; the estate page works in anonymous scenario bands instead.

## What is still open

These sit on the flagged-for-review page, each with the publisher that holds the record:

- The owner's market values, the property-tax and assessment histories, the rent and the utility and insurance estimates are the owner's own records, not checked against a county roll or a quote.
- Property A's tax rate area and its published ad valorem rate. 1.18% is assumed and flagged.
- A property-specific insurance premium for either building. The Department of Insurance publishes a statewide average and an online premium survey, not an average for a postal area.
- A market rent for Property A, and the seller's actual selling costs.
- Whether the trust actually holds title, and whether the transfer is between a parent and a child.

## How this was checked

Every rule, threshold and rate on the site was read on the publishing agency's own domain and is linked from the row that uses it. The ledger holds 111 sources. A build-time verifier fails if a table row has no official link, if the build is not reproducible, if any internal link or fragment does not resolve, or if any published dollar figure is not a multiple of $10. A separate check recomputed the published relationships from the inputs.

## Read next

- `index.html` — the dashboard
- `decision.html` — the five paths, the sensitivity and the break-evens
- `questions.html` — what is unknown and how to find it, starting with A-1
- `suggestions.html` — the review queue; nothing there has been implemented
- `review.html` — every unverified figure and modelling caveat
- `sources.html` — the full ledger
