"""Save a table

For: Getting started

## Goal

Keep a Statement's result in a Saved table: a real table in the warehouse that your Statements
write into, a Partition at a time, or whole for a table that isn't partitioned, and that other
Statements then read like any other table. You
describe the table in a Table reference, create it, fill a day's Partition, add more rows to
it, and rebuild the table when its columns change.

## When you'd use it

When a result is slow to work out, or many notebooks and dashboards read it, it is cheaper to
work it out once a day and save it than to work it out again every time someone asks. A Saved
table also keeps each day's rows as they were on the day they were written.

The Example database can be read but not written to, so on this page each write shows its
Hive, ready to paste, and a step that sends a write sends it to `example_database.execute`,
which prints its first line and changes nothing. At work, `run` sends the same Statements to
your warehouse, through your own execute.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts

### Describe the Saved table

The table this how-to saves, mart.runs_to_review, holds the runs someone should look at each
day: the runs that failed, and the runs that succeeded but raised a high alert. Like every
table, it gets a Table reference: its name, its columns and their types, its partition
column and its key. `write_table_reference` can't write this one for you, since the table doesn't
exist yet, so you write it by hand, as [Describe a table by hand](#describe_a_table_by_hand)
shows argument by argument:

>>> runs_to_review = Table(
...     "mart.runs_to_review",
...     columns={
...         "run_id": "bigint",
...         "job_id": "bigint",
...         "dt": "string",  # the day the run happened, as yyyy-MM-dd
...     },
...     partitioned_by=["dt"],
...     key=["run_id"],
...     location="/data/your_team/mart.db/runs_to_review",
...     purge=True,
... )

- Name a database you are allowed to write to, here mart; the tables you read, such as
  `ops.job_runs`, usually belong to someone else.
- Write each type as the warehouse's DESCRIBE prints it, such as `"bigint"`, `"int"` or `"string"`.
- `partitioned_by=["dt"]` makes the table stored a Partition, here a day, at a time: a write
  replaces or adds to the Partitions it fills, and every Statement that reads the table filters
  `runs_to_review.dt`.
- `key=["run_id"]` names the table's Key, the columns that tell one row from another: no two
  rows of a day share a `"run_id"`. The warehouse never checks it, so the Toolbox does: each
  write below must show that every row it writes has a `"run_id"` of its own, or it is
  refused, as [Keys](#keys) shows. It also warns when a join could repeat rows, as
  [Guards, Warnings and opt-outs](#guards_warnings_and_opt_outs) shows.
- `location="/data/your_team/mart.db/runs_to_review"` is the table's own folder, used exactly
  as written: ask whoever looks after your warehouse where you may write. No two of your Saved
  tables may share a folder, or have one inside the other, and the Toolbox refuses two that do:
  two tables in one folder read each other's files.
- `purge=True` makes dropping the table delete its files too, as the last step below needs.
  Without it, the warehouse forgets a dropped table but keeps its files, and a table created
  in the same folder again gets its old rows back once their Partitions are listed again, as
  `repair_partitions` does.

At work, keep this in its own file, as the gallery's
[Saved table example](examples.html#saved_table) does, so every Statement that writes or reads
the table imports the same reference.

### Create it

`create_table` makes the Statement that creates the table from its Table reference. Like
every Statement, it is built first and sent later:

>>> create = create_table(runs_to_review)
>>> text = show_hive(create)
CREATE EXTERNAL TABLE mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/runs_to_review'
TBLPROPERTIES (
  'external.table.purge'='true'
);

EXTERNAL and LOCATION make it a table whose files are yours, in its own folder.
`PARTITIONED BY (dt STRING)` is its partition column: the table keeps each day apart.
`STORED AS ORC` is the file format the warehouse saves it in. TBLPROPERTIES holds
`purge=True`.
[Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) shows the rest of
what a Saved table's Table reference can say about how it is kept.

`PRIMARY KEY (run_id) DISABLE NOVALIDATE` writes the Key into the table, for whoever reads
it: `DISABLE NOVALIDATE` says Hive keeps it as information only, and never checks it.

You send it once. If the table already exists, the warehouse refuses to create it again, on
purpose: after you edit the Table reference, sending this again can't quietly look as if it
changed the real table. In a notebook you run from the top every day, use `may_exist=True`
instead, which skips the table when it is already there and never changes it:

>>> create_if_missing = create_table(runs_to_review, may_exist=True)
>>> text = show_hive(create_if_missing)
CREATE EXTERNAL TABLE IF NOT EXISTS mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/runs_to_review'
TBLPROPERTIES (
  'external.table.purge'='true'
);

### Look at a day's rows before you save them

A write is a SELECT with a line on top that says where its rows go. Run the SELECT on its own
first, to see the rows the write would save. These are the runs that failed on 2026-09-24.
`equals` on the partition column `job_runs.dt` reads one day's Partition:

>>> failed_on_the_day = statement(
...     SELECT(job_runs.run_id, job_runs.job_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
>>> run(failed_on_the_day, query=example_database.query)
   run_id  job_id
0     102       2

### Write a day with INSERT_OVERWRITE

`INSERT_OVERWRITE(runs_to_review, partition={"dt": day})` turns the same SELECT into a write
into one day's Partition. A daily write is a function of the day, so the same lines write any
day:

>>> def failed_runs(day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(runs_to_review, partition={"dt": day}),
...         SELECT(job_runs.run_id, job_runs.job_id),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day), equals(job_runs.status, "FAILED")),
...     )
>>> write_failed = failed_runs("2026-09-24")
>>> text = show_hive(write_failed)
INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')
SELECT
  job_runs.run_id,
  job_runs.job_id
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED';

Three things to notice:

- The SELECT doesn't list the partition column, dt. `partition={"dt": day}` names its value,
  which the Toolbox writes into the first line as PARTITION(dt = '2026-09-24'). It says where
  the rows go, and WHERE which rows are read: keep them the same day.
- The SELECT lists every other column of the Table reference, each under its own name:
  `job_runs.run_id` fills `"run_id"` because the names match. A column named otherwise would
  need `AS`, such as `AS(job_runs.job_id, "job_id")`. The Toolbox puts them in the table's
  order, since the warehouse fills columns by position.
- INSERT OVERWRITE replaces whatever the day's Partition held, and no other. Sending it twice
  leaves the same rows, not twice as many, which makes it the safe first write of each day.

### Send it

`run` sends a write through your execute, where a read goes through your query: a write gives
back no rows, so `run` gives back None for it. The Example database can't be written to, so
its execute prints the first line of the Hive and changes nothing:

>>> run(write_failed, execute=example_database.execute)
execute: INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')

At work, the same `run`, with your own execute in place of `example_database.execute`, writes
the day. Send `create` first, once.

### Add rows to a day with INSERT_INTO

The second kind of run to review, one that succeeded but raised a high alert, comes from a
second table, `ops.run_alerts`. `INSERT_INTO` adds rows to the day and keeps the ones already
there. Two new pieces of SQL appear in it:

- `JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id))` pairs each alert with the
  run whose `"run_id"` matches, so one row holds columns from both tables. See
  [`JOIN`](examples.html#JOIN), and [Join tables safely](#join_tables_safely) for why a join
  can repeat rows.
- `SELECT_DISTINCT` keeps each different row once: a run that raised two high alerts would
  otherwise come out twice. See [`SELECT_DISTINCT`](examples.html#SELECT_DISTINCT).

`SELECT_DISTINCT` is also how the Toolbox sees that each row has a Key of its own: it makes one
row for each different `"run_id"` and `"job_id"`, and one `"run_id"` always comes with the same
`"job_id"`, so there is one row for each run. Without it, the write is refused, as
[Keys](#keys) shows. The Toolbox checks only the rows this write adds. Here they can't share a
`"run_id"` with the failed runs the day holds already, since these runs succeeded.

The day written is the one `partition=` names. Each table read needs a filter on its partition
column, the joined one too; here both read the same day.

>>> def alerted_runs(day: str) -> Statement:
...     return statement(
...         INSERT_INTO(runs_to_review, partition={"dt": day}),
...         # A run can raise several high alerts: DISTINCT keeps each run once.
...         SELECT_DISTINCT(job_runs.run_id, job_runs.job_id),
...         FROM(run_alerts),
...         JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...         WHERE(
...             equals(run_alerts.dt, day),
...             equals(job_runs.dt, day),  # the joined table needs its own filter too
...             equals(run_alerts.severity, "high"),
...             equals(job_runs.status, "SUCCESS"),
...         ),
...     )
>>> write_alerted = alerted_runs("2026-09-24")
>>> text = show_hive(write_alerted)
INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')
SELECT DISTINCT
  job_runs.run_id,
  job_runs.job_id
FROM ops.run_alerts AS run_alerts
JOIN ops.job_runs AS job_runs
  ON job_runs.run_id = run_alerts.run_id
WHERE
  run_alerts.dt = '2026-09-24'
  AND job_runs.dt = '2026-09-24'
  AND run_alerts.severity = 'high'
  AND job_runs.status = 'SUCCESS';

Its rows, checked first as a plain SELECT, are run 101, which succeeded but raised a high
alert:

>>> alerted_on_the_day = statement(
...     SELECT_DISTINCT(job_runs.run_id, job_runs.job_id),
...     FROM(run_alerts),
...     JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(job_runs.dt, "2026-09-24"),
...           equals(run_alerts.severity, "high"), equals(job_runs.status, "SUCCESS")),
... )
>>> run(alerted_on_the_day, query=example_database.query)
   run_id  job_id
0     101       1

### Write a day in the right order

INSERT INTO is not safe to send twice: the second time, its rows are in the day twice. So a
day is always written in the same order: the INSERT_OVERWRITE first, which clears the day,
then the INSERT_INTO. To redo a day, send both again, in that order. Keep the day's writes in
one list, in the order they are sent:

>>> def writes_for(day: str) -> list[Statement]:
...     return [failed_runs(day), alerted_runs(day)]
>>> day_writes = writes_for("2026-09-24")
>>> len(day_writes)
2

A loop sends the day's writes in order. Here it is a function that takes your own execute,
written as in [Start a Project](#start_a_project); on this page the Example database's execute
stands in for it, and prints the first line of each write:

>>> from collections.abc import Callable
>>> def send_day(day: str, execute: Callable[[str], None]) -> None:
...     for write in writes_for(day):
...         run(write, execute=execute)
>>> send_day("2026-09-24", execute=example_database.execute)
execute: INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')
execute: INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')

[Backfill a range of days](#backfill_a_range_of_days) writes many days this way, and
[Run a daily pipeline](#run_a_daily_pipeline) runs the day's steps every morning.

### Rebuild it after its columns change

Say the reviewers want each run's minutes too. Change the Table reference first:

>>> runs_to_review = Table(
...     "mart.runs_to_review",
...     columns={
...         "run_id": "bigint",
...         "job_id": "bigint",
...         "duration_mins": "int",
...         "dt": "string",
...     },
...     partitioned_by=["dt"],
...     key=["run_id"],
...     location="/data/your_team/mart.db/runs_to_review",
...     purge=True,
... )

The real table still has the old columns, and `create_table` alone would be refused by the
warehouse, since the table exists. To rebuild it, drop it and create it again. Dropping a
table is one of the changes the admin module writes, which the star import leaves out, so
import it by name. `admin.drop_table` deletes the whole table, every Partition of it, since
`purge=True` was in the Table reference when `create_table` made the table, and the Toolbox
can't bring it back; it refuses a table that isn't one of your Saved tables, and `show_hive`
says what it changes before its Hive:

>>> from sqlglot_composer import admin
>>> rebuild = [admin.drop_table(runs_to_review), create_table(runs_to_review)]
>>> text = show_hive(rebuild)
-- 1 of 2: rebuild[0]
-- admin.drop_table(mart.runs_to_review) drops the table mart.runs_to_review: the warehouse
-- forgets it, and every Statement that reads it fails until it is created again.
-- Can't be undone when the table itself has external.table.purge true, as purge=True in its
-- Table reference asks: then the table's files go too, and nothing brings them back.
-- Check first: DESCRIBE FORMATTED mart.runs_to_review shows, under Table Parameters, whether
-- external.table.purge is true in the table itself: that, not the Table reference, decides
-- whether the files go.
DROP TABLE IF EXISTS mart.runs_to_review;
<BLANKLINE>
-- 2 of 2: rebuild[1]
CREATE EXTERNAL TABLE mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT,
  duration_mins INT...
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/runs_to_review'
TBLPROPERTIES (
  'external.table.purge'='true'
);

`IF EXISTS` means the drop does nothing, rather than failing, when the table isn't there.
Each run of an admin Statement adds an entry to the Admin log, admin_log.md beside your
notebook, so you can see later what was dropped, when and by which script.

A rebuild suits any change to the columns: one removed, renamed or given another type, as well
as one added. A column only added after the others can instead be added in place, keeping the
days already written, which read NULL in it until they are written again:
`admin.add_columns(runs_to_review, query=...)`, as
[A pipeline of Saved tables](#a_pipeline_of_saved_tables) shows. For a partitioned table it
writes CASCADE, so the Partitions already there get the column too. Here the table is
young and its days are written again from their sources anyway, so the rebuild is the simpler
choice.

The writes must change too. The old `failed_runs` still selects two columns where the table now
has three, and the warehouse fills a table's columns by position, so values would land in the
wrong columns. The Toolbox refuses it as it is built:

>>> failed_runs("2026-09-24")
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(runs_to_review): it leaves out duration_mins.
...

Give each write the new column. Python looks up `runs_to_review` when the function runs, so
the functions written again here write the new table:

>>> def failed_runs(day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(runs_to_review, partition={"dt": day}),
...         SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day), equals(job_runs.status, "FAILED")),
...     )
>>> def alerted_runs(day: str) -> Statement:
...     return statement(
...         INSERT_INTO(runs_to_review, partition={"dt": day}),
...         SELECT_DISTINCT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...         FROM(run_alerts),
...         JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...         WHERE(
...             equals(run_alerts.dt, day),
...             equals(job_runs.dt, day),
...             equals(run_alerts.severity, "high"),
...             equals(job_runs.status, "SUCCESS"),
...         ),
...     )
>>> text = show_hive(failed_runs("2026-09-24"))
INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt = '2026-09-24')
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.duration_mins
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24' AND job_runs.status = 'FAILED';

Then write every day again, oldest first, as
[Backfill a range of days](#backfill_a_range_of_days) shows: the drop deleted them all.

### A table that isn't partitioned, written whole

Some results aren't kept a day at a time: each team's runs over the last two days, say, which
the next write replaces. Leave `partitioned_by=` out of such a Saved table. `create_table` then
makes it with no PARTITIONED BY, and a write fills the whole table: `INSERT_OVERWRITE` replaces
every row it holds, and its Hive names no PARTITION. Its Key here is the team, which GROUP_BY
makes one row for:

>>> jobs = example_database.jobs
>>> team_runs = Table(
...     "mart.team_runs",
...     columns={"team": "string", "runs": "bigint"},
...     key=["team"],
...     location="/data/your_team/mart.db/team_runs",
... )
>>> text = show_hive(statement(
...     INSERT_OVERWRITE(team_runs),
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     GROUP_BY(jobs.team),
... ))
INSERT OVERWRITE TABLE mart.team_runs
SELECT
  jobs.team,
  COUNT(*) AS runs
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'
GROUP BY
  jobs.team;

It reads two days of job_runs and writes their rows into the one table at once. Everything is
checked as for a write into a Partition: its Key, and that job_runs's partition column is
filtered in WHERE. It must be one of your Saved tables, with `location=`, since the write
replaces all of it.

## Check it worked

Every write above was built without a refusal, so its SELECT matches the Table reference. At
work, after sending the day's writes, read the day back from the Saved table
and count its rows: here, 2 for 2026-09-24, run 102 and run 101.

>>> saved = statement(
...     SELECT(runs_to_review.dt, AS(count_rows(), "runs")),
...     FROM(runs_to_review),
...     WHERE(equals(runs_to_review.dt, "2026-09-24")),
...     GROUP_BY(runs_to_review.dt),
... )
>>> text = show_hive(saved)
SELECT
  runs_to_review.dt,
  COUNT(*) AS runs
FROM mart.runs_to_review AS runs_to_review
WHERE
  runs_to_review.dt = '2026-09-24'
GROUP BY
  runs_to_review.dt;

Then check that the real table matches its Table reference with
[`check_table_reference`](examples.html#check_table_reference), as
[Keep a Table reference true over time](#keep_a_table_reference_true_over_time) shows.

## Common mistakes

### Selecting a partition column the write names

The day comes from `partition=`, so a write that also selects `job_runs.dt` is refused as you
build it:

>>> statement(
...     INSERT_OVERWRITE(runs_to_review, partition={"dt": "2026-09-24"}),
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(runs_to_review): it also selects dt.
...

Leave `job_runs.dt` out of SELECT, and filter the same day in WHERE.

### A partition= that names one day, and a WHERE that reads two

`partition=` says where the rows go, and WHERE which rows are read. Nothing checks that they
agree, so this write would put the failed runs of both days into 2026-09-24's Partition:

>>> two_days_into_one = statement(
...     INSERT_OVERWRITE(runs_to_review, partition={"dt": "2026-09-24"}),
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
... )

Read the same day you name. To write several days at once, leave `partition=` out and SELECT
`job_runs.dt` last: each row then goes to its own day's Partition, filled from the rows, and
show_hive prints the Session setting that needs ahead of the write. Send it first with
`run(hive_settings("dynamic_partitions"), execute=...)`:

>>> text = show_hive(statement(
...     INSERT_OVERWRITE(runs_to_review),
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
... ))
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.runs_to_review PARTITION(dt)
SELECT
  job_runs.run_id,
  job_runs.job_id,
  job_runs.duration_mins,
  job_runs.dt
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24' AND job_runs.status = 'FAILED';

[Backfill a range of days](#backfill_a_range_of_days) writes a range of days this way.

### A joined table without a filter on its partition column

Every partitioned table a Statement reads needs a filter on its partition column, the joined
one too. Leave out `job_runs.dt` and the write stops before anything runs:

>>> statement(
...     INSERT_INTO(runs_to_review, partition={"dt": "2026-09-24"}),
...     SELECT_DISTINCT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(run_alerts),
...     JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  JOIN(job_runs, ON=...) reads ops.job_runs, but filters none of its partition columns: dt.
...

The day written still comes from `partition=`; the joined table's filter only limits what it
reads. Filter `job_runs.dt` to the same day. If a run can raise an
alert after midnight, its run is from the day before, so read both days of `job_runs`:
`between(job_runs.dt, "2026-09-23", "2026-09-24")`.

### A type the warehouse spells differently

`create_table` takes each type as DESCRIBE prints it, and refuses another spelling, saying
which to write:

>>> create_table(Table("mart.runs_to_review",
...     columns={"run_id": "integer", "job_id": "bigint", "dt": "string"},
...     partitioned_by=["dt"]))
Traceback (most recent call last):
...
ValueError:
  What happened:  create_table(runs_to_review): run_id's type 'integer' isn't one create_table can use.
...

### Leaving out location=

Every Saved table is made in a folder of its own, so `create_table` refuses a Table reference
that doesn't say which:

>>> create_table(Table("mart.runs_to_review",
...     columns={"run_id": "bigint", "job_id": "bigint", "dt": "string"},
...     partitioned_by=["dt"]))
Traceback (most recent call last):
...
ValueError:
  What happened:  create_table(runs_to_review): its Table reference has no location=.
...

Add `location=` with the table's own folder, as above. The tables you only read
need none: they are someone else's, in folders of their own.

## Next

- Write many past days at once: [Backfill a range of days](#backfill_a_range_of_days).
- Build and check the SELECT a write sends, before you write it:
  [Build a first Statement and paste its Hive](#build_a_first_statement).
- Write each day's tables in order, every day: [Run a daily pipeline](#run_a_daily_pipeline).
- The same steps as functions in a file, in the gallery's
  [Saved table example](examples.html#saved_table), and each name's own entry:
  [`create_table`](examples.html#create_table),
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE),
  [`INSERT_INTO`](examples.html#INSERT_INTO) and
  [`admin.drop_table`](examples.html#admin.drop_table).
"""
