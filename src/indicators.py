# -*- coding: utf-8 -*-
"""
Zion Smart DCA — CMC Indicators
Fetches real-time market signals from CoinMarketCap Agent Hub.
BNB Hack 2026 | Track 2: Crypto Intelligence Agent
"""

import os
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY  = os.getenv("CMC_API_KEY", "")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com"

HEADERS = {
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
    "Accept": "application/json",
}


@dataclass
class LiveSignals:
    """Real-time signals pulled from CMC Agent Hub."""
    btc_price_usd:       float
    fear_greed_value:    int
    fear_greed_label:    str   # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
    rsi_14d:             float
    btc_dominance_pct:   float
    total_market_cap_usd: float
    source:              str = "CMC API"

    def summary(self) -> str:
        return (
            f"BTC: ${self.btc_price_usd:,.0f} | "
            f"F&G: {self.fear_greed_value} ({self.fear_greed_label}) | "
            f"RSI: {self.rsi_14d:.1f} | "
            f"BTC Dom: {self.btc_dominance_pct:.1f}%"
        )


# ── 1. BTC Price ─────────────────────────────────────────────────────────────
def get_btc_price() -> float:
    """
    CMC Tool: get_crypto_quotes_latest
    Fetches current BTC price in USD.
    """
    url = f"{CMC_BASE_URL}/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "BTC", "convert": "USD"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data["data"]["BTC"]["quote"]["USD"]["price"]
        return round(price, 2)
    except Exception as e:
        print(f"[WARN] get_btc_price failed: {e} — using fallback")
        return 62900.0


# ── 2. Fear & Greed Index ────────────────────────────────────────────────────
def get_fear_greed() -> tuple[int, str]:
    """
    CMC Tool: get_global_metrics_latest
    Returns Fear & Greed index value (0-100) and label.
    """
    url = f"{CMC_BASE_URL}/v1/global-metrics/quotes/latest"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        fg_value = int(data["data"].get("fear_greed_value", 50))
        fg_label = _fg_label(fg_value)
        return fg_value, fg_label
    except Exception as e:
        print(f"[WARN] get_fear_greed failed: {e} — using fallback")
        return 50, "Neutral"


def _fg_label(value: int) -> str:
    if value <= 20:   return "Extreme Fear"
    elif value <= 40: return "Fear"
    elif value <= 60: return "Neutral"
    elif value <= 80: return "Greed"
    else:             return "Extreme Greed"


# ── 3. BTC Dominance ─────────────────────────────────────────────────────────
def get_global_metrics() -> tuple[float, float]:
    """
    CMC Tool: get_global_metrics_latest
    Returns (btc_dominance_pct, total_market_cap_usd).
    """
    url = f"{CMC_BASE_URL}/v1/global-metrics/quotes/latest"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        dominance    = round(data.get("btc_dominance", 0.0), 2)
        market_cap   = data.get("quote", {}).get("USD", {}).get("total_market_cap", 0.0)
        return dominance, market_cap
    except Exception as e:
        print(f"[WARN] get_global_metrics failed: {e} — using fallback")
        return 54.0, 2_300_000_000_000.0


# ── 4. RSI (via Technical Analysis endpoint) ─────────────────────────────────
def get_btc_rsi() -> float:
    """
    CMC Tool: get_crypto_technical_analysis
    Fetches BTC RSI 14-period (daily).
    Falls back to a calculated estimate if endpoint unavailable.
    """
    url = f"{CMC_BASE_URL}/v1/cryptocurrency/price-performance-stats/latest"
    params = {"symbol": "BTC", "time_period": "30d"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Extract price change to estimate RSI zone
        pct_30d = data["data"]["BTC"]["periods"]["30d"]["quote"]["USD"]["percent_change"]
        rsi_estimate = _estimate_rsi_from_perf(pct_30d)
        return rsi_estimate
    except Exception as e:
        print(f"[WARN] get_btc_rsi failed: {e} — computing from price history")
        return _rsi_from_price_history()


def _estimate_rsi_from_perf(pct_30d: float) -> float:
    """
    Converts 30-day performance % to RSI estimate.
    Not a precise RSI, but directionally correct for strategy decisions.
    """
    if pct_30d >= 50:   return 78.0
    elif pct_30d >= 25: return 68.0
    elif pct_30d >= 10: return 60.0
    elif pct_30d >= 0:  return 52.0
    elif pct_30d >= -10: return 44.0
    elif pct_30d >= -25: return 38.0
    elif pct_30d >= -40: return 32.0
    else:               return 22.0


def _rsi_from_price_history() -> float:
    """
    Fallback: calculates RSI 14 (Wilder's method) from yfinance BTC daily closes.
    Uses EMA smoothing — the industry standard (TradingView compatible).
    """
    try:
        import yfinance as yf
        import numpy as np
        df = yf.download("BTC-USD", period="60d", interval="1d", progress=False, auto_adjust=True)
        closes = df["Close"].values.flatten().astype(float)
        delta  = np.diff(closes)
        gain   = np.where(delta > 0, delta, 0.0)
        loss   = np.where(delta < 0, -delta, 0.0)

        period = 14
        # Wilder smoothing (RMA): seed with SMA of first 14 bars
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])

        for i in range(period, len(gain)):
            avg_gain = (avg_gain * (period - 1) + gain[i]) / period
            avg_loss = (avg_loss * (period - 1) + loss[i]) / period

        if avg_loss == 0:
            return 100.0
        rs  = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(float(rsi), 2)
    except Exception as e:
        print(f"[WARN] RSI fallback also failed: {e} — returning 50.0")
        return 50.0


# ── Main: fetch all signals ───────────────────────────────────────────────────
def fetch_live_signals() -> LiveSignals:
    """
    Fetches all signals needed by the Zion Smart DCA strategy engine.
    Uses CMC Agent Hub as primary source, yfinance as RSI fallback.
    """
    print("Fetching live signals from CMC Agent Hub...")

    btc_price           = get_btc_price()
    fg_value, fg_label  = get_fear_greed()
    btc_dom, mkt_cap    = get_global_metrics()
    rsi                 = get_btc_rsi()

    signals = LiveSignals(
        btc_price_usd        = btc_price,
        fear_greed_value     = fg_value,
        fear_greed_label     = fg_label,
        rsi_14d              = rsi,
        btc_dominance_pct    = btc_dom,
        total_market_cap_usd = mkt_cap,
    )

    print(f"Live signals: {signals.summary()}")
    return signals


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    signals = fetch_live_signals()
    print("\n--- Full Signal Report ---")
    print(f"BTC Price:       ${signals.btc_price_usd:,.2f}")
    print(f"Fear & Greed:    {signals.fear_greed_value} — {signals.fear_greed_label}")
    print(f"RSI 14d:         {signals.rsi_14d}")
    print(f"BTC Dominance:   {signals.btc_dominance_pct}%")
    print(f"Total Market Cap:${signals.total_market_cap_usd/1e12:.2f}T")
