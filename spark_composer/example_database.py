# Spark Composer 3.0, exported 2026-09-30 18:29 - generated from dev, do not edit
"""The Example database: three made-up tables, and a send to run Statements on.

It holds the Table references `jobs`, `job_runs` and `run_alerts`, their rows (two days,
2026-09-23 and 2026-09-24), and `send`, which runs a Statement's Hive on a small database of
the Toolbox's own and returns a DataFrame, just like your own send at work. It never reaches
your warehouse, so it is safe to try anything here. Where it can't run a query, it says why.

Unlike the warehouse, it gives the rows in the same order every time. When a Statement has no
ORDER_BY, its rows are sorted by its first column, then its second, and so on, with None first.
At work, rows come back in no fixed order: sort the DataFrame in pandas when the order matters.

>>> runs = example_database.job_runs
>>> run(statement(
...     SELECT(runs.run_id, runs.status, runs.duration_mins),
...     FROM(runs),
...     WHERE(equals(runs.dt, "2026-09-23")),
... ), send=example_database.send)
   run_id   status  duration_mins
0      95  SUCCESS             12
1      96  SUCCESS             18
2      97   FAILED             30
3      98     None             15
4      99     TEST              5
"""

from __future__ import annotations

import re

import pandas as pd

from . import engine
from .refusals import four_part_message
from .tables import Table

TOOLBOX_VERSION = "3.0"

# --- The Table references -----------------------------------------------------------------

jobs = Table(
    "ops.jobs",
    columns={"job_id": "bigint", "job_name": "string", "team": "string", "region": "string"},
    date_partition=None,
    key=["job_id"],
)

job_runs = Table(
    "ops.job_runs",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "status": "string",  # SUCCESS / FAILED / TEST, NULL while running
        "duration_mins": "int",
        "avg_retry_secs": "double",
        "dt": "string",
    },
    date_partition="dt",
    key=["run_id"],
    does_not_add_up=["avg_retry_secs"],
)

run_alerts = Table(
    "ops.run_alerts",
    columns={
        "alert_id": "bigint",
        "run_id": "bigint",
        "severity": "string",  # low / high
        "dt": "string",
    },
    date_partition="dt",
    key=["alert_id"],
)

# The column comments DESCRIBE returns.
_COMMENTS = {
    ("job_runs", "status"): "SUCCESS / FAILED / TEST, NULL while running",
    ("run_alerts", "severity"): "low / high",
}

# --- The rows: small enough to read by eye, so every wrong number is visibly wrong ----------

_JOBS = [
    # job_id, job_name,       team,      region
    (1, "nightly_load", "data", "LON"),
    (2, "invoice_sync", "finance", "PAR"),
    (3, "report_build", "finance", "NYC"),
    (4, "cache_warm", "web", "LON"),  # never runs: shows what LEFT_JOIN keeps
]

_JOB_RUNS = [
    # run_id, job_id, status,  duration_mins, avg_retry_secs, dt
    (95, 1, "SUCCESS", 12, 2.0, "2026-09-23"),
    (96, 2, "SUCCESS", 18, 0.0, "2026-09-23"),
    (97, 3, "FAILED", 30, 8.0, "2026-09-23"),
    (98, 2, None, 15, None, "2026-09-23"),  # still running: status NULL
    (99, 1, "TEST", 5, 0.0, "2026-09-23"),
    (101, 1, "SUCCESS", 10, 1.0, "2026-09-24"),
    (102, 2, "FAILED", 20, 6.0, "2026-09-24"),
    (103, 3, "SUCCESS", 30, 0.0, "2026-09-24"),
    (104, 1, "SUCCESS", 40, 3.0, "2026-09-24"),
]

_RUN_ALERTS = [
    # alert_id, run_id, severity, dt
    (1, 97, "high", "2026-09-23"),
    (2, 97, "low", "2026-09-23"),
    (3, 101, "low", "2026-09-24"),
    (4, 101, "low", "2026-09-24"),
    (5, 101, "high", "2026-09-24"),
    (6, 102, "high", "2026-09-24"),
    (7, 103, "low", "2026-09-24"),
    (8, 103, "low", "2026-09-24"),
    (9, 104, "low", "2026-09-24"),
]

_TABLES = {"jobs": (jobs, _JOBS), "job_runs": (job_runs, _JOB_RUNS),
          "run_alerts": (run_alerts, _RUN_ALERTS)}

def _table(name: str) -> tuple[Table, list]:
    short = name.strip().strip("`").split(".")[-1].strip("`")
    if short not in _TABLES:
        raise ValueError(four_part_message(
            what=f"The Example database has no table {name!r}.",
            why="It holds only three made-up tables.",
            fix="Use ops.jobs, ops.job_runs or ops.run_alerts.",
            opt_out=None,
        ))
    return _TABLES[short]


def _describe(name: str) -> pd.DataFrame:
    """What DESCRIBE prints: the columns, then the partition columns again."""
    table, _ = _table(name)
    rows = [(column, kind, _COMMENTS.get((table._alias, column), ""))
            for column, kind in table._columns.items()]
    if table._date_partition is not None:
        rows += [
            ("", None, None),
            ("# Partition Information", None, None),
            ("# col_name", "data_type", "comment"),
            (table._date_partition, table._columns[table._date_partition], ""),
        ]
    return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])


def _show_partitions(name: str) -> pd.DataFrame:
    """What SHOW PARTITIONS prints: one row per day, like dt=2026-09-23."""
    table, rows = _table(name)
    if table._date_partition is None:
        raise ValueError(f"Table {table._name} is not a partitioned table.")
    position = list(table._columns).index(table._date_partition)
    days = sorted({row[position] for row in rows})
    return pd.DataFrame({"partition": [f"{table._date_partition}={day}" for day in days]})


# A string in single or double quotes, a name in backticks, or a comment to the end of its
# line: what a query says, as opposed to what it is. Whichever starts first wins, as when Hive
# reads it, so a -- inside a string is part of the string.
_SAID = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`]|``)*`|--[^\n]*""")


def _outside_brackets(text: str) -> str:
    """The Hive with its comments, quoted text and everything inside brackets blanked out.

    What is left is the query itself: a window's OVER (...) and a Derived table's
    WITH ... AS (...) are inside brackets, and a string can say anything.
    """
    said = _SAID.sub(lambda found: "" if found.group().startswith("--") else "''", text)
    depth, outside = 0, []
    for character in said:
        depth += {"(": 1, ")": -1}.get(character, 0)
        outside.append(character if depth == 0 else " ")
    return "".join(outside)


def _command(words: list[str]) -> str:
    """The word a query's command starts with: the first, or the first after WITH's tables.

    After WITH come the Derived tables, `name AS (...)`, with a comma between each; the first
    word after a closing bracket with no comma after it starts the command.
    """
    if words[:1] != ["WITH"]:
        return words[0] if words else ""
    for before, word in zip(words, words[1:]):
        if before == ")" and word != ",":
            return word
    return ""


def _is_query(text: str) -> bool:
    """Whether the Hive is one query that only reads.

    Its command must be SELECT, and nothing may follow a `;`: a write, even after WITH, and a
    second command are not queries.
    """
    words = [word.upper() for word in
             re.findall(r"[A-Za-z_]+|[;),]", _outside_brackets(text).rstrip().rstrip(";"))]
    return ";" not in words and _command(words) == "SELECT"


def _sorts_itself(text: str) -> bool:
    """Whether the Hive sorts its own rows: an ORDER BY outside every bracket.

    An ORDER BY inside brackets belongs to a window or to a Derived table, and neither orders
    the rows that come back.
    """
    return re.search(r"\bORDER\s+BY\b", _outside_brackets(text), re.IGNORECASE) is not None


def _in_order(row: tuple) -> tuple:
    """A row's place when the rows are sorted by every column, with NULL first."""
    return tuple((value is not None, value) for value in row)


def send(hive):
    """Run Hive on the Example database and return a DataFrame, like your send at work.

    >>> example_database.send("DESCRIBE ops.jobs")
       col_name data_type comment
    0    job_id    bigint
    1  job_name    string
    2      team    string
    3    region    string
    """
    text = hive.strip()
    words = text.split()
    if words[:1] and words[0].upper() == "DESCRIBE":
        return _describe(words[-1])
    if [w.upper() for w in words[:2]] == ["SHOW", "PARTITIONS"]:
        return _show_partitions(words[-1])
    if not _is_query(text):
        raise ValueError(four_part_message(
            what="The Example database only answers SELECT, DESCRIBE and SHOW PARTITIONS; it "
            "can't be written to.",
            why="Its tables are made up and fixed, so every Worked example gives the same "
            "numbers.",
            fix="to_hive(...) shows a write's Hive without sending it, as in "
            "to_hive(drop_table(t)). It takes what create_table, drop_table or statement(...) "
            "builds, not text.",
            opt_out=None,
        ))
    columns, rows = engine.run_query(text, _TABLES)
    if not _sorts_itself(text):
        rows = sorted(rows, key=_in_order)
    return pd.DataFrame(rows, columns=columns)
