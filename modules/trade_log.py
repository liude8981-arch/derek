import pandas as pd
from modules.db import db_select, db_insert, db_delete

TABLE = "trade_log"
DIRECTIONS = ["Long", "Short", "Watch Only"]


def save_trade(data: dict):
    db_insert(TABLE, data)


def load_trades() -> pd.DataFrame:
    return pd.DataFrame(db_select(TABLE, order_col="date"))


def delete_trade(row_id: int):
    db_delete(TABLE, row_id)
