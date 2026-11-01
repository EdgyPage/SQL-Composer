"""warehouse - your connection to the warehouse, conn, and its two calls.

Set conn to your team's connection, the one team_connection.py gives.
"""

import sys

import pandas as pd

sys.path.append(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-E2-1")
from team_connection import conn  # noqa: E402  - your team's warehouse connection


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
