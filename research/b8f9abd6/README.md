# Research module RES-LAW / RES-PROC — session `arena-b8f9abd6`

Checked 2026-11-10. This module holds public law only: no owner figures, addresses, ZIP codes, names or parcel data.
It is input for the final integration session. It does **not** change the site index or navigation.

| File | Contents |
|---|---|
| `law_watch.json` | 26 rows: current federal / state / local rules and pending or failed changes, each with an official source URL and status |
| `inheritance_process.json` | 15-step trust-inheritance sequence with deadlines, forms and statutory basis, plus a Prop 19 worked example on round hypothetical numbers |
| `estate_threshold_projection.csv` | Federal basic exclusion 2026–2050. The official column has values only for 2026 and 2027. Later years are left blank and flagged `unverified (not yet published)`. Scenario columns use 2.0 / 2.5 / 3.2 %/yr, plus married-with-portability and half-exclusion stress columns |
| `estate_tax_examples.csv` | Headroom and federal tax for hypothetical taxable estates of $10M–$40M in 2026, 2027, 2040, 2045 and 2050 |
| `law-watch.html` | A standalone, ready-to-link page that renders all of the above. It has no scripts and no remote assets |
| `build_research.py` / `verify_research.py` | Build the outputs reproducibly and run the checks (official hosts, $10 multiples, blank-unless-verified, no ZIP-like tokens) |

```sh
python research/b8f9abd6/build_research.py
python research/b8f9abd6/verify_research.py
```

## Findings that matter for the decision

1. **Federal estate tax.** The basic exclusion is $15,000,000 for 2026 deaths and $15,480,000 for 2027 (IRS IR-2026-133). The rate is 40% on the excess (Form 706 Table A). Portability can double the shelter for a married couple, but only if Form 706 is filed at the first death. Repeal bills S.587 and H.R.1301 have had no action since they were referred to committee on 02/13/2025.
2. **There is no California estate or inheritance tax** for deaths on or after 1/1/2005 (State Controller). No transfer tax applies when the trust distributes the house to the heir (R&TC §11930).
3. **Basis step-up.** Inherited property takes its date-of-death fair market value as basis (IRS FAQ). Selling soon after inheriting is therefore nearly free of income tax. Rev. Rul. 2023-2 is a warning: irrevocable grantor-trust assets left outside the estate do not get the step-up.
4. **Prop 19 is the deciding property-tax rule.** An heir who moves in within one year keeps taxable value + $1,044,586 (adjusted every other year) and pays tax on the rest. If the heir does not move in, the house is reassessed to full market value. Only the parent's principal residence qualifies. A rental the parent did not live in gets no exclusion.
5. **Prop 19 repeal failed.** Initiative 25-0017 did not qualify for the 2026 ballot (SOS memo #26138), and no similar initiative is circulating now. Plan on current Prop 19 rules.
6. **November 3, 2026 results (unofficial until certification by Dec 11, 2026).** Prop 3 passing makes high-income CA tax rates permanent, which affects gains on large sales. Prop 42 passing bars new state taxes on owning financial assets. Prop 40 is failing, and so is Prop 43.
7. **Solar.** NEM 2.0 terms last 20 years from interconnection (CPUC). A system installed before 2023 will probably leave NEM before a 2040–2050 inheritance, so today's roughly $0 bill or small monthly credit should not be assumed to continue.

## Not verified here (left blank / flagged)

- 2028+ federal exclusion amounts. These are projections only.
- The Prop 19 exclusion amount for transfers from Feb 16, 2027. It was not yet published when checked.
- San Francisco's charter-city transfer-tax rate schedule.
- Insurance premiums, utility rates and maintenance costs. These are outside this module's scope.
