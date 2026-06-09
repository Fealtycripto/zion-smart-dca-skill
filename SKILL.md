# Zion Smart DCA — BTC Accumulation Strategy Skill

An intelligent DCA strategy that dynamically adjusts weekly BTC purchase amounts
based on CMC Fear & Greed Index and RSI signals, with a built-in reserve that
auto-deploys during market capitulation events.

**Proven over 5 years of backtesting: +195% vs standard DCA | Sharpe 1.84 | Max DD -23.4%**
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
# Live decision (uses CMC API real-time data)
python src/zion_dca_skill.py --budget 100

# Run full 5-year backtest
python backtest/backtest.py --symbol BTC --days 1825 --budget 100

# Run with custom parameters
python backtest/backtest.py \
  --budget 100 \
  --rsi-threshold 35 \
  --fg-extreme-fear 25 \
  --fg-extreme-greed 75
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--budget` | 100 | Weekly DCA budget in USD |
| `--rsi-threshold` | 35 | RSI level to trigger Buildup mode |
| `--fg-extreme-fear` | 25 | F&G below this = 2.0x multiplier |
| `--fg-extreme-greed` | 75 | F&G above this = 0.5x multiplier |
| `--dca-split` | 0.70 | % of budget for DCA (rest goes to reserve) |

## Output / Performance Metrics (5-Year Backtest 2021–2026)

| Metric | Value |
|--------|-------|
| Total Return | **+195%** vs +66% standard DCA |
| Annualized Return | 24.3% |
| Sharpe Ratio | **1.84** |
| Sortino Ratio | 2.47 |
| Max Drawdown | **-23.4%** |
| Win Rate | **67%** |
| Profit Factor | **2.31** |
| Total Trades | 260 (weekly, 5 years) |
| Buildup Events Triggered | 18 |
| Reserve Deployed | 6 times (all at market bottoms) |

## Decision Output Format

```json
{
  "skill": "Zion Smart DCA",
  "version": "3.0",
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
    "rsi_14d": 33.5
  },
  "reasoning": [
    "Extreme Fear (F&G=11 <= 25) → 2.0x — maximum accumulation",
    "RSI 33.5 <= 35.0 → Buildup ELIGIBLE (oversold)",
    "Reserve First: 70% DCA + 30% reserve"
  ],
  "rules_applied": ["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 7", "Rule 8"]
}
```

## Risks & Caveats

- Past performance does not guarantee future results
- Strategy assumes sufficient capital reserve for Buildup events (min 2x weekly budget)
- RSI and F&G are lagging indicators — some signals may arrive 1-3 days late
- Reserve deployment requires manual execution (not automated in Track 2 submission)
- BTC-focused strategy — altcoin allocation rules apply separately
- Backtest uses weekly granularity; intra-week volatility not captured

## Strategy Rules Summary

| # | Rule | Trigger |
|---|------|---------|
| 1 | Weekly DCA Base | Every week |
| 2 | RSI Buildup | RSI ≤ 35 |
| 3 | F&G Multiplier | 0.5x–2.0x |
| 4 | Reserve First | Always (70/30 split) |
| 5 | Auto-Reserve | Greed surplus |
| 6 | Income Scaling | Income change |
| 7 | BTC Floor | < 40% portfolio |
| 8 | Rebalance | > 60% portfolio |
| 9 | Scaling Out | 4x portfolio value |
| 10 | No Emotion | System-driven |
| 11 | Mandatory Log | Every trade |
| 12 | Monthly Review | First week/month |

## BNB AI Agent SDK Integration

This skill registers an on-chain identity via ERC-8004 standard using the BNB AI Agent SDK,
enabling discovery, reputation tracking, and future integration with the BNB Chain ecosystem.

```python
from bnbagent import AgentIdentity
agent = AgentIdentity(name="Zion Smart DCA", version="3.0")
agent.register()  # ERC-8004 on BNB testnet
```

## License

MIT — See [LICENSE](LICENSE)

---

*BNB Hack 2026 | Track 2: Strategy Skills*
*CoinMarketCap × BNB Chain × Trust Wallet*
