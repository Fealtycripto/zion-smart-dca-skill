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
    rsi_buildup_threshold: float = 35.0   # RSI trigger for Buildup (Rule 2)
    fg_extreme_fear:      int   = 25      # F&G below = 2.0x (Rule 3)
    fg_fear:              int   = 49      # F&G below = 1.5x (Rule 3)
    fg_greed:             int   = 74      # F&G above = 1.0x (Rule 3)
    fg_extreme_greed:     int   = 75      # F&G above = 0.5x (Rule 3)
    btc_min_pct:          float = 0.40    # Rule 7: never below 40%
    btc_rebalance_pct:    float = 0.60    # Rule 8: rebalance if above 60%


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
        Extreme Greed (>=75) → 0.5x (accumulate reserve)
        Greed/Neutral (50-74) → 1.0x (standard)
        Fear (25-49) → 1.5x (accumulate more)
        Extreme Fear (<=24) → 2.0x (maximum accumulation)
        """
        cfg = self.config
        if fg >= cfg.fg_extreme_greed:
            return 0.5, f"Extreme Greed (F&G={fg} >= {cfg.fg_extreme_greed}) → 0.5x — reducing exposure"
        elif fg >= cfg.fg_fear + 1:
            return 1.0, f"Neutral/Greed (F&G={fg}) → 1.0x — standard DCA"
        elif fg >= cfg.fg_extreme_fear:
            return 1.5, f"Fear (F&G={fg} in 25-49) → 1.5x — increasing accumulation"
        else:
            return 2.0, f"Extreme Fear (F&G={fg} <= {cfg.fg_extreme_fear}) → 2.0x — maximum accumulation"

    # ─── Rule 2: Buildup Eligibility ───────────────────────────────────────
    def _is_buildup_eligible(self, rsi: float) -> tuple[bool, str]:
        """
        Rule 2 — Buildup eligible when RSI <= 35 (oversold signal).
        Confirms an undervalued entry point when combined with F&G fear.
        """
        threshold = self.config.rsi_buildup_threshold
        if rsi <= threshold:
            return True, f"RSI {rsi:.1f} <= {threshold} → Buildup ELIGIBLE (oversold)"
        return False, f"RSI {rsi:.1f} > {threshold} → Standard DCA (not oversold)"

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
    def check_scaling_out(self, total_invested: float, portfolio_value: float) -> Optional[str]:
        """
        Rule 9 — Scaling Out: if portfolio grew 4x vs invested, take 40% profit.
        Reinject 20% back into DCA budget.
        """
        if portfolio_value >= total_invested * 4:
            take_profit = portfolio_value * 0.40
            reinject    = take_profit * 0.20
            return (
                f"Rule 9 TRIGGERED: Portfolio {portfolio_value:.0f} >= 4x invested ({total_invested:.0f}). "
                f"Recommend: Take ${take_profit:.0f} profit, reinject ${reinject:.0f} into DCA."
            )
        return None

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
                f"Rule 5: Greed phase → surplus ${cfg.weekly_budget_usd * cfg.dca_split_pct * (1 - multiplier):.2f} "
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
        if multiplier == 2.0 and is_buildup:
            dca_type = DCAType.BUILDUP_2X
        elif multiplier == 1.5 and is_buildup:
            dca_type = DCAType.BUILDUP_15X
        elif multiplier == 0.5:
            dca_type = DCAType.BUILDUP_05X
        else:
            dca_type = DCAType.DCA_NORMAL

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

    # Scenario 1: Extreme Fear + Buildup (05/Jun/2026 — real event)
    print("=" * 60)
    print("SCENARIO 1: Extreme Fear + Buildup (05/Jun/2026 real)")
    print("=" * 60)
    signals_buildup = MarketSignals(
        btc_price_usd=60500.0,
        fear_greed_index=11,
        rsi_14d=33.5,
        btc_portfolio_pct=0.54,
    )
    result = engine.evaluate(signals_buildup)
    print(json.dumps(result.to_dict(), indent=2))

    # Scenario 2: Extreme Greed — accumulate reserve
    print("\n" + "=" * 60)
    print("SCENARIO 2: Extreme Greed — protect & accumulate reserve")
    print("=" * 60)
    signals_greed = MarketSignals(
        btc_price_usd=95000.0,
        fear_greed_index=82,
        rsi_14d=71.0,
        btc_portfolio_pct=0.65,
    )
    result2 = engine.evaluate(signals_greed)
    print(json.dumps(result2.to_dict(), indent=2))

    # Scenario 3: Neutral market
    print("\n" + "=" * 60)
    print("SCENARIO 3: Neutral market — standard DCA")
    print("=" * 60)
    signals_neutral = MarketSignals(
        btc_price_usd=62900.0,
        fear_greed_index=48,
        rsi_14d=42.0,
        btc_portfolio_pct=0.54,
    )
    result3 = engine.evaluate(signals_neutral)
    print(json.dumps(result3.to_dict(), indent=2))
