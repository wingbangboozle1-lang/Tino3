"""Phased-entry test on the official monthly series.

Question: if the sale proceeds are parked in short Treasuries for a fixed number of
months and only then bought into stocks in equal monthly tranches, how much does that
soften the entry risk compared with buying the index in one lump on the peak month?

Inputs (official, read from the repository, not typed from memory):
  assets/data/crash_1929.csv  NBER macrohistory Dow Jones monthly average (FRED M1109BUSM293NNBR)
                              and NBER 3-to-6 month Treasury notes and certificates (FRED M1329AUSM193NNBR)
  assets/data/crash_2007.csv  FRED NASDAQCOM monthly average, 3-month bill (TB3MS), 2-year note (GS2)

Method, identical for every episode:
  * The index is a price index. Dividends are excluded for both strategies, so the
    comparison between them is like for like but the levels are not total returns.
  * Parked cash earns the month's Treasury yield divided by twelve and compounds monthly.
  * Phased strategy: hold cash for W months, then buy in N equal monthly tranches of the
    cash that remains (N = 12). Lump strategy: buy everything in the entry month.
  * Every figure is per $1,000,000 of sale proceeds. That amount is a normalising unit,
    not the owner's figure, and results are rounded to the nearest $10.

Standard library only. No network access.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"

PRINCIPAL = 1_000_000.0
TRANCHES = 12           # months over which the parked cash is bought into stocks
HORIZON = 96            # months after the entry month that every strategy is valued
WAITS = (24, 30, 36)    # months parked before buying starts


def money10(x: float) -> int:
    return int((abs(x) + 5.0) // 10 * 10) * (1 if x >= 0 else -1)


def load(path: Path, mapping: dict[str, str]) -> tuple[list[str], dict[str, dict[str, float | None]]]:
    """Read a series CSV. mapping maps CSV header -> short key used by the tests."""
    months: list[str] = []
    data: dict[str, dict[str, float | None]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            m = row["month"]
            months.append(m)
            data[m] = {key: (float(row[hdr]) if row[hdr].strip() else None)
                       for hdr, key in mapping.items()}
    return months, data


def run_strategy(levels: list[float], yields_pct: list[float | None], wait: int | None,
                 tranches: int = TRANCHES) -> dict:
    """Value one strategy along a monthly path of index levels.

    levels[t] is the index at the start of month t (t = 0 is the entry month).
    yields_pct[t] is the parking yield earned during month t (annual percent).
    wait=None means the lump-sum strategy.
    """
    horizon = len(levels) - 1
    cash = PRINCIPAL
    units = 0.0
    values: list[float] = []
    for t in range(horizon + 1):
        if wait is None:
            if t == 0:
                units = PRINCIPAL / levels[0]
                cash = 0.0
        elif wait <= t < wait + tranches and cash > 0:
            k = t - wait
            spend = cash / (tranches - k)
            units += spend / levels[t]
            cash -= spend
        values.append(cash + units * levels[t])
        if t < horizon and cash > 0:
            y = yields_pct[t]
            if y is None:
                raise ValueError("parking yield missing inside the test window")
            cash *= 1.0 + y / 100.0 / 12.0
    peak = values[0]
    worst_dd = 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            worst_dd = max(worst_dd, (peak - v) / peak)
    low_t = min(range(len(values)), key=lambda t: values[t])
    never_below_cost = min(values) >= PRINCIPAL - 0.005
    recovered = None
    if not never_below_cost:
        for t in range(low_t, len(values)):
            if values[t] >= PRINCIPAL:
                recovered = t
                break
    return {
        "terminal": money10(values[-1]),
        "terminal_multiple": round(values[-1] / PRINCIPAL, 3),
        "worst_value": money10(values[low_t]),
        "worst_change_pct": round((values[low_t] / PRINCIPAL - 1.0) * 100.0, 1),
        "worst_at_month": low_t,
        "max_drawdown_pct": round(worst_dd * 100.0, 1),
        "never_below_cost": never_below_cost,
        "recovered_at_month": recovered,
        "final_cash_share_pct": round(cash / values[-1] * 100.0, 1) if values[-1] else 0.0,
    }


def run_episode(months, data, key: str, cash_col: str, entry: str, horizon: int = HORIZON) -> dict:
    i0 = months.index(entry)
    window = months[i0: i0 + horizon + 1]
    if len(window) != horizon + 1:
        raise ValueError(f"{entry}: not enough months for a {horizon}-month horizon")
    levels = [data[m][key] for m in window]
    if any(v is None for v in levels):
        raise ValueError(f"{entry}: index level missing")
    yields = [data[m][cash_col] for m in window]
    out = {"entry": entry, "cash": cash_col, "horizon_months": horizon,
           "entry_level": levels[0], "strategies": {}}
    out["strategies"]["lump"] = run_strategy(levels, yields, None)
    for w in WAITS:
        out["strategies"][f"phased_{w}"] = run_strategy(levels, yields, w)
    out["strategies"]["lump"]["label"] = "Lump sum on the entry month"
    for w in WAITS:
        out["strategies"][f"phased_{w}"]["label"] = f"Park {w} months, then buy over {TRANCHES}"
    out["window_first"] = window[0]
    out["window_last"] = window[-1]
    return out


def sweep(months, data, key: str, cash_col: str, entries: list[str], horizon: int = HORIZON) -> dict:
    """Run every entry month in a window and report how often each phased path beat the lump."""
    rows = []
    for e in entries:
        ep = run_episode(months, data, key, cash_col, e, horizon)
        lump = ep["strategies"]["lump"]["terminal"]
        row = {"entry": e, "lump_terminal": lump,
               "lump_worst_pct": ep["strategies"]["lump"]["worst_change_pct"]}
        for w in WAITS:
            ph = ep["strategies"][f"phased_{w}"]
            row[f"phased_{w}_terminal"] = ph["terminal"]
            row[f"phased_{w}_worst_pct"] = ph["worst_change_pct"]
            row[f"phased_{w}_beats_lump"] = ph["terminal"] > lump
        rows.append(row)
    summary = {}
    for w in WAITS:
        beats = sum(1 for r in rows if r[f"phased_{w}_beats_lump"])
        summary[f"phased_{w}"] = {
            "entries": len(rows),
            "beats_lump": beats,
            "worst_worst_pct": min(r[f"phased_{w}_worst_pct"] for r in rows),
            "median_terminal_vs_lump_pct": round(
                sorted((r[f"phased_{w}_terminal"] / r["lump_terminal"] - 1) * 100 for r in rows)[len(rows) // 2], 1),
        }
    return {"rows": rows, "summary": summary,
            "lump_worst_pct_range": [min(r["lump_worst_pct"] for r in rows),
                                     max(r["lump_worst_pct"] for r in rows)]}


def run_all() -> dict:
    m29, d29 = load(DATA / "crash_1929.csv", {
        "dow_jones_industrial_monthly_average_nbr_m11009b": "dow",
        "treasury_3to6m_pct_nbr_m13029a": "cash_3to6m"})
    m07, d07 = load(DATA / "crash_2007.csv", {
        "nasdaq_composite_monthly_average": "nasdaq",
        "treasury_3m_bill_pct_fred_TB3MS": "tb3m",
        "treasury_2y_note_pct_fred_GS2": "gs2"})

    episodes = {
        "crash_1929": {
            "title": "Entry at the September 1929 peak (monthly average)",
            "index": "Dow Jones Industrial Average, monthly average (NBER, via FRED)",
            "cash": "3-to-6-month Treasury notes and certificates (NBER, via FRED)",
            "result": run_episode(m29, d29, "dow", "cash_3to6m", "1929-09"),
            "anchors": {"peak_daily": 381.17, "peak_date": "3 September 1929",
                        "trough_daily": 41.22, "trough_date": "8 July 1932",
                        "recovery_date": "23 November 1954"},
        },
        "crash_2007": {
            "title": "Entry at the October 2007 peak (monthly average)",
            "index": "NASDAQ Composite, monthly average (FRED NASDAQCOM); proxy for a broad stock index",
            "cash": "3-month Treasury bill (FRED TB3MS)",
            "result": run_episode(m07, d07, "nasdaq", "tb3m", "2007-10"),
        },
        "crash_2007_2y": {
            "title": "Entry at the October 2007 peak, parked in 2-year Treasuries",
            "index": "NASDAQ Composite, monthly average (FRED NASDAQCOM); proxy for a broad stock index",
            "cash": "2-year Treasury note (FRED GS2)",
            "result": run_episode(m07, d07, "nasdaq", "gs2", "2007-10"),
        },
        "sweep_1929": {
            "title": "Sensitivity: every entry month in 1929",
            "index": "Dow Jones Industrial Average, monthly average (NBER, via FRED)",
            "cash": "3-to-6-month Treasury notes and certificates (NBER, via FRED)",
            "result": sweep(m29, d29, "dow", "cash_3to6m", [f"1929-{m:02d}" for m in range(1, 13)]),
        },
        "sweep_2007": {
            "title": "Sensitivity: every entry month from October 2007 to June 2008",
            "index": "NASDAQ Composite, monthly average (FRED NASDAQCOM); proxy for a broad stock index",
            "cash": "3-month Treasury bill (FRED TB3MS)",
            "result": sweep(m07, d07, "nasdaq", "tb3m", [f"{y}-{m:02d}" for y, m in
                            [(2007, 10), (2007, 11), (2007, 12)] + [(2008, m) for m in range(1, 7)]]),
        },
        "control_2012": {
            "title": "Control: entry in January 2012, when the market was not falling",
            "index": "NASDAQ Composite, monthly average (FRED NASDAQCOM); proxy for a broad stock index",
            "cash": "3-month Treasury bill (FRED TB3MS)",
            "result": run_episode(m07, d07, "nasdaq", "tb3m", "2012-01"),
        },
    }
    return {
        "meta": {
            "method": ("Price indices only; dividends excluded for both strategies. Parked cash earns the "
                       "month's Treasury yield divided by twelve. Phased strategies wait the stated months, "
                       f"then buy in {TRANCHES} equal monthly tranches of the remaining cash. Every value is "
                       f"per $1,000,000 of proceeds and rounded to $10. Valued {HORIZON} months after entry."),
            "tranches": TRANCHES,
            "horizon_months": HORIZON,
            "waits": list(WAITS),
            "limits": ("The 1929 episode uses monthly averages, so its peak and trough differ from the "
                       "daily closes published by the Federal Reserve. The 2007 episode uses NASDAQ "
                       "Composite because the FRED monthly S&P 500 and Dow pages returned by the source "
                       "began in December 2016 and could not be used for 2007 to 2010."),
        },
        "episodes": episodes,
    }


if __name__ == "__main__":
    import json
    res = run_all()
    OUT = DATA / "crash.json"
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for key, ep in res["episodes"].items():
        r = ep["result"]
        if "strategies" not in r:
            print(key, "sweep", r["summary"], "lump worst range", r["lump_worst_pct_range"])
            continue
        print(key, r["entry"], r["cash"])
        for sk, sv in r["strategies"].items():
            print(f"   {sk:12s} terminal {sv['terminal']:>12,}  worst {sv['worst_change_pct']:>7}%  "
                  f"maxDD {sv['max_drawdown_pct']:>5}%  never_below_cost {sv['never_below_cost']} recovered {sv['recovered_at_month']}")
    print("wrote", OUT.relative_to(ROOT))
