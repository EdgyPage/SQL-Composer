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

from .tables import Table

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
COMMENTS = {
    ("job_runs", "status"): "SUCCESS / FAILED / TEST, NULL while running",
    ("run_alerts", "severity"): "low / high",
}

# --- The rows: small enough to read by eye, so every wrong number is visibly wrong ----------

JOBS = [
    # job_id, job_name,       team,      region
    (1, "nightly_load", "data", "LON"),
    (2, "invoice_sync", "finance", "PAR"),
    (3, "report_build", "finance", "NYC"),
    (4, "cache_warm", "web", "LON"),  # never runs: shows what LEFT_JOIN keeps
]

JOB_RUNS = [
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

RUN_ALERTS = [
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

TABLES = {"jobs": (jobs, JOBS), "job_runs": (job_runs, JOB_RUNS),
          "run_alerts": (run_alerts, RUN_ALERTS)}

EXECUTOR_NEEDS = (30, 19, 0)


def _table(name: str) -> tuple[Table, list]:
    short = name.strip().strip("`").split(".")[-1].strip("`")
    if short not in TABLES:
        raise ValueError(
            f"The Example database has no table {name!r}. Its tables are ops.jobs, "
            "ops.job_runs and ops.run_alerts."
        )
    return TABLES[short]


def _describe(name: str) -> pd.DataFrame:
    """What Hive's DESCRIBE prints: the columns, then the partition columns again."""
    table, _ = _table(name)
    rows = [(column, kind, COMMENTS.get((table._alias, column), ""))
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

    if version >= EXECUTOR_NEEDS:
        check = execute("SELECT COUNT(DISTINCT x) AS n FROM t", dialect="hive",
                        tables={"t": [{"x": "a"}, {"x": "a"}, {"x": "b"}, {"x": None}]})
        if check.rows == [(2,)]:
            return
    raise RuntimeError(
        f"The Example database runs queries on sqlglot's own executor, which needs sqlglot "
        f"30.19.0 or newer to count correctly. This Python has sqlglot {found}. The rest of "
        "the Toolbox works as usual; only running queries on the Example database stops."
    )


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
        raise ValueError(
            "The Example database only answers SELECT, DESCRIBE and SHOW PARTITIONS; it "
            "can't be written to. A write's Hive can still be shown with to_hive(...)."
        )
    _executor_ready()
    from sqlglot.executor import execute

    schema = {"ops": {name: dict(table._columns) for name, (table, _) in TABLES.items()}}
    tables = {"ops": {name: [dict(zip(table._columns, row)) for row in rows]
                      for name, (table, rows) in TABLES.items()}}
    result = execute(text, schema=schema, tables=tables, dialect="hive")
    return pd.DataFrame(result.rows, columns=result.columns)
