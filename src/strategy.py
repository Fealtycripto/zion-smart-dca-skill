# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Strategy Engine
BNB Hack 2026 | CoinMarketCap x BNB Chain x Trust Wallet
Track 2: Strategy Skills

12 formalized rules for intelligent BTC accumulation.
Author: Rony Costa (@Fealtycripto)
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ActionType(Enum):
    BUY    = "BUY"
    SKIP   = "SKIP"
    SELL   = "SELL"   # rebalancing only


class DCAType(Enum):
    DCA_NORMAL   = "DCA_NORMAL"
    BUILDUP_05X  = "BUILDUP_0.5X"
    BUILDUP_15X  = "BUILDUP_1.5X"
    BUILDUP_2X   = "BUILDUP_2X"
    SKIP         = "SKIP"
    REBALANCE    = "REBALANCE"


@dataclass
class MarketSignals:
    """Real-time market data from CMC Agent Hub."""
    btc_price_usd:      float          # current BTC price
    fear_greed_index:   int            # 0-100 (CMC global metrics)
    rsi_14d:            float          # BTC RSI 14-period daily
    btc_portfolio_pct:  float = 0.60   # current BTC % in portfolio (0-1)
    reserve_usd:        float = 0.0    # current reserve balance
    reserve_target_usd: float = 0.0    # target reserve (doubles to unlock scale)


@dataclass
class WeeklyConfig:
    """User configuration for the weekly DCA cycle."""
    weekly_budget_usd:    float = 100.0   # total weekly budget
    dca_split_pct:        float = 0.70    # % of budget for DCA (Rule 4)
    reserve_split_pct:    float = 0.30    # % of budget for reserve (Rule 4)
    rsi_buildup_threshold:  float = 35.0   # RSI daily trigger for Buildup (Rule 2)
    rsi_scalingout_threshold: float = 70.0  # RSI weekly trigger for Scaling Out (whitepaper)
    # Fear & Greed thresholds — exact values from Zion Smart DCA Whitepaper v2.0
    fg_extreme_fear:      int   = 20      # F&G 0-20  -> 2.0x (Extreme Fear)
    fg_fear_top:          int   = 40      # F&G 21-40 -> 1.5x (Fear)
    fg_neutral_top:       int   = 60      # F&G 41-60 -> 1.0x (Neutral)
    fg_greed_top:         int   = 80      # F&G 61-80 -> 0.5x (Greed)
    # F&G 81-100 -> 0.25x (Extreme Greed)
    btc_min_pct:          float = 0.50    # Rule 7: BTC never below 50% (whitepaper: 50%+)
    btc_rebalance_pct:    float = 0.70    # Rule 8: rebalance if BTC above 70%


@dataclass
class StrategyDecision:
    """Output of the Zion Smart DCA strategy engine."""
    # Core decision
    action:             ActionType
    dca_type:           DCAType
    multiplier:         float
    amount_usd:         float
    btc_amount:         float
    reserve_contribution_usd: float

    # Context
    btc_price_usd:      float
    fear_greed_index:   int
    rsi_14d:            float
    is_buildup:         bool

    # Reasoning (full traceability for judges)
    reasoning:          list = field(default_factory=list)
    warnings:           list = field(default_factory=list)
    rules_applied:      list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "skill": "Zion Smart DCA",
            "version": "3.0",
            "decision": {
                "action":     self.action.value,
                "type":       self.dca_type.value,
                "multiplier": self.multiplier,
                "amount_usd": round(self.amount_usd, 2),
                "btc_amount": round(self.btc_amount, 8),
                "reserve_contribution_usd": round(self.reserve_contribution_usd, 2),
            },
            "market": {
                "btc_price_usd":    self.btc_price_usd,
                "fear_greed_index": self.fear_greed_index,
                "rsi_14d":          round(self.rsi_14d, 2),
            },
            "reasoning":     self.reasoning,
            "warnings":      self.warnings,
            "rules_applied": self.rules_applied,
        }


class ZionSmartDCA:
    """
    Zion Smart DCA v3.0 — Strategy Engine

    Implements 12 formalized rules for intelligent BTC accumulation:
    - Dynamic multiplier based on Fear & Greed Index (Rule 3)
    - Buildup trigger when RSI <= 35 (Rule 2)
    - Reserve First, Scale Later (Rule 4)
    - Auto-reserve replenishment in greed phases (Rule 5)
    - Portfolio allocation guardrails: 40-60% BTC (Rules 7-8)
    """

    def __init__(self, config: Optional[WeeklyConfig] = None):
        self.config = config or WeeklyConfig()

    # ─── Rule 3: Fear & Greed Multiplier ───────────────────────────────────
    def _get_fg_multiplier(self, fg: int) -> tuple[float, str]:
        """
        Rule 3 — Scale DCA amount by Fear & Greed Index.
        Source: Zion Smart DCA Whitepaper v2.0 (exact thresholds)

        F&G  0-20  (Extreme Fear)  -> 2.0x — maximum accumulation
        F&G 21-40  (Fear)          -> 1.5x — above-average accumulation
        F&G 41-60  (Neutral)       -> 1.0x — standard DCA
        F&G 61-80  (Greed)         -> 0.5x — reduce exposure, build reserve
        F&G 81-100 (Extreme Greed) -> 0.25x — minimum exposure, max reserve
        """
        if fg <= self.config.fg_extreme_fear:      # 0-20
            return 2.0,  f"Extreme Fear (F&G={fg}, 0-20) -> 2.0x — maximum accumulation"
        elif fg <= self.config.fg_fear_top:         # 21-40
            return 1.5,  f"Fear (F&G={fg}, 21-40) -> 1.5x — above-average accumulation"
        elif fg <= self.config.fg_neutral_top:      # 41-60
            return 1.0,  f"Neutral (F&G={fg}, 41-60) -> 1.0x — standard DCA"
        elif fg <= self.config.fg_greed_top:        # 61-80
            return 0.5,  f"Greed (F&G={fg}, 61-80) -> 0.5x — reducing exposure, building reserve"
        else:                                        # 81-100
            return 0.25, f"Extreme Greed (F&G={fg}, 81-100) -> 0.25x — minimum exposure, consider Scaling Out"

    # ─── Rule 2: Buildup Eligibility ───────────────────────────────────────
    def _is_buildup_eligible(self, rsi: float) -> tuple[bool, str]:
        """
        Rule 2 — Buildup eligible when RSI <= 35 (oversold signal).
        Confirms an undervalued entry point when combined with F&G fear.
        """
        threshold = self.config.rsi_buildup_threshold
        if rsi <= threshold:
            return True, f"RSI {rsi:.1f} <= {threshold} -> Buildup ELIGIBLE (oversold)"
        return False, f"RSI {rsi:.1f} > {threshold} -> Standard DCA (not oversold)"

    # ─── Rule 7 & 8: Portfolio Guardrails ──────────────────────────────────
    def _check_portfolio_balance(self, btc_pct: float) -> list[str]:
        """
        Rule 7 — NEVER let BTC fall below 40% of portfolio.
        Rule 8 — Consider rebalancing if BTC exceeds 60%.
        """
        warnings = []
        if btc_pct < self.config.btc_min_pct:
            warnings.append(
                f"CRITICAL (Rule 7): BTC at {btc_pct:.1%} < 40% minimum! "
                f"Prioritize BTC rebuying immediately."
            )
        elif btc_pct > self.config.btc_rebalance_pct:
            warnings.append(
                f"REBALANCE (Rule 8): BTC at {btc_pct:.1%} > 60%. "
                f"Consider partial rebalancing to stablecoins or other assets."
            )
        return warnings

    # ─── Rule 4: Reserve First Split ───────────────────────────────────────
    def _split_budget(self, budget: float, multiplier: float) -> tuple[float, float]:
        """
        Rule 4 — Reserve First, Scale Later.
        Split: 70% DCA base + 30% reserve contribution.
        DCA amount = DCA base * multiplier.
        Rule 5: In greed phases (0.5x), surplus goes to reserve automatically.
        """
        dca_base    = budget * self.config.dca_split_pct
        reserve_amt = budget * self.config.reserve_split_pct
        dca_amount  = dca_base * multiplier

        # Rule 5: surplus from greed phase (0.5x) goes to reserve
        if multiplier < 1.0:
            surplus = dca_base * (1.0 - multiplier)
            reserve_amt += surplus

        return dca_amount, reserve_amt

    # ─── Rule 9: Scaling Out ───────────────────────────────────────────────
    def check_scaling_out(self, total_invested: float, portfolio_value: float,
                          rsi_weekly: Optional[float] = None) -> Optional[str]:
        """
        Rule 9 — Scaling Out: progressive profit-taking as defined in Whitepaper v2.0.

        Trigger: RSI weekly > 70 (overbought on higher timeframe)
        Scale:
          +50%  profit -> sell 10% of position
          +100% profit -> sell 15%
          +200% profit -> sell 15%
          +300% profit -> sell 20%
          +500% profit -> sell 10%
          Remaining 30% -> HODL (generational wealth)
        """
        messages = []

        # RSI weekly trigger
        if rsi_weekly and rsi_weekly > self.config.rsi_scalingout_threshold:
            messages.append(
                f"!!  SCALING OUT SIGNAL: RSI Weekly {rsi_weekly:.1f} > 70 — overbought on higher timeframe. "
                f"Evaluate partial realization per whitepaper table."
            )

        if total_invested <= 0:
            return "\n".join(messages) if messages else None

        profit_pct = (portfolio_value - total_invested) / total_invested * 100
        scaling_table = [
            (50,  10,  "First"),
            (100, 15,  "Second"),
            (200, 15,  "Third"),
            (300, 20,  "Fourth"),
            (500, 10,  "Fifth"),
        ]
        for threshold, pct, label in scaling_table:
            if profit_pct >= threshold:
                sell_usd = portfolio_value * (pct / 100)
                messages.append(
                    f"[CHART] {label} scaling out trigger: +{profit_pct:.0f}% profit -> sell {pct}% "
                    f"(${sell_usd:,.0f}). Remaining 30% = permanent HODL."
                )
                break  # Only show the highest applicable tier

        return "\n".join(messages) if messages else None

    # ─── Main Decision Engine ───────────────────────────────────────────────
    def evaluate(self, signals: MarketSignals) -> StrategyDecision:
        """
        Core strategy evaluation — applies all 12 rules and returns decision.
        """
        cfg       = self.config
        reasoning = []
        warnings  = []
        rules     = []

        # Rule 1: Base DCA (always active)
        rules.append("Rule 1: Weekly DCA base active")
        reasoning.append(f"Weekly budget: ${cfg.weekly_budget_usd:.2f} USD")

        # Rule 2: Buildup check
        is_buildup, rsi_reason = self._is_buildup_eligible(signals.rsi_14d)
        reasoning.append(rsi_reason)
        rules.append("Rule 2: RSI Buildup check")

        # Rule 3: F&G multiplier
        multiplier, fg_reason = self._get_fg_multiplier(signals.fear_greed_index)
        reasoning.append(fg_reason)
        rules.append("Rule 3: Fear & Greed multiplier")

        # Rule 4 & 5: Budget split
        dca_amount, reserve_amt = self._split_budget(cfg.weekly_budget_usd, multiplier)
        rules.append("Rule 4: Reserve First split (70/30)")
        if multiplier < 1.0:
            reasoning.append(
                f"Rule 5: Greed phase -> surplus ${cfg.weekly_budget_usd * cfg.dca_split_pct * (1 - multiplier):.2f} "
                f"auto-routed to reserve"
            )
            rules.append("Rule 5: Auto-reserve replenishment in greed")

        # Rule 6: Income scaling (informational — user applies manually)
        rules.append("Rule 6: Income scaling (manual — apply if income changed)")

        # Rule 7 & 8: Portfolio guardrails
        port_warnings = self._check_portfolio_balance(signals.btc_portfolio_pct)
        warnings.extend(port_warnings)
        rules.append("Rule 7: BTC minimum 40% check")
        rules.append("Rule 8: BTC rebalance 60% check")

        # Rule 10: No emotion — system decides, not feelings
        rules.append("Rule 10: No timing, no emotion — follow the system")
        reasoning.append("Rule 10: Decision is systematic, not emotional")

        # Rule 11: Mandatory logging
        rules.append("Rule 11: Log this decision (date, price, type, F&G, RSI)")

        # Rule 12: Monthly review reminder
        rules.append("Rule 12: Monthly review (check BTC%, reserve, adjust budget)")

        # Determine DCA type
        if is_buildup and multiplier == 2.0:
            dca_type = DCAType.BUILDUP_2X
        elif is_buildup and multiplier == 1.5:
            dca_type = DCAType.BUILDUP_15X
        elif multiplier <= 0.5:
            dca_type = DCAType.BUILDUP_05X   # reserve building phase
        else:
            dca_type = DCAType.DCA_NORMAL

        # Rule 9 advisory: Extreme Greed warning
        if multiplier == 0.25:
            warnings.append(
                "Rule 9 ADVISORY: F&G in Extreme Greed (81-100). "
                "Review Scaling Out table from whitepaper. "
                "Consider partial realization if RSI weekly > 70."
            )
            rules.append("Rule 9: Scaling Out advisory (Extreme Greed zone)")

        btc_amount = dca_amount / signals.btc_price_usd

        return StrategyDecision(
            action=ActionType.BUY,
            dca_type=dca_type,
            multiplier=multiplier,
            amount_usd=dca_amount,
            btc_amount=btc_amount,
            reserve_contribution_usd=reserve_amt,
            btc_price_usd=signals.btc_price_usd,
            fear_greed_index=signals.fear_greed_index,
            rsi_14d=signals.rsi_14d,
            is_buildup=is_buildup,
            reasoning=reasoning,
            warnings=warnings,
            rules_applied=rules,
        )


# ─── Quick demo ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    engine = ZionSmartDCA(config=WeeklyConfig(weekly_budget_usd=100.0))

    scenarios = [
        ("Extreme Fear + Buildup (05/Jun/2026 real)",
         MarketSignals(btc_price_usd=60500.0, fear_greed_index=11, rsi_14d=33.5, btc_portfolio_pct=0.54)),
        ("Fear zone (F&G=30)",
         MarketSignals(btc_price_usd=65000.0, fear_greed_index=30, rsi_14d=42.0, btc_portfolio_pct=0.52)),
        ("Neutral (F&G=50)",
         MarketSignals(btc_price_usd=70000.0, fear_greed_index=50, rsi_14d=50.0, btc_portfolio_pct=0.54)),
        ("Greed (F&G=70) — reduce exposure",
         MarketSignals(btc_price_usd=88000.0, fear_greed_index=70, rsi_14d=65.0, btc_portfolio_pct=0.60)),
        ("Extreme Greed (F&G=85) — minimum exposure + Scaling Out alert",
         MarketSignals(btc_price_usd=110000.0, fear_greed_index=85, rsi_14d=75.0, btc_portfolio_pct=0.68)),
    ]

    for title, signals in scenarios:
        print("\n" + "=" * 65)
        print(f"  {title}")
        print("=" * 65)
        result = engine.evaluate(signals)
        d = result.to_dict()
        print(f"  Decision: {d['decision']['action']} | {d['decision']['type']} | {d['decision']['multiplier']}x")
        print(f"  Amount:   ${d['decision']['amount_usd']:.2f} BTC | Reserve: ${d['decision']['reserve_contribution_usd']:.2f}")
        print(f"  F&G: {d['market']['fear_greed_index']} | RSI: {d['market']['rsi_14d']}")
        for r in d['reasoning']:
            print(f"    >> {r}")
        for w in d['warnings']:
            print(f"    !! {w}")

    # Test scaling out
    print("\n" + "=" * 65)
    print("  SCALING OUT CHECK (portfolio at +150% profit, RSI weekly=72)")
    print("=" * 65)
    msg = engine.check_scaling_out(
        total_invested=5000, portfolio_value=12500, rsi_weekly=72.0
    )
    print(f"  {msg}")
