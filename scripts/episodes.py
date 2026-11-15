"""Real historical entry-timing replays for the black-swan page.

Reads  : assets/data/episodes.json, assets/data/episodes/*.csv,
         assets/data/inputs.json (rounding convention only)
Writes : nothing. Imported by scripts/model.py, which writes assets/data/model.json.

Why this module exists
----------------------
The site's earlier crash-entry test used an invented crash sequence (-40%, +25%,
+10%). The owner asked for real 1929- and 2008-style conditions, so this module
replays the actual monthly price history of those episodes, fetched from the
publisher's own domain and stored verbatim beside this code.

Method, stated plainly
----------------------
For each episode the same amount of net sale proceeds enters three strategies.
The amount is chosen so the nominal result can be read in today's money either
way: $1,000,000 of start-year purchasing power, which means the amount is scaled
by the consumer price index at the entry month.

  1. lump     buy the index at the entry month's level and hold to the exit.
  2. phase    earn the official short cash rate for the parking period, then buy
              the index in twelve equal monthly purchases.
  3. park34   earn the official short cash rate for 34 months, then buy the index
              in one purchase in month 35. This separates the waiting period from
              the phase-in.

All three end holding the same index at the exit month, so the comparison is the
number of index units the money bought. Two of the three are never out of the
market for a single month; the third misses the parking window entirely.

Everything is deterministic. There is no randomness and no fitting anywhere in
this module, and every dollar figure is rounded to the nearest $10.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data"
EPISODES = json.loads((DATA / "episodes.json").read_text(encoding="utf-8"))

START_POWER = 1_000_000          # $1,000,000 of entry-month purchasing power
PARK_MONTHS = 30                 # midpoint of the owner's 24-36 month window
PHASE_MONTHS = 12                # equal monthly purchases after the park
LATE_PARK_MONTHS = 34            # the "park the whole 34 months" variant
BASE_CPI_MONTH = "2026-10"       # latest published month, used to express results today


def money10(x: float) -> int:
    """Round to the nearest $10, halves up, exactly as the rest of the model does."""
    return int((abs(x) + 5.0) // 10 * 10) * (1 if x >= 0 else -1)


def _month_key(date: str) -> str:
    return date[:7]


def load_series(key: str) -> dict[str, float]:
    """Read one stored CSV verbatim and return {YYYY-MM: value}."""
    spec = EPISODES["series"][key]
    path = DATA / "episodes" / spec["file"]
    out: dict[str, float] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    if header[1] != spec["column"]:
        raise SystemExit(f"{path}: column header {header[1]!r} is not {spec['column']!r}")
    for line in lines[1:]:
        if not line.strip():
            continue
        date, raw = line.split(",")
        if not raw.strip():
            continue          # a published blank is left blank, never filled
        out[_month_key(date)] = float(raw)
    return out


SERIES = {key: load_series(key) for key in EPISODES["series"]}
CPI = SERIES["cpi"]


def month_range(start: str, end: str) -> list[str]:
    y0, m0 = (int(p) for p in start.split("-"))
    y1, m1 = (int(p) for p in end.split("-"))
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def price(series: dict[str, float], month: str) -> float:
    if month not in series:
        raise SystemExit(f"no published value for {month}: the replay cannot be built by interpolation")
    return series[month]


def replay(ep: dict, entry_override: str | None = None, park: int | None = None) -> dict:
    """Run the three entry strategies over one episode's real monthly prices.

    Units of the index are bought at a month's published close and then simply
    held. A held unit does not change, so the only index prices needed are the
    entry close, the purchase months and the exit close. The cash balance earns
    the published short rate of each month it is actually held, so a 1929 replay
    needs cash rates for the parking window only - which is why the stored call
    money file stops in 1932 without leaving a hole.
    """
    entry = entry_override or ep["entry"]
    park_months = PARK_MONTHS if park is None else park
    months = month_range(entry, ep["exit"])
    eq = SERIES[ep["eq"]]
    cash = SERIES[ep["cash"]]

    cpi_entry = price(CPI, entry)
    base_cpi = price(CPI, BASE_CPI_MONTH)
    # $1,000,000 of today's purchasing power, converted back to the entry month.
    # CPI is a price index (1982-84 = 100), so this is a ratio, not a level.
    principal = START_POWER * cpi_entry / base_cpi
    entry_price = price(eq, entry)
    exit_price = price(eq, ep["exit"])

    def park_then_buy(park: int, phase: int) -> float:
        """Park the balance for `park` months, then buy over `phase` months."""
        balance = principal
        units = 0.0
        chunk = principal / phase if phase else principal
        in_cash = True
        for idx in range(1, len(months)):
            if not in_cash:
                break                                # every dollar is in the index
            month = months[idx]
            rate = price(cash, month) / 100.0        # rate for the month being traversed
            balance *= (1 + rate) ** (1 / 12)
            if idx > park:
                take = min(chunk, balance)
                balance -= take
                units += take / price(eq, month)
                if park + phase >= len(months) - 1 or balance <= 1e-9:
                    in_cash = False
        return units

    units_held = {
        # Strategy 1: everything in at the entry close, held to the exit.
        "lump": principal / entry_price,
        # Strategy 2: 30 months of cash, then twelve equal monthly purchases.
        "phase": park_then_buy(park_months, PHASE_MONTHS),
        # Strategy 3: 34 months of cash, then one purchase.
        "park34": park_then_buy(LATE_PARK_MONTHS, 1),   # the "whole park, then buy" variant
    }

    exit_cpi = price(CPI, ep["exit"])
    out = {
        "key": ep["key"],
        "name": ep["name"],
        "entry": entry,
        "exit": ep["exit"],
        "months": len(months) - 1,
        "analogue": ep["analogue"],
        "notes": ep["notes"],
        "src": ep["src"],
        "principal": money10(principal),
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "peak_label": ep["peak_label"],
        "series_name": EPISODES["series"][ep["eq"]]["title"],
        "cash_name": EPISODES["series"][ep["cash"]]["title"],
        "strategies": {},
    }
    for name, units in units_held.items():
        nominal = units * exit_price
        out["strategies"][name] = {
            "units": round(units, 2),
            "nominal": money10(nominal),
            # expressed in October 2026 purchasing power, the same basis for all three
            "real_today": money10(nominal * base_cpi / exit_cpi),
            "start_power": money10(nominal * cpi_entry / exit_cpi),
            "multiple": round(nominal / principal, 3),
        }
    lump_real = out["strategies"]["lump"]["real_today"]
    for name in ("phase", "park34"):
        out["strategies"][name]["vs_lump"] = money10(
            out["strategies"][name]["real_today"] - lump_real)
    out["strategies"]["phase"]["vs_park34"] = money10(
        out["strategies"]["phase"]["real_today"] - out["strategies"]["park34"]["real_today"])
    out["lump_real_today"] = lump_real
    out["best"] = max(("lump", "phase", "park34"),
                      key=lambda k: out["strategies"][k]["real_today"])
    return out


def park_sensitivity() -> list[dict]:
    """The owner asked for a 24-36 month window, so both ends are priced.

    Each row re-runs the same episode with the parking period set to 24, 30 and
    36 months. The phase-in stays at twelve equal monthly purchases.
    """
    rows = []
    for ep in EPISODES["episodes"]:
        for park in (24, 30, 36):
            r = replay(ep, park=park)
            phase = r["strategies"]["phase"]["real_today"]
            lump = r["strategies"]["lump"]["real_today"]
            best = "phase" if phase > lump else "lump"
            rows.append({
                "key": ep["key"],
                "name": ep["name"],
                "park_months": park,
                "phase_real_today": phase,
                "lump_real_today": lump,
                "gap": phase - lump,
                "best": best,
                "best_label": (f"Park {park} months, then phase in over {PHASE_MONTHS}"
                               if best == "phase" else "Invest on day one"),
                "src": ep["src"],
            })
    return rows


def offset_sensitivity() -> list[dict]:
    """What if the heir did not inherit at the peak, but a year or two after it?

    Nobody knows a peak is a peak until afterwards. This re-runs each episode with
    the entry moved twelve and twenty-four months later, holding the exit fixed, so
    the table shows how much of the parking result depends on the crash starting
    almost immediately after the inheritance.
    """
    rows = []
    for ep in EPISODES["episodes"]:
        months = month_range(ep["entry"], ep["exit"])
        for offset in (0, 12, 24):
            if offset >= len(months) - 24:
                continue
            entry = months[offset]
            r = replay(ep, entry_override=entry)
            phase = r["strategies"]["phase"]["real_today"]
            lump = r["strategies"]["lump"]["real_today"]
            best = "phase" if phase > lump else "lump"
            rows.append({
                "key": ep["key"],
                "name": ep["name"],
                "offset_months": offset,
                "entry": entry,
                "lump_real_today": lump,
                "phase_real_today": phase,
                "gap": phase - lump,
                "best": best,
                "best_label": (f"Park {PARK_MONTHS} months, then phase in over {PHASE_MONTHS}"
                               if best == "phase" else "Invest on day one"),
                "src": ep["src"],
            })
    return rows


def inverse_replay(ep: dict, crash_offset_months: int) -> dict:
    """The realistic unlucky case: inheritance now, the crash arrives later.

    The money enters the index at the episode's peak month. The crash is then
    aligned so that it begins `crash_offset_months` after the inheritance, using
    the episode's own monthly prices, and the comparison runs from the
    inheritance month for the episode's full horizon. The phased strategy parks
    for the window the owner asked for and phases in over twelve months; the
    lump strategy is fully invested from the start.
    """
    eq = SERIES[ep["eq"]]
    cash = SERIES[ep["cash"]]
    entry = ep["entry"]
    # take the episode's price path, then shift it later in time
    path_months = month_range(ep["entry"], ep["exit"])
    eq_path = [price(eq, m) for m in path_months]
    # cash rates are only needed for the first park+phase months, where the stored
    # call money file is complete; beyond that the money is in the index
    cash_path = [price(cash, m) if i <= PARK_MONTHS + PHASE_MONTHS else None
                 for i, m in enumerate(path_months)]
    shift = crash_offset_months
    # The comparison may not run past the end of the episode's own record. A short
    # episode therefore produces a shorter comparison, and the table says so.
    horizon = len(path_months) - shift
    if horizon < PARK_MONTHS + PHASE_MONTHS + 1:
        raise SystemExit(f"{ep['key']}: no comparison window left at a {crash_offset_months}-month offset")

    cpi_entry = price(CPI, entry)
    base_cpi = price(CPI, BASE_CPI_MONTH)
    principal = START_POWER * cpi_entry / base_cpi

    # month 0 is the inheritance; the index level in month i is the episode's
    # level i months after its peak, and the cash rate is the same month's rate.
    levels = eq_path[:horizon]
    rates = cash_path[:horizon]

    units_lump = principal / levels[0]

    balance = principal
    units = 0.0
    chunk = principal / PHASE_MONTHS
    in_cash = True
    for i in range(1, horizon):
        if not in_cash:
            break
        if i <= PARK_MONTHS + PHASE_MONTHS:      # cash is held only inside this window
            balance *= (1 + rates[i] / 100.0) ** (1 / 12)
        if i > PARK_MONTHS:
            take = min(chunk, balance)
            balance -= take
            units += take / levels[i]
            if balance <= 1e-9:
                in_cash = False

    exit_level = levels[-1]
    exit_month = path_months[horizon - 1]
    exit_cpi = price(CPI, exit_month)
    real = lambda u: money10(u * exit_level * base_cpi / exit_cpi)
    lump_real, phase_real = real(units_lump), real(units)
    return {
        "key": ep["key"],
        "name": ep["name"],
        "crash_offset_months": crash_offset_months,
        "horizon_months": horizon,
        "lump_real_today": lump_real,
        "phase_real_today": phase_real,
        "gap": phase_real - lump_real,
        "best": "phase" if phase_real > lump_real else "lump",
        "src": ep["src"],
    }


def inverse_sensitivity() -> list[dict]:
    """Crash arriving at different distances after the inheritance."""
    rows = []
    for ep in EPISODES["episodes"]:
        # trailing windows may be shorter than the episode; every row states its own horizon
        for offset in (0, 12, 24, 36):
            try:
                rows.append(inverse_replay(ep, offset))
            except SystemExit:
                continue          # no comparison window is left at this offset
    return rows


def build() -> dict:
    rows = [replay(ep) for ep in EPISODES["episodes"]]
    winners = {}
    for name in ("lump", "phase", "park34"):
        winners[name] = sum(1 for r in rows if r["best"] == name)
    phase_better = [r["key"] for r in rows
                    if r["strategies"]["phase"]["real_today"] > r["strategies"]["lump"]["real_today"]]
    worst_phase_gap = min(rows, key=lambda r: r["strategies"]["phase"]["vs_lump"])
    return {
        "method": EPISODES["meta"]["method"],
        "limits": EPISODES["meta"]["limits"],
        "start_power": START_POWER,
        "park_months": PARK_MONTHS,
        "phase_months": PHASE_MONTHS,
        "late_park_months": LATE_PARK_MONTHS,
        "base_cpi_month": BASE_CPI_MONTH,
        "strategies": {s["key"]: {"name": s["name"], "description": s["description"]}
                       for s in EPISODES["strategies"]},
        "series": {k: {f: v[f] for f in ("publisher", "title", "url", "units", "coverage", "src", "limits")}
                   for k, v in EPISODES["series"].items()},
        "episodes": rows,
        "winners": winners,
        "phase_better_than_lump": phase_better,
        "worst_phase_gap_key": worst_phase_gap["key"],
        "worst_phase_gap": worst_phase_gap["strategies"]["phase"]["vs_lump"],
        "park_sensitivity": park_sensitivity(),
        "offset_sensitivity": offset_sensitivity(),
        "inverse_sensitivity": inverse_sensitivity(),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(build(), width=120, sort_dicts=False)
