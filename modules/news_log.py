import pandas as pd
from modules.db import execute, init_tables, placeholder, _is_postgres

CATEGORIES = ["Fed", "Inflation", "Yield", "Oil", "Earnings", "Geopolitical", "Other"]


def save_news(data: dict):
    init_tables()
    is_pg = _is_postgres()
    cols = list(data)
    ph = placeholder(len(cols), is_pg)
    sql = f"INSERT INTO news_log ({','.join(cols)}) VALUES ({ph})"
    execute(sql, list(data.values()))


def load_news() -> pd.DataFrame:
    init_tables()
    rows = execute("SELECT * FROM news_log ORDER BY date DESC", fetch=True)
    return pd.DataFrame(rows)


def delete_news(row_id: int):
    execute("DELETE FROM news_log WHERE id=%s" if _is_postgres() else "DELETE FROM news_log WHERE id=?",
            (row_id,))
