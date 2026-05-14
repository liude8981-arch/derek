import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from modules.data_loader import fetch_price_data, compute_summary, WATCHLIST
from modules.regime import get_regime
from modules.journal import save_journal, load_journals
from modules.news_log import save_news, load_news, delete_news, CATEGORIES, IMPORTANCE
from modules.earnings_log import save_earnings, load_earnings, delete_earnings, GUIDANCE_OPTIONS
from modules.trade_log import save_trade, load_trades, delete_trade, DIRECTIONS
from modules.market_impact import IMPACTS, IMPORTANCE_BADGE, IMPORTANCE_COLOR

st.set_page_config(page_title="市場研究系統", page_icon="📊", layout="wide")

# ── 側邊欄 ───────────────────────────────────────────────────────────────────
st.sidebar.title("📊 市場研究系統")
page = st.sidebar.radio(
    "功能選單",
    ["總覽儀表板", "新聞紀錄", "週總結", "市場環境", "財報追蹤", "交易日誌", "設定"],
)

# ── 資料快取 ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner="正在抓取市場資料…")
def get_data():
    close   = fetch_price_data(period="3mo")
    summary = compute_summary(close)
    regime  = get_regime(close)
    return close, summary, regime


def _pct_style(val):
    if val is None:
        return ""
    return "color:#26a69a" if float(val) >= 0 else "color:#ef5350"


CAT_ZH = {
    "Equity": "股票",
    "Rates": "利率",
    "Commodity": "商品",
    "Volatility": "波動率",
    "Currency": "貨幣",
    "Crypto": "加密貨幣",
}

# ════════════════════════════════════════════════════════════════════════════
#  總覽儀表板
# ════════════════════════════════════════════════════════════════════════════
if page == "總覽儀表板":
    st.title("📈 總體市場監控儀表板")
    close, summary, regime = get_data()

    c1, c2 = st.columns(2)
    c1.metric("今日市場環境", regime["daily_regime"])
    c1.caption(regime["daily_note"])
    c2.metric("本週市場環境", regime["weekly_regime"])
    c2.caption(regime["weekly_note"])
    st.divider()

    cat_icons = {"Equity":"📊","Rates":"📉","Commodity":"🛢️",
                 "Volatility":"⚡","Currency":"💵","Crypto":"₿"}
    for cat, tickers in WATCHLIST.items():
        sub = summary[summary["Ticker"].isin(tickers)]
        if sub.empty:
            continue
        cat_label = CAT_ZH.get(cat, cat)
        st.subheader(f"{cat_icons.get(cat,'')} {cat_label}")
        cols = ["Ticker","Price","Day %","Week %","Month %","Trend"]
        col_zh = {"Ticker":"代號","Price":"現價","Day %":"日漲跌",
                  "Week %":"週漲跌","Month %":"月漲跌","Trend":"趨勢"}
        tbl = sub[cols].set_index("Ticker").rename(columns=col_zh)
        styled = (
            tbl.style
            .map(_pct_style, subset=["日漲跌","週漲跌","月漲跌"])
            .format({"現價":"{:.4f}","日漲跌":"{:+.2f}%",
                     "週漲跌":"{:+.2f}%","月漲跌":"{:+.2f}%"}, na_rep="—")
        )
        st.dataframe(styled, use_container_width=True)

    st.divider()
    st.subheader("📉 價格走勢圖")
    chosen = st.selectbox("選擇標的", summary["Ticker"].tolist())
    if chosen and chosen in close.columns:
        s = close[chosen].dropna().tail(60)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s.index, y=s, mode="lines", name=chosen,
                                 line=dict(width=2, color="#26a69a")))
        fig.add_trace(go.Scatter(x=s.index, y=s.rolling(20).mean(), mode="lines",
                                 name="20日均線", line=dict(dash="dash", color="orange")))
        fig.add_trace(go.Scatter(x=s.index, y=s.rolling(60).mean(), mode="lines",
                                 name="60日均線", line=dict(dash="dot", color="#ef5350")))
        fig.update_layout(height=360, margin=dict(l=0,r=0,t=20,b=0),
                          plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                          font_color="white",
                          xaxis=dict(gridcolor="#2a2a2a"),
                          yaxis=dict(gridcolor="#2a2a2a"))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🔄 重新整理資料"):
        st.cache_data.clear(); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  新聞紀錄
# ════════════════════════════════════════════════════════════════════════════
elif page == "新聞紀錄":
    st.title("📰 新聞紀錄")
    tab_add, tab_hist = st.tabs(["➕ 新增新聞", "📜 歷史紀錄"])

    with tab_add:
        col_form, col_guide = st.columns([3, 2])

        with col_form:
            with st.form("news_form", clear_on_submit=True):
                n_date       = st.date_input("日期", value=date.today())
                n_cat        = st.selectbox("新聞分類", CATEGORIES)
                n_importance = st.select_slider("重要程度", IMPORTANCE[::-1], value="Medium")
                n_title      = st.text_input("新聞標題 *")
                n_source     = st.text_input("新聞來源（Bloomberg / Reuters / FT…）")
                n_summary    = st.text_area("新聞內容摘要")
                n_interp     = st.text_area("我的解讀")
                n_assets     = st.text_input("可能影響資產（逗號分隔）")
                n_reaction   = st.text_area("實際市場反應")
                submitted    = st.form_submit_button("💾 儲存新聞")

            if submitted and n_title:
                save_news({
                    "date": str(n_date), "category": n_cat,
                    "importance": n_importance, "title": n_title,
                    "source": n_source, "content_summary": n_summary,
                    "interpretation": n_interp,
                    "affected_assets": n_assets, "market_reaction": n_reaction,
                })
                st.success("已儲存！")

        with col_guide:
            st.markdown("### 📋 市場影響速查")
            impact = IMPACTS.get(n_cat if 'n_cat' in dir() else "Fed", IMPACTS["Other"])
            st.markdown(f"**{impact['icon']} {n_cat if 'n_cat' in dir() else 'Fed'}**")
            for s in impact["scenarios"]:
                with st.expander(s["label"]):
                    if s["up"]:
                        st.markdown("**↑ 可能上漲：** " + "　".join(s["up"]))
                    if s["down"]:
                        st.markdown("**↓ 可能下跌：** " + "　".join(s["down"]))
                    st.caption(s["note"])

    with tab_hist:
        df = load_news()
        if df.empty:
            st.info("尚無新聞紀錄。")
        else:
            col1, col2, col3 = st.columns(3)
            cat_f  = col1.multiselect("分類篩選", CATEGORIES, default=CATEGORIES)
            imp_f  = col2.multiselect("重要程度篩選", IMPORTANCE, default=IMPORTANCE)
            search = col3.text_input("搜尋標題")

            mask = df["category"].isin(cat_f) & df["importance"].isin(imp_f)
            if search:
                mask &= df["title"].str.contains(search, case=False, na=False)
            df = df[mask]

            for _, row in df.iterrows():
                imp   = row.get("importance", "Low")
                badge = IMPORTANCE_BADGE.get(imp, imp)
                label = f"{badge} | [{row.get('date','')}] [{row.get('category','')}] {row.get('title','')}"
                with st.expander(label):
                    st.markdown(f"**來源：** {row.get('source','—')}")
                    st.markdown(f"**摘要：** {row.get('content_summary','—')}")
                    st.markdown(f"**我的解讀：** {row.get('interpretation','—')}")
                    st.markdown(f"**影響資產：** {row.get('affected_assets','—')}")
                    st.markdown(f"**市場反應：** {row.get('market_reaction','—')}")
                    if st.button("🗑️ 刪除", key=f"del_news_{row.get('id')}"):
                        delete_news(int(row["id"])); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  週總結
# ════════════════════════════════════════════════════════════════════════════
elif page == "週總結":
    st.title("📓 週總結")
    tab_new, tab_hist = st.tabs(["➕ 新增週總結", "📜 歷史紀錄"])

    with tab_new:
        _, _, regime = get_data()
        auto_regime = regime["weekly_regime"]

        with st.form("journal_form", clear_on_submit=True):
            week_start = st.date_input("週開始日期", value=date.today())
            headlines  = st.text_area("本週重點新聞")
            main_theme = st.text_area("本週市場主線")

            st.markdown("**各市場解讀**")
            c1, c2 = st.columns(2)
            equity     = c1.text_area("股票市場")
            rates      = c2.text_area("利率市場")
            commodity  = c1.text_area("商品市場")
            currency   = c2.text_area("美元走勢")
            volatility = c1.text_area("波動率")
            crypto     = c2.text_area("加密貨幣")

            st.markdown("**本週結論**")
            c3, c4 = st.columns(2)
            strongest  = c3.text_input("本週最強資產")
            weakest    = c4.text_input("本週最弱資產")
            regime_in  = st.text_input("市場環境判斷", value=auto_regime)
            next_watch = st.text_area("下週觀察重點")
            summary    = st.text_area("一句話總結")
            submitted  = st.form_submit_button("💾 儲存")

        if submitted:
            save_journal({
                "week_start": str(week_start), "headlines": headlines,
                "main_theme": main_theme, "equity": equity, "rates": rates,
                "commodity": commodity, "currency": currency,
                "volatility": volatility, "crypto": crypto,
                "strongest": strongest, "weakest": weakest,
                "regime": regime_in, "next_watch": next_watch, "summary": summary,
            })
            st.success("已儲存！")

    with tab_hist:
        df = load_journals()
        if df.empty:
            st.info("尚無週總結紀錄。")
        else:
            for _, row in df.iterrows():
                with st.expander(f"📅 {row['week_start']}  —  {row.get('regime','')}"):
                    st.markdown(f"**市場主線：** {row.get('main_theme','')}")
                    st.markdown(f"**重點新聞：** {row.get('headlines','')}")
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**股票市場：** {row.get('equity','')}")
                    c2.markdown(f"**利率市場：** {row.get('rates','')}")
                    c3.markdown(f"**商品市場：** {row.get('commodity','')}")
                    c4, c5, c6 = st.columns(3)
                    c4.markdown(f"**美元走勢：** {row.get('currency','')}")
                    c5.markdown(f"**波動率：** {row.get('volatility','')}")
                    c6.markdown(f"**加密貨幣：** {row.get('crypto','')}")
                    st.markdown(f"**最強：** {row.get('strongest','')}　**最弱：** {row.get('weakest','')}")
                    st.markdown(f"**下週觀察：** {row.get('next_watch','')}")
                    st.info(f"💬 {row.get('summary','')}")


# ════════════════════════════════════════════════════════════════════════════
#  市場環境
# ════════════════════════════════════════════════════════════════════════════
elif page == "市場環境":
    st.title("🧭 市場環境判斷")
    close, summary, regime = get_data()

    c1, c2 = st.columns(2)
    c1.metric("今日環境", regime["daily_regime"])
    c1.caption(regime["daily_note"])
    c2.metric("本週環境", regime["weekly_regime"])
    c2.caption(regime["weekly_note"])
    st.divider()

    # ── 訊號明細表 ────────────────────────────────────────────────────────
    st.subheader("📊 訊號明細")
    signal_rows = []
    for cat, tickers in WATCHLIST.items():
        for tkr in tickers:
            row = summary[summary["Ticker"] == tkr]
            if row.empty:
                continue
            r = row.iloc[0]
            d = r.get("Day %"); w = r.get("Week %")
            signal_rows.append({
                "類別":   CAT_ZH.get(cat, cat),
                "代號":   tkr,
                "日漲跌": d,
                "週漲跌": w,
                "趨勢":   r.get("Trend","—"),
                "訊號":   "🟢 偏多" if (w or 0) > 1 else ("🔴 偏空" if (w or 0) < -1 else "⚪ 中性"),
            })
    sig_df = pd.DataFrame(signal_rows)
    st.dataframe(
        sig_df.style
        .map(_pct_style, subset=["日漲跌","週漲跌"])
        .format({"日漲跌":"{:+.2f}%","週漲跌":"{:+.2f}%"}, na_rep="—"),
        use_container_width=True,
    )
    st.divider()

    # ── 環境判斷規則 ──────────────────────────────────────────────────────
    st.subheader("📋 環境判斷規則")
    regimes = [
        ("🟢 風險偏好（Risk-On）",
         "SPY/QQQ/IWM 上漲，VIX 下跌，DXY 下跌",
         "風險資產全面走強，市場情緒樂觀，適合偏多操作。"),
        ("🔴 風險規避（Risk-Off）",
         "SPY/QQQ/IWM 下跌，VIX 上升，DXY 上升",
         "避險情緒主導，資金流向美元/黃金，應減少風險敞口。"),
        ("🟠 通膨交易（Inflation Trade）",
         "GLD/USO/DBC 上漲，TNX 上升",
         "通膨交易佔主導，能源/商品/抗通膨資產表現強勢。"),
        ("🔵 降息驅動多頭（Lower Yield Risk-On）",
         "TNX 下跌，TLT 上漲，QQQ/IWM 上漲",
         "長端利率下降推升估值，科技/成長股為主線。"),
        ("⚪ 方向不明（Unclear）",
         "多空訊號混雜",
         "方向不明確，建議降低倉位，等待更清晰的市場訊號。"),
    ]
    for label, condition, action in regimes:
        with st.expander(label):
            st.markdown(f"**觸發條件：** {condition}")
            st.markdown(f"**操作建議：** {action}")
    st.divider()

    # ── 新聞類型 → 市場影響速查 ───────────────────────────────────────────
    st.subheader("📰 新聞類型 → 市場影響速查")
    for cat, data in IMPACTS.items():
        if cat == "Other":
            continue
        with st.expander(f"{data['icon']} {cat}"):
            for s in data["scenarios"]:
                cols = st.columns([2, 3, 3])
                cols[0].markdown(f"**{s['label']}**")
                if s["up"]:
                    cols[1].markdown("↑ " + "  ".join(s["up"]))
                if s["down"]:
                    cols[2].markdown("↓ " + "  ".join(s["down"]))
                st.caption(s["note"])


# ════════════════════════════════════════════════════════════════════════════
#  財報追蹤
# ════════════════════════════════════════════════════════════════════════════
elif page == "財報追蹤":
    st.title("📋 財報追蹤")
    tab_add, tab_hist = st.tabs(["➕ 新增財報", "📜 歷史紀錄"])

    with tab_add:
        with st.form("earnings_form", clear_on_submit=True):
            e_ticker = st.text_input("股票代號").upper()
            e_date   = st.date_input("財報日期", value=date.today())
            e_rev    = st.radio("營收是否成長？", ["是","否"], horizontal=True)
            e_eps    = st.radio("EPS 是否超預期？", ["是","否"], horizontal=True)
            e_guide  = st.selectbox("Guidance 展望", GUIDANCE_OPTIONS)
            e_react  = st.number_input("財報後股價反應（%）", step=0.1, format="%.2f")
            e_interp = st.text_area("我的解讀")
            sub      = st.form_submit_button("💾 儲存")
        if sub and e_ticker:
            save_earnings({"ticker":e_ticker,"report_date":str(e_date),
                           "revenue_growth":e_rev,"eps_beat":e_eps,
                           "guidance":e_guide,"price_reaction":e_react,
                           "interpretation":e_interp})
            st.success("已儲存！")

    with tab_hist:
        df = load_earnings()
        if df.empty:
            st.info("尚無財報紀錄。")
        else:
            st.dataframe(df.drop(columns=["created_at"],errors="ignore"),
                         use_container_width=True)
            del_id = st.number_input("輸入 ID 刪除", min_value=1, step=1)
            if st.button("🗑️ 刪除"):
                delete_earnings(int(del_id)); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  交易日誌
# ════════════════════════════════════════════════════════════════════════════
elif page == "交易日誌":
    st.title("📒 交易日誌")
    tab_add, tab_hist = st.tabs(["➕ 新增交易", "📜 歷史紀錄"])

    with tab_add:
        with st.form("trade_form", clear_on_submit=True):
            t_date   = st.date_input("日期", value=date.today())
            t_ticker = st.text_input("標的代號").upper()
            t_dir    = st.selectbox("交易方向", DIRECTIONS)
            t_reason = st.text_area("進場理由")
            t_regime = st.text_input("當時市場環境")
            t_risk   = st.text_area("風險評估")
            t_stop   = st.text_input("停損設定")
            t_result = st.text_area("交易結果")
            t_review = st.text_area("事後檢討")
            sub      = st.form_submit_button("💾 儲存")
        if sub and t_ticker:
            save_trade({"date":str(t_date),"ticker":t_ticker,"direction":t_dir,
                        "reason":t_reason,"regime":t_regime,"risk":t_risk,
                        "stop_loss":t_stop,"result":t_result,"review":t_review})
            st.success("已儲存！")

    with tab_hist:
        df = load_trades()
        if df.empty:
            st.info("尚無交易紀錄。")
        else:
            filt = st.multiselect("方向篩選", DIRECTIONS, default=DIRECTIONS)
            df   = df[df["direction"].isin(filt)]
            for _, row in df.iterrows():
                with st.expander(f"[{row['date']}] {row['ticker']} — {row['direction']}"):
                    st.markdown(f"**市場環境：** {row.get('regime','')}")
                    st.markdown(f"**進場理由：** {row.get('reason','')}")
                    st.markdown(f"**風險評估：** {row.get('risk','')}　**停損：** {row.get('stop_loss','')}")
                    st.markdown(f"**交易結果：** {row.get('result','')}")
                    st.markdown(f"**事後檢討：** {row.get('review','')}")
                    if st.button("🗑️ 刪除", key=f"del_trade_{row.get('id')}"):
                        delete_trade(int(row["id"])); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  設定
# ════════════════════════════════════════════════════════════════════════════
elif page == "設定":
    st.title("⚙️ 設定")
    if st.button("🔄 清除資料快取"):
        st.cache_data.clear(); st.success("快取已清除。")
    st.markdown("---")
    st.markdown("**個人市場研究系統** — v2.0  \nStreamlit · yfinance · Supabase")
