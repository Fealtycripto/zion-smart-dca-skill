# -*- coding: utf-8 -*-
"""
Zion Smart DCA — Historical Data Loader
Downloads BTC OHLCV data via yfinance for backtesting.
BNB Hack 2026 | Track 2: Crypto Intelligence Agent
"""

import os
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

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


def add_weekly_fear_greed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Approximates weekly Fear & Greed based on BTC price performance.
    Used for backtesting since historical F&G API requires paid plan.
    
    Method: derives F&G proxy from:
    - 30-day rolling return (trend signal)
    - 14-day RSI (momentum signal)  
    - Distance from 200-day MA (macro signal)
    """
    import numpy as np

    df = df.copy()
    close = df["Close"]

    # RSI 14 (Wilder method)
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs       = avg_gain / avg_loss
    df["RSI"] = (100 - 100 / (1 + rs)).round(2)

    # 30d return
    df["ret_30d"] = close.pct_change(30) * 100

    # Distance from 200MA
    df["ma200"]      = close.rolling(200).mean()
    df["dist_ma200"] = ((close - df["ma200"]) / df["ma200"] * 100).round(2)

    # F&G proxy (0-100) — calibrated to match historical F&G index behavior
    fg_raw = (
        df["RSI"] * 0.40 +                           # RSI component (40%)
        (df["ret_30d"].clip(-50, 50) + 50) * 0.35 + # 30d trend component (35%)
        (df["dist_ma200"].clip(-40, 40) + 40) * 0.25 * (100/80)  # MA200 component (25%)
    )
    df["FearGreed"] = fg_raw.clip(0, 100).round(0).astype("Int64")

    return df


if __name__ == "__main__":
    df = download_btc_data(start="2021-01-01", force=False)
    df = add_weekly_fear_greed(df)
    print("\nSample data (last 5 rows):")
    print(df[["Close", "RSI", "FearGreed", "dist_ma200"]].tail())
    print(f"\nTotal rows: {len(df)}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
