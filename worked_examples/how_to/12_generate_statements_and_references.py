"""Generate Statements and Table references in a loop

For: Intermediate

## Goal

Build many Statements from one function and a loop, in place of copying the same lines and
changing a word in each: one Statement per team, one per table of a Database, and one per
entry of a dict of settings. A Statement is one query, made of the Toolbox's Clause functions.
Then, for tables you only check, generate their Table references from settings too, run a
Statement for each, and export one Lineage for the lot. A Table reference describes one table:
its columns and their types, its Partitions and its Key; Lineage is the record of which table
columns feed each column a Statement gives.

## When you'd use it

- If you would otherwise copy a Statement and change one value, such as a team, a status or a
  region, write the Statement once as a function of that value, as steps 4 and 5 do.
- If you ask the same question of several tables, such as every table of `ops`, loop over the
  tables, as steps 8 to 11 do.
- If you keep a set of checks, make each one a line of settings, so adding a check is one more
  line, not one more Statement to write, as steps 12 to 14 do.
- If you check many tables but never read them in a Statement, make their Table references in
  the notebook, from settings, as steps 15 to 18 do.
- If only a value changes and one result is enough, write one Statement with `GROUP_BY`: it
  answers for every value at once, as step 3 shows.
- If you have not yet done the Getting started how-tos, do
  [Add your tables' references](#add_your_tables_references),
  [Build and run a first statement](#build_and_run_a_first_statement) and
  [Count, join and stay safe](#count_join_and_stay_safe) first.

A Statement is a Python value, built by Python functions, so a loop builds Statements as it
builds anything else.

## Steps

### 1. Copy the Intermediate Example project

Goal: a Project to work in. A Project is your folder of scripts at work, in the Toolbox's fixed
layout, and an Example project is one made for the Example database's tables, to read and copy
from. Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder holds the Intermediate Example project's files. Then step 2.

### 2. Import the Toolbox, pandas and your query

Goal: every name the steps call. Import the Toolbox, pandas, the Project's `ops` Database and
your query. A Database is a named group of tables, the first part of a table's name, `ops` in
`ops.jobs`:

>>> from sqlglot_composer import *
>>> import pandas as pd
>>> from references import ops
>>> from warehouse import query, execute

Done when the four imports run without an error. Then step 3.

### 3. Check whether one Statement does it

Goal: write a loop only where you need one. `ops.team_notes` holds the notes each team wrote
about its jobs. It isn't partitioned, so a Statement may read all of it. How many notes has
each team written? One Statement, grouped by team, answers for every team at once, in one
query:

>>> team_notes = ops.team_notes  # -> Table
>>> notes_per_team = statement(  # -> Statement
...     SELECT(team_notes.team, AS(count_rows(), "notes")),
...     FROM(team_notes),
...     GROUP_BY(team_notes.team),
... )
>>> run_query(notes_per_team, query)  # -> DataFrame
      team  notes
0     data      2
1  finance      2
2      web      1

A loop is for when each Statement must be its own: its own result to send somewhere, its own
table, or its own columns and conditions.

Done when you know each Statement must be its own: here, each team wants its own file. Then
step 4.

### 4. Write the Statement once, as a function

Goal: one function that gives any team's Statement. Each team wants its own notes, in a file
of its own. Write the Statement once, as a function of the team:

>>> def notes_of(team: str) -> Statement:
...     return statement(
...         SELECT(team_notes.written_on, team_notes.note),
...         FROM(team_notes),
...         WHERE(equals(team_notes.team, team)),
...     )

Done when `notes_of` is defined. Then step 5.

### 5. Build one Statement per team in a loop

Goal: each team's Statement, kept by team. Loop over the three teams, keeping each team's
Statement in a dict, by team:

>>> per_team = {}
>>> for team in ["data", "finance", "web"]:
...     per_team[team] = notes_of(team)
>>> run_query(per_team["finance"], query)  # -> DataFrame
   written_on                                     note
0  2026-09-18   report_build came over from data today
1  2026-09-21  invoice_sync's bill comes in a day late

Done when finance's Statement gives its two notes. Then step 6.

### 6. Save each team's result in a file

Goal: one CSV file per team. Run each Statement, and save each team's result in its own CSV
file:

>>> for team in per_team:
...     result = run_query(per_team[team], query)
...     result.to_csv(f"notes_{team}.csv", index=False)

A team with no notes gets a file with only the column names, so every team gets a file.

Done when notes_data.csv, notes_finance.csv and notes_web.csv are in the folder. Then step 7.

### 7. Print every Statement's Hive

Goal: every team's Hive, ready to paste into another program. Put the Statements in a list, and
`show_hive` prints them all, each headed by its place in the list:

>>> team_statements = list(per_team.values())  # -> list[Statement]
>>> text = show_hive(team_statements)  # -> str
-- 1 of 3: team_statements[0]
SELECT
  team_notes.written_on,
  team_notes.note
FROM ops.team_notes AS team_notes
WHERE
  team_notes.team = 'data';
<BLANKLINE>
-- 2 of 3: team_statements[1]
SELECT
  team_notes.written_on,
  team_notes.note
FROM ops.team_notes AS team_notes
WHERE
  team_notes.team = 'finance';
<BLANKLINE>
-- 3 of 3: team_statements[2]
SELECT
  team_notes.written_on,
  team_notes.note
FROM ops.team_notes AS team_notes
WHERE
  team_notes.team = 'web';

The three differ only in their last line, the team.

Done when the three Statements' Hive differs only in the team. Then step 8.

### 8. List the tables of a Database

Goal: the names to loop over. How many rows does each table of `ops` hold? `dir(ops)` lists its
tables, the list tab completion shows, and `getattr(ops, name)` gives the table named `name`:

>>> dir(ops)  # -> list[str]
['job_events', 'job_owners', 'region_budgets', 'region_costs', 'team_notes']

Done when `dir(ops)` lists the five tables. Then step 9.

### 9. Say which rows to count in each table

Goal: a filter for each table. The tables are partitioned in different ways, and a read of a
partitioned table must filter one of its partition columns. A Partition is a slice of a table:
the rows that share one value of each column it is partitioned by. So say for each table which
rows to count: a condition on one of its partition columns, or None for `ops.team_notes`,
which has none:

>>> reads = {
...     "job_events": equals(ops.job_events.dt, "2026-09-24"),
...     "job_owners": equals(ops.job_owners.dt, "2026-09-24"),
...     "region_budgets": equals(ops.region_budgets.region, "eu"),
...     "region_costs": equals(ops.region_costs.region, "eu"),
...     "team_notes": None,
... }

Done when `reads` holds an entry for each name `dir(ops)` lists. Then step 10.

### 10. Write the counting function

Goal: one function that counts any table's rows. The function takes the table itself, a Table
reference, as an argument, and adds a WHERE only where there is a condition:

>>> def row_count(table: Table, where: Condition | None) -> Statement:
...     clauses = [SELECT(AS(count_rows(), "row_count")), FROM(table)]
...     if where is not None:
...         clauses.append(WHERE(where))
...     return statement(*clauses)

Done when `row_count` is defined. Then step 11.

### 11. Count each table's rows in a loop

Goal: one row per table. Loop over the tables, by name, and gather one row per table:

>>> counted = []
>>> for name in dir(ops):
...     result = run_query(row_count(getattr(ops, name), reads[name]), query)
...     counted.append({"table": name, "row_count": result["row_count"][0]})
>>> pd.DataFrame(counted)  # -> DataFrame
            table  row_count
0      job_events          3
1      job_owners          4
2  region_budgets          3
3    region_costs         24
4      team_notes          5

Done when the DataFrame holds a row count for each of the five tables. Then step 12.

### 12. Write each check as settings

Goal: a set of daily checks, one entry each. Each check counts, on one day, the rows of a table
whose column holds a given value. Each check is a few settings, so each is an entry of a dict:
its name, then its table, its column and its value.

>>> CHECKS = {
...     "failed_runs": {"table": ops.job_events, "column": "event_type", "value": "fail"},
...     "retries": {"table": ops.job_events, "column": "event_type", "value": "retry"},
...     "web_jobs": {"table": ops.job_owners, "column": "team", "value": "web"},
... }

Done when `CHECKS` holds the three checks. Then step 13.

### 13. Write the check function

Goal: one function that builds any check's Statement. The function names the column as text,
so it reads it from the Table reference with Python's `getattr`:
`getattr(ops.job_events, "event_type")` is `ops.job_events.event_type`. Both tables are
partitioned by their day, dt:

>>> def matching_rows(table: Table, column: str, value: str, day: str) -> Statement:
...     return statement(
...         SELECT(AS(count_rows(), "matching")),
...         FROM(table),
...         WHERE(equals(table.dt, day), equals(getattr(table, column), value)),
...     )

Done when `matching_rows` is defined. Then step 14.

### 14. Run each check in a loop

Goal: one row per check. The loop builds and runs each check, and gathers one row per check:

>>> found = []
>>> for name, setting in CHECKS.items():
...     check = matching_rows(setting["table"], setting["column"], setting["value"],
...                           "2026-09-18")
...     result = run_query(check, query)
...     found.append({"check": name, "matching": result["matching"][0]})
>>> pd.DataFrame(found)  # -> DataFrame
         check  matching
0  failed_runs         1
1      retries         0
2     web_jobs         1

To add a check, add one line to `CHECKS`; the function and the loop stay as they are.

Done when the DataFrame holds a count for each of the three checks. Then step 15.

### 15. Write a setting per table to check

Goal: what each generated Table reference needs, a line each. Your Statements read the tables
of `ops` through their Table references in references/, which `project.add_references` wrote
from each table's DESCRIBE. A weekly check over many tables you never read in a Statement
needs less: a Table reference made in the notebook, from a line of settings each. Here, three
tables of the Example database this Project doesn't read: the table's name, its partition
columns, its Key, the columns whose values name one row, under `"add_up"` the columns a daily
total adds up, and under `"does_not_add_up"` any that must never be added up, such as
avg_retry_secs, an average per run:

>>> settings = [
...     {"table": "ops.job_runs", "partitioned_by": ["dt"], "key": ["run_id"],
...      "add_up": ["duration_mins"], "does_not_add_up": ["avg_retry_secs"]},
...     {"table": "ops.run_alerts", "partitioned_by": ["dt"], "key": ["alert_id"],
...      "add_up": []},
...     {"table": "ops.scheduler_runs", "partitioned_by": ["dt"], "key": ["run_id"],
...      "add_up": []},
... ]

Done when `settings` holds a line for each of the three tables. Then step 16.

### 16. Read a table's DESCRIBE

Goal: see what your query gives for each column. A Table reference needs each column and its
type. Rather than type them, ask the table: your query runs DESCRIBE, which lists the columns,
one per row, each with its name in `"col_name"` and its type in `"data_type"`. After them it
lists the partition columns again, under a heading row starting with `#`, often after an empty
row, so stop at the first such row:

>>> query("DESCRIBE ops.scheduler_runs")  # -> DataFrame
                  col_name  data_type  comment
0                   run_id     bigint
1                   job_id     bigint
2                       dt     string
3                                 NaN      NaN
4  # Partition Information        NaN      NaN
5               # col_name  data_type  comment
6                       dt     string

Done when you see where the columns end: the first empty row or row starting with `#`. Then
step 17.

### 17. Build a Table reference from each setting

Goal: a Table reference per table, in the notebook. `table_reference` builds a Table reference
from a setting and what DESCRIBE gives:

>>> from collections.abc import Callable
>>> def table_reference(setting: dict[str, str | list[str]],
...                     query: Callable[[str], pd.DataFrame]) -> Table:
...     described = query("DESCRIBE " + setting["table"])
...     columns = {}
...     for name, data_type in zip(described["col_name"], described["data_type"]):
...         if not name or name.startswith("#"):
...             break
...         columns[name] = data_type
...     return Table(setting["table"], columns=columns,
...                  partitioned_by=setting["partitioned_by"], key=setting["key"],
...                  does_not_add_up=setting.get("does_not_add_up", []))
>>> tables = {setting["table"]: table_reference(setting, query)  # -> dict[str, Table]
...           for setting in settings}
>>> tables["ops.job_runs"]
Table('ops.job_runs', columns: run_id, job_id, status, duration_mins, avg_retry_secs, dt)

Done when `tables["ops.job_runs"]` shows its six columns. Then step 18.

### 18. Check what you generated

Goal: proof each generated Table reference is right. Check it as you would a Table reference
you wrote: each still matches its table, and each Key holds on the newest day:

>>> for t in tables.values():
...     print(check_table_reference(t, query=query))
...     print(check_key(t, query=query, where=equals(t.dt, "2026-09-24")))
ops.job_runs matches its Table reference.
ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.
ops.run_alerts matches its Table reference.
ops.run_alerts: the key (alert_id) holds where run_alerts.dt = '2026-09-24'.
ops.scheduler_runs matches its Table reference.
ops.scheduler_runs: the key (run_id) holds where scheduler_runs.dt = '2026-09-24'.

A Table reference generated like this lasts as long as the notebook. For a table you build on,
keep its Table reference in references/, with `project.add_references`, as [Add your tables'
references](#add_your_tables_references) shows, so a change to the table shows up as a
difference when you check it, rather than slipping into your Statements.

Done when each table matches its Table reference and each Key holds. Then step 19.

### 19. Generate a Statement for each table

Goal: each table's daily totals, from one function. `daily_totals` writes one Statement for a
table and its setting: per day, the number of rows and the total of each column it adds up.
`getattr(t, "duration_mins")` is `t.duration_mins`, for a column whose name you hold as text,
so a column the table doesn't have stops here, naming the real ones:

>>> def daily_totals(t: Table, setting: dict[str, str | list[str]], first_day: str,
...                  last_day: str) -> Statement:
...     totals = [AS(sum_of(getattr(t, name)), "total_" + name)
...               for name in setting["add_up"]]
...     return statement(
...         SELECT(t.dt, AS(count_rows(), "row_count"), totals),
...         FROM(t),
...         WHERE(between(t.dt, first_day, last_day)),
...         GROUP_BY(t.dt),
...     )
>>> daily = {setting["table"]: daily_totals(  # -> dict[str, Statement]
...              tables[setting["table"]], setting, "2026-09-23", "2026-09-24")
...          for setting in settings}
>>> text = show_hive(*daily.values())  # -> str
-- 1 of 3
SELECT
  job_runs.dt,
  COUNT(*) AS row_count,
  SUM(job_runs.duration_mins) AS total_duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  job_runs.dt;
<BLANKLINE>
-- 2 of 3
SELECT
  run_alerts.dt,
  COUNT(*) AS row_count
FROM ops.run_alerts AS run_alerts
WHERE
  run_alerts.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  run_alerts.dt;
<BLANKLINE>
-- 3 of 3
SELECT
  scheduler_runs.dt,
  COUNT(*) AS row_count
FROM ops.scheduler_runs AS scheduler_runs
WHERE
  scheduler_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  scheduler_runs.dt;

Done when `show_hive` prints three Statements, one per table. Then step 20.

### 20. Run them all

Goal: each table's result, kept under its name. Run each in a loop, and keep each result under
its table's name:

>>> results = {name: run_query(totals, query)  # -> dict[str, DataFrame]
...            for name, totals in daily.items()}
>>> results["ops.job_runs"]
           dt  row_count  total_duration_mins
0  2026-09-23          5                   80
1  2026-09-24          4                  100

Done when `results["ops.job_runs"]` holds a row for each of the two days. Then step 21.

### 21. Export one Lineage for them all

Goal: one page that traces every Statement. Pass every Statement to
[`export_lineage`](examples.html#export_lineage) at once, and it writes one HTML page and one
Markdown file for them all, laid out as in [Follow lineage](#follow_lineage). `to=` names the
HTML file, and the Markdown file goes beside it.

`export_lineage` names each Statement after the variable that holds it. These sit in a dict, in
no variable of their own, so it numbers them in the order you passed them: in the file below,
statement_1 is `ops.job_runs`'s, statement_2 `ops.run_alerts`'s and statement_3
`ops.scheduler_runs`'s, and each one's Hive, at the end of its part, names its table.

>>> html_file, markdown_file = export_lineage(*daily.values(),
...                                           to="daily_totals.html")  # -> tuple[Path, Path]

Done when daily_totals.html and daily_totals.md are written. Then check it worked, below.

## Check it worked

The per-team Statements together find every note the one grouped Statement counts: five.

>>> sum(len(run_query(team_statement, query)) for team_statement in per_team.values())
5

And the loops made one Statement per team, per table, per check and per setting:

>>> len(per_team), len(counted), len(found), len(daily)
(3, 5, 3, 3)
>>> markdown_file.name
'daily_totals.md'

Before you go on, check that:

- the per-team Statements find 5 notes in all, as the grouped Statement counts;
- the lengths show `(3, 5, 3, 3)`: one Statement per team, per table, per check and per
  setting;
- `markdown_file.name` shows `'daily_totals.md'`.

## Common mistakes

### A setting that names a column the table doesn't have

A typo in a setting is caught when the Statement is built, with the column's likely name and
the table's columns:

>>> matching_rows(ops.job_events, "event_typ", "fail", "2026-09-18")
Traceback (most recent call last):
...
AttributeError: job_events has no column 'event_typ'. Did you mean 'event_type'? Its columns
    are: event_id, job_id, event_type, minutes, dt.

Write the column's name as the message lists it.

### A partitioned table with no condition in the loop

Give a partitioned table None in `reads`, and its Statement reads every Partition it has.
The Load limit, the check that refuses a Statement that would read too much, stops it, and with
it the loop, naming the partition columns to filter:

>>> row_count(ops.region_costs, None)
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(region_costs) reads ops.region_costs, but filters none of its partition
                  columns: region, dt.
...

Give each partitioned table a condition on one of its partition columns, as `reads` does.

### A setting that looks for a missing value

A check for jobs with no owner can't use `equals` with None: in SQL nothing equals a missing
value, so it would always count 0. A Guard, a check that refuses a Statement that would give a
wrong result, stops it, and with it the loop:

>>> matching_rows(ops.job_owners, "owner", None, "2026-09-24")
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  equals(job_owners.owner, None) compares with None.
...

Use `is_null` for such a check: give it a function of its own, or a setting that says which
condition to build.

### Adding up an average

A setting can list under `"add_up"` a column that must not be added up, such as
"avg_retry_secs", an average per run. Because the Table reference was generated with
`"does_not_add_up"` from the setting, the Toolbox refuses it:

>>> averages = {"table": "ops.job_runs", "key": ["run_id"], "add_up": ["avg_retry_secs"]}
>>> daily_totals(tables["ops.job_runs"], averages, "2026-09-23", "2026-09-24")
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  sum_of(job_runs.avg_retry_secs) adds up job_runs.avg_retry_secs, which is
                  listed in does_not_add_up in its Table reference.
...

Fill in `"does_not_add_up"` for every table: left out, nothing would refuse it, and the total
would come out, and be wrong.

## Next

- Checks of your data, such as no repeated Keys or no missing values, as Statements you
  could generate per table the same way: [Check data quality](#check_data_quality).
- Write a range of a Saved table's Partitions, in one write or in a loop of writes:
  [Rewrite some partitions](#rewrite_some_partitions).
- Compare a Lineage before and after you change the function that writes your Statements:
  [Review and test a change](#review_and_test_a_change).
- The gallery's [`all_columns`](examples.html#all_columns) entry, which gives a Table
  reference's columns as a list to loop over, and [`Table`](examples.html#Table), which says
  what each part of a Table reference does.
"""
