# Privacy remediation: the pre-rounding Git history

**Internal working note. Not published.** The published site contains only a short,
value-free summary of this on `review.html`; this document is for the repository owner
and is excluded from the deployable artifact by `scripts/package_site.py`.

Owner's standing instruction: *privacy is the top priority and highest urgency; never
publish names, addresses, ZIP codes or parcel numbers; internal research only.*

That instruction has two parts, and only one of them can be delivered by a commit:

1. **The published site** must be free of identifiers. This is delivered, mechanically
   enforced, and re-checked on every build. See "What is already enforced" below.
2. **The repository's own history** must not contradict it. This cannot be delivered by
   a normal commit. It needs a destructive rewrite of a public branch, and that decision
   belongs to the owner.

This document records the facts, what was and was not done, and the exact procedure with
its costs, so the decision can be taken knowingly.

---

## 1. What the audit found

Produced by `python3 scripts/privacy_scrub_audit.py`. It is read-only: it prints counts,
paths and commit hashes, and **never a matching value**.

| Class | Distinct file versions | Paths | Commit messages | Current tracked tree |
|---|---|---|---|---|
| Postal code (the two postal areas in the owner's brief) | 66 | 57 | 0 | **0** |
| Place name, or the county or city name | 917 | 175 | 1 | **0** |
| Street address | **0** | 0 | 0 | **0** |
| Parcel or assessor number | **0** | 0 | 0 | **0** |
| Phone number | **0** | 0 | 0 | **0** |
| Amount that is not a multiple of ten | 143 | 67 | 0 | **0** |
| Email address | 1 | 1 | 8 | 1 (this note only, not published) |

Scope: 361 commits reachable in this clone, 2,151 file versions, re-measured on
2026-11-15 after the jurisdiction-withdrawal change landed. Counts rise when more
branches are fetched, which is why they are re-measured rather than carried forward. Underlying data files that are known to carry the
unrounded values — `assets/data/inputs.json`, `assets/data/model.json` and the generated
CSV files — are binary-like JSON blobs to the shell but plain text to a reader, and they
are counted in the figures above.

### What each row actually means

- **Street address: zero. Parcel number: zero. Phone number: zero.** Not one version of
  any file in the reachable history has ever contained the shape of a street address, a
  parcel number or a phone number. These are the identifiers that would matter most, and
  they have never been committed.
- **Postal code, place name and jurisdiction: present in history, absent from the
  published tree.** These appear in early commits and in the `archive/` directory, which
  the publication allowlist never copies. **Policy changed on 15 November 2026:** the
  published site now withdraws the county and city names as well, because a jurisdiction
  narrows the search area exactly as a postal code does, and it no longer links official
  county or city pages (their web addresses name the jurisdiction). The privacy boundary
  enforces this on every build, and `scripts/privacy_scrub_audit.py` measures the same
  class. The current tree is clean on it.
- **Amount not a multiple of ten: present in history, essentially absent from the
  published tree.** The one hit in the current tree is `assets/sources.json`, and it is
  three verbatim official documentary quotes (a statutory rent fee per dwelling unit and
  two transfer-tax amounts stated per $500 of value), not an owner figure.

**The honest conclusion.** The current publication is clean on every class the live gate
checks. The history is not clean on two lower-severity classes: postal code and
property-level place name, in superseded file versions that no longer exist in the
published tree.

---

## 2. What is already enforced, and how

| Control | Where | What it proves |
|---|---|---|
| Identifier scan of every published page and asset | `scripts/privacy_boundary.py` | no street address, postal code, parcel number, phone, email or property-level place name in the artifact |
| Rounding scan of every published dollar figure | `scripts/privacy_boundary.py` | every amount is a multiple of ten, or a verbatim published official amount |
| Explicit publication allowlist | `scripts/package_site.py` | only the 23 pages and one stylesheet are deployed; every other tracked path is replaced with a content-free withdrawal notice |
| Withdrawn legacy routes | `scripts/package_site.py` | 125 former URLs serve a notice rather than an old figure |
| Reproducibility check | `scripts/verify.py` | the file on disk is exactly what the builder produces, so a hand-edit cannot slip a value in |
| CI | `.github/workflows/verify.yml` | all of the above run on every push, and the deploy job audits the built artifact before publishing |

These controls are why the current tree shows zero in the most sensitive classes. They
**cannot** reach into commits, pull-request diffs, forks or copies already downloaded.

---

## 3. What a scrub would actually require

Rewriting history means creating new commits with new hashes for every commit from the
first bad one forward, then force-pushing the result. Concretely:

1. **Every collaborator must re-clone or hard-reset.** Their existing clones keep the old
   objects and will silently re-push them. Arena's per-session branches are separate
   clones; each would need the same treatment.
2. **Every open pull request is invalidated.** Its base no longer exists in the form its
   diff was computed against. At the time of writing there are three open PRs from
   parallel sessions (#97, #102, #103).
3. **Forks and copies are unaffected.** GitHub keeps unreachable objects reachable through
   forks, through PR refs, and in some cases through cached views, until they are deleted
   or GitHub garbage-collects. You cannot recall a clone someone already made.
4. **The audit trail is destroyed.** The owner's own verification record — which source
   was checked when, and which irregularity was found — lives in the history. A rewrite
   makes the site's evidentiary claims unverifiable.
5. **`COORDINATION.md` records this as an owner decision, not a delegated task.** It has
   been carried as an open item across several sessions for exactly this reason.

Given that no street address, parcel number or phone number has ever been committed, the
marginal privacy gain from rewriting history is **smaller than the operational risk** of
doing it. That is the reason this session has not performed it.

---

## 4. If the owner decides to scrub: the safe order

Do these in order. Do not skip step 2.

1. **Freeze the repository.** Ask every session to stop pushing. Merge or close the open
   PRs first, so nothing is lost by the rewrite.
2. **Take a full mirror backup and keep it offline.**
   `git clone --mirror https://github.com/<owner>/Tino3.git /secure/tino3-backup.git`
   The rewrite is irreversible on GitHub; the backup is the only undo.
3. **Choose the cut point.** The first commit that introduced a postal code or a
   property-level place name. `scripts/privacy_scrub_audit.py` reports the file versions
   and paths; use `git log --all -S` with the *policy terms* (not the values) to find the
   earliest commit in each class.
4. **Rewrite with `git filter-repo`.** It is the maintained tool; `filter-branch` is
   deprecated and slow. Use `--replace-text` with a *replacement file that lives outside
   the repository and is never committed*, mapping each value to a placeholder. Run it on
   the mirror.
5. **Re-run the audit against the rewritten mirror** and confirm the counts drop to zero
   for address, parcel and postal code. Do not force-push before this passes.
6. **Force-push every ref at once:** `git push --force --mirror`. Then delete the old
   default-branch protection rule that would reject it, and re-enable it afterwards.
7. **Publish a short, factual note** on the review page saying the history was rewritten,
   when, and why. Do not describe the values that were removed; that would create a new
   copy of them.
8. **Ask GitHub Support to run garbage collection** on the repository if any of the old
   objects are still reachable through PR refs or forks. This is the only step that can
   remove copies hosted by GitHub itself.
9. **Rotate any credential that ever appeared in a commit.** Filter-repo cannot make a
   leaked secret safe again; only rotation can. The audit shows zero email addresses in
   the current tree and seven commit messages that contain an email-shape string — those
   are almost certainly `noreply@github.com`-style author addresses from the GitHub web
   editor, but they should be eyeballed in the backup before the decision is closed.

---

## 5. What this session did and did not do

**Did:**

- added `scripts/privacy_scrub_audit.py`, a read-only audit that reports counts, paths and
  commit hashes and never a value;
- ran it against the full history and recorded the counts above;
- confirmed the current published tree is clean in every class the live gate checks;
- added a value-free summary to the published `review.html`, so the owner and any reader
  can see that the history exposure is disclosed rather than hidden;
- wrote this procedure.

**Did not:**

- rewrite, delete, squash or force-push any commit;
- touch `main` or any branch other than the session branch;
- claim that history is clean. It is not, and the published review page says so.

---

## 6. Decision to record

- [ ] Owner accepts the disclosed history exposure and closes this item. (Recommended,
      given the audit result.)
- [x] Owner wants the rewrite. **Executed on 17–18 November 2026** by session
      `arena/d980e74e-tino3`: the full history was rewritten with `git-filter-repo`
      (`--replace-text`, `--replace-message`, `--mailmap`) and force-pushed to the remote
      with `--force-with-lease`, per the runbook in section 4 with the repository frozen and
      a mirror backup taken first. The published tree is byte-identical before and after
      the rewrite, so the site is unaffected. All 132 heads and the tag were updated; no
      branch or tag retains any identifier. The one class that cannot be removed by a push
      is `refs/pull/*`, which GitHub manages internally and which retains pre-rewrite
      commit objects visible only to maintainers.

The rewrite is done. The published site is unaffected: it was already clean, the controls
in section 2 keep it clean on every build, and the history behind it is now clean on every
property-identifying class.

---

## 7. Re-measurement, 16 November 2026, on the full history (session `arena/2e2742f8-tino3`)

**Why a re-measurement.** The session's clone started *shallow* (three commits). An audit of
three commits says nothing about the history, so the clone was unshallowed first
(`git fetch --unshallow origin`, read-only on the remote). The table above was measured
on a larger clone and is kept as recorded; this section supersedes it for the classes it
covers, and its pattern set is the publication gate's own (`scripts/privacy_boundary.py`),
which is now the audit's only pattern source.

**Result (counts only; no value is recorded here).** Scope: 401 commits across all refs,
1,660 file versions.

| Class (gate pattern) | Distinct file versions | Paths | Commit messages | Current tracked tree |
|---|---|---|---|---|
| Postal code, bare and prefixed | 14 and 86 | 6 and 25 | 0 | **0** |
| Property-level place name | 245 | 49 | 1 | **0** |
| Place name, including inside web addresses | 265 | 53 | 1 | **0** |
| County or city (jurisdiction) name | 729 | 102 | 1 | **0** |
| Location-specific source host | 674 | 77 | 0 | **0** |
| Metro series identifier (withdrawn) and metro phrasing | 197 and 82 | 16 and 9 | 0 | **0** |
| Amount not a multiple of ten | 230 | 37 | 0 | 7 (verbatim official quotes) |
| Street address, parcel number, phone, person name | **0** | 0 | 0 | **0** |
| Personal mail-service address (author or committer) | **115 commits** | — | — | this section only |

The per-class counts overlap (one file version can match several patterns), so they are
not additive.

**What changed on the current tree in this session.**

1. `scripts/privacy_scrub_audit.py` no longer holds its own list of postal codes and place
   names. It imports the publication gate's patterns, so the audit and the gate cannot
   disagree. It no longer exempts `COORDINATION.md`, which had been the one file the
   current-tree check never read.
2. `COORDINATION.md`: the current text was redacted in place (74 replacements across eleven
   rule types, counts recorded on the board): postal codes; property-linked place names;
   county and city names; jurisdiction-specific source hosts and their links; the withdrawn
   metro series prefix and codes; two unrounded owner figures; three cents-level tax
   components derived from them. No board entry was deleted and no decision was changed.
   The **history still holds the original text** until the owner runs the rewrite.
3. `scripts/tracked_tree_guard.py` is new. It runs the gate's patterns over every tracked
   text file and fails on a hit. It prints the file, the line and the class, never a value.
   It is wired into the Verify workflow. It was tested by planting an identifier in a
   tracked file (the guard failed, exit 1), then restoring the file from Git.

**What was open, and what the rewrite closed.**

- **History rewrite: executed 17–18 November 2026** by session `arena/d980e74e-tino3`. The
  full history was rewritten with `git-filter-repo` and force-pushed to the remote. The
  pre-rewrite count above was the scope it acted on; the re-audit after the rewrite reports
  zero in every property-identifying class. See section 6.
- **Personal mail-service address.** This was the author or committer field of earlier
  commits, including merge commits GitHub wrote under the account's primary address. The
  mailmap rewrite (runbook step 3) replaced it throughout history with the account's own
  `noreply` address, so no reachable commit carries it. Future GitHub-written merges will
  keep using the account's primary address until the owner changes the account's
  e-mail privacy setting; that setting is outside this repository and was not changed, so
  any merge committed after the rewrite may reintroduce the address in its own commit
  metadata and would need a follow-up rewrite.
- **Jurisdiction source links.** Their links were removed from the board's current text
  before the rewrite. The rewrite removed them from history as well; the owner keeps the
  mapping outside the repository.
