# Composer core 4.0, exported 2026-10-06 00:26 - generated from dev, do not edit
"""The Example database: six made-up tables, and a send to run Statements on.

It holds the Table references `jobs`, `job_runs` and `run_alerts`, with rows on two days,
2026-09-23 and 2026-09-24, and three more with rows on 14 days, 2026-09-11 to 2026-09-24:

- `job_events`: each run's events, start, finish, retry and fail;
- `job_owners`: one row per job per day, with its team and owner, so you can see report_build
  move from data to finance on 2026-09-18;
- `region_costs`: each run's cost in cents, partitioned by region ("eu" or "us", where
  the job is billed, not the jobs table's LON, PAR or NYC), then by day, with days written like
  20260911 rather than 2026-09-11.

These three keep a record of their own: they have no run_id, and don't match job_runs run for
run.

`send` runs a Statement's Hive on a small database of the Toolbox's own and returns a
DataFrame, just like your own send at work. It never reaches your warehouse, so it is safe to
try anything here. Where it can't run a query, it says why.

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

from . import edition
from .refusals import refuse
from .tables import Table

TOOLBOX_VERSION = "4.0"

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

# Three more tables, with rows on 14 days, 2026-09-11 to 2026-09-24.

job_events = Table(
    "ops.job_events",
    columns={
        "event_id": "bigint",
        "job_id": "bigint",
        "event_type": "string",  # start / finish / retry / fail
        "minutes": "int",  # minutes since the run started
        "dt": "string",
    },
    date_partition="dt",
    key=["event_id"],
)

job_owners = Table(
    "ops.job_owners",
    columns={
        "job_id": "bigint",
        "team": "string",
        "owner": "string",  # NULL when nobody owns the job
        "dt": "string",
    },
    date_partition="dt",
    key=["job_id", "dt"],
)

region_costs = Table(
    "ops.region_costs",
    columns={
        "job_id": "bigint",
        "cost_cents": "bigint",  # NULL until the bill comes in
        "region": "string",
        "dt": "string",
    },
    date_partition="dt",
    date_format="%Y%m%d",
    key=["job_id", "region", "dt"],
)

# The column comments DESCRIBE returns.
_COMMENTS = {
    ("job_runs", "status"): "SUCCESS / FAILED / TEST, NULL while running",
    ("run_alerts", "severity"): "low / high",
    ("job_events", "event_type"): "start / finish / retry / fail",
    ("job_events", "minutes"): "minutes since the run started",
    ("job_owners", "owner"): "NULL when nobody owns the job",
    ("region_costs", "cost_cents"): "NULL until the bill comes in",
}

# The partition columns, in order, of a table partitioned by more than its Date partition.
_PARTITIONS = {"region_costs": ["region", "dt"]}

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

_JOB_EVENTS = [
    # event_id, job_id, event_type, minutes, dt
    (1, 1, "start", 0, "2026-09-11"),
    (2, 1, "finish", 12, "2026-09-11"),
    (3, 2, "start", 0, "2026-09-11"),
    (4, 2, "finish", 18, "2026-09-11"),
    (5, 3, "start", 0, "2026-09-11"),
    (6, 3, "finish", 30, "2026-09-11"),
    (7, 1, "start", 0, "2026-09-12"),
    (8, 1, "finish", 11, "2026-09-12"),
    (9, 1, "start", 0, "2026-09-13"),
    (10, 1, "finish", 13, "2026-09-13"),
    (11, 1, "start", 0, "2026-09-14"),
    (12, 1, "finish", 12, "2026-09-14"),
    (13, 2, "start", 0, "2026-09-14"),
    (14, 2, "finish", 20, "2026-09-14"),
    (15, 3, "start", 0, "2026-09-14"),
    (16, 3, "retry", 8, "2026-09-14"),
    (17, 3, "finish", 41, "2026-09-14"),
    (18, 1, "start", 0, "2026-09-15"),
    (19, 1, "finish", 10, "2026-09-15"),
    (20, 2, "start", 0, "2026-09-15"),
    (21, 2, "finish", 17, "2026-09-15"),
    (22, 1, "start", 0, "2026-09-16"),
    (23, 1, "retry", 5, "2026-09-16"),
    (24, 1, "finish", 25, "2026-09-16"),
    (25, 2, "start", 0, "2026-09-16"),
    (26, 2, "finish", 19, "2026-09-16"),
    (27, 1, "start", 0, "2026-09-17"),
    (28, 1, "finish", 12, "2026-09-17"),
    (29, 2, "start", 0, "2026-09-17"),
    (30, 2, "finish", 16, "2026-09-17"),
    (31, 1, "start", 0, "2026-09-18"),
    (32, 1, "finish", 14, "2026-09-18"),
    (33, 2, "start", 0, "2026-09-18"),
    (34, 2, "finish", 22, "2026-09-18"),
    (35, 3, "start", 0, "2026-09-18"),
    (36, 3, "fail", 12, "2026-09-18"),
    (37, 1, "start", 0, "2026-09-19"),
    (38, 1, "finish", 11, "2026-09-19"),
    (39, 1, "start", 0, "2026-09-20"),
    (40, 1, "finish", 12, "2026-09-20"),
    (41, 1, "start", 0, "2026-09-21"),
    (42, 1, "finish", 13, "2026-09-21"),
    (43, 2, "start", 0, "2026-09-21"),
    (44, 2, "finish", 21, "2026-09-21"),
    (45, 3, "start", 0, "2026-09-21"),
    (46, 3, "finish", 33, "2026-09-21"),
    (47, 1, "start", 0, "2026-09-22"),
    (48, 1, "finish", 10, "2026-09-22"),
    (49, 2, "start", 0, "2026-09-22"),
    (50, 2, "finish", 18, "2026-09-22"),
    (51, 1, "start", 0, "2026-09-23"),
    (52, 1, "finish", 12, "2026-09-23"),
    (53, 2, "start", 0, "2026-09-23"),
    (54, 2, "finish", 18, "2026-09-23"),
    (55, 1, "start", 0, "2026-09-24"),
    (56, 1, "finish", 10, "2026-09-24"),
    (57, 2, "start", 0, "2026-09-24"),  # still running: no finish yet
]

_JOB_OWNERS = [
    # job_id, team, owner, dt: every job, every day
    (1, "data", "ana", "2026-09-11"),
    (2, "finance", "ben", "2026-09-11"),
    (3, "data", "ana", "2026-09-11"),
    (4, "web", None, "2026-09-11"),  # nobody owns cache_warm
    (1, "data", "ana", "2026-09-12"),
    (2, "finance", "ben", "2026-09-12"),
    (3, "data", "ana", "2026-09-12"),
    (4, "web", None, "2026-09-12"),
    (1, "data", "ana", "2026-09-13"),
    (2, "finance", "ben", "2026-09-13"),
    (3, "data", "ana", "2026-09-13"),
    (4, "web", None, "2026-09-13"),
    (1, "data", "ana", "2026-09-14"),
    (2, "finance", "ben", "2026-09-14"),
    (3, "data", "ana", "2026-09-14"),
    (4, "web", None, "2026-09-14"),
    (1, "data", "ana", "2026-09-15"),
    (2, "finance", "ben", "2026-09-15"),
    (3, "data", "ana", "2026-09-15"),
    (4, "web", None, "2026-09-15"),
    (1, "data", "ana", "2026-09-16"),
    (2, "finance", "ben", "2026-09-16"),
    (3, "data", "ana", "2026-09-16"),
    (4, "web", None, "2026-09-16"),
    (1, "data", "ana", "2026-09-17"),
    (2, "finance", "ben", "2026-09-17"),
    (3, "data", "ana", "2026-09-17"),
    (4, "web", None, "2026-09-17"),
    (1, "data", "ana", "2026-09-18"),
    (2, "finance", "ben", "2026-09-18"),
    (3, "finance", "chloe", "2026-09-18"),  # report_build moves to finance
    (4, "web", None, "2026-09-18"),
    (1, "data", "ana", "2026-09-19"),
    (2, "finance", "ben", "2026-09-19"),
    (3, "finance", "chloe", "2026-09-19"),
    (4, "web", None, "2026-09-19"),
    (1, "data", "ana", "2026-09-20"),
    (2, "finance", "ben", "2026-09-20"),
    (3, "finance", "chloe", "2026-09-20"),
    (4, "web", None, "2026-09-20"),
    (1, "data", "ana", "2026-09-21"),
    (2, "finance", "ben", "2026-09-21"),
    (3, "finance", "chloe", "2026-09-21"),
    (4, "web", None, "2026-09-21"),
    (1, "data", "ana", "2026-09-22"),
    (2, "finance", "ben", "2026-09-22"),
    (3, "finance", "chloe", "2026-09-22"),
    (4, "web", None, "2026-09-22"),
    (1, "data", "ana", "2026-09-23"),
    (2, "finance", "ben", "2026-09-23"),
    (3, "finance", "chloe", "2026-09-23"),
    (4, "web", None, "2026-09-23"),
    (1, "data", "ana", "2026-09-24"),
    (2, "finance", "ben", "2026-09-24"),
    (3, "finance", "chloe", "2026-09-24"),
    (4, "web", None, "2026-09-24"),
]

_REGION_COSTS = [
    # job_id, cost_cents, region, dt: London and Paris are billed in eu, New York in us
    (1, 120, "eu", "20260911"),
    (2, 180, "eu", "20260911"),
    (1, 110, "eu", "20260912"),
    (1, 130, "eu", "20260913"),
    (1, 120, "eu", "20260914"),
    (2, 200, "eu", "20260914"),
    (1, 100, "eu", "20260915"),
    (2, 170, "eu", "20260915"),
    (1, 250, "eu", "20260916"),
    (2, 190, "eu", "20260916"),
    (1, 120, "eu", "20260917"),
    (2, 160, "eu", "20260917"),
    (1, 140, "eu", "20260918"),
    (2, 220, "eu", "20260918"),
    (1, 110, "eu", "20260919"),
    (1, 120, "eu", "20260920"),
    (1, 130, "eu", "20260921"),
    (2, 210, "eu", "20260921"),
    (1, 100, "eu", "20260922"),
    (2, 180, "eu", "20260922"),
    (1, 120, "eu", "20260923"),
    (2, 180, "eu", "20260923"),
    (1, 100, "eu", "20260924"),
    (2, None, "eu", "20260924"),  # still running: not billed yet
    (3, 300, "us", "20260911"),
    (3, 410, "us", "20260914"),
    (3, 120, "us", "20260918"),
    (3, 330, "us", "20260921"),
]

_TABLES = {"jobs": (jobs, _JOBS), "job_runs": (job_runs, _JOB_RUNS),
          "run_alerts": (run_alerts, _RUN_ALERTS), "job_events": (job_events, _JOB_EVENTS),
          "job_owners": (job_owners, _JOB_OWNERS),
          "region_costs": (region_costs, _REGION_COSTS)}

def _table(name: str) -> tuple[Table, list]:
    # Hive and Spark read a table's name whatever its case.
    *database, short = [part.strip("`").lower() for part in name.strip().split(".")]
    if short not in _TABLES or database not in ([], ["ops"]):
        names = [f"ops.{table}" for table in _TABLES]
        refuse(
            what=f"The Example database has no table {name!r}.",
            why="It holds six made-up tables, all in the database ops.",
            fix=f"Use {', '.join(names[:-1])} or {names[-1]}.",
            error=ValueError,
        )
    return _TABLES[short]


def _partition_columns(table: Table) -> list[str]:
    """The table's partition columns, in order: its Date partition, and any before it."""
    if table._date_partition is None:
        return []
    return _PARTITIONS.get(table._alias, [table._date_partition])


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
        ]
        rows += [(column, table._columns[column], "") for column in _partition_columns(table)]
    return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])


def _show_partitions(name: str) -> pd.DataFrame:
    """What SHOW PARTITIONS prints: one row per partition, like dt=2026-09-23, or
    region=eu/dt=20260911 for a table partitioned by two columns."""
    table, rows = _table(name)
    if table._date_partition is None:
        raise ValueError(f"Table {table._name} is not a partitioned table.")
    columns = _partition_columns(table)
    positions = [list(table._columns).index(column) for column in columns]
    values = sorted({tuple(row[position] for position in positions) for row in rows})
    return pd.DataFrame({"partition": [
        "/".join(f"{column}={value}" for column, value in zip(columns, partition))
        for partition in values]})


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
    if not isinstance(hive, str):
        refuse(
            what=f"example_database.send was given {hive!r}, which isn't Hive text.",
            why="Like your send at work, it takes Hive text to run.",
            fix="To run a Statement, pass it to run(s, send=example_database.send), which "
            "turns it into Hive; to_hive(s) shows that Hive.",
            given=hive, call="example_database.send",
        )
    text = hive.strip()
    words = text.split()
    if words[:1] and words[0].upper() == "DESCRIBE":
        return _describe(words[-1])
    if [w.upper() for w in words[:2]] == ["SHOW", "PARTITIONS"]:
        return _show_partitions(words[-1])
    if not _is_query(text):
        refuse(
            what="The Example database only answers SELECT, DESCRIBE and SHOW PARTITIONS; it "
            "can't be written to.",
            why="Its tables are made up and fixed, so every Worked example gives the same "
            "numbers.",
            fix="to_hive(...) shows a write's Hive without sending it, as in "
            "to_hive(drop_table(t)). It takes what create_table, drop_table or statement(...) "
            "builds, not text.",
            error=ValueError,
        )
    columns, rows = edition.run_query(text, _TABLES)
    if not _sorts_itself(text):
        rows = sorted(rows, key=_in_order)
    return pd.DataFrame(rows, columns=columns)
