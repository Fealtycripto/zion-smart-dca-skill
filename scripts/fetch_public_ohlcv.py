"""Download closed public candles without API keys or account access."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import ccxt


def download(exchange_name: str, symbol: str, days: int = 7) -> dict:
    if exchange_name not in ("kraken", "coinbase") or symbol not in ("BTC/USD", "ETH/USD"):
        raise ValueError("Use the documented public exchange/symbol combinations")
    if not 1 <= days <= 7:
        raise ValueError("This evaluation adapter supports 1–7 days")
    exchange = getattr(ccxt, exchange_name)({"enableRateLimit": True, "timeout": 15000})
    now = exchange.milliseconds()
    rows = exchange.fetch_ohlcv(symbol, "1h", since=now-days*86400000, limit=days*24)
    closed = [r for r in rows if r[0]+3600000 <= now]
    if not closed or len({r[0] for r in closed}) != len(closed):
        raise ValueError("Empty or duplicate candle timestamps")
    if not all(all(math.isfinite(float(v)) for v in r[:6]) and r[4] > 0 for r in closed):
        raise ValueError("Invalid candle values")
    gaps = sum(closed[i][0]-closed[i-1][0] != 3600000 for i in range(1,len(closed)))
    return {"source": exchange_name, "symbol": symbol, "timeframe": "1h",
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(), "closed_candles_only": True,
            "gaps": gaps, "ohlcv": closed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exchange", choices=["kraken", "coinbase"], required=True)
    parser.add_argument("--symbol", choices=["BTC/USD", "ETH/USD"], required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = download(args.exchange, args.symbol, args.days)
    # Do not overwrite an existing dataset by default.
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    print(f"Saved {len(result['ohlcv'])} closed candles; gaps={result['gaps']}")


if __name__ == "__main__":
    main()
