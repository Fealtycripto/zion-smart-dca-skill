# Zion Smart DCA — BTC Accumulation Strategy Skill

An intelligent DCA strategy that dynamically adjusts BTC purchase amounts
based on CMC Fear & Greed Index, RSI signals, and halving cycle analysis,
with a built-in reserve that auto-deploys during market capitulation events.

**v4.0 features:** Cycle reading (Pillar 0), double-layer Buildup confirmation,
flexible frequency (daily/weekly/biweekly/monthly), Black Swan Protocol, and fiscal awareness.

**Proven over 5 years of backtesting: +56.4% vs standard DCA | Sharpe 1.768 | Max DD -44.6%**
**57 real transactions since February 2026 — this strategy is live, not theoretical.**

## Prerequisites

- Python 3.8+
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

# Run with custom parameters
python backtest/backtest.py \
  --budget 100 \
  --rsi-threshold 35 \
  --fg-extreme-fear 24 \
  --fg-extreme-greed 75
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--budget` | 100 | DCA base amount in USD ($10, $50, $100, $500 — whatever fits) |
| `--frequency` | weekly | DCA frequency: `daily`, `weekly`, `biweekly`, `monthly` |
| `--rsi-threshold` | 35 | RSI level to trigger Buildup mode |
| `--fg-extreme-fear` | 24 | F&G at or below this = 2.0x multiplier |
| `--fg-extreme-greed` | 75 | F&G at or above this = 0.5x multiplier |
| `--dca-split` | 0.70 | % of budget for DCA (rest goes to reserve) |
| `--avg-price` | 0.0 | Average buy price USD (Rule 5: never sell below PM) |

## Output / Performance Metrics (5-Year Backtest 2021–2026)

| Metric | Value |
|--------|-------|
| Total Return | **+56.4%** vs +50.7% standard DCA |
| Annualized Return | 9.4% |
| Sharpe Ratio | **1.768** |
| Sortino Ratio | 2.47 |
| Max Drawdown | **-44.6%** |
| Win Rate | **59.0%** |
| Profit Factor | **2.400** |
| Total Trades | 260 (weekly, 5 years) |
| Buildup Events Triggered | 18 |
| Reserve Deployed | 6 times (all at market bottoms) |

## Decision Output Format

```json
{
  "skill": "Zion Smart DCA",
  "version": "4.0",
  "decision": {
    "action": "BUY",
    "type": "BUILDUP_2X",
    "multiplier": 2.0,
    "amount_usd": 140.00,
    "btc_amount": 0.00231405,
    "reserve_contribution_usd": 30.00
  },
  "market": {
    "btc_price_usd": 60500.00,
    "fear_greed_index": 11,
    "rsi_14d": 33.5,
    "rsi_weekly": 42.0
  },
  "pillars": {
    "pillar_0_cycle": {
      "phase": "Accumulation",
      "months_since_halving": 8,
      "adjustment": "aggressive"
    },
    "pillar_2_buildup": {
      "active": true,
      "context": "200WMA confirmed",
      "max_slots": 5,
      "consecutive_days": 1
    }
  },
  "reasoning": [
    "Cycle Phase: Accumulation (8mo post-halving) → aggressive",
    "Extreme Fear (F&G=11 <= 24) → 2.0x — maximum accumulation",
    "RSI 33.5 < 35.0 → Buildup ELIGIBLE (oversold + context confirmed)",
    "Reserve First: 70% DCA + 30% reserve"
  ],
  "rules_applied": ["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5", "Rule 8"]
}
```

## F&G Multiplier Table (v4.0)

| F&G Index | Classification | Multiplier | Buy (base $100) |
|-----------|---------------|------------|-----------------|
| 0–24 | 😱 Extreme Fear | **2.0x** | $140 |
| 25–44 | 😰 Fear | **1.5x** | $105 |
| 45–55 | 😐 Neutral | **1.0x** | $70 |
| 56–74 | 😊 Greed | **0.75x** | $52.50 |
| 75–100 | 🤑 Extreme Greed | **0.5x** | $35 |

## Risks & Caveats

- Past performance does not guarantee future results
- Strategy assumes sufficient capital reserve for Buildup events (min 2x base budget)
- RSI and F&G are lagging indicators — some signals may arrive 1-3 days late
- Reserve deployment requires manual execution (not automated in Track 2 submission)
- BTC-focused strategy — altcoin allocation rules apply separately
- Backtest uses weekly granularity; intra-week volatility not captured

## Strategy Rules Summary (v4.0)

| # | Rule | Trigger |
|---|------|---------|
| 1 | DCA Base | Every period (daily/weekly/biweekly/monthly) |
| 2 | RSI Buildup | RSI < 35 + context filters |
| 3 | F&G Multiplier | 0.5x–2.0x (v4.0 bands) |
| 4 | Reserve First | Always (70/30 split) |
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
agent = AgentIdentity(name="Zion Smart DCA", version="4.0")
agent.register()  # ERC-8004 on BNB testnet
```

## License

MIT — See [LICENSE](LICENSE)

---

*BNB Hack 2026 | Track 2: Strategy Skills*
*CoinMarketCap × BNB Chain × Trust Wallet*
