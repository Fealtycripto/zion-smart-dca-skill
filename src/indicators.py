# -*- coding: utf-8 -*-
"""
Zion Smart DCA v4.0 — CMC Indicators + Derived Signals
Fetches real-time market signals from CoinMarketCap Agent Hub.
BNB Hack 2026 | Track 2: Crypto Intelligence Agent

New in v4.0:
  - RSI Weekly (for Scaling Out dual confirmation)
  - ATH and distance from ATH
  - 200-Week Moving Average
  - Cycle phase estimation
"""

import os
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
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
    """Real-time signals pulled from CMC Agent Hub + derived indicators."""
    btc_price_usd:         float
    fear_greed_value:      int
    fear_greed_label:      str    # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
    rsi_14d:               float  # RSI daily 14-period
    rsi_weekly:            float  # RSI weekly 14-period (new v4.0)
    btc_dominance_pct:     float
    total_market_cap_usd:  float
    btc_ath_usd:           float  # All-Time High (new v4.0)
    ath_drop_pct:          float  # % drop from ATH (new v4.0)
    price_vs_200wma:       float  # price / 200WMA ratio (new v4.0)
    cycle_phase:           str    # estimated cycle phase (new v4.0)
    months_since_halving:  int    # months since last halving (new v4.0)
    source:                str = "CMC API + yfinance"

    def summary(self) -> str:
        return (
            f"BTC: ${self.btc_price_usd:,.0f} | "
            f"F&G: {self.fear_greed_value} ({self.fear_greed_label}) | "
            f"RSI-D: {self.rsi_14d:.1f} | RSI-W: {self.rsi_weekly:.1f} | "
            f"ATH drop: {self.ath_drop_pct:.1f}% | "
            f"vs 200WMA: {self.price_vs_200wma:.2f}x | "
            f"Cycle: {self.cycle_phase}"
        )


# ── 1. BTC Price ─────────────────────────────────────────────────────────────
def get_btc_price() -> float:
    """CMC Tool: get_crypto_quotes_latest — Fetches current BTC price in USD."""
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
        return _btc_price_fallback()


def _btc_price_fallback() -> float:
    """Fallback: get BTC price from yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker("BTC-USD")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        pass
    return 63000.0


# ── 2. Fear & Greed Index ────────────────────────────────────────────────────
def get_fear_greed() -> tuple:
    """CMC Tool: get_global_metrics_latest — Returns F&G value (0-100) and label."""
    url = f"{CMC_BASE_URL}/v1/global-metrics/quotes/latest"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        fg_value = int(data["data"].get("fear_greed_value", 50))
        fg_label = _fg_label_v4(fg_value)
        return fg_value, fg_label
    except Exception as e:
        print(f"[WARN] get_fear_greed CMC failed: {e} — trying Alternative.me")
        return _fg_alternative_me()


def _fg_alternative_me() -> tuple:
    """Fallback: Fear & Greed from Alternative.me (free, no API key)."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1&format=json", timeout=10)
        r.raise_for_status()
        data = r.json()
        value = int(data["data"][0]["value"])
        return value, _fg_label_v4(value)
    except Exception as e:
        print(f"[WARN] Alternative.me F&G also failed: {e} — returning 50/Neutral")
        return 50, "Neutral"


def _fg_label_v4(value: int) -> str:
    """F&G labels with v4.0 thresholds."""
    if value <= 24:   return "Extreme Fear"
    elif value <= 44: return "Fear"
    elif value <= 55: return "Neutral"
    elif value <= 74: return "Greed"
    else:             return "Extreme Greed"


# ── 3. Global Metrics ────────────────────────────────────────────────────────
def get_global_metrics() -> tuple:
    """CMC Tool: get_global_metrics_latest — Returns (btc_dominance, total_market_cap)."""
    url = f"{CMC_BASE_URL}/v1/global-metrics/quotes/latest"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        dominance  = round(data.get("btc_dominance", 0.0), 2)
        market_cap = data.get("quote", {}).get("USD", {}).get("total_market_cap", 0.0)
        return dominance, market_cap
    except Exception as e:
        print(f"[WARN] get_global_metrics failed: {e} — using fallback")
        return 54.0, 2_300_000_000_000.0


# ── 4. RSI Daily (14-period, Wilder method) ──────────────────────────────────
def get_btc_rsi_daily() -> float:
    """Calculates RSI 14-period daily from BTC price history (Wilder EMA method)."""
    return _compute_rsi(period_str="60d", interval="1d")


# ── 5. RSI Weekly (14-period, Wilder method) — NEW v4.0 ─────────────────────
def get_btc_rsi_weekly() -> float:
    """Calculates RSI 14-period weekly from BTC price history (Wilder EMA method)."""
    return _compute_rsi(period_str="2y", interval="1wk")


def _compute_rsi(period_str: str = "60d", interval: str = "1d") -> float:
    """
    Computes RSI using Wilder's Exponential Moving Average method.
    Compatible with TradingView, Bloomberg, MetaTrader.
    """
    try:
        import yfinance as yf
        import numpy as np

        df = yf.download("BTC-USD", period=period_str, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return 50.0

        closes = df["Close"].values.flatten().astype(float)
        if len(closes) < 16:
            return 50.0

        delta = np.diff(closes)
        gain  = np.where(delta > 0, delta, 0.0)
        loss  = np.where(delta < 0, -delta, 0.0)

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
        print(f"[WARN] RSI computation failed ({interval}): {e} — returning 50.0")
        return 50.0


# ── 6. ATH and Distance from ATH — NEW v4.0 ─────────────────────────────────
def get_btc_ath() -> tuple:
    """
    Fetches BTC All-Time High and calculates current distance.
    Returns (ath_price, ath_drop_pct).
    """
    try:
        import yfinance as yf
        df = yf.download("BTC-USD", period="max", interval="1wk",
                         progress=False, auto_adjust=True)
        if df.empty:
            return 108000.0, 0.0

        ath = float(df["High"].values.flatten().max())
        current = float(df["Close"].values.flatten()[-1])
        drop_pct = ((current - ath) / ath) * 100  # negative value
        return round(ath, 2), round(drop_pct, 2)
    except Exception as e:
        print(f"[WARN] ATH calculation failed: {e} — using fallback")
        return 108000.0, -40.0


# ── 7. 200-Week Moving Average — NEW v4.0 ────────────────────────────────────
def get_200wma_ratio() -> float:
    """
    Calculates BTC price / 200-Week Moving Average ratio.
    > 1.0 = price above 200WMA (healthy)
    < 1.0 = price below 200WMA (maximum historical accumulation zone)
    """
    try:
        import yfinance as yf
        import numpy as np

        df = yf.download("BTC-USD", period="5y", interval="1wk",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 200:
            return 1.0

        closes = df["Close"].values.flatten().astype(float)
        wma_200 = np.mean(closes[-200:])
        current = closes[-1]
        ratio = current / wma_200 if wma_200 > 0 else 1.0
        return round(ratio, 4)
    except Exception as e:
        print(f"[WARN] 200WMA calculation failed: {e} — returning 1.0")
        return 1.0


# ── 8. Cycle Phase Estimation — NEW v4.0 ─────────────────────────────────────
def estimate_cycle_phase() -> tuple:
    """
    Estimates current Bitcoin cycle phase based on months since last halving.
    Last halving: April 19, 2024.

    Returns (phase_name, months_since_halving).
    """
    halving_date = datetime(2024, 4, 19)
    now = datetime.utcnow()
    months = (now.year - halving_date.year) * 12 + (now.month - halving_date.month)

    if months < 0:
        phase = "ACCUMULATION_PRE_HALVING"
    elif months <= 6:
        phase = "INITIAL_IMPULSE"
    elif months <= 18:
        phase = "BULL_RUN"
    elif months <= 24:
        phase = "DISTRIBUTION"
    else:
        phase = "BEAR_MARKET"

    return phase, months


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: Fetch All Signals
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_live_signals() -> LiveSignals:
    """
    Fetches ALL signals needed by the Zion Smart DCA v4.0 strategy engine.
    Sources: CMC Agent Hub (primary) + yfinance (RSI, ATH, 200WMA)
    """
    print("Fetching live signals from CMC Agent Hub + yfinance...")

    btc_price           = get_btc_price()
    fg_value, fg_label  = get_fear_greed()
    btc_dom, mkt_cap    = get_global_metrics()
    rsi_daily           = get_btc_rsi_daily()
    rsi_weekly          = get_btc_rsi_weekly()
    ath, ath_drop       = get_btc_ath()
    wma_ratio           = get_200wma_ratio()
    cycle_phase, months = estimate_cycle_phase()

    signals = LiveSignals(
        btc_price_usd        = btc_price,
        fear_greed_value     = fg_value,
        fear_greed_label     = fg_label,
        rsi_14d              = rsi_daily,
        rsi_weekly           = rsi_weekly,
        btc_dominance_pct    = btc_dom,
        total_market_cap_usd = mkt_cap,
        btc_ath_usd          = ath,
        ath_drop_pct         = ath_drop,
        price_vs_200wma      = wma_ratio,
        cycle_phase          = cycle_phase,
        months_since_halving = months,
    )

    print(f"Live signals: {signals.summary()}")
    return signals


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    signals = fetch_live_signals()
    print("\n--- Full Signal Report (v4.0) ---")
    print(f"BTC Price:       ${signals.btc_price_usd:,.2f}")
    print(f"Fear & Greed:    {signals.fear_greed_value} — {signals.fear_greed_label}")
    print(f"RSI Daily:       {signals.rsi_14d}")
    print(f"RSI Weekly:      {signals.rsi_weekly}")
    print(f"BTC Dominance:   {signals.btc_dominance_pct}%")
    print(f"Total Mkt Cap:   ${signals.total_market_cap_usd/1e12:.2f}T")
    print(f"BTC ATH:         ${signals.btc_ath_usd:,.0f}")
    print(f"ATH Drop:        {signals.ath_drop_pct:.1f}%")
    print(f"Price vs 200WMA: {signals.price_vs_200wma:.4f}x")
    print(f"Cycle Phase:     {signals.cycle_phase} ({signals.months_since_halving}m since halving)")
