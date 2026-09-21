# Laboratory 2 — Quantify Dashboard Reads

## 1. Quality requirements

### Read latency

Measurement starts when a complete request reaches the Dashboard and ends when the final response byte is sent. During busy periods, **p95 of correct reads must complete in ≤2,000 ms**. Exactly 2,000 ms passes. Successful, unavailable and unauthorised results are measured separately.

### Availability

The Dashboard is usable when an authenticated user can perform the main reads, see data status and read their Watchlist. Trading hours are Monday–Friday, 09:30–16:00 America/New_York, excluding exchange holidays.

| 30-day interval | Target | Assumed hours | Downtime budget |
|---|---:|---:|---:|
| Trading hours | 99.95% | 22×6.5 = 143 h | **4 min 17 sec** |
| Rest of day | 99.90% | 720−143 = 577 h | **34 min 37 sec** |

Trading hours have a stricter target because both traffic and data value peak then. The intervals are measured separately.

### Consistency

- Stock-price age is current time minus provider timestamp. Up to 15 minutes is accepted; 15–20 minutes is **Delayed**; over 20 minutes or without a valid timestamp is **Unavailable**.
- Outside trading hours, the last official price must show its timestamp and closed-market status.
- After a confirmed Watchlist change, 100% of subsequent reads by the same user reflect it. Another user's Watchlist is never returned.

## 2. Steady-state RPS

`RPS = concurrent users × participating share × actions per user / seconds`

| Read | 300 users | 3,000 users | 30,000 users |
|---|---:|---:|---:|
| Overview | 300×0.70/30 = **7.00** | **70.00** | **700.00** |
| Filter | 300×0.50×3/60 = **7.50** | **75.00** | **750.00** |
| Stock price | 300×0.20 = **60.00** | **600.00** | **6,000.00** |
| History | 300×0.20/300 = **0.20** | **2.00** | **20.00** |
| Watchlist | 300×0.60/60 = **3.00** | **30.00** | **300.00** |
| Search | 300×0.10×3/60 = **1.50** | **15.00** | **150.00** |
| **Total** | **79.20 RPS** | **792.00 RPS** | **7,920.00 RPS** |

## 3. Market-open RPS

Additional Overview = users×30%/10 s. Additional Watchlist = users×30%×60%/10 s.

| Calculation | 300 | 3,000 | 30,000 |
|---|---:|---:|---:|
| Steady traffic | 79.20 | 792.00 | 7,920.00 |
| Additional Overview | 9.00 | 90.00 | 900.00 |
| Additional Watchlist | 5.40 | 54.00 | 540.00 |
| **Subtotal** | **93.60** | **936.00** | **9,360.00** |
| 10% margin | 9.36 | 93.60 | 936.00 |
| With margin | 102.96 | 1,029.60 | 10,296.00 |
| **Final rounded target** | **103 RPS** | **1,030 RPS** | **10,296 RPS** |

Only the final target is rounded upward.

## 4. Storage estimates

### Stock definition

For version 1, a Stock is an active USD-denominated **common stock or ADR listed on Nasdaq**. Preferred stock, ETFs, funds, bonds, options, warrants and units are excluded. Delisted instruments remain in reference data for seven years but are excluded from default search.

Sources observed on **21 September 2026**:

- [Investor.gov — Stocks](https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks)
- [Nasdaq Trader — Symbol Directory Definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs)
- [Nasdaq Listings](https://www.nasdaq.com/solutions/listings)

Capacity planning assumes **3,300 Stocks**, rounded upward. Implementation must replace it with the daily filtered Symbol Directory count.

### Synchronised data

| Dataset | Purpose | Assumed synchronisation |
|---|---|---|
| Stock reference: symbol, name, exchange, sector, currency, type, status | Search, Filter, details | Daily |
| Latest price, change, provider timestamp and status | Overview, Stock price, freshness | Every 15 minutes during trading |
| Daily OHLC, volume and provider time | Price history | Daily; retain 7 years |
| Exchange state, session and timezone | Explain live/closed status | Daily and on state change |

### Calculation

Assumptions: 3,300 Stocks, 252 trading days/year and seven retained years.

| Dataset | Records | Bytes/record | Raw storage |
|---|---:|---:|---:|
| Stock reference | 3,300 | 300 B | **0.990 MB** |
| Latest prices | 3,300 | 180 B | **0.594 MB** |
| Price history | 3,300×252×7 = 5,821,200 | 160 B | **931.392 MB** |
| Market status | 252×7 = 1,764 | 150 B | **0.265 MB** |
| **Initial total** | — | — | **932.251 MB ≈ 0.932 GB** |

Daily history growth: **0.528 MB/trading day**. Annual history growth: **133.056 MB/year**. Figures are raw storage and exclude indexes, replication, backups, compression and user Watchlists.

## 5. Potential bottlenecks

| Quality | Potential bottleneck | Evidence | Possible effect | Next measurement |
|---|---|---|---|---|
| Latency | Stock-price read path | 6,000 of 7,920 stable RPS | p95 exceeds 2 s | p50/p95/p99 and processing/wait time |
| Consistency | Provider/synchronisation lag | 15-minute freshness threshold | Delayed data appears current | Provider age and delayed rate |
| Throughput | Market-open burst | 10,296 RPS capacity target | Throttling, queues or errors | Completed RPS, saturation and errors |
| Availability | External provider failure | Two direct dependencies and small budget | Authentication/data unavailable | Dependency uptime, timeouts and error-budget burn |

These are hypotheses requiring load tests and path-specific telemetry.

