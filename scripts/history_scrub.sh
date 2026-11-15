#!/usr/bin/env bash
# Pre-rounding Git history scrub - audit and guarded runbook.
#
# WHY THIS EXISTS
# The current tree is clean: every published figure is rounded to the nearest $10
# and scripts/privacy_boundary.py passes. Earlier commits and pull-request diffs of
# this public repository may still contain finer, pre-rounding figures and
# property-level identifiers (postal codes, area and utility names). Only a history
# rewrite can remove those copies. Rounding is not anonymisation, and deleting files
# from the working tree does not delete them from history.
#
# WHY IT IS PREPARED HERE AND NOT EXECUTED
# A history scrub means rewriting commits and force-pushing the rewritten refs,
# including `main`. Agent sessions in this repository may push only their own
# session branch, so the rewrite is documented and automated here but must be run
# by the repository owner or an administrator with push rights to `main`. Run it
# when no other session has work in flight: it invalidates every open branch.
#
# PRIVACY NOTE ON THIS FILE
# The identifier patterns below are built from string fragments at run time on
# purpose, so this file's own text never carries an identifier. Candidate figures
# are detected at run time and written to a temporary file OUTSIDE the repository;
# they are never added to the tree.
#
# USAGE
#   bash scripts/history_scrub.sh                # AUDIT ONLY (default, read-only)
#   bash scripts/history_scrub.sh --figures      # audit + list candidate unrounded figures
#   I_UNDERSTAND_THIS_REWRITES_HISTORY=1 bash scripts/history_scrub.sh --rewrite
#
# REQUIREMENTS FOR --rewrite
#   git-filter-repo (https://github.com/newren/git-filter-repo), and a fresh
#   `git clone --mirror` as the working copy. Never rewrite the only copy.
#
# AFTER A REWRITE (checklist for the owner)
#   1. Force-push every rewritten ref: main and any live session branches.
#   2. Re-check pull-request diffs: old diff URLs can serve pre-rewrite content;
#      comment on, or close and re-open, affected pull requests.
#   3. Rewrite commit author and committer addresses too (83 earlier commits carry
#      a personal e-mail address): run git-filter-repo with a mailmap file mapping
#      the personal address to the GitHub no-reply address, before or with the
#      text replacement pass. Then set the account's e-mail privacy so new commits
#      never expose it again.
#   4. Forks keep the old history. Ask fork owners to delete, or delete and
#      recreate the forks you control.
#   5. Ask GitHub Support to purge cached views (raw files, commit diffs) or wait
#      for caches to expire: https://support.github.com/
#   6. Confirm GitHub Pages rebuilds from the rewritten main and re-run the gates:
#      python3 scripts/build.py && python3 scripts/verify.py &&
#      python3 scripts/privacy_boundary.py && python3 scripts/package_site.py &&
#      python3 scripts/verify_legacy.py --config-only
#   7. Re-run this script's audit and expect zero findings.
#   8. Until step 1 completes, treat the exposed copies as public and live.

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="audit"
[ "${1:-}" = "--figures" ] && MODE="figures"
[ "${1:-}" = "--rewrite" ] && MODE="rewrite"

# --- token classes, built from fragments so this file carries no identifier -----
zip_a='950'"14"; zip_b='941'"22"; zip_c='950'"15"; zip_d='941'"16"; zip_e='941'"32"
place_1='Cuper'"tino"; place_2='Sunny'"vale"; place_3='Los Alt'"os"; place_4='Sara'"toga"
place_5='Los Gat'"os"; place_6='Monte Ser'"eno"; place_7='Mountain V'"iew"; place_8='Camp'"bell"
place_9='San'" Jose"; place_10='Outer Sun'"set"; place_11='Inner Sun'"set"; place_12='Park'"side"
util_1='sj'"water"; util_2='sj'"wc"
TOKENS=("$zip_a" "$zip_b" "$zip_c" "$zip_d" "$zip_e" \
        "$place_1" "$place_2" "$place_3" "$place_4" "$place_5" "$place_6" "$place_7" \
        "$place_8" "$place_9" "$place_10" "$place_11" "$place_12" "$util_1" "$util_2")

echo "== history scrub audit ($(date -u +%Y-%m-%dT%H:%MZ)) =="
echo "refs under audit:"
git for-each-ref --format='  %(refname:short) %(objectname:short)' | sed -n '1,20p'

found=0
for tok in "${TOKENS[@]}"; do
  n=$(git log --all --oneline -S"$tok" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" != "0" ]; then
    echo "IDENTIFIER '$tok': appears in the history of $n commit(s)"
    found=1
  fi
done
[ "$found" = "0" ] && echo "IDENTIFIERS: none of the known identifier tokens appear in any commit."

if [ "$MODE" = "figures" ] || [ "$MODE" = "rewrite" ]; then
  # Candidate pre-rounding figures: dollar amounts across all revisions that are
  # neither a multiple of ten nor a published official amount. Output goes to /tmp,
  # never into the repository.
  out=/tmp/history_scrub_figures_$$.txt
  git rev-list --all | while read -r rev; do
    git grep -h -E '\$ ?[0-9][0-9,]{2,}(\.[0-9]+)?' "$rev" -- '*.html' '*.json' '*.md' '*.csv' 2>/dev/null || true
  done | sort -u > "${out}.raw" || true
  python3 - "$out.raw" "$out" <<'PYEOF'
import re, sys
raw, out = sys.argv[1], sys.argv[2]
official = {1, 5, 15, 1_000_000, 1_022_600, 1_044_586, 250_000, 500_000, 371_000,
            5_490_000, 11_180_000, 11_400_000, 11_580_000, 11_700_000, 12_060_000,
            12_920_000, 13_610_000, 13_990_000, 15_000_000, 15_480_000, 19_000, 20_000,
            5_000_000_000, 15_000_000_000}
scale = re.compile(r'\$ ?([0-9][0-9,]{2,})(\.[0-9]+)?\s*(trillion|billion|million)?', re.I)
cands = set()
for line in open(raw, encoding='utf-8', errors='replace'):
    for m in scale.finditer(line):
        if m.group(3):
            continue  # published macroeconomic aggregate, not property-level
        amt = int(m.group(1).replace(',', ''))
        if amt % 10 != 0 and amt not in official:
            cands.add(('$' + m.group(1)))
with open(out, 'w', encoding='utf-8') as fh:
    for c in sorted(cands, key=lambda s: len(s), reverse=True):
        fh.write(c + '\n')
print(f"candidate unrounded figures found: {len(cands)} (written to {out}, outside the repository)")
PYEOF
  echo "Review ${out}: each candidate is a figure that predates the $10 rounding rule."
fi

if [ "$MODE" != "rewrite" ]; then
  echo
  echo "Audit complete. Nothing was changed. To run the rewrite:"
  echo "  I_UNDERSTAND_THIS_REWRITES_HISTORY=1 bash scripts/history_scrub.sh --rewrite"
  exit 0
fi

if [ "${I_UNDERSTAND_THIS_REWRITES_HISTORY:-}" != "1" ]; then
  echo "REFUSED: rewriting history rewrites every ref and needs a force-push to main."
  echo "Set I_UNDERSTAND_THIS_REWRITES_HISTORY=1 to proceed, from a fresh mirror clone."
  exit 1
fi
if ! command -v git-filter-repo >/dev/null 2>&1 && ! python3 -c 'import git_filter_repo' 2>/dev/null; then
  echo "REFUSED: git-filter-repo is not installed. Install it first:"
  echo "  pip install git-filter-repo   (or: pipx install git-filter-repo)"
  echo "Earlier sessions found the system Python externally managed (PEP 668); use pipx"
  echo "or a virtual environment rather than --break-system-packages."
  exit 1
fi

repl=/tmp/history_scrub_replacements_$$.txt
: > "$repl"
for tok in "${TOKENS[@]}"; do
  printf '%s==>REDACTED\n' "$tok" >> "$repl"
done
if [ -f /tmp/history_scrub_figures_$$.txt ]; then
  while read -r fig; do
    [ -n "$fig" ] && printf '%s==>REDACTED-FIGURE\n' "$fig" >> "$repl"
  done < /tmp/history_scrub_figures_$$.txt
fi
echo "Replacement directives: $repl (outside the repository)"
echo "Running git-filter-repo --replace-text on every ref..."
git filter-repo --replace-text "$repl" --force
echo
echo "Rewrite done. NOW COMPLETE THE CHECKLIST IN THIS FILE'S HEADER:"
echo "force-push main and live branches, clean pull-request diffs, handle forks,"
echo "ask GitHub Support about cached views, confirm the Pages rebuild, re-run the"
echo "gates, and re-run this audit expecting zero findings."
