"""Read-only audit of the repository's own history for the owner's privacy question.

The owner asked for the pre-rounding Git history to be scrubbed. A normal commit
cannot do that, and rewriting a public branch has consequences the owner has to
accept knowingly. This tool exists so that decision can be made on facts instead of
on fear or on reassurance:

  * it reads every commit reachable in this clone, every file version in it, and
    every commit message;
  * it counts how many file versions carry each class of identifier;
  * **it never prints a matching value.** Output is counts, file paths and commit
    hashes only. A scrub audit that echoed the secrets it found would create a new
    copy of them in the terminal, the build log and this repository's own records.

Nothing is written, nothing is rewritten and nothing is deleted. Exit code 0 always
unless the tool itself fails; this is a report, not a gate.

Usage:
    python3 scripts/privacy_scrub_audit.py            # human-readable report
    python3 scripts/privacy_scrub_audit.py --json     # same facts as JSON
    python3 scripts/privacy_scrub_audit.py --no-fetch # skip the network probe
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Patterns come from the publication gate itself, so the history audit measures exactly
# what the live gate measures and no identifier list is duplicated in this public file.
# (The gate keeps its literals split across string fragments, so its own text never
# carries an identifier.) Importing the gate is safe: it only reads the artifact at run time.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacy_boundary import FORBIDDEN as _GATE_PATTERNS  # noqa: E402
from privacy_boundary import check_money as _gate_check_money  # noqa: E402

PATTERNS = dict(_GATE_PATTERNS)

# The tracked-tree guard exempts github.com service addresses, which are not personal.
# The audit must agree with it or it reports a false exposure: two such addresses were
# counted in the current tree on 17 November 2026, both of them documentation of the
# privacy procedure itself (a GitHub noreply address in a runbook and in a scrub tool).
SERVICE_EMAIL = re.compile(r"@(?:[\w-]+\.)*github\.com\b", re.I)


def _email_shape(text: str) -> bool:
    """True only for a personal-shaped address; service addresses are not exposure."""
    return any(not SERVICE_EMAIL.search(m) for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text))

UNROUNDED = "amount not a multiple of ten"

# The exemption list is deliberately not duplicated here. The gate's own money test is
# called, so an official amount the gate allows - a statutory recording fee, a published
# threshold - can never be reported here as exposure, and a figure the gate would fail on
# can never be hidden from this audit. An earlier edition kept its own copy of the list,
# and it had drifted: on 17 November 2026 it counted seven files in the current tree as
# carrying unrounded amounts where the gate counts one, the difference being the $3, $75
# and $225 statutory fees the copy had never been told about. One definition, in the gate.
def has_unrounded_amount(text: str) -> bool:
    """True when the publication gate would object to an amount in this text."""
    return bool(_gate_check_money(text, "history-audit")[0])


def has_identifier(text: str, pattern: re.Pattern) -> bool:
    return bool(pattern.search(text))


# Current-tree files that legitimately contain the patterns (the gate itself, the
# board's own discussion of the rule, and this tool). Counted separately.
# Only the gate file itself is exempt: its identifiers are split across string fragments, so
# it does not carry a single identifier, and the exemption is kept for its regex text only.
SELF_FILES = {"scripts/privacy_boundary.py"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True,
                                   errors="replace", stderr=subprocess.DEVNULL)


def history_is_shallow() -> bool:
    """A shallow checkout cannot support a whole-history privacy conclusion."""
    try:
        return git("rev-parse", "--is-shallow-repository").strip().lower() == "true"
    except subprocess.CalledProcessError:
        # Fail closed: if Git cannot establish completeness, report the audit as
        # incomplete rather than implying that only reachable commits exist.
        return True


def commits() -> list[dict]:
    out = git("log", "--all", "--format=%H%x1f%ad%x1f%an%x1f%s", "--date=short")
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        h, d, an, subj = line.split("\x1f", 3)
        rows.append({"hash": h, "date": d, "author": an, "subject": subj})
    return rows


def file_versions() -> list[tuple[str, str]]:
    """(commit, path) for every blob in every commit reachable in this clone."""
    out = git("log", "--all", "--pretty=format:%H", "--name-only")
    pairs, current = [], None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
        elif current:
            pairs.append((current, line))
    return pairs


def blob(commit: str, path: str) -> str:
    try:
        return git("show", f"{commit}:{path}")
    except subprocess.CalledProcessError:
        return ""      # the path is not in that commit (a rename, or a deletion)


def scan() -> dict:
    shallow = history_is_shallow()
    cmts = commits()
    pairs = file_versions()
    # unique blobs is the honest denominator: the same file version appears in many commits
    classes = list(PATTERNS) + [UNROUNDED]
    seen: dict[str, set[str]] = {k: set() for k in classes}
    first_commit: dict[str, str] = {}
    paths_hit: dict[str, set[str]] = {k: set() for k in classes}
    cache: dict[tuple[str, str], dict[str, bool]] = {}
    for commit, path in pairs:
        if path in SELF_FILES:
            continue
        key = (commit, path)
        if key not in cache:
            text = blob(commit, path)
            found = {label: (_email_shape(text) if label == "email address"
                             else has_identifier(text, p)) for label, p in PATTERNS.items()}
            found[UNROUNDED] = has_unrounded_amount(text)
            cache[key] = found
        for label, hit in cache[key].items():
            if hit:
                seen[label].add(f"{commit}:{path}")
                paths_hit[label].add(path)
                first_commit.setdefault(label, commit)
    msg_hits = {label: [] for label in PATTERNS}
    for c in cmts:
        for label, p in PATTERNS.items():
            if _email_shape(c["subject"]) if label == "email address" else p.search(c["subject"]):
                msg_hits[label].append(c["hash"][:8])
    current = {}
    for label, p in PATTERNS.items():
        hits = []
        for path in git("ls-files").splitlines():
            if path in SELF_FILES:
                continue
            f = ROOT / path
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            hit = _email_shape(text) if label == "email address" else has_identifier(text, p)
            if hit:
                hits.append(path)
        current[label] = hits
    unrounded_now = []
    for path in git("ls-files").splitlines():
        if path in SELF_FILES:
            continue
        f = ROOT / path
        if f.is_file() and f.suffix in {".html", ".md", ".css", ".json", ".csv"}:
            try:
                if has_unrounded_amount(f.read_text(encoding="utf-8", errors="replace")):
                    unrounded_now.append(path)
            except OSError:
                pass
    current[UNROUNDED] = unrounded_now
    return {
        "repo": "wingbangboozle1-lang/Tino3",
        "audited_at_commit": git("rev-parse", "HEAD").strip(),
        "history_complete": not shallow,
        "commits_reachable": len(cmts),
        "earliest_commit_date": cmts[-1]["date"] if cmts else None,
        "latest_commit_date": cmts[0]["date"] if cmts else None,
        "file_versions_scanned": len(pairs),
        "unique_file_versions_by_class": {k: len(v) for k, v in seen.items()},
        "classes": classes,
        "paths_by_class": {k: sorted(v) for k, v in paths_hit.items()},
        "commit_messages_matching": {**{k: len(v) for k, v in msg_hits.items()}, UNROUNDED: 0},
        "current_tree_matches": current,
        "note": (
            "Counts only. No matching value is printed, stored or returned by this tool. "
            "Treat every count as an upper bound, for three reasons. (1) A file version can "
            "match because the rule itself is being described, not because a real identifier "
            "is present. (2) An official documentary quote can carry a non-multiple-of-ten "
            "amount - a statutory fee per unit, or a fiscal impact stated per $500 of value - "
            "which is not an owner figure. (3) The patterns look for the shape of an "
            "identifier, not for its truth. The classes that cannot be explained by any of "
            "those - street address and parcel number - are the ones to act on."),
    }


def main() -> int:
    as_json = "--json" in sys.argv
    report = scan()
    if as_json:
        print(json.dumps(report, indent=2))
        return 0
    print("Repository history privacy audit (read-only, counts only)")
    print(f"  repository      : {report['repo']}")
    print(f"  commit audited  : {report['audited_at_commit'][:12]}")
    if report["history_complete"]:
        print("  history scope   : complete for refs reachable in this clone")
    else:
        print("  history scope   : INCOMPLETE (shallow Git checkout; fetch full history to audit all commits)")
    print(f"  commits         : {report['commits_reachable']} "
          f"({report['earliest_commit_date']} to {report['latest_commit_date']})")
    print(f"  file versions   : {report['file_versions_scanned']}")
    print()
    print(f"  {'class':26} {'versions':>9} {'paths':>6} {'msgs':>5} {'current tree':>13}")
    for label in report["classes"]:
        print(f"  {label:26} {report['unique_file_versions_by_class'][label]:>9} "
              f"{len(report['paths_by_class'][label]):>6} "
              f"{report['commit_messages_matching'][label]:>5} "
              f"{len(report['current_tree_matches'][label]):>13}")
    print()
    print("  Paths that matched, by class (paths only, never values):")
    for label, paths in report["paths_by_class"].items():
        if paths:
            print(f"    {label}: {', '.join(paths[:6])}{' ...' if len(paths) > 6 else ''}")
    print()
    print("  " + report["note"])
    print()
    print("  This tool changed nothing. Deciding whether to rewrite history is the owner's,")
    print("  and the procedure and its consequences are set out in PRIVACY_REMEDIATION.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
