"""The usability loop's scenarios, built into `tools/usability_scenarios/` (Toolbox 8.2, ticket
03; the map's Notes, "The loop").

    python tools/usability_scenario_files.py

Each scenario's folder holds `scenario.json`, the files it gives the user, the Hive its team's
warehouse ran already, any presentation workbook (the user's own view, for an Excel scenario),
and `key.json`, its answer key. A Workflow scenario's key comes from the warehouse itself: the
rows the original Hive wrote, or an independent query's, never the Toolbox's own conversion. An
Excel scenario's key is computed here in Python from the workbook's raw rows, as its formulas
compute them. `reference_end` reaches each scenario's end with the Toolbox, in a prepared run,
and `tests/journeys/test_usability_scenarios.py` holds that end to the key: so a key never asks
for what the Toolbox can't do, and each scenario is also a test of what the Toolbox says it
does, an Excel one of the SQL each formula maps to.
"""

from __future__ import annotations

import contextlib
import json
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
from openpyxl.worksheet.table import Table as ExcelTable

TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(TOOLS.parent)]

import usability_loop  # noqa: E402
from how_to_page import project_on_the_path, times_pinned  # noqa: E402
from workflow_warehouse import SavedWarehouse  # noqa: E402

from sqlglot_composer import TOOLBOX_VERSION, admin, equals, example_database, project  # noqa: E402
from sqlglot_composer import notebooks, run_execute  # noqa: E402

FOLDER = usability_loop.SCENARIOS
DEV, PROD = "mart_dev", "team_prod"
# Where a converted table's compare with its original is written.
COMPARED = "tables/{stem}/conversion/compare.md"


def location(table: str) -> str:
    """A table's folder, as each scenario's job gives it."""
    database, name = table.split(".")
    return f"/data/team/{database}.db/{name}"


DATABASES_SAID = (f"Your Dev Database is {DEV}, and your Prod Database is {PROD}. Each new "
                  "table you make goes in the folder /data/team/<its database>.db/<its name>, "
                  "such as /data/team/mart_dev.db/weekly; a table someone else made stays "
                  "where it is.")

# --- The Hive the scenarios give -------------------------------------------------------------

ONE_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
WITH f AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED')
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS fails, f.dt
FROM f JOIN ops.job_owners o ON f.job_id = o.job_id
GROUP BY o.team, f.dt;
"""
LONG_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_runs_counted (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_fails_counted (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TEMPORARY TABLE failed_runs AS
SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED';
WITH owned AS (SELECT o.job_id, o.team FROM ops.job_owners o)
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT w.team AS team, COUNT(*) AS fails, f.dt
FROM failed_runs f JOIN owned w ON f.job_id = w.job_id
GROUP BY w.team, f.dt;
FROM ops.job_runs r
INSERT OVERWRITE TABLE mart.job_runs_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS runs, r.dt GROUP BY r.job_id, r.dt
INSERT OVERWRITE TABLE mart.job_fails_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS fails, r.dt WHERE r.status = 'FAILED' GROUP BY r.job_id, r.dt;
DROP TABLE IF EXISTS failed_runs;
"""
# Toolbox 8.3: a script holding Script tags, as the user's scheduler keeps it, and as it ran,
# each tag filled in: RUN_DAY bare, SKIP_TEAM inside quotes.
TAGGED_SCRIPT = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS fails, r.dt
FROM ops.job_runs r JOIN ops.job_owners o ON r.job_id = o.job_id
WHERE r.status = 'FAILED' AND r.dt = <PARM="RUN_DAY"/> AND o.team <> '<PARM="SKIP_TEAM"/>'
GROUP BY o.team, r.dt;
"""
TAGGED_SCRIPT_RAN = (TAGGED_SCRIPT.replace('<PARM="RUN_DAY"/>', "'2026-09-24'")
                     .replace('<PARM="SKIP_TEAM"/>', "data"))
FAILED_RUNS = """SELECT r.job_id, COUNT(*) AS fails
FROM ops.job_runs r
WHERE r.status = 'FAILED'
GROUP BY r.job_id
"""
RUNS_PER_DAY = ("SELECT job_id, COUNT(*) AS runs, dt FROM ops.job_runs "
                "WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY job_id, dt")

# --- Keys, from the warehouse ----------------------------------------------------------------


def warehouse_rows(hive_ran: list[str], query: str) -> tuple[list[str], list[list[object]]]:
    """The columns and rows of `query`, in a warehouse that has run `hive_ran`."""
    with tempfile.TemporaryDirectory() as temporary:
        warehouse = SavedWarehouse(Path(temporary) / "warehouse.json")
        for hive in hive_ran:
            warehouse.execute(hive)
        found = warehouse.query(query)
    rows = []
    for row in found.itertuples(index=False):
        rows.append([value.item() if hasattr(value, "item") else value for value in row])
    return [str(column) for column in found.columns], rows


def table_key(hive_ran: list[str], query: str) -> dict[str, object]:
    """A key's table: the columns and rows `query` gives, in a warehouse that ran `hive_ran`."""
    columns, rows = warehouse_rows(hive_ran, query)
    return {"columns": columns, "rows": rows}


# --- Excel: presentation workbooks and their keys ---------------------------------------------


def example_rows(name: str) -> tuple[list[str], list[list[object]]]:
    """An Example database table's columns and rows, as a sample pasted into a workbook."""
    found = example_database.query(f"SELECT * FROM ops.{name}")
    rows = []
    for row in found.itertuples(index=False):
        # A NaN is an empty cell.
        rows.append([None if value != value else value for value in row])
    return list(found.columns), rows


def add_sheet(workbook: openpyxl.Workbook, title: str, header: list[str],
              rows: list[list[object]], note: str = "") -> None:
    """A sheet of a presentation workbook: its rows under a header, as plain cells, as a
    person's own workbook holds them, and a note beside them saying where they came from."""
    sheet = workbook.create_sheet(title)
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    if note:
        sheet.cell(row=1, column=len(header) + 2, value=note)


def run_report_workbook() -> openpyxl.Workbook:
    """E1's own view: the runs pasted on one sheet, and a Report of formulas over them."""
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    header, rows = example_rows("job_runs")
    add_sheet(workbook, "Runs", header, rows, "Copied from ops.job_runs in our warehouse.")
    report = [[job, f"=COUNTIFS(Runs!$B:$B,A{line})",
               f'=COUNTIFS(Runs!$B:$B,A{line},Runs!$C:$C,"FAILED")',
               f"=AVERAGEIFS(Runs!$D:$D,Runs!$B:$B,A{line})"]
              for line, job in enumerate((1, 2, 3), 2)]
    add_sheet(workbook, "Report", ["job_id", "runs", "failed_runs", "avg_duration_mins"],
              report, "One row per job: its runs, how many failed, its average minutes.")
    return workbook


def run_report_key() -> dict[str, object]:
    """E1's Report, as its formulas compute it from the runs."""
    _, rows = example_rows("job_runs")
    report = []
    for job in (1, 2, 3):
        mine = [row for row in rows if row[1] == job]
        failed = [row for row in mine if row[2] == "FAILED"]
        report.append([job, len(mine), len(failed), sum(row[3] for row in mine) / len(mine)])
    return {"columns": ["job_id", "runs", "failed_runs", "avg_duration_mins"], "rows": report}


def team_report_workbook() -> openpyxl.Workbook:
    """E2's own view: the jobs and the runs on two sheets, each run's team looked up, and a
    summary per team."""
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    header, rows = example_rows("jobs")
    add_sheet(workbook, "Jobs", header, rows, "Copied from ops.jobs in our warehouse.")
    header, rows = example_rows("job_runs")
    looked_up = [[*row, f"=VLOOKUP(B{line},Jobs!$A:$C,3,FALSE)"]
                 for line, row in enumerate(rows, 2)]
    add_sheet(workbook, "Runs", [*header, "team"], looked_up,
              "Copied from ops.job_runs in our warehouse; team looked up from Jobs.")
    teams = [[team, f"=COUNTIF(Runs!$G:$G,A{line})", f"=SUMIF(Runs!$G:$G,A{line},Runs!$D:$D)"]
             for line, team in enumerate(("data", "finance", "web"), 2)]
    add_sheet(workbook, "Teams", ["team", "runs", "total_duration_mins"], teams,
              "One row per team: its runs, and their minutes added up.")
    return workbook


def team_report_key() -> dict[str, object]:
    """E2's summary per team, as its formulas compute it."""
    _, jobs = example_rows("jobs")
    _, runs = example_rows("job_runs")
    team_of = {job[0]: job[2] for job in jobs}
    summary = []
    for team in ("data", "finance", "web"):
        mine = [run for run in runs if team_of[run[1]] == team]
        summary.append([team, len(mine), sum(run[3] for run in mine)])
    return {"columns": ["team", "runs", "total_duration_mins"], "rows": summary}


CLEAN_RUNS_M = """let
    Source = Excel.CurrentWorkbook(){[Name="Raw"]}[Content],
    Typed = Table.TransformColumnTypes(Source, {{"run_id", Int64.Type}, {"job_id", Int64.Type},
        {"status", type text}, {"duration_mins", Int64.Type}, {"dt", type text}}),
    Kept = Table.SelectRows(Typed, each [status] <> null and [status] <> "TEST")
in
    Kept"""


def daily_runs_workbook() -> openpyxl.Workbook:
    """E3's own view: the raw runs, a Power Query that cleans them into a Clean sheet (its M
    code on a sheet of its own, as the file holds it), and a Daily summary with a Total Row."""
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    header, rows = example_rows("job_runs")
    add_sheet(workbook, "Raw", header, rows, "Copied from ops.job_runs in our warehouse.")
    clean = [row for row in rows if row[2] is not None and row[2] != "TEST"]
    add_sheet(workbook, "Clean", header, clean,
              'Loaded by the Power Query "CleanRuns" from Raw: runs with no status, and test '
              "runs, left out.")
    cleaned = ExcelTable(displayName="CleanRuns", ref=f"A1:F{len(clean) + 1}")
    workbook["Clean"].add_table(cleaned)
    sheet = workbook.create_sheet("Power Query CleanRuns")
    sheet["A1"] = 'Power Query "CleanRuns", loading into the Table CleanRuns on Clean:'
    for line, text in enumerate(CLEAN_RUNS_M.splitlines(), 2):
        sheet.cell(row=line, column=1, value=text)
    days = [[day, f'=COUNTIFS(CleanRuns[dt],A{line})',
             f'=SUMIFS(CleanRuns[duration_mins],CleanRuns[dt],A{line})']
            for line, day in enumerate(("2026-09-23", "2026-09-24"), 2)]
    days.append(["Total", "=SUBTOTAL(109,B2:B3)", "=SUBTOTAL(109,C2:C3)"])
    add_sheet(workbook, "Daily", ["dt", "runs", "total_duration_mins"], days,
              "One row per day of the clean runs, and a Total Row.")
    return workbook


def daily_runs_key() -> dict[str, object]:
    """E3's Daily summary of the clean runs, a row per day. Its Total Row isn't saved: the
    Toolbox refuses a subtotal row in a Saved table, whose sums would count each row twice, so
    a Statement that reads the table adds it."""
    _, rows = example_rows("job_runs")
    clean = [row for row in rows if row[2] is not None and row[2] != "TEST"]
    summary = []
    for day in ("2026-09-23", "2026-09-24"):
        mine = [row for row in clean if row[5] == day]
        summary.append([day, len(mine), sum(row[3] for row in mine)])
    return {"columns": ["dt", "runs", "total_duration_mins"], "rows": summary}


CENTS_A_MINUTE = 50
TYPED_JOB = 3
# Job 3's cost, typed over its formula in the user's own workbook.
TYPED_OVER = {TYPED_JOB: 1000}


def costs_workbook() -> openpyxl.Workbook:
    """E4's own view: the jobs and runs, a rate typed in a cell, each job's cost (one typed
    over its formula), and the runs per team: two final summaries, on sheets of their own."""
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    header, rows = example_rows("jobs")
    add_sheet(workbook, "Jobs", header, rows, "Copied from ops.jobs in our warehouse.")
    header, rows = example_rows("job_runs")
    add_sheet(workbook, "Runs", header, rows, "Copied from ops.job_runs in our warehouse.")
    sheet = workbook.create_sheet("Rate")
    sheet["A1"], sheet["B1"] = "cents a minute", CENTS_A_MINUTE
    costs = []
    for line, job in enumerate((1, 2, 3, 4), 2):
        formula = f"=SUMIF(Runs!$B:$B,A{line},Runs!$D:$D)*Rate!$B$1"
        costs.append([job, TYPED_OVER.get(job, formula)])
    add_sheet(workbook, "Job costs", ["job_id", "cost_cents"], costs,
              "Each job's minutes times the rate; job 3's was typed in by hand, as agreed.")
    # Each of the team's jobs' runs, counted: the runs whose job's team is this one.
    teams = [[team, f"=SUMPRODUCT((Jobs!$C$2:$C$5=A{line})"
                    "*COUNTIF(Runs!$B:$B,Jobs!$A$2:$A$5))"]
             for line, team in enumerate(("data", "finance", "web"), 2)]
    add_sheet(workbook, "Team runs", ["team", "runs"], teams, "How many runs each team had.")
    return workbook


def costs_key() -> dict[str, dict[str, object]]:
    """E4's two summaries, as the workbook computes them, job 3's cost as typed."""
    _, jobs = example_rows("jobs")
    _, runs = example_rows("job_runs")
    costs = []
    for job in (1, 2, 3, 4):
        minutes = sum(run[3] for run in runs if run[1] == job)
        costs.append([job, TYPED_OVER.get(job, minutes * CENTS_A_MINUTE)])
    team_of = {job[0]: job[2] for job in jobs}
    teams = []
    for team in ("data", "finance", "web"):
        teams.append([team, len([run for run in runs if team_of[run[1]] == team])])
    return {f"{DEV}.job_costs": {"columns": ["job_id", "cost_cents"], "rows": costs},
            f"{DEV}.team_runs": {"columns": ["team", "runs"], "rows": teams}}


# --- The reference Hive of each Excel scenario: the SQL its formulas map to -------------------

REFERENCE_HIVE = {
    "job_run_report": """SELECT r.job_id, COUNT(*) AS runs,
       SUM(CASE WHEN r.status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
       AVG(r.duration_mins) AS avg_duration_mins
FROM ops.job_runs r
GROUP BY r.job_id
""",
    "team_report": """SELECT j.team, COUNT(r.run_id) AS runs,
       COALESCE(SUM(r.duration_mins), 0) AS total_duration_mins
FROM ops.jobs j
LEFT JOIN ops.job_runs r ON r.job_id = j.job_id
GROUP BY j.team
""",
    "daily_runs": """SELECT r.dt, COUNT(*) AS runs, SUM(r.duration_mins) AS total_duration_mins
FROM ops.job_runs r
WHERE r.status IS NOT NULL AND r.status <> 'TEST'
GROUP BY r.dt
""",
    "job_costs": f"""SELECT j.job_id,
       CASE WHEN j.job_id = {TYPED_JOB} THEN {TYPED_OVER[TYPED_JOB]}
            ELSE COALESCE(SUM(r.duration_mins), 0) * {CENTS_A_MINUTE} END AS cost_cents
FROM ops.jobs j
LEFT JOIN ops.job_runs r ON r.job_id = j.job_id
GROUP BY j.job_id
""",
    "team_runs": """SELECT j.team, COUNT(r.run_id) AS runs
FROM ops.jobs j
LEFT JOIN ops.job_runs r ON r.job_id = j.job_id
GROUP BY j.team
""",
}

# W7's script: each new run of ops.job_runs added to mart.run_log, PERIOD_END the latest day
# the scheduler finds; and as it ran, the day filled in.
RUN_LOG = """SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.run_log (run_id BIGINT, job_id BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.run_log PARTITION (dt)
SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs r
WHERE r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 1) AND <PARM="PERIOD_END"/>
  AND r.run_id NOT IN (SELECT l.run_id FROM mart.run_log l);
"""
RUN_LOG_RAN = RUN_LOG.replace('<PARM="PERIOD_END"/>', "'2026-09-24'")

# --- The scenarios ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Built:
    """One scenario as built: its scenario.json, its files, its key, and its reference end."""

    held: dict[str, object]
    files: dict[str, str] = field(default_factory=dict)  # text files, by name
    workbooks: dict[str, Callable[[], openpyxl.Workbook]] = field(default_factory=dict)
    key: Callable[[], dict[str, object]] = dict


def technical(job: str) -> dict[str, str]:
    return {"role": "technical", "job": job}


def excel_phases(book: str, final: str, tables: str) -> list[dict[str, str]]:
    """An Excel scenario's two phases: the user fills in the Formula workbook from their own,
    then a converter, fresh, makes its tables."""
    return [
        {"role": "non_technical", "job":
            f"Your manager wants {final} of your workbook from_your_team/{book} turned into a "
            "table in the company's warehouse, so the data team can keep it up to date. Get it "
            "ready for them: make a copy of the empty Formula workbook that came with the "
            "Toolbox, main/copilot/formula_workbook.xlsx, fill it in as its Steps sheet says, "
            f"and save it as my_work/{Path(book).stem}_formula.xlsx."},
        {"role": "converter", "job":
            f"Your colleague filled in a Formula workbook, my_work/{Path(book).stem}"
            "_formula.xlsx, from their own workbook. Turn it into tables of your own in your "
            f"Dev Database, written there: {tables}. Use Copilot to turn the workbook into "
            "Hive, as the workbook's Steps sheet says, then make the tables with the Toolbox, "
            f"as its README says. {DATABASES_SAID}"},
    ]


def scenarios() -> dict[str, Built]:
    """Each scenario, by its id: the Workflow ones, then the Excel ones."""
    return {**workflow_scenarios(), **new_table_scenarios(), **excel_scenarios(),
            **held_out_workflow_scenarios()}


def workflow_scenarios() -> dict[str, Built]:
    """Each Workflow scenario, by its id."""
    team_fails = f"{DEV}.team_fails"
    daily_fails = f"{DEV}.daily_fails"
    run_log = f"{DEV}.run_log"
    return {
        "W1": Built({
            "id": "W1", "split": "dev", "title": "convert one script with a CTE",
            "phases": [technical(
                "Your team's script, from_your_team/weekly_fails.hql, writes mart.team_fails, "
                "a table in a database you can't write to; it has run, so mart.team_fails "
                "holds its rows. Make your own copy of that table in your Dev Database, "
                f"{team_fails}, written there and checked against the original, with the "
                "Toolbox. "
                f"{DATABASES_SAID}")],
            "hive_ran": ["weekly_fails.hql"],
            "given": {"from_your_team/weekly_fails.hql": "weekly_fails.hql"}},
            {"weekly_fails.hql": ONE_SCRIPT},
            key=lambda: {"tables": {team_fails: table_key(
                [ONE_SCRIPT], "SELECT team, fails, dt FROM mart.team_fails")},
                "files": [{"path": COMPARED.format(stem="mart_dev__team_fails"),
                           "holds": ["Passed"]}]}),
        "W6": Built({
            "id": "W6", "split": "dev", "title": "convert a script holding Script tags",
            "phases": [technical(
                "Your team's script, from_your_team/daily_fails.hql, writes mart.daily_fails, "
                "a table in a database you can't write to. The scheduler that runs it puts a "
                'value in place of each <PARM="NAME"/> before Hive reads it: this time it put '
                "2026-09-24 for RUN_DAY and data for SKIP_TEAM, and the script has run, so "
                "mart.daily_fails holds its rows. Make your own copy of that table in your Dev "
                f"Database, {daily_fails}, written there and checked against the original, "
                f"with the Toolbox. {DATABASES_SAID}")],
            "hive_ran": ["daily_fails_ran.hql"],
            "given": {"from_your_team/daily_fails.hql": "daily_fails.hql"}},
            {"daily_fails.hql": TAGGED_SCRIPT, "daily_fails_ran.hql": TAGGED_SCRIPT_RAN},
            key=lambda: {"tables": {daily_fails: table_key(
                [TAGGED_SCRIPT_RAN], "SELECT team, fails, dt FROM mart.daily_fails")},
                "files": [{"path": COMPARED.format(stem="mart_dev__daily_fails"),
                           "holds": ["Passed"]},
                          {"path": "references/mart_dev__daily_fails.py",
                           "holds": ["'2026-09-24'"]}]}),
        "W7": Built({
            "id": "W7", "split": "dev",
            "title": "convert a script whose Script tag is the latest day, its seed limited",
            "phases": [technical(
                "Your team's script, from_your_team/run_log.hql, adds each new run of "
                "ops.job_runs to mart.run_log, a table in a database you can't write to. The "
                'scheduler that runs it puts in place of <PARM="PERIOD_END"/> the latest day '
                "ops.job_runs holds, as it stands at each run; it has run, so mart.run_log "
                f"holds its rows. Make your own copy of that table in your Dev Database, "
                f"{run_log}, written there and checked against the original, with the "
                "Toolbox. Your copy must work out PERIOD_END itself each time it is written, "
                "from what ops.job_runs holds then, never a day typed in. mart.run_log holds "
                "years of days at work, and you only need 2026-09-24 on: copy only those days "
                f"of its rows into your copy at the start. {DATABASES_SAID}")],
            "hive_ran": ["run_log_ran.hql"],
            "given": {"from_your_team/run_log.hql": "run_log.hql"}},
            {"run_log.hql": RUN_LOG, "run_log_ran.hql": RUN_LOG_RAN},
            key=lambda: {"tables": {run_log: table_key(
                [RUN_LOG_RAN], "SELECT run_id, job_id, dt FROM mart.run_log")},
                "files": [{"path": COMPARED.format(stem="mart_dev__run_log"),
                           "holds": ["Passed"]},
                          {"path": "references/mart_dev__run_log.py",
                           "holds": ["# a Run value", "2026-09-24"]}]}),
        "W4": Built({
            "id": "W4", "split": "dev", "title": "Table references",
            "phases": [technical(
                "Your work will read two tables of the warehouse, ops.jobs and ops.run_alerts. "
                "Start a Project with the Toolbox, and add a Table reference for each: the Key "
                "of ops.jobs is job_id, and of ops.run_alerts, alert_id. "
                f"{DATABASES_SAID}")]},
            key=lambda: {"files": [
                {"path": "references/ops__jobs.py", "holds": ['key=["job_id"]']},
                {"path": "references/ops__run_alerts.py", "holds": ['key=["alert_id"]']}]}),
    }


def new_table_scenarios() -> dict[str, Built]:
    """Each Workflow scenario that makes a new table of the user's own, by its id."""
    return {
        "W2": Built({
            "id": "W2", "split": "dev", "title": "a new table from its Template",
            "phases": [technical(
                f"Make a new table of your own, {DEV}.runs_per_day, with the Toolbox: one row "
                "per job and day of ops.job_runs, for 2026-09-23 and 2026-09-24, with job_id, "
                "runs (how many runs that job had that day) and dt, partitioned by dt. Write "
                f"its logic yourself, then write the table. {DATABASES_SAID}")]},
            key=lambda: {"tables": {f"{DEV}.runs_per_day": table_key([], RUNS_PER_DAY)},
                         "files": [{"path": "references/mart_dev__runs_per_day.py",
                                    "holds": [location(f"{DEV}.runs_per_day")]}]}),
        "W3": Built({
            "id": "W3", "split": "dev", "title": "a new table from a query",
            "phases": [technical(
                "Your team gave you a query, from_your_team/failed_runs.hql. Make it a table "
                f"of your own, {DEV}.failed_runs, with the Toolbox: written, and checked "
                f"against the query. {DATABASES_SAID}")],
            "given": {"from_your_team/failed_runs.hql": "failed_runs.hql"}},
            {"failed_runs.hql": FAILED_RUNS},
            key=lambda: {"tables": {f"{DEV}.failed_runs": table_key([], FAILED_RUNS)},
                         "files": [{"path": COMPARED.format(stem="mart_dev__failed_runs"),
                                    "holds": ["Passed"]}]}),
        "W5": Built({
            "id": "W5", "split": "dev", "title": "change a Saved table",
            "phases": [technical(
                f"In your team's Project, my_project, the Saved table {DEV}.runs_per_day holds "
                "the day 2026-09-24, which it shouldn't: remove that day from the table, with "
                "the Toolbox, as its guides say to change a Saved table.")],
            "start_from": "W2"},
            key=lambda: {"tables": {f"{DEV}.runs_per_day": table_key(
                [], RUNS_PER_DAY.replace("BETWEEN '2026-09-23' AND '2026-09-24'",
                                         "= '2026-09-23'"))}}),
    }


def held_out_workflow_scenarios() -> dict[str, Built]:
    """Each held-out Workflow scenario, by its id."""
    return {
        "H1": Built({
            "id": "H1", "split": "held_out", "title": "convert a long script, then promote it",
            "phases": [technical(
                "Your team's script, from_your_team/weekly.hql, writes three tables of mart, a "
                "database you can't write to; it has run, so they hold its rows. Make your own "
                "copy of each in your Dev Database, named as its original, such as "
                f"{DEV}.team_fails for mart.team_fails, written and checked against its "
                "original, then carry them to your Prod Database, written there, with the "
                "Toolbox. "
                f"{DATABASES_SAID}")],
            "hive_ran": ["weekly.hql"], "given": {"from_your_team/weekly.hql": "weekly.hql"}},
            {"weekly.hql": LONG_SCRIPT},
            key=lambda: {"tables": {
                f"{PROD}.team_fails": table_key(
                    [LONG_SCRIPT], "SELECT team, fails, dt FROM mart.team_fails"),
                f"{PROD}.job_runs_counted": table_key(
                    [LONG_SCRIPT], "SELECT job_id, runs, dt FROM mart.job_runs_counted"),
                f"{PROD}.job_fails_counted": table_key(
                    [LONG_SCRIPT], "SELECT job_id, fails, dt FROM mart.job_fails_counted")}}),
        "H2": Built({
            "id": "H2", "split": "held_out", "title": "upgrade a Project left by 8.0",
            "phases": [technical(
                "Your team's Project, my_project, was made with an older Toolbox. You have "
                "downloaded the new one, main/. Bring the Project up to date with it, every "
                f"change it asks for made. {DATABASES_SAID}")],
            "project": "tests/upgrade_from/8.0/starter"},
            key=lambda: {"files": [{"path": "admin/project_version.txt",
                                    "holds": [TOOLBOX_VERSION]},
                                   {"path": "admin/databases.py", "holds": [f'"{DEV}"']}]}),
    }


def excel_scenarios() -> dict[str, Built]:
    """Each Excel scenario, by its id."""
    return {
        "E1": Built({
            "id": "E1", "split": "dev", "title": "one sheet of raw data, with formulas",
            "phases": excel_phases("run_report.xlsx", "the Report sheet",
                                   f"{DEV}.job_run_report, from its Report"),
            "given": {"from_your_team/run_report.xlsx": "run_report.xlsx"}},
            workbooks={"run_report.xlsx": run_report_workbook},
            key=lambda: {"tables": {f"{DEV}.job_run_report": run_report_key()}}),
        "E2": Built({
            "id": "E2", "split": "dev", "title": "two data sources on two sheets, joined",
            "phases": excel_phases("team_report.xlsx", "the Teams sheet",
                                   f"{DEV}.team_report, from its Teams summary"),
            "given": {"from_your_team/team_report.xlsx": "team_report.xlsx"}},
            workbooks={"team_report.xlsx": team_report_workbook},
            key=lambda: {"tables": {f"{DEV}.team_report": team_report_key()}}),
        "E3": Built({
            "id": "E3", "split": "dev", "title": "a Power Query step and a Total Row",
            "phases": excel_phases("daily_runs.xlsx", "the Daily sheet",
                                   f"{DEV}.daily_runs, from its Daily summary"),
            "given": {"from_your_team/daily_runs.xlsx": "daily_runs.xlsx"}},
            workbooks={"daily_runs.xlsx": daily_runs_workbook},
            key=lambda: {"tables": {f"{DEV}.daily_runs": daily_runs_key()}}),
        "E4": Built({
            "id": "E4", "split": "held_out",
            "title": "two final Tables, a fixed value and a value typed over a formula",
            "phases": excel_phases("costs.xlsx", "the Job costs and Team runs sheets",
                                   f"{DEV}.job_costs and {DEV}.team_runs"),
            "given": {"from_your_team/costs.xlsx": "costs.xlsx"}},
            workbooks={"costs.xlsx": costs_workbook},
            key=lambda: {"tables": costs_key()}),
    }


# --- Reference ends ---------------------------------------------------------------------------


def start_the_project(run: Path) -> Path:
    """A Project started in run/my_project, its Databases filled in, as a user starts one."""
    root = run / "my_project"
    root.mkdir()
    with contextlib.chdir(root):
        project.start()
    fill_in_the_databases(root)
    return root


def fill_in_the_databases(root: Path) -> None:
    """A Project's admin/databases.py, DEV and PROD filled in."""
    databases = root / "admin" / "databases.py"
    text = databases.read_text(encoding="utf-8")
    text = text.replace('"<DEV_DATABASE>"', f'"{DEV}"').replace('"<PROD_DATABASE>"',
                                                                f'"{PROD}"')
    databases.write_text(text, encoding="utf-8")


def type_into(root: Path, workflow: str, **values: object) -> None:
    """Each value typed into a Workflow notebook's names or decisions cell, in place of its
    line, as a user types it, and the notebook saved."""
    notebook = root / "admin" / "workflows" / workflow / f"{workflow}.ipynb"
    for name, value in values.items():
        for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
            lines = text.split("\n")
            starts = [at for at, line in enumerate(lines) if line.startswith(f"{name} = ")]
            if starts:
                lines[starts[0]] = f"{name} = {value!r}"
                notebooks.write_cell_text(notebook, number, "\n".join(lines))
                break
        else:
            raise ValueError(f"{workflow}.ipynb has no line {name} = ... to type into")


def run_the_workflow(workflow: str, warehouse: SavedWarehouse) -> str:
    """A Workflow run by its notebook's last cell, from the notebook's folder, where it reads
    the files its names cell names, through the warehouse; what it said, as text."""
    folder = project.project_folder(Path.cwd()) / "admin" / "workflows" / workflow
    with contextlib.chdir(folder):
        said = project.run_workflow(workflow, query=warehouse.query,
                                    execute=warehouse.execute)
    return repr(said)


def add_references(root: Path, keys: dict[str, list[str]], warehouse: SavedWarehouse) -> None:
    """The references Workflow, each table's Key answered in its decisions cell."""
    type_into(root, "references", TABLES=list(keys),
              DECISIONS={table: {"key": key} for table, key in keys.items()})
    finish("references", warehouse)


def where_each_goes(tables: list[str]) -> dict[str, dict[str, object]]:
    """Each table's decisions answered with its location, as the user answers them."""
    return {table: {"location": location(table)} for table in tables}


def finish(workflow: str, warehouse: SavedWarehouse) -> None:
    """A Workflow run to its end, failing unless it says every step is done."""
    said = run_the_workflow(workflow, warehouse)
    if "every step is done" not in said:
        raise AssertionError(said)


def reference_w1(root: Path, warehouse: SavedWarehouse) -> None:
    folder = root / "admin" / "workflows" / "convert"
    shutil.copyfile(root.parent / "from_your_team" / "weekly_fails.hql",
                    folder / "weekly_fails.hql")
    table = f"{DEV}.team_fails"
    type_into(root, "convert", NAME="weekly", FILES=["weekly_fails.hql"],
              RENAME={"mart.team_fails": "team_fails"}, DECISIONS=where_each_goes([table]))
    finish("convert", warehouse)


def reference_w6(root: Path, warehouse: SavedWarehouse) -> None:
    """W6's end: the tagged script converted, each tag answered in the decisions cell with
    what the scheduler put there, a bare one with the day's own quotes."""
    folder = root / "admin" / "workflows" / "convert"
    shutil.copyfile(root.parent / "from_your_team" / "daily_fails.hql",
                    folder / "daily_fails.hql")
    table = f"{DEV}.daily_fails"
    answers = where_each_goes([table])
    answers[table]["tags"] = {"RUN_DAY": "'2026-09-24'", "SKIP_TEAM": "data"}
    type_into(root, "convert", NAME="daily", FILES=["daily_fails.hql"], DATABASE="ops",
              RENAME={"mart.daily_fails": "daily_fails"}, DECISIONS=answers)
    finish("convert", warehouse)


# W7's Run value: the latest day ops.job_runs holds, as the user writes it in their Project.
RUN_VALUES = '''"""Run values: what a Script tag stands for, worked out each time a table is
written."""

import datetime

from sqlglot_composer import latest_partition
from references.ops__job_runs import job_runs
from warehouse import query


def period_end() -> datetime.date:
    """The latest day ops.job_runs holds."""
    return latest_partition(job_runs.dt, query)
'''


def reference_w7(root: Path, warehouse: SavedWarehouse) -> None:
    """W7's end: the script converted, PERIOD_END answered by the user's function, which reads
    the latest day ops.job_runs holds, and the seed limited to 2026-09-24 on."""
    folder = root / "admin" / "workflows" / "convert"
    shutil.copyfile(root.parent / "from_your_team" / "run_log.hql", folder / "run_log.hql")
    table = f"{DEV}.run_log"
    type_into(root, "convert", NAME="run_log", FILES=["run_log.hql"], DATABASE="ops",
              RENAME={"mart.run_log": "run_log"})
    run_the_workflow("convert", warehouse)
    (root / "building_blocks" / "run_values.py").write_text(RUN_VALUES, encoding="utf-8")
    notebook = folder / "convert.ipynb"
    for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
        if text.startswith("DECISIONS ="):
            notebooks.write_cell_text(notebook, number, W7_DECISIONS.format(
                table=table, location=location(table)))
    finish("convert", warehouse)


W7_DECISIONS = """from building_blocks.run_values import period_end

DECISIONS = {{
    "{table}": {{"location": "{location}", "key": None,
                 "tags": {{"PERIOD_END": period_end}}, "seed": {{"dt": "2026-09-24"}}}},
}}
"""


def fill_runs_per_day_logic(text: str) -> str:
    """The saved_table Template's logic, filled in for runs_per_day, as a user fills it in."""
    for placeholder, value in (
            ("<SOURCE_NAME>", "ops__job_runs"), ("<SOURCE_TABLE>", "job_runs"),
            ("<READS>", 'between(job_runs.dt, "2026-09-23", "2026-09-24")'),
            ("<GROUP_COLUMN>", "job_id"), ("<COUNT_NAME>", '"runs"'),
            ("<PARTITION_COLUMN>", "dt")):
        text = text.replace(placeholder, value)
    return text.replace("create_table, equals,", "between, create_table, equals,", 1)


def reference_w2(root: Path, warehouse: SavedWarehouse) -> None:
    add_references(root, {"ops.job_runs": ["run_id"]}, warehouse)
    table = f"{DEV}.runs_per_day"
    type_into(root, "new_table", TABLES=[table],
              DECISIONS=where_each_goes([table]))
    run_the_workflow("new_table", warehouse)
    notebook = root / "tables" / "mart_dev__runs_per_day" / "mart_dev__runs_per_day.ipynb"
    for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
        if text.startswith("# logic"):
            notebooks.write_cell_text(notebook, number, fill_runs_per_day_logic(text))
    finish("new_table", warehouse)


def reference_w3(root: Path, warehouse: SavedWarehouse) -> None:
    add_references(root, {"ops.job_runs": ["run_id"]}, warehouse)
    shutil.copyfile(root.parent / "from_your_team" / "failed_runs.hql",
                    root / "admin" / "workflows" / "new_table" / "failed_runs.hql")
    table = f"{DEV}.failed_runs"
    type_into(root, "new_table", TABLES=[table], QUERIES={"failed_runs": "failed_runs.hql"},
              DECISIONS=where_each_goes([table]))
    finish("new_table", warehouse)


def reference_w4(root: Path, warehouse: SavedWarehouse) -> None:
    add_references(root, {"ops.jobs": ["job_id"], "ops.run_alerts": ["alert_id"]}, warehouse)


def reference_w5(root: Path, warehouse: SavedWarehouse) -> None:
    from references.mart_dev__runs_per_day import runs_per_day

    change = admin.drop_partitions(runs_per_day, where=equals(runs_per_day.dt, "2026-09-24"))
    run_execute(change, warehouse.execute)


def reference_h1(root: Path, warehouse: SavedWarehouse) -> None:
    shutil.copyfile(root.parent / "from_your_team" / "weekly.hql",
                    root / "admin" / "workflows" / "convert" / "weekly.hql")
    names = ["team_fails", "job_runs_counted", "job_fails_counted"]
    tables = [f"{DEV}.{name}" for name in names]
    type_into(root, "convert", NAME="weekly", FILES=["weekly.hql"], DATABASE="ops",
              RENAME={f"mart.{name}": name for name in names},
              DECISIONS=where_each_goes(tables))
    finish("convert", warehouse)
    prods = [table.replace(f"{DEV}.", f"{PROD}.") for table in tables]
    type_into(root, "promote", TABLES=tables,
              DECISIONS=where_each_goes(prods))
    finish("promote", warehouse)


def without_upgrade_marks(text: str) -> str:
    """The text without its lines marked # UPGRADE, as a user takes each out once done."""
    return "".join(line for line in text.splitlines(keepends=True)
                   if "# UPGRADE" not in line)


def reference_h2(root: Path, warehouse: SavedWarehouse) -> None:
    with contextlib.chdir(root / "admin"):
        project.upgrade()
    fill_in_the_databases(root)
    for path in [*root.rglob("*.py"), *root.rglob("*.ipynb")]:
        if "removed" in path.parts or "# UPGRADE" not in path.read_text(encoding="utf-8"):
            continue
        if path.suffix == ".py":
            path.write_text(without_upgrade_marks(path.read_text(encoding="utf-8")),
                            encoding="utf-8")
            continue
        for number, (_, text) in enumerate(notebooks.read_cells(path), 1):
            if "# UPGRADE" in text:
                notebooks.write_cell_text(path, number, without_upgrade_marks(text))
    finish("upgrade", warehouse)


def reference_excel(tables: list[str], references: dict[str, list[str]],
                    keys: dict[str, list[str]]) -> Callable[..., None]:
    """An Excel scenario's reference end: its Hive, as Copilot should write it, saved and made
    into each table by new_table, each table's location and Key answered, as `keys` gives
    them."""
    def reach(root: Path, warehouse: SavedWarehouse) -> None:
        add_references(root, references, warehouse)
        folder = root / "admin" / "workflows" / "new_table"
        queries = {}
        for table in tables:
            name = table.split(".")[1]
            (folder / f"{name}.hql").write_text(REFERENCE_HIVE[name], encoding="utf-8")
            queries[name] = f"{name}.hql"
        answers = where_each_goes(tables)
        for table, key in keys.items():
            answers[table]["key"] = key
        type_into(root, "new_table", TABLES=tables, QUERIES=queries, DECISIONS=answers)
        finish("new_table", warehouse)
    return reach


RUNS_KEY = {"ops.job_runs": ["run_id"]}
JOINED_KEYS = {"ops.jobs": ["job_id"], "ops.job_runs": ["run_id"]}
REFERENCE_ENDS: dict[str, Callable[[Path, SavedWarehouse], None]] = {
    "W1": reference_w1, "W2": reference_w2, "W3": reference_w3, "W4": reference_w4,
    "W5": reference_w5, "W6": reference_w6, "W7": reference_w7, "H1": reference_h1,
    "H2": reference_h2,
    "E1": reference_excel([f"{DEV}.job_run_report"], RUNS_KEY,
                          {f"{DEV}.job_run_report": ["job_id"]}),
    "E2": reference_excel([f"{DEV}.team_report"], JOINED_KEYS,
                          {f"{DEV}.team_report": ["team"]}),
    "E3": reference_excel([f"{DEV}.daily_runs"], RUNS_KEY, {f"{DEV}.daily_runs": ["dt"]}),
    "E4": reference_excel([f"{DEV}.job_costs", f"{DEV}.team_runs"], JOINED_KEYS,
                          {f"{DEV}.job_costs": ["job_id"], f"{DEV}.team_runs": ["team"]}),
}


def reference_end(scenario_id: str, run: Path) -> None:
    """A scenario's end reached with the Toolbox in the prepared run `run`: in the Project the
    run holds, or one started there as its user would."""
    root = run / "my_project"
    if not root.is_dir():
        root = start_the_project(run)
    warehouse = SavedWarehouse(run / "_loop" / "warehouse.json")
    with contextlib.chdir(root), project_on_the_path(root):
        REFERENCE_ENDS[scenario_id](root, warehouse)


# --- Building the folders ---------------------------------------------------------------------


def build(folder: Path = FOLDER) -> None:
    """Write every scenario's folder into `folder`, as this file says, each Project action's
    time pinned, so a build writes the same files each time."""
    with times_pinned():
        for scenario_id, built in scenarios().items():
            build_one(folder / scenario_id, scenario_id, built)


def build_one(place: Path, scenario_id: str, built: Built) -> None:
    """Write one scenario's folder, `place`, afresh."""
    if place.exists():
        shutil.rmtree(place)
    place.mkdir(parents=True)
    (place / "scenario.json").write_text(json.dumps(built.held, indent=1) + "\n",
                                         encoding="utf-8")
    for name, text in built.files.items():
        (place / name).write_text(text, encoding="utf-8")
    for name, make in built.workbooks.items():
        make().save(place / name)
    (place / "key.json").write_text(json.dumps(built.key(), indent=1) + "\n",
                                    encoding="utf-8")


if __name__ == "__main__":
    build()
