<!-- Spark Composer 4.0, exported 2026-10-06 00:26 - copy it, then edit your copy -->
# The starter Example project

A small project laid out the way one should be at work, written for Spark Composer on three
of the Example database's tables: `ops.jobs`, `ops.job_runs` and `ops.run_alerts`. Copy the
layout for your own project, then replace the tables and the Statements with yours.

It has three examples. Example 1 and example 2 each save one day's numbers in a Saved table,
and example 3 combines them: it reads both Saved tables to give each team's day. Along the way
it shows how to:

- write a table's Table reference, its column names and types, from the table itself, with
  `write_table_reference`, instead of typing them;
- create a Saved table from its Table reference with `create_table`, then write it a day at a
  time with `INSERT_OVERWRITE`, and fill in past days with `by_day`;
- name a step with `derived(...)` in a Building block, so several Statements read the same
  numbers worked out the same way (the Hive writes it as `WITH ... AS (...)`);
- run every step in one fixed order, print the Hive of all of them with `show_hive`, and
  draw where each column comes from with `export_lineage`.

## The files

The scripts sit in three Levels, and a script imports only from a lower Level and from the
Toolbox, never from its own Level or a higher one. That keeps each file small, and means a
change to a Table reference reaches every Statement that reads it.

| File | What it is |
|---|---|
| `table_references/` | **Level 0.** One Table reference per table: its columns and their types, its Date partition and its key. |
| `table_references/jobs.py` | `ops.jobs`, each job's name, team and region. **Generated**, then filled in by hand. |
| `table_references/job_runs.py` | `ops.job_runs`, one row per run. **Generated**, then filled in by hand. |
| `table_references/run_alerts.py` | `ops.run_alerts`, one row per alert a run raised. **Generated**, then filled in by hand. |
| `table_references/daily_job_runs.py` | `mart.daily_job_runs`, the Saved table example 1 writes. Written by hand. |
| `table_references/alerts_per_job.py` | `mart.alerts_per_job`, the Saved table example 2 writes. Written by hand. |
| `table_references/team_day.py` | `mart.team_day`, the Saved table example 3 writes. Written by hand. |
| `building_blocks/` | **Level 1.** Pieces that several Statements share. |
| `building_blocks/runs_per_job_day.py` | Runs, failed runs and minutes per job and day, as a Derived table. Examples 1 and 3 read it. |
| `statements/` | **Level 2.** The Statements, each example in its own file. |
| `statements/example_1_daily_job_runs.py` | Example 1: each job's runs, failed runs and minutes per day, saved in `mart.daily_job_runs`. |
| `statements/example_2_alerts_per_job.py` | Example 2: each job's alerts and high alerts per day, joining each alert to its run, saved in `mart.alerts_per_job`. |
| `statements/example_3_team_day.py` | Example 3: reads both Saved tables and `ops.jobs` to save each team's day in `mart.team_day`. |
| `run_pipeline.py` | Every step of the three examples for one day, in order. It sits above the Levels, so it may import from all three. |
| `lineage/` | **Generated** by `export_lineage`: where each column comes from, as an HTML page and a Markdown twin. |
| `lineage/example_1_daily_job_runs.html` and `lineage/example_1_daily_job_runs.md` | Example 1's write. |
| `lineage/example_2_alerts_per_job.html` and `lineage/example_2_alerts_per_job.md` | Example 2's write. |
| `lineage/example_3_team_day.html` and `lineage/example_3_team_day.md` | Example 3's write. |
| `lineage/all_three.html` and `lineage/all_three.md` | All three together: from `ops.job_runs` and `ops.run_alerts`, through the two Saved tables, to `mart.team_day`. |
| `README.md` | This file. |

**Generated** files are written by the Toolbox, not typed:

- The three Table references of the tables the project reads were written by
  `write_table_reference("ops.jobs", send=...)` and so on, which asks the table for its columns.
  It can't know the key, a one-line description, or which columns don't add up, so it leaves a
  TODO line for each; those lines were filled in by hand, and say so. The Saved tables' Table
  references are written by hand, since those tables don't exist until `create_table` makes
  them.
- The lineage files were written by `write_lineage_files("2026-09-24")` in `run_pipeline.py`.

## Each example's steps

Each example file has the same steps, as functions that return Statements:

1. `create()`: create the Saved table, if it isn't there yet.
2. `preview(day)`: the rows the day's write would save, as a SELECT to run and check first.
3. `write_day(day)`: save one day, replacing whatever the day held, so sending it twice is safe.
   Send it every day.
4. `backfill(first_day, last_day)`: save every day from `first_day` to `last_day`, for days
   already past, such as when a Saved table is new.

`write_day` and `backfill` save the same rows for a day. `backfill` builds the day's
Statement once over all the days, then `by_day` cuts it into one write per day, oldest first,
to send in that order. Each of those writes keeps the day in `GROUP_BY`, so no day's counts are
mixed with another's.

No step selects the Date partition, `dt`, of the Saved table it writes: the Toolbox reads the
day from the WHERE bound (one day only) and writes it as `PARTITION(dt = '...')`.

Every read of a table must bound its Date partition at both ends, a joined table's too, and
`by_day` cuts only the days of the table in FROM, leaving a joined table's bound as written.
So example 2 reads the joined `ops.job_runs` from the day before (a run can raise an alert
after midnight), and example 3's `backfill` bounds the joined `mart.alerts_per_job` inside
`LEFT_JOIN`'s `ON=`, with `between(alerts_per_job.dt, first_day, last_day)`.

Example 3 runs after examples 1 and 2 have written the same day, since it reads what they
write: `run_pipeline.py` keeps that order. It also has `team_runs_from_job_runs(day)`, which
tries example 3's team grouping on the Example database: it reads only ops tables, not the
Saved tables, so it runs on the Example database too.

## Running it here, on the Example database

Python must find the Toolbox's two folders, `composer_core` and `spark_composer`: put them
beside `run_pipeline.py`, or name the folder holding them in `PYTHONPATH`. They sit in the
Toolbox's top folder, the one that holds `example_projects` too, so in this folder:

```
PYTHONPATH=../../.. python run_pipeline.py
```

or, in the Windows command prompt:

```
set PYTHONPATH=..\..\..
python run_pipeline.py
```

That prints the Hive of every step for the Example database's last day, in order, each headed
by its name, such as `-- 4 of 6: write_daily_job_runs`, without sending anything (a dry run).

The scripts import the Toolbox as `from spark_composer import ...`, the folder of the Edition
they are written for. With the other Edition, write its folder's name in each import instead.

Each step that runs takes `send=`: a function that takes a Hive string and returns a pandas
DataFrame, such as `lambda hive: spark.sql(hive).toPandas()` at work. Here it is
`example_database.send`. The Example database can be read but not written, so try the
`preview` steps there, in Python started in this folder:

```python
from spark_composer import example_database, run
from statements import example_1_daily_job_runs as example_1
from statements import example_3_team_day as example_3

run(example_1.preview("2026-09-24"), send=example_database.send)
run(example_3.team_runs_from_job_runs("2026-09-24"), send=example_database.send)
```

Example 3's `preview` reads the Saved tables, which only your warehouse holds.

To write the lineage files again, in the same Python:

```python
import run_pipeline

run_pipeline.write_lineage_files("2026-09-24")
```

## Running it at work

1. Copy this folder, and put the Toolbox's two folders beside `run_pipeline.py`.
2. In `table_references/`, delete the three generated files. Start Python in that folder,
   since `write_table_reference` writes its file into the folder Python started in, with the
   Toolbox's folders in `PYTHONPATH`. Write your own tables' Table references with
   `write_table_reference("your_db.your_table", send=run_query)`, `run_query` being your own
   send function, and fill in each TODO line. Write your Saved tables' Table references by
   hand, naming a database you may write to.
3. Change the Building blocks and Statements to read your tables.
4. Check a day with `run(example_1.preview(day), send=run_query)`, print everything with
   `dry_run(day)` from `run_pipeline.py`, then send it all every day with
   `send_all(run_query, day)`.
5. Run `write_lineage_files(day)` after a change, and keep the lineage files with your
   scripts, so a reviewer can see where each column comes from.
