# sqlglot Composer 8.1 - copy it, then edit your copy
"""warehouse - your connection to the warehouse, conn, and its two calls.
"""

import sys

import pandas as pd

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W1-2")
from team_connection import conn  # noqa: E402


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
