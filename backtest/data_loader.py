# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Historical Data Loader
Downloads BTC OHLCV data via yfinance for backtesting.
Fear & Greed: real historical data from Alternative.me API (free, 365-day history).
Fallback: proxy calculated from RSI + 30d return + MA200 distance.
BNB Hack 2026 | Track 2: Crypto Intelligence Agent
"""

import os
import requests
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

FG_CSV = Path(__file__).parent / "fear_greed_historical.csv"

DATA_DIR  = Path(__file__).parent
CSV_PATH  = DATA_DIR / "btc_2021_2026.csv"


def download_btc_data(
    start: str = "2021-01-01",
    end:   str  = None,
    force: bool = False
) -> pd.DataFrame:
    """
    Downloads BTC daily OHLCV from Yahoo Finance.
    Caches to CSV to avoid repeated downloads.
    
    Returns DataFrame with columns: Date, Open, High, Low, Close, Volume
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    # Use cache if exists and not forcing
    if CSV_PATH.exists() and not force:
        print(f"Loading cached data from {CSV_PATH.name}...")
        df = pd.read_csv(CSV_PATH, index_col="Date", parse_dates=True)
        print(f"Loaded {len(df)} days ({df.index[0].date()} to {df.index[-1].date()})")
        return df

    print(f"Downloading BTC data {start} -> {end}...")
    raw = yf.download(
        "BTC-USD",
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=True,
    )

    # Flatten MultiIndex columns if present
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index.name = "Date"
    df = df.dropna()

    df.to_csv(CSV_PATH)
    print(f"Saved {len(df)} days to {CSV_PATH.name}")
    return df


def fetch_real_fear_greed(limit: int = 365) -> pd.DataFrame:
    """
    Fetches real Fear & Greed Index from Alternative.me (free API).
    Returns DataFrame with Date index and FearGreed column.
    Source: https://alternative.me/crypto/fear-and-greed-index/
    """
    try:
        url = f"https://api.alternative.me/fng/?limit={limit}&format=json"
        r   = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        records = [
            {
                "Date":      datetime.fromtimestamp(int(d["timestamp"])).strftime("%Y-%m-%d"),
                "FearGreed": int(d["value"]),
                "FG_Label":  d["value_classification"],
                "Source":    "alternative.me (real)",
            }
            for d in data
        ]
        fg_df = pd.DataFrame(records)
        fg_df["Date"] = pd.to_datetime(fg_df["Date"])
        fg_df = fg_df.set_index("Date").sort_index()
        fg_df.to_csv(FG_CSV)
        print(f"Real F&G loaded: {len(fg_df)} days ({fg_df.index[0].date()} to {fg_df.index[-1].date()})")
        return fg_df
    except Exception as e:
        print(f"Alternative.me API unavailable ({e}), using proxy F&G.")
        return pd.DataFrame()


def _compute_fg_proxy(df: pd.DataFrame) -> pd.Series:
    """Proxy F&G from RSI + 30d return + MA200 distance (fallback only)."""
    import numpy as np
    close    = df["Close"]
    ret_30d  = close.pct_change(30) * 100
    ma200    = close.rolling(200).mean()
    dist_ma  = ((close - ma200) / ma200 * 100)
    rsi      = df["RSI"] if "RSI" in df.columns else pd.Series(50, index=df.index)
    fg_raw   = (
        rsi * 0.40 +
        (ret_30d.clip(-50, 50) + 50) * 0.35 +
        (dist_ma.clip(-40, 40) + 40) * 0.25 * (100 / 80)
    )
    return fg_raw.clip(0, 100).round(0)


def add_weekly_fear_greed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds RSI and Fear & Greed to daily BTC DataFrame.

    Priority:
      1. Real historical F&G from Alternative.me (free API, 365-day history)
      2. Cached CSV from previous fetch
      3. Proxy calculated from price indicators (fallback)
    """
    import numpy as np

    df = df.copy()
    close = df["Close"]

    # RSI 14 (Wilder EMA method — same as TradingView)
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs       = avg_gain / avg_loss
    df["RSI"] = (100 - 100 / (1 + rs)).round(2)

    # --- Try real F&G first ---
    fg_real = pd.DataFrame()

    # 1. Load from cache if fresh enough
    if FG_CSV.exists():
        cached = pd.read_csv(FG_CSV, index_col="Date", parse_dates=True)
        if not cached.empty and cached.index[-1].date() >= (datetime.today().date() - timedelta(days=2)):
            fg_real = cached
            print(f"Using cached real F&G ({len(fg_real)} days)")

    # 2. Fetch fresh from API
    if fg_real.empty:
        fg_real = fetch_real_fear_greed(limit=500)

    # 3. Merge real F&G where available, proxy elsewhere
    if not fg_real.empty:
        df["FearGreed"] = pd.NA
        df["FG_Source"] = "proxy"

        # Align real data
        common = df.index.intersection(fg_real.index)
        df.loc[common, "FearGreed"] = fg_real.loc[common, "FearGreed"].values
        df.loc[common, "FG_Source"] = "real"

        # Fill gaps with proxy
        proxy = _compute_fg_proxy(df)
        missing = df["FearGreed"].isna()
        df.loc[missing, "FearGreed"] = proxy[missing]
        df.loc[missing, "FG_Source"] = "proxy"

        real_count  = (df["FG_Source"] == "real").sum()
        proxy_count = (df["FG_Source"] == "proxy").sum()
        print(f"F&G coverage: {real_count} real days + {proxy_count} proxy days")
    else:
        # Full proxy fallback
        df["FearGreed"] = _compute_fg_proxy(df)
        df["FG_Source"]  = "proxy"
        print("F&G: using full proxy (Alternative.me unavailable)")

    df["FearGreed"] = df["FearGreed"].round(0).astype("Int64")
    return df


if __name__ == "__main__":
    df = download_btc_data(start="2021-01-01", force=False)
    df = add_weekly_fear_greed(df)
    print("\nSample data (last 5 rows):")
    print(df[["Close", "RSI", "FearGreed", "dist_ma200"]].tail())
    print(f"\nTotal rows: {len(df)}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
