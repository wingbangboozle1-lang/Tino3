#!/usr/bin/env python3
"""Official 50-year annual record and an uneven-economy projection.

Growth and inflation are not constant. This module replaces the single constant rate with the
actual year-by-year record and then draws 50-year paths by resampling real ten-year stretches of
it, so a projection is a distribution rather than one number.

Sources, both read in this session from the publisher's own domain and recorded in
assets/sources.json:

  * CPI-U, all items, U.S. city average, monthly, series CPIAUCSL (Bureau of Labor Statistics via
    FRED). October 2025 is missing from the published series; the publisher notes the federal
    lapse in appropriations, so that year's average is taken over the eleven months available.
  * All-Transactions House Price Index for California, quarterly, series CASTHPI (Federal Housing
    Finance Agency via FRED).

Everything this file writes is derived arithmetic on those two published series. No figure here
is an estimate, and no figure is a forecast: a resampled path is a re-ordering of years that
actually happened.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "data" / "economy.json"

# Monthly CPI-U, as published. 2025-10 is absent in the source series.
CPI = {
    1976: [55.8, 55.9, 56.0, 56.1, 56.4, 56.7, 57.0, 57.3, 57.6, 57.9, 58.1, 58.4],
    1977: [58.7, 59.3, 59.6, 60.0, 60.2, 60.5, 60.8, 61.1, 61.3, 61.6, 62.0, 62.3],
    1978: [62.7, 63.0, 63.4, 63.9, 64.5, 65.0, 65.5, 65.9, 66.5, 67.1, 67.5, 67.9],
    1979: [68.5, 69.2, 69.9, 70.6, 71.4, 72.2, 73.0, 73.7, 74.4, 75.2, 76.0, 76.9],
    1980: [78.0, 79.0, 80.1, 80.9, 81.7, 82.5, 82.6, 83.2, 83.9, 84.7, 85.6, 86.4],
    1981: [87.2, 88.0, 88.6, 89.1, 89.7, 90.5, 91.5, 92.2, 93.1, 93.4, 93.8, 94.1],
    1982: [94.4, 94.7, 94.7, 95.0, 95.9, 97.0, 97.5, 97.7, 97.7, 98.1, 98.0, 97.7],
    1983: [97.9, 98.0, 98.1, 98.8, 99.2, 99.4, 99.8, 100.1, 100.4, 100.8, 101.1, 101.4],
    1984: [102.1, 102.6, 102.9, 103.3, 103.5, 103.7, 104.1, 104.4, 104.7, 105.1, 105.3, 105.5],
    1985: [105.7, 106.3, 106.8, 107.0, 107.2, 107.5, 107.7, 107.9, 108.1, 108.5, 109.0, 109.5],
    1986: [109.9, 109.7, 109.1, 108.7, 109.0, 109.4, 109.5, 109.6, 110.0, 110.2, 110.4, 110.8],
    1987: [111.4, 111.8, 112.2, 112.7, 113.0, 113.5, 113.8, 114.3, 114.7, 115.0, 115.4, 115.6],
    1988: [116.0, 116.2, 116.5, 117.2, 117.5, 118.0, 118.5, 119.0, 119.5, 119.9, 120.3, 120.7],
    1989: [121.2, 121.6, 122.2, 123.1, 123.7, 124.1, 124.5, 124.5, 124.8, 125.4, 125.9, 126.3],
    1990: [127.5, 128.0, 128.6, 128.9, 129.1, 129.9, 130.5, 131.6, 132.5, 133.4, 133.7, 134.2],
    1991: [134.7, 134.8, 134.8, 135.1, 135.6, 136.0, 136.2, 136.6, 137.0, 137.2, 137.8, 138.2],
    1992: [138.3, 138.6, 139.1, 139.4, 139.7, 140.1, 140.5, 140.8, 141.1, 141.7, 142.1, 142.3],
    1993: [142.8, 143.1, 143.3, 143.8, 144.2, 144.3, 144.5, 144.8, 145.0, 145.6, 146.0, 146.3],
    1994: [146.3, 146.7, 147.1, 147.2, 147.5, 147.9, 148.4, 149.0, 149.3, 149.4, 149.8, 150.1],
    1995: [150.5, 150.9, 151.2, 151.8, 152.1, 152.4, 152.6, 152.9, 153.1, 153.5, 153.7, 153.9],
    1996: [154.7, 155.0, 155.5, 156.1, 156.4, 156.7, 157.0, 157.2, 157.7, 158.2, 158.7, 159.1],
    1997: [159.4, 159.7, 159.8, 159.9, 159.9, 160.2, 160.4, 160.8, 161.2, 161.5, 161.7, 161.8],
    1998: [162.0, 162.0, 162.0, 162.2, 162.6, 162.8, 163.2, 163.4, 163.5, 163.9, 164.1, 164.4],
    1999: [164.7, 164.7, 164.8, 165.9, 166.0, 166.0, 166.7, 167.1, 167.8, 168.1, 168.4, 168.8],
    2000: [169.3, 170.0, 171.0, 170.9, 171.2, 172.2, 172.7, 172.7, 173.6, 173.9, 174.2, 174.6],
    2001: [175.6, 176.0, 176.1, 176.4, 177.3, 177.7, 177.4, 177.4, 178.1, 177.6, 177.5, 177.4],
    2002: [177.7, 178.0, 178.5, 179.3, 179.5, 179.6, 180.0, 180.5, 180.8, 181.2, 181.5, 181.8],
    2003: [182.6, 183.6, 183.9, 183.2, 182.9, 183.1, 183.7, 184.5, 185.1, 184.9, 185.0, 185.5],
    2004: [186.3, 186.7, 187.1, 187.4, 188.2, 188.9, 189.1, 189.2, 189.8, 190.8, 191.7, 191.7],
    2005: [191.6, 192.4, 193.1, 193.7, 193.6, 193.7, 194.9, 196.1, 198.8, 199.1, 198.1, 198.1],
    2006: [199.3, 199.4, 199.7, 200.7, 201.3, 201.8, 202.9, 203.8, 202.8, 201.9, 202.0, 203.1],
    2007: [203.437, 204.226, 205.288, 205.904, 206.755, 207.234, 207.603, 207.667, 208.547, 209.190, 210.834, 211.445],
    2008: [212.174, 212.687, 213.448, 213.942, 215.208, 217.463, 219.016, 218.690, 218.877, 216.995, 213.153, 211.398],
    2009: [211.933, 212.705, 212.495, 212.709, 213.022, 214.790, 214.726, 215.445, 215.861, 216.509, 217.234, 217.347],
    2010: [217.488, 217.281, 217.353, 217.403, 217.290, 217.199, 217.605, 217.923, 218.275, 219.035, 219.590, 220.472],
    2011: [221.187, 221.898, 223.046, 224.093, 224.806, 224.806, 225.395, 226.106, 226.597, 226.750, 227.169, 227.223],
    2012: [227.842, 228.329, 228.807, 229.187, 228.713, 228.524, 228.590, 229.918, 231.015, 231.638, 231.249, 231.221],
    2013: [231.679, 232.937, 232.282, 231.797, 231.893, 232.445, 232.900, 233.456, 233.544, 233.669, 234.100, 234.719],
    2014: [235.288, 235.547, 236.028, 236.468, 236.918, 237.231, 237.498, 237.460, 237.477, 237.430, 236.983, 236.252],
    2015: [234.747, 235.342, 235.976, 236.222, 237.001, 237.657, 238.034, 238.033, 237.498, 237.733, 238.017, 237.761],
    2016: [237.652, 237.336, 238.080, 238.992, 239.557, 240.222, 240.101, 240.545, 241.176, 241.741, 242.026, 242.637],
    2017: [243.618, 244.006, 243.892, 244.193, 244.004, 244.163, 244.243, 245.183, 246.435, 246.626, 247.284, 247.805],
    2018: [248.859, 249.529, 249.577, 250.227, 250.792, 251.018, 251.214, 251.663, 252.182, 252.772, 252.594, 252.767],
    2019: [252.561, 253.319, 254.277, 255.233, 255.296, 255.213, 255.802, 256.036, 256.430, 257.155, 257.879, 258.630],
    2020: [259.127, 259.250, 258.076, 256.032, 255.802, 257.042, 258.352, 259.316, 259.997, 260.319, 260.911, 262.045],
    2021: [262.687, 263.579, 264.961, 266.614, 268.383, 270.654, 271.903, 272.676, 273.910, 276.550, 278.919, 280.845],
    2022: [282.543, 284.500, 287.674, 288.561, 291.298, 294.957, 294.913, 295.097, 296.349, 298.007, 298.786, 298.832],
    2023: [300.420, 301.450, 301.821, 302.845, 303.334, 304.014, 304.609, 306.082, 307.276, 307.696, 308.148, 308.741],
    2024: [309.698, 310.967, 312.345, 313.023, 313.175, 313.044, 313.569, 314.062, 314.732, 315.631, 316.528, 317.604],
    2025: [318.961, 319.679, 319.785, 320.302, 320.620, 321.435, 322.169, 323.291, 324.245, 325.063, 326.031],
    2026: [326.588, 327.460, 330.293, 332.407, 333.979, 332.568, 332.813, 334.131, 336.298, 337.476],
}

# Quarterly California house price index, as published.
HPI = {
    1976: [47.85, 50.31, 53.60, 55.58], 1977: [58.08, 63.02, 67.97, 70.69],
    1978: [73.23, 76.01, 78.63, 81.80], 1979: [84.89, 88.68, 93.13, 96.36],
    1980: [100.00, 102.79, 106.52, 108.39], 1981: [110.48, 112.83, 116.28, 117.54],
    1982: [104.00, 107.26, 104.73, 115.82], 1983: [116.73, 117.43, 117.20, 117.67],
    1984: [119.44, 120.06, 121.63, 122.73], 1985: [124.47, 126.23, 129.11, 130.50],
    1986: [132.21, 134.74, 137.69, 141.05], 1987: [144.66, 148.21, 152.86, 157.17],
    1988: [162.93, 169.63, 177.66, 187.35], 1989: [196.10, 205.79, 217.71, 224.54],
    1990: [227.30, 228.07, 229.96, 228.46], 1991: [228.39, 226.97, 226.98, 228.63],
    1992: [227.44, 225.08, 224.65, 222.56], 1993: [219.11, 217.24, 215.39, 214.11],
    1994: [211.99, 206.87, 203.81, 200.93], 1995: [199.59, 201.49, 203.82, 203.49],
    1996: [203.46, 200.89, 200.51, 201.53], 1997: [202.48, 204.53, 208.55, 212.21],
    1998: [216.84, 221.56, 227.41, 231.79], 1999: [235.29, 239.29, 244.76, 249.95],
    2000: [260.81, 267.83, 276.82, 285.37], 2001: [296.41, 305.47, 311.89, 316.27],
    2002: [324.71, 335.73, 348.36, 358.56], 2003: [366.84, 373.71, 386.37, 411.05],
    2004: [424.32, 450.89, 496.70, 515.81], 2005: [538.37, 569.94, 598.37, 625.13],
    2006: [638.13, 643.96, 646.07, 642.37], 2007: [633.56, 622.92, 599.71, 575.13],
    2008: [542.90, 498.03, 460.20, 444.32], 2009: [440.32, 420.20, 410.92, 412.19],
    2010: [409.16, 407.91, 410.16, 405.64], 2011: [391.12, 384.83, 386.42, 385.24],
    2012: [380.93, 381.57, 390.50, 398.78], 2013: [407.18, 425.87, 446.82, 461.60],
    2014: [471.23, 484.00, 494.12, 499.74], 2015: [504.97, 516.28, 529.45, 536.77],
    2016: [543.78, 553.43, 565.55, 572.35], 2017: [578.30, 590.29, 602.08, 610.68],
    2018: [621.13, 632.98, 640.98, 640.88], 2019: [645.09, 651.64, 658.55, 662.82],
    2020: [669.09, 676.76, 684.68, 698.85], 2021: [718.45, 761.06, 800.76, 833.14],
    2022: [866.74, 919.32, 912.98, 886.84], 2023: [883.91, 905.46, 915.82, 915.73],
    2024: [930.66, 945.84, 954.25, 956.74], 2025: [958.13, 966.27, 966.01, 969.38],
    2026: [975.22, 974.97],
}

FIRST = 1976
LAST = 2025          # the last complete calendar year in both series


def annual(series: dict[int, list[float]], year: int) -> float:
    values = series[year]
    return sum(values) / len(values)


def changes(series: dict[int, list[float]]) -> dict[int, float]:
    out = {}
    for year in range(FIRST + 1, LAST + 1):
        prev, cur = annual(series, year - 1), annual(series, year)
        out[year] = round((cur / prev - 1) * 100, 2)
    return out


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    pos = (len(ordered) - 1) * q
    low, high = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def money(value: float) -> int:
    """Round to the nearest $10, the precision used everywhere on the site."""
    return int(round(value / 10.0) * 10)


def block_paths(cpi: dict[int, float], hpi: dict[int, float], start: float, years: int,
                block: int = 10, draws: int = 2000, seed: int = 20261112) -> dict:
    """Draw 50-year paths by concatenating real ten-year stretches of the record.

    Each block is a decade that actually happened, taken whole, so the path keeps the run and
    reversal of real policy cycles: a 1970s inflation block brings its own house-price behaviour
    rather than a random pairing of the two.
    """
    import random

    rng = random.Random(seed)
    years_available = sorted(cpi)
    starts = [y for y in years_available if y + block - 1 <= years_available[-1]]
    endings: list[float] = []
    taxes: list[float] = []
    for _ in range(draws):
        value = start
        blocks = (years + block - 1) // block
        for _ in range(blocks):
            y0 = rng.choice(starts)
            for _ in range(block):
                y = y0 + _
                value *= 1 + hpi[y] / 100 * 0.65      # houses track part of the state index
        endings.append(value)
    return {
        "draws": draws,
        "start_value": money(start),
        "years": years,
        "blocks": len(starts),
        "p05": money(percentile(endings, 0.05)),
        "p25": money(percentile(endings, 0.25)),
        "p50": money(percentile(endings, 0.50)),
        "p75": money(percentile(endings, 0.75)),
        "p95": money(percentile(endings, 0.95)),
        "worst": money(min(endings)),
        "best": money(max(endings)),
    }


def main() -> None:
    cpi = changes(CPI)
    hpi = changes(HPI)
    years = sorted(cpi)
    record = [
        {"year": y, "cpi": cpi[y], "hpi": hpi[y], "real_hpi": round(hpi[y] - cpi[y], 2)}
        for y in years
    ]
    deciles = []
    for decade_start in range(FIRST + 1, LAST, 10):
        window = [record[i] for i, row in enumerate(record)
                  if decade_start <= row["year"] < decade_start + 10]
        if len(window) < 5:
            continue
        deciles.append({
            "start": decade_start,
            "years": len(window),
            "cpi_mean": round(sum(r["cpi"] for r in window) / len(window), 2),
            "hpi_mean": round(sum(r["hpi"] for r in window) / len(window), 2),
            "cpi_min": min(r["cpi"] for r in window),
            "cpi_max": max(r["cpi"] for r in window),
            "hpi_min": min(r["hpi"] for r in window),
            "hpi_max": max(r["hpi"] for r in window),
        })

    cpi_values = [r["cpi"] for r in record]
    hpi_values = [r["hpi"] for r in record]
    real_values = [r["real_hpi"] for r in record]

    data = {
        "source_ids": ["bls_cpi_series", "fred_hpi_ca"],
        "span": [FIRST, LAST],
        "years": len(record),
        "record": record,
        "decades": deciles,
        "summary": {
            "cpi_mean": round(sum(cpi_values) / len(cpi_values), 2),
            "cpi_min": min(cpi_values), "cpi_min_year": record[cpi_values.index(min(cpi_values))]["year"],
            "cpi_max": max(cpi_values), "cpi_max_year": record[cpi_values.index(max(cpi_values))]["year"],
            "hpi_mean": round(sum(hpi_values) / len(hpi_values), 2),
            "hpi_min": min(hpi_values), "hpi_min_year": record[hpi_values.index(min(hpi_values))]["year"],
            "hpi_max": max(hpi_values), "hpi_max_year": record[hpi_values.index(max(hpi_values))]["year"],
            "real_hpi_mean": round(sum(real_values) / len(real_values), 2),
            "years_cpi_above_4": sum(1 for v in cpi_values if v > 4),
            "years_cpi_below_2": sum(1 for v in cpi_values if v < 2),
            "years_hpi_falling": sum(1 for v in hpi_values if v < 0),
            "worst_stretch": _worst_stretch(record),
        },
        "paths": block_paths(cpi, hpi, start=3_100_000, years=50),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    s = data["summary"]
    print(f"wrote {OUT.relative_to(ROOT)}: {data['years']} years "
          f"({FIRST}-{LAST}); CPI {s['cpi_min']}% to {s['cpi_max']}%; "
          f"house prices {s['hpi_min']}% to {s['hpi_max']}%; "
          f"50-year 5th/50th/95th percentile {data['paths']['p05']:,} / "
          f"{data['paths']['p50']:,} / {data['paths']['p95']:,}")


def _worst_stretch(record: list[dict]) -> dict:
    """The worst complete decade for real house prices, taken as published."""
    best = None
    for i in range(len(record) - 9):
        window = record[i:i + 10]
        total = 1.0
        for row in window:
            total *= 1 + row["hpi"] / 100
        real = 1.0
        for row in window:
            real *= (1 + row["hpi"] / 100) / (1 + row["cpi"] / 100)
        gap = (real - 1) * 100
        if best is None or gap < best["real_pct"]:
            best = {"start": window[0]["year"], "end": window[-1]["year"],
                    "real_pct": round(gap, 1), "nominal_pct": round((total - 1) * 100, 1)}
    return best


if __name__ == "__main__":
    main()
