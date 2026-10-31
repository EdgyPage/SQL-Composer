"""warehouse - your connection to the warehouse, conn, and its two calls.

Why: every notebook in the Project reaches the warehouse through query and execute, so a change
to how you reach it is made here, once.

Set conn to your connection: an object whose query(sql) runs Hive that gives back rows and gives
them back as a pandas DataFrame, and whose execute(sql) runs Hive that changes something and
gives back nothing. Until you do, conn is the Example database, which the how-tos run on. You
pick which one sends each Statement, by calling run_query(s, query) for what gives back rows, as
a SELECT does, or run_execute(s, execute) for what changes something, as a write does. Let the
two share one session, so a Session setting sent through execute holds for what is sent after
it; and let each raise when the warehouse reports a failure, since the Toolbox knows a step
failed only when your connection raises. It imports none of your own files, so any notebook or
script of yours can import it.
"""

import pandas as pd

from sqlglot_composer import example_database

# Your connection to the warehouse. At work, replace example_database with your own, such as
# conn = your_library.connect(...): its query(sql) gives back a DataFrame, and its
# execute(sql) gives back nothing.
conn = example_database


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return conn.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    conn.execute(hive)
