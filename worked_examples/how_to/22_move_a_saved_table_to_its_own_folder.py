"""Move a Saved table to its own folder

For: Intermediate

## Goal

Move a Saved table that shares its folder with other tables into a folder of its own, with
the admin module: copy it whole into a new table at its own folder, compare the two, then
drop the old table and give the new one its name. Along the way, meet the admin module, the
changes to your own Saved tables that the Toolbox writes and checks for you.

## When you'd use it

When `check_table_reference` says a Saved table isn't at its own folder: a table made by hand
in a folder it shares with other tables, or one `create_table` made before 5.0, a managed
table, whose files the warehouse keeps where it chooses. A Saved table keeps its files in a
folder of its own, the one its `location=` names. Two tables in one folder read each other's
files, and an INSERT OVERWRITE of a Partition in one can delete the other's files for that
Partition, so move each one out before writing it again.

It needs [Save a table](#save_a_table) and [Keep the project in
order](#keep_the_project_in_order), which checks Table references against their tables;
[Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) explains the folder
of its own.

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, into the folder
it runs in, which Python's path holds already, as Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

The admin module holds the changes to your own Saved tables: dropping one or some of its
Partitions, adding columns, setting its properties, and moving it. The star import leaves it
out, so you import it by name, and it is plain where a notebook changes a table:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import admin, project
>>> from warehouse import execute, query
>>> from references import mart
>>> job_day_facts = mart.job_day_facts  # -> Table

### Find the table that shares a folder

mart.job_day_facts, each job's events, runs and minutes per day beside its team, is one of the
Project's Saved tables. Its Table reference, references/mart__job_day_facts.py, gives it its
own folder, /data/your_team/mart.db/job_day_facts.

The Example database holds no Saved table, so a stand-in query plays the warehouse at work: it
answers DESCRIBE FORMATTED for a mart.job_day_facts that was made by hand in
/data/your_team/tables, a folder other tables share:

>>> import pandas as pd
>>> def query_at_work(hive: str) -> pd.DataFrame:
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("team", "string", ""), ("events", "bigint", ""),
...         ("runs", "bigint", ""), ("minutes", "bigint", ""),
...         ("# Partition Information", None, None), ("dt", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_day_facts, query=query_at_work)  # -> Verdict
mart.job_day_facts differs from its Table reference.
Problems:
  - it is at hdfs://namenode:8020/data/your_team/tables, not at /data/your_team/mart.db/job_day_facts, the folder location= names: change the line to location="hdfs://namenode:8020/data/your_team/tables", if that is the own folder of the table. A folder that isn't a table's own may hold other tables' files: two tables in one folder read each other's files, and an INSERT OVERWRITE of a Partition in one can delete the other's files for that Partition. Move it with admin.move_to_own_folder(t, query=...).

Here /data/your_team/tables isn't mart.job_day_facts' own folder, so the line to change isn't
the Table reference's: the table is the one to move.

### Check its rows first

The move copies the table as it reads it. Where two tables shared a folder, each read the
other's files too, so a Partition may hold rows that aren't its own. Before you move it, check
its Key on its newest Partition, with `check_key(job_day_facts, query=query,
where=equals(job_day_facts.dt, "2026-09-24"))`, and look at a Partition you know. If the rows
are mixed, don't copy them: drop the table with `admin.drop_table`, create it with
`create_table`, and write it again from its sources, as [Rewrite some
partitions](#rewrite_some_partitions) does.

### Build the move

`admin.move_to_own_folder` sends DESCRIBE FORMATTED through your query to find where the table
is, and gives back the steps that move it, as a list of Statements, in order. `show_hive`
prints each one, after what it does:

>>> moves = admin.move_to_own_folder(job_day_facts, query=query_at_work)  # -> list[Statement]
>>> text = show_hive(moves)
-- 1 of 6: moves[0]
-- admin.move_to_own_folder(mart.job_day_facts, query=...) moves mart.job_day_facts to its
-- own folder, /data/your_team/mart.db/job_day_facts. This first step creates
-- mart.job_day_facts_moving there; the steps after it copy the table's rows into it, compare
-- the two, then drop mart.job_day_facts and give the copy its name. Send them in order, one
-- at a time.
-- The old table's files stay where they are, since its folder may hold other tables' files
-- too: ask whoever looks after the folder before deleting any.
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_day_facts_moving (
  job_id BIGINT,
  team STRING,
  events BIGINT,
  runs BIGINT,
  minutes BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day_facts';
<BLANKLINE>
-- 2 of 6: moves[1]
-- Copies all of mart.job_day_facts's rows into mart.job_day_facts_moving.
-- It fills dt from the rows, which needs the Session setting "dynamic_partitions": send
-- run(hive_settings("dynamic_partitions"), execute=...) before it.
INSERT OVERWRITE TABLE mart.job_day_facts_moving PARTITION(dt)
SELECT
  job_day_facts.job_id,
  job_day_facts.team,
  job_day_facts.events,
  job_day_facts.runs,
  job_day_facts.minutes,
  job_day_facts.dt
FROM mart.job_day_facts AS job_day_facts;
<BLANKLINE>
-- 3 of 6: moves[2]
-- Compares each Partition's rows in mart.job_day_facts and mart.job_day_facts_moving, and
-- stops the move, before anything is dropped, if any Partition differs or is missing from
-- the copy. It gives back no rows when they match.
-- Rows with no value in a partition column are counted under __HIVE_DEFAULT_PARTITION__, as
-- Hive names their Partition.
WITH old_counts AS (
  SELECT
    COALESCE(CAST(job_day_facts.dt AS STRING), '__HIVE_DEFAULT_PARTITION__') AS dt,
    COUNT(*) AS row_count
  FROM mart.job_day_facts AS job_day_facts
  GROUP BY
    COALESCE(CAST(job_day_facts.dt AS STRING), '__HIVE_DEFAULT_PARTITION__')
), copied_counts AS (
  SELECT
    COALESCE(CAST(job_day_facts_moving.dt AS STRING), '__HIVE_DEFAULT_PARTITION__') AS dt,
    COUNT(*) AS row_count
  FROM mart.job_day_facts_moving AS job_day_facts_moving
  GROUP BY
    COALESCE(CAST(job_day_facts_moving.dt AS STRING), '__HIVE_DEFAULT_PARTITION__')
)
SELECT
  old_counts.dt,
  old_counts.row_count AS old_rows,
  copied_counts.row_count AS copied_rows
FROM old_counts
LEFT JOIN copied_counts
  ON copied_counts.dt = old_counts.dt
WHERE
  copied_counts.row_count IS NULL
  OR copied_counts.row_count <> old_counts.row_count;
<BLANKLINE>
-- 4 of 6: moves[3]
-- Sets external.table.purge to false on mart.job_day_facts, so that dropping it next leaves
-- the files in its folder, which other tables may read.
ALTER TABLE mart.job_day_facts SET TBLPROPERTIES (
  'external.table.purge'='false'
);
<BLANKLINE>
-- 5 of 6: moves[4]
-- Drops the old mart.job_day_facts: its files stay in the folder it shared. Can't be undone,
-- so send it only after the step before it, the comparison, gave back no rows.
DROP TABLE IF EXISTS mart.job_day_facts;
<BLANKLINE>
-- 6 of 6: moves[5]
-- Gives mart.job_day_facts_moving the name mart.job_day_facts. Its files stay at its own
-- folder, /data/your_team/mart.db/job_day_facts. If this step fails, send it alone again.
ALTER TABLE mart.job_day_facts_moving RENAME TO mart.job_day_facts;

The new table is made at the folder the Table reference names, under a name of its own while
the old table still has the table's name. The copy is one INSERT OVERWRITE, which fills each
Partition from the rows' own dt, so sent twice it is written once. The third step counts each
Partition's rows in both tables. The fourth keeps the old files when the old table is dropped,
since the folder it shared holds other tables' files too. Only then is the old table dropped,
and the new one renamed: a renamed table keeps its folder.

### Send the steps at work

At work, send the Session setting the copy needs, then each step in turn with `run`. A step
that fails raises, so the loop stops there, and the steps after it aren't sent. The third step
raises when a Partition's rows differ, before anything is dropped. `run` sends the third step
through your query, since it reads rows, and every other step through your execute. Here it is
a function that takes your own query and execute and gives back the steps, so that one can be
sent again; it isn't called on this page, since the Example database is never written to:

>>> from collections.abc import Callable
>>> def move(t: Table, query: Callable[[str], pd.DataFrame],
...          execute: Callable[[str], None]) -> list[Statement]:
...     moves = admin.move_to_own_folder(t, query=query)
...     run(hive_settings("dynamic_partitions"), execute=execute)
...     for step in moves:
...         run(step, query=query, execute=execute)
...     return moves

Each step that `run` sends adds an entry to the Admin log, the Project's admin/admin_log.md:
when, the call, such as admin.move_to_own_folder(mart.job_day_facts, query=...)[2] for the
third step, the Hive, the script and its git commit, and whether it worked. `show_hive` adds
nothing to it.

If a step before the drop fails, fix what it says and send the steps again from the first:
creating the new table again does nothing, and the copy is written again whole. If the third
step says a Partition is missing from the copy, one was written since the copy, so send the
steps again from the first. Once the old table is dropped, the steps can't be made again, since
the table they read is gone: if only the last step, the rename, fails, send it alone again
with `run(moves[-1], execute=execute)`, from the `moves` you made.

### Move the other tables

Each of your Saved tables that shared the folder needs the same, one at a time, each to its own
folder. Once none of them reads the old folder, its files are left over: ask whoever looks after
the folder before deleting any, since other teams' tables may read it too.

## Check it worked

Once the steps have run, the table is at its own folder. A stand-in query plays the warehouse
again, now describing the moved table:

>>> def query_after_the_move(hive: str) -> pd.DataFrame:
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("team", "string", ""), ("events", "bigint", ""),
...         ("runs", "bigint", ""), ("minutes", "bigint", ""),
...         ("# Partition Information", None, None), ("dt", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/mart.db/job_day_facts", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_day_facts, query=query_after_the_move)
mart.job_day_facts matches its Table reference.

The compare step checked that each Partition holds as many rows in the new table as in the
old. You can also check a Partition against where its rows come from. The Example database
doesn't hold mart.job_day_facts, but its notebook's preview() gives the rows its write()
saves, from the tables the Example database does hold. `project.load` gives a Table notebook's
logic, its functions, as [Save a table](#save_a_table) shows:

>>> logic = project.load("mart.job_day_facts")
>>> logic
The logic of mart.job_day_facts: create, rows, preview, write_days, write.
>>> run(logic.preview(), query=query)  # -> DataFrame
   job_id     team  events  runs  minutes          dt
0       1     data       2     1       10  2026-09-22
1       1     data       2     1       10  2026-09-24
2       1     data       2     1       12  2026-09-23
3       2  finance       1     1        0  2026-09-24
4       2  finance       2     1       18  2026-09-22
5       2  finance       2     1       18  2026-09-23

The moved mart.job_day_facts should hold the same two rows on 2026-09-24, with these numbers.

## Common mistakes

### Moving a table someone else owns

The admin module changes only your own Saved tables, the ones whose Table reference has
`location=`. Any other is refused before anything is sent:

>>> from references import ops
>>> admin.move_to_own_folder(ops.job_events, query=query_at_work)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(...) was given ops.job_events, which isn't one of your Saved tables: its Table reference has no location=.
...

### Moving a table that is at its own folder already

Once a table is at its own folder, there is nothing to move, and a move built again is refused,
so a notebook that moves a table can't move it twice:

>>> admin.move_to_own_folder(job_day_facts, query=query_after_the_move)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(mart.job_day_facts, query=...): mart.job_day_facts is at its own folder already, hdfs://namenode:8020/data/your_team/mart.db/job_day_facts.
...

### Sending the steps out of order

Send the steps in their order, each once the one before has worked: the drop is sent only
after the compare step gave back no rows. Running only some of them, or the drop on its own,
can lose Partitions the copy doesn't hold.

## Next

- How a Saved table is stored, and why it needs a folder of its own:
  [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored).
- Check every Table reference against its table: [Keep the project in
  order](#keep_the_project_in_order).
- Write some of a table's Partitions again from their sources: [Rewrite some
  partitions](#rewrite_some_partitions).
- The admin module's other changes, each with its own entry in the gallery:
  [`admin.drop_table`](examples.html#admin.drop_table),
  [`admin.drop_partitions`](examples.html#admin.drop_partitions),
  [`admin.add_columns`](examples.html#admin.add_columns),
  [`admin.set_properties`](examples.html#admin.set_properties) and
  [`admin.move_to_own_folder`](examples.html#admin.move_to_own_folder).
"""
