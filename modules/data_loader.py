import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

WATCHLIST = {
    "Equity":      ["SPY", "QQQ", "DIA", "IWM"],
    "Rates":       ["^TNX", "TLT"],
    "Commodity":   ["GLD", "USO", "DBC"],
    "Volatility":  ["^VIX"],
    "Currency":    ["DX-Y.NYB"],
    "Crypto":      ["BTC-USD"],
}

ALL_TICKERS = [t for tickers in WATCHLIST.values() for t in tickers]

TICKER_LABELS = {
    "^TNX":    "US 10Y Yield",
    "DX-Y.NYB": "DXY",
}


def fetch_price_data(period="3mo") -> pd.DataFrame:
    """Download OHLCV for all watchlist tickers, return close prices."""
    raw = yf.download(
        ALL_TICKERS,
        period=period,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]]
    close = close.ffill().dropna(how="all")
    return close


def compute_summary(close: pd.DataFrame) -> pd.DataFrame:
    """Build one-row-per-ticker summary table."""
    rows = []
    today = close.index[-1]

    for ticker in ALL_TICKERS:
        if ticker not in close.columns:
            continue

        s = close[ticker].dropna()
        if len(s) < 2:
            continue

        price = s.iloc[-1]

        def pct(n_days):
            past = s[s.index <= today - timedelta(days=n_days)]
            if past.empty:
                return np.nan
            return (price - past.iloc[-1]) / past.iloc[-1] * 100

        d1  = (price - s.iloc[-2]) / s.iloc[-2] * 100
        w1  = pct(7)
        m1  = pct(30)
        ma20 = s.tail(20).mean() if len(s) >= 20 else np.nan
        ma60 = s.tail(60).mean() if len(s) >= 60 else np.nan

        if not np.isnan(ma20) and not np.isnan(ma60):
            if price > ma20 > ma60:
                trend = "▲ Uptrend"
            elif price < ma20 < ma60:
                trend = "▼ Downtrend"
            else:
                trend = "— Sideways"
        else:
            trend = "—"

        category = next(
            (cat for cat, tl in WATCHLIST.items() if ticker in tl), "Other"
        )

        rows.append({
            "Ticker":    ticker,
            "Name":      TICKER_LABELS.get(ticker, ticker),
            "Category":  category,
            "Price":     round(price, 4),
            "Day %":     round(d1, 2),
            "Week %":    round(w1, 2) if not np.isnan(w1) else None,
            "Month %":   round(m1, 2) if not np.isnan(m1) else None,
            "MA20":      round(ma20, 4) if not np.isnan(ma20) else None,
            "MA60":      round(ma60, 4) if not np.isnan(ma60) else None,
            "Trend":     trend,
        })

    return pd.DataFrame(rows)
