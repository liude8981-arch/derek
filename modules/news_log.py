import pandas as pd
from modules.db import db_select, db_insert, db_delete

TABLE = "news_log"

CATEGORIES = ["Fed", "Inflation", "Yield", "Earnings", "Oil", "Geopolitical", "Other"]
IMPORTANCE  = ["High", "Medium", "Low"]


def save_news(data: dict):
    db_insert(TABLE, data)


def load_news() -> pd.DataFrame:
    return pd.DataFrame(db_select(TABLE, order_col="date"))


def delete_news(row_id: int):
    db_delete(TABLE, row_id)
