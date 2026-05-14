import pandas as pd
from modules.db import execute, init_tables, placeholder, _is_postgres

DIRECTIONS = ["Long", "Short", "Watch Only"]


def save_trade(data: dict):
    init_tables()
    is_pg = _is_postgres()
    cols = list(data)
    ph = placeholder(len(cols), is_pg)
    sql = f"INSERT INTO trade_log ({','.join(cols)}) VALUES ({ph})"
    execute(sql, list(data.values()))


def load_trades() -> pd.DataFrame:
    init_tables()
    rows = execute("SELECT * FROM trade_log ORDER BY date DESC", fetch=True)
    return pd.DataFrame(rows)


def delete_trade(row_id: int):
    execute("DELETE FROM trade_log WHERE id=%s" if _is_postgres() else "DELETE FROM trade_log WHERE id=?",
            (row_id,))
