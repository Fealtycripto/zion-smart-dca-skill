# Zion Smart DCA v3.0 — Technical Q&A for Judges
> BNB Hack 2026 | Track: Crypto Intelligence Agent | Author: Rony Costa

This document answers the most likely technical and strategic questions judges may ask.
Every answer is grounded in verifiable data and documented code.

---

## 📊 DATA SOURCES

### Q: Where does the Fear & Greed Index come from?

**For live decisions (skill running now):**
```
Source: CoinMarketCap API → /v1/global-metrics/quotes/latest
Field:  fear_and_greed_value (0–100)
Cost:   Included in CMC Basic plan (free tier)
```

**For historical simulation (Feb–Jun 2026):**
```
Source: Alternative.me Crypto Fear & Greed Index
URL:    https://api.alternative.me/fng/?limit=500&format=json
Cost:   Free, no API key required
Coverage: 500 days of real daily data
Verified: Each data point matches public chart at alternative.me/crypto/fear-and-greed-index/
```

**Fallback (pre-2025 backtest data):**
```
Method: Proxy calculated from 3 price indicators:
  - RSI 14-period (40% weight)
  - 30-day BTC return (35% weight)
  - Distance from 200-day moving average (25% weight)
Note: Used ONLY for dates before Jan 2025 where real F&G API doesn't cover.
      Clearly labeled as "proxy" in code and output.
```

---

### Q: Where does the RSI come from?

**Short answer:** Calculated directly from BTC price data. Not fetched from any API.

**Detailed answer:**

RSI (Relative Strength Index) is a mathematical formula applied to price history.
We download daily BTC-USD OHLCV data from **Yahoo Finance** via `yfinance` library,
then compute RSI 14-period using the **Wilder Exponential Moving Average** method:

```python
# Wilder EMA method (same as TradingView, Bloomberg, MetaTrader)
delta    = close.diff()
gain     = delta.clip(lower=0)            # Only positive days
loss     = (-delta).clip(lower=0)         # Only negative days
avg_gain = gain.ewm(com=13, adjust=False).mean()   # Wilder smoothing (α = 1/14)
avg_loss = loss.ewm(com=13, adjust=False).mean()
rs       = avg_gain / avg_loss
RSI      = 100 - (100 / (1 + rs))
```

**Why not use CMC's RSI endpoint directly?**
The CMC endpoint `/v3/cryptocurrency/price-performance-stats` (which includes RSI)
returns HTTP 403 on the Basic plan. It requires a higher tier subscription.
Our calculated RSI is **mathematically identical** — RSI is a deterministic formula,
not a proprietary index. Any platform using the same price data and Wilder smoothing
will produce the same result.

**Verification:**
1. Download BTC-USD daily from Yahoo Finance for any date range
2. Apply the formula above with period=14
3. Compare to TradingView RSI(14) — values will match within rounding precision

---

### Q: Where does BTC price data come from?

**For backtesting:**
```
Source: Yahoo Finance via yfinance Python library
Symbol: BTC-USD
Interval: 1 day (daily OHLCV)
Range: 2021-01-01 to 2026-06-08 (1,985 days)
Cached: backtest/btc_2021_2026.csv (reproducible)
```

**For live skill decisions:**
```
Source: CoinMarketCap API → /v2/cryptocurrency/quotes/latest?symbol=BTC
Field:  data.BTC[0].quote.USD.price
Cost:   Included in CMC Basic plan
```

---

### Q: Are the F&G values in your simulation real or estimated?

**For Feb 13 – Jun 8, 2026 (the live simulation period):**
> **100% real.** Every single F&G value comes directly from Alternative.me's
> historical API. You can verify any individual day at:
> `https://api.alternative.me/fng/?limit=365&format=json`

**Notable real values in the simulation period:**
| Date | Real F&G | Classification |
|------|----------|----------------|
| 2026-02-13 | **9** | Extreme Fear |
| 2026-02-22 | **5** | Extreme Fear (near all-time low) |
| 2026-02-23 | **8** | Extreme Fear |
| 2026-03-30 | **11** | Extreme Fear |
| 2026-06-05 | **12** | Extreme Fear |
| 2026-06-08 | **10** | Extreme Fear |

---

## 🧠 STRATEGY METHODOLOGY

### Q: Why does the multiplier have only 4 levels? Isn't it too simplistic?

**Design choice, not a limitation.**

4 discrete levels (0.5x / 1.0x / 1.5x / 2.0x) were chosen deliberately because:
1. **Psychological clarity** — users need to understand exactly what the system is doing
2. **Execution discipline** — "buy double this week" is actionable; a continuous function isn't
3. **Backtested stability** — the 4-band system performs consistently across all market cycles

**For v3.2 roadmap:** A continuous multiplier function is planned:
```python
multiplier = max(0.5, min(2.0, 2.0 - (fear_greed / 100) * 1.5))
```
This would capture the gradient more precisely (e.g., F&G=12 gives 1.82x instead of 2.0x).

---

### Q: Why BTC only in the skill? Your profile mentions ETH, SOL, LINK.

**BTC is the primary accumulation asset by design.**

The strategy's core signals — Fear & Greed Index, BTC Dominance — are Bitcoin-native.
The 12 rules are calibrated for BTC's market cycle behavior:
- BTC has the most reliable F&G correlation
- BTC dominance is a macro indicator for the entire market
- Long-term accumulation conviction is strongest for BTC

**For ETH, SOL, LINK:** The same 12-rule logic applies, using each asset's own RSI,
but without the dominance check (Rules 7/8 are BTC-specific). This is planned for v3.1:
```python
python src/zion_dca_skill.py --asset ETH --budget 50
```

**The personal trades** including ETH/SOL/LINK applied the same principles manually
to those positions — the skill formalizes the BTC implementation first.

---

### Q: How do you justify -10.8% ROI in the live simulation? You lost money.

**Context is everything.**

The period Feb–Jun 2026 coincided with a significant BTC correction.
Any strategy holding BTC would be negative in USD terms during this period.

The relevant comparisons:
1. **vs Standard DCA:** Zion lost -10.8% vs Standard DCA's -12.3% → **better performance**
2. **BTC accumulated:** 0.033661 vs 0.023624 → **+42.5% more sats** (what matters long-term)
3. **Reserve:** $230 still available, ready to deploy at next capitulation event
4. **The strategy is designed for 3–5 year cycles, not 4-month snapshots**

> "In a bear market, the goal is not to be profitable in USD — it's to accumulate
> as many sats as possible at the lowest average price. Zion Smart DCA does this
> 42.5% better than Standard DCA during market corrections."

---

### Q: What are the Buildup events and did they actually work?

**Buildup mode** activates when RSI ≤ 35 (oversold) AND reserve funds are available.
It deploys 50% of the reserve in addition to the standard DCA allocation.

**Live simulation Buildup events:**
| Date | BTC Price | F&G | RSI | Deployed | Outcome |
|------|-----------|-----|-----|----------|---------|
| 2026-06-01 | $71,320 | 23 | 30.2 | $280 | BTC dropped further to $63k → bought more next week |
| 2026-06-08 | $63,091 | 10 | 26.1 | $280 | Most recent — lowest price in the period |

> The second Buildup on Jun 8 at $63,091 with F&G=10 is a textbook capitulation entry.
> Historical data shows F&G values of 5–10 have consistently marked local bottoms.

---

### Q: How is the Reserve First principle implemented technically?

```python
# Every week, budget splits before any calculation:
dca_base    = weekly_budget * 0.70   # $70 of $100
reserve_add = weekly_budget * 0.30   # $30 of $100

# Multiplier applies only to the DCA portion:
dca_amount = dca_base * multiplier   # e.g., $70 * 2.0 = $140 in Extreme Fear

# During greed (multiplier < 1.0), surplus also goes to reserve:
if multiplier < 1.0:
    surplus      = dca_base * (1 - multiplier)
    reserve_add += surplus   # even more saved for next dip

# Reserve only deploys during Buildup (RSI <= 35):
if rsi <= 35 and reserve >= threshold:
    dca_amount += min(reserve * 0.50, dca_amount)
    reserve    -= deployed_from_reserve
```

---

## 🔗 BNB CHAIN INTEGRATION

### Q: Is the ERC-8004 registration real or simulated?

**Real.** The agent is registered on BSC Testnet.

```
TX Hash:  0x5b36774865ad295891d898ccca74b88ded502a593fa5624d0671e1cf37afd558
Network:  BSC Testnet (chain_id: 97)
Explorer: https://testnet.bscscan.com/tx/0x5b36774865ad295891d898ccca74b88ded502a593fa5624d0671e1cf37afd558
Wallet:   0x4E9feDB6DFb93fe7Ae98E2d2Bfe4fb6398A568bd
SDK:      bnbagent v0.3.6 (ERC-8004 standard)
```

Anyone can verify this transaction on BSCscan testnet.

---

### Q: Why testnet and not mainnet?

**Standard practice for hackathon submissions.** Using testnet:
1. Allows gas-free registration (paymaster sponsored)
2. Removes financial risk during development
3. Demonstrates the same technical integration as mainnet
4. The BNB Hack 2026 guidelines recommend testnet for track submissions

Mainnet deployment is planned post-hackathon for production release.

---

## 📦 CMC INTEGRATION

### Q: Which CMC Agent Hub tools does the skill use?

| Tool | Purpose | Plan Required |
|------|---------|--------------|
| `get_global_metrics_latest` | Fear & Greed Index, BTC Dominance | Basic |
| `get_crypto_quotes_latest` | Current BTC price | Basic |
| `get_upcoming_macro_events` | Macro context awareness | Basic |
| `trending_crypto_narratives` | Market sentiment context | Basic |
| `get_crypto_technical_analysis` | RSI (returns 403 on Basic) | Pro+ |

**The RSI limitation** is handled by our own Wilder EMA calculation from price data.
All other 4 tools work correctly on the Basic plan.

---

### Q: What's the CMC API usage during this hackathon?

```
Monthly credit limit:  15,000
Credits used (Jun):    181
Credits remaining:     14,819
Rate limit:            50 requests/minute
```

The skill is extremely efficient — one full decision uses ~4–5 API calls.

---

## 🏆 COMPETITIVE DIFFERENTIATION

### Q: What makes this better than existing DCA tools?

| Feature | Zion Smart DCA | Typical DCA Tools |
|---------|---------------|-------------------|
| Real-time F&G signals | ✅ CMC API | ❌ Fixed schedule |
| RSI confirmation | ✅ Buildup trigger | ❌ Not considered |
| Reserve management | ✅ 30% systematic | ❌ Manual |
| On-chain identity | ✅ ERC-8004 | ❌ None |
| Decision traceability | ✅ Full reasoning[] | ❌ Black box |
| Backtested (5yr) | ✅ 1,985 days | ⚠️ Varies |
| Real-market simulation | ✅ Alt.me + Yahoo | ❌ Rarely |

### Q: Why not just Buy & Hold if it had higher total return?

Three reasons:

1. **Capital requirement:** B&H requires $28,400 invested on day 1 (Jan 2021 price).
   DCA requires $100/week — accessible to anyone with regular income.

2. **Psychological sustainability:** B&H experienced -77.3% drawdown in 2022.
   Zion DCA's max drawdown was -45.5%. Studies show 90%+ of retail investors
   sell during -50%+ drawdowns. A strategy only works if you can stick to it.

3. **Correct comparison:** vs **Standard DCA** (the real alternative for regular investors),
   Zion outperforms: +195% vs +66% total return, Sharpe 1.84 vs 1.12.

---

## 📁 REPRODUCIBILITY

All results in this submission are fully reproducible:

```bash
# Reproduce 5-year backtest
python backtest/backtest.py --days 1825 --budget 100

# Reproduce live period simulation (Feb-Jun 2026)
python backtest/live_simulation.py

# Run live skill with current market data
python src/zion_dca_skill.py --budget 100

# Verify F&G data source
curl "https://api.alternative.me/fng/?limit=10&format=json"

# Verify BTC price data source
python -c "import yfinance as yf; print(yf.download('BTC-USD', start='2026-02-13', end='2026-02-20'))"
```

---

*Document version: 1.0 | Last updated: June 9, 2026*
*Zion Smart DCA v3.0 | BNB Hack 2026 | github.com/Fealtycripto/zion-smart-dca-skill*
