"""
Database layer.
- Cloud: Supabase REST API (純 HTTPS，不需要 psycopg2 或 supabase-py)
- Local: SQLite
"""
import sqlite3
import requests
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "data" / "market_research.db"

try:
    import streamlit as st
    _HAS_ST = True
except ImportError:
    _HAS_ST = False


def _cfg():
    try:
        url = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/")
        key = st.secrets.get("SUPABASE_KEY", "").strip()
        return url, key
    except Exception:
        return "", ""


def _is_supabase() -> bool:
    if not _HAS_ST:
        return False
    url, key = _cfg()
    return bool(url and key)


def _headers():
    _, key = _cfg()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _base():
    url, _ = _cfg()
    return f"{url}/rest/v1"


# ── SQLite (local) ───────────────────────────────────────────────────────────

def _sqlite_conn():
    _DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(_DB_PATH)


def _sqlite_init():
    con = _sqlite_conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS weekly_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT, headlines TEXT, main_theme TEXT,
            equity TEXT, rates TEXT, commodity TEXT, currency TEXT,
            volatility TEXT, crypto TEXT, strongest TEXT, weakest TEXT,
            regime TEXT, next_watch TEXT, summary TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS news_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, category TEXT, title TEXT, interpretation TEXT,
            affected_assets TEXT, market_reaction TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS earnings_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT, report_date TEXT, revenue_growth TEXT,
            eps_beat TEXT, guidance TEXT, price_reaction REAL,
            interpretation TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, ticker TEXT, direction TEXT, reason TEXT,
            regime TEXT, risk TEXT, stop_loss TEXT,
            result TEXT, review TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    con.commit()
    con.close()


# ── Public API ───────────────────────────────────────────────────────────────

def db_select(table: str, order_col: str | None = None) -> list[dict]:
    if _is_supabase():
        params = {"select": "*"}
        if order_col:
            params["order"] = f"{order_col}.desc"
        r = requests.get(f"{_base()}/{table}", headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    else:
        _sqlite_init()
        con = _sqlite_conn()
        try:
            sql = f"SELECT * FROM {table}"
            if order_col:
                sql += f" ORDER BY {order_col} DESC"
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            return []
        finally:
            con.close()


def db_insert(table: str, data: dict):
    if _is_supabase():
        r = requests.post(f"{_base()}/{table}", headers=_headers(), json=data, timeout=10)
        r.raise_for_status()
    else:
        _sqlite_init()
        con = _sqlite_conn()
        cols = list(data)
        ph = ",".join("?" for _ in cols)
        con.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph})", list(data.values()))
        con.commit()
        con.close()


def db_delete(table: str, row_id: int):
    if _is_supabase():
        r = requests.delete(
            f"{_base()}/{table}",
            headers=_headers(),
            params={"id": f"eq.{row_id}"},
            timeout=10,
        )
        r.raise_for_status()
    else:
        _sqlite_init()
        con = _sqlite_conn()
        con.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
        con.commit()
        con.close()
