# The intermediate Example project

A project laid out the way one should be at work, written for sqlglot Composer on three of the
Example database's tables, each with 14 days of rows, 2026-09-11 to 2026-09-24:
`ops.job_events` (each run's start, retries, and finish or fail), `ops.job_owners` (a snapshot
of each job's team and owner every day) and `ops.region_costs` (what each job's runs cost, in
cents, partitioned by region, then by a day written like 20260924). The jobs are those of
`ops.jobs`, which this project doesn't read: job 1 is nightly_load, job 2 invoice_sync, job 3
report_build and job 4 cache_warm, which never runs. Read the starter Example project,
`example_projects/starter/`, first: this one builds on its layout and steps.

It has three examples and a set of quality checks. Example 1 saves each job's cost per day,
example 2 each job's day with the team that owned the job that day, and example 3 combines them
into each team's days and weeks. Along the way it shows how to:

- write a Table reference for a table partitioned first by something other than days, and
  whose days are written another way, with `date_format`;
- load a few days again on every run, so late rows are saved, with `by_day`, and why
  `INSERT_OVERWRITE` makes writing a day again safe;
- join two tables whose days are written differently, by saving one of them first;
- look a job's team up as of each day from a daily snapshot table, and find each job's newest
  snapshot with `row_number`;
- add days up into weeks with `week_start`;
- write Building blocks that take the days, one that is a join rather than a Derived table, and
  one that finds rows with no match (an anti-join);
- write the same quality checks for every table from a few settings, with `all_columns`;
- run every step in order, for the last 3 days or for a backfill, print the Hive of all of
  them with `show_hive`, and compare the lineage before and after editing a Building block.

## The files

The scripts sit in three Levels, and a script imports only from a lower Level and from the
Toolbox, never from its own Level or a higher one. `settings.py` is Level 0, beside the Table
references.

| File | What it is |
|---|---|
| `settings.py` | **Level 0.** One dict per table the project reads: its name, Date partition, key and the columns to add up. The quality checks are written from it. |
| `table_references/` | **Level 0.** One Table reference per table: its columns and their types, its Date partition and its key. |
| `table_references/job_events.py` | `ops.job_events`, one row per event of a run. **Generated**, then filled in by hand. |
| `table_references/job_owners.py` | `ops.job_owners`, one row per job per day, with its team and owner. **Generated**, then filled in by hand. |
| `table_references/region_costs.py` | `ops.region_costs`, one row per job, region and day, with its cost. **Generated**, then filled in by hand, its Date partition too. |
| `table_references/job_day_costs.py` | `mart.job_day_costs`, the Saved table example 1 writes. Written by hand. |
| `table_references/job_day_facts.py` | `mart.job_day_facts`, the Saved table example 2 writes. Written by hand. |
| `table_references/team_days.py` | `mart.team_days`, the Saved table example 3 writes. Written by hand. |
| `building_blocks/` | **Level 1.** Pieces that several Statements share. |
| `building_blocks/events_per_job_day.py` | Events, runs and minutes per job and day, as a Derived table. It takes the days to read. |
| `building_blocks/owner_on_day.py` | A join to the team each job had on each row's day: the as-of lookup. |
| `building_blocks/costs_per_job_day.py` | Each job's cost per day, every region added up, as a Derived table. |
| `building_blocks/jobs_without_events.py` | Each job and day with an owner but no event: an anti-join. |
| `statements/` | **Level 2.** The Statements, each example in its own file, and the quality checks. |
| `statements/example_1_job_day_costs.py` | Example 1: each job's cost per day, the last 3 days saved again on every run, in `mart.job_day_costs`. |
| `statements/example_2_owner_as_of.py` | Example 2: each job's events, runs and minutes per day, with the team that owned it that day, in `mart.job_day_facts`; and each job's newest owner. |
| `statements/example_3_team_week.py` | Example 3: reads both Saved tables to save each team's days in `mart.team_days`, and adds them up into weeks. |
| `statements/quality_checks.py` | Repeated keys, NULLs, rows per day, the costs billed against the costs saved, and the jobs that didn't run. |
| `run_pipeline.py` | Every step of the three examples in order, and the quality checks. It sits above the Levels, so it may import from all three. |
| `lineage/` | **Generated** by `export_lineage`: where each column comes from, as an HTML page and a Markdown twin. |
| `lineage/example_1_job_day_costs.html` and `lineage/example_1_job_day_costs.md` | Example 1's write. |
| `lineage/example_2_owner_as_of.html` and `lineage/example_2_owner_as_of.md` | Example 2's write. |
| `lineage/example_3_team_week.html` and `lineage/example_3_team_week.md` | Example 3's write. |
| `lineage/all_three.html` and `lineage/all_three.md` | All three together: from the three ops tables, through the two Saved tables, to `mart.team_days`. |
| `lineage/review_before_edit.html` and `lineage/review_before_edit.md` | The lineage review, before the Building block edit described below. |
| `lineage/review_after_edit.html` and `lineage/review_after_edit.md` | The lineage review, after it. |
| `README.md` | This file. |

**Generated** files are written by the Toolbox, not typed:

- The three Table references of the tables the project reads were written by
  `write_table_reference("ops.job_events", send=...)` and so on, which asks the table for its
  columns and partitions. It can't know the key, a one-line description, or which columns
  don't add up, so it leaves a TODO line for each; those lines were filled in by hand, and say
  so. The Saved tables' Table references are written by hand, since those tables don't exist
  until `create_table` makes them.
- The lineage files were written by `write_lineage_files("2026-09-24")` in `run_pipeline.py`,
  except `lineage/review_before_edit.html` and its Markdown twin, which
  `write_lineage_review("2026-09-24", to=...)` wrote before the Building block edit described
  below. `write_lineage_files` writes only the "after" file again.

## A table whose days are written another way

`ops.region_costs` is partitioned by region, then by its Date partition, dt, and writes its
days like 20260924.
`write_table_reference` finds a Date partition only when the first partition holds days, so for
this table it wrote `date_partition=None` with a TODO line. Filled in by hand, the lines say
which partition holds the days, and how they are written:

```python
    date_partition="dt",
    date_format="%Y%m%d",
```

Then every condition on the Date partition is checked against that way of writing days. A day
written "2026-09-24" is refused, since it would match none of the table's days; a
`datetime.date`, such as `datetime.date(2026, 9, 24)`, is written the table's way, as
'20260924'. `costs_per_job_day` hands it the days that way. Only the Date partition must be
bounded: reading every region is fine.

Two tables whose days are written differently can't be joined on the day: `ON=` compares the
days as text, and 20260924 never equals 2026-09-24. The Toolbox refuses such a join as you
write it, naming how each table writes its days. Here, example 1 saves the costs first, in
`mart.job_day_costs`, which writes its days like 2026-09-24, as the other tables do: a write
fills `PARTITION(dt = '...')` written the Saved table's way, whatever way the table it read
writes its days. From then on, the costs join on the day like any other table.

## Each example's steps

Each example file has the same steps, as functions that return Statements:

1. `create()`: create the Saved table, if it isn't there yet.
2. `preview(day)`: the rows the day's write would save, as a SELECT to run and check first.
3. `write_days(first_day, last_day)`: save every day from `first_day` to `last_day`, one write
   per day, each replacing whatever its day held. Send them in order.

The starter's examples have `write_day(day)` for every day and `backfill(first_day,
last_day)` for days past. Here every run writes several days, so one step, `write_days`, does
both: a backfill is `write_days` from an earlier first day.

`write_days` builds one Statement over all the days, then `by_day` cuts it into one write per
day, oldest first. Each write keeps its day in `GROUP_BY`, directly or in a Building block, so
no day's numbers are mixed with another's. No step selects the Date partition, dt, of the Saved
table it writes: the Toolbox reads the day from each write's WHERE bound and writes it as
`PARTITION(dt = '...')`.

**Late rows, and writing a day again.** A bill or an event lands in the partition of the day
it is for, but can reach the table a day or two after that day was saved: invoice_sync's bill
for 2026-09-24 is still NULL. (A run that ends on a later day is another matter: its end
event is that later day's, so its minutes count on that day.) So every run writes the last 3 days again, not just the newest
one: an incremental load. `INSERT_OVERWRITE` replaces each day it writes, so a day written
again holds the same rows once, and a run sent twice by mistake does no harm. To fill in days
already past, such as when a Saved table is new, write from an earlier first day: that is a
backfill, the same Statement over more days.

**Looking the team up as of each day.** A job can move team: report_build moves from data to
finance on 2026-09-18. `ops.job_owners` holds a snapshot of every job's team each day, so
example 2 joins each job's day to the snapshot of the same day, with `owner_on_day`, and its
events count for the team it had then. A team taken from today's snapshot instead would count
all of report_build's past days for finance.

**The newest snapshot of each job.** Example 2's `newest_owners(day)` answers who owns each job
now: it numbers each job's snapshots from the 7 days up to the day with `row_number`, newest
first, and keeps number 1. `row_number` is a window function. Each Edition ships its own
Example database, and the one that runs its queries with sqlglot, rather than on Spark, has no
window functions: it stops with a message saying so. `newest_owners_by_newest_day(day)` gives
the same rows another way, so either Example database runs it: each job's newest day with
`max_of`, joined back to that day's snapshot.

**Days and weeks.** A write fills one day of a Saved table, so `mart.team_days` holds days, and
example 3's `week_totals(first_day, last_day)` adds each team's week up when it reads them,
grouping the days by `week_start`, the Monday that starts each day's week. That is right here
because events, runs, minutes and cents all add up: a count of different jobs wouldn't, since a
job that ran on two days of a week would be counted twice.

Every read of a table must bound its Date partition at both ends, a joined table's too, and
`by_day` cuts only the days of the table in FROM, leaving a joined table's bound as written.
So `owner_on_day` and example 3 bound their joined tables inside `ON=`, and match each row to
the joined table's row of the same day.

## The quality checks

`statements/quality_checks.py` writes the same three checks for each table `settings.py` names:

- `repeated_keys`: each key that picks out more than one row. It should find none: a repeated
  key means a join on it counts a row twice.
- `null_counts`: how many rows hold NULL in each column, every column from `all_columns`, so a
  column added to a Table reference later is checked too.
- `rows_per_day`: each day's rows, and each of its `add_up` columns added up, so a day much
  bigger or smaller than the rest stands out.

To check one more table, write its Table reference, add its dict to `settings.py` and to
`TABLES_READ` there, and add its Table reference to `TABLE_REFERENCES` in `quality_checks.py`.
`settings.py` names each table and its key again, rather than importing the Table references:
it is Level 0, as they are, and a script imports only from lower Levels. Two more checks are written by hand:
`costs_billed_and_saved`, the cents `ops.region_costs` holds for the days against the cents
example 1 saved, which must be equal, and `jobs_not_run`, the jobs with an owner but no event
on a day. `every_check(first_day, last_day)` gives them all by name, and `run_pipeline.py`'s
`check_all(send, day)` runs them and returns the results as pandas DataFrames.

## Reviewing an edit with lineage

`events_per_job_day` first counted a run's minutes only when it finished. A run that fails
uses the cluster too, so this line was edited to count a fail's minutes as well:

```diff
-    ends_a_run = equals(job_events.event_type, "finish")
+    ends_a_run = is_in(job_events.event_type, ["finish", "fail"])
```

Before editing a Building block, write the lineage of everything it feeds; after, write it
again, and compare the two Markdown files, side by side or with
`git diff --no-index lineage/review_before_edit.md lineage/review_after_edit.md`. `write_lineage_review(day, to=...)` in
`run_pipeline.py` writes the lineage of example 2's write, which reads the Building block, and
of example 3's, which reads what example 2 saves. `lineage/review_before_edit.md` was written
before the edit, and `lineage/review_after_edit.md` after. Compared, they differ only in how
`events_per_job_day.minutes` is worked out, in the Python and in the Hive. Each file shows that
column copied into `mart.job_day_facts`' minutes and, through it, summed into `mart.team_days`'
minutes: those are the two outputs the edit reaches.

## Running it here, on the Example database

Python must find the Toolbox's two folders, `composer_core` and `sqlglot_composer`: put them
beside `run_pipeline.py`, or name the folder holding them in `PYTHONPATH`. In the Toolbox's own
repository they are two folders up, so in this folder:

```
PYTHONPATH=../.. python run_pipeline.py
```

or, in the Windows command prompt:

```
set PYTHONPATH=..\..
python run_pipeline.py
```

That prints the Hive of every step for the last 3 days up to the Example database's last day,
in order, each headed by its name, such as `-- 4 of 12: write_job_day_costs[0]`, the first day
of example 1's writes, without sending anything (a dry run).

The scripts import the Toolbox as `from sqlglot_composer import ...`, the folder of the Edition
they are written for. With the other Edition, write its folder's name in each import instead.

Each step that runs takes `send=`: a function that takes a Hive string and returns a pandas
DataFrame, such as `lambda hive: spark.sql(hive).toPandas()` at work. Here it is
`example_database.send`. The Example database can be read but not written, so try the
`preview` steps and the quality checks there, in Python started in this folder:

```python
from sqlglot_composer import example_database, run
from statements import example_1_job_day_costs as example_1
from statements import example_2_owner_as_of as example_2
from statements import example_3_team_week as example_3
from statements import quality_checks

run(example_1.preview("2026-09-24"), send=example_database.send)
run(example_2.preview("2026-09-18"), send=example_database.send)
run(example_2.newest_owners_by_newest_day("2026-09-24"), send=example_database.send)
run(example_3.team_day_from_job_events("2026-09-18"), send=example_database.send)
run(quality_checks.jobs_not_run("2026-09-22", "2026-09-24"), send=example_database.send)
```

`example_2.preview("2026-09-18")` shows report_build (job 3) in finance, and
`preview("2026-09-14")` in data. `example_1.preview("2026-09-24")` shows job 2's cost as NaN,
pandas' way of showing NULL, and so job 1's as 100.0 rather than 100: a column holding NaN is
a column of floats in pandas.

Example 3's `preview` and `week_totals`, and the check `costs_billed_and_saved`, read the Saved
tables, which only your warehouse holds.

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
3. Change `settings.py`, the Building blocks and the Statements to read your tables.
4. Check a day with `run(example_1.preview(day), send=run_query)`, print everything with
   `dry_run(day)` from `run_pipeline.py`, then send it all on every run with
   `send_all(run_query, day)`, and check what it wrote with `check_all(run_query, day)`. For a
   backfill, pass the first day to write: `send_all(run_query, day, backfill_from=first_day)`.
5. Run `write_lineage_files(day)` after a change, and keep the lineage files with your
   scripts, so a reviewer can see where each column comes from. Before editing a Building
   block, write `write_lineage_review(day, to=...)` to a file of its own to compare with after.
