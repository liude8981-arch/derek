"""
Database connection abstraction.
- Local: SQLite (data/market_research.db)
- Cloud: Supabase PostgreSQL via st.secrets["supabase_url"]
"""
import sqlite3
import os
from pathlib import Path

try:
    import streamlit as st
    _HAS_ST = True
except ImportError:
    _HAS_ST = False

_DB_PATH = Path(__file__).parent.parent / "data" / "market_research.db"


def _is_postgres() -> bool:
    if not _HAS_ST:
        return False
    try:
        return "supabase_url" in st.secrets
    except Exception:
        return False


def get_connection():
    if _is_postgres():
        import psycopg2
        try:
            return psycopg2.connect(st.secrets["supabase_url"])
        except Exception as e:
            if _HAS_ST:
                st.error(f"❌ Supabase 連線失敗，請確認 Secrets 中的 supabase_url 是否正確。\n\n錯誤：{e}")
            raise
    else:
        _DB_PATH.parent.mkdir(exist_ok=True)
        return sqlite3.connect(_DB_PATH)


def placeholder(n: int, is_pg: bool) -> str:
    if is_pg:
        return ",".join(f"%s" for _ in range(n))
    return ",".join("?" for _ in range(n))


def execute(sql: str, params=(), fetch=False):
    """Run a single statement, optionally returning rows as list-of-dicts."""
    is_pg = _is_postgres()
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        if fetch:
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            return rows
        con.commit()
    finally:
        con.close()
    return []


def executemany_insert(table: str, cols: list[str], rows: list[list]):
    is_pg = _is_postgres()
    ph = placeholder(len(cols), is_pg)
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph})"
    con = get_connection()
    try:
        cur = con.cursor()
        cur.executemany(sql, rows)
        con.commit()
    finally:
        con.close()


def init_tables():
    """Create all tables if they don't exist (works for both SQLite & PG)."""
    is_pg = _is_postgres()
    auto_pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    ts_default = "DEFAULT NOW()" if is_pg else "DEFAULT (datetime('now'))"

    ddls = [
        f"""CREATE TABLE IF NOT EXISTS weekly_journal (
            id          {auto_pk},
            week_start  TEXT,
            headlines   TEXT,
            main_theme  TEXT,
            equity      TEXT,
            rates       TEXT,
            commodity   TEXT,
            currency    TEXT,
            volatility  TEXT,
            crypto      TEXT,
            strongest   TEXT,
            weakest     TEXT,
            regime      TEXT,
            next_watch  TEXT,
            summary     TEXT,
            created_at  TEXT {ts_default}
        )""",
        f"""CREATE TABLE IF NOT EXISTS news_log (
            id              {auto_pk},
            date            TEXT,
            category        TEXT,
            title           TEXT,
            interpretation  TEXT,
            affected_assets TEXT,
            market_reaction TEXT,
            created_at      TEXT {ts_default}
        )""",
        f"""CREATE TABLE IF NOT EXISTS earnings_log (
            id               {auto_pk},
            ticker           TEXT,
            report_date      TEXT,
            revenue_growth   TEXT,
            eps_beat         TEXT,
            guidance         TEXT,
            price_reaction   REAL,
            interpretation   TEXT,
            created_at       TEXT {ts_default}
        )""",
        f"""CREATE TABLE IF NOT EXISTS trade_log (
            id          {auto_pk},
            date        TEXT,
            ticker      TEXT,
            direction   TEXT,
            reason      TEXT,
            regime      TEXT,
            risk        TEXT,
            stop_loss   TEXT,
            result      TEXT,
            review      TEXT,
            created_at  TEXT {ts_default}
        )""",
    ]
    con = get_connection()
    try:
        cur = con.cursor()
        for ddl in ddls:
            cur.execute(ddl)
        con.commit()
    finally:
        con.close()
