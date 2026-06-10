# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Live Period Simulation
$100/week in BTC using real market data (Feb 13 - Jun 8, 2026)
Real prices + F&G proxy from actual market conditions.

This simulates: "What if someone followed Zion Smart DCA v4.0 exactly
since Feb 13, 2026 with $100/week in Bitcoin?"
"""

import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from data_loader import download_btc_data, add_weekly_fear_greed

# ─── Config ──────────────────────────────────────────────────────────────────
START_DATE   = "2026-02-13"
END_DATE     = "2026-06-08"
WEEKLY_BUDGET = 100.0
DCA_SPLIT     = 0.70   # 70% goes to BTC
RESERVE_SPLIT = 0.30   # 30% to reserve
RSI_BUILDUP   = 35.0


DARK_BG = "#0D1117"
CARD_BG = "#161B22"
GOLD    = "#F5A623"
BLUE    = "#3B82F6"
GREEN   = "#22C55E"
RED     = "#EF4444"
GRAY    = "#6B7280"
WHITE   = "#F9FAFB"

plt.rcParams.update({
    "figure.facecolor": DARK_BG, "axes.facecolor": CARD_BG,
    "axes.edgecolor": "#30363D", "axes.labelcolor": WHITE,
    "axes.titlecolor": WHITE, "xtick.color": GRAY, "ytick.color": GRAY,
    "text.color": WHITE, "grid.color": "#21262D", "grid.linewidth": 0.8,
    "legend.facecolor": CARD_BG, "legend.edgecolor": "#30363D",
})

OUT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_multiplier(fg: float) -> float:
    """Exact thresholds from Zion Smart DCA v4.0."""
    if fg <= 24:   return 2.0   # Extreme Fear  (0-24)
    elif fg <= 44: return 1.5   # Fear          (25-44)
    elif fg <= 55: return 1.0   # Neutral       (45-55)
    elif fg <= 74: return 0.75  # Greed         (56-74)
    else:          return 0.5   # Extreme Greed (75-100)


def get_fg_label(fg: float) -> str:
    if fg <= 24:   return "EXTREME FEAR"
    elif fg <= 44: return "Fear"
    elif fg <= 55: return "Neutral"
    elif fg <= 74: return "Greed"
    else:          return "EXTREME GREED"


def run_simulation(df_weekly: pd.DataFrame) -> pd.DataFrame:
    records   = []
    btc_held  = 0.0
    cash_spent = 0.0
    reserve   = 0.0
    week_num  = 0

    for _, row in df_weekly.iterrows():
        week_num += 1
        price = float(row["Close"])
        fg    = float(row["FearGreed"]) if pd.notna(row["FearGreed"]) else 50.0
        rsi   = float(row["RSI"])       if pd.notna(row["RSI"])       else 50.0

        mult        = get_multiplier(fg)
        dca_base    = WEEKLY_BUDGET * DCA_SPLIT    # $70
        reserve_add = WEEKLY_BUDGET * RESERVE_SPLIT # $30

        # Surplus to reserve during greed
        if mult < 1.0:
            surplus      = dca_base * (1 - mult)
            reserve_add += surplus

        dca_amount = dca_base * mult

        # Buildup: RSI oversold + reserve available
        is_buildup = (rsi <= RSI_BUILDUP) and (reserve >= dca_amount * 0.5)
        if is_buildup:
            extra       = min(reserve * 0.5, dca_amount)
            dca_amount += extra
            reserve    -= extra

        reserve    += reserve_add
        btc_bought  = dca_amount / price
        btc_held   += btc_bought
        cash_spent += dca_amount

        records.append({
            "week":           week_num,
            "date":           row.name,
            "btc_price":      round(price, 2),
            "fear_greed":     int(fg),
            "fg_label":       get_fg_label(fg),
            "rsi":            round(rsi, 1),
            "multiplier":     mult,
            "dca_amount":     round(dca_amount, 2),
            "btc_bought":     round(btc_bought, 8),
            "btc_held":       round(btc_held, 8),
            "cash_spent":     round(cash_spent, 2),
            "reserve":        round(reserve, 2),
            "portfolio_value": round(btc_held * price, 2),
            "is_buildup":     is_buildup,
            "decision":       "BUILDUP" if is_buildup else f"DCA {mult}x",
        })

    return pd.DataFrame(records).set_index("date")


def run_standard_dca(df_weekly: pd.DataFrame) -> pd.DataFrame:
    records   = []
    btc_held  = 0.0
    cash_spent = 0.0
    for _, row in df_weekly.iterrows():
        price      = float(row["Close"])
        btc_bought = WEEKLY_BUDGET / price
        btc_held  += btc_bought
        cash_spent += WEEKLY_BUDGET
        records.append({
            "date":            row.name,
            "btc_price":       price,
            "btc_bought":      round(btc_bought, 8),
            "btc_held":        round(btc_held, 8),
            "cash_spent":      round(cash_spent, 2),
            "portfolio_value": round(btc_held * price, 2),
        })
    return pd.DataFrame(records).set_index("date")


def print_results(df_zion: pd.DataFrame, df_dca: pd.DataFrame):
    z = df_zion.iloc[-1]
    d = df_dca.iloc[-1]
    buildups = df_zion[df_zion["is_buildup"] == True]

    print("\n" + "=" * 65)
    print("  ZION SMART DCA v4.0 — LIVE PERIOD SIMULATION")
    print(f"  {START_DATE} to {END_DATE} | $100/week | BTC only")
    print("=" * 65)
    print(f"  {'Metric':<28} {'Zion DCA':>14} {'Std DCA':>14}")
    print(f"  {'-'*28} {'-'*14} {'-'*14}")
    print(f"  {'Total Invested':<28} ${z['cash_spent']:>13,.2f} ${d['cash_spent']:>13,.2f}")
    print(f"  {'BTC Accumulated':<28} {z['btc_held']:>14.6f} {d['btc_held']:>14.6f}")
    print(f"  {'Portfolio Value':<28} ${z['portfolio_value']:>13,.2f} ${d['portfolio_value']:>13,.2f}")
    roi_z = (z['portfolio_value'] - z['cash_spent']) / z['cash_spent'] * 100
    roi_d = (d['portfolio_value'] - d['cash_spent']) / d['cash_spent'] * 100
    print(f"  {'Return on Invested':<28} {roi_z:>13.1f}% {roi_d:>13.1f}%")
    print(f"  {'Reserve Available':<28} ${z['reserve']:>13,.2f} {'N/A':>14}")
    print(f"  {'Buildup Events':<28} {len(buildups):>14} {'N/A':>14}")
    print(f"  {'Weeks Simulated':<28} {len(df_zion):>14} {len(df_dca):>14}")
    print("=" * 65)

    if len(buildups) > 0:
        print(f"\n  BUILDUP EVENTS DETAIL:")
        for _, b in buildups.iterrows():
            print(f"    Week {b['week']:>2} | {b.name.date()} | BTC ${b['btc_price']:>8,.0f}"
                  f" | F&G {b['fear_greed']:>3} ({b['fg_label']}) | RSI {b['rsi']:>5.1f}"
                  f" | Deployed ${b['dca_amount']:>6.2f}")
    print()


def generate_chart(df_zion: pd.DataFrame, df_dca: pd.DataFrame):
    fig, axes = plt.subplots(3, 1, figsize=(14, 12),
                              gridspec_kw={"height_ratios": [3, 2, 1.5]})
    fig.patch.set_facecolor(DARK_BG)

    # ── Chart 1: Portfolio Value ──────────────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(df_zion.index, df_zion["portfolio_value"], color=GOLD, lw=2.5,
             label=f"Zion Smart DCA  (${df_zion['portfolio_value'].iloc[-1]:,.0f})")
    ax1.plot(df_dca.index,  df_dca["portfolio_value"],  color=BLUE, lw=2.0,
             label=f"Standard DCA    (${df_dca['portfolio_value'].iloc[-1]:,.0f})", alpha=0.8)
    ax1.plot(df_zion.index, df_zion["cash_spent"], color=GRAY, lw=1.2,
             linestyle="--", alpha=0.6, label="Capital Invested")

    buildups = df_zion[df_zion["is_buildup"] == True]
    if len(buildups) > 0:
        ax1.scatter(buildups.index, buildups["portfolio_value"],
                    color=GREEN, s=120, zorder=5,
                    label=f"BUILDUP! (F&G={buildups.iloc[0]['fear_greed']})", marker="^")

    ax1.set_title(f"Zion Smart DCA v4.0 — Live Period Simulation\n"
                  f"{START_DATE} to {END_DATE} | $100/week | Bitcoin only",
                  fontsize=14, fontweight="bold", pad=15)
    ax1.set_ylabel("Value (USD)")
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ── Chart 2: BTC Accumulated ─────────────────────────────────────────────
    ax2 = axes[1]
    ax2.fill_between(df_zion.index, df_zion["btc_held"], df_dca["btc_held"],
                     where=(df_zion["btc_held"] >= df_dca["btc_held"]),
                     color=GOLD, alpha=0.2, label="Extra BTC vs Standard DCA")
    ax2.plot(df_zion.index, df_zion["btc_held"], color=GOLD, lw=2.5,
             label=f"Zion DCA: {df_zion['btc_held'].iloc[-1]:.6f} BTC")
    ax2.plot(df_dca.index,  df_dca["btc_held"],  color=BLUE, lw=2.0,
             label=f"Std DCA:  {df_dca['btc_held'].iloc[-1]:.6f} BTC", alpha=0.8)
    if len(buildups) > 0:
        ax2.scatter(buildups.index, buildups["btc_held"],
                    color=GREEN, s=100, zorder=5, marker="^")
    ax2.set_ylabel("BTC Accumulated")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # ── Chart 3: Fear & Greed + Multiplier ───────────────────────────────────
    ax3 = axes[2]
    fg_vals = df_zion["fear_greed"].values.astype(float)
    dates   = df_zion.index
    ax3.fill_between(dates, fg_vals, 50,
                     where=(fg_vals <= 50), color=RED, alpha=0.35, label="Fear zone")
    ax3.fill_between(dates, fg_vals, 50,
                     where=(fg_vals >= 50), color=GREEN, alpha=0.2, label="Greed zone")
    ax3.plot(dates, fg_vals, color=WHITE, lw=1.5)
    ax3.axhline(25, color=RED,   lw=0.8, linestyle="--", alpha=0.7)
    ax3.axhline(75, color=GREEN, lw=0.8, linestyle="--", alpha=0.7)
    if len(buildups) > 0:
        for bdate in buildups.index:
            ax3.axvline(bdate, color=GREEN, lw=1.5, alpha=0.8, linestyle=":")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("Fear & Greed")
    ax3.set_xlabel("Date")
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout(pad=2.0)
    out = OUT_DIR / "07_live_simulation.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Chart saved: {out.name}")
    return out


def save_summary(df_zion: pd.DataFrame, df_dca: pd.DataFrame):
    z = df_zion.iloc[-1]
    d = df_dca.iloc[-1]
    buildups = df_zion[df_zion["is_buildup"] == True]
    roi_z = (z['portfolio_value'] - z['cash_spent']) / z['cash_spent'] * 100
    roi_d = (d['portfolio_value'] - d['cash_spent']) / d['cash_spent'] * 100

    summary = {
        "simulation_type":   "Live Period — Real Market Data",
        "period":            f"{START_DATE} to {END_DATE}",
        "weekly_budget_usd": WEEKLY_BUDGET,
        "asset":             "BTC only",
        "weeks_simulated":   len(df_zion),
        "zion_smart_dca": {
            "total_invested":    round(float(z['cash_spent']), 2),
            "btc_accumulated":   round(float(z['btc_held']), 8),
            "portfolio_value":   round(float(z['portfolio_value']), 2),
            "return_pct":        round(roi_z, 2),
            "reserve_usd":       round(float(z['reserve']), 2),
            "buildup_events":    len(buildups),
        },
        "standard_dca": {
            "total_invested":  round(float(d['cash_spent']), 2),
            "btc_accumulated": round(float(d['btc_held']), 8),
            "portfolio_value": round(float(d['portfolio_value']), 2),
            "return_pct":      round(roi_d, 2),
        },
        "buildup_events_detail": [
            {
                "date":       str(row.name.date()),
                "btc_price":  row["btc_price"],
                "fear_greed": row["fear_greed"],
                "fg_label":   row["fg_label"],
                "rsi":        row["rsi"],
                "deployed_usd": row["dca_amount"],
            }
            for _, row in buildups.iterrows()
        ]
    }

    out = Path(__file__).parent.parent / "docs" / "live_simulation.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"Summary saved: {out.name}")
    return summary


# ─── Weekly log (anonymized — no wallet address) ─────────────────────────────
def save_weekly_log(df_zion: pd.DataFrame):
    log = df_zion[[
        "week", "btc_price", "fear_greed", "fg_label", "rsi",
        "multiplier", "decision", "dca_amount", "btc_bought",
        "btc_held", "cash_spent", "reserve", "portfolio_value", "is_buildup"
    ]].copy()
    out = Path(__file__).parent.parent / "docs" / "weekly_decisions.csv"
    log.to_csv(out)
    print(f"Weekly log saved: {out.name}")


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Loading BTC data {START_DATE} -> {END_DATE}...")
    df_daily  = download_btc_data(start="2021-01-01", force=False)
    df_daily  = add_weekly_fear_greed(df_daily)
    df_weekly = df_daily.resample("W-MON").last().dropna(subset=["Close"])

    # Filter to live period only
    df_period = df_weekly[
        (df_weekly.index >= START_DATE) &
        (df_weekly.index <= END_DATE)
    ]
    print(f"Weeks in period: {len(df_period)}")

    print("\nRunning Zion Smart DCA simulation...")
    df_zion = run_simulation(df_period)

    print("Running Standard DCA simulation...")
    df_dca  = run_standard_dca(df_period)

    print_results(df_zion, df_dca)
    generate_chart(df_zion, df_dca)
    summary = save_summary(df_zion, df_dca)
    save_weekly_log(df_zion)

    print("\nDone! Files saved to docs/")
