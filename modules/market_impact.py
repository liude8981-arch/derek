"""
Simple rules-based market impact guide per news category.
"""

IMPACTS = {
    "Fed": {
        "icon": "🏦",
        "scenarios": [
            {
                "label": "偏鷹 Hawkish",
                "up":   ["^TNX ↑", "DX-Y.NYB ↑"],
                "down": ["QQQ ↓", "TLT ↓", "IWM ↓", "BTC ↓"],
                "note": "升息預期上升 → 利率走高、美元走強、成長股/債券承壓",
            },
            {
                "label": "偏鴿 Dovish",
                "up":   ["QQQ ↑", "TLT ↑", "IWM ↑", "BTC ↑"],
                "down": ["^TNX ↓", "DX-Y.NYB ↓"],
                "note": "降息預期上升 → 利率走低、成長股/債券受惠、美元走弱",
            },
        ],
    },
    "Inflation": {
        "icon": "📈",
        "scenarios": [
            {
                "label": "CPI/PPI 高於預期",
                "up":   ["^TNX ↑", "DX-Y.NYB ↑", "GLD ↑", "USO ↑"],
                "down": ["QQQ ↓", "TLT ↓", "IWM ↓"],
                "note": "通膨超預期 → 升息預期增、利率上升、成長股承壓",
            },
            {
                "label": "CPI/PPI 低於預期",
                "up":   ["QQQ ↑", "TLT ↑", "IWM ↑", "BTC ↑"],
                "down": ["^TNX ↓", "DX-Y.NYB ↓"],
                "note": "通膨降溫 → 降息預期增、成長股/債券受惠",
            },
        ],
    },
    "Yield": {
        "icon": "📉",
        "scenarios": [
            {
                "label": "長端利率上升",
                "up":   ["DX-Y.NYB ↑", "^TNX ↑"],
                "down": ["TLT ↓", "QQQ ↓", "IWM ↓"],
                "note": "長端利率走高 → 壓制估值，科技/小型股承壓",
            },
            {
                "label": "長端利率下降",
                "up":   ["TLT ↑", "QQQ ↑", "IWM ↑"],
                "down": ["^TNX ↓", "DX-Y.NYB ↓"],
                "note": "長端利率下降 → 估值提升，科技/小型股受惠",
            },
        ],
    },
    "Earnings": {
        "icon": "💼",
        "scenarios": [
            {
                "label": "財報優於預期 / Guidance 上修",
                "up":   ["SPY ↑", "QQQ ↑", "個股 ↑"],
                "down": ["^VIX ↓"],
                "note": "財報亮眼 → 市場風險偏好上升、個股強勢",
            },
            {
                "label": "財報低於預期 / Guidance 下修",
                "up":   ["^VIX ↑"],
                "down": ["SPY ↓", "QQQ ↓", "個股 ↓"],
                "note": "Guidance 下修 → 股票偏空，若為大型股可能拖累指數",
            },
        ],
    },
    "Oil": {
        "icon": "🛢️",
        "scenarios": [
            {
                "label": "油價上漲",
                "up":   ["USO ↑", "DBC ↑", "能源股 ↑"],
                "down": ["消費/航空股 ↓"],
                "note": "油價走升 → 通膨壓力增、能源股受惠、消費/運輸承壓",
            },
            {
                "label": "油價下跌",
                "up":   ["消費股 ↑", "航空股 ↑"],
                "down": ["USO ↓", "DBC ↓", "能源股 ↓"],
                "note": "油價下跌 → 可能代表需求放緩，注意景氣衰退訊號",
            },
        ],
    },
    "Geopolitical": {
        "icon": "🌍",
        "scenarios": [
            {
                "label": "地緣政治升溫",
                "up":   ["^VIX ↑", "GLD ↑", "USO ↑", "DX-Y.NYB ↑"],
                "down": ["SPY ↓", "QQQ ↓", "IWM ↓"],
                "note": "地緣衝突升溫 → 避險需求大增、VIX/黃金走強、股市承壓",
            },
            {
                "label": "地緣政治降溫",
                "up":   ["SPY ↑", "QQQ ↑", "IWM ↑"],
                "down": ["^VIX ↓", "GLD ↓"],
                "note": "緊張局勢緩解 → 風險偏好回升、股市反彈、黃金回落",
            },
        ],
    },
    "Other": {
        "icon": "📰",
        "scenarios": [
            {
                "label": "依個別情況判斷",
                "up":   [],
                "down": [],
                "note": "請依新聞內容自行評估影響資產。",
            },
        ],
    },
}

IMPORTANCE_BADGE = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}
IMPORTANCE_COLOR = {"High": "#ef5350", "Medium": "#ffa726", "Low": "#26a69a"}
