"""The tasks the Copilot files are measured on: what a user asks Copilot, and the right answer.

Each task is a request a sqlglot Composer user types into Copilot's web chat, the context
Copilot needs (the Table references the user's Project has), and a reference answer: the
Python a careful user would write, which `tools/copilot_eval.py` runs the same way it runs a
model's answer, on the Example database, to score the model's against it.

There are three tasks for each of the ten objectives of the Copilot files (`01` to `10`, as
`copilot/00_start_here.txt` lists them): two on the dev split, which the files may be tuned on,
and one held out, scored once per version of the files. Six are traps, where the answer most
people write first is refused by a Guard or a Load limit.

A task's kind says what its answer gives and how it is checked:

- read, convert, fix: a Statement `s`, whose rows on the Example database must be the
  reference's;
- hive: a Statement `s`, whose Hive must be the reference's, as compare_hive compares them,
  for what the Example database can't run, such as subtotals;
- write: a Statement `s` that writes a Saved table, writing the reference's rows into the same
  table the same way;
- logic: a Table notebook's logic cell, whose create() makes the table and write() writes the
  reference's rows;
- table: a Table reference `t`, with the reference's name, columns, partitions, Key and
  location;
- verdict: a Verdict `v`, from a check, that holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The objectives, by the number of the Copilot file that serves each.
OBJECTIVES = {
    "01": "imports and the Project",
    "02": "Table references",
    "03": "building a Statement",
    "04": "joins",
    "05": "windows and subtotals",
    "06": "saving a table",
    "07": "converting Hive",
    "08": "checking and comparing",
    "09": "fixing a refusal",
    "10": "hand-written Hive and other functions",
}

# What the answer must assign, by kind.
GIVES = {"read": "s", "convert": "s", "fix": "s", "hive": "s", "write": "s", "logic": "write()",
         "table": "t", "verdict": "v"}

# The Saved table the writing tasks write, as the user's Project describes it.
JOB_DAY_RUNS = '''from sqlglot_composer import Table

job_day_runs = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)
'''


@dataclass(frozen=True)
class Task:
    """One request to Copilot, with the context it needs and the right answer."""

    id: str
    objective: str
    split: str  # "dev" or "held_out"
    request: str
    kind: str
    reference: str
    tables: tuple[str, ...] = ()  # the Example database's tables the Project has, by name
    saved: dict[str, str] = field(default_factory=dict)  # mart Table references, by name
    trap: bool = False
    runs_it: bool = False  # the request asks to run it with query
    partition: dict[str, str] | None = None  # for comparing a write's rows


TASKS = (
    # --- 01 imports and the Project ---------------------------------------------------------
    Task("T01", "01", "dev",
         "Read each job's name and team from ops.jobs, and run it with my query. Import "
         "everything you use.",
         "read", '''from sqlglot_composer import FROM, SELECT, run_query, statement
from references.ops__jobs import jobs
from warehouse import query

s = statement(SELECT(jobs.job_name, jobs.team), FROM(jobs))
rows = run_query(s, query)
''', tables=("jobs",), runs_it=True),
    Task("T02", "01", "dev",
         "Using my Database module (from references import ops), list the run_id and status "
         "of each run in ops.job_runs on 2026-09-24.",
         "read", '''from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references import ops

s = statement(
    SELECT(ops.job_runs.run_id, ops.job_runs.status),
    FROM(ops.job_runs),
    WHERE(equals(ops.job_runs.dt, "2026-09-24")),
)
''', tables=("job_runs",)),
    Task("T03", "01", "held_out",
         "Count the alerts in ops.run_alerts on 2026-09-24 for each severity, as columns "
         "severity and alerts, and run it with my query.",
         "read", '''from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, run_query, statement
from references.ops__run_alerts import run_alerts
from warehouse import query

s = statement(
    SELECT(run_alerts.severity, AS(count_rows(), "alerts")),
    FROM(run_alerts),
    WHERE(equals(run_alerts.dt, "2026-09-24")),
    GROUP_BY(run_alerts.severity),
)
rows = run_query(s, query)
''', tables=("run_alerts",), runs_it=True),
    # --- 02 Table references ----------------------------------------------------------------
    Task("T04", "02", "dev",
         "Write the Table reference for a new Saved table, mart.job_day_runs: columns job_id "
         "bigint, runs bigint and dt string; partitioned by dt; its Key is job_id and dt; "
         "stored at /data/your_team/mart.db/job_day_runs.",
         "table", '''from sqlglot_composer import Table

t = Table(
    "mart.job_day_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_runs",
)
'''),
    Task("T05", "02", "dev",
         "Check, with my query, that ops.job_runs's Key holds on 2026-09-24.",
         "verdict", '''from sqlglot_composer import check_key, equals
from references.ops__job_runs import job_runs
from warehouse import query

v = check_key(job_runs, query=query, where=equals(job_runs.dt, "2026-09-24"))
''', tables=("job_runs",)),
    Task("T06", "02", "held_out",
         "Write the Table reference for a new Saved table, mart.team_alerts: columns team "
         "string, alerts bigint, high_share double and dt string; partitioned by dt; its Key "
         "is team and dt; stored at /data/your_team/mart.db/team_alerts. high_share is a "
         "share of a day's alerts, so it must never be added up.",
         "table", '''from sqlglot_composer import Table

t = Table(
    "mart.team_alerts",
    columns={"team": "string", "alerts": "bigint", "high_share": "double", "dt": "string"},
    partitioned_by=["dt"],
    key=["team", "dt"],
    does_not_add_up=["high_share"],
    location="/data/your_team/mart.db/team_alerts",
)
'''),
    # --- 03 building a Statement ------------------------------------------------------------
    Task("T07", "03", "dev",
         "The failed runs (status FAILED) in ops.job_runs from 2026-09-23 to 2026-09-24: "
         "run_id, job_id and duration_mins.",
         "read", '''from sqlglot_composer import FROM, SELECT, WHERE, between, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"), equals(job_runs.status, "FAILED")),
)
''', tables=("job_runs",)),
    Task("T08", "03", "dev",
         "The total minutes of each job's runs over every day ops.job_runs holds, all of "
         "them: job_id and minutes.",
         "read", '''from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, statement, sum_of
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
    FROM(job_runs, reads_all_partitions=True),
    GROUP_BY(job_runs.job_id),
)
''', tables=("job_runs",), trap=True),
    Task("T09", "03", "held_out",
         "The jobs whose runs from 2026-09-23 to 2026-09-24 took more than 15 minutes on "
         "average: job_id and avg_minutes.",
         "read", '''from sqlglot_composer import AS, FROM, GROUP_BY, HAVING, SELECT, WHERE, average_of, between, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.job_id, AS(average_of(job_runs.duration_mins), "avg_minutes")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(job_runs.job_id),
    HAVING(more_than(average_of(job_runs.duration_mins), 15)),
)
''', tables=("job_runs",)),
    # --- 04 joins ---------------------------------------------------------------------------
    Task("T10", "04", "dev",
         "Each run in ops.job_runs on 2026-09-24 with its job's name from ops.jobs: run_id, "
         "job_name and status.",
         "read", '''from sqlglot_composer import FROM, JOIN, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(job_runs.run_id, jobs.job_name, job_runs.status),
    FROM(job_runs),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
''', tables=("job_runs", "jobs")),
    Task("T11", "04", "dev",
         "Every job in ops.jobs with how many runs it had in ops.job_runs on 2026-09-24, 0 for "
         "a job with none: job_id, job_name and runs.",
         "read", '''from sqlglot_composer import AS, FROM, GROUP_BY, LEFT_JOIN, SELECT, all_of, count_distinct, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, jobs.job_name, AS(count_distinct(job_runs.run_id), "runs")),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                  equals(job_runs.dt, "2026-09-24"))),
    GROUP_BY(jobs.job_id, jobs.job_name),
)
''', tables=("jobs", "job_runs"), trap=True),
    Task("T12", "04", "held_out",
         "The high-severity alerts in ops.run_alerts on 2026-09-24, each with the name of the "
         "job whose run raised it (ops.job_runs gives the run's job, ops.jobs the job's name): "
         "alert_id and job_name.",
         "read", '''from sqlglot_composer import FROM, JOIN, SELECT, WHERE, all_of, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs
from references.ops__run_alerts import run_alerts

s = statement(
    SELECT(run_alerts.alert_id, jobs.job_name),
    FROM(run_alerts),
    JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
    JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
    WHERE(equals(run_alerts.dt, "2026-09-24"), equals(job_runs.dt, "2026-09-24"),
          equals(run_alerts.severity, "high")),
)
''', tables=("run_alerts", "job_runs", "jobs"), trap=True),
    # --- 05 windows and subtotals -----------------------------------------------------------
    Task("T13", "05", "dev",
         "Each job's longest run in ops.job_runs from 2026-09-23 to 2026-09-24, one row per "
         "job, the smallest run_id on a tie: job_id, run_id and duration_mins.",
         "read", '''from sqlglot_composer import AS, FROM, SELECT, WHERE, between, derived, descending, equals, row_number, statement
from references.ops__job_runs import job_runs

numbered = derived("numbered", statement(
    SELECT(job_runs.job_id, job_runs.run_id, job_runs.duration_mins,
           AS(row_number(PARTITION_BY=job_runs.job_id,
                         ORDER_BY=[descending(job_runs.duration_mins), job_runs.run_id]),
              "longest_first")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
))
s = statement(
    SELECT(numbered.job_id, numbered.run_id, numbered.duration_mins),
    FROM(numbered),
    WHERE(equals(numbered.longest_first, 1)),
)
''', tables=("job_runs",)),
    Task("T14", "05", "dev",
         "The runs in ops.job_runs on each day from 2026-09-23 to 2026-09-24, with a total "
         "row for both days: dt and runs.",
         "hive", '''from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, between, count_rows, rollup, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.dt, AS(count_rows(), "runs")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    GROUP_BY(rollup(job_runs.dt)),
)
''', tables=("job_runs",)),
    Task("T15", "05", "held_out",
         "For each run in ops.job_runs from 2026-09-23 to 2026-09-24, the minutes of the same "
         "job's run before it, by run_id: run_id, job_id, duration_mins and minutes_before.",
         "read", '''from sqlglot_composer import AS, FROM, SELECT, WHERE, between, lag, statement, window
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins,
           AS(lag(job_runs.duration_mins,
                  over=window(PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)),
              "minutes_before")),
    FROM(job_runs),
    WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
)
''', tables=("job_runs",)),
    # --- 06 saving a table ------------------------------------------------------------------
    Task("T16", "06", "dev",
         "Write each job's number of runs in ops.job_runs on 2026-09-24 into my Saved table "
         "mart.job_day_runs (from references.mart__job_day_runs import job_day_runs), "
         "replacing what that day held.",
         "write", '''from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, count_rows, equals, statement
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_OVERWRITE(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
''', tables=("job_runs",), saved={"job_day_runs": JOB_DAY_RUNS},
         partition={"dt": "2026-09-24"}),
    Task("T17", "06", "dev",
         "Write the logic cell of mart.job_day_runs's Table notebook (from "
         "references.mart__job_day_runs import job_day_runs): create(), which makes the "
         "table; rows(day), the clauses that count each job's runs in ops.job_runs on that "
         "day; preview(), which reads them for DAY = \"2026-09-24\"; and write(), which "
         "replaces DAY's rows.",
         "logic", '''from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, count_rows, create_table, equals, statement
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

DAY = "2026-09-24"


def create() -> Statement:
    return create_table(job_day_runs, may_exist=True)


def rows(day: str) -> list[Clause]:
    return [
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, day)),
        GROUP_BY(job_runs.job_id, job_runs.dt),
    ]


def preview() -> Statement:
    return statement(*rows(DAY))


def write() -> Statement:
    return statement(INSERT_OVERWRITE(job_day_runs), *rows(DAY))
''', tables=("job_runs",), saved={"job_day_runs": JOB_DAY_RUNS},
         partition={"dt": "2026-09-24"}),
    Task("T18", "06", "held_out",
         "Add each job's number of runs in ops.job_runs on 2026-09-23 to my Saved table "
         "mart.job_day_runs (from references.mart__job_day_runs import job_day_runs), keeping "
         "what it already holds.",
         "write", '''from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_INTO, SELECT, WHERE, count_rows, equals, statement
from references.mart__job_day_runs import job_day_runs
from references.ops__job_runs import job_runs

s = statement(
    INSERT_INTO(job_day_runs),
    SELECT(job_runs.job_id, AS(count_rows(), "runs"), job_runs.dt),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-23")),
    GROUP_BY(job_runs.job_id, job_runs.dt),
)
''', tables=("job_runs",), saved={"job_day_runs": JOB_DAY_RUNS},
         partition={"dt": "2026-09-23"}),
    # --- 07 converting Hive -----------------------------------------------------------------
    Task("T19", "07", "dev",
         "Convert this Hive into Toolbox code:\n\n"
         "SELECT r.job_id, COUNT(*) AS runs\n"
         "FROM ops.job_runs r\n"
         "WHERE r.dt = '2026-09-24' AND r.status IN ('FAILED', 'SUCCESS', 'RETRY', 'TEST')\n"
         "GROUP BY r.job_id",
         "convert", '''from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, count_rows, equals, is_in, statement
from references.ops__job_runs import job_runs

STATUS_VALUES = ["FAILED", "SUCCESS", "RETRY", "TEST"]

r = AS(job_runs, "r")
s = statement(
    SELECT(r.job_id, AS(count_rows(), "runs")),
    FROM(r),
    WHERE(equals(r.dt, "2026-09-24"), is_in(r.status, STATUS_VALUES)),
    GROUP_BY(r.job_id),
)
''', tables=("job_runs",)),
    Task("T20", "07", "dev",
         "Convert this Hive into Toolbox code:\n\n"
         "WITH ev AS (\n"
         "  SELECT e.job_id, e.event_type\n"
         "  FROM ops.job_events e\n"
         "  WHERE e.dt BETWEEN '2026-09-20' AND '2026-09-24'\n"
         ")\n"
         "SELECT ev.job_id, SUM(CASE WHEN ev.event_type = 'finish' THEN 1 ELSE 0 END) AS finishes\n"
         "FROM ev\n"
         "GROUP BY ev.job_id",
         "convert", '''from sqlglot_composer import AS, FROM, GROUP_BY, SELECT, WHERE, between, derived, equals, if_else, statement, sum_of
from references.ops__job_events import job_events

e = AS(job_events, "e")
ev = derived("ev", statement(
    SELECT(e.job_id, e.event_type),
    FROM(e),
    WHERE(between(e.dt, "2026-09-20", "2026-09-24")),
))
s = statement(
    SELECT(ev.job_id, AS(sum_of(if_else(equals(ev.event_type, "finish"), 1, 0)), "finishes")),
    FROM(ev),
    GROUP_BY(ev.job_id),
)
''', tables=("job_events",)),
    Task("T21", "07", "held_out",
         "Convert this Hive into Toolbox code:\n\n"
         "SELECT j.job_name,\n"
         "       CASE j.team WHEN 'data' THEN 'Data' WHEN 'web' THEN 'Web' ELSE 'Other' END AS team_name,\n"
         "       r.run_id\n"
         "FROM ops.jobs j\n"
         "LEFT JOIN ops.job_runs r ON r.job_id = j.job_id AND r.dt = '2026-09-24'",
         "convert", '''from sqlglot_composer import AS, FROM, LEFT_JOIN, SELECT, all_of, equals, mapped, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

TEAM_NAME_BY_TEAM = {"data": "Data", "web": "Web"}

j = AS(jobs, "j")
r = AS(job_runs, "r")
s = statement(
    SELECT(j.job_name, AS(mapped(j.team, TEAM_NAME_BY_TEAM, otherwise="Other"), "team_name"),
           r.run_id),
    FROM(j),
    LEFT_JOIN(r, ON=all_of(equals(r.job_id, j.job_id), equals(r.dt, "2026-09-24"))),
)
''', tables=("jobs", "job_runs")),
    # --- 08 checking and comparing ----------------------------------------------------------
    Task("T22", "08", "dev",
         "My team's Hive was\n\n"
         "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'\n\n"
         "and my Statement is\n\n"
         "s0 = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),\n"
         "               WHERE(equals(job_runs.dt, \"2026-09-24\")))\n\n"
         "Check, with my query, that the two give the same rows on 2026-09-24.",
         "verdict", '''from sqlglot_composer import FROM, SELECT, WHERE, compare_with_original, equals, statement
from references.ops__job_runs import job_runs
from warehouse import query

HIVE = "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'"
s0 = statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
               WHERE(equals(job_runs.dt, "2026-09-24")))
v = compare_with_original(s0, HIVE, query=query, partition={"dt": "2026-09-24"})
''', tables=("job_runs",)),
    Task("T23", "08", "dev",
         "My team's Hive was\n\n"
         "select r.job_id, r.job_name from ops.jobs r -- every job\n\n"
         "and my Statement is s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs)). "
         "Check that its Hive is the same query, without running anything.",
         "verdict", '''from sqlglot_composer import FROM, SELECT, compare_hive, statement
from references.ops__jobs import jobs

s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))
v = compare_hive(s0, "select r.job_id, r.job_name from ops.jobs r -- every job")
''', tables=("jobs",)),
    Task("T24", "08", "held_out",
         "Check, with my query, that ops.job_owners's Key holds from 2026-09-20 to 2026-09-24.",
         "verdict", '''from sqlglot_composer import between, check_key
from references.ops__job_owners import job_owners
from warehouse import query

v = check_key(job_owners, query=query, where=between(job_owners.dt, "2026-09-20", "2026-09-24"))
''', tables=("job_owners",)),
    # --- 09 fixing a refusal ----------------------------------------------------------------
    Task("T25", "09", "dev",
         "I want the failed runs on 2026-09-24, but\n\n"
         "s = statement(SELECT(job_runs.run_id), FROM(job_runs),\n"
         "              WHERE(job_runs.status == \"FAILED\"))\n\n"
         "stops with:\n\n"
         "TypeError:\n"
         "  What happened:  A column was used with Python's ==.\n"
         "  Usual fix:      Use equals(column, value).\n\n"
         "Fix it.",
         "fix", '''from sqlglot_composer import FROM, SELECT, WHERE, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
)
''', tables=("job_runs",), trap=True),
    Task("T26", "09", "dev",
         "I want the 3 longest runs on 2026-09-24, longest first, but\n\n"
         "s = statement(SELECT(job_runs.run_id, job_runs.duration_mins), FROM(job_runs),\n"
         "              WHERE(equals(job_runs.dt, \"2026-09-24\")),\n"
         "              ORDER_BY(descending(job_runs.duration_mins)))\n\n"
         "stops with:\n\n"
         "LoadRefused:\n"
         "  What happened:  ORDER_BY has no LIMIT.\n"
         "  Usual fix:      Sort in pandas after run_query(...), with df.sort_values(...). For "
         "a top N, add LIMIT(n).\n\n"
         "Fix it.",
         "fix", '''from sqlglot_composer import FROM, LIMIT, ORDER_BY, SELECT, WHERE, descending, equals, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id, job_runs.duration_mins),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
    ORDER_BY(descending(job_runs.duration_mins)),
    LIMIT(3),
)
''', tables=("job_runs",), trap=True),
    Task("T27", "09", "held_out",
         "I want every job with its runs on 2026-09-24, a job with none kept once, but\n\n"
         "s = statement(SELECT(jobs.job_id, job_runs.run_id), FROM(jobs),\n"
         "              LEFT_JOIN(job_runs, ON=equals(job_runs.job_id, jobs.job_id)),\n"
         "              WHERE(equals(job_runs.dt, \"2026-09-24\")))\n\n"
         "stops with:\n\n"
         "GuardRefused:\n"
         "  What happened:  WHERE has job_runs.dt = '2026-09-24', a condition on job_runs, "
         "which LEFT_JOIN brought in.\n"
         "  Usual fix:      Move the condition into LEFT_JOIN(job_runs, ON=...), next to the "
         "join condition, so it only decides which rows match.\n\n"
         "Fix it.",
         "fix", '''from sqlglot_composer import FROM, LEFT_JOIN, SELECT, all_of, equals, statement
from references.ops__job_runs import job_runs
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, job_runs.run_id),
    FROM(jobs),
    LEFT_JOIN(job_runs, ON=all_of(equals(job_runs.job_id, jobs.job_id),
                                  equals(job_runs.dt, "2026-09-24"))),
)
''', tables=("jobs", "job_runs"), trap=True),
    # --- 10 hand-written Hive and other functions -------------------------------------------
    Task("T28", "10", "dev",
         "Each job in ops.jobs with a label for its team: data is \"Data platform\", finance "
         "is \"Finance\", any other team \"Other\": job_id and team_label.",
         "read", '''from sqlglot_composer import AS, FROM, SELECT, mapped, statement
from references.ops__jobs import jobs

s = statement(
    SELECT(jobs.job_id, AS(mapped(jobs.team, {"data": "Data platform", "finance": "Finance"},
                                  otherwise="Other"), "team_label")),
    FROM(jobs),
)
''', tables=("jobs",)),
    Task("T29", "10", "dev",
         "Each job in ops.jobs with its name in capitals, using Hive's upper function: job_id "
         "and name_upper.",
         "read", '''from sqlglot_composer import AS, FROM, SELECT, hive_function, statement
from references.ops__jobs import jobs

s = statement(SELECT(jobs.job_id, AS(hive_function("upper", jobs.job_name), "name_upper")),
              FROM(jobs))
''', tables=("jobs",)),
    Task("T30", "10", "held_out",
         "Label each run in ops.job_runs on 2026-09-24: \"failed\" when its status is FAILED, "
         "else \"slow\" when it took more than 25 minutes, else \"ok\": run_id and label.",
         "read", '''from sqlglot_composer import AS, FROM, SELECT, WHERE, equals, first_match, more_than, statement
from references.ops__job_runs import job_runs

s = statement(
    SELECT(job_runs.run_id,
           AS(first_match([(equals(job_runs.status, "FAILED"), "failed"),
                           (more_than(job_runs.duration_mins, 25), "slow")],
                          otherwise="ok"), "label")),
    FROM(job_runs),
    WHERE(equals(job_runs.dt, "2026-09-24")),
)
''', tables=("job_runs",)),
)

BY_ID = {task.id: task for task in TASKS}
