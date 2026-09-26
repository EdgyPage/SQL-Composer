# SQL Composer 2.0, exported 2026-09-25 21:43 - generated from dev, do not edit
"""The Example database: three made-up tables, and a send to run Statements on.

It holds the Table references `jobs`, `job_runs` and `run_alerts`, their rows (two days,
2026-09-23 and 2026-09-24), and `send`, which runs a Statement's Hive on sqlglot's own
executor and returns a DataFrame, just like your own send at work. Nothing leaves Python,
so it is safe to try anything here. It needs sqlglot 30.19.0 or newer to run a query;
DESCRIBE and SHOW PARTITIONS work on any version.

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
import sqlglot
from sqlglot import exp

from .refusals import four_part_message
from .tables import Table, hive_text

TOOLBOX_VERSION = "2.0"

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

# Hive's column comments, which DESCRIBE returns.
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

_EXECUTOR_NEEDS = (30, 19, 0)


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
    """What Hive's DESCRIBE prints: the columns, then the partition columns again."""
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
    """What Hive's SHOW PARTITIONS prints: one row per day, like dt=2026-09-23."""
    table, rows = _table(name)
    if table._date_partition is None:
        raise ValueError(f"Table {table._name} is not a partitioned table.")
    position = list(table._columns).index(table._date_partition)
    days = sorted({row[position] for row in rows})
    return pd.DataFrame({"partition": [f"{table._date_partition}={day}" for day in days]})


def _executor_ready() -> None:
    """Stop with a plain message when sqlglot's executor would give wrong answers."""
    found = sqlglot.__version__
    numbers = re.match(r"(\d+)\.(\d+)\.(\d+)", found)
    version = tuple(int(n) for n in numbers.groups()) if numbers else (0, 0, 0)
    from sqlglot.executor import execute

    if version >= _EXECUTOR_NEEDS:
        check = execute("SELECT COUNT(DISTINCT x) AS n FROM t", dialect="hive",
                        tables={"t": [{"x": "a"}, {"x": "a"}, {"x": "b"}, {"x": None}]})
        if check.rows == [(2,)]:
            return
    raise RuntimeError(four_part_message(
        what="The Example database runs queries on sqlglot's own executor, which needs "
        f"sqlglot 30.19.0 or newer to count correctly. This Python has sqlglot {found}.",
        why="An older executor counts COUNT(DISTINCT ...) wrong, and says nothing.",
        fix="The rest of the Toolbox works as usual: to_hive(...) still shows a Statement's "
        "Hive. Only running queries on the Example database stops.",
        opt_out=None,
    ))


def _like_spelled_out(tree: exp.Expression) -> exp.Expression:
    """Rewrite each escaped LIKE, since sqlglot's executor ignores LIKE's backslash.

    starts_with and contains put a backslash before % and _ so they match themselves. Hive
    reads them that way, but the executor would still take _ for any one character.
    """
    for like in list(tree.find_all(exp.Like)):
        pattern = like.expression
        if isinstance(pattern, exp.Literal) and pattern.is_string and "\\" in pattern.this:
            like.replace(_matching_text(like.this, pattern.this))
    return tree


def _matching_text(column: exp.Expression, pattern: str) -> exp.Expression:
    """The same test as `column LIKE pattern`, for a pattern of text between optional %."""
    parts, i = [], 0
    while i < len(pattern):
        if pattern[i] == "\\" and i + 1 < len(pattern):
            parts.append(("text", pattern[i + 1]))
            i += 2
        else:
            parts.append(("wild" if pattern[i] in "%_" else "text", pattern[i]))
            i += 1
    leading = parts[:1] == [("wild", "%")]
    trailing = len(parts) > leading and parts[-1] == ("wild", "%")
    middle = parts[leading:len(parts) - trailing]
    if any(kind == "wild" for kind, _ in middle):
        _cant_run(f"LIKE with a % or _ in the middle ({pattern!r})")
    text = "".join(char for _, char in middle)
    found = exp.Literal.string(text)
    size = exp.Literal.number(len(text))
    if leading and trailing:
        return exp.GT(this=exp.StrPosition(this=column, substr=found),
                      expression=exp.Literal.number(0))
    if leading:
        return exp.EQ(this=exp.Right(this=column, expression=size), expression=found)
    if trailing:
        return exp.EQ(this=exp.Left(this=column, expression=size), expression=found)
    return exp.EQ(this=column, expression=found)


def _missing_function(tree: exp.Expression, error: str) -> str:
    """The Hive name of the function the executor didn't know, from its error."""
    found = re.search(r"name '(\w+)' is not defined", error)
    if found is not None:
        for function in tree.find_all(exp.Func):
            if function.key.upper() == found.group(1):
                return hive_text(function).split("(")[0]
    return f"what this needs ({error})"


def _cant_run(missing: str, error: Exception | None = None) -> None:
    raise RuntimeError(four_part_message(
        what=f"The Example database can't run this Hive: its executor has no {missing}.",
        why="The Example database runs Hive on sqlglot's own small executor, which knows only "
        "part of Hive. Hive at work knows all of it.",
        fix="See the Hive with to_hive(...), and run it at work with your own send; or try "
        "the Statement here without that part.",
        opt_out=None,
    )) from error


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
    tree = sqlglot.parse_one(text, read="hive")
    if not isinstance(tree, exp.Select):
        raise ValueError(four_part_message(
            what="The Example database only answers SELECT, DESCRIBE and SHOW PARTITIONS; it "
            "can't be written to.",
            why="Its tables are made up and fixed, so every Worked example gives the same "
            "numbers.",
            fix="A write's Hive can still be shown with to_hive(...).",
            opt_out=None,
        ))
    _executor_ready()
    from sqlglot.executor import execute

    schema = {"ops": {name: dict(table._columns) for name, (table, _) in _TABLES.items()}}
    tables = {"ops": {name: [dict(zip(table._columns, row)) for row in rows]
                      for name, (table, rows) in _TABLES.items()}}
    if tree.find(exp.Window):
        _cant_run("window functions such as row_number")
    try:
        result = execute(_like_spelled_out(tree), schema=schema, tables=tables, dialect="hive")
    except sqlglot.errors.ExecuteError as error:
        _cant_run(_missing_function(tree, str(error)), error)
    return pd.DataFrame(result.rows, columns=result.columns)
