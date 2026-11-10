"""Verify the arena-b8f9abd6 research module (standard library only).

Checks: reproducible build; every law/process row cites an https URL on an official host;
every non-statutory dollar output is a multiple of $10; official columns are blank unless
verified; no ZIP-code-like tokens; no forms/scripts/remote assets in the HTML page.
"""
import csv, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
OFFICIAL_HOSTS = ("irs.gov", "ca.gov", "congress.gov")   # *.ca.gov covers BOE, SCO, SOS, CPUC, LAO, leginfo
STATUTORY_EXACT = {"exclusion_amount"}                     # published exact amounts, shown unrounded

def official(url):
    host = urlparse(url).hostname or ""
    return url.startswith("https://") and any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)

def main():
    before = {p.name: p.read_bytes() for p in HERE.iterdir() if p.suffix in (".json", ".csv", ".html")}
    subprocess.check_call([sys.executable, str(HERE / "build_research.py")], stdout=subprocess.DEVNULL)
    after = {p.name: p.read_bytes() for p in HERE.iterdir() if p.suffix in (".json", ".csv", ".html")}
    assert before == after, "generated files are stale: run build_research.py and commit"

    law = json.loads((HERE / "law_watch.json").read_text())["rows"]
    proc = json.loads((HERE / "inheritance_process.json").read_text())
    for row in law + proc["steps"]:
        assert official(row["url"]), f"non-official source: {row}"
    for row in law:
        assert row["status"] in ("verified", "unverified"), row
    ex = proc["prop19_example"]
    for k, v in ex.items():
        if isinstance(v, int) and k not in STATUTORY_EXACT:
            assert v % 10 == 0, (k, v)

    n = 0
    for name in ("estate_threshold_projection.csv", "estate_tax_examples.csv"):
        for row in csv.DictReader(open(HERE / name)):
            for k, v in row.items():
                if v and re.fullmatch(r"-?\d+", v) and k not in ("year", "year_of_death"):
                    assert int(v) % 10 == 0, (name, k, v); n += 1
                if k.endswith("source") and v:
                    assert official(v), (name, k, v)
            if name.startswith("estate_threshold"):
                assert (row["official_basic_exclusion"] == "") == (row["official_status"] != "verified"), row

    for p in HERE.iterdir():
        if p.suffix in (".json", ".csv", ".html", ".md"):
            text = p.read_text()
            assert not re.search(r"(?<![\d,$.])9[0-6]\d{3}(?![\d,])", text), f"ZIP-like token in {p.name}"
    page = (HERE / "law-watch.html").read_text()
    for bad in ("<script", "<form", "<iframe", "src=\"http", "src='http", "<link rel=\"stylesheet\" href=\"http"):
        assert bad not in page, bad
    hrefs = re.findall(r"href='(https?://[^']+)'", page)
    assert hrefs and all(official(h) for h in hrefs), [h for h in hrefs if not official(h)]
    print(f"PASS: {len(law)} law rows + {len(proc['steps'])} steps cite official hosts; "
          f"{n} dollar cells are $10 multiples; {len(hrefs)} page links official; reproducible; no ZIP-like tokens.")

if __name__ == "__main__":
    main()
