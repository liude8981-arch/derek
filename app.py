import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from modules.data_loader import fetch_price_data, compute_summary, WATCHLIST
from modules.regime import get_regime
from modules.journal import save_journal, load_journals
from modules.news_log import save_news, load_news, delete_news, CATEGORIES
from modules.earnings_log import save_earnings, load_earnings, delete_earnings, GUIDANCE_OPTIONS
from modules.trade_log import save_trade, load_trades, delete_trade, DIRECTIONS

st.set_page_config(
    page_title="Market Research System",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar navigation ──────────────────────────────────────────────────────
st.sidebar.title("📊 Market Research")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Macro Journal", "News Log", "Earnings Log", "Trade Journal", "Settings"],
)

# ── Global data cache (15 min TTL) ──────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner="Fetching market data…")
def get_data():
    close   = fetch_price_data(period="3mo")
    summary = compute_summary(close)
    regime  = get_regime(close)
    return close, summary, regime


# ── Colour helpers ───────────────────────────────────────────────────────────
def pct_color(val):
    if val is None:
        return ""
    return "color: #26a69a" if val >= 0 else "color: #ef5350"


def style_pct(val):
    return pct_color(val)


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.title("📈 Macro Watchlist Dashboard")

    close, summary, regime = get_data()

    # ── Market Regime banner ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Today's Regime",  regime["daily_regime"])
        st.caption(regime["daily_note"])
    with col2:
        st.metric("Weekly Regime",   regime["weekly_regime"])
        st.caption(regime["weekly_note"])

    st.divider()

    # ── Watchlist table per category ─────────────────────────────────────────
    for cat, tickers in WATCHLIST.items():
        cat_df = summary[summary["Ticker"].isin(tickers)].copy()
        if cat_df.empty:
            continue

        st.subheader(f"{'📊' if cat=='Equity' else '📉' if cat=='Rates' else '🛢️' if cat=='Commodity' else '⚡' if cat=='Volatility' else '💵' if cat=='Currency' else '₿'} {cat}")

        display_cols = ["Ticker", "Price", "Day %", "Week %", "Month %", "MA20", "MA60", "Trend"]
        tbl = cat_df[display_cols].set_index("Ticker")

        styled = tbl.style.map(style_pct, subset=["Day %", "Week %", "Month %"]).format(
            {
                "Price":   "{:.4f}",
                "Day %":   "{:+.2f}%",
                "Week %":  "{:+.2f}%",
                "Month %": "{:+.2f}%",
                "MA20":    "{:.4f}",
                "MA60":    "{:.4f}",
            },
            na_rep="—",
        )
        st.dataframe(styled, use_container_width=True)

    st.divider()

    # ── Mini price chart ─────────────────────────────────────────────────────
    st.subheader("📉 Price Chart")
    all_tickers = summary["Ticker"].tolist()
    chosen = st.selectbox("Select ticker", all_tickers)
    if chosen and chosen in close.columns:
        s = close[chosen].dropna().tail(60)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=chosen, line=dict(width=2)))
        fig.add_trace(go.Scatter(
            x=s.index, y=s.rolling(20).mean(), mode="lines",
            name="MA20", line=dict(dash="dash", color="orange"), opacity=0.8,
        ))
        fig.add_trace(go.Scatter(
            x=s.index, y=s.rolling(60).mean(), mode="lines",
            name="MA60", line=dict(dash="dot", color="red"), opacity=0.6,
        ))
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0),
                          plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                          font_color="white", xaxis=dict(gridcolor="#2a2a2a"),
                          yaxis=dict(gridcolor="#2a2a2a"))
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: MACRO JOURNAL
# ════════════════════════════════════════════════════════════════════════════
elif page == "Macro Journal":
    st.title("📓 Weekly Macro Journal")

    tab_new, tab_history = st.tabs(["➕ New Entry", "📜 History"])

    with tab_new:
        with st.form("journal_form", clear_on_submit=True):
            week_start   = st.date_input("Week Start Date", value=date.today())
            headlines    = st.text_area("本週重點新聞")
            main_theme   = st.text_area("本週市場主線")
            equity       = st.text_area("Equity 股票市場")
            rates        = st.text_area("Rates 利率債券市場")
            commodity    = st.text_area("Commodity 商品市場")
            currency     = st.text_area("Currency 美元")
            volatility   = st.text_area("Volatility 波動率")
            crypto       = st.text_area("Crypto 加密貨幣")
            strongest    = st.text_input("本週最強資產")
            weakest      = st.text_input("本週最弱資產")
            regime       = st.text_input("Market Regime")
            next_watch   = st.text_area("下週觀察重點")
            summary_note = st.text_area("一句話總結")
            submitted    = st.form_submit_button("💾 Save Journal")

        if submitted:
            save_journal({
                "week_start": str(week_start),
                "headlines": headlines, "main_theme": main_theme,
                "equity": equity, "rates": rates, "commodity": commodity,
                "currency": currency, "volatility": volatility, "crypto": crypto,
                "strongest": strongest, "weakest": weakest,
                "regime": regime, "next_watch": next_watch, "summary": summary_note,
            })
            st.success("Journal saved!")

    with tab_history:
        df = load_journals()
        if df.empty:
            st.info("No journal entries yet.")
        else:
            for _, row in df.iterrows():
                with st.expander(f"📅 Week of {row['week_start']}  —  {row['regime']}"):
                    st.markdown(f"**市場主線：** {row['main_theme']}")
                    st.markdown(f"**重點新聞：** {row['headlines']}")
                    cols = st.columns(3)
                    cols[0].markdown(f"**Equity：** {row['equity']}")
                    cols[1].markdown(f"**Rates：** {row['rates']}")
                    cols[2].markdown(f"**Commodity：** {row['commodity']}")
                    cols2 = st.columns(3)
                    cols2[0].markdown(f"**Currency：** {row['currency']}")
                    cols2[1].markdown(f"**Volatility：** {row['volatility']}")
                    cols2[2].markdown(f"**Crypto：** {row['crypto']}")
                    st.markdown(f"**最強：** {row['strongest']}　**最弱：** {row['weakest']}")
                    st.markdown(f"**下週觀察：** {row['next_watch']}")
                    st.info(f"💬 {row['summary']}")


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: NEWS LOG
# ════════════════════════════════════════════════════════════════════════════
elif page == "News Log":
    st.title("📰 News Log")

    tab_new, tab_history = st.tabs(["➕ Add News", "📜 History"])

    with tab_new:
        with st.form("news_form", clear_on_submit=True):
            n_date     = st.date_input("Date", value=date.today())
            n_cat      = st.selectbox("Category", CATEGORIES)
            n_title    = st.text_input("News Title")
            n_interp   = st.text_area("My Interpretation")
            n_assets   = st.text_input("Affected Assets (comma-separated)")
            n_reaction = st.text_area("Actual Market Reaction")
            submitted  = st.form_submit_button("💾 Save News")

        if submitted and n_title:
            save_news({
                "date": str(n_date), "category": n_cat, "title": n_title,
                "interpretation": n_interp, "affected_assets": n_assets,
                "market_reaction": n_reaction,
            })
            st.success("News saved!")

    with tab_history:
        df = load_news()
        if df.empty:
            st.info("No news entries yet.")
        else:
            cat_filter = st.multiselect("Filter by category", CATEGORIES, default=CATEGORIES)
            df = df[df["category"].isin(cat_filter)]
            for _, row in df.iterrows():
                with st.expander(f"[{row['date']}] [{row['category']}] {row['title']}"):
                    st.markdown(f"**解讀：** {row['interpretation']}")
                    st.markdown(f"**影響資產：** {row['affected_assets']}")
                    st.markdown(f"**市場反應：** {row['market_reaction']}")
                    if st.button("🗑️ Delete", key=f"del_news_{row['id']}"):
                        delete_news(row["id"])
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: EARNINGS LOG
# ════════════════════════════════════════════════════════════════════════════
elif page == "Earnings Log":
    st.title("📋 Earnings Log")

    tab_new, tab_history = st.tabs(["➕ Add Earnings", "📜 History"])

    with tab_new:
        with st.form("earnings_form", clear_on_submit=True):
            e_ticker   = st.text_input("Ticker Symbol").upper()
            e_date     = st.date_input("Report Date", value=date.today())
            e_rev      = st.radio("Revenue Growth?", ["Yes", "No"], horizontal=True)
            e_eps      = st.radio("EPS Beat?",       ["Yes", "No"], horizontal=True)
            e_guidance = st.selectbox("Guidance", GUIDANCE_OPTIONS)
            e_react    = st.number_input("Price Reaction After Earnings (%)", step=0.1, format="%.2f")
            e_interp   = st.text_area("My Interpretation")
            submitted  = st.form_submit_button("💾 Save")

        if submitted and e_ticker:
            save_earnings({
                "ticker": e_ticker, "report_date": str(e_date),
                "revenue_growth": e_rev, "eps_beat": e_eps,
                "guidance": e_guidance, "price_reaction": e_react,
                "interpretation": e_interp,
            })
            st.success("Earnings saved!")

    with tab_history:
        df = load_earnings()
        if df.empty:
            st.info("No earnings entries yet.")
        else:
            st.dataframe(df.drop(columns=["created_at"], errors="ignore"), use_container_width=True)
            del_id = st.number_input("Delete by ID", min_value=1, step=1, value=1)
            if st.button("🗑️ Delete Entry"):
                delete_earnings(int(del_id))
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: TRADE JOURNAL
# ════════════════════════════════════════════════════════════════════════════
elif page == "Trade Journal":
    st.title("📒 Trade Journal")

    tab_new, tab_history = st.tabs(["➕ Add Trade", "📜 History"])

    with tab_new:
        with st.form("trade_form", clear_on_submit=True):
            t_date      = st.date_input("Date", value=date.today())
            t_ticker    = st.text_input("Ticker Symbol").upper()
            t_dir       = st.selectbox("Direction", DIRECTIONS)
            t_reason    = st.text_area("Entry Rationale")
            t_regime    = st.text_input("Macro Regime at Entry")
            t_risk      = st.text_area("Risk / Thesis Risk")
            t_stop      = st.text_input("Stop Loss")
            t_result    = st.text_area("Result")
            t_review    = st.text_area("Post-Trade Review")
            submitted   = st.form_submit_button("💾 Save Trade")

        if submitted and t_ticker:
            save_trade({
                "date": str(t_date), "ticker": t_ticker, "direction": t_dir,
                "reason": t_reason, "regime": t_regime, "risk": t_risk,
                "stop_loss": t_stop, "result": t_result, "review": t_review,
            })
            st.success("Trade saved!")

    with tab_history:
        df = load_trades()
        if df.empty:
            st.info("No trade entries yet.")
        else:
            dir_filter = st.multiselect("Filter by direction", DIRECTIONS, default=DIRECTIONS)
            df = df[df["direction"].isin(dir_filter)]
            for _, row in df.iterrows():
                label = f"[{row['date']}] {row['ticker']} — {row['direction']}"
                with st.expander(label):
                    st.markdown(f"**Regime：** {row['regime']}")
                    st.markdown(f"**Rationale：** {row['reason']}")
                    st.markdown(f"**Risk：** {row['risk']}　**Stop：** {row['stop_loss']}")
                    st.markdown(f"**Result：** {row['result']}")
                    st.markdown(f"**Review：** {row['review']}")
                    if st.button("🗑️ Delete", key=f"del_trade_{row['id']}"):
                        delete_trade(row["id"])
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ════════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    st.title("⚙️ Settings")
    st.markdown("### Data")
    if st.button("🔄 Clear Data Cache"):
        st.cache_data.clear()
        st.success("Cache cleared. Next page load will re-fetch from yfinance.")

    st.markdown("### About")
    st.markdown(
        "**Personal Market Research System** — MVP v1.0  \n"
        "Built with Streamlit · yfinance · SQLite  \n"
    )
