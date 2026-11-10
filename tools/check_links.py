#!/usr/bin/env python3
"""
check_links.py — validate the generated site.

Checks performed
----------------
1. every relative href/src resolves to a file that exists in the repository
2. every fragment (#id) resolves to an id in the target document
3. every page is reachable from index.html (BFS over the link graph)
4. every page links to the source register and to a stylesheet
5. no template artefacts leak into rendered text ( "{", "}", "None", "False" )
6. every external URL is collected into build/external-links.txt for manual review

Exit code 1 if any check fails. External URLs can not be fetched from this
sandbox (no outbound network in the shell), so they are inventoried rather than
requested; each one was opened with the browsing tool during verification.
"""

import os
import re
import sys
from collections import deque
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HREF = re.compile(r'(?:href|src)="([^"]+)"')
ID = re.compile(r'\sid="([^"]+)"')


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buf = []

    def handle_data(self, d):
        self.buf.append(d)


def html_files():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "build", "data", "tools", "node_modules")]
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(base, f))
    return sorted(out)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def main():
    files = html_files()
    errors = []
    externals = set()
    graph = {}

    ids = {}
    for f in files:
        with open(f) as fh:
            src = fh.read()
        ids[rel(f)] = set(ID.findall(src))

    for f in files:
        r = rel(f)
        with open(f) as fh:
            src = fh.read()
        links = []
        for href in HREF.findall(src):
            if href.startswith(("http://", "https://", "mailto:", "data:", "//")):
                externals.add(href)
                continue
            target, _, frag = href.partition("#")
            if target:
                tpath = os.path.normpath(os.path.join(os.path.dirname(f), target))
                if not os.path.exists(tpath):
                    errors.append(f"{r}: broken link -> {href}")
                    continue
                trel = rel(tpath)
                links.append(trel)
                if frag and tpath.endswith(".html"):
                    if frag not in ids.get(trel, set()):
                        errors.append(f"{r}: missing anchor #{frag} in {trel}")
            else:
                if frag and frag not in ids.get(r, set()):
                    errors.append(f"{r}: missing local anchor #{frag}")
        graph[r] = links

        if r != "index.html" and 'href="../assets/style.css"' not in src:
            errors.append(f"{r}: no stylesheet link")
        if r.startswith("pages/") and r != "pages/sources.html":
            if "sources.html#S" not in src and "pages/sources.html#S" not in src:
                errors.append(f"{r}: no source citation chips")

        # template-artefact lint on rendered text
        tp = Text()
        tp.feed(src)
        text = " ".join(tp.buf)
        if "{" in text or "}" in text:
            idx = text.index("{") if "{" in text else text.index("}")
            errors.append(f"{r}: unrendered template brace near ...{text[max(0,idx-60):idx+60]!r}")
        for artefact in ("None", "False", "TRUNCATED"):
            if re.search(rf"\b{artefact}\b", text):
                idx = re.search(rf"\b{artefact}\b", text).start()
                errors.append(f"{r}: placeholder token {artefact!r} near ...{text[max(0,idx-60):idx+60]!r}")

    # reachability
    seen = {"index.html"}
    q = deque(["index.html"])
    while q:
        cur = q.popleft()
        for nxt in graph.get(cur, []):
            if nxt not in seen and nxt.endswith(".html"):
                seen.add(nxt)
                q.append(nxt)
    for f in files:
        r = rel(f)
        if r not in seen:
            errors.append(f"{r}: unreachable from index.html")

    with open(os.path.join(ROOT, "build", "external-links.txt"), "w") as fh:
        for u in sorted(externals):
            fh.write(u + "\n")

    print(f"pages checked      : {len(files)}")
    print(f"external URLs      : {len(externals)}  (inventoried in build/external-links.txt)")
    print(f"internal link graph: {sum(len(v) for v in graph.values())} edges")
    if errors:
        print(f"\nFAIL — {len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("\nOK — all internal links, anchors and reachability checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
