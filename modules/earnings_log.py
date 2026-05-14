import pandas as pd
from modules.db import db_select, db_insert, db_delete

TABLE = "earnings_log"
GUIDANCE_OPTIONS = ["Bullish", "Neutral", "Bearish"]


def save_earnings(data: dict):
    db_insert(TABLE, data)


def load_earnings() -> pd.DataFrame:
    return pd.DataFrame(db_select(TABLE, order_col="report_date"))


def delete_earnings(row_id: int):
    db_delete(TABLE, row_id)
