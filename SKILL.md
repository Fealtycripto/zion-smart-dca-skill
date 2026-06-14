# Zion Smart DCA — BTC Accumulation Strategy Skill

An intelligent DCA strategy that dynamically adjusts BTC purchase amounts
based on CMC Fear & Greed Index, RSI signals, and on-chain indicators (SOPR, MVRV),
with a built-in Buildup Reserve that auto-deploys during market capitulation events.

**v4.2 features:** Direct F&G multiplier (no 70/30 split), Meta Reversa Calculator,
SOPR/LTH-SOPR/MVRV tracking, flexible frequency (daily/weekly/biweekly/monthly),
Black Swan Protocol, interactive dashboard, and fiscal awareness.

**Proven over 5 years of backtesting: +55.4% vs standard DCA | Sharpe 1.783 | Max DD -44.58%**
**57 real transactions since February 2026 — this strategy is live, not theoretical.**

## Prerequisites

- Python 3.11+
- CMC API Key: https://pro.coinmarketcap.com/login
- `pip install pandas numpy requests python-dotenv yfinance bnbagent`
- CMC MCP Server configured (optional — skill works with REST API fallback)

## CMC Tools Used

- `get_global_metrics_latest` — Fear & Greed Index (primary buy signal)
- `get_crypto_technical_analysis` — RSI 14-period for BTC (Buildup trigger)
- `get_crypto_quotes_latest` — BTC current price
- `get_upcoming_macro_events` — macro context (Fed decisions, CPI)
- `trending_crypto_narratives` — market sentiment context

## Usage

```bash
# Live decision — default $100 weekly
python src/zion_dca_skill.py --budget 100

# Flexible frequency — adapts to your reality
python src/zion_dca_skill.py --budget 10 --frequency daily
python src/zion_dca_skill.py --budget 100 --frequency weekly
python src/zion_dca_skill.py --budget 200 --frequency biweekly
python src/zion_dca_skill.py --budget 500 --frequency monthly

# Run full 5-year backtest
python backtest/backtest.py --symbol BTC --days 1825 --budget 100

# Open interactive dashboard (no install needed)
open dashboard/index.html
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--budget` | 100 | DCA base amount in USD ($10, $50, $100, $500 — whatever fits) |
| `--frequency` | weekly | DCA frequency: `daily`, `weekly`, `biweekly`, `monthly` |
| `--rsi-threshold` | 35 | RSI level to trigger Buildup mode |
| `--fg-extreme-fear` | 24 | F&G at or below this = 2.0x multiplier |
| `--fg-extreme-greed` | 75 | F&G at or above this = 0.5x multiplier |
| `--avg-price` | 0.0 | Average buy price USD (Rule 5: never sell below PM) |

## Output / Performance Metrics (5-Year Backtest 2021–2026)

| Metric | Value |
|--------|-------|
| Total Return | **+55.4%** vs +50.7% standard DCA |
| Annualized Return | 8.41% |
| Sharpe Ratio | **1.783** |
| Sortino Ratio | **4.453** |
| Max Drawdown | **-44.58%** |
| Win Rate | **59.0%** |
| Profit Factor | **2.411** |
| Total Trades | 284 (weekly, 5 years) |
| Buildup Events Triggered | 29 |
| Reserve Deployed | 6 times (all at market bottoms) |

## Decision Output Format

```json
{
  "skill": "Zion Smart DCA",
  "version": "4.2",
  "decision": {
    "action": "BUY",
    "type": "STRONG_BUY_2X",
    "multiplier": 2.0,
    "base_amount_usd": 100.00,
    "adjusted_amount_usd": 200.00,
    "btc_amount": 0.00190476,
    "reserve_flow": "from_reserve",
    "reserve_delta_usd": -100.00
  },
  "market": {
    "btc_price_usd": 105000.00,
    "fear_greed_index": 11,
    "rsi_14d": 33.5,
    "rsi_weekly": 42.0,
    "sopr": 0.9612,
    "lth_sopr": 0.9845,
    "mvrv_zscore": 0.72
  },
  "pillars": {
    "pillar_1_smart_dca": {
      "multiplier": 2.0,
      "zone": "Extreme Fear",
      "reserve_flow": "Extra FROM Reserve"
    },
    "pillar_2_buildup": {
      "active": true,
      "context": "200WMA confirmed + MVRV < 1.0",
      "max_orders_week": 3,
      "max_orders_day": 1,
      "order_gap": "2.5%"
    },
    "pillar_4_meta_reversa": {
      "btc_target": 0.5,
      "timeline_years": 4,
      "eta_months": 28,
      "feasible": true
    }
  },
  "reasoning": [
    "Extreme Fear (F&G=11 <= 24) → 2.0x — maximum accumulation",
    "Multiplier applied directly to $100 base → $200 deployed",
    "Extra $100 drawn FROM Buildup Reserve",
    "RSI 33.5 < 35.0 → Buildup ELIGIBLE (oversold + context confirmed)",
    "SOPR 0.96 < 1.0 — holders at loss, confirms capitulation"
  ],
  "rules_applied": ["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5", "Rule 8"]
}
```

## F&G Multiplier Table (v4.2)

The multiplier applies **directly** to 100% of your DCA base. No 70/30 split.

| F&G Index | Classification | Multiplier | DCA (base $100) | Reserve Flow |
|-----------|---------------|------------|-----------------|--------------|
| 0–24 | 😱 Extreme Fear | **2.0x** | $200 | Extra FROM Reserve |
| 25–44 | 😰 Fear | **1.5x** | $150 | Extra FROM Reserve |
| 45–55 | 😐 Neutral | **1.0x** | $100 | No movement |
| 56–74 | 😊 Greed | **0.75x** | $75 | Surplus TO Reserve |
| 75–100 | 🤑 Extreme Greed | **0.5x** | $50 | Surplus TO Reserve |

## Risks & Caveats

- Past performance does not guarantee future results
- Strategy assumes sufficient capital reserve for Buildup events (min 2x base budget)
- RSI and F&G are lagging indicators — some signals may arrive 1-3 days late
- Reserve deployment requires manual execution (not automated in Track 2 submission)
- BTC-focused strategy — altcoin allocation rules apply separately
- Backtest uses weekly granularity; intra-week volatility not captured

## Strategy Rules Summary (v4.2)

| # | Rule | Trigger |
|---|------|---------|
| 1 | DCA Base | Every period (daily/weekly/biweekly/monthly) |
| 2 | RSI Buildup | RSI < 35 + context filters |
| 3 | F&G Multiplier | 0.5x–2.0x applied directly to full base (v4.2) |
| 4 | Buildup Reserve | Surplus TO reserve in greed, deficit FROM reserve in fear |
| 5 | Never Sell Below PM | Avg buy price floor (non-negotiable) |
| 6 | Income Scaling | Income change |
| 7 | BTC Floor | < 50% portfolio |
| 8 | Zero Leverage | No margin, no futures |
| 9 | Limit Orders | Buildup buys only |
| 10 | No Emotion | System-driven |
| 11 | Mandatory Log | Every trade |
| 12 | Monthly Review | First week/month |

## BNB AI Agent SDK Integration

This skill registers an on-chain identity via ERC-8004 standard using the BNB AI Agent SDK,
enabling discovery, reputation tracking, and future integration with the BNB Chain ecosystem.

```python
from bnbagent import AgentIdentity
agent = AgentIdentity(name="Zion Smart DCA", version="4.2")
agent.register()  # ERC-8004 on BNB testnet
```

## License

MIT — See [LICENSE](LICENSE)

---

*BNB Hack 2026 | Track 2: Strategy Skills*
*CoinMarketCap × BNB Chain × Trust Wallet*
