"""warehouse - your connection to the warehouse, conn, and its two calls.

Why: every notebook in the Project reaches the warehouse through query and execute, so a change
to how you reach it is made here, once.

Set conn to your connection: an object whose query(sql) runs Hive that gives back rows and gives
them back as a pandas DataFrame, and whose execute(sql) runs Hive that changes something:
whatever it gives back, execute drops. You pick which one sends each Statement, by calling
run_query(s, query) for what gives back rows, as a SELECT does, or run_execute(s, execute) for
what changes something, as a write does. Let the two share one session, so a Session setting sent
through execute holds for what is sent after it; and let each raise when the warehouse reports a
failure, since the Toolbox knows a step failed only when your connection raises. It imports none
of your own files, so any notebook or script of yours can import it.
"""

import sys

import pandas as pd

# The folder that holds team_connection.py, your team's connection.
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E2-2")

from team_connection import conn  # noqa: E402


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
