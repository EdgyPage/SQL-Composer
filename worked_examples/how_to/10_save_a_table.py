"""Save a table

For: Getting started

## Goal

Keep a Statement's result in a Saved table: a real table in the warehouse that your Statements
write into, one day at a time, and that other Statements then read like any other table. You
describe the table in a Table reference, create it, fill a day, add more rows to a day, and
rebuild it when its columns change.

## When you'd use it

When a result is slow to work out, or many notebooks and dashboards read it, it is cheaper to
work it out once a day and save it than to work it out again every time someone asks. A Saved
table also keeps each day's rows as they were on the day they were written.

The Example database can be read but not written to, so on this page each write shows its
Hive, ready to paste, and the one step that tries to send a write shows the message the
Example database stops it with. At work, `run` sends the same Statements to your warehouse.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts

### Describe the Saved table

The table this how-to saves, mart.runs_to_review, holds the runs someone should look at each
day: the runs that failed, and the runs that succeeded but raised a high alert. Like every
table, it gets a Table reference: its name, its columns and their types, its Date partition
and its key. `write_table_reference` can't write this one for you, since the table doesn't
exist yet, so you write it by hand:

>>> runs_to_review = Table(
...     "mart.runs_to_review",
...     columns={
...         "run_id": "bigint",
...         "job_id": "bigint",
...         "dt": "string",  # the day the run happened, as yyyy-MM-dd
...     },
...     date_partition="dt",
...     key=["run_id"],
... )

- Name a database you are allowed to write to, here mart; the tables you read, such as
  `ops.job_runs`, usually belong to someone else.
- Write each type as the warehouse's DESCRIBE prints it, such as `"bigint"`, `"int"` or `"string"`.
- `date_partition="dt"` makes the table stored a day at a time: each write fills one day, and
  every Statement that reads it gives the days it reads.

At work, keep this in its own file, as the gallery's
[Saved table example](examples.html#saved_table) does, so every Statement that writes or reads
the table imports the same reference.

### Create it

`create_table` makes the Statement that creates the table from its Table reference. Like
every Statement, it is built first and sent later:

>>> create = create_table(runs_to_review)
>>> text = show_hive(create)
CREATE TABLE mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;

`PARTITIONED BY (dt STRING)` is the Date partition: the table keeps each day apart.
`STORED AS ORC` is the file format the warehouse saves it in.

You send it once. If the table already exists, the warehouse refuses to create it again, on
purpose: after you edit the Table reference, sending this again can't quietly look as if it
changed the real table. In a notebook you run from the top every day, use `may_exist=True`
instead, which skips the table when it is already there and never changes it:

>>> create_if_missing = create_table(runs_to_review, may_exist=True)
>>> text = show_hive(create_if_missing)
CREATE TABLE IF NOT EXISTS mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;

### Look at a day's rows before you save them

A write is a SELECT with a line on top that says where its rows go. Run the SELECT on its own
first, to see the rows the write would save. These are the runs that failed on 2026-09-24:

>>> failed_on_the_day = statement(
...     SELECT(job_runs.run_id, job_runs.job_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
>>> run(failed_on_the_day, send=example_database.send)
   run_id  job_id
0     102       2

### Write a day with INSERT_OVERWRITE

`INSERT_OVERWRITE(runs_to_review)` turns the same SELECT into a write. A daily write is a
function of the day, so the same lines write any day:

>>> def failed_runs(day):
...     return statement(
...         INSERT_OVERWRITE(runs_to_review),
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

- The SELECT doesn't list the Date partition, dt. The Toolbox reads the day from the WHERE,
  which must name one day, and writes it into the first line as PARTITION(dt = '2026-09-24'),
  which fills the Date partition.
- The SELECT lists every other column of the Table reference, each under its own name. The
  Toolbox puts them in the table's order, since the warehouse fills columns by position.
- INSERT OVERWRITE replaces whatever the day held. Sending it twice leaves the same rows, not
  twice as many, which makes it the safe first write of each day.

### Send it

`run` sends a write as it sends a read. The Example database can't be written to, so here it
stops, and says so:

>>> run(write_failed, send=example_database.send)
Traceback (most recent call last):
...
ValueError:
  What happened:  The Example database only answers SELECT, DESCRIBE and SHOW PARTITIONS; it can't be written to.
...

At work, the same `run`, with your own send in place of `example_database.send`, writes the
day, and gives back whatever your send returns for a write, usually an empty DataFrame. Send
`create` first, once.

### Add rows to a day with INSERT_INTO

The second kind of run to review, one that succeeded but raised a high alert, comes from a
second table, `ops.run_alerts`. `INSERT_INTO` adds rows to the day and keeps the ones already
there:

>>> def alerted_runs(day):
...     return statement(
...         INSERT_INTO(runs_to_review),
...         # A run can raise several high alerts: DISTINCT keeps each run once.
...         SELECT_DISTINCT(job_runs.run_id, job_runs.job_id),
...         FROM(run_alerts),
...         JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...         WHERE(
...             equals(run_alerts.dt, day),
...             equals(job_runs.dt, day),  # the joined table's days need a bound too
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
>>> run(alerted_on_the_day, send=example_database.send)
   run_id  job_id
0     101       1

### Write a day in the right order

INSERT INTO is not safe to send twice: the second time, its rows are in the day twice. So a
day is always written in the same order: the INSERT_OVERWRITE first, which clears the day,
then the INSERT_INTO. To redo a day, send both again, in that order. Keep the day's writes in
one list, in the order they are sent:

>>> def write_day(day):
...     return [failed_runs(day), alerted_runs(day)]
>>> day_writes = write_day("2026-09-24")
>>> len(day_writes)
2

At work, the day is sent with a loop, your own send in place of the Example database's:

    for write in write_day("2026-09-24"):
        run(write, send=example_database.send)

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
...     date_partition="dt",
...     key=["run_id"],
... )

The real table still has the old columns, and `create_table` alone would be refused by the
warehouse, since the table exists. To rebuild it, drop it and create it again.
`drop_table` deletes the whole table, every day of it, and the Toolbox can't bring it back, so
use it only on a Saved table you made:

>>> rebuild = [drop_table(runs_to_review), create_table(runs_to_review)]
>>> text = show_hive(rebuild)
-- 1 of 2: rebuild[0]
DROP TABLE IF EXISTS mart.runs_to_review;
<BLANKLINE>
-- 2 of 2: rebuild[1]
CREATE TABLE mart.runs_to_review (
  run_id BIGINT,
  job_id BIGINT,
  duration_mins INT
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC;

`IF EXISTS` means the drop does nothing, rather than failing, when the table isn't there. Then
give each write the new column, and write every day again, oldest first, as
[Backfill a range of days](#backfill_a_range_of_days) shows. Until a write selects
`job_runs.duration_mins`, the Toolbox refuses it, as the Common mistakes below show.

## Check it worked

Every write above was built without a refusal, so its SELECT matches the Table reference and
reads one day. At work, after sending the day's writes, read the day back from the Saved table
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

### Selecting the Date partition in a write

The day comes from the WHERE, so a write that also selects `job_runs.dt` is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(runs_to_review),
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins, job_runs.dt),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(runs_to_review): it also selects dt.
...

Leave `job_runs.dt` out of SELECT, and bound it to one day in WHERE.

### A write that doesn't select every column

After the Table reference gained `"duration_mins"`, the old write leaves it out, and the
warehouse would fill the table's columns by position, so values would land in the wrong
columns. The Toolbox refuses it:

>>> failed_runs("2026-09-24")
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(runs_to_review): it leaves out duration_mins.
...

Add `job_runs.duration_mins` to the SELECT of each write.

### A write that reads more than one day

A write fills one day, so a write whose WHERE reads two days is refused when its Hive is
written, by `show_hive`, `to_hive` or `run`:

>>> two_days = statement(
...     INSERT_OVERWRITE(runs_to_review),
...     SELECT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24"),
...           equals(job_runs.status, "FAILED")),
... )
>>> text = show_hive(two_days)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(runs_to_review) covers 2 days.
...

Split it into one write per day with `by_day`, as
[Backfill a range of days](#backfill_a_range_of_days) shows.

### A joined table without a bound on its days

Every table with a Date partition needs its days bounded, the joined one too. Leave out
`job_runs.dt` and the write stops before anything runs:

>>> statement(
...     INSERT_INTO(runs_to_review),
...     SELECT_DISTINCT(job_runs.run_id, job_runs.job_id, job_runs.duration_mins),
...     FROM(run_alerts),
...     JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
...     WHERE(equals(run_alerts.dt, "2026-09-24"), equals(run_alerts.severity, "high")),
... )
Traceback (most recent call last):
...
composer_core.refusals.LoadRefused:
  What happened:  JOIN(job_runs, ON=...) reads ops.job_runs, but nothing bounds its Date partition dt at both ends.
...

Bound `job_runs.dt` in WHERE too, to the same day, or from the day before if a run can raise
an alert after midnight.

### A type the warehouse spells differently

`create_table` takes each type as DESCRIBE prints it, and refuses another spelling, saying
which to write:

>>> create_table(Table("mart.runs_to_review",
...     columns={"run_id": "integer", "job_id": "bigint", "dt": "string"},
...     date_partition="dt"))
Traceback (most recent call last):
...
ValueError:
  What happened:  create_table(runs_to_review): run_id's type 'integer' isn't one create_table can use.
...

## Next

- Write many past days at once: [Backfill a range of days](#backfill_a_range_of_days).
- Write each day's tables in order, every day: [Run a daily pipeline](#run_a_daily_pipeline).
- The same steps as functions in a file, in the gallery's
  [Saved table example](examples.html#saved_table), and each name's own entry:
  [`create_table`](examples.html#create_table),
  [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE),
  [`INSERT_INTO`](examples.html#INSERT_INTO) and [`drop_table`](examples.html#drop_table).
"""
