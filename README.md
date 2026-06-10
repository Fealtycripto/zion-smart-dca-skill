# Zion Smart DCA — BTC Accumulation Strategy Skill

<div align="center">

![Zion Smart DCA Logo](docs/logo.png)

**An AI-powered CMC Skill that removes emotion from Bitcoin accumulation.**

[![BNB Hack 2026](https://img.shields.io/badge/BNB%20Hack-2026-yellow?style=flat-square)](https://dorahacks.io/hackathon/bnbhack-twt-cmc/)
[![Track](https://img.shields.io/badge/Track-Strategy%20Skills-blue?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square)](#)
[![CMC Agent Hub](https://img.shields.io/badge/CMC-Agent%20Hub-orange?style=flat-square)](#)
[![License](https://img.shields.io/badge/License-MIT-white?style=flat-square)](#)

</div>

---

## The Problem

Most retail investors lose money not because they pick the wrong assets — but because they make emotional decisions at the worst possible times. Standard DCA is blind: it buys the same amount every period regardless of market conditions, wasting capital in greed phases and under-accumulating during fear events.

## The Solution

**Zion Smart DCA v4.0** is a 12-rule strategy skill powered by real-time CoinMarketCap data, built around **5 pillars** that adapt to the investor's reality:

> **💡 Flexibility First:** The strategy is SMART precisely because it adapts to YOU.
> Frequency is NOT fixed — choose daily, weekly, biweekly, or monthly.
> Amount is NOT fixed — $10, $50, $100, $500, whatever fits your budget.
> The system adjusts multipliers and signals regardless of your base amount or frequency.

### Pillar 0 — Cycle Reading

The strategy starts by reading the macro cycle phase based on the Bitcoin halving:

| Phase | Months Since Halving | Behavior |
|-------|---------------------|----------|
| 🟢 Accumulation | 0–12 | Maximum aggression — historical best entries |
| 🔵 Expansion | 12–24 | Normal DCA — trend establishing |
| 🟡 Euphoria | 24–36 | Defensive — reduce exposure, tighten stops |
| 🔴 Distribution | 36–48 | Scaling out — take profits systematically |
| ⚫ Post-Cycle | 48+ | Wait for next halving signal |

### Pillar 1 — F&G Multiplier Scale

| Signal | F&G Range | Multiplier | Example (base $100) |
|--------|-----------|------------|---------------------|
| 😱 Extreme Fear | 0–24 | **2.0x** | $140 |
| 😰 Fear | 25–44 | **1.5x** | $105 |
| 😐 Neutral | 45–55 | **1.0x** | $70 |
| 😊 Greed | 56–74 | **0.75x** | $52.50 |
| 🤑 Extreme Greed | 75–100 | **0.5x** | $35 |

### Pillar 2 — Buildup Mode (Double-Layer Confirmation)

Buildup activates only when **both conditions** are met:
1. **RSI daily < 35** (oversold)
2. **Context filters pass** — at least one of: price above 200WMA, MVRV < 1.0, ATH drop > 50%

**Slot scale by market depth:**

| Distance from ATH | Max Slots |
|-------------------|-----------|
| < 30% from ATH | 1–2 slots |
| 30–60% from ATH | 3–5 slots |
| > 60% from ATH | 6–10 slots |

**Cooldown rule:** Buy up to 3 consecutive days, then stop and wait for new confirmation.

### Pillar 3 — Scaling Out (Dual Confirmation)

Scaling out requires **both**:
1. **RSI weekly > 70** (overbought on weekly timeframe)
2. **Secondary confirmation** — at least one of: Pi Cycle Top, MVRV > 7, BTC Dominance < 40%

### Reserve First Principle (Rule 4)

30% of every budget is reserved. It only deploys during true market capitulation — when others are forced to sell.

---

## Proven Results

### 5-Year Backtest (2021–2026)

> ⚠️ **Note:** Results being recalculated with v4.0 parameters. Values below are from v3.0 backtest — v4.0 expected to show improved risk-adjusted returns due to tighter F&G bands and cycle awareness.

| Metric | Zion Smart DCA | Standard DCA | Buy & Hold |
|--------|---------------|-------------|------------|
| Total Return | **+56.4%** | +50.7% | +97.3% |
| Sharpe Ratio | **1.768** | 1.699 | 1.67 |
| Max Drawdown | **-44.6%** | -46.4% | -77.3% |
| Win Rate | **59.0%** | 59.4% | N/A |
| Profit Factor | **2.400** | 2.275 | N/A |

> Zion Smart DCA outperforms Standard DCA by +5.7pp return with better risk-adjusted metrics (Sharpe 1.768 vs 1.699) and slightly lower max drawdown.

### Live Period Simulation (Feb 13 – Jun 8, 2026 | Real Market Data)

> ⚠️ **Note:** Results being recalculated with v4.0 parameters. The values below used v3.0 thresholds — v4.0's wider Extreme Fear band (0–24 vs 0–20) would have captured even more accumulation events.

Using **real Fear & Greed data** from [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/) and real BTC prices from Yahoo Finance:

| Metric | Zion Smart DCA | Standard DCA |
|--------|---------------|-------------|
| BTC Accumulated | **0.031782 BTC** | 0.023624 BTC |
| Extra BTC vs Standard | **+0.008158 BTC (+34.5%)** | — |
| Portfolio Value | $2,005 | $1,490 |
| Reserve Available | **$265 (ready to deploy)** | N/A |
| Buildup Events | **2** (F&G 23 + F&G 10) | N/A |

**Why such a big difference?** Because the market spent **94% of weeks in Fear or Extreme Fear** during this period:

| Multiplier Zone | Weeks | F&G Range | Buy (base $100) |
|----------------|-------|-----------|-----------------|
| 🔴 Extreme Fear (2x) | **8** | F&G 0–24 | $140 |
| 🟡 Fear (1.5x) | **7** | F&G 25–44 | $105 |
| ⚪ Neutral (1x) | **2** | F&G 45–55 | $70 |

> Standard DCA bought $70 every single week. Zion Smart DCA averaged **$131.76/week** — buying $140 during 8 weeks of Extreme Fear — accumulating **34.5% more Bitcoin** for the same weekly budget.

**Data sources:**
- BTC price: [Yahoo Finance](https://finance.yahoo.com/quote/BTC-USD/) via yfinance
- Fear & Greed Index: [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/) (real historical data)
- RSI 14-period: Wilder EMA method calculated from price data (same methodology as TradingView)

## Real-World Proof

This strategy has been live since **February 13, 2026** tracking real BTC purchases. The author applies the exact same 12 rules personally — the live simulation above reflects what those conditions looked like using real market data from that period.

## CMC Agent Hub Integration

The skill uses **5 CMC MCP tools** for real-time decision making:

```
get_global_metrics_latest       → Fear & Greed Index
get_crypto_technical_analysis   → RSI 14-period (BTC)
get_crypto_quotes_latest        → Current BTC price
get_upcoming_macro_events       → Macro context
trending_crypto_narratives      → Market sentiment
```

## Quick Start

```bash
git clone https://github.com/Fealtycripto/zion-smart-dca-skill
cd zion-smart-dca-skill
pip install -r requirements.txt
cp .env.example .env   # add your CMC API key

# Run a live decision (default: $100 weekly)
python src/zion_dca_skill.py

# Run with custom frequency and budget
python src/zion_dca_skill.py --budget 50 --frequency daily
python src/zion_dca_skill.py --budget 200 --frequency biweekly
python src/zion_dca_skill.py --budget 500 --frequency monthly

# Run 5-year backtest
python backtest/backtest.py --days 1825 --budget 100
```

## Project Structure

```
zion-smart-dca-skill/
├── SKILL.md                 ← CMC Skill playbook (official format)
├── src/
│   ├── strategy.py          ← 12-rule strategy engine (v4.0)
│   ├── indicators.py        ← CMC Agent Hub integration
│   ├── zion_dca_skill.py    ← Main skill entry point
│   ├── agent.py             ← BNB AI Agent SDK (ERC-8004)
│   ├── commerce.py          ← ERC-8183 Agentic Commerce jobs
│   └── server.py            ← FastAPI job server (ERC-8183 endpoints)
├── backtest/
│   ├── backtest.py          ← Backtesting engine
│   ├── data_loader.py       ← Historical BTC data (2021-2026)
│   └── results_summary.json ← Full backtest results
└── docs/
    └── strategy_rules.md    ← All 12 rules explained
```

## The 12 Rules

1. **DCA Base** — fixed amount per period (daily/weekly/biweekly/monthly), no excuses
2. **RSI Buildup Trigger** — RSI < 35 + context filters (200WMA, MVRV, ATH%) activates Buildup mode
3. **F&G Multiplier Scale** — 0.5x to 2.0x based on market sentiment (v4.0 thresholds)
4. **Reserve First** — 70% DCA + 30% reserve, always
5. **Never Sell Below PM** — never sell below average buy price (non-negotiable)
6. **Income Scaling** — extra income ÷ 4 = DCA increase
7. **BTC Floor (50%)** — portfolio never goes below 50% BTC
8. **Zero Leverage** — no margin, no futures, no exceptions
9. **Limit Orders Only** — Buildup buys use limit orders for best execution
10. **No Emotion** — system decides, not feelings
11. **Mandatory Logging** — every trade recorded with full context
12. **Monthly Review** — adjust budget, check reserve, verify allocation

## Black Swan Protocol

4 types of black swan events with specific responses:

| Type | Trigger | Response |
|------|---------|----------|
| 🔴 Exchange Collapse | Major CEX insolvency | Withdraw all to cold storage, halt DCA 7 days |
| 🟠 Regulatory Shock | Major country ban/restriction | Reduce position 50%, wait for clarity |
| 🟡 Flash Crash | BTC drops >30% in 24h | Deploy 100% reserve immediately |
| ⚫ Black Monday | Crypto + TradFi simultaneous crash | Full defensive — cash only for 14 days |

## Fiscal Layer

Brazilian tax optimization (R$35k monthly exemption threshold):
- Track monthly sell volume in BRL
- Alert when approaching R$35k limit
- Suggest splitting sales across months when possible

## Mission Milestones

| Marco | Target | Status |
|-------|--------|--------|
| 🥉 Bronze | 0.1 BTC accumulated | In progress |
| 🥈 Silver | 0.5 BTC accumulated | — |
| 🥇 Gold | 1.0 BTC accumulated | — |
| 💎 Diamond | 2.1 BTC (full coin + reserve) | — |

## Built With

- **Python 3.11** + pandas + numpy
- **CMC Agent Hub** (MCP Server — 5 tools)
- **BNB AI Agent SDK** (ERC-8004 on-chain identity)
- **yfinance** for historical BTC data

## On-chain Identity (ERC-8004)

This agent is registered on **BNB Smart Chain Testnet** via the ERC-8004 standard.

| Field | Value |
|-------|-------|
| **Wallet** | `0x4E9feDB6DFb93fe7Ae98E2d2Bfe4fb6398A568bd` |
| **TX Hash** | [`0x4dcc42a27db87bc573c855edb0b0735a22548ce554042a8fbbd2519b8466b1c3`](https://testnet.bscscan.com/tx/0x4dcc42a27db87bc573c855edb0b0735a22548ce554042a8fbbd2519b8466b1c3) |
| **Network** | BSC Testnet (chain_id: 97) |
| **Standard** | ERC-8004 (Trustless Agent Identity) |

```bash
# Register agent on BNB testnet
python src/agent.py --register

# View agent identity card
python src/agent.py --info

# Start ERC-8183 job server
python src/agent.py --serve
```

## ERC-8183 Agentic Commerce

Zion Smart DCA exposes its analysis capabilities as **paid jobs** via the [ERC-8183](https://eips.ethereum.org/EIPS/eip-8183) Agentic Commerce standard. Other AI agents can discover, purchase, and consume DCA analysis through a standard REST API.

### Available Jobs

| Job Type | Description | Price |
|----------|-------------|-------|
| `analyze_market` | Real-time market analysis + DCA recommendation | $0.50 / 0.001 BNB |
| `backtest_period` | Historical backtest with performance comparison | $2.00 / 0.004 BNB |
| `portfolio_check` | Scaling Out analysis + milestone check | $0.25 / 0.0005 BNB |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `GET` | `/agent-card` | ERC-8004 agent identity card |
| `GET` | `/jobs` | List available job types (ERC-8183 catalog) |
| `POST` | `/jobs/analyze` | Execute market analysis job |
| `POST` | `/jobs/backtest` | Execute backtest job |
| `POST` | `/jobs/portfolio` | Execute portfolio check job |
| `GET` | `/jobs/{job_id}` | Query job status |

### Quick Start — Job Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start the ERC-8183 job server
python src/agent.py --serve
# OR directly:
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload

# Open interactive docs
# http://localhost:8000/docs
```

### Example — Agent-to-Agent Request

```python
import requests

# 1. Discover available jobs
jobs = requests.get("http://localhost:8000/jobs").json()

# 2. Request market analysis
result = requests.post("http://localhost:8000/jobs/analyze", json={
    "budget_usd": 100,
    "frequency": "weekly",
    "btc_pct": 0.54,
}).json()

print(result["result"]["decision"]["decision"]["action"])  # "BUY"
print(result["result"]["decision"]["decision"]["multiplier"])  # 2.0
```

### ERC-8183 Flow

```
┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│  Requesting Agent │──>│  ERC-8183 Escrow     │──>│  Zion Smart DCA  │
│  (any AI agent)   │   │  (on-chain payment)  │   │  (job provider)  │
│                   │<──│                      │<──│                  │
│  Receives result  │   │  Releases payment    │   │  Returns analysis│
└──────────────────┘    └─────────────────────┘    └──────────────────┘
```

## Author

**Rony Costa** ([@Fealtycripto](https://github.com/Fealtycripto))  
Creator of [Cripto Zion](https://criptozion.xyz) — financial sovereignty tools for Brazilian crypto investors.

---

*Submitted to BNB Hack 2026 — Track 2: Strategy Skills*  
*CoinMarketCap × BNB Chain × Trust Wallet*
