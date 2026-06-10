# -*- coding: utf-8 -*-
"""
Zion Smart DCA v4.0 — ERC-8183 Agentic Commerce
Enables other agents to request DCA analysis as paid jobs.

BNB Hack 2026 | Track 2: Crypto Intelligence Agent
Special Prize: Best Use of BNB AI Agent SDK ($2,000)

ERC-8183 defines a standard for agent-to-agent commerce:
  - Jobs: discrete units of work that agents can request
  - Escrow: payment held until job is completed
  - Verification: results are verifiable on-chain

This module wraps the Zion Smart DCA strategy engine as a set of
purchasable analysis jobs that any ERC-8183 compatible agent can request.

Job Types:
  1. analyze_market  — Get current market analysis + DCA recommendation
  2. backtest_period — Run backtest for a specific historical period
  3. portfolio_check — Check if it's time to scale out (take profits)
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from strategy import ZionSmartDCA, DCAConfig, MarketSignals, StrategyDecision
from indicators import LiveSignals, fetch_live_signals


# ═══════════════════════════════════════════════════════════════════════════════
# JOB STATUS & METADATA
# ═══════════════════════════════════════════════════════════════════════════════

class JobStatus:
    """ERC-8183 job lifecycle states."""
    CREATED    = "created"
    FUNDED     = "funded"       # escrow received
    EXECUTING  = "executing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    DISPUTED   = "disputed"


@dataclass
class JobMetadata:
    """ERC-8183 compatible job metadata for escrow."""
    job_id:          str
    job_type:        str
    description:     str
    status:          str
    created_at:      str
    price_usd:       float
    price_bnb:       float          # estimated BNB equivalent
    estimated_time:  int             # seconds
    provider:        str = "Zion Smart DCA v4.0"
    provider_agent:  str = "0x4E9feDB6DFb93fe7Ae98E2d2Bfe4fb6398A568bd"
    erc_standard:    str = "ERC-8183"
    chain_id:        int = 97        # BSC Testnet
    result:          Optional[Dict] = None
    completed_at:    Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # Remove None fields for cleaner JSON
        return {k: v for k, v in d.items() if v is not None}


# ═══════════════════════════════════════════════════════════════════════════════
# JOB PRICING
# ═══════════════════════════════════════════════════════════════════════════════

JOB_PRICING = {
    "analyze_market": {
        "description": "Real-time market analysis with DCA recommendation using "
                       "Fear & Greed Index, RSI signals, and halving cycle awareness.",
        "price_usd":      0.50,
        "price_bnb":      0.001,
        "estimated_time": 15,    # seconds
    },
    "backtest_period": {
        "description": "Run Zion Smart DCA backtest for a custom historical period. "
                       "Returns performance metrics, Sharpe ratio, and comparison vs standard DCA.",
        "price_usd":      2.00,
        "price_bnb":      0.004,
        "estimated_time": 60,
    },
    "portfolio_check": {
        "description": "Check if current market conditions warrant Scaling Out "
                       "(profit taking). Uses dual RSI confirmation + cycle phase analysis.",
        "price_usd":      0.25,
        "price_bnb":      0.0005,
        "estimated_time": 10,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN JOB ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ZionAnalysisJob:
    """
    ERC-8183 job provider for Zion Smart DCA analysis.

    Enables agent-to-agent commerce: any ERC-8183 compatible agent can
    request analysis jobs, pay via escrow, and receive verifiable results.

    Usage:
        job_engine = ZionAnalysisJob()

        # 1. List available jobs
        catalog = job_engine.list_jobs()

        # 2. Create a job (returns metadata for escrow)
        meta = job_engine.create_job('analyze_market', {'budget_usd': 100})

        # 3. Execute the job (after escrow is funded)
        result = job_engine.execute_job(meta.job_id, 'analyze_market', {'budget_usd': 100})
    """

    def __init__(self, config: Optional[DCAConfig] = None):
        self.engine = ZionSmartDCA(config=config)
        self._jobs: Dict[str, JobMetadata] = {}

    # ─── Job Catalog ──────────────────────────────────────────────────────

    def list_jobs(self) -> Dict[str, Any]:
        """
        Returns the catalog of available job types (ERC-8183 service discovery).
        Other agents use this to understand what analysis is available.
        """
        return {
            "provider":      "Zion Smart DCA v4.0",
            "erc_standard":  "ERC-8183",
            "chain_id":      97,
            "agent_address": "0x4E9feDB6DFb93fe7Ae98E2d2Bfe4fb6398A568bd",
            "jobs":          JOB_PRICING,
        }

    # ─── Job Creation (pre-escrow) ────────────────────────────────────────

    def create_job(self, job_type: str, params: Dict[str, Any]) -> JobMetadata:
        """
        Create a new analysis job. Returns metadata for escrow funding.

        The requesting agent uses this metadata to:
          1. Verify pricing and estimated completion time
          2. Fund the escrow contract on-chain
          3. Then call execute_job() with the funded job_id

        Args:
            job_type: One of 'analyze_market', 'backtest_period', 'portfolio_check'
            params:   Job-specific parameters

        Returns:
            JobMetadata with escrow details
        """
        if job_type not in JOB_PRICING:
            raise ValueError(
                f"Unknown job type '{job_type}'. "
                f"Available: {list(JOB_PRICING.keys())}"
            )

        pricing = JOB_PRICING[job_type]
        job_id = f"zion-{job_type}-{uuid.uuid4().hex[:12]}"

        meta = JobMetadata(
            job_id         = job_id,
            job_type       = job_type,
            description    = pricing["description"],
            status         = JobStatus.CREATED,
            created_at     = datetime.now(timezone.utc).isoformat(),
            price_usd      = pricing["price_usd"],
            price_bnb      = pricing["price_bnb"],
            estimated_time = pricing["estimated_time"],
        )

        self._jobs[job_id] = meta
        return meta

    # ─── Job Execution ────────────────────────────────────────────────────

    def execute_job(self, job_id: str, job_type: str,
                    params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a funded job and return results.

        In a full ERC-8183 implementation, this would:
          1. Verify escrow is funded on-chain
          2. Execute the analysis
          3. Submit results hash on-chain
          4. Release escrow to provider

        Args:
            job_id:   The job identifier from create_job()
            job_type: Type of analysis to run
            params:   Job-specific parameters

        Returns:
            Dict with job results + metadata
        """
        # Update status
        if job_id in self._jobs:
            self._jobs[job_id].status = JobStatus.EXECUTING

        try:
            if job_type == "analyze_market":
                result = self._analyze_market(params)
            elif job_type == "backtest_period":
                result = self._backtest_period(params)
            elif job_type == "portfolio_check":
                result = self._portfolio_check(params)
            else:
                raise ValueError(f"Unknown job type: {job_type}")

            # Update job metadata
            if job_id in self._jobs:
                self._jobs[job_id].status = JobStatus.COMPLETED
                self._jobs[job_id].completed_at = datetime.now(timezone.utc).isoformat()
                self._jobs[job_id].result = result

            return {
                "job_id":       job_id,
                "job_type":     job_type,
                "status":       JobStatus.COMPLETED,
                "erc_standard": "ERC-8183",
                "provider":     "Zion Smart DCA v4.0",
                "timestamp":    datetime.now(timezone.utc).isoformat(),
                "result":       result,
            }

        except Exception as e:
            if job_id in self._jobs:
                self._jobs[job_id].status = JobStatus.FAILED
            return {
                "job_id":    job_id,
                "job_type":  job_type,
                "status":    JobStatus.FAILED,
                "error":     str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    # ─── Job Status Query ─────────────────────────────────────────────────

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Query the status of a job (ERC-8183 status endpoint)."""
        meta = self._jobs.get(job_id)
        if meta is None:
            return None
        return meta.to_dict()

    # ═══════════════════════════════════════════════════════════════════════
    # JOB IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════════════════════

    def _analyze_market(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Job: analyze_market
        Fetches live signals and runs the full Zion Smart DCA strategy engine.

        Params:
            budget_usd (float): DCA base amount (default: 100)
            frequency  (str):   DCA frequency (default: 'weekly')
            btc_pct    (float): Current BTC allocation (default: 0.54)

        Returns:
            Full strategy decision with market context, reasoning, and rules applied.
        """
        budget    = params.get("budget_usd", 100.0)
        frequency = params.get("frequency", "weekly")
        btc_pct   = params.get("btc_pct", 0.54)
        avg_price = params.get("avg_buy_price_usd", 0.0)

        # Fetch live market signals
        live = fetch_live_signals()

        # Build MarketSignals
        signals = MarketSignals(
            btc_price_usd     = live.btc_price_usd,
            fear_greed_index  = live.fear_greed_value,
            rsi_14d           = live.rsi_14d,
            rsi_weekly        = live.rsi_weekly,
            btc_portfolio_pct = btc_pct,
            btc_ath_usd       = live.btc_ath_usd,
            ath_drop_pct      = live.ath_drop_pct,
            price_vs_200wma   = live.price_vs_200wma,
            avg_buy_price     = avg_price,
        )

        # Run strategy engine
        config = DCAConfig(base_amount_usd=budget, frequency=frequency)
        engine = ZionSmartDCA(config=config)
        decision = engine.evaluate(signals)

        return {
            "job_type":      "analyze_market",
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "version":       "4.0",
            "market": {
                "btc_price_usd":    live.btc_price_usd,
                "fear_greed_index": live.fear_greed_value,
                "fear_greed_label": live.fear_greed_label,
                "rsi_daily":        live.rsi_14d,
                "rsi_weekly":       live.rsi_weekly,
                "ath_drop_pct":     live.ath_drop_pct,
                "price_vs_200wma":  live.price_vs_200wma,
                "cycle_phase":      live.cycle_phase,
            },
            "decision":      decision.to_dict(),
            "input_params": {
                "budget_usd": budget,
                "frequency":  frequency,
                "btc_pct":    btc_pct,
            },
        }

    def _backtest_period(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Job: backtest_period
        Runs a backtest simulation for a specified period.

        Params:
            start_date (str): Start date in YYYY-MM-DD format (default: '2021-01-01')
            end_date   (str): End date in YYYY-MM-DD format (default: today)
            budget_usd (float): DCA base amount (default: 100)
            frequency  (str): DCA frequency (default: 'weekly')

        Returns:
            Backtest summary with performance metrics.
        """
        start_str  = params.get("start_date", "2021-01-01")
        end_str    = params.get("end_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        budget     = params.get("budget_usd", 100.0)
        frequency  = params.get("frequency", "weekly")

        try:
            import yfinance as yf
            import numpy as np

            # Download historical data
            df = yf.download("BTC-USD", start=start_str, end=end_str,
                             interval="1wk", progress=False, auto_adjust=True)
            if df.empty:
                return {"error": "No data available for specified period"}

            closes = df["Close"].values.flatten().astype(float)
            config = DCAConfig(base_amount_usd=budget, frequency=frequency)
            engine = ZionSmartDCA(config=config)

            # Simple backtest: iterate weeks with simulated F&G
            total_invested = 0.0
            total_btc = 0.0
            weeks = len(closes)

            for i, price in enumerate(closes):
                if price <= 0:
                    continue
                # Simulate F&G based on price momentum
                if i >= 1:
                    change = (price - closes[i-1]) / closes[i-1] * 100
                    if change < -10:
                        fg = 15
                    elif change < -5:
                        fg = 30
                    elif change < 0:
                        fg = 45
                    elif change < 5:
                        fg = 55
                    elif change < 10:
                        fg = 65
                    else:
                        fg = 80
                else:
                    fg = 50

                signals = MarketSignals(
                    btc_price_usd=price,
                    fear_greed_index=fg,
                    rsi_14d=50.0,
                    rsi_weekly=50.0,
                )
                decision = engine.evaluate(signals)
                total_invested += decision.amount_usd
                total_btc += decision.btc_amount

            final_value = total_btc * closes[-1]
            total_return = ((final_value - total_invested) / total_invested * 100
                           if total_invested > 0 else 0)

            # Standard DCA comparison
            std_invested = budget * weeks
            std_btc = sum(budget / p for p in closes if p > 0)
            std_value = std_btc * closes[-1]
            std_return = ((std_value - std_invested) / std_invested * 100
                         if std_invested > 0 else 0)

            return {
                "job_type":       "backtest_period",
                "period":         f"{start_str} to {end_str}",
                "total_weeks":    weeks,
                "zion_smart_dca": {
                    "total_invested":  round(total_invested, 2),
                    "btc_accumulated": round(total_btc, 8),
                    "final_value":     round(final_value, 2),
                    "total_return_pct": round(total_return, 2),
                },
                "standard_dca": {
                    "total_invested":  round(std_invested, 2),
                    "btc_accumulated": round(std_btc, 8),
                    "final_value":     round(std_value, 2),
                    "total_return_pct": round(std_return, 2),
                },
                "outperformance_pp": round(total_return - std_return, 2),
                "version":        "4.0",
            }

        except ImportError:
            return {
                "error": "yfinance/numpy required for backtest. "
                         "Install with: pip install yfinance numpy"
            }
        except Exception as e:
            return {"error": f"Backtest failed: {str(e)}"}

    def _portfolio_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Job: portfolio_check
        Checks if current conditions warrant Scaling Out (profit taking).

        Params:
            avg_buy_price_usd (float): Average purchase price (required for Rule 5)
            total_invested    (float): Total USD invested
            portfolio_value   (float): Current portfolio value in USD
            btc_held          (float): Amount of BTC held

        Returns:
            Scaling out analysis with recommendations.
        """
        avg_price   = params.get("avg_buy_price_usd", 0.0)
        invested    = params.get("total_invested", 0.0)
        port_value  = params.get("portfolio_value", 0.0)
        btc_held    = params.get("btc_held", 0.0)

        # Fetch live signals
        live = fetch_live_signals()

        signals = MarketSignals(
            btc_price_usd     = live.btc_price_usd,
            fear_greed_index  = live.fear_greed_value,
            rsi_14d           = live.rsi_14d,
            rsi_weekly        = live.rsi_weekly,
            avg_buy_price     = avg_price,
            total_invested    = invested,
            portfolio_value   = port_value,
            btc_ath_usd       = live.btc_ath_usd,
            ath_drop_pct      = live.ath_drop_pct,
            price_vs_200wma   = live.price_vs_200wma,
        )

        # Check Scaling Out (Pillar 3)
        scaling = self.engine.check_scaling_out(signals)

        # Check milestones
        milestones = self.engine.check_milestones(invested, port_value, btc_held)

        # Profit analysis
        profit_pct = 0.0
        if invested > 0:
            profit_pct = (port_value - invested) / invested * 100

        return {
            "job_type":        "portfolio_check",
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "version":         "4.0",
            "market": {
                "btc_price_usd":    live.btc_price_usd,
                "rsi_weekly":       live.rsi_weekly,
                "fear_greed_index": live.fear_greed_value,
                "cycle_phase":      live.cycle_phase,
            },
            "portfolio": {
                "avg_buy_price_usd": avg_price,
                "total_invested":    invested,
                "portfolio_value":   port_value,
                "profit_pct":        round(profit_pct, 2),
                "btc_held":          btc_held,
            },
            "scaling_out": {
                "signal":     scaling.get("signal", False),
                "sell_pct":   scaling.get("sell_pct", 0),
                "messages":   scaling.get("messages", []),
            },
            "milestones": milestones,
            "recommendation": (
                "SCALE OUT — take partial profits"
                if scaling.get("signal")
                else "HOLD — conditions not met for profit taking"
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI — Quick test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  ZION SMART DCA v4.0 — ERC-8183 AGENTIC COMMERCE")
    print("=" * 65)

    job_engine = ZionAnalysisJob()

    # 1. List available jobs
    catalog = job_engine.list_jobs()
    print("\n  Available Jobs:")
    for jtype, info in catalog["jobs"].items():
        print(f"    [{jtype}] ${info['price_usd']:.2f} — {info['description'][:60]}...")

    # 2. Create and execute an analyze_market job
    print("\n  Creating 'analyze_market' job...")
    meta = job_engine.create_job("analyze_market", {"budget_usd": 100, "frequency": "weekly"})
    print(f"    Job ID:  {meta.job_id}")
    print(f"    Price:   ${meta.price_usd:.2f} ({meta.price_bnb} BNB)")
    print(f"    Status:  {meta.status}")

    print("\n  Executing job...")
    result = job_engine.execute_job(meta.job_id, "analyze_market", {"budget_usd": 100})
    print(f"    Status:  {result['status']}")
    if result["status"] == "completed":
        decision = result["result"]["decision"]["decision"]
        print(f"    Action:  {decision['action']} | {decision['type']} | {decision['multiplier']}x")
        print(f"    Amount:  ${decision['amount_usd']:.2f}")

    # 3. Create and execute a portfolio_check job
    print("\n  Creating 'portfolio_check' job...")
    meta2 = job_engine.create_job("portfolio_check", {})
    result2 = job_engine.execute_job(meta2.job_id, "portfolio_check", {
        "avg_buy_price_usd": 45000,
        "total_invested": 20000,
        "portfolio_value": 52000,
        "btc_held": 0.5,
    })
    print(f"    Status:         {result2['status']}")
    if result2["status"] == "completed":
        print(f"    Recommendation: {result2['result']['recommendation']}")

    print("\n" + "=" * 65)
