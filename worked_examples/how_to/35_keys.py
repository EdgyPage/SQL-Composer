"""Keys, checked before each write

For: Intermediate

## Goal

Give each Saved table a Key, the columns that tell one row from another, and let the Toolbox
check it: a write whose rows the Toolbox can't see are one per Key is refused before anything
is sent, and Lineage shows which columns are in each step's Key and where one was lost.

## When you'd use it

Every time you make a Saved table. Hive never checks a Key: a table declared
with one takes two rows with the same Key without a word. Then every join on that Key repeats
rows, and every sum over the join comes out too big, far from the write that caused it. The
Toolbox checks the Key while the write is built, where the mistake is.

## Steps

### Import the Toolbox and name the tables

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs
>>> run_alerts = example_database.run_alerts

### Give the Saved table a Key

mart.job_day will hold one row for each job on each day: its runs and its minutes. Its Key
says so, with `key=`:

>>> job_day = Table(
...     "mart.job_day",
...     columns={"job_id": "bigint", "runs": "bigint", "minutes": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
...     location="/data/your_team/tables",
... )

`location=` is the folder your Saved tables go in, as
[Choose how a Saved table is stored](#choose_how_a_saved_table_is_stored) shows.

The Key holds the Date partition, `job_day.dt`, since a job has a row on every day. A write
fills one day, so within a write every row has the same `job_day.dt`: the Toolbox checks that
the write has one row for each `"job_id"`.

A Key may also leave the Date partition out, as `key=["run_id"]` does in
[Save a table](#save_a_table): a write is checked the same way. Name the Date partition when
the same value comes back on every day, as a job does here, so the Key says what one row is
over all the days; leave it out when each value appears on one day only, as a run does.

### A write that shows its Key

`GROUP_BY(job_runs.job_id)` makes one row for each `"job_id"`, so the Toolbox can see the Key
holds, and builds the write:

>>> def write_day(day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(job_day),
...         SELECT(job_runs.job_id, AS(count_rows(), "runs"),
...                AS(sum_of(job_runs.duration_mins), "minutes")),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day)),
...         GROUP_BY(job_runs.job_id),
...     )
>>> text = show_hive(write_day("2026-09-24"))
INSERT OVERWRITE TABLE mart.job_day PARTITION(dt = '2026-09-24')
SELECT
  job_runs.job_id,
  COUNT(*) AS runs,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id;

### A write that can't show it is refused

Leave GROUP_BY out, and the write would save one row for each run: a job with two runs that
day would have two rows with the same Key. It is refused as it is built:

>>> statement(
...     INSERT_OVERWRITE(job_day),
...     SELECT(job_runs.job_id, AS(job_runs.run_id, "runs"),
...            AS(job_runs.duration_mins, "minutes")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_day) can't show that each row it writes has a Key (job_id, dt) of its own: job_runs' rows are told apart by run_id, not by job_id.
...

`job_runs`' own Key is `"run_id"`: without GROUP_BY, the rows written are its rows, one for each
run, and nothing makes them one for each job.

### The ways the Toolbox sees a Key

The Toolbox looks at how a write makes its rows. Each of these shows a Key:

- **GROUP_BY over the Key's columns**, as above: one row for each group.
- **SELECT_DISTINCT**: one row for each different row. A column whose value another column
  already fixes doesn't count: one `job_runs.run_id` always comes with the same
  `job_runs.job_id`, so SELECT_DISTINCT of both makes one row for each run.
- **row_number(...) kept at 1 for each Key**, in a Derived table, as
  [The latest row per key](#latest_row_per_key) does: one row for each `PARTITION_BY=` value.
- **The rows of the table in FROM, by its own Key**, when SELECT returns that Key's columns,
  and each join matches its joined table's whole Key, so each row from FROM meets at most one
  row of the joined table. A SEMI_JOIN or ANTI_JOIN keeps the Key whatever its ON= matches,
  since it never repeats a row; a FULL_JOIN loses it, since either side's columns may be NULL.
  [Semi-, anti- and full joins](#semi_anti_and_full_joins) shows each.

Here the last two are used together: each job's newest run, numbered in a Derived table, then
joined to `ops.jobs` on its whole Key, `jobs.job_id`, which keeps one row for each job:

>>> newest_run = Table(
...     "mart.newest_run",
...     columns={"job_id": "bigint", "run_id": "bigint", "team": "string", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> def write_newest(day: str) -> Statement:
...     numbered = derived("numbered", statement(
...         SELECT(job_runs.job_id, job_runs.run_id,
...                AS(row_number(PARTITION_BY=job_runs.job_id,
...                              ORDER_BY=descending(job_runs.run_id)), "newest_first")),
...         FROM(job_runs),
...         WHERE(equals(job_runs.dt, day)),
...     ))
...     return statement(
...         INSERT_OVERWRITE(newest_run),
...         SELECT(numbered.job_id, numbered.run_id, jobs.team),
...         FROM(numbered),
...         JOIN(jobs, ON=equals(jobs.job_id, numbered.job_id)),
...         WHERE(equals(numbered.newest_first, 1)),
...     )
>>> newest = write_newest("2026-09-24")

`INSERT_INTO` is checked the same way, on the rows it adds. The rows the day holds already may
share a Key with them, which the Toolbox can't see: [`check_key`](examples.html#check_key), in
Check it worked below, finds them once the day is written.

### When the rows are one per Key for a reason the Toolbox can't see

Sometimes you know more than the Toolbox can see: a table whose rows are one per job for a
reason no Table reference says. Then `unproven_key=True` on the write lets it through:

>>> one_per_job = statement(
...     INSERT_OVERWRITE(job_day, unproven_key=True),
...     SELECT(job_runs.job_id, AS(job_runs.run_id, "runs"),
...            AS(job_runs.duration_mins, "minutes")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )

Use it only when you are sure, and check the day with `check_key` after it is written: here
one failed run a day per job is a habit of the Example database, not a rule.

### The Key in CREATE TABLE

`create_table` makes the table, with its Key:

>>> text = show_hive(create_table(job_day))
CREATE EXTERNAL TABLE mart.job_day (
  job_id BIGINT,
  runs BIGINT,
  minutes BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/tables/mart/job_day';

`PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE` is the Key. `DISABLE NOVALIDATE` tells Hive to
keep it as information only: Hive never checks it, which is why the Toolbox does.

### Lineage shows each step's Key

`export_lineage` marks each column that is part of a Key "in the Key", and its report lists
each step's Key, or where it lost one, and whether the write's Key holds:

>>> html_file, markdown_file = export_lineage(newest, to="lineage/newest.html")
>>> keys = markdown_file.read_text(encoding="utf-8").split("### Keys")[1]
>>> print(keys.split("###")[0].strip())
The columns that tell each step's rows apart, as the Toolbox works them out. A column in one
is marked "in the Key" in the chart.
<BLANKLINE>
- derived('numbered', ...): Key (run_id), since job_runs' rows are told apart by run_id; or
  Key (job_id, newest_first), since row_number(...) numbers the rows of each job_id.
- newest: Key (job_id), since numbered's rows are told apart by job_id, newest_first, with
  newest_first held to one value; or Key (run_id), since numbered's rows are told apart by
  run_id.
- mart.newest_run's Key (job_id, dt) holds: each row written has its own.

The Derived table numbered has two Keys: each run, and each job with its number. The write
keeps number 1, holding newest_first to one value, which leaves one row for each job.

## Check it worked

The Toolbox's check sees how the rows are made; `check_key` counts the rows themselves, on the
newest day the table holds. Run it on a Saved table after its first writes, and on any table
you join to by its Key. On the Example database's `ops.job_runs`:

>>> check_key(job_runs, send=example_database.send)
ops.job_runs: the key (run_id) holds on 2026-09-24.

## Common mistakes

### Grouping by more than the Key

A GROUP_BY with one more column makes one row for each pair, not for each Key:

>>> job_status = Table(
...     "mart.job_status",
...     columns={"job_id": "bigint", "status": "string", "runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["job_id", "dt"],
... )
>>> statement(
...     INSERT_OVERWRITE(job_status),
...     SELECT(job_runs.job_id, job_runs.status, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(job_runs.job_id, job_runs.status),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_status) can't show that each row it writes has a Key (job_id, dt) of its own: GROUP_BY makes one row for each job_id, status, not one for each job_id.
...

A job with a failed run and a good one would have two rows. Either the Key is wrong, and
should be `key=["job_id", "status", "dt"]`, or the write should group by `job_runs.job_id`
alone.

### A join that can repeat rows

A join that doesn't match its joined table's whole Key can add several rows to one. A run
with two alerts comes out twice:

>>> run_and_alert = Table(
...     "mart.run_and_alert",
...     columns={"run_id": "bigint", "severity": "string", "dt": "string"},
...     date_partition="dt",
...     key=["run_id", "dt"],
... )
>>> statement(
...     INSERT_OVERWRITE(run_and_alert),
...     SELECT(job_runs.run_id, run_alerts.severity),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id), many_matches=True),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(run_alerts.dt, "2026-09-24")),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(run_and_alert) can't show that each row it writes has a Key (run_id, dt) of its own: JOIN(run_alerts, ON=...) can match several run_alerts rows to one row, so nothing makes its rows one for each run_id.
...

Two checks are at work here. JOIN's repeated-rows Warning is silenced by
`many_matches=True`, which says you mean the repeated rows. The write's Key check is not: the
Saved table's Key still says one row for each run, and these rows can repeat a run. Group the alerts first, one row for each run, as
[Join tables safely](#join_tables_safely) shows, and join that.

### Silencing the check with unproven_key=True

`unproven_key=True` doesn't make the rows one per Key: it only stops the Toolbox saying they
might not be. Reach for GROUP_BY, SELECT_DISTINCT or row_number first.

## Next

- [Join tables safely](#join_tables_safely): the repeated-rows Warning, which reads the Keys of
  the tables a Statement joins.
- [The latest row per key](#latest_row_per_key): row_number, kept at 1 for each Key.
- [Save a table](#save_a_table) and [A pipeline of Saved tables](#a_pipeline_of_saved_tables):
  writes that each show their Key.
- The gallery's [`INSERT_OVERWRITE`](examples.html#INSERT_OVERWRITE) and
  [`check_key`](examples.html#check_key).
"""
