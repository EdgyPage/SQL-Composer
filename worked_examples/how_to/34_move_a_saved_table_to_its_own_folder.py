"""Move a Saved table to its own folder

For: Intermediate

## Goal

Move a Saved table that shares its folder with other tables into a folder of its own, with
the admin module: copy its days into a new table at its own folder, compare the two, then
drop the old table and give the new one its name. Along the way, meet the admin module, the
changes to your own Saved tables that the Toolbox writes and checks for you.

## When you'd use it

When `check_table_reference` says a Saved table isn't at its own folder. That is a table made
by hand in a folder it shares with other tables, or one `create_table` made before 5.0, a
managed table, whose files the warehouse keeps where it chooses; a Saved table now keeps its
files in a folder of its own, under the folder you give. Two tables in one folder read each other's files, and an INSERT OVERWRITE of a day in
one can delete the other's files for that day, so move each one out before writing it again.
[Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) explains the
folder of its own.

## Steps

### Import the Toolbox and the admin module

The admin module holds the changes to your own Saved tables: dropping one or its old days,
adding columns, setting its properties, and moving it. The star import leaves it out, so you
import it by name, and it is plain where a notebook changes a table:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import admin

### Find the table that shares a folder

mart.job_day holds each job's starts and finishes each day. Its Table reference gives it its
own folder, /data/your_team/tables/mart/job_day:

>>> job_day = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "starts": "bigint", "finishes": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
...     location="/data/your_team/tables",
... )

The Example database holds no Saved table, so a stand-in send plays the warehouse at work: it
answers DESCRIBE FORMATTED and SHOW PARTITIONS for a mart.job_day that was made by hand in
/data/your_team/tables itself, a folder other tables share:

>>> import pandas as pd
>>> def send_at_work(hive):
...     if hive.startswith("SHOW PARTITIONS"):
...         return pd.DataFrame({"partition": ["dt=2026-09-23", "dt=2026-09-24"]})
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("starts", "bigint", ""), ("finishes", "bigint", ""),
...         ("# Partition Information", None, None), ("dt", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_day, send=send_at_work)
mart.job_day differs from its Table reference.
Problems:
  - it is at hdfs://namenode:8020/data/your_team/tables, not at its own folder /data/your_team/tables/mart/job_day. A folder that isn't a table's own may hold other tables' files: two tables in one folder read each other's files, and an INSERT OVERWRITE of a day in one can delete the other's files for that day. Move it with admin.move_to_own_folder(t, send=...).

### Check its rows first

The move copies each day as the old table reads it. Where two tables shared a day's folder,
each read the other's files too, so a day may hold rows that aren't its own. Before you move
it, check its Key on the newest day with `check_key(job_day, send=...)`, and look at a day you
know. If the rows are mixed, don't copy them: drop the table with `admin.drop_table`, create it
with `create_table`, and write its days again from their source, as
[Backfill a range of days](#backfill_a_range_of_days) does.

### Build the move

`admin.move_to_own_folder` sends DESCRIBE FORMATTED and SHOW PARTITIONS to find where the table
is and which days it holds, and gives back the steps that move it, as a list of Statements, in
order. `show_hive` prints each one, after what it does:

>>> moves = admin.move_to_own_folder(job_day, send=send_at_work)
>>> text = show_hive(moves)
-- 1 of 7: moves[0]
-- admin.move_to_own_folder(mart.job_day, send=...) moves mart.job_day to its own folder,
-- /data/your_team/tables/mart/job_day. This first step creates mart.job_day_moving there;
-- the steps after it copy each of its 2 days into it, compare the two, then drop
-- mart.job_day and give the copy its name. Send them in order, one at a time.
-- The old table's files stay where they are, since its folder may hold other tables' files
-- too: ask whoever looks after the folder before deleting any.
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_day_moving (
  job_id BIGINT,
  starts BIGINT,
  finishes BIGINT...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/tables/mart/job_day';
<BLANKLINE>
-- 2 of 7: moves[1]
-- Copies mart.job_day's rows on 2026-09-23 into mart.job_day_moving.
INSERT OVERWRITE TABLE mart.job_day_moving PARTITION(dt = '2026-09-23')
SELECT
  job_day.job_id,
  job_day.starts,
  job_day.finishes
FROM mart.job_day AS job_day
WHERE
  job_day.dt = '2026-09-23';
<BLANKLINE>
-- 3 of 7: moves[2]
-- Copies mart.job_day's rows on 2026-09-24 into mart.job_day_moving.
INSERT OVERWRITE TABLE mart.job_day_moving PARTITION(dt = '2026-09-24')
SELECT
  job_day.job_id,
  job_day.starts,
  job_day.finishes
FROM mart.job_day AS job_day
WHERE
  job_day.dt = '2026-09-24';
<BLANKLINE>
-- 4 of 7: moves[3]
-- Compares each day's rows in mart.job_day and mart.job_day_moving, and stops the move,
-- before anything is dropped, if any day differs or is missing from the copy. It gives back
-- no rows when they match.
WITH old_days AS (
  SELECT
    job_day.dt,
    COUNT(*) AS row_count
  FROM mart.job_day AS job_day
  WHERE
    NOT job_day.dt IS NULL
  GROUP BY
    job_day.dt
), copied_days AS (
  SELECT
    job_day_moving.dt,
    COUNT(*) AS row_count
  FROM mart.job_day_moving AS job_day_moving
  WHERE
    NOT job_day_moving.dt IS NULL
  GROUP BY
    job_day_moving.dt
)
SELECT
  old_days.dt,
  old_days.row_count AS old_rows,
  copied_days.row_count AS copied_rows
FROM old_days
LEFT JOIN copied_days
  ON copied_days.dt = old_days.dt
WHERE
  copied_days.row_count IS NULL OR copied_days.row_count <> old_days.row_count;
<BLANKLINE>
-- 5 of 7: moves[4]
-- Sets external.table.purge to false on mart.job_day, so that dropping it next leaves the
-- files in its folder, which other tables may read.
ALTER TABLE mart.job_day SET TBLPROPERTIES (
  'external.table.purge'='false'
);
<BLANKLINE>
-- 6 of 7: moves[5]
-- Drops the old mart.job_day: its files stay in the folder it shared. Can't be undone, so
-- send it only after the step before it, the comparison, gave back no rows.
DROP TABLE IF EXISTS mart.job_day;
<BLANKLINE>
-- 7 of 7: moves[6]
-- Gives mart.job_day_moving the name mart.job_day. Its files stay at its own folder,
-- /data/your_team/tables/mart/job_day. If this step fails, send it alone again.
ALTER TABLE mart.job_day_moving RENAME TO mart.job_day;

The new table is made at the folder the Table reference names, under a name of its own while
the old table still has the table's name. Each day is one INSERT OVERWRITE, so a day sent twice
is written once. The fourth step counts each day's rows in both tables. The fifth keeps the old
files when the old table is dropped, since the folder it shared holds other tables' files too.
Only then is the old table dropped, and the new one renamed: a renamed table keeps its folder.

### Send the steps at work

At work, send each step in turn with `run`. A step that fails raises, so the loop stops there,
and the steps after it aren't sent. The fourth step raises when a day's rows differ, before
anything is dropped. Here it is a function that takes your own send and gives back the steps,
so that one can be sent again; it isn't called on this page, since the Example database is
never written to:

>>> def move(t, send):
...     moves = admin.move_to_own_folder(t, send=send)
...     for step in moves:
...         run(step, send=send)
...     return moves

Each step that `run` sends adds an entry to the Admin log, admin_log.md beside your notebook
unless `set_admin_log` moved it: when, the call, such as
admin.move_to_own_folder(mart.job_day, send=...)[3] for the fourth step, the Hive, the script
and its git commit, and whether it worked. `show_hive` adds nothing to it.

If a step before the drop fails, fix what it says and send the steps again from the first:
creating the new table again does nothing, and each day is written again whole. If the fourth
step says a day is missing from the copy, a day was written since the steps were made, so make
them again with `admin.move_to_own_folder` and send them all. Once the old table is dropped,
the steps can't be made again, since the table they read is gone: if only the last step, the
rename, fails, send it alone again with `run(moves[-1], send=...)`, from the `moves` you made.

### Move the other tables

Each of your Saved tables that shared the folder needs the same, one at a time, each to its own
folder. Once none of them reads the old folder, its files are left over: ask whoever looks after
the folder before deleting any, since other teams' tables may read it too.

## Check it worked

Once the steps have run, the table is at its own folder. A stand-in send plays the warehouse
again, now describing the moved table:

>>> def send_after_the_move(hive):
...     if hive.startswith("SHOW PARTITIONS"):
...         return pd.DataFrame({"partition": ["dt=2026-09-23", "dt=2026-09-24"]})
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("starts", "bigint", ""), ("finishes", "bigint", ""),
...         ("# Partition Information", None, None), ("dt", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/tables/mart/job_day", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_day, send=send_after_the_move)
mart.job_day matches its Table reference.

The compare step checked that each day holds as many rows in the new table as in the old.
You can also check a day against where its rows come from. The Example database doesn't hold
mart.job_day, but it holds ops.job_events, from which mart.job_day's days are written. Its
2026-09-24 gives one row per job, two rows, so the moved mart.job_day should hold two rows on
2026-09-24 too, with these numbers:

>>> job_events = example_database.job_events
>>> run(statement(
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "start")), "starts"),
...            AS(count_rows(where=equals(job_events.event_type, "finish")), "finishes")),
...     FROM(job_events),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_events.job_id),
... ), send=example_database.send)
   job_id  starts  finishes
0       1       1         1
1       2       1         0

## Common mistakes

### Moving a table someone else owns

The admin module changes only your own Saved tables, the ones whose Table reference has
`location=`. Any other is refused before anything is sent:

>>> admin.move_to_own_folder(example_database.job_runs, send=send_at_work)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(...) was given ops.job_runs, which isn't one of your Saved tables: its Table reference has no location=.
...

### Moving a table that is at its own folder already

Once a table is at its own folder, there is nothing to move, and a move built again is refused,
so a notebook that moves a table can't move it twice:

>>> admin.move_to_own_folder(job_day, send=send_after_the_move)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(mart.job_day, send=...): mart.job_day is at its own folder already, hdfs://namenode:8020/data/your_team/tables/mart/job_day.
...

### Sending the steps out of order

Send the steps in their order, each once the one before has worked: the drop is sent only
after the compare step gave back no rows. Running only some of them, or the drop on its own,
can lose days the copy doesn't hold. If Spark rather than Hive runs your tables, ask whoever
looks after them first: Spark runs each of these steps, but may keep a managed table its own
way.

## Next

- How a Saved table is stored, and why it needs a folder of its own:
  [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored).
- Check a Table reference against its table again after the table changes:
  [Keep a Table reference true over time](#keep_a_table_reference_true_over_time).
- Write a table's days again from their source:
  [Backfill a range of days](#backfill_a_range_of_days).
- The admin module's other changes, each with its own entry in the gallery:
  [`admin.drop_table`](examples.html#admin.drop_table),
  [`admin.drop_days`](examples.html#admin.drop_days),
  [`admin.add_columns`](examples.html#admin.add_columns),
  [`admin.set_properties`](examples.html#admin.set_properties) and
  [`admin.move_to_own_folder`](examples.html#admin.move_to_own_folder).
"""
