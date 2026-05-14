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

st.set_page_config(page_title="Market Research", page_icon="📊", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("📊 Market Research")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "News Log", "Weekly Review", "Market Regime",
     "Earnings Log", "Trade Journal", "Settings"],
)

# ── Data cache ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner="Fetching market data…")
def get_data():
    close   = fetch_price_data(period="3mo")
    summary = compute_summary(close)
    regime  = get_regime(close)
    return close, summary, regime


def _pct_style(val):
    if val is None:
        return ""
    return "color:#26a69a" if float(val) >= 0 else "color:#ef5350"


# ════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.title("📈 Macro Watchlist Dashboard")
    close, summary, regime = get_data()

    c1, c2 = st.columns(2)
    c1.metric("Today's Regime",  regime["daily_regime"])
    c1.caption(regime["daily_note"])
    c2.metric("Weekly Regime",   regime["weekly_regime"])
    c2.caption(regime["weekly_note"])
    st.divider()

    cat_icons = {"Equity":"📊","Rates":"📉","Commodity":"🛢️",
                 "Volatility":"⚡","Currency":"💵","Crypto":"₿"}
    for cat, tickers in WATCHLIST.items():
        sub = summary[summary["Ticker"].isin(tickers)]
        if sub.empty:
            continue
        st.subheader(f"{cat_icons.get(cat,'')} {cat}")
        cols = ["Ticker","Price","Day %","Week %","Month %","Trend"]
        tbl  = sub[cols].set_index("Ticker")
        styled = (
            tbl.style
            .map(_pct_style, subset=["Day %","Week %","Month %"])
            .format({"Price":"{:.4f}","Day %":"{:+.2f}%",
                     "Week %":"{:+.2f}%","Month %":"{:+.2f}%"}, na_rep="—")
        )
        st.dataframe(styled, use_container_width=True)

    st.divider()
    st.subheader("📉 Price Chart")
    chosen = st.selectbox("Select ticker", summary["Ticker"].tolist())
    if chosen and chosen in close.columns:
        s = close[chosen].dropna().tail(60)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s.index, y=s, mode="lines", name=chosen,
                                 line=dict(width=2, color="#26a69a")))
        fig.add_trace(go.Scatter(x=s.index, y=s.rolling(20).mean(), mode="lines",
                                 name="MA20", line=dict(dash="dash", color="orange")))
        fig.add_trace(go.Scatter(x=s.index, y=s.rolling(60).mean(), mode="lines",
                                 name="MA60", line=dict(dash="dot", color="#ef5350")))
        fig.update_layout(height=360, margin=dict(l=0,r=0,t=20,b=0),
                          plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                          font_color="white",
                          xaxis=dict(gridcolor="#2a2a2a"),
                          yaxis=dict(gridcolor="#2a2a2a"))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear(); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  NEWS LOG
# ════════════════════════════════════════════════════════════════════════════
elif page == "News Log":
    st.title("📰 News Log")
    tab_add, tab_hist = st.tabs(["➕ Add News", "📜 History"])

    with tab_add:
        col_form, col_guide = st.columns([3, 2])

        with col_form:
            with st.form("news_form", clear_on_submit=True):
                n_date       = st.date_input("Date", value=date.today())
                n_cat        = st.selectbox("Category", CATEGORIES)
                n_importance = st.select_slider("Importance", IMPORTANCE[::-1], value="Medium")
                n_title      = st.text_input("News Title *")
                n_source     = st.text_input("Source (Bloomberg / Reuters / FT…)")
                n_summary    = st.text_area("Content Summary")
                n_interp     = st.text_area("My Interpretation")
                n_assets     = st.text_input("Affected Assets (comma-separated)")
                n_reaction   = st.text_area("Actual Market Reaction")
                submitted    = st.form_submit_button("💾 Save News")

            if submitted and n_title:
                save_news({
                    "date": str(n_date), "category": n_cat,
                    "importance": n_importance, "title": n_title,
                    "source": n_source, "content_summary": n_summary,
                    "interpretation": n_interp,
                    "affected_assets": n_assets, "market_reaction": n_reaction,
                })
                st.success("Saved!")

        with col_guide:
            st.markdown("### 📋 Impact Guide")
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
            st.info("No news entries yet.")
        else:
            col1, col2, col3 = st.columns(3)
            cat_f = col1.multiselect("Category", CATEGORIES, default=CATEGORIES)
            imp_f = col2.multiselect("Importance", IMPORTANCE, default=IMPORTANCE)
            search = col3.text_input("Search title")

            mask = df["category"].isin(cat_f) & df["importance"].isin(imp_f)
            if search:
                mask &= df["title"].str.contains(search, case=False, na=False)
            df = df[mask]

            for _, row in df.iterrows():
                imp   = row.get("importance", "Low")
                badge = IMPORTANCE_BADGE.get(imp, imp)
                color = IMPORTANCE_COLOR.get(imp, "#26a69a")
                label = f"{badge} | [{row.get('date','')}] [{row.get('category','')}] {row.get('title','')}"
                with st.expander(label):
                    st.markdown(f"**來源：** {row.get('source','—')}")
                    st.markdown(f"**摘要：** {row.get('content_summary','—')}")
                    st.markdown(f"**我的解讀：** {row.get('interpretation','—')}")
                    st.markdown(f"**影響資產：** {row.get('affected_assets','—')}")
                    st.markdown(f"**市場反應：** {row.get('market_reaction','—')}")
                    if st.button("🗑️ Delete", key=f"del_news_{row.get('id')}"):
                        delete_news(int(row["id"])); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  WEEKLY REVIEW
# ════════════════════════════════════════════════════════════════════════════
elif page == "Weekly Review":
    st.title("📓 Weekly Review")
    tab_new, tab_hist = st.tabs(["➕ New Entry", "📜 History"])

    with tab_new:
        _, _, regime = get_data()
        auto_regime = regime["weekly_regime"]

        with st.form("journal_form", clear_on_submit=True):
            week_start = st.date_input("Week Start", value=date.today())
            headlines  = st.text_area("本週重點新聞")
            main_theme = st.text_area("本週市場主線")

            st.markdown("**各市場解讀**")
            c1, c2 = st.columns(2)
            equity     = c1.text_area("Equity 股票市場")
            rates      = c2.text_area("Rates 利率市場")
            commodity  = c1.text_area("Commodity 商品市場")
            currency   = c2.text_area("Currency 美元")
            volatility = c1.text_area("Volatility 波動率")
            crypto     = c2.text_area("Crypto 加密貨幣")

            st.markdown("**本週結論**")
            c3, c4 = st.columns(2)
            strongest  = c3.text_input("本週最強資產")
            weakest    = c4.text_input("本週最弱資產")
            regime_in  = st.text_input("Market Regime", value=auto_regime)
            next_watch = st.text_area("下週觀察重點")
            summary    = st.text_area("一句話總結")
            submitted  = st.form_submit_button("💾 Save")

        if submitted:
            save_journal({
                "week_start": str(week_start), "headlines": headlines,
                "main_theme": main_theme, "equity": equity, "rates": rates,
                "commodity": commodity, "currency": currency,
                "volatility": volatility, "crypto": crypto,
                "strongest": strongest, "weakest": weakest,
                "regime": regime_in, "next_watch": next_watch, "summary": summary,
            })
            st.success("Saved!")

    with tab_hist:
        df = load_journals()
        if df.empty:
            st.info("No entries yet.")
        else:
            for _, row in df.iterrows():
                with st.expander(f"📅 {row['week_start']}  —  {row.get('regime','')}"):
                    st.markdown(f"**市場主線：** {row.get('main_theme','')}")
                    st.markdown(f"**重點新聞：** {row.get('headlines','')}")
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Equity：** {row.get('equity','')}")
                    c2.markdown(f"**Rates：** {row.get('rates','')}")
                    c3.markdown(f"**Commodity：** {row.get('commodity','')}")
                    c4, c5, c6 = st.columns(3)
                    c4.markdown(f"**Currency：** {row.get('currency','')}")
                    c5.markdown(f"**Volatility：** {row.get('volatility','')}")
                    c6.markdown(f"**Crypto：** {row.get('crypto','')}")
                    st.markdown(f"**最強：** {row.get('strongest','')}　**最弱：** {row.get('weakest','')}")
                    st.markdown(f"**下週觀察：** {row.get('next_watch','')}")
                    st.info(f"💬 {row.get('summary','')}")


# ════════════════════════════════════════════════════════════════════════════
#  MARKET REGIME
# ════════════════════════════════════════════════════════════════════════════
elif page == "Market Regime":
    st.title("🧭 Market Regime")
    close, summary, regime = get_data()

    # ── Regime banner ─────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    c1.metric("Today", regime["daily_regime"])
    c1.caption(regime["daily_note"])
    c2.metric("This Week", regime["weekly_regime"])
    c2.caption(regime["weekly_note"])
    st.divider()

    # ── Signal table ──────────────────────────────────────────────────────
    st.subheader("📊 Signal Breakdown")
    signal_rows = []
    for cat, tickers in WATCHLIST.items():
        for tkr in tickers:
            row = summary[summary["Ticker"] == tkr]
            if row.empty:
                continue
            r = row.iloc[0]
            d = r.get("Day %"); w = r.get("Week %")
            signal_rows.append({
                "Category": cat,
                "Ticker":   tkr,
                "Day %":    d,
                "Week %":   w,
                "Trend":    r.get("Trend","—"),
                "Signal":   "🟢 Bullish" if (w or 0) > 1 else ("🔴 Bearish" if (w or 0) < -1 else "⚪ Neutral"),
            })
    sig_df = pd.DataFrame(signal_rows)
    st.dataframe(
        sig_df.style
        .map(_pct_style, subset=["Day %","Week %"])
        .format({"Day %":"{:+.2f}%","Week %":"{:+.2f}%"}, na_rep="—"),
        use_container_width=True,
    )
    st.divider()

    # ── Regime rule guide ────────────────────────────────────────────────
    st.subheader("📋 Regime Rules")
    regimes = [
        ("🟢 Risk-On",            "SPY/QQQ/IWM 上漲，VIX 下跌，DXY 下跌",
         "風險資產全面走強，市場情緒樂觀，適合偏多操作。"),
        ("🔴 Risk-Off",           "SPY/QQQ/IWM 下跌，VIX 上升，DXY 上升",
         "避險情緒主導，資金流向美元/黃金，減少風險敞口。"),
        ("🟠 Inflation Trade",    "GLD/USO/DBC 上漲，TNX 上升",
         "通膨交易佔主導，能源/商品/抗通膨資產表現強。"),
        ("🔵 Lower Yield Risk-On","TNX 下跌，TLT 上漲，QQQ/IWM 上漲",
         "長端利率下降推升估值，科技/成長股為主線。"),
        ("⚪ Unclear",            "多空訊號混雜",
         "方向不明確，降低倉位，等待更清晰的訊號。"),
    ]
    for label, condition, action in regimes:
        with st.expander(label):
            st.markdown(f"**條件：** {condition}")
            st.markdown(f"**操作建議：** {action}")
    st.divider()

    # ── News impact quick-ref ────────────────────────────────────────────
    st.subheader("📰 News → Market Impact 速查")
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
#  EARNINGS LOG
# ════════════════════════════════════════════════════════════════════════════
elif page == "Earnings Log":
    st.title("📋 Earnings Log")
    tab_add, tab_hist = st.tabs(["➕ Add", "📜 History"])

    with tab_add:
        with st.form("earnings_form", clear_on_submit=True):
            e_ticker  = st.text_input("Ticker").upper()
            e_date    = st.date_input("Report Date", value=date.today())
            e_rev     = st.radio("Revenue Growth?", ["Yes","No"], horizontal=True)
            e_eps     = st.radio("EPS Beat?",       ["Yes","No"], horizontal=True)
            e_guide   = st.selectbox("Guidance", GUIDANCE_OPTIONS)
            e_react   = st.number_input("Price Reaction (%)", step=0.1, format="%.2f")
            e_interp  = st.text_area("Interpretation")
            sub       = st.form_submit_button("💾 Save")
        if sub and e_ticker:
            save_earnings({"ticker":e_ticker,"report_date":str(e_date),
                           "revenue_growth":e_rev,"eps_beat":e_eps,
                           "guidance":e_guide,"price_reaction":e_react,
                           "interpretation":e_interp})
            st.success("Saved!")

    with tab_hist:
        df = load_earnings()
        if df.empty:
            st.info("No entries.")
        else:
            st.dataframe(df.drop(columns=["created_at"],errors="ignore"),
                         use_container_width=True)
            del_id = st.number_input("Delete by ID", min_value=1, step=1)
            if st.button("🗑️ Delete"):
                delete_earnings(int(del_id)); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  TRADE JOURNAL
# ════════════════════════════════════════════════════════════════════════════
elif page == "Trade Journal":
    st.title("📒 Trade Journal")
    tab_add, tab_hist = st.tabs(["➕ Add", "📜 History"])

    with tab_add:
        with st.form("trade_form", clear_on_submit=True):
            t_date   = st.date_input("Date", value=date.today())
            t_ticker = st.text_input("Ticker").upper()
            t_dir    = st.selectbox("Direction", DIRECTIONS)
            t_reason = st.text_area("Entry Rationale")
            t_regime = st.text_input("Macro Regime")
            t_risk   = st.text_area("Risk")
            t_stop   = st.text_input("Stop Loss")
            t_result = st.text_area("Result")
            t_review = st.text_area("Review")
            sub      = st.form_submit_button("💾 Save")
        if sub and t_ticker:
            save_trade({"date":str(t_date),"ticker":t_ticker,"direction":t_dir,
                        "reason":t_reason,"regime":t_regime,"risk":t_risk,
                        "stop_loss":t_stop,"result":t_result,"review":t_review})
            st.success("Saved!")

    with tab_hist:
        df = load_trades()
        if df.empty:
            st.info("No entries.")
        else:
            filt = st.multiselect("Direction", DIRECTIONS, default=DIRECTIONS)
            df   = df[df["direction"].isin(filt)]
            for _, row in df.iterrows():
                with st.expander(f"[{row['date']}] {row['ticker']} — {row['direction']}"):
                    st.markdown(f"**Regime：** {row.get('regime','')}")
                    st.markdown(f"**Rationale：** {row.get('reason','')}")
                    st.markdown(f"**Risk：** {row.get('risk','')}　**Stop：** {row.get('stop_loss','')}")
                    st.markdown(f"**Result：** {row.get('result','')}")
                    st.markdown(f"**Review：** {row.get('review','')}")
                    if st.button("🗑️ Delete", key=f"del_trade_{row.get('id')}"):
                        delete_trade(int(row["id"])); st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    st.title("⚙️ Settings")
    if st.button("🔄 Clear Data Cache"):
        st.cache_data.clear(); st.success("Cache cleared.")
    st.markdown("---")
    st.markdown("**Personal Market Research System** — v2.0  \nStreamlit · yfinance · Supabase")
