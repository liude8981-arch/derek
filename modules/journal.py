import pandas as pd
from modules.db import db_select, db_insert

TABLE = "weekly_journal"


def save_journal(data: dict):
    db_insert(TABLE, data)


def load_journals() -> pd.DataFrame:
    return pd.DataFrame(db_select(TABLE, order_col="week_start"))
