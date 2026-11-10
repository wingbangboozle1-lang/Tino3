#!/usr/bin/env python3
"""build_site.py — render the whole static site from data/model.json."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import site_lib
from site_lib import ROOT, M, write
from sources import SOURCES

import pages_a, pages_b, pages_c, md_summary


def main():
    # Source chips resolve differently from the root page and from pages/.
    site_lib.set_rel("")
    pages_a.build_index()
    site_lib.set_rel("../")

    pages_a.build_exec()
    pages_a.build_process()
    pages_a.build_taxes()
    pages_b.build_cupertino()
    pages_b.build_sf()
    pages_b.build_opex()
    pages_b.build_projections()
    pages_c.build_decision()
    pages_c.build_risks()
    pages_c.build_sources()
    pages_c.build_flagged()

    md_summary.build()

    # source register as machine-readable data
    with open(os.path.join(ROOT, "data", "sources.json"), "w") as f:
        json.dump(SOURCES, f, indent=1)

    # GitHub Pages: serve files verbatim, no Jekyll processing.
    open(os.path.join(ROOT, ".nojekyll"), "w").close()

    print("built: index.html +", len(os.listdir(os.path.join(ROOT, "pages"))), "pages")


if __name__ == "__main__":
    main()
