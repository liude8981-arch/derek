import pandas as pd
from modules.db import execute, init_tables, placeholder, _is_postgres, get_connection

FIELDS = [
    "week_start","headlines","main_theme","equity","rates","commodity",
    "currency","volatility","crypto","strongest","weakest","regime",
    "next_watch","summary",
]


def save_journal(data: dict):
    init_tables()
    is_pg = _is_postgres()
    cols = list(data)
    ph = placeholder(len(cols), is_pg)
    sql = f"INSERT INTO weekly_journal ({','.join(cols)}) VALUES ({ph})"
    execute(sql, list(data.values()))


def load_journals() -> pd.DataFrame:
    init_tables()
    rows = execute("SELECT * FROM weekly_journal ORDER BY week_start DESC", fetch=True)
    return pd.DataFrame(rows)
