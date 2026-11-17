# Property inheritance decision dashboard

A privacy-conscious, source-linked planning dashboard for two California properties:
**Property A** is the home expected to pass through a trust around 2040–2050; **Property B** is a
three-unit rental building already owned by the heir. The analysis keeps their ownership and tax
positions separate while comparing living in, renting, and selling Property A, including mixed paths
and reinvestment choices.

**Live site:** <https://wingbangboozle1-lang.github.io/Tino3/>

> **Privacy warning.** The public site uses placeholders and omits names, street addresses, parcel
> identifiers, ZIP codes, county and city names, trust details, beneficiary details and account
> information. Owner-supplied dollar inputs shown on the site are rounded to the nearest $10, but
> rounding is not anonymization: public records or prior knowledge may identify a property. The
> repository is public. Earlier Git history and pull-request records may retain finer values or
> identifying context; the current site cannot erase those copies. The owner-run history scrub
> procedure and its limits are documented below and in `PRIVACY_REMEDIATION.md`.

## Start here

- `index.html` — executive dashboard, including the conditions that would change the answer and
  reinvestment risk near the top.
- `executive-summary.html` — concise summary of the conditional model result and major caveats.
- `decision.html`, `what-if.html` — comparable transfer-date/horizon paths and selectable sensitivity
  cases. Values are scenario outputs, not appraisals or forecasts.
- `precommit.html` — the conditions that would choose each path, written and dated before the
  figures arrive, so the outcome cannot be reverse-engineered from one projection; carries an
  empty decision record to complete by hand.
- `briefing.html` — one-page, printable Attorney & CPA discussion sheet.
- `questions.html` — what is known, what is missing, who can verify it, and suggested next steps.
- `suggestions.html` — proposals kept separate from implemented changes; each can be reviewed,
  adopted, deferred or rejected before implementation.
- `review.html` — flagged, assumed and unverified items.

- **Start here:** Dashboard (the answer, its confidence, the date it was computed and the three checks that would move it, on the first screen), the **pre-commitment register** (`precommit.html`: the rules the household writes down before reading any figure, with empty decision columns), executive summary, decision analysis (including the mixed paths and the Proposition 19 clawback), the what-if cases page (one lever at a time, link-driven, no script), and a printable Attorney & CPA briefing sheet.
- **Rules and the estate:** the trust steps, a dated deadlines timeline with official source links (`timeline.html`), thresholds and the law page.
- **Properties:** Property A, Property B, and the ownership distinction.
- **Costs and projections:** Running costs, year-by-year projections, income tax by path.
- **The letting path, taxed:** the income tax page carries the five statutory rules that decide
  what a letting year owes, the rent at which the let stops being a tax loss, and the break-even
  rent re-solved under ten treatments of the result (`taxes.html#letting-tax`).
- **Rules and estate:** Inheritance process, estate/inheritance tax thresholds, law watch.
- **Economic uncertainty:** Black-swan conditions and the historical economy record.
- **Review:** Questions before deciding, suggestions for review, and Flagged for Review.
- **Evidence:** Glossary and source ledger.

The remaining pages cover the distinct property profiles, carrying costs, projections, income and
estate taxes, the inheritance process, deadlines, current law and proposals, black-swan scenarios,
the historical economic record, a glossary and the source ledger. Navigation groups the material by
purpose.

## Model boundaries and headline result

The current model conditionally favours selling Property A soon after inheritance unless the heir
actually wants to live there. This is not individualized legal, tax or investment advice. It depends
on the beneficiary's eligibility for any property-tax exclusion, trust/title facts, date-of-death
basis, actual sale costs, occupancy, rents, insurance, maintenance, utilities, debt, market returns
and laws in force at transfer. Missing or unverified property-specific amounts are not presented as
confirmed; they are identified on the relevant pages and on `review.html`.

There are **25 generated HTML pages** and one stylesheet in the public allowlist. The pages show rounded owner-provided figures, model outputs and official-source-backed legal/economic information. The source ledger contains **123 entries**. Both property placeholders grow with the California state-level FHFA house-price index: the two metropolitan-area series were withdrawn on 15 November 2026 because the index publisher's own metadata crosswalked the placeholders to their metropolitan areas (an audit finding), and the privacy gate now rejects the withdrawn series identifiers and metro phrasing. The jurisdiction-specific entries (the two properties' county and city official pages) were also withdrawn, because their publishers identify the properties. A factual table row either links to an official source or is explicitly registered as unsourceable/unverified. The letting path is the one path that is priced under the income tax rules rather than before them: rent is ordinary income, the building is written off over 27.5 years and recaptured on sale, and a rental loss is suspended rather than deducted. It is published as a band over ten statutory treatments and three stated combined rates, because the household's marginal rate was never supplied.

The Black Swan analysis uses one canonical monthly park-and-phase engine and one short-Treasury
parking-yield assumption. It includes synthetic stresses and historical entry replays, including
1929, 2000, 2008 and 2020. Historical results are not forecasts; they do not ensure future Treasury
rates, protect against every market path, or eliminate opportunity cost. The brief shows the
reinvestment risk next to the staging result.
The investment, legal, tax and property-law conditions expected in 2040–2050 are unknown. Current
law and pending proposals are kept distinct on the law-watch page. Recheck official authorities and
professional advice when dates, facts or laws change.

## Published site and verification snapshot

The current generated edition contains **25 HTML pages**, **one runtime stylesheet**, **123 entries
in the source ledger**, and **141 content-free withdrawal notices** for retired routes. The latest
local verification reports **1342 table rows**: **1158 linked to official publishers** and **184
explicitly registered as unsourceable or unverified**. A row without a confirming official source is
not filled in by inference. The public site contains no source ledger or internal model data files;
the Jekyll and Actions publication boundaries are checked separately.

The model and pages are generated from `assets/data/` and `scripts/build.py`; do not edit generated
HTML or CSV outputs by hand. `EXECUTIVE_SUMMARY.md` is generated from the same model data and is
checked for drift. The source links and what they support are listed on `sources.html`.

## Privacy and Git history

`scripts/tracked_tree_guard.py` runs the publication gate's identifier patterns over every tracked text
file (including the coordination board) and fails the Verify workflow on a hit; it prints file, line and
class only. `scripts/privacy_scrub_audit.py` uses the same patterns for the history audit. The audit
must be run on a full clone (`git fetch --unshallow`): a shallow clone silently under-reports history.
On 16 November 2026 the full history (401 commits) still held postal codes, place and county names,
and an earlier-edition file set, and 115 commits carry a personal mail-service address; counts are in
`PRIVACY_REMEDIATION.md` section 7. Only the owner can run the rewrite.

`privacy_boundary.py` checks the published artifact for prohibited identifiers and unrounded
owner-supplied monetary values. The current page set passing that gate does **not** mean all public
Git history is clean. Earlier commits, pull-request diffs, forks, caches and clones may retain
previously exposed material.

`scripts/history_scrub.py` and `scripts/history_scrub.sh` document audit and rewrite procedures. The
rewrite is not performed by ordinary site builds. It changes Git history and requires a coordinated
force-push; the owner must decide whether and when to run it. A rewrite cannot guarantee removal from
forks, caches, clones or merged pull-request records. See `PRIVACY_REMEDIATION.md` for the internal
remediation record. Do not add identifying data to this public repository.

## Publication

GitHub Pages currently builds the `main` branch repository root with Jekyll. `_config.yml` is
maintained by `scripts/verify_legacy.py`; do not add `.nojekyll` or weaken its exclusion boundary.
A separate Actions workflow packages and deploys an allowlisted artifact. These are separate
publication paths, so check both after a publication change. The latest GitHub Pages status should
be checked through the repository's Pages settings and Actions runs.

## Estate liquidity and the two-person case

`scripts/liquidity.py` writes `assets/data/liquidity.json` and answers a question the path model does not:
if the estate owes federal estate tax, when is it due and how is it paid? The estate's own size is
deliberately not published and not modelled as a figure, so the engine works in anonymous bands of the
amount above the exclusion.

- **The clock.** The tax is 40% of the amount above the exclusion and is due nine months after death. A
  six-month extension of time to *file* is not an extension of time to *pay*; interest runs from the original
  due date whether or not an extension was granted.
- **The interest rate.** Federal short-term rate plus three percentage points, set quarterly and compounded
  daily. The published rate for the fourth quarter of 2026 is 7%, on a 4% short-term rate. The published
  range across 2022-2026 is 3% to 8%.
- **Deferral.** Section 6161(a)(2) allows a discretionary extension of time to pay, one year at a time for up
  to ten years, and only for the amount of the actual cash shortage. The page prices one, three, five and ten
  years, both as a single payment at the end and as equal annual instalments, against the return the cash
  would have earned if it had stayed invested.
- **Section 6166.** The fifteen-year instalment election exists, but it requires an interest in a closely
  held business exceeding 35% of the adjusted gross estate. A home occupied as a personal residence is not
  that on the face of the statute, so the site does not assume it is available; the rule and the 2% rate are
  still published, with the eligibility question flagged for the attorney.
- **The two-person case.** Two exclusions with portability at each inheritance year, and the joint
  section 121 amount repriced against every mixed path. The pure-path model still runs on single-filer
  assumptions, which is the conservative case.

## Mixed paths, distributions and the clawback

`scripts/mixed.py` writes `assets/data/mixed.json` and is the only new analysis engine this edition. It does
four things the pure-path model could not:

- **Mixed paths.** "Live in it for five years, then sell" occupies for five years, sells in year five, and
  compounds the net proceeds for the remaining twenty-five. That is not the same thing as selling in year
  thirty after five years of occupancy, which is what the pure paths implied. Eleven mixed cases are priced,
  plus the favourable reading of each live-then-let case.
- **The Proposition 19 clawback.** Revenue and Taxation Code section 63.2(a)(1)(C) enrols the base year value
  established at the change in ownership when the eligible transferee stops qualifying for the homeowners'
  exemption. Moving out is therefore not free, and the site now prices both the strict reading and the
  favourable one that `model.py`'s `live_then_rent` path quietly assumed.
- **Opportunity cost.** Living in the house produces somewhere to live. The imputed-rent table prices that
  benefit across a range of hypothetical market rents, each labelled a scenario: no official source publishes
  a market rent for a specific home and the input is still empty.
- **Distributions.** Every path is run against the same seeded fifty-year block bootstrap of the verified FRED
  record that the economy page uses, and published as deciles plus a histogram of the sell-minus-keep gap. The
  charts are divs and CSS, because the build refuses to publish a `<script>` element.

The engine is validated against the existing model: an immediate sale and a thirty-year occupation reproduce
`model.json`'s `sell_equities` and `live_in` terminals exactly, and a thirty-year letting reproduces
`rent_out`.

## Rebuild and verification

The project uses the Python standard library only. From the repository root, after changing any
model input or historical series, run the complete deterministic pipeline before reviewing or
publishing a recommendation:

```bash
python3 scripts/rebuild.py
python3 scripts/verify.py
python3 scripts/privacy_boundary.py
python3 scripts/tracked_tree_guard.py
python3 scripts/package_site.py
python3 scripts/verify_legacy.py --config-only
```

`rebuild.py` runs `model.py`, `economy.py`, `model.py` again, `mixed.py`, and `build.py` in that
order. The first model pass supplies break-even values used by the economy bootstrap; the second
model pass embeds the freshly rebuilt bootstrap. The mixed-path model then consumes both current
outputs. The pipeline writes the derived JSON/CSV tables, 25 pages, and `EXECUTIVE_SUMMARY.md`.
Its generator output is suppressed to keep detailed property diagnostics out of CI logs; run an
individual component locally if a failure needs diagnosis.

CI runs this same pipeline on pull requests and before deployment, then checks that every generated
page, summary, model, distribution, mixed-path file, and projection table matches the committed
version. Source inputs (`inputs.json`, the checked-in series, and the dated episode record) are not
mistaken for generated output by that check. Commit regenerated outputs alongside any input change,
and review the rebuilt dashboard's answer and the conditions that would change it before merge.

The verification checks cover deterministic generation, page structure, table-row source links or
explicit review-register entries, internal links and fragments, official-host allowlisting, monetary
rounding, privacy boundaries, packaged routes, and the legacy Jekyll source boundary. CI also builds
and audits the actual legacy Jekyll output. These mechanical checks do not prove a legal
interpretation, validate an owner-supplied bill, quote an insurer, or predict a future market.

## Limits to resolve before acting

- Independently verify owner-provided values, tax bills, assessment history, rental income, leases,
  utility charges, title, trust terms, debt and the date-of-death valuation.
- Obtain real insurance quotations and comparable market-rent opinions; the site does not invent
  property-specific premiums or rents.
- Confirm Property A's applicable tax-rate area, Proposition 19 eligibility and occupancy plan with
  the assessor and qualified counsel. Confirm Property B's leases and applicable local rules.
- Obtain a five-year maintenance and capital plan for each building, and decide whether a like-kind
  exchange is relevant before a sale.
- Ask an estate attorney and tax adviser about estate liquidity, prior taxable gifts, portability,
  basis, depreciation/recapture, and the transfer's actual tax-year consequences.
- Set the household's written decision criteria and investment policy before the actual figures
  arrive; rerun the model annually and whenever an input or law changes.

These are open verification tasks, not conclusions. The questions, suggestions, source ledger and
flagged review register identify who can resolve each one and where the result belongs.
