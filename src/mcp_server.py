"""Local MCP analysis over caller-provided signals. No keys, APIs, wallets or orders."""
import math
from typing import Annotated, Literal
from pydantic import Field
from mcp.server import MCPServer
from strategy import DCAConfig, MarketSignals, ZionSmartDCA

server = MCPServer("Zion Smart DCA — local analysis")


@server.tool()
def strategy_info() -> dict:
    """Describe the implemented Python strategy and its execution boundary."""
    return {"strategy_version": "4.0", "budget_split": {"dca": 0.7, "reserve": 0.3},
            "source": "caller_provided", "executes_orders": False,
            "note": "The v4.2 browser simulator is a separate experiment."}


@server.tool()
def evaluate_signals(
    budget: Annotated[float, Field(gt=0)],
    btc_price: Annotated[float, Field(gt=0)],
    fear_greed: Annotated[int, Field(ge=0, le=100)],
    rsi_daily: Annotated[float, Field(ge=0, le=100)],
    frequency: Literal["daily", "weekly", "biweekly", "monthly"] = "weekly",
) -> dict:
    """Evaluate explicitly supplied signals using the existing v4.0 engine; never execute orders."""
    if not all(math.isfinite(x) for x in (budget, btc_price, rsi_daily)):
        raise ValueError("Inputs must be finite")
    signals = MarketSignals(btc_price_usd=btc_price, fear_greed_index=fear_greed,
                            rsi_14d=rsi_daily)
    result = ZionSmartDCA(DCAConfig(base_amount_usd=budget, frequency=frequency)).evaluate(signals).to_dict()
    return {"strategy_version": "4.0", "source": "caller_provided",
            "executes_orders": False,
            "assumptions": {"rsi_weekly": signals.rsi_weekly,
                            "btc_portfolio_pct": signals.btc_portfolio_pct,
                            "reserve_usd": signals.reserve_usd,
                            "price_vs_200wma": signals.price_vs_200wma,
                            "mvrv_z_score": signals.mvrv_z_score,
                            "note": "Other MarketSignals fields retain engine defaults; no portfolio data was observed."},
            "analysis": result}


if __name__ == "__main__":
    # Local stdio transport; no listener or exposure on a public interface.
    server.run()
