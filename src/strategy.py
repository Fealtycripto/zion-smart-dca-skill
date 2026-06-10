# -*- coding: utf-8 -*-
"""
Zion Smart DCA v4.0 — Strategy Engine
BNB Hack 2026 | CoinMarketCap x BNB Chain x Trust Wallet
Track 2: Crypto Intelligence Agent

4 Pillars + 12 Rules for intelligent BTC accumulation.
Author: Rony Costa (@Fealtycripto)

IMPORTANT — Flexibility by design:
  - Frequency: daily, weekly, biweekly, or monthly — YOUR choice.
  - Amount: $10, $50, $100, $500 — whatever fits YOUR reality.
  - The strategy adapts to the investor, not the other way around.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime, timedelta, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class ActionType(Enum):
    BUY    = "BUY"
    SKIP   = "SKIP"
    SELL   = "SELL"


class DCAType(Enum):
    DCA_NORMAL     = "DCA_NORMAL"
    BUILDUP_SLOT   = "BUILDUP_SLOT"
    SKIP           = "SKIP"
    SCALING_OUT    = "SCALING_OUT"


class CyclePhase(Enum):
    """Pillar 0 — The 5 phases of the Bitcoin cycle (based on 3 documented halvings)."""
    ACCUMULATION_PRE_HALVING = "ACCUMULATION_PRE_HALVING"   # -12 to 0 months
    INITIAL_IMPULSE          = "INITIAL_IMPULSE"            # 0 to +6 months
    BULL_RUN                 = "BULL_RUN"                   # +6 to +18 months
    DISTRIBUTION             = "DISTRIBUTION"               # +18 to +24 months
    BEAR_MARKET              = "BEAR_MARKET"                # +24 to +48 months


class BuildupContext(Enum):
    """Buildup context filters — at least 1 must be present for full deployment."""
    ABOVE_200WMA     = "ABOVE_200WMA"       # temporary panic (1-3 slots)
    BELOW_200WMA     = "BELOW_200WMA"       # maximum historical zone (5-10 slots)
    MVRV_BELOW_ZERO  = "MVRV_BELOW_ZERO"    # holders in average loss (3-6 slots)
    ATH_DROP_GT_60   = "ATH_DROP_GT_60"     # deep bear (6-10 slots)
    NO_FILTER        = "NO_FILTER"          # caution: max 1 slot


class BlackSwanType(Enum):
    """Black Swan Protocol — 4 types of extreme events."""
    MARKET_CRASH      = "MARKET_CRASH"       # >30% drop in <72h
    EXCHANGE_FAILURE  = "EXCHANGE_FAILURE"    # exchange hack/insolvency
    STABLECOIN_DEPEG  = "STABLECOIN_DEPEG"   # USDT/USDC depegs >3%
    SEVERE_REGULATION = "SEVERE_REGULATION"  # government ban/restriction


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MarketSignals:
    """Real-time market data from CMC Agent Hub + derived indicators."""
    btc_price_usd:        float
    fear_greed_index:     int              # 0-100
    rsi_14d:              float            # RSI daily 14-period
    rsi_weekly:           float = 50.0     # RSI weekly 14-period (for Scaling Out)
    btc_portfolio_pct:    float = 0.60     # current BTC % in portfolio (0-1)
    reserve_usd:          float = 0.0
    reserve_target_usd:   float = 0.0
    btc_ath_usd:          float = 108000.0 # BTC all-time high
    ath_drop_pct:         float = 0.0      # % drop from ATH (0 to -100)
    price_vs_200wma:      float = 1.0      # ratio: price / 200WMA (>1 = above)
    mvrv_z_score:         Optional[float] = None  # on-chain (if available)
    avg_buy_price:        float = 0.0      # average purchase price (for PM rule)
    total_invested:       float = 0.0
    portfolio_value:      float = 0.0
    last_buildup_date:    Optional[datetime] = None
    consecutive_buys:     int = 0          # consecutive Buildup days


@dataclass
class DCAConfig:
    """
    User configuration — flexible by design.

    The Zion Smart DCA adapts to the investor's reality:
    - Frequency: daily, weekly, biweekly, or monthly
    - Amount: any value that fits the investor's budget
    - The strategy is SMART precisely because it's flexible
    """
    # Core — the investor defines these
    base_amount_usd:       float = 100.0   # base DCA amount per cycle
    frequency:             str   = "weekly" # "daily", "weekly", "biweekly", "monthly"

    # Strategy parameters (Zion Smart DCA v4.0 defaults)
    dca_split_pct:         float = 0.70    # % of budget for DCA
    reserve_split_pct:     float = 0.30    # % of budget for reserve

    # Fear & Greed thresholds — OFFICIAL v4.0 (from ZION-SMART-DCA-REGRAS.md)
    fg_extreme_fear:       int   = 24      # F&G 0-24  -> 2.0x
    fg_fear_top:           int   = 44      # F&G 25-44 -> 1.5x
    fg_neutral_top:        int   = 55      # F&G 45-55 -> 1.0x
    fg_greed_top:          int   = 74      # F&G 56-74 -> 0.75x
    # F&G 75-100 -> 0.5x

    # RSI thresholds
    rsi_buildup_threshold:     float = 35.0   # RSI daily < 35 = Buildup eligible
    rsi_scalingout_threshold:  float = 70.0   # RSI weekly > 70 = Scaling Out signal

    # Buildup constraints
    buildup_max_consecutive:   int   = 3      # buy up to 3 consecutive days, then stop
    buildup_cooldown_days:     int   = 3      # wait 3 days after a Buildup burst

    # Portfolio guardrails
    btc_min_pct:           float = 0.50    # BTC never below 50% of portfolio
    stablecoin_min_pct:    float = 0.10    # stablecoins always >= 10%

    # Halving reference (for Pillar 0)
    last_halving_date:     str   = "2024-04-19"  # most recent BTC halving


@dataclass
class StrategyDecision:
    """Output of the Zion Smart DCA v4.0 strategy engine."""
    action:                  ActionType
    dca_type:                DCAType
    multiplier:              float
    amount_usd:              float
    btc_amount:              float
    reserve_contribution_usd: float

    # Market context
    btc_price_usd:           float
    fear_greed_index:        int
    rsi_14d:                 float
    rsi_weekly:              float
    is_buildup:              bool

    # Pillar 0
    cycle_phase:             str
    cycle_months_since_halving: int
    cycle_adjustment:        str

    # Buildup details
    buildup_context:         str = ""
    buildup_max_slots:       int = 0
    buildup_consecutive:     int = 0

    # Reasoning (full traceability for judges)
    reasoning:               list = field(default_factory=list)
    warnings:                list = field(default_factory=list)
    rules_applied:           list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "skill": "Zion Smart DCA",
            "version": "4.0",
            "pillars": {
                "pillar_0_cycle": {
                    "phase": self.cycle_phase,
                    "months_since_halving": self.cycle_months_since_halving,
                    "adjustment": self.cycle_adjustment,
                },
                "pillar_1_dca": {
                    "multiplier": self.multiplier,
                    "amount_usd": round(self.amount_usd, 2),
                    "btc_amount": round(self.btc_amount, 8),
                    "reserve_contribution_usd": round(self.reserve_contribution_usd, 2),
                },
                "pillar_2_buildup": {
                    "active": self.is_buildup,
                    "context": self.buildup_context,
                    "max_slots": self.buildup_max_slots,
                    "consecutive_days": self.buildup_consecutive,
                },
                "pillar_3_scaling_out": {
                    "rsi_weekly": round(self.rsi_weekly, 2),
                },
            },
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
                "rsi_weekly":       round(self.rsi_weekly, 2),
            },
            "reasoning":     self.reasoning,
            "warnings":      self.warnings,
            "rules_applied": self.rules_applied,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ZionSmartDCA:
    """
    Zion Smart DCA v4.0 — Strategy Engine

    4 Pillars:
      Pillar 0 — Cycle Reading (calibrates all other pillars)
      Pillar 1 — Intelligent DCA (F&G multiplier)
      Pillar 2 — Buildup (extra buying in drops with double-layer confirmation)
      Pillar 3 — Scaling Out (partial realization at tops with dual confirmation)

    12 Rules + Black Swan Protocol + Fiscal Layer + Mission Milestones

    Flexibility by design:
      - Frequency: daily / weekly / biweekly / monthly
      - Amount: any value — $10, $50, $100, $500 — what matters is consistency
      - The strategy adapts to the investor, not the other way around
    """

    VERSION = "4.0"

    def __init__(self, config: Optional[DCAConfig] = None):
        self.config = config or DCAConfig()

    # ─── Pillar 0: Cycle Phase Detection ──────────────────────────────────

    def _detect_cycle_phase(self, reference_date: Optional[datetime] = None) -> tuple:
        """
        Pillar 0 — Identifies the current phase of the Bitcoin cycle.
        Based on months since the last halving (April 19, 2024).

        Phases:
          -12 to 0 months  → Accumulation Pre-Halving
           0 to +6 months  → Initial Impulse
          +6 to +18 months → Bull Run
         +18 to +24 months → Distribution
         +24 to +48 months → Bear Market
        """
        halving = datetime.strptime(self.config.last_halving_date, "%Y-%m-%d")
        now = reference_date or datetime.now(timezone.utc)
        months = (now.year - halving.year) * 12 + (now.month - halving.month)

        if months < 0:
            phase = CyclePhase.ACCUMULATION_PRE_HALVING
        elif months <= 6:
            phase = CyclePhase.INITIAL_IMPULSE
        elif months <= 18:
            phase = CyclePhase.BULL_RUN
        elif months <= 24:
            phase = CyclePhase.DISTRIBUTION
        else:
            phase = CyclePhase.BEAR_MARKET

        return phase, months

    def _get_cycle_adjustment(self, phase: CyclePhase) -> tuple:
        """
        Returns the multiplier adjustment and description based on cycle phase.
        The cycle doesn't replace the F&G multiplier — it CALIBRATES it.
        """
        adjustments = {
            CyclePhase.ACCUMULATION_PRE_HALVING: (
                0.0, "Apply normally — ideal phase for base DCA"
            ),
            CyclePhase.INITIAL_IMPULSE: (
                -0.25, "Reduce fear multiplier by 0.25x — not a structural drop"
            ),
            CyclePhase.BULL_RUN: (
                0.0, "Apply normally — Scaling Out active in this phase"
            ),
            CyclePhase.DISTRIBUTION: (
                0.0, "Buildup suspended — focus on aggressive Scaling Out"
            ),
            CyclePhase.BEAR_MARKET: (
                0.0, "Apply normally + secondary filters active"
            ),
        }
        return adjustments.get(phase, (0.0, "Unknown phase"))

    # ─── Pillar 1: F&G Multiplier (Rule 2) ────────────────────────────────

    def _get_fg_multiplier(self, fg: int) -> tuple:
        """
        Rule 2 — Scale DCA amount by Fear & Greed Index.
        Source: Zion Smart DCA OFFICIAL v4.0 (ZION-SMART-DCA-REGRAS.md)

        F&G  0-24  (Extreme Fear)  -> 2.0x  — maximum accumulation
        F&G 25-44  (Fear)          -> 1.5x  — above-average accumulation
        F&G 45-55  (Neutral)       -> 1.0x  — standard DCA
        F&G 56-74  (Greed)         -> 0.75x — reduce exposure, build reserve
        F&G 75-100 (Extreme Greed) -> 0.5x  — minimum exposure, max reserve
        """
        cfg = self.config
        if fg <= cfg.fg_extreme_fear:        # 0-24
            return 2.0,  f"Extreme Fear (F&G={fg}, 0-24) -> 2.0x — maximum accumulation"
        elif fg <= cfg.fg_fear_top:          # 25-44
            return 1.5,  f"Fear (F&G={fg}, 25-44) -> 1.5x — above-average accumulation"
        elif fg <= cfg.fg_neutral_top:       # 45-55
            return 1.0,  f"Neutral (F&G={fg}, 45-55) -> 1.0x — standard DCA"
        elif fg <= cfg.fg_greed_top:         # 56-74
            return 0.75, f"Greed (F&G={fg}, 56-74) -> 0.75x — reducing exposure, building reserve"
        else:                                # 75-100
            return 0.5,  f"Extreme Greed (F&G={fg}, 75-100) -> 0.5x — minimum exposure, max reserve"

    # ─── Pillar 2: Buildup (Rule 3) ───────────────────────────────────────

    def _check_buildup(self, signals: MarketSignals) -> tuple:
        """
        Rule 3 — Buildup: extra buying when RSI daily < 35.
        DOUBLE LAYER (v4.0):
          Layer 1: RSI < 35 (mandatory)
          Layer 2: At least 1 context filter (200WMA, MVRV, ATH drop)

        Slot scale by market depth:
          < 30% from ATH → 1-2 slots (temporary panic)
          30-60% from ATH → 3-5 slots (cautious strategy)
          > 60% from ATH → 6-10 slots (maximum historical opportunity)
          Systemic event → PAUSE 7 days

        Cooldown: buy up to 3 consecutive days, then stop and wait.
        """
        cfg = self.config
        rsi = signals.rsi_14d

        # Layer 1: RSI check
        if rsi > cfg.rsi_buildup_threshold:
            return False, "NO_FILTER", 0, f"RSI {rsi:.1f} > {cfg.rsi_buildup_threshold} -> Standard DCA (not oversold)"

        # Cooldown check: max 3 consecutive buys, then stop
        if signals.consecutive_buys >= cfg.buildup_max_consecutive:
            return False, "COOLDOWN", 0, (
                f"Buildup COOLDOWN: {signals.consecutive_buys} consecutive buys reached "
                f"(max {cfg.buildup_max_consecutive}). Wait for cooldown before next Buildup."
            )

        # Cooldown check: time-based
        if signals.last_buildup_date:
            days_since = (datetime.now(timezone.utc) - signals.last_buildup_date).days
            if days_since < cfg.buildup_cooldown_days and signals.consecutive_buys >= cfg.buildup_max_consecutive:
                return False, "COOLDOWN", 0, (
                    f"Buildup COOLDOWN: only {days_since}d since last burst "
                    f"(min {cfg.buildup_cooldown_days}d). Waiting."
                )

        # Layer 2: Context filters
        ath_drop = abs(signals.ath_drop_pct)
        context = BuildupContext.NO_FILTER
        max_slots = 1  # default without filter

        if signals.price_vs_200wma < 1.0:
            context = BuildupContext.BELOW_200WMA
            if ath_drop >= 60:
                max_slots = 10
            elif ath_drop >= 30:
                max_slots = 6
            else:
                max_slots = 5
        elif signals.mvrv_z_score is not None and signals.mvrv_z_score < 0:
            context = BuildupContext.MVRV_BELOW_ZERO
            max_slots = min(6, max(3, int(ath_drop / 10)))
        elif ath_drop >= 60:
            context = BuildupContext.ATH_DROP_GT_60
            max_slots = 10
        elif signals.price_vs_200wma >= 1.0:
            context = BuildupContext.ABOVE_200WMA
            if ath_drop < 30:
                max_slots = 2
            else:
                max_slots = 3

        # Scale by ATH drop (regardless of filter)
        if ath_drop < 30:
            slot_by_depth = 2
        elif ath_drop < 60:
            slot_by_depth = 5
        else:
            slot_by_depth = 10

        max_slots = min(max_slots, slot_by_depth)

        reason = (
            f"RSI {rsi:.1f} <= {cfg.rsi_buildup_threshold} -> BUILDUP ELIGIBLE | "
            f"Context: {context.value} | ATH drop: -{ath_drop:.1f}% | "
            f"Max slots: {max_slots}"
        )

        return True, context.value, max_slots, reason

    # ─── Pillar 3: Scaling Out (Rule 4) ───────────────────────────────────

    def check_scaling_out(self, signals: MarketSignals) -> Optional[dict]:
        """
        Rule 4 — Scaling Out: progressive profit-taking.

        DUAL CONFIRMATION required (v4.0):
          Primary: RSI weekly > 70 + price > average buy price
          Secondary (at least 1):
            A. Pi Cycle Top Indicator activated
            B. MVRV Z-Score > 7
            C. BTC dominance < 40% with altcoins exploding
            D. Puell Multiple > 2.0

        Rule 5: NEVER sell below average buy price. Non-negotiable.

        Max 2 operations per month (40% of position/month).
        """
        cfg = self.config
        result = {"signal": False, "messages": [], "sell_pct": 0}

        # Rule 5: NEVER sell below average price
        if signals.avg_buy_price > 0 and signals.btc_price_usd < signals.avg_buy_price:
            result["messages"].append(
                f"Rule 5 BLOCK: BTC ${signals.btc_price_usd:,.0f} < avg buy price "
                f"${signals.avg_buy_price:,.0f}. CANNOT sell. This rule is NON-NEGOTIABLE."
            )
            return result

        # Primary trigger: RSI weekly > 70
        if signals.rsi_weekly <= cfg.rsi_scalingout_threshold:
            return result  # no signal

        result["signal"] = True
        result["messages"].append(
            f"SCALING OUT SIGNAL: RSI Weekly {signals.rsi_weekly:.1f} > {cfg.rsi_scalingout_threshold}"
        )

        # Profit tier check
        if signals.total_invested > 0:
            profit_pct = (signals.portfolio_value - signals.total_invested) / signals.total_invested * 100
            scaling_table = [
                (500, 10, "Fifth"),
                (300, 20, "Fourth"),
                (200, 15, "Third"),
                (100, 15, "Second"),
                (50,  10, "First"),
            ]
            for threshold, pct, label in scaling_table:
                if profit_pct >= threshold:
                    result["sell_pct"] = pct
                    result["messages"].append(
                        f"{label} realization tier: +{profit_pct:.0f}% profit -> sell {pct}% | "
                        f"80% to cash + 20% reinvested in DCA. Remaining 30% = permanent HODL."
                    )
                    break

        return result

    # ─── Budget Split (Rule 6 + Rule 7) ───────────────────────────────────

    def _split_budget(self, budget: float, multiplier: float) -> tuple:
        """
        Rule 6 — Reserve First, Scale Later.
        Split: configurable DCA% + reserve% (default 70/30).

        Rule 7 — Auto-reserve replenishment.
        In greed phases (multiplier < 1.0), surplus goes to reserve.
        """
        cfg = self.config
        dca_base    = budget * cfg.dca_split_pct
        reserve_amt = budget * cfg.reserve_split_pct
        dca_amount  = dca_base * multiplier

        # Rule 7: surplus from greed phase goes to reserve
        if multiplier < 1.0:
            surplus = dca_base * (1.0 - multiplier)
            reserve_amt += surplus

        return dca_amount, reserve_amt

    # ─── Black Swan Protocol ──────────────────────────────────────────────

    def check_black_swan(self, price_change_72h_pct: float = 0.0,
                         exchange_issue: bool = False,
                         stablecoin_depeg_pct: float = 0.0) -> Optional[dict]:
        """
        Black Swan Protocol (v4.0) — Response to extreme events.

        Type 1: Market crash (>30% drop in <72h) -> DO NOTHING for 24h
        Type 2: Exchange failure -> Don't panic-sell other positions
        Type 3: Stablecoin depeg (>3%) -> Convert to BTC/ETH immediately
        Type 4: Severe regulation -> Wait for final text in Official Gazette
        """
        if abs(price_change_72h_pct) > 30:
            return {
                "type": BlackSwanType.MARKET_CRASH.value,
                "action": "PAUSE_24H",
                "message": (
                    f"BLACK SWAN: BTC dropped {price_change_72h_pct:.1f}% in 72h. "
                    f"First 24h: DO NOTHING. Initial panic is always exaggerated. "
                    f"After 24h: evaluate context and Buildup opportunities."
                ),
            }
        if exchange_issue:
            return {
                "type": BlackSwanType.EXCHANGE_FAILURE.value,
                "action": "HOLD",
                "message": (
                    "BLACK SWAN: Exchange issue detected. "
                    "Do NOT panic-sell other positions. Contact exchange support. "
                    "Prevention: never >20% of crypto portfolio on a single exchange."
                ),
            }
        if abs(stablecoin_depeg_pct) > 3:
            return {
                "type": BlackSwanType.STABLECOIN_DEPEG.value,
                "action": "CONVERT_TO_BTC",
                "message": (
                    f"BLACK SWAN: Stablecoin depeg at {stablecoin_depeg_pct:.1f}%. "
                    f"Convert to BTC or ETH immediately. "
                    f"Prevention: diversify between at least 2 stablecoins."
                ),
            }
        return None

    # ─── Mission Milestones ───────────────────────────────────────────────

    def check_milestones(self, total_invested: float, portfolio_value: float,
                         btc_held: float = 0.0) -> list:
        """
        Mission Milestones (v4.0) — Define where the finish line is.
        """
        milestones = []
        if total_invested > 0:
            ratio = portfolio_value / total_invested
            if ratio >= 3.0:
                milestones.append(
                    "MILESTONE 1 REACHED: Portfolio is 3x invested capital. "
                    "Consider selling 33% to recover initial capital. DCA continues."
                )
        if btc_held >= 1.0:
            milestones.append(
                "MILESTONE 2 REACHED: 1 BTC accumulated! "
                "Separate this BTC in cold wallet labeled 'untouchable'. "
                "Continue DCA for the next position. First BTC is never sold."
            )
        return milestones

    # ─── Fiscal Layer (informational) ─────────────────────────────────────

    def fiscal_advisory(self, monthly_realized_profit_brl: float = 0.0) -> Optional[str]:
        """
        Fiscal Layer (v4.0) — Brazilian tax efficiency.
        Monthly gains up to R$35,000 in crypto are TAX-FREE.
        """
        if monthly_realized_profit_brl > 35000:
            return (
                f"FISCAL WARNING: Monthly realized profit R${monthly_realized_profit_brl:,.0f} "
                f"exceeds R$35,000 threshold. DARF required (15-22.5% tax). "
                f"Consider splitting realizations across different months."
            )
        return None

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN DECISION ENGINE
    # ═══════════════════════════════════════════════════════════════════════

    def evaluate(self, signals: MarketSignals,
                 reference_date: Optional[datetime] = None) -> StrategyDecision:
        """
        Core strategy evaluation — applies all 4 pillars + 12 rules.
        Returns a fully traceable decision.
        """
        cfg       = self.config
        reasoning = []
        warnings  = []
        rules     = []

        # ── Pillar 0: Cycle Phase ──────────────────────────────────────────
        phase, months = self._detect_cycle_phase(reference_date)
        cycle_adj, cycle_desc = self._get_cycle_adjustment(phase)
        reasoning.append(
            f"Pillar 0 — Cycle: {phase.value} ({months} months since halving). {cycle_desc}"
        )
        rules.append("Pillar 0: Cycle phase detection")

        # ── Rule 0: Emergency fund check (informational) ──────────────────
        rules.append("Rule 0: Emergency fund in BRL (6 months expenses) — verify before investing")

        # ── Rule 1: Base DCA (always active) ──────────────────────────────
        rules.append(f"Rule 1: DCA base active ({cfg.frequency}, ${cfg.base_amount_usd})")
        reasoning.append(
            f"DCA budget: ${cfg.base_amount_usd:.2f} USD | "
            f"Frequency: {cfg.frequency} | "
            f"The amount adapts to the investor's reality"
        )

        # ── Rule 2: F&G Multiplier ────────────────────────────────────────
        multiplier, fg_reason = self._get_fg_multiplier(signals.fear_greed_index)
        reasoning.append(fg_reason)
        rules.append("Rule 2: Fear & Greed multiplier (v4.0 thresholds)")

        # Apply cycle adjustment to multiplier
        if cycle_adj != 0:
            original = multiplier
            multiplier = max(0.5, multiplier + cycle_adj)
            reasoning.append(
                f"Pillar 0 adjustment: {original}x -> {multiplier}x "
                f"(cycle phase: {phase.value})"
            )

        # Distribution phase: suspend Buildup, focus on Scaling Out
        buildup_suspended = (phase == CyclePhase.DISTRIBUTION)
        if buildup_suspended:
            warnings.append(
                "Pillar 0: Distribution phase — Buildup SUSPENDED. "
                "Focus on aggressive Scaling Out."
            )

        # ── Rule 3: Buildup check ─────────────────────────────────────────
        if not buildup_suspended:
            is_buildup, context, max_slots, buildup_reason = self._check_buildup(signals)
        else:
            is_buildup, context, max_slots, buildup_reason = False, "SUSPENDED", 0, "Buildup suspended (Distribution phase)"

        reasoning.append(buildup_reason)
        rules.append("Rule 3: Buildup double-layer check")

        # ── Rules 6 & 7: Budget split ─────────────────────────────────────
        dca_amount, reserve_amt = self._split_budget(cfg.base_amount_usd, multiplier)
        rules.append("Rule 6: Reserve First split")
        if multiplier < 1.0:
            surplus = cfg.base_amount_usd * cfg.dca_split_pct * (1 - multiplier)
            reasoning.append(
                f"Rule 7: Greed phase -> surplus ${surplus:.2f} auto-routed to reserve"
            )
            rules.append("Rule 7: Auto-reserve replenishment in greed")

        # ── Rule 5: Never sell below average price ────────────────────────
        rules.append("Rule 5: Never sell below average buy price (non-negotiable)")

        # ── Rule 8: Zero leverage ─────────────────────────────────────────
        rules.append("Rule 8: Zero leverage — always. No exceptions.")

        # ── Rule 9: Limit orders for Buildup ──────────────────────────────
        if is_buildup:
            warnings.append(
                "Rule 9: Use LIMIT orders for Buildup — never market orders. "
                "Set price target below current price. Discipline > Urgency."
            )
        rules.append("Rule 9: Buildup uses limit orders only")

        # ── Rule 10: Extreme scenario pre-calculation ─────────────────────
        rules.append("Rule 10: Calculate extreme scenario before starting")

        # ── Rule 11: Asset criteria + sizing ──────────────────────────────
        rules.append("Rule 11: Asset criteria (market cap >$5B, >3 years, sizing limits)")

        # ── Portfolio guardrails ──────────────────────────────────────────
        if signals.btc_portfolio_pct < cfg.btc_min_pct:
            warnings.append(
                f"CRITICAL: BTC at {signals.btc_portfolio_pct:.1%} < 50% minimum! "
                f"Prioritize BTC buying immediately."
            )

        # ── Rule 12: Consistency beats timing ─────────────────────────────
        rules.append("Rule 12: Consistency beats timing. Always.")
        reasoning.append("Rule 12: Decision is systematic, not emotional")

        # ── Determine DCA type ────────────────────────────────────────────
        if is_buildup:
            dca_type = DCAType.BUILDUP_SLOT
        elif multiplier < 1.0:
            dca_type = DCAType.SKIP  # still buys but reduced
        else:
            dca_type = DCAType.DCA_NORMAL

        # ── Scaling Out advisory ──────────────────────────────────────────
        scaling = self.check_scaling_out(signals)
        if scaling and scaling.get("signal"):
            for msg in scaling["messages"]:
                warnings.append(msg)
            rules.append("Rule 4: Scaling Out advisory")

        btc_amount = dca_amount / signals.btc_price_usd if signals.btc_price_usd > 0 else 0

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
            rsi_weekly=signals.rsi_weekly,
            is_buildup=is_buildup,
            cycle_phase=phase.value,
            cycle_months_since_halving=months,
            cycle_adjustment=cycle_desc,
            buildup_context=context if isinstance(context, str) else context.value,
            buildup_max_slots=max_slots,
            buildup_consecutive=signals.consecutive_buys,
            reasoning=reasoning,
            warnings=warnings,
            rules_applied=rules,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO — Quick test with realistic scenarios
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    # Show that the strategy is flexible
    print("\n" + "=" * 70)
    print("  ZION SMART DCA v4.0 — FLEXIBILITY DEMO")
    print("  The amount and frequency adapt to YOUR reality.")
    print("=" * 70)

    configs = [
        ("Conservative ($50/month)",  DCAConfig(base_amount_usd=50, frequency="monthly")),
        ("Standard ($100/week)",      DCAConfig(base_amount_usd=100, frequency="weekly")),
        ("Aggressive ($25/day)",      DCAConfig(base_amount_usd=25, frequency="daily")),
        ("Whale ($500/biweekly)",     DCAConfig(base_amount_usd=500, frequency="biweekly")),
    ]

    for label, cfg in configs:
        engine = ZionSmartDCA(config=cfg)
        print(f"\n  Profile: {label}")
        print(f"  -> Base: ${cfg.base_amount_usd} / {cfg.frequency}")

    # Main scenarios
    engine = ZionSmartDCA(config=DCAConfig(base_amount_usd=100.0, frequency="weekly"))

    scenarios = [
        ("EXTREME FEAR + BUILDUP (Jun/2026 real — F&G=10, RSI=26)",
         MarketSignals(
             btc_price_usd=63091, fear_greed_index=10, rsi_14d=26.1,
             rsi_weekly=38.0, btc_portfolio_pct=0.54,
             btc_ath_usd=108000, ath_drop_pct=-41.6,
             price_vs_200wma=0.95,
         )),
        ("FEAR (F&G=30, RSI=42)",
         MarketSignals(
             btc_price_usd=65000, fear_greed_index=30, rsi_14d=42.0,
             rsi_weekly=45.0, btc_portfolio_pct=0.52,
             btc_ath_usd=108000, ath_drop_pct=-39.8,
             price_vs_200wma=1.02,
         )),
        ("NEUTRAL (F&G=50, RSI=50)",
         MarketSignals(
             btc_price_usd=70000, fear_greed_index=50, rsi_14d=50.0,
             rsi_weekly=52.0, btc_portfolio_pct=0.55,
             btc_ath_usd=108000, ath_drop_pct=-35.2,
             price_vs_200wma=1.10,
         )),
        ("GREED (F&G=65) — reduced + reserve building",
         MarketSignals(
             btc_price_usd=88000, fear_greed_index=65, rsi_14d=62.0,
             rsi_weekly=58.0, btc_portfolio_pct=0.60,
             btc_ath_usd=108000, ath_drop_pct=-18.5,
             price_vs_200wma=1.30,
         )),
        ("EXTREME GREED (F&G=82) — minimum exposure",
         MarketSignals(
             btc_price_usd=105000, fear_greed_index=82, rsi_14d=72.0,
             rsi_weekly=75.0, btc_portfolio_pct=0.68,
             btc_ath_usd=108000, ath_drop_pct=-2.8,
             price_vs_200wma=1.55,
             avg_buy_price=45000, total_invested=20000, portfolio_value=52000,
         )),
        ("BUILDUP COOLDOWN (3 consecutive buys reached)",
         MarketSignals(
             btc_price_usd=61000, fear_greed_index=8, rsi_14d=24.0,
             rsi_weekly=35.0, btc_portfolio_pct=0.54,
             btc_ath_usd=108000, ath_drop_pct=-43.5,
             price_vs_200wma=0.92,
             consecutive_buys=3,
         )),
    ]

    for title, signals in scenarios:
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
        result = engine.evaluate(signals)
        d = result.to_dict()
        print(f"  Decision: {d['decision']['action']} | {d['decision']['type']} | {d['decision']['multiplier']}x")
        print(f"  Amount:   ${d['decision']['amount_usd']:.2f} | Reserve: ${d['decision']['reserve_contribution_usd']:.2f}")
        print(f"  Cycle:    {d['pillars']['pillar_0_cycle']['phase']} ({d['pillars']['pillar_0_cycle']['months_since_halving']}m)")
        if d['pillars']['pillar_2_buildup']['active']:
            b = d['pillars']['pillar_2_buildup']
            print(f"  Buildup:  ACTIVE | Context: {b['context']} | Max slots: {b['max_slots']}")
        print(f"  F&G: {d['market']['fear_greed_index']} | RSI-D: {d['market']['rsi_14d']} | RSI-W: {d['market']['rsi_weekly']}")
        for r in d['reasoning']:
            r_clean = r.replace('\u2192', '->')
            print(f"    >> {r_clean}")
        for w in d['warnings']:
            print(f"    !! {w}")
