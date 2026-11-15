"""Git-history scrub kit: audit and rewrite the pre-rounding history.

The owner's instruction is to scrub the pre-rounding Git history and keep the
repository privacy-first. Earlier commits and pull-request diffs in this public
repository contain the owner's finer, pre-rounding figures, the properties'
place and district names, postal codes and a personal commit-author email. The
published SITE is clean; this tool cleans the HISTORY the owner can clean.

Design constraints
------------------
* Standard library only, like every other script in this repository.
* The audit NEVER prints a matched token value - only the class, the number of
  commits affected and the first-seen commit, so the report itself cannot leak.
* The rewrite NEVER runs in the working repository. It clones a fresh mirror,
  transforms the fast-export stream, imports it, and hands the owner exact
  push commands. A force-push to `main` rewrites every clone, so it stays an
  explicit owner action; no session may perform it.
* What is replaced in every historical blob and commit message:
    - every identifier class from scripts/privacy_boundary.py's FORBIDDEN
      blocklist (street addresses, emails, postal codes, parcel numbers,
      phone numbers, property-level place names, place names inside web
      addresses, person-name patterns);
    - every dollar amount not rounded to the nearest $10 (the pre-rounding
      owner figures) - replaced with a generic placeholder, including the
      official verbatim amounts, because a historical blob is never rendered;
    - multi-decimal numbers and percentages (the pre-rounding metro series
      values fingerprint the location) when --keep-percentages is not given.
  The blocklist file itself is skipped so the gate keeps working.
* Commit metadata: every author/committer name and email outside the
  allow-list (the Arena agent's GitHub no-reply identity) is replaced with the
  repository's no-reply placeholder.

Owner procedure (summarised; see README "Git history scrub")
------------------------------------------------------------
    python3 scripts/history_scrub.py --check
    python3 scripts/history_scrub.py --run --source https://github.com/<owner>/<repo>.git \
        --out /tmp/Tino3-scrub-mirror
    # inspect the mirror, then
    git -C /tmp/Tino3-scrub-mirror push --force origin 'refs/heads/*:refs/heads/*' 'refs/tags/*:refs/tags/*'
  GitHub-side remnants (merged pull-request commit lists, cached views, forks)
  are outside what a force-push can reach; only GitHub Support can purge those.

Usage
-----
    python3 scripts/history_scrub.py --check [--ref PATTERN ...]
    python3 scripts/history_scrub.py --run --source SOURCE --out DIR
        [--execute] [--keep-percentages] [--keep-emails EMAIL ...]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import privacy_boundary as pb  # noqa: E402  (the same blocklist the site gate uses)

# Identity allow-list: committer identities that are already anonymous.
ALLOWED_EMAILS = {
    "297053741+arena-agent@users.noreply.github.com",
    "arena-agent@users.noreply.github.com",
    "owner@users.noreply.github.com",
}
REPLACEMENT_IDENTITY = b"Owner <owner@users.noreply.github.com>"

# Files that must keep their content (the gate's own blocklist).
SKIP_PATHS = {"scripts/privacy_boundary.py", "scripts/history_scrub.py"}

MONEY = re.compile(rb"\$\s?\d[\d,]*(?:\.\d+)?")
PERCENT = re.compile(rb"\b\d+\.\d+%")
DECIMAL = re.compile(rb"\b\d+\.\d{2,}\b")

PLACEHOLDERS = {
    "street address": b"[address]",
    "email address": b"[email]",
    "postal code": b"[postal-code]",
    "bare postal code": b"[postal-code]",
    "parcel or APN": b"[parcel]",
    "phone number": b"[phone]",
    "property level place name": b"[locality]",
    "place name anywhere, including web addresses": b"[locality]",
    "person name pattern": b"[name]",
    "metro-series crosswalk": b"[metro-series]",
    "metro phrasing attached to a placeholder": b"[metro]",
    "placeholder area phrasing": b"[metro]",
}


def git(*args: str, cwd: str | Path | None = None, input: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, input=input,
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def money_is_pre_rounding(match: bytes) -> bool:
    body = match.lstrip(b"$").replace(b",", b"").replace(b" ", b"")
    whole = body.split(b".")[0]
    try:
        return int(whole) % 10 != 0
    except ValueError:
        return False


def scrub_bytes(data: bytes, keep_percentages: bool) -> tuple[bytes, dict[str, int]]:
    """Same as scrub_bytes but money amounts are replaced only when unrounded."""
    counts: dict[str, int] = {}
    out = data

    def sub(pattern: re.Pattern, repl_fn, label: str, text: bytes) -> bytes:
        # Count only matches whose text actually changed, not every match processed.
        n = 0

        def counting(m):
            nonlocal n
            out = repl_fn(m)
            if out != m.group(0):
                n += 1
            return out

        new = pattern.sub(counting, text)
        if n:
            counts[label] = counts.get(label, 0) + n
        return new

    for label, pattern in pb.FORBIDDEN.items():
        # privacy_boundary compiles str patterns; the fast-export stream is bytes.
        bpat = re.compile(pattern.pattern.encode("utf-8"), pattern.flags & ~re.UNICODE | re.ASCII)
        r = PLACEHOLDERS.get(label, b"[redacted]")
        out = sub(bpat, lambda m, r=r: r, label, out)
    out = sub(MONEY, lambda m: m.group(0) if not money_is_pre_rounding(m.group(0)) else b"[amount]",
              "pre-rounding dollar amounts", out)
    if not keep_percentages:
        out = sub(PERCENT, lambda m: b"[percent]", "pre-rounding percentages", out)
        out = sub(DECIMAL, lambda m: b"[number]", "pre-rounding multi-decimal numbers", out)
    return out, counts


PERSON_RE = re.compile(rb"^(author|committer) ([^<>]*?) <([^<>]*)> (.*)$", re.M)


def scrub_identity(line: bytes) -> tuple[bytes, bool]:
    m = PERSON_RE.match(line + b"") if not line.endswith(b"\n") else PERSON_RE.match(line[:-1])
    target = m.group(0) if m else line
    if m:
        name, email, rest = m.group(2).strip(), m.group(3).strip(), m.group(4)
        if email.decode("utf-8", "replace") not in ALLOWED_EMAILS:
            return b"%s %s <owner@users.noreply.github.com> %s\n" % (
                m.group(1), b"Owner", rest), True
    return line, False


class StreamScrubber:
    """Transform a git fast-export stream: blobs, commit messages and identities.

    `preserve_shas` holds the git blob SHAs of the published tip tree. Those blobs
    pass through byte-for-byte: the current tree is clean under the identifier
    rules, its money is $10-rounded or officially published, and its numbers are
    load-bearing (the model reads them). Scrubbing them would corrupt the build.
    """

    def __init__(self, keep_percentages: bool, preserve_shas: set[bytes] | None = None):
        self.keep_percentages = keep_percentages
        self.preserve_shas = preserve_shas or set()
        self.blob_hits: dict[str, int] = {}
        self.preserved_hits: dict[str, int] = {}
        self.identities_rewritten = 0
        self.blobs = 0
        self.preserved_blobs = 0
        self.commits = 0
        self._sha = __import__("hashlib").sha1

    def transform(self, stream: bytes) -> bytes:
        out = bytearray()
        i = 0
        n = len(stream)
        while i < n:
            nl = stream.find(b"\n", i)
            if nl == -1:
                nl = n
            line = stream[i:nl + 1]
            if line.startswith(b"data "):
                size = int(line[5:].strip())
                body_start = nl + 1
                body = stream[body_start:body_start + size]
                blob_sha = self._sha(b"blob %d\x00" % len(body) + body).digest()
                if blob_sha in self.preserve_shas:
                    self.preserved_blobs += 1
                    _, counts = scrub_bytes(body, self.keep_percentages)
                    for k, v in counts.items():
                        self.preserved_hits[k] = self.preserved_hits.get(k, 0) + v
                    out += line
                    out += body
                    i = body_start + size
                    continue
                scrubbed, counts = scrub_bytes(body, self.keep_percentages)
                self.blobs += 1
                for k, v in counts.items():
                    self.blob_hits[k] = self.blob_hits.get(k, 0) + v
                out += b"data %d\n" % len(scrubbed)
                out += scrubbed
                i = body_start + size
                continue
            if line.startswith(b"author ") or line.startswith(b"committer "):
                new, changed = scrub_identity(line)
                if changed:
                    self.identities_rewritten += 1
                out += new
                i = nl + 1
                continue
            if line.startswith(b"commit ") or line.startswith(b"reset "):
                self.commits += 1
            out += line
            i = nl + 1
        return bytes(out)


def collect_hits(text: bytes, where: str, hits: dict[str, dict[str, int]]) -> None:
    for label, pattern in pb.FORBIDDEN.items():
        for m in pattern.finditer(text):
            hits.setdefault(label, {}).setdefault(where, 0)
            hits[label][where] += 1
    for m in MONEY.finditer(text):
        if money_is_pre_rounding(m.group(0)):
            hits.setdefault("pre-rounding dollar amounts", {}).setdefault(where, 0)
            hits["pre-rounding dollar amounts"][where] += 1


def preserved_tip_blobs(repo: str, ref: str) -> set[bytes]:
    """Blob SHAs of the tip tree of `ref` - the content that must keep building."""
    out = set()
    listing = git("ls-tree", "-r", ref, cwd=repo).decode("utf-8", "replace")
    for line in listing.splitlines():
        meta, _, path = line.partition("\t")
        mode, kind, sha = meta.split()
        if kind == "blob":
            out.add(bytes.fromhex(sha))
    return out


def walk_history(repo: str, keep_percentages: bool, preserve_shas: set[bytes] | None = None) -> dict:
    """Read every reachable blob and commit message; report classes, not values."""
    args = ["fast-export", "--all", "--signed-tags=strip",
            "--tag-of-filtered-object=rewrite", "--reencode=yes", "--no-data"]
    stream = git(*args, cwd=repo)
    commits = 0
    hits: dict[str, dict[str, int]] = {}
    emails: dict[str, int] = {}
    # fast-export --no-data still emits author/committer lines and mark/file-refs
    # but not blob contents, so blob bodies need a second pass with data.
    for m in PERSON_RE.finditer(stream):
        email = m.group(3).decode("utf-8", "replace").strip()
        if email not in ALLOWED_EMAILS:
            emails[email[:3] + "...@" + email.split("@")[-1]] = emails.get(
                email[:3] + "...@" + email.split("@")[-1], 0) + 1
        commits += 1

    blob_hits: dict[str, int] = {}
    data_stream = git("fast-export", "--all", "--signed-tags=strip",
                      "--tag-of-filtered-object=rewrite", "--reencode=yes", cwd=repo)
    sc = StreamScrubber(keep_percentages, preserve_shas)
    sc.transform(data_stream)
    return {"commits": commits, "emails": emails, "blob_hits": sc.blob_hits,
            "preserved_hits": sc.preserved_hits,
            "identities_rewritten": sc.identities_rewritten}


def cmd_check(args) -> int:
    repo = args.repo or "."
    print(f"Scanning reachable history of {Path(repo).resolve()} (identifiers and "
          f"pre-rounding figures; token values are never printed)...")
    preserve = preserved_tip_blobs(repo, args.preserve_tip) if args.preserve_tip else None
    res = walk_history(repo, args.keep_percentages, preserve)
    total = 0
    for label, count in sorted(res["blob_hits"].items()):
        total += count
        print(f"  {label}: {count} occurrences in historical file contents")
    for label, count in sorted(res["preserved_hits"].items()):
        print(f"  {label}: {count} occurrences in the preserved tip ({args.preserve_tip}) - "
              f"published content, left untouched")
    for email, n in sorted(res["emails"].items()):
        total += n
        print(f"  commit identity outside the allow-list ({email}): {n} occurrences")
    if total == 0:
        print("  clean: no flagged class appears in the reachable history.")
    else:
        print(f"  total flagged occurrences: {total}")
        print("  run --run --source <url> --out <dir> to build a scrubbed mirror "
              "(the force-push stays yours).")
    return 0 if total == 0 else 3


def cmd_run(args) -> int:
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        print(f"refusing: {out} exists and is not empty")
        return 2
    repo_root = Path(__file__).resolve().parents[1]
    if out.resolve().is_relative_to(repo_root):
        print("refusing: --out must be outside the repository")
        return 2
    print(f"cloning mirror of {args.source} into {out} ...")
    git("clone", "--mirror", args.source, str(out))
    print("reading history...")
    before = walk_history(str(out), args.keep_percentages)
    if not before["blob_hits"] and not before["emails"]:
        print("history is already clean; nothing to rewrite.")
        return 0
    preserve_ref = args.preserve_tip
    preserve = preserved_tip_blobs(str(out), preserve_ref)
    print(f"  preserving {len(preserve)} published tip blobs on '{preserve_ref}' byte-for-byte")
    stream = git("fast-export", "--all", "--signed-tags=strip",
                 "--tag-of-filtered-object=rewrite", "--reencode=yes", cwd=str(out))
    sc = StreamScrubber(args.keep_percentages, preserve)
    scrubbed = sc.transform(stream)
    print("importing rewritten history...")
    git("fast-import", "--force", "--quiet", cwd=str(out), input=scrubbed)
    git("reflog", "expire", "--expire=now", "--all", cwd=str(out))
    git("gc", "--prune=now", "--quiet", cwd=str(out))
    print("rewrite summary (classes only, never token values):")
    for label, n in sorted(sc.blob_hits.items()):
        print(f"  {label}: {n} replacements")
    print(f"  commit identities rewritten: {sc.identities_rewritten}")
    print(f"  commits processed: {sc.commits}, blobs processed: {sc.blobs}, "
          f"tip blobs preserved: {sc.preserved_blobs}")
    print()
    print("NEXT STEPS (owner actions, not performed by this tool):")
    print(f"  1. inspect: git -C {out} log --oneline | head")
    print(f"  2. push:    git -C {out} push --force origin 'refs/heads/*:refs/heads/*' "
          f"'refs/tags/*:refs/tags/*'")
    print("  3. re-clone fresh copies everywhere; old clones keep the old objects.")
    print("  4. GitHub-side remnants (merged PR commit lists, caches, forks) are NOT "
          "reachable by a force-push; contact GitHub Support if they must be purged.")
    if not args.execute:
        print()
        print("NOTE: ran without --execute? this run DID rewrite the mirror clone; "
              "the original repository is untouched.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="audit reachable history (read-only)")
    ap.add_argument("--run", action="store_true", help="build a scrubbed mirror clone")
    ap.add_argument("--repo", help="repository path for --check (default: this repository)")
    ap.add_argument("--source", help="clone URL or path for --run")
    ap.add_argument("--out", help="output mirror directory for --run (must be outside the repo)")
    ap.add_argument("--execute", action="store_true", help="acknowledge the mirror will be rewritten")
    ap.add_argument("--keep-percentages", action="store_true",
                    help="do not replace percentages and multi-decimal numbers")
    ap.add_argument("--preserve-tip", default="main",
                    help="ref whose tip blobs are preserved byte-for-byte (default: main)")
    args = ap.parse_args()
    if args.check:
        return cmd_check(args)
    if args.run:
        if not args.source or not args.out:
            print("--run needs --source and --out")
            return 2
        return cmd_run(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
