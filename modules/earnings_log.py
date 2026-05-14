import pandas as pd
from modules.db import execute, init_tables, placeholder, _is_postgres

GUIDANCE_OPTIONS = ["Bullish", "Neutral", "Bearish"]


def save_earnings(data: dict):
    init_tables()
    is_pg = _is_postgres()
    cols = list(data)
    ph = placeholder(len(cols), is_pg)
    sql = f"INSERT INTO earnings_log ({','.join(cols)}) VALUES ({ph})"
    execute(sql, list(data.values()))


def load_earnings() -> pd.DataFrame:
    init_tables()
    rows = execute("SELECT * FROM earnings_log ORDER BY report_date DESC", fetch=True)
    return pd.DataFrame(rows)


def delete_earnings(row_id: int):
    execute("DELETE FROM earnings_log WHERE id=%s" if _is_postgres() else "DELETE FROM earnings_log WHERE id=?",
            (row_id,))
