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
| Property-level place name | 173 | 105 | 1 | **0** |
| Street address | **0** | 0 | 0 | **0** |
| Parcel or assessor number | **0** | 0 | 0 | **0** |
| Email address | 0 | 0 | 7 | **0** |
| Phone number | **0** | 0 | 0 | **0** |
| Amount that is not a multiple of ten | 111 | 67 | 0 | 1 (verbatim official quotes only) |

Scope: 343 commits reachable in this clone, 1,696 file versions, earliest commit
2026-11-10, latest 2026-11-15. Underlying data files that are known to carry the
unrounded values — `assets/data/inputs.json`, `assets/data/model.json` and the generated
CSV files — are binary-like JSON blobs to the shell but plain text to a reader, and they
are counted in the figures above.

### What each row actually means

- **Street address: zero. Parcel number: zero. Phone number: zero.** Not one version of
  any file in the reachable history has ever contained the shape of a street address, a
  parcel number or a phone number. These are the identifiers that would matter most, and
  they have never been committed.
- **Postal code and place name: present in history, absent from the published tree.**
  These appear in early commits and in the `archive/` directory, which the publication
  allowlist never copies. The site names only "Santa Clara County" and "City and County of
  San Francisco", which are the levels at which the property-tax, rent and transfer rules
  operate. Whether the owner regards a county-level place name as acceptable is a policy
  choice, not a technical one; the current site assumes it is acceptable and says so in
  the privacy notice on every page.
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
- [ ] Owner wants the rewrite. Follow section 4 with the repository frozen and a mirror
      backup taken first.

Either way, the published site is unaffected: it is already clean, and the controls in
section 2 keep it clean on every build.
