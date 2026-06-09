# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Main Skill Entry Point
BNB Hack 2026 | Track 2: Crypto Intelligence Agent

Usage:
    python src/zion_dca_skill.py
    python src/zion_dca_skill.py --budget 200
    python src/zion_dca_skill.py --budget 150 --btc-pct 0.54
"""

import sys
import json
import argparse
import os
from pathlib import Path

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).parent))

from strategy  import ZionSmartDCA, WeeklyConfig, MarketSignals
from indicators import fetch_live_signals


def parse_args():
    p = argparse.ArgumentParser(description="Zion Smart DCA Strategy Skill")
    p.add_argument("--budget",   type=float, default=float(os.getenv("WEEKLY_BUDGET_USD", 100)),
                   help="Weekly DCA budget in USD (default: 100)")
    p.add_argument("--btc-pct",  type=float, default=0.54,
                   help="Current BTC allocation in portfolio as decimal, e.g. 0.54 for 54pct")
    p.add_argument("--reserve",  type=float, default=0.0,
                   help="Current reserve balance in USD (default: 0)")
    p.add_argument("--json",     action="store_true",
                   help="Output raw JSON only for agent pipelines")
    return p.parse_args()


def run_skill(budget: float, btc_pct: float, reserve: float, json_only: bool = False):
    # ── 1. Fetch live signals from CMC ──────────────────────────────────────
    live = fetch_live_signals()

    # ── 2. Build MarketSignals for strategy engine ───────────────────────────
    signals = MarketSignals(
        btc_price_usd       = live.btc_price_usd,
        fear_greed_index    = live.fear_greed_value,
        rsi_14d             = live.rsi_14d,
        btc_portfolio_pct   = btc_pct,
        reserve_usd         = reserve,
    )

    # ── 3. Run strategy engine ───────────────────────────────────────────────
    config = WeeklyConfig(weekly_budget_usd=budget)
    engine = ZionSmartDCA(config=config)
    decision = engine.evaluate(signals)

    # ── 4. Build enriched output ─────────────────────────────────────────────
    output = decision.to_dict()
    output["market"]["btc_dominance_pct"]    = live.btc_dominance_pct
    output["market"]["total_market_cap_usd"] = live.total_market_cap_usd
    output["market"]["fear_greed_label"]     = live.fear_greed_label
    output["context"] = {
        "portfolio_btc_pct":    btc_pct,
        "reserve_balance_usd":  reserve,
        "weekly_budget_usd":    budget,
        "data_source":          "CoinMarketCap Agent Hub + yfinance RSI",
    }

    if json_only:
        print(json.dumps(output, indent=2))
        return output

    # ── 5. Human-readable output ─────────────────────────────────────────────
    d = output["decision"]
    m = output["market"]

    sep = "=" * 60
    print("\n" + sep)
    print("  ZION SMART DCA v3.0 - WEEKLY DECISION")
    print(sep)

    print("\n  MARKET CONDITIONS")
    print(f"  BTC Price:      ${m['btc_price_usd']:>12,.2f}")
    print(f"  Fear & Greed:   {m['fear_greed_index']:>3}  ({m['fear_greed_label']})")
    print(f"  RSI 14d:        {m['rsi_14d']:>6.1f}")
    print(f"  BTC Dominance:  {m['btc_dominance_pct']:>5.1f}%")

    print("\n  THIS WEEK'S DECISION")
    print(f"  Action:         {d['action']} - {d['type']}")
    print(f"  Multiplier:     {d['multiplier']}x")
    print(f"  Amount USD:     ${d['amount_usd']:>8,.2f}")
    print(f"  BTC to buy:     {d['btc_amount']:.8f} BTC")
    print(f"  Reserve add:    ${d['reserve_contribution_usd']:>8,.2f}")

    print("\n  REASONING")
    for r in output["reasoning"]:
        r_clean = r.replace('\u2192', '->')
        print(f"  * {r_clean}")

    if output["warnings"]:
        print("\n  WARNINGS")
        for w in output["warnings"]:
            print(f"  ! {w}")

    print(f"\n  RULES APPLIED: {', '.join(output['rules_applied'])}")
    print(sep + "\n")

    return output


if __name__ == "__main__":
    args = parse_args()
    run_skill(
        budget    = args.budget,
        btc_pct   = args.btc_pct,
        reserve   = args.reserve,
        json_only = args.json,
    )
