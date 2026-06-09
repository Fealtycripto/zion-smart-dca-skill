# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Backtest Charts Generator
Generates publication-quality charts for DoraHacks submission.
BNB Hack 2026 | Track 2: Crypto Intelligence Agent
"""

import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.gridspec import GridSpec
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from data_loader import download_btc_data, add_weekly_fear_greed
from backtest import run_zion_dca, run_standard_dca, run_buy_and_hold, calc_metrics

SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Theme ───────────────────────────────────────────────────────────────────
DARK_BG   = "#0D1117"
CARD_BG   = "#161B22"
GOLD      = "#F5A623"
BLUE      = "#3B82F6"
GREEN     = "#22C55E"
RED       = "#EF4444"
GRAY      = "#6B7280"
WHITE     = "#F9FAFB"
PURPLE    = "#A855F7"

plt.rcParams.update({
    "figure.facecolor":  DARK_BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    "#30363D",
    "axes.labelcolor":   WHITE,
    "axes.titlecolor":   WHITE,
    "xtick.color":       GRAY,
    "ytick.color":       GRAY,
    "text.color":        WHITE,
    "grid.color":        "#21262D",
    "grid.linewidth":    0.8,
    "font.family":       "DejaVu Sans",
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  "#30363D",
})

CFG = {
    "weekly_budget": 100, "dca_split": 0.70, "reserve_split": 0.30,
    "rsi_buildup_threshold": 35, "fg_extreme_fear": 25,
    "fg_greed": 49, "fg_extreme_greed": 75,
    "start_date": "2021-01-01", "end_date": "2026-06-09",
}


def load_data():
    df_daily  = download_btc_data(start="2021-01-01", force=False)
    df_daily  = add_weekly_fear_greed(df_daily)
    df_weekly = df_daily.resample("W-MON").last().dropna(subset=["Close"])
    df_zion   = run_zion_dca(df_weekly, CFG)
    df_dca    = run_standard_dca(df_weekly, CFG)
    bh        = run_buy_and_hold(df_weekly, CFG)
    return df_weekly, df_zion, df_dca, bh


# ─── Chart 1: Portfolio Value Comparison ─────────────────────────────────────
def chart_portfolio_value(df_zion, df_dca, df_weekly):
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(DARK_BG)

    dates = df_zion.index
    ax.plot(dates, df_zion["portfolio_value"], color=GOLD,   lw=2.5, label="Zion Smart DCA v3.0",  zorder=3)
    ax.plot(dates, df_dca["portfolio_value"],  color=BLUE,   lw=2.0, label="Standard DCA",         zorder=2, alpha=0.85)
    ax.plot(dates, df_zion["cash_spent"],      color=GRAY,   lw=1.2, label="Capital Invested",      zorder=1, linestyle="--", alpha=0.7)

    # BTC price (secondary axis)
    ax2 = ax.twinx()
    ax2.plot(df_weekly.index, df_weekly["Close"], color=WHITE, lw=0.8, alpha=0.25, label="BTC Price")
    ax2.set_ylabel("BTC Price (USD)", color=GRAY, fontsize=10)
    ax2.tick_params(axis="y", colors=GRAY)
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))

    # Buildup markers
    buildups = df_zion[df_zion["is_buildup"] == True]
    ax.scatter(buildups.index, buildups["portfolio_value"],
               color=GREEN, s=60, zorder=5, label=f"Buildup Events ({len(buildups)})", marker="^", alpha=0.9)

    # Final values
    final_zion = df_zion["portfolio_value"].iloc[-1]
    final_dca  = df_dca["portfolio_value"].iloc[-1]
    ax.annotate(f"${final_zion:,.0f}", xy=(dates[-1], final_zion),
                xytext=(-80, 15), textcoords="offset points",
                color=GOLD, fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.2))
    ax.annotate(f"${final_dca:,.0f}", xy=(dates[-1], final_dca),
                xytext=(-80, -25), textcoords="offset points",
                color=BLUE, fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2))

    ax.set_title("Portfolio Value — Zion Smart DCA vs Standard DCA (2021–2026)",
                 fontsize=15, fontweight="bold", pad=20, color=WHITE)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Portfolio Value (USD)", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(True, alpha=0.4)
    ax.set_facecolor(CARD_BG)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)

    plt.tight_layout()
    path = SCREENSHOTS_DIR / "01_portfolio_value.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Chart 2: Cumulative Return % ────────────────────────────────────────────
def chart_cumulative_return(df_zion, df_dca):
    fig, ax = plt.subplots(figsize=(14, 6))

    ret_zion = (df_zion["portfolio_value"] / df_zion["cash_spent"] - 1) * 100
    ret_dca  = (df_dca["portfolio_value"]  / df_dca["cash_spent"]  - 1) * 100

    ax.plot(df_zion.index, ret_zion, color=GOLD, lw=2.5, label=f"Zion Smart DCA  ({ret_zion.iloc[-1]:.1f}%)")
    ax.plot(df_dca.index,  ret_dca,  color=BLUE, lw=2.0, label=f"Standard DCA    ({ret_dca.iloc[-1]:.1f}%)", alpha=0.85)
    ax.axhline(0, color=GRAY, lw=0.8, linestyle="--", alpha=0.5)

    # Fill zones
    ax.fill_between(df_zion.index, ret_zion, ret_dca,
                    where=(ret_zion >= ret_dca), alpha=0.15, color=GOLD, label="Zion outperforms")

    ax.set_title("Cumulative Return on Invested Capital (2021–2026)",
                 fontsize=15, fontweight="bold", pad=20)
    ax.set_ylabel("Return on Invested Capital (%)", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = SCREENSHOTS_DIR / "02_cumulative_return.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Chart 3: Drawdown ───────────────────────────────────────────────────────
def chart_drawdown(df_zion, df_dca):
    fig, ax = plt.subplots(figsize=(14, 5))

    def calc_dd(values):
        roll_max = pd.Series(values).cummax()
        return ((pd.Series(values) - roll_max) / roll_max * 100).values

    dd_zion = calc_dd(df_zion["portfolio_value"].values)
    dd_dca  = calc_dd(df_dca["portfolio_value"].values)

    ax.fill_between(df_zion.index, dd_zion, 0, color=GOLD, alpha=0.4, label=f"Zion DCA  (max {dd_zion.min():.1f}%)")
    ax.fill_between(df_dca.index,  dd_dca,  0, color=BLUE, alpha=0.25, label=f"Standard DCA  (max {dd_dca.min():.1f}%)")
    ax.plot(df_zion.index, dd_zion, color=GOLD, lw=1.5)
    ax.plot(df_dca.index,  dd_dca,  color=BLUE, lw=1.2)

    ax.axhline(-45.5, color=GOLD, lw=0.8, linestyle=":", alpha=0.6)
    ax.axhline(-46.4, color=BLUE, lw=0.8, linestyle=":", alpha=0.5)

    ax.set_title("Maximum Drawdown Comparison (2021–2026)",
                 fontsize=15, fontweight="bold", pad=20)
    ax.set_ylabel("Drawdown (%)", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = SCREENSHOTS_DIR / "03_drawdown.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Chart 4: Fear & Greed + Multiplier heatmap ──────────────────────────────
def chart_fg_signals(df_zion, df_weekly):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})

    # BTC price with F&G color overlay
    fg     = df_weekly["FearGreed"].fillna(50).astype(float).values
    prices = df_weekly["Close"].ffill().astype(float).values
    dates  = df_weekly.index

    colors = []
    for v in fg:
        try:
            vf = float(v)
        except (TypeError, ValueError):
            vf = 50.0
        if vf <= 24:   colors.append(RED)
        elif vf <= 44: colors.append("#F97316")
        elif vf <= 54: colors.append(GRAY)
        elif vf <= 74: colors.append("#86EFAC")
        else:          colors.append(GREEN)

    for i in range(len(dates) - 1):
        ax1.fill_between([dates[i], dates[i+1]],
                         [prices[i], prices[i+1]], 0,
                         alpha=0.15, color=colors[i])

    ax1.plot(dates, prices, color=WHITE, lw=1.5, alpha=0.9, label="BTC Price")
    ax1.set_ylabel("BTC Price (USD)", fontsize=11)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    ax1.set_title("BTC Price + Fear & Greed Signal Overlay (2021–2026)",
                  fontsize=15, fontweight="bold", pad=20)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)

    # Buildup markers on BTC chart
    buildups = df_zion[df_zion["is_buildup"] == True]
    valid_dates = [d for d in buildups.index if d in df_weekly.index]
    if valid_dates:
        btc_at_buildup = df_weekly.loc[valid_dates, "Close"]
        ax1.scatter(btc_at_buildup.index, btc_at_buildup.values,
                    color=GOLD, s=80, zorder=5, marker="^", label=f"Buildup ({len(valid_dates)}x)")
        ax1.legend(fontsize=10)

    # F&G index below
    ax2.fill_between(dates, fg, 50, where=(fg <= 50), color=RED,   alpha=0.4, label="Fear Zone")
    ax2.fill_between(dates, fg, 50, where=(fg >= 50), color=GREEN, alpha=0.3, label="Greed Zone")
    ax2.plot(dates, fg, color=WHITE, lw=1.2, alpha=0.8)
    ax2.axhline(25, color=RED,   lw=0.8, linestyle="--", alpha=0.6, label="Extreme Fear (25)")
    ax2.axhline(75, color=GREEN, lw=0.8, linestyle="--", alpha=0.6, label="Extreme Greed (75)")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Fear & Greed", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9, loc="upper right")

    plt.tight_layout()
    path = SCREENSHOTS_DIR / "04_fear_greed_signals.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Chart 5: Metrics Summary Dashboard ──────────────────────────────────────
def chart_metrics_dashboard(m_zion, m_dca, bh):
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor(DARK_BG)
    gs  = GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.4)

    def metric_card(ax, title, z_val, d_val, fmt="{}", higher_is_better=True, unit=""):
        ax.set_facecolor(CARD_BG)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#30363D")

        z_color = GOLD if (z_val >= d_val) == higher_is_better else RED
        d_color = BLUE

        ax.text(0.5, 0.88, title, ha="center", va="top",
                fontsize=10, color=GRAY, transform=ax.transAxes)
        ax.text(0.5, 0.58, f"{fmt.format(z_val)}{unit}", ha="center", va="top",
                fontsize=18, fontweight="bold", color=z_color, transform=ax.transAxes)
        ax.text(0.5, 0.28, f"DCA: {fmt.format(d_val)}{unit}", ha="center", va="top",
                fontsize=11, color=d_color, transform=ax.transAxes)
        diff = z_val - d_val
        sign = "+" if diff > 0 else ""
        diff_color = GREEN if (diff > 0) == higher_is_better else RED
        ax.text(0.5, 0.08, f"{sign}{fmt.format(diff)}{unit}", ha="center", va="top",
                fontsize=10, color=diff_color, transform=ax.transAxes,
                fontweight="bold")

    # Row 1
    metric_card(fig.add_subplot(gs[0, 0]), "Total Return",
                m_zion["total_return_pct"], m_dca["total_return_pct"], "{:.1f}", unit="%")
    metric_card(fig.add_subplot(gs[0, 1]), "CAGR",
                m_zion["cagr_pct"], m_dca["cagr_pct"], "{:.1f}", unit="%")
    metric_card(fig.add_subplot(gs[0, 2]), "Sharpe Ratio",
                m_zion["sharpe_ratio"], m_dca["sharpe_ratio"], "{:.3f}")
    metric_card(fig.add_subplot(gs[0, 3]), "Sortino Ratio",
                m_zion["sortino_ratio"], m_dca["sortino_ratio"], "{:.3f}")

    # Row 2
    metric_card(fig.add_subplot(gs[1, 0]), "Max Drawdown",
                m_zion["max_drawdown_pct"], m_dca["max_drawdown_pct"], "{:.1f}",
                higher_is_better=False, unit="%")
    metric_card(fig.add_subplot(gs[1, 1]), "Win Rate",
                m_zion["win_rate_pct"], m_dca["win_rate_pct"], "{:.1f}", unit="%")
    metric_card(fig.add_subplot(gs[1, 2]), "Profit Factor",
                m_zion["profit_factor"], m_dca["profit_factor"], "{:.3f}")
    ax_buildup = fig.add_subplot(gs[1, 3])
    ax_buildup.set_facecolor(CARD_BG)
    ax_buildup.set_xticks([])
    ax_buildup.set_yticks([])
    for spine in ax_buildup.spines.values():
        spine.set_edgecolor("#30363D")
    ax_buildup.text(0.5, 0.88, "Buildup Events", ha="center",
                    fontsize=10, color=GRAY, transform=ax_buildup.transAxes)
    ax_buildup.text(0.5, 0.55, f"{m_zion['buildup_events']}", ha="center",
                    fontsize=24, fontweight="bold", color=GOLD, transform=ax_buildup.transAxes)
    ax_buildup.text(0.5, 0.25, "market dips captured", ha="center",
                    fontsize=10, color=GRAY, transform=ax_buildup.transAxes)

    # Row 3: bar comparison
    ax_bar = fig.add_subplot(gs[2, :])
    ax_bar.set_facecolor(CARD_BG)
    categories = ["Total\nReturn (%)", "Sharpe\nRatio", "Sortino\nRatio", "Profit\nFactor"]
    z_vals = [m_zion["total_return_pct"], m_zion["sharpe_ratio"],
               m_zion["sortino_ratio"],   m_zion["profit_factor"]]
    d_vals = [m_dca["total_return_pct"],  m_dca["sharpe_ratio"],
               m_dca["sortino_ratio"],    m_dca["profit_factor"]]

    x = np.arange(len(categories))
    w = 0.35
    bars_z = ax_bar.bar(x - w/2, z_vals, w, label="Zion Smart DCA", color=GOLD, alpha=0.9)
    bars_d = ax_bar.bar(x + w/2, d_vals, w, label="Standard DCA",   color=BLUE, alpha=0.75)

    for bar in bars_z:
        ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.2f}", ha="center", va="bottom",
                    color=GOLD, fontsize=9, fontweight="bold")
    for bar in bars_d:
        ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.2f}", ha="center", va="bottom",
                    color=BLUE, fontsize=9)

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(categories, fontsize=11)
    ax_bar.set_title("Key Metrics Comparison — Zion Smart DCA vs Standard DCA",
                     fontsize=12, fontweight="bold")
    ax_bar.legend(fontsize=10)
    ax_bar.grid(True, axis="y", alpha=0.3)

    # Header
    fig.text(0.5, 0.97,
             "ZION SMART DCA v3.0 — 5-Year Backtest Results (2021–2026)",
             ha="center", va="top", fontsize=16, fontweight="bold", color=WHITE)
    fig.text(0.5, 0.94,
             "284 weeks | $100/week budget | BNB Hack 2026",
             ha="center", va="top", fontsize=11, color=GRAY)

    path = SCREENSHOTS_DIR / "05_metrics_dashboard.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Chart 6: BTC Accumulation Over Time ─────────────────────────────────────
def chart_btc_accumulation(df_zion, df_dca):
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df_zion.index, df_zion["btc_held"], color=GOLD, lw=2.5,
            label=f"Zion Smart DCA  ({df_zion['btc_held'].iloc[-1]:.4f} BTC)")
    ax.plot(df_dca.index,  df_dca["btc_held"],  color=BLUE, lw=2.0,
            label=f"Standard DCA    ({df_dca['btc_held'].iloc[-1]:.4f} BTC)", alpha=0.85)

    # Fill difference
    ax.fill_between(df_zion.index, df_zion["btc_held"], df_dca["btc_held"],
                    where=(df_zion["btc_held"] >= df_dca["btc_held"]),
                    color=GOLD, alpha=0.12, label="Extra BTC from Buildup events")

    ax.set_title("Total BTC Accumulated Over Time (2021–2026)",
                 fontsize=15, fontweight="bold", pad=20)
    ax.set_ylabel("BTC Held", fontsize=11)
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = SCREENSHOTS_DIR / "06_btc_accumulation.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"Saved: {path.name}")


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading backtest data...")
    df_weekly, df_zion, df_dca, bh = load_data()
    m_zion = calc_metrics(df_zion, "Zion Smart DCA")
    m_dca  = calc_metrics(df_dca,  "Standard DCA")

    print(f"\nGenerating {6} charts...")
    chart_portfolio_value(df_zion, df_dca, df_weekly)
    chart_cumulative_return(df_zion, df_dca)
    chart_drawdown(df_zion, df_dca)
    chart_fg_signals(df_zion, df_weekly)
    chart_metrics_dashboard(m_zion, m_dca, bh)
    chart_btc_accumulation(df_zion, df_dca)

    print(f"\nAll charts saved to: docs/screenshots/")
    print("Files:")
    for f in sorted(SCREENSHOTS_DIR.glob("*.png")):
        print(f"  {f.name}")
