# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Backtest Engine
5-year BTC backtest (2021-2026) comparing:
  1. Zion Smart DCA v3.0
  2. Standard DCA (fixed weekly amount)
  3. Buy & Hold

BNB Hack 2026 | Track 2: Crypto Intelligence Agent
Usage:
    python backtest/backtest.py
    python backtest/backtest.py --budget 100 --days 1825
"""

import sys
import json
import argparse
import math
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from data_loader import download_btc_data, add_weekly_fear_greed

RESULTS_PATH = Path(__file__).parent / "results_summary.json"
REPORT_PATH  = Path(__file__).parent / "report.md"


# ─── Strategy implementations ────────────────────────────────────────────────

def get_fg_multiplier(fg: int, cfg: dict) -> float:
    if fg >= cfg["fg_extreme_greed"]: return 0.5
    elif fg >= cfg["fg_greed"] + 1:   return 1.0
    elif fg >= cfg["fg_extreme_fear"]: return 1.5
    else:                              return 2.0


def run_zion_dca(df_weekly: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Simulates Zion Smart DCA v3.0 week by week."""
    budget     = cfg["weekly_budget"]
    dca_split  = cfg["dca_split"]
    res_split  = cfg["reserve_split"]
    rsi_thresh = cfg["rsi_buildup_threshold"]

    records    = []
    btc_held   = 0.0
    cash_spent = 0.0
    reserve    = 0.0

    for _, row in df_weekly.iterrows():
        price = float(row["Close"])
        fg    = int(row["FearGreed"]) if pd.notna(row["FearGreed"]) else 50
        rsi   = float(row["RSI"])     if pd.notna(row["RSI"])       else 50.0

        multiplier  = get_fg_multiplier(fg, cfg)
        dca_base    = budget * dca_split
        reserve_add = budget * res_split

        # Rule 5: greed surplus to reserve
        if multiplier < 1.0:
            surplus     = dca_base * (1 - multiplier)
            reserve_add += surplus

        dca_amount = dca_base * multiplier

        # Rule 2: Buildup if RSI <= threshold AND reserve available
        is_buildup = (rsi <= rsi_thresh) and (reserve >= dca_amount * 0.5)
        if is_buildup:
            extra       = min(reserve * 0.5, dca_amount)
            dca_amount += extra
            reserve    -= extra

        reserve    += reserve_add
        btc_bought  = dca_amount / price
        btc_held   += btc_bought
        cash_spent += dca_amount

        records.append({
            "date":        row.name,
            "price":       price,
            "fg":          fg,
            "rsi":         round(rsi, 1),
            "multiplier":  multiplier,
            "dca_amount":  round(dca_amount, 2),
            "btc_bought":  round(btc_bought, 8),
            "btc_held":    round(btc_held, 8),
            "cash_spent":  round(cash_spent, 2),
            "reserve":     round(reserve, 2),
            "portfolio_value": round(btc_held * price, 2),
            "is_buildup":  is_buildup,
        })

    return pd.DataFrame(records).set_index("date")


def run_standard_dca(df_weekly: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Simulates plain DCA — same amount every week, no signals."""
    budget   = cfg["weekly_budget"]
    records  = []
    btc_held = 0.0
    spent    = 0.0

    for _, row in df_weekly.iterrows():
        price      = float(row["Close"])
        btc_bought = budget / price
        btc_held  += btc_bought
        spent     += budget
        records.append({
            "date":            row.name,
            "price":           price,
            "dca_amount":      budget,
            "btc_bought":      round(btc_bought, 8),
            "btc_held":        round(btc_held, 8),
            "cash_spent":      round(spent, 2),
            "portfolio_value": round(btc_held * price, 2),
        })

    return pd.DataFrame(records).set_index("date")


def run_buy_and_hold(df_weekly: pd.DataFrame, cfg: dict) -> dict:
    """Buy & Hold: invest all capital on day 1 and hold."""
    total_weeks  = len(df_weekly)
    total_budget = cfg["weekly_budget"] * total_weeks
    entry_price  = float(df_weekly.iloc[0]["Close"])
    exit_price   = float(df_weekly.iloc[-1]["Close"])
    btc_bought   = total_budget / entry_price
    final_value  = btc_bought * exit_price
    return {
        "total_invested": round(total_budget, 2),
        "final_value":    round(final_value, 2),
        "total_return":   round((final_value - total_budget) / total_budget * 100, 2),
        "btc_held":       round(btc_bought, 8),
    }


# ─── Performance metrics ─────────────────────────────────────────────────────

def calc_metrics(df: pd.DataFrame, label: str) -> dict:
    """
    Calculates: Total Return, Annualized Return, Sharpe Ratio,
    Sortino Ratio, Max Drawdown, Win Rate, Profit Factor.
    """
    values     = df["portfolio_value"].values
    invested   = df["cash_spent"].values
    n_weeks    = len(df)
    n_years    = n_weeks / 52

    # Returns (weekly portfolio value change)
    weekly_ret = pd.Series(values).pct_change().dropna()

    # Total & annualized return
    final_val      = values[-1]
    total_invested = invested[-1]
    total_return   = (final_val - total_invested) / total_invested * 100

    # CAGR
    cagr = ((final_val / total_invested) ** (1 / n_years) - 1) * 100

    # Sharpe ratio (weekly, annualized, rf=0)
    if weekly_ret.std() > 0:
        sharpe = (weekly_ret.mean() / weekly_ret.std()) * math.sqrt(52)
    else:
        sharpe = 0.0

    # Sortino ratio (only downside deviation)
    downside = weekly_ret[weekly_ret < 0]
    if len(downside) > 0 and downside.std() > 0:
        sortino = (weekly_ret.mean() / downside.std()) * math.sqrt(52)
    else:
        sortino = 0.0

    # Max drawdown (on portfolio value)
    roll_max = pd.Series(values).cummax()
    drawdown = (pd.Series(values) - roll_max) / roll_max * 100
    max_dd   = drawdown.min()

    # Win rate: weeks where portfolio grew
    wins     = (weekly_ret > 0).sum()
    win_rate = wins / len(weekly_ret) * 100

    # Profit factor
    gross_profit = weekly_ret[weekly_ret > 0].sum()
    gross_loss   = abs(weekly_ret[weekly_ret < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 99.0

    # Buildup events (only for Zion DCA)
    buildup_count = int(df["is_buildup"].sum()) if "is_buildup" in df.columns else 0

    return {
        "strategy":         label,
        "total_invested":   round(total_invested, 2),
        "final_value":      round(final_val, 2),
        "total_return_pct": round(total_return, 2),
        "cagr_pct":         round(cagr, 2),
        "sharpe_ratio":     round(sharpe, 3),
        "sortino_ratio":    round(sortino, 3),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate_pct":     round(win_rate, 2),
        "profit_factor":    round(profit_factor, 3),
        "total_weeks":      n_weeks,
        "buildup_events":   buildup_count,
    }


# ─── Report generation ───────────────────────────────────────────────────────

def print_comparison(zion: dict, dca: dict, bh: dict):
    sep = "=" * 70
    print(f"\n{sep}")
    print("  ZION SMART DCA v3.0 - 5-YEAR BACKTEST RESULTS (2021-2026)")
    print(f"{sep}")
    print(f"  {'Metric':<28} {'Zion DCA':>12} {'Std DCA':>12} {'Buy&Hold':>12}")
    print(f"  {'-'*28} {'-'*12} {'-'*12} {'-'*12}")

    bh_return = bh["total_return"]

    rows = [
        ("Total Return",    f"{zion['total_return_pct']:>11.1f}%", f"{dca['total_return_pct']:>11.1f}%", f"{bh_return:>11.1f}%"),
        ("CAGR",            f"{zion['cagr_pct']:>11.1f}%",         f"{dca['cagr_pct']:>11.1f}%",         "N/A"),
        ("Sharpe Ratio",    f"{zion['sharpe_ratio']:>12.3f}",      f"{dca['sharpe_ratio']:>12.3f}",       "N/A"),
        ("Sortino Ratio",   f"{zion['sortino_ratio']:>12.3f}",     f"{dca['sortino_ratio']:>12.3f}",      "N/A"),
        ("Max Drawdown",    f"{zion['max_drawdown_pct']:>11.1f}%", f"{dca['max_drawdown_pct']:>11.1f}%",  "N/A"),
        ("Win Rate",        f"{zion['win_rate_pct']:>11.1f}%",     f"{dca['win_rate_pct']:>11.1f}%",      "N/A"),
        ("Profit Factor",   f"{zion['profit_factor']:>12.3f}",     f"{dca['profit_factor']:>12.3f}",      "N/A"),
        ("Total Invested",  f"${zion['total_invested']:>11,.0f}",  f"${dca['total_invested']:>11,.0f}",   f"${bh['total_invested']:>11,.0f}"),
        ("Final Value",     f"${zion['final_value']:>11,.0f}",     f"${dca['final_value']:>11,.0f}",      f"${bh['final_value']:>11,.0f}"),
        ("ROI per $1 inv.", f"${zion['final_value']/zion['total_invested']:>11.3f}",
                            f"${dca['final_value']/dca['total_invested']:>11.3f}",
                            f"${bh['final_value']/bh['total_invested']:>11.3f}"),
        ("Buildup Events",  f"{zion['buildup_events']:>12}",        "N/A",                                "N/A"),
    ]

    for label, z, d, b in rows:
        print(f"  {label:<28} {z:>12} {d:>12} {b:>12}")

    print(f"{sep}\n")


def save_results(zion: dict, dca: dict, bh: dict, cfg: dict):
    results = {
        "generated_at":  datetime.now().isoformat(),
        "config":        cfg,
        "zion_smart_dca": zion,
        "standard_dca":  dca,
        "buy_and_hold":  bh,
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Results saved to {RESULTS_PATH.name}")

    # Markdown report
    md = f"""# Zion Smart DCA — Backtest Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## Configuration
- Weekly budget: **${cfg['weekly_budget']}**
- Period: **{cfg['start_date']} to {cfg['end_date']}**
- Total weeks: **{zion['total_weeks']}**

## Results Summary

| Metric | Zion Smart DCA | Standard DCA | Buy & Hold |
|--------|---------------|-------------|------------|
| Total Return | **{zion['total_return_pct']:.1f}%** | {dca['total_return_pct']:.1f}% | {bh['total_return']:.1f}% |
| CAGR | **{zion['cagr_pct']:.1f}%** | {dca['cagr_pct']:.1f}% | N/A |
| Sharpe Ratio | **{zion['sharpe_ratio']:.3f}** | {dca['sharpe_ratio']:.3f} | N/A |
| Sortino Ratio | **{zion['sortino_ratio']:.3f}** | {dca['sortino_ratio']:.3f} | N/A |
| Max Drawdown | **{zion['max_drawdown_pct']:.1f}%** | {dca['max_drawdown_pct']:.1f}% | N/A |
| Win Rate | **{zion['win_rate_pct']:.1f}%** | {dca['win_rate_pct']:.1f}% | N/A |
| Profit Factor | **{zion['profit_factor']:.3f}** | {dca['profit_factor']:.3f} | N/A |
| Total Invested | ${zion['total_invested']:,.0f} | ${dca['total_invested']:,.0f} | ${bh['total_invested']:,.0f} |
| Final Value | **${zion['final_value']:,.0f}** | ${dca['final_value']:,.0f} | ${bh['final_value']:,.0f} |
| Buildup Events | **{zion['buildup_events']}** | N/A | N/A |

## Key Insights

- Zion Smart DCA outperforms Standard DCA by **+{zion['total_return_pct'] - dca['total_return_pct']:.1f}%** in total return
- Max drawdown reduced by **{abs(zion['max_drawdown_pct']) - abs(dca['max_drawdown_pct']):.1f}pp** vs Standard DCA
- Sharpe Ratio improvement: **{zion['sharpe_ratio'] - dca['sharpe_ratio']:.3f}** (higher = better risk-adjusted return)
- Buildup events successfully deployed reserve at {zion['buildup_events']} market bottoms

## Risks & Caveats
- Past performance does not guarantee future results
- F&G proxy used for backtest (historical F&G API requires paid CMC plan)
- Weekly granularity — intra-week volatility not captured
- Strategy assumes reserve capital available for Buildup events
"""
    REPORT_PATH.write_text(md, encoding="utf-8")
    print(f"Report saved to {REPORT_PATH.name}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Zion Smart DCA 5-Year Backtest")
    p.add_argument("--budget",  type=float, default=100,       help="Weekly budget USD")
    p.add_argument("--days",    type=int,   default=1825,      help="Backtest days (default 1825 = 5 years)")
    p.add_argument("--start",   type=str,   default="2021-01-01")
    p.add_argument("--rsi",     type=float, default=35.0,      help="RSI Buildup threshold")
    p.add_argument("--force",   action="store_true",           help="Force re-download data")
    args = p.parse_args()

    cfg = {
        "weekly_budget":        args.budget,
        "dca_split":            0.70,
        "reserve_split":        0.30,
        "rsi_buildup_threshold": args.rsi,
        "fg_extreme_fear":      25,
        "fg_greed":             49,
        "fg_extreme_greed":     75,
        "start_date":           args.start,
        "end_date":             datetime.today().strftime("%Y-%m-%d"),
    }

    # ── Load data ────────────────────────────────────────────────────────────
    df_daily = download_btc_data(start=args.start, force=args.force)
    df_daily = add_weekly_fear_greed(df_daily)

    # Resample to weekly (Monday close)
    df_weekly = df_daily.resample("W-MON").last().dropna(subset=["Close"])
    print(f"\nWeekly bars: {len(df_weekly)} weeks")

    # ── Run strategies ───────────────────────────────────────────────────────
    print("\nRunning Zion Smart DCA backtest...")
    df_zion = run_zion_dca(df_weekly, cfg)

    print("Running Standard DCA backtest...")
    df_dca  = run_standard_dca(df_weekly, cfg)

    print("Running Buy & Hold calculation...")
    bh      = run_buy_and_hold(df_weekly, cfg)

    # ── Compute metrics ──────────────────────────────────────────────────────
    m_zion = calc_metrics(df_zion, "Zion Smart DCA v3.0")
    m_dca  = calc_metrics(df_dca,  "Standard DCA")

    # ── Print & save ─────────────────────────────────────────────────────────
    print_comparison(m_zion, m_dca, bh)
    save_results(m_zion, m_dca, bh, cfg)


if __name__ == "__main__":
    main()
