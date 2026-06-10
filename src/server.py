# -*- coding: utf-8 -*-
"""
Zion Smart DCA v4.0 — ERC-8183 Job Server
Exposes analysis capabilities as agentic commerce endpoints.

BNB Hack 2026 | Track 2: Crypto Intelligence Agent
Special Prize: Best Use of BNB AI Agent SDK ($2,000)

Endpoints:
  GET  /health         — Server health check
  GET  /agent-card     — ERC-8004 agent identity card
  GET  /jobs           — List available job types (ERC-8183 catalog)
  POST /jobs/analyze   — Execute market analysis job
  POST /jobs/backtest  — Execute backtest job
  POST /jobs/portfolio — Execute portfolio check job
  GET  /jobs/{job_id}  — Query job status

Usage:
  pip install 'fastapi[standard]'
  uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError as e:
    raise ImportError(
        "FastAPI is required for the job server. Install with:\n"
        "  pip install 'fastapi[standard]'\n"
        f"Original error: {e}"
    )

from commerce import ZionAnalysisJob, JOB_PRICING
from agent import AGENT_CARD


# ═══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Zion Smart DCA v4.0 — Strategy Skill Server",
    description=(
        "ERC-8183 compatible job server for intelligent BTC accumulation analysis. "
        "Provides agent-to-agent commerce endpoints for market analysis, backtesting, "
        "and portfolio management powered by the Zion Smart DCA v4.0 strategy engine."
    ),
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name":  "Rony Costa (@Fealtycripto)",
        "url":   "https://github.com/Fealtycripto/zion-smart-dca-skill",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS — allow agent-to-agent communication from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared job engine instance
job_engine = ZionAnalysisJob()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """Request body for market analysis job."""
    budget_usd: float = Field(default=100.0, ge=1.0,
                              description="DCA base amount in USD. Any amount works: $10, $50, $500.")
    frequency: str = Field(default="weekly",
                          description="DCA frequency: daily, weekly, biweekly, monthly")
    btc_pct: float = Field(default=0.54, ge=0.0, le=1.0,
                           description="Current BTC allocation as decimal (0.54 = 54%)")
    avg_buy_price_usd: float = Field(default=0.0, ge=0.0,
                                     description="Average buy price for Rule 5 (never sell below PM)")


class BacktestRequest(BaseModel):
    """Request body for backtest job."""
    start_date: str = Field(default="2021-01-01",
                           description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(default=None,
                                    description="End date in YYYY-MM-DD format (default: today)")
    budget_usd: float = Field(default=100.0, ge=1.0,
                              description="DCA base amount in USD")
    frequency: str = Field(default="weekly",
                          description="DCA frequency: daily, weekly, biweekly, monthly")


class PortfolioRequest(BaseModel):
    """Request body for portfolio check job."""
    avg_buy_price_usd: float = Field(default=0.0, ge=0.0,
                                     description="Average purchase price in USD")
    total_invested: float = Field(default=0.0, ge=0.0,
                                  description="Total USD invested")
    portfolio_value: float = Field(default=0.0, ge=0.0,
                                   description="Current portfolio value in USD")
    btc_held: float = Field(default=0.0, ge=0.0,
                            description="Amount of BTC held")


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
def health():
    """Server health check."""
    return {
        "status":  "ok",
        "version": "4.0",
        "engine":  "ZionSmartDCA",
        "erc":     ["ERC-8004", "ERC-8183"],
    }


@app.get("/agent-card", tags=["Identity"])
def agent_card():
    """
    Returns the ERC-8004 agent identity card.
    Used by other agents to discover this agent's capabilities.
    """
    return AGENT_CARD


@app.get("/jobs", tags=["ERC-8183 Commerce"])
def list_jobs():
    """
    List all available job types (ERC-8183 service catalog).
    Other agents use this endpoint to discover purchasable services.
    """
    return job_engine.list_jobs()


@app.post("/jobs/analyze", tags=["ERC-8183 Commerce"])
def analyze_market(request: AnalyzeRequest):
    """
    Execute a market analysis job.

    Fetches live BTC signals (price, Fear & Greed, RSI, cycle phase)
    and returns a full DCA strategy recommendation with reasoning.

    ERC-8183 pricing: $0.50 / 0.001 BNB per analysis
    """
    meta = job_engine.create_job("analyze_market", request.model_dump())
    result = job_engine.execute_job(
        meta.job_id, "analyze_market", request.model_dump()
    )

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Job failed"))

    return result


@app.post("/jobs/backtest", tags=["ERC-8183 Commerce"])
def backtest_period(request: BacktestRequest):
    """
    Run a backtest for a custom historical period.

    Downloads BTC price history and simulates Zion Smart DCA vs Standard DCA.
    Returns performance comparison with total return, BTC accumulated, and more.

    ERC-8183 pricing: $2.00 / 0.004 BNB per backtest
    """
    params = request.model_dump()
    meta = job_engine.create_job("backtest_period", params)
    result = job_engine.execute_job(meta.job_id, "backtest_period", params)

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Job failed"))

    return result


@app.post("/jobs/portfolio", tags=["ERC-8183 Commerce"])
def portfolio_check(request: PortfolioRequest):
    """
    Check if current conditions warrant Scaling Out (profit taking).

    Analyzes RSI weekly, cycle phase, and profit levels to determine
    if partial profit-taking is recommended. Enforces Rule 5: never sell below PM.

    ERC-8183 pricing: $0.25 / 0.0005 BNB per check
    """
    params = request.model_dump()
    meta = job_engine.create_job("portfolio_check", params)
    result = job_engine.execute_job(meta.job_id, "portfolio_check", params)

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Job failed"))

    return result


@app.get("/jobs/{job_id}", tags=["ERC-8183 Commerce"])
def get_job_status(job_id: str):
    """
    Query the status of a previously created job.
    Returns full job metadata including results if completed.
    """
    status = job_engine.get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return status


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — for development
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("\n  Starting Zion Smart DCA v4.0 — ERC-8183 Job Server")
    print("  Docs: http://localhost:8000/docs")
    print("  Agent Card: http://localhost:8000/agent-card\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
