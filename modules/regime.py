import pandas as pd
import numpy as np
from datetime import timedelta


def _get_change(close: pd.DataFrame, ticker: str, days: int) -> float | None:
    if ticker not in close.columns:
        return None
    s = close[ticker].dropna()
    if len(s) < 2:
        return None
    today = s.index[-1]
    past = s[s.index <= today - timedelta(days=days)]
    if past.empty:
        return None
    return (s.iloc[-1] - past.iloc[-1]) / past.iloc[-1] * 100


def _sign(v) -> int:
    if v is None or np.isnan(v):
        return 0
    return 1 if v > 0 else (-1 if v < 0 else 0)


def _classify(close: pd.DataFrame, days: int) -> tuple[str, str]:
    spy  = _sign(_get_change(close, "SPY",      days))
    qqq  = _sign(_get_change(close, "QQQ",      days))
    iwm  = _sign(_get_change(close, "IWM",      days))
    vix  = _sign(_get_change(close, "^VIX",     days))
    dxy  = _sign(_get_change(close, "DX-Y.NYB", days))
    tlt  = _sign(_get_change(close, "TLT",      days))
    tnx  = _sign(_get_change(close, "^TNX",     days))
    gld  = _sign(_get_change(close, "GLD",      days))
    uso  = _sign(_get_change(close, "USO",      days))
    dbc  = _sign(_get_change(close, "DBC",      days))

    equity_score = spy + qqq + iwm          # −3..+3

    if equity_score >= 2 and vix < 0 and dxy <= 0:
        regime = "🟢 Risk-On"
        note   = "股市強勢、波動率下滑、美元偏弱，市場情緒樂觀。"

    elif equity_score <= -2 and vix > 0 and dxy >= 0:
        regime = "🔴 Risk-Off"
        note   = "股市下跌、波動率攀升、美元走強，市場避險情緒主導。"

    elif gld >= 1 and uso >= 1 and dbc >= 1 and tnx > 0:
        regime = "🟠 Inflation Trade"
        note   = "商品全面上漲、長端利率上升，通膨交易佔主導。"

    elif tnx < 0 and tlt > 0 and qqq >= 1 and iwm >= 1:
        regime = "🔵 Lower Yield Risk-On"
        note   = "長端利率下降帶動科技/小型股走強，成長股受惠。"

    else:
        regime = "⚪ Unclear"
        note   = "多空訊號混雜，市場方向尚不明確，需觀察後續發展。"

    return regime, note


def get_regime(close: pd.DataFrame) -> dict:
    daily_regime, daily_note   = _classify(close, 1)
    weekly_regime, weekly_note = _classify(close, 7)
    return {
        "daily_regime":  daily_regime,
        "daily_note":    daily_note,
        "weekly_regime": weekly_regime,
        "weekly_note":   weekly_note,
    }
