"""A build-time estimate of whether the printable brief fits on one sheet.

No browser is available in this environment, so the printed pagination of the
Attorney and CPA brief cannot be looked at. What can be done is to measure the
thing the claim depends on: the height of the brief's content against the height
of the paper it is printed on, using the print rules this repository actually
ships.

Two properties make the estimate worth publishing:

  * it reads the constants out of `assets/style.css` rather than repeating
    them, so changing the stylesheet changes the estimate, and the two cannot
    drift apart; and
  * it is deliberately pessimistic - a wide average character width, no margin
    collapsing, and a safety margin on the total - so it over-estimates the
    printed height rather than under-estimating it. A build that passes this
    check is very unlikely to overflow; a build that fails it probably would.

It is an estimate and is labelled as one wherever it is published. It is not a
substitute for opening the page in a browser and printing it, which remains an
open item on the register of unverified things.

Run it directly to measure any brief against any stylesheet::

    python3 scripts/print_budget.py briefing.html assets/style.css
"""
from __future__ import annotations

import math
import re
from html.parser import HTMLParser
from pathlib import Path

# --- the pessimistic constants -------------------------------------------------
# A proportional face at small sizes averages a shade over half the font size per
# character. Half a point over is used here so the estimate runs long.
CHAR_WIDTH_RATIO = 0.55
# A safety margin applied to the total, so an estimate that lands exactly on the
# page is still treated as over.
SAFETY = 1.06
# The usable fraction of a column: the last line of a paragraph is rarely full,
# and a section cannot be split across columns without a visible break.
COLUMN_FILL = 0.97

PT_PER_IN = 72.0
PT_PER_PX = 0.75


# --- a small CSS reader --------------------------------------------------------
def _rule_blocks(css: str) -> list[tuple[str, str]]:
    """Every (selector, body) pair in a stylesheet, at any nesting depth.

    Media queries are flattened: their contents are returned with the inner
    selector, which is what the print rules need. At-rules such as ``@page``
    are returned as well, so a page box can be read.
    """
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(css)
    while i < n:
        if css[i] != "{":
            i += 1
            continue
        depth = 1
        j = i + 1
        while j < n and depth:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1
        body = css[i + 1:j - 1]
        k = i - 1
        while k >= 0 and css[k] not in "{}":
            k -= 1
        selector = " ".join(css[k + 1:i].split())
        if selector.startswith("@") and not selector.startswith("@page"):
            # a conditional group: its contents carry the rules we need
            blocks.extend(_rule_blocks(body))
        else:
            blocks.append((selector, body))
        i = j
    return blocks


def _find_rule(css: str, selector_fragment: str, requires: str | None = None) -> str | None:
    """The declaration body of the rule whose selector contains the fragment.

    ``requires`` narrows the match to a rule that also contains a given
    declaration, so a print override can be found separately from the base rule.
    """
    for selector, body in _rule_blocks(css):
        if selector_fragment in selector and (requires is None or requires in body):
            return body
    return None


def _num(text: str | None, default: float | None = None) -> float | None:
    if text is None:
        return default
    m = re.search(r"(-?\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else default


def _hidden_classes(css: str) -> set[str]:
    """The class names the print rules take off the page.

    A class used inside a ``:has(...)`` selector is the switch that turns the
    print rules on, not something they hide, so it is excluded.
    """
    switch_classes: set[str] = set()
    for selector, _body in _rule_blocks(css):
        for group in re.findall(r":has\(([^)]*)\)", selector):
            switch_classes.update(re.findall(r"\.([A-Za-z0-9_-]+)", group))
    hidden: set[str] = set()
    for selector, body in _rule_blocks(css):
        if "display:none" not in re.sub(r"\s+", "", body):
            continue
        for name in re.findall(r"\.([A-Za-z0-9_-]+)", selector):
            if name not in switch_classes:
                hidden.add(name)
    return hidden


# --- the print geometry, read out of the stylesheet ----------------------------
class Geometry:
    """The printable geometry of the brief, taken from assets/style.css."""

    def __init__(self, css: str):
        page = _find_rule(css, "@page brief") or ""
        margin_in = _num(re.search(r"margin:\s*([^;]+)", page).group(1)
                         if re.search(r"margin:\s*([^;]+)", page) else None, 0.38)
        self.page_w = 8.5 * PT_PER_IN
        self.page_h = 11.0 * PT_PER_IN
        self.margin = margin_in * PT_PER_IN
        self.printable_w = self.page_w - 2 * self.margin
        self.printable_h = self.page_h - 2 * self.margin

        grid = _find_rule(css, ".print-brief) .brief-grid", "gap:") or ""
        gap = re.search(r"gap:\s*([\d.]+)px\s+([\d.]+)px", grid)
        self.row_gap = float(gap.group(1)) * PT_PER_PX if gap else 3.0
        self.col_gap = float(gap.group(2)) * PT_PER_PX if gap else 9.0
        # The column count comes from the base grid rule; the print rule only
        # overrides the gap.
        template = _find_rule(css, ".brief-grid", "grid-template-columns") or ""
        self.columns = 2 if "1fr 1fr" in template else 1

        text_rule = _find_rule(css, ".print-brief) .brief-grid li") or ""
        self.font_pt = _num(re.search(r"font-size:\s*([\d.]+)pt", text_rule).group(1)
                            if re.search(r"font-size:\s*([\d.]+)pt", text_rule) else None, 7.4)
        self.line_height = _num(re.search(r"line-height:\s*([\d.]+)", text_rule).group(1)
                                if re.search(r"line-height:\s*([\d.]+)", text_rule) else None, 1.2)
        self.block_margin = float(_num(re.search(r"margin:\s*([\d.]+)px", text_rule).group(1),
                                       2.0) * PT_PER_PX) if re.search(r"margin:\s*([\d.]+)px", text_rule) else 1.5

        # The block above and below the grid: the title, the confidential line
        # and the footer. Their sizes are read from the stylesheet for the same
        # reason the grid sizes are: so the estimate cannot drift from the sheet.
        h1_rule = _find_rule(css, ".print-brief) main > h1") or ""
        conf_rule = _find_rule(css, ".print-brief) .brief-confidential") or ""
        foot_rule = _find_rule(css, ".print-brief) .brief-footer") or ""
        self.h1_pt = _num(re.search(r"font-size:\s*([\d.]+)pt", h1_rule).group(1)
                          if re.search(r"font-size:\s*([\d.]+)pt", h1_rule) else None, 19.0)
        self.h1_margin = 3.0 * PT_PER_PX
        self.conf_pt = _num(re.search(r"font-size:\s*([\d.]+)pt", conf_rule).group(1)
                            if re.search(r"font-size:\s*([\d.]+)pt", conf_rule) else None, 8.0)
        self.foot_pt = _num(re.search(r"font-size:\s*([\d.]+)pt", foot_rule).group(1)
                            if re.search(r"font-size:\s*([\d.]+)pt", foot_rule) else None, 7.0)

        h2_rule = _find_rule(css, ".print-brief) .brief-grid h2") or ""
        h2_size = _num(re.search(r"font-size:\s*([\d.]+)pt", h2_rule).group(1)
                       if re.search(r"font-size:\s*([\d.]+)pt", h2_rule) else None, 10.0)
        h2_margin = re.search(r"margin:\s*([\d.]+)px\s+0\s+([\d.]+)px", h2_rule)
        self.h2_pt = h2_size
        self.h2_margin = ((float(h2_margin.group(1)) + float(h2_margin.group(2))) * PT_PER_PX
                           if h2_margin else 4.5)

    @property
    def column_w(self) -> float:
        return (self.printable_w - self.col_gap * (self.columns - 1)) / self.columns

    @property
    def line_pt(self) -> float:
        return self.font_pt * self.line_height

    @property
    def chars_per_line(self) -> float:
        return self.column_w / (self.font_pt * CHAR_WIDTH_RATIO)


# --- the brief's own structure -------------------------------------------------
class _Brief(HTMLParser):
    """Pull the `.brief-grid` sections out of the brief and measure each one.

    Elements the print rules hide are skipped, together with their contents,
    because they never reach the paper.
    """

    def __init__(self, geom: Geometry, hidden: set[str] | None = None):
        super().__init__(convert_charrefs=True)
        self.geom = geom
        self.hidden = hidden or set()
        self.sections: list[dict] = []
        self.depth = 0
        self.in_grid = False
        self.in_section = False
        self.section: dict | None = None
        self.capture: str | None = None
        self.text: list[str] = []
        self.in_h1 = False
        self.skip = 0
        self.h1_text = ""
        self.conf_text = ""
        self.footer_text = ""
        self.outside: dict | None = None

    # -- helpers
    def _flush(self) -> None:
        if self.capture:
            body = " ".join("".join(self.text).split())
        if self.capture and self.section is None:
            # the blocks outside the grid: the title, the confidential line and
            # the footer. Their text is kept so their wrapped height can be
            # counted against the full page width.
            if self.capture == "h1":
                self.h1_text = body
            elif self.capture == "conf":
                self.conf_text = body
            elif self.capture == "footer":
                self.footer_text = body
            self.capture = None
            self.text = []
            return
        if self.capture and self.section is not None:
            if self.capture == "p":
                self.section["paras"].append(body)
            elif self.capture == "li":
                self.section["items"].append(body)
            elif self.capture == "h2":
                self.section["heading"] = body
        self.capture = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        attr = {k: (v or "") for k, v in attrs}
        classes = set(attr.get("class", "").split())
        if self.skip:
            # inside something the print rules remove
            if tag not in {"br", "img", "meta", "link", "input"}:
                self.skip += 1
            return
        if classes & self.hidden:
            self.skip = 1
            return
        if tag == "div" and "brief-grid" in classes:
            self.in_grid = True
        elif tag == "section" and self.in_grid:
            self.in_section = True
            self.section = {"heading": "", "paras": [], "items": []}
            self.depth = 1
        elif tag == "h1":
            self.in_h1 = True
            self.capture = "h1"
            self.text = []
        elif tag == "p" and self.section is None and "brief-confidential" in classes:
            self._flush()
            self.capture = "conf"
            self.text = []
        elif tag == "p" and self.section is None and "brief-footer" in classes:
            self._flush()
            self.capture = "footer"
            self.text = []
        elif tag == "p" and self.section is not None:
            self._flush()
            self.capture = "p"
            self.text = []
        elif tag == "li" and self.section is not None:
            self._flush()
            self.capture = "li"
            self.text = []
        elif tag == "h2" and self.section is not None:
            self._flush()
            self.capture = "h2"
            self.text = []

    def handle_endtag(self, tag):
        if self.skip:
            if tag not in {"br", "img", "meta", "link", "input"}:
                self.skip -= 1
            return
        if tag == "section" and self.in_section:
            self._flush()
            self.sections.append(self.section)
            self.section = None
            self.in_section = False
        elif tag in {"p", "li", "h2", "h1"}:
            self._flush()
            self.in_h1 = False

    def handle_data(self, data):
        if self.capture and not self.skip:
            self.text.append(data)


def _section_height(section: dict, geom: Geometry) -> float:
    """The printed height of one grid section, in points."""
    height = 0.0
    if section["heading"]:
        # a heading can wrap inside the narrow column, so its lines are counted
        h2_cpl = geom.column_w / (geom.h2_pt * CHAR_WIDTH_RATIO)
        heading_lines = max(1, math.ceil(len(section["heading"]) / h2_cpl))
        height += heading_lines * geom.h2_pt * 1.25 + geom.h2_margin
    cpl = geom.chars_per_line
    for para in section["paras"]:
        lines = max(1, math.ceil(len(para) / cpl))
        height += lines * geom.line_pt + geom.block_margin * 2
    if section["items"]:
        # a list item is indented, so it fits fewer characters per line
        indent = 12.0 * PT_PER_PX
        item_cpl = (geom.column_w - indent) / (geom.font_pt * CHAR_WIDTH_RATIO)
        for item in section["items"]:
            lines = max(1, math.ceil(len(item) / item_cpl))
            height += lines * geom.line_pt + geom.block_margin * 2
    return height


def measure(html_text: str, css_text: str) -> dict:
    """Measure the brief against one sheet of paper."""
    geom = Geometry(css_text)
    parser = _Brief(geom, _hidden_classes(css_text))
    parser.feed(html_text)

    # The grid places the sections in order, two to a row. A row is as tall as
    # its taller cell, so the pairing can waste space; that is counted honestly.
    heights = [_section_height(s, geom) for s in parser.sections]
    rows = []
    for i in range(0, len(heights), geom.columns):
        rows.append(max(heights[i:i + geom.columns]))
    grid_height = sum(rows) + geom.row_gap * max(0, len(rows) - 1)

    # Header and footer are outside the grid and run the full page width, so
    # their lines are counted against the full printable width. Assuming one
    # line each would under-count them.
    hidden = _hidden_classes(css_text)
    full_cpl = geom.printable_w / (geom.font_pt * CHAR_WIDTH_RATIO)

    def full_lines(text: str, size_pt: float) -> int:
        if not text:
            return 0
        cpl = geom.printable_w / (size_pt * CHAR_WIDTH_RATIO)
        return max(1, math.ceil(len(text) / cpl))

    header = 0.0
    # the title, the confidential line, and the screen lede if it still prints
    header += full_lines(parser.h1_text, geom.h1_pt) * geom.h1_pt * 1.25 + geom.h1_margin
    if "lede" not in hidden:
        header += 9.0 * 1.25 + 6.0 * PT_PER_PX
    header += full_lines(parser.conf_text, geom.conf_pt) * geom.conf_pt * 1.25 + 3.0 * PT_PER_PX * 2
    footer = full_lines(parser.footer_text, geom.foot_pt) * geom.foot_pt * 1.25 + (4.0 + 3.0) * PT_PER_PX

    total = (header + grid_height + footer) * SAFETY * (1 / COLUMN_FILL)
    capacity = geom.printable_h
    return {
        "estimated_height_pt": round(total, 1),
        "capacity_pt": round(capacity, 1),
        "fills": round(total / capacity, 3) if capacity else None,
        "sections": len(parser.sections),
        "grid_rows": len(rows),
        "column_width_pt": round(geom.column_w, 1),
        "chars_per_line": round(geom.chars_per_line, 1),
        "font_pt": geom.font_pt,
        "margin_in": round(geom.margin / PT_PER_IN, 3),
        "fits_one_page": total <= capacity,
        "section_heights_pt": [round(h, 1) for h in heights],
        "header_lines": {"title": len(parser.h1_text.split()),
                         "confidential": len(parser.conf_text.split()),
                         "footer": len(parser.footer_text.split())},
    }


def check(html_text: str, css_text: str) -> dict:
    """Measure the brief and raise if it is estimated not to fit one sheet."""
    report = measure(html_text, css_text)
    if not report["fits_one_page"]:
        raise SystemExit(
            "Print budget failed: the Attorney and CPA brief is estimated at "
            f"{report['estimated_height_pt']}pt against {report['capacity_pt']}pt of usable "
            f"page height ({report['fills']:.0%} of a sheet). Shorten the brief or the print "
            "rules; the one-page claim is published.")
    return report


def main(argv: list[str] | None = None) -> int:
    """Measure a brief file against a stylesheet, from the command line.

    ``python3 scripts/print_budget.py BRIEF.html [STYLE.css]``

    The stylesheet defaults to the one this repository ships. The exit code is
    0 when the brief is estimated to fit one sheet and 1 when it is not, so
    the command can be used as a check in its own right.
    """
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__)
        return 2
    html_path = Path(args[0])
    css_path = Path(args[1]) if len(args) > 1 else Path(__file__).resolve().parents[1] / "assets" / "style.css"
    report = measure(html_path.read_text(encoding="utf-8"), css_path.read_text(encoding="utf-8"))
    print(format_report(report))
    return 0 if report["fits_one_page"] else 1


def format_report(report: dict) -> str:
    """A one-line description for the published page."""
    verdict = "fits" if report["fits_one_page"] else "does not fit"
    return (f"estimated at {report['fills']:.0%} of one letter sheet "
            f"({report['estimated_height_pt']:.0f}pt against {report['capacity_pt']:.0f}pt of usable "
            f"page height), across {report['sections']} sections in {report['grid_rows']} grid rows; "
            f"{verdict} one page")


if __name__ == "__main__":
    raise SystemExit(main())
