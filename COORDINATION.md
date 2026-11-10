# Coordination board

Session ID: `arena/653eba50-tino3` (fixed Arena branch; no parallel sessions visible in repository).

| Task | Status | Owner / scope |
|---|---|---|
| Research, source verification, dashboard and deployment configuration | in progress | arena/653eba50-tino3 — all repository files |

## Work log
- Initial repository review: repository contained only `README.md`; `COORDINATION.md` was absent. Created this board before implementation.
- Scope is claimed for this session. Repository branch constraint is `arena/653eba50-tino3`; user-proposed per-session branches cannot be used in this Arena session.
- Sources checked against official material: IRS 2026 Form 706 instructions (https://www.irs.gov/instructions/i706); IRS 2026 Form 709 instructions (https://www.irs.gov/instructions/i709); IRS gifts/inheritances basis FAQ (https://www.irs.gov/faqs/interest-dividends-other-types-of-income/gifts-inheritances); California BOE Prop 19 adjustment release (https://www.boe.ca.gov/news/2025/nr-25-02.htm); BOE property assessment guide (https://boe.ca.gov/pdf/pub800-10.pdf). The BOE release confirms $1,044,586 for Feb. 16, 2025–Feb. 15, 2027; public display rounded to nearest $10 ($1,044,590).
- Verification performed: parsed all HTML anchors (18 in-page anchors, none broken); confirmed each data table includes source/status links; `git diff --check` passed. Official BOE page and IRS Form 706 page fetched directly. Personal names, street addresses, parcel IDs and account information are not included.
- Irregularities flagged in site: user-provided prices, operating costs, rents and historical tax/assessment data unverified; 94122 historic assessment figures look anomalously low relative to provided market estimate; no official insurance quote or forward values were established; future laws cannot be known; state death-tax status not asserted as verified here.
- Website is a single-page dashboard with category navigation and a clearly labeled Flagged for Review section. No numeric forward projection is fabricated because this conflicts with the instruction to leave unconfirmed values blank. A real after-tax recommendation needs estate/title/occupancy facts and verified income/cost/tax evidence.
- Deployment workflow added for GitHub Pages Actions. Local/GitHub deployment has not yet been established. Pull request, merge and live deployment results will be recorded below if platform permissions allow.
