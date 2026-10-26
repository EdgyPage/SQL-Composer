# sqlglot Composer 7.2 - copy it, then edit your copy
"""warehouse - your two calls to the warehouse, query and execute.

Why: every notebook in the Project reaches the warehouse through these two functions, so a
change to how you reach it is made here, once.

You pick which one sends each Statement, by calling run_query(s, query) for what gives back
rows, as a SELECT does, or run_execute(s, execute) for what changes something, as a write does.
Replace each example_database call with your warehouse's own: the how-to Start a Project shows
how to write them. Let the two share one session, so a Session setting sent through execute
holds for what is sent after it, through either function; and let each raise when the warehouse
reports a failure, since the Toolbox knows a step failed only when your function raises. It
imports none of your own files, so any notebook or script of yours can import it.
"""

import pandas as pd

from sqlglot_composer import example_database


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    return example_database.query(hive)  # at work: your warehouse's query call


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    example_database.execute(hive)  # at work: your warehouse's execute call
