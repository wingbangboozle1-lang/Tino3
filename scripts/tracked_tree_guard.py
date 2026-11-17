"""Tracked-tree identifier guard.

The publication gate (scripts/privacy_boundary.py) checks the deployable artifact. This
guard checks something the artifact check cannot: the text of every file that is
*tracked in this public repository*, including the coordination board, the
remediation records and the scripts. A public repository should not carry a postal
code, a property-level place name, a county or city name, a jurisdiction-specific
source host or a withdrawn metro series identifier, even in a note, because the
repository is public.

It also fails on an unresolved Git conflict marker at the start of a line in any
tracked text file. Rule R-1143-2 in the coordination board already requires a manual
grep for `<<<<<<<` / `=======` / `>>>>>>>` before every merge to `main`; this check
makes that rule mechanical, because two merges (one into `README.md`, one into the
coordination board) have landed on `main` carrying merge residue.

It reuses the publication gate's own patterns (one definition of an identifier), so
the two checks cannot drift apart. It prints file names, line numbers and pattern
classes only. It never prints a matched value.

Exemptions, each deliberate:
  * scripts/privacy_boundary.py - the gate itself; its literals are split across string
    fragments so that its text carries no identifier, and it is scanned by its own
    gate anyway.
  * e-mail addresses at github.com (service and no-reply addresses) - not personal.

Exit status: 0 when clean, 1 when any tracked file carries a gated identifier.

Usage:
    python3 scripts/tracked_tree_guard.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from privacy_boundary import FORBIDDEN  # noqa: E402  (single source of identifier patterns)

EXEMPT_FILES = {"scripts/privacy_boundary.py"}
SERVICE_EMAIL = re.compile(r"@(?:[\w-]+\.)*github\.com\b", re.I)

# An unresolved conflict marker at the start of a line: the seven-character open
# or close marker (with or without a branch label after it) or the seven-character
# separator on a line of its own. The current tree has no legitimate line-start run
# of these characters (checked 17 November 2026 over every tracked text file), and a
# Markdown setext underline long enough to match would be exactly the kind of line
# the board's manual rule would have flagged anyway.
CONFLICT_MARKER = re.compile(r"^(?:<{7,}(?: .*)?|={7,}\s*$|>{7,}(?: .*)?)")


def tracked_text_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    files = []
    for name in out.splitlines():
        if name in EXEMPT_FILES:
            continue
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary asset; not text, not scanned here
        files.append(name)
    return files


def scan() -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for name in tracked_text_files():
        text = (ROOT / name).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            for label, pattern in FORBIDDEN.items():
                for match in pattern.finditer(line):
                    if label == "email address" and SERVICE_EMAIL.search(match.group(0)):
                        continue
                    findings.append((name, number, label))
                    break
            if CONFLICT_MARKER.match(line):
                findings.append((name, number, "git conflict marker"))
    return findings


def main() -> int:
    findings = scan()
    if not findings:
        print("PASS tracked-tree guard: no gated identifier in any tracked text file "
              f"({len(tracked_text_files())} files scanned).")
        return 0
    by_class = Counter(label for _, _, label in findings)
    print("FAIL tracked-tree guard: gated identifiers found in tracked files "
          "(file, line and class only; values are never printed):")
    for label, count in by_class.most_common():
        print(f"  {label}: {count}")
    for name, number, label in findings[:200]:
        print(f"  {name}:{number}  [{label}]")
    print("Remove or generalise the text (for example '[place withheld]'), then re-run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
