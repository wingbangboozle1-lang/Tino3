# Provenance: real historical episode series

Every CSV in this directory is a verbatim copy of a series published on the Federal
Reserve Bank of St. Louis FRED domain, fetched on 2026-11-15 with the publisher's own
CSV download endpoint (`https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`).
Column headers are exactly as published. No value was typed from memory, adjusted,
interpolated or filled. Where a published month was blank it was left out rather than
estimated.

| File | Series | Publisher of the series | Coverage stored |
|---|---|---|---|
| djia_monthly.csv | M1109BUSM293NNBR, Dow-Jones Industrial Stock Price Index for United States | National Bureau of Economic Research | 1928-01 to 1968-12, monthly |
| nasdaq_monthly.csv | NASDAQCOM, NASDAQ Composite | Nasdaq, Inc. | 1999-12 to 2025-12, month-end close |
| tb3ms_monthly.csv | TB3MS, 3-Month Treasury Bill Secondary Market Rate, Discount Basis | Board of Governors of the Federal Reserve System | 2000-01 to 2025-12, monthly average |
| callmoney_monthly.csv | M13001USM156NNBR, Call Money Rates, Mixed Collateral | National Bureau of Economic Research | 1929-01 to 1938-12, monthly average |
| cpiaucns_monthly.csv | CPIAUCNS, Consumer Price Index for All Urban Consumers, All Items | U.S. Bureau of Labor Statistics | 1928-01 to 2026-10, monthly index |

Notes that matter for the analysis:

* **djia_monthly.csv** is the published NBER series, which averages the highest and
  lowest index values for the month through 1948. 20 stocks are used through September
  1928 and 30 thereafter. It is a price index: no dividends.
* **nasdaq_monthly.csv** is the month-end close, i.e. FRED's monthly aggregation with
  the end-of-period method. It replaced an earlier month-average download in this
  directory, so that every entry and exit price in the module is the same kind of number.
* **callmoney_monthly.csv** is a brokered money-market rate, not a Treasury bill yield,
  and is the only official short-term cash rate published for the months around the
  1929 peak. TB3MS does not begin until 1934.
* **cpiaucns_monthly.csv** is used only to restate results in constant purchasing
  power, never to drive a return.

To re-verify any value, fetch the same endpoint with the same `cosd`/`coed` window and
compare byte for byte. `scripts/episodes.py` raises an error rather than interpolate if a
month it needs is missing from these files, so a short file cannot silently change a result.
