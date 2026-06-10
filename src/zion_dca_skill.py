# -*- coding: utf-8 -*-
"""
Zion Smart DCA v4.0 — Main Skill Entry Point
BNB Hack 2026 | Track 2: Crypto Intelligence Agent

Usage:
    python src/zion_dca_skill.py
    python src/zion_dca_skill.py --budget 200
    python src/zion_dca_skill.py --budget 50 --frequency monthly
    python src/zion_dca_skill.py --budget 25 --frequency daily --btc-pct 0.54
"""

import sys
import json
import argparse
import os
from pathlib import Path

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).parent))

from strategy   import ZionSmartDCA, DCAConfig, MarketSignals
from indicators import fetch_live_signals


def parse_args():
    p = argparse.ArgumentParser(
        description="Zion Smart DCA v4.0 — Intelligent BTC Accumulation Strategy",
        epilog=(
            "The strategy adapts to YOUR reality:\n"
            "  --budget 10 --frequency daily    → $10/day\n"
            "  --budget 100 --frequency weekly   → $100/week\n"
            "  --budget 200 --frequency biweekly → $200/biweekly\n"
            "  --budget 500 --frequency monthly  → $500/month\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--budget",    type=float, default=float(os.getenv("DCA_BUDGET_USD", 100)),
                   help="DCA base amount in USD (default: 100). Any amount works — $10, $50, $500.")
    p.add_argument("--frequency", type=str,   default=os.getenv("DCA_FREQUENCY", "weekly"),
                   choices=["daily", "weekly", "biweekly", "monthly"],
                   help="DCA frequency (default: weekly)")
    p.add_argument("--btc-pct",   type=float, default=0.54,
                   help="Current BTC allocation in portfolio as decimal, e.g. 0.54 for 54%%")
    p.add_argument("--reserve",   type=float, default=0.0,
                   help="Current reserve balance in USD (default: 0)")
    p.add_argument("--avg-price", type=float, default=0.0,
                   help="Average buy price in USD (for Rule 5: never sell below PM)")
    p.add_argument("--json",      action="store_true",
                   help="Output raw JSON only for agent pipelines")
    return p.parse_args()


def run_skill(budget: float, frequency: str = "weekly",
              btc_pct: float = 0.54, reserve: float = 0.0,
              avg_price: float = 0.0, json_only: bool = False):
    """Runs the Zion Smart DCA v4.0 skill with live market data."""

    # ── 1. Fetch live signals from CMC + yfinance ────────────────────────
    live = fetch_live_signals()

    # ── 2. Build MarketSignals for strategy engine ───────────────────────
    signals = MarketSignals(
        btc_price_usd     = live.btc_price_usd,
        fear_greed_index  = live.fear_greed_value,
        rsi_14d           = live.rsi_14d,
        rsi_weekly        = live.rsi_weekly,
        btc_portfolio_pct = btc_pct,
        reserve_usd       = reserve,
        btc_ath_usd       = live.btc_ath_usd,
        ath_drop_pct      = live.ath_drop_pct,
        price_vs_200wma   = live.price_vs_200wma,
        avg_buy_price     = avg_price,
    )

    # ── 3. Run strategy engine ───────────────────────────────────────────
    config = DCAConfig(base_amount_usd=budget, frequency=frequency)
    engine = ZionSmartDCA(config=config)
    decision = engine.evaluate(signals)

    # ── 4. Build enriched output ─────────────────────────────────────────
    output = decision.to_dict()
    output["market"]["btc_dominance_pct"]    = live.btc_dominance_pct
    output["market"]["total_market_cap_usd"] = live.total_market_cap_usd
    output["market"]["fear_greed_label"]     = live.fear_greed_label
    output["market"]["btc_ath_usd"]          = live.btc_ath_usd
    output["market"]["ath_drop_pct"]         = live.ath_drop_pct
    output["market"]["price_vs_200wma"]      = live.price_vs_200wma
    output["context"] = {
        "portfolio_btc_pct":   btc_pct,
        "reserve_balance_usd": reserve,
        "dca_budget_usd":      budget,
        "dca_frequency":       frequency,
        "avg_buy_price_usd":   avg_price,
        "data_source":         "CoinMarketCap Agent Hub + yfinance",
        "note":                "Amount and frequency adapt to the investor's reality",
    }

    if json_only:
        print(json.dumps(output, indent=2))
        return output

    # ── 5. Human-readable output ─────────────────────────────────────────
    d = output["decision"]
    m = output["market"]
    p0 = output["pillars"]["pillar_0_cycle"]
    p2 = output["pillars"]["pillar_2_buildup"]

    sep = "=" * 65
    print("\n" + sep)
    print("  ZION SMART DCA v4.0 — STRATEGY DECISION")
    print(f"  Frequency: {frequency} | Budget: ${budget:.0f}")
    print(sep)

    print("\n  MARKET CONDITIONS")
    print(f"  BTC Price:       ${m['btc_price_usd']:>12,.2f}")
    print(f"  Fear & Greed:    {m['fear_greed_index']:>3}  ({m['fear_greed_label']})")
    print(f"  RSI Daily:       {m['rsi_14d']:>6.1f}")
    print(f"  RSI Weekly:      {m['rsi_weekly']:>6.1f}")
    print(f"  BTC Dominance:   {m['btc_dominance_pct']:>5.1f}%")
    print(f"  ATH Drop:        {m['ath_drop_pct']:>5.1f}%")
    print(f"  vs 200WMA:       {m['price_vs_200wma']:>5.2f}x")

    print(f"\n  CYCLE ANALYSIS (Pillar 0)")
    print(f"  Phase:           {p0['phase']}")
    print(f"  Months since halving: {p0['months_since_halving']}")
    print(f"  Adjustment:      {p0['adjustment']}")

    print(f"\n  THIS PERIOD'S DECISION")
    print(f"  Action:          {d['action']} - {d['type']}")
    print(f"  Multiplier:      {d['multiplier']}x")
    print(f"  Amount USD:      ${d['amount_usd']:>8,.2f}")
    print(f"  BTC to buy:      {d['btc_amount']:.8f} BTC")
    print(f"  Reserve add:     ${d['reserve_contribution_usd']:>8,.2f}")

    if p2['active']:
        print(f"\n  BUILDUP ACTIVE")
        print(f"  Context:         {p2['context']}")
        print(f"  Max slots:       {p2['max_slots']}")
        print(f"  Consecutive:     {p2['consecutive_days']}")

    print(f"\n  REASONING")
    for r in output["reasoning"]:
        r_clean = r.replace('\u2192', '->')
        print(f"  * {r_clean}")

    if output["warnings"]:
        print(f"\n  WARNINGS")
        for w in output["warnings"]:
            print(f"  ! {w}")

    print(f"\n  RULES APPLIED: {', '.join(output['rules_applied'])}")
    print(sep + "\n")

    return output


if __name__ == "__main__":
    args = parse_args()
    run_skill(
        budget    = args.budget,
        frequency = args.frequency,
        btc_pct   = args.btc_pct,
        reserve   = args.reserve,
        avg_price = args.avg_price,
        json_only = args.json,
    )
