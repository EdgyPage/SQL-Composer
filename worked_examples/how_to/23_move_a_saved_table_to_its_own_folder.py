"""Move a Saved table to its own folder

For: Intermediate

## Goal

Move a Saved table that shares its folder with other tables into a folder of its own, with
the admin module: copy it whole into a new table at its own folder, check the copy, then
drop the old table and give the new one its name. A Saved table is a real table in your
warehouse that your own Statements, the queries you build with the Toolbox, write. Along the
way, meet the admin module: the changes to your own Saved tables that the Toolbox writes and
checks for you.

## When you'd use it

- If `check_table_reference` says a Saved table isn't at its own folder, move it, as the steps
  below do.
- If a table was made by hand in a folder it shares with other tables, move it before writing
  it again: two tables in one folder read each other's files, and an INSERT OVERWRITE of a
  Partition in one can delete the other's files for that Partition.
- If `create_table` made a table before 5.0, a managed table, whose files the warehouse keeps
  where it chooses, move it to the folder of its own its `location=` names.
- If you have not saved a table or checked a Table reference yet, do
  [Save a table](#save_a_table) and [Keep the Project in order](#keep_the_project_in_order)
  first; [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) explains the
  folder of its own.

## Steps

### 1. Start from the Intermediate Example project

Goal: a Project, your folder of scripts at work, holding a Saved table. Work in a copy of the
Intermediate Example project, at its top: copy `example_projects/intermediate/` from the
download to a folder of your own, copy the `sqlglot_composer` folder into it, as a Project holds
it, and open a notebook there. This page makes the same copy in its first step, from the
download the Toolbox came in, into the folder it runs in, which Python's path holds already, as
Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Done when the folder you work in holds the Project's admin/, references/ and tables/ folders.
Then step 2.

### 2. Import the admin module

Goal: the admin module, beside the everyday names. The admin module holds the changes to your
own Saved tables: dropping one or some of its Partitions, adding columns, setting its
properties, and moving it. The star import leaves it out, so import it by name, and it is plain
where a notebook changes a table:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import admin, project
>>> from warehouse import connect, query, execute
>>> connect(example_database)
>>> from references import mart
>>> job_day_facts = mart.job_day_facts  # -> Table

Done when `job_day_facts` is set. Then step 3.

### 3. Find the table that shares a folder

Goal: know which table to move. mart.job_day_facts, each job's events, runs and minutes per day
beside its team, is one of the Project's Saved tables. Its Table reference, the file that
describes the table, references/mart__job_day_facts.py, gives it its own folder,
/data/your_team/mart.db/job_day_facts.

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
  - it is at hdfs://namenode:8020/data/your_team/tables, not at
    /data/your_team/mart.db/job_day_facts, the folder location= names: change the line to
    location="hdfs://namenode:8020/data/your_team/tables", if that is the own folder of the
    table. A folder that isn't a table's own may hold other tables' files: two tables in one
    folder read each other's files, and an INSERT OVERWRITE of a Partition in one can delete the
    other's files for that Partition. Move it with admin.move_to_own_folder(t, query=...).

Here /data/your_team/tables isn't mart.job_day_facts' own folder, so the line to change isn't
the Table reference's: the table is the one to move.

Done when the check names the folder the table shares. Then step 4.

### 4. Check its rows first

Goal: rows worth copying. The move copies the table as it reads it. Where two tables shared a
folder, each read the other's files too, so a Partition may hold rows that aren't its own.
Before you move it, check its Key, the columns that name one row, on its newest Partition, with
`check_key(job_day_facts, query=query, where=equals(job_day_facts.dt, "2026-09-24"))`, and look
at a Partition you know. If the rows are mixed, rebuild the table in place of moving it: drop it
with `admin.drop_table`, create it with `create_table`, and write it again from its sources, as
[Rewrite some partitions](#rewrite_some_partitions) does.

Done when the Key check finds nothing wrong and a Partition you know holds only its own rows.
Then step 5.

### 5. Build the move

Goal: the first two Statements of the move. The move comes in two calls, so that the old table
can't be dropped before its copy is checked. `admin.move_to_own_folder` sends DESCRIBE FORMATTED
through your query to find where the table is, and gives back the first two steps, as a list of
Statements, in order. `show_hive` prints each one, after what it does:

>>> moves = admin.move_to_own_folder(job_day_facts, query=query_at_work)  # -> list[Statement]
>>> text = show_hive(moves)
-- 1 of 2: moves[0]
-- admin.move_to_own_folder(mart.job_day_facts, query=...) moves mart.job_day_facts to its
-- own folder, /data/your_team/mart.db/job_day_facts. This first step creates
-- mart.job_day_facts_moving there, and the next copies the table's rows into it. Then
-- admin.check_the_copy compares the two and gives the steps that drop mart.job_day_facts and
-- give the copy its name. Send them in order, one at a time.
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
-- 2 of 2: moves[1]
-- Copies all of mart.job_day_facts's rows into mart.job_day_facts_moving.
-- It fills dt from the rows, which needs the Session setting "dynamic_partitions": send
-- run_execute(hive_settings("dynamic_partitions"), execute) before it.
INSERT OVERWRITE TABLE mart.job_day_facts_moving PARTITION(dt)
SELECT
  job_day_facts.job_id,
  job_day_facts.team,
  job_day_facts.events,
  job_day_facts.runs,
  job_day_facts.minutes,
  job_day_facts.dt
FROM mart.job_day_facts AS job_day_facts;

The new table is made at the folder the Table reference names, under a name of its own while
the old table still has the table's name. The copy is one INSERT OVERWRITE, which fills each
Partition from the rows' own dt, so sent twice it is written once.

Done when `moves` holds the CREATE and the INSERT OVERWRITE. Then step 6.

### 6. Check the copy, then get the steps that finish

Goal: the steps that drop the old table, given only once the copy holds every row. Once both
steps have run, `admin.check_the_copy` counts each Partition's rows in both tables, through your
query, and stops the move with a message, before anything is dropped, if any Partition differs
or is missing from the copy. When they match, it gives back the steps that finish the move. The
comparison's Hive starts `WITH old_counts`, as its entry in the Admin log shows. The stand-in
query answers it with no row, as the warehouse does when every Partition matches:

>>> def query_after_the_copy(hive: str) -> pd.DataFrame:
...     if hive.startswith("WITH old_counts"):  # the count of each Partition's rows
...         return pd.DataFrame(columns=["dt", "old_rows", "copied_rows"])
...     return query_at_work(hive)
>>> finish = admin.check_the_copy(job_day_facts,
...                               query=query_after_the_copy)  # -> list[Statement]
>>> text = show_hive(finish)
-- 1 of 3: finish[0]
-- Sets external.table.purge to false on mart.job_day_facts, so that dropping it next leaves
-- the files in its folder, which other tables may read.
ALTER TABLE mart.job_day_facts SET TBLPROPERTIES (
  'external.table.purge'='false'
);
<BLANKLINE>
-- 2 of 3: finish[1]
-- Drops the old mart.job_day_facts: its files stay in the folder it shared. Can't be undone:
-- admin.check_the_copy gives it only once the copy holds every row.
DROP TABLE IF EXISTS mart.job_day_facts;
<BLANKLINE>
-- 3 of 3: finish[2]
-- Gives mart.job_day_facts_moving the name mart.job_day_facts. Its files stay at its own
-- folder, /data/your_team/mart.db/job_day_facts. If this step fails, send it alone again.
ALTER TABLE mart.job_day_facts_moving RENAME TO mart.job_day_facts;

The first keeps the old files when the old table is dropped, since the folder it shared holds
other tables' files too. Only then is the old table dropped, and the new one renamed: a renamed
table keeps its folder.

Done when `finish` holds the three steps: keep the files, drop, rename. Then step 7.

### 7. Send the steps at work

Goal: the move made in your warehouse. At work, send the Session setting the copy needs, then
each step in turn with `run_execute`, then the check, then the steps it gives. A step that
fails raises, so the function stops there, and the steps after it aren't sent; the check raises
when a Partition's rows differ, before anything is dropped. Here it is a function that takes
your own query and execute, so that the move can be sent again; it isn't called on this page,
since the Example database is never written to:

>>> from collections.abc import Callable
>>> def move(t: Table, query: Callable[[str], pd.DataFrame],
...          execute: Callable[[str], None]) -> None:
...     run_execute(hive_settings("dynamic_partitions"), execute)
...     for step in admin.move_to_own_folder(t, query=query):
...         run_execute(step, execute)
...     for step in admin.check_the_copy(t, query=query):
...         run_execute(step, execute)

Each step `run_execute` sends, and each check, adds an entry to the Admin log, the Project's
admin/admin_log.md: when, the call, such as admin.move_to_own_folder(mart.job_day_facts,
query=...)[1] for the copy, the Hive, the script and its git commit, and whether it worked.
`show_hive` adds nothing to it.

- If a step before the drop fails, fix what it says and send the move again from the first:
  creating the new table again does nothing, and the copy is written again whole.
- If the check says a Partition is missing from the copy, one was written since the copy, so
  send the move again.
- If only the last step, the rename, fails, send it alone again with
  `run_execute(finish[-1], execute)`, from the `finish` the check gave: once the old table is
  dropped, the check can't be made again, since the table it reads is gone.

Done when the Admin log holds an entry that worked for each step. Then step 8.

### 8. Move the other tables

Goal: every Saved table that shared the folder at its own. Move each of them the same way, one
at a time, each to its own folder. Once none of them reads the old folder, its files are left
over: ask whoever looks after the folder before deleting any, since other teams' tables may
read it too.

Done when `check_table_reference` says each of those tables matches its Table reference. Then
check it worked, below.

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

The check made sure each Partition holds as many rows in the new table as in the old. You can
also check a Partition against where its rows come from. The Example database doesn't hold
mart.job_day_facts, but its notebook's preview() gives the rows its write() saves, from the
tables the Example database does hold. `project.load` gives a Table notebook's logic, its
functions, as [Save a table](#save_a_table) shows:

>>> logic = project.load("mart.job_day_facts")  # -> the notebook's functions
>>> logic
The logic of mart.job_day_facts: create, rows, preview, write_days, write.
>>> run_query(logic.preview(), query)  # -> DataFrame
   job_id     team  events  runs  minutes          dt
0       1     data       2     1       10  2026-09-22
1       1     data       2     1       10  2026-09-24
2       1     data       2     1       12  2026-09-23
3       2  finance       1     1        0  2026-09-24
4       2  finance       2     1       18  2026-09-22
5       2  finance       2     1       18  2026-09-23

The moved mart.job_day_facts should hold the same two rows on 2026-09-24, with these numbers.

Before you go on, check that:

- `check_table_reference` says mart.job_day_facts matches its Table reference;
- the moved table holds the two rows of 2026-09-24 that `logic.preview()` gives;
- no table named mart.job_day_facts_moving is left in the warehouse.

## Common mistakes

### Moving a table someone else owns

The admin module changes only your own Saved tables, the ones whose Table reference has
`location=`. Any other is refused before anything is sent:

>>> from references import ops
>>> admin.move_to_own_folder(ops.job_events, query=query_at_work)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(...) was given ops.job_events, which isn't one of
                  your Saved tables: its Table reference has no location=.
...

Move only tables whose Table reference has `location=`; ask the owner of any other table.

### Moving a table that is at its own folder already

Once a table is at its own folder, there is nothing to move, and a move built again is refused,
so a notebook that moves a table can't move it twice:

>>> admin.move_to_own_folder(job_day_facts, query=query_after_the_move)
Traceback (most recent call last):
...
ValueError:
  What happened:  admin.move_to_own_folder(mart.job_day_facts, query=...): mart.job_day_facts is
                  at its own folder already,
                  hdfs://namenode:8020/data/your_team/mart.db/job_day_facts.
...

### Dropping the table without the check

`admin.move_to_own_folder` gives no step that drops anything: the drop comes only from
`admin.check_the_copy`, once the copy holds every row. A DROP written by hand, or
`admin.drop_table`, sent before the check, can lose Partitions the copy doesn't hold. Send the
drop only as `admin.check_the_copy` gives it.

## Next

- How a Saved table is stored, and why it needs a folder of its own:
  [Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored).
- Check every Table reference against its table: [Keep the Project in
  order](#keep_the_project_in_order).
- Write some of a table's Partitions again from their sources: [Rewrite some
  partitions](#rewrite_some_partitions).
- The admin module's other changes, each with its own entry in the gallery:
  [`admin.drop_table`](examples.html#admin.drop_table),
  [`admin.drop_partitions`](examples.html#admin.drop_partitions),
  [`admin.add_columns`](examples.html#admin.add_columns),
  [`admin.set_properties`](examples.html#admin.set_properties),
  [`admin.move_to_own_folder`](examples.html#admin.move_to_own_folder) and
  [`admin.check_the_copy`](examples.html#admin.check_the_copy).
"""
