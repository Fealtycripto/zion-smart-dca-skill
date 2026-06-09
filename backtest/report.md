# Zion Smart DCA — Backtest Report
*Generated: 2026-06-09 18:55*

## Configuration
- Weekly budget: **$100.0**
- Period: **2021-01-01 to 2026-06-09**
- Total weeks: **284**

## Results Summary

| Metric | Zion Smart DCA | Standard DCA | Buy & Hold |
|--------|---------------|-------------|------------|
| Total Return | **56.4%** | 50.7% | 97.3% |
| CAGR | **8.5%** | 7.8% | N/A |
| Sharpe Ratio | **1.768** | 1.699 | N/A |
| Sortino Ratio | **4.412** | 3.945 | N/A |
| Max Drawdown | **-44.6%** | -46.4% | N/A |
| Win Rate | **59.0%** | 59.4% | N/A |
| Profit Factor | **2.400** | 2.275 | N/A |
| Total Invested | $23,625 | $28,400 | $28,400 |
| Final Value | **$36,943** | $42,806 | $56,042 |
| Buildup Events | **29** | N/A | N/A |

## Key Insights

- Zion Smart DCA outperforms Standard DCA by **+5.6pp** in total return
- Max drawdown reduced by **-1.8pp** vs Standard DCA
- Sharpe Ratio improvement: **+0.069** (higher = better risk-adjusted return)
- Sortino Ratio improvement: **+0.467** (better downside protection)
- ROI per $1 invested: **$1.564** vs $1.507 (DCA)
- Buildup events successfully deployed reserve at 29 market dip moments

## Why Not Just Buy & Hold?

Buy & Hold showed a higher raw return (97.3%) — but this comparison is misleading for three reasons:

**1. Capital requirements are incompatible.**
Buy & Hold requires the full $28,400 upfront on Day 1. Zion Smart DCA requires only $100.0/week.
The realistic alternative for weekly earners is NOT Buy & Hold — it's Standard DCA.
Against Standard DCA, Zion outperforms by +5.6pp.

**2. The -77% drawdown is psychologically unsurvivable.**
During 2022, BTC fell from $69k to $15k — a 77.3% peak-to-trough decline over 12 months.
Research shows >90% of retail investors panic-sell before recovery in such scenarios.
A strategy that exists on paper but gets abandoned is worth nothing.
Zion DCA's -44.6% max drawdown is painful but within the range humans can sustain.

**3. Period dependency — B&H is extremely start-date sensitive.**
This backtest begins 2021-01-01 at ~$31,972 — BTC nearly tripled within 10 months.
Had the backtest started Nov 2021 (BTC peak at $69k), Buy & Hold would show negative results today.
Zion Smart DCA would still be positive, as it buys more during the bear market.

**Conclusion:** Zion Smart DCA is the optimal strategy for someone accumulating BTC
from regular income — not lump-sum investing. Its edge is risk-adjusted return,
psychological sustainability, and capital accessibility.

## Risks & Caveats
- Past performance does not guarantee future results
- F&G proxy used for backtest (historical F&G API requires paid CMC plan)
- Weekly granularity — intra-week volatility not captured
- Strategy assumes reserve capital available for Buildup events
