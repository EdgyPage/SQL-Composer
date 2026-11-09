"""warehouse - connect, which takes your connection, and its two calls.

Why: every notebook in the Project reaches the warehouse through query and execute, so a change
to how you reach it is made here, once.

Each notebook runs on its own, so each gives its connection at its top, in its setup cell, with
connect(your_connection), before it calls query or execute; until it does, they refuse. Your
connection is an object whose query(sql) runs Hive that gives back rows and gives them back as
a pandas DataFrame, and whose execute(sql) runs Hive that changes something: whatever it gives
back, execute drops. The Example projects and the how-tos connect to the Example database:
connect(example_database). You pick which one sends each Statement, by calling
run_query(s, query) for what gives back rows, as a SELECT does, or run_execute(s, execute) for
what changes something, as a write does. Let the two share one session, so a Session setting
sent through execute holds for what is sent after it; and let each raise when the warehouse
reports a failure, since the Toolbox knows a step failed only when your connection raises. Keep
it importing nothing from references/, building_blocks/ or tables/, so any notebook or script
of yours can import it.
"""

from typing import NoReturn

import pandas as pd

# The connection this notebook gave connect(...): None until it connects.
_connection = None


def connect(connection: object) -> None:
    """Set the connection query and execute pass each Hive string to, such as
    connect(example_database): an object with a query(sql) and an execute(sql)."""
    global _connection
    for call in ("query", "execute"):
        if not callable(getattr(connection, call, None)):
            _refuse(
                what=f"The connection given to connect(...), a {type(connection).__name__}, "
                f"has no {call}(sql).",
                why="query passes each Hive string that gives back rows to your connection's "
                "query(sql), and execute each one that changes something to its execute(sql), "
                "so your connection needs both.",
                fix="Pass connect(...) the connection itself, the object with both, such as "
                f"connect(example_database) in the Example projects. If yours names its {call} "
                f"another way, change {call} below to call it.",
                error=TypeError,
            )
    _connection = connection


def query(hive: str) -> pd.DataFrame:
    """Run a Hive string that gives back rows, and give them back as a pandas DataFrame."""
    _check_connected("query")
    return _connection.query(hive)


def execute(hive: str) -> None:
    """Run a Hive string that changes something, such as a write, and give back nothing."""
    _check_connected("execute")
    _connection.execute(hive)


def _check_connected(call: str) -> None:
    """Refuse a call to query or execute made before this notebook connected."""
    if _connection is None:
        _refuse(
            what=f"No connection: call connect(...) first. {call}(...) was called before this "
            "notebook gave warehouse.py its connection.",
            why="Each notebook runs on its own, in a Python of its own, so each connects at "
            "its top: a connection given in another notebook, or before this one's kernel "
            "restarted, isn't this one's.",
            fix="In this notebook's setup cell, at its top, fill in the line connect(...) "
            "under its from warehouse import line with your connection, such as "
            "connect(example_database) in the Example projects, then run that cell again.",
            error=RuntimeError,
        )


def _refuse(what: str, why: str, fix: str, error: type[Exception]) -> NoReturn:
    """Stop, with the four parts every refusal of the Toolbox has."""
    raise error(f"\n  What happened:  {what}"
                f"\n  Why it matters: {why}"
                f"\n  Usual fix:      {fix}"
                "\n  Opt-out:        none - this one can't be switched off.")
