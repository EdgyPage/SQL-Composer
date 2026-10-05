"""A library of Building blocks

For: Intermediate

## Goal

Write the pieces many Statements share once, as Building blocks: functions that take the days
as arguments and give back a Derived table. You build a block from other blocks, write the two
joins people reach for most, keep the rows that have a match (a semi-join) and keep those that
don't (an anti-join), as blocks, and keep each block's name the same wherever it is used.

## When you'd use it

When the same piece, such as "the runs that started on these days", turns up in several
Statements or several notebooks. Written once, it is worked out the same way everywhere, and
fixed in one place. At work the blocks live in a file under building_blocks/, Level 1, which
the Statements import.

## Steps

### Import the Toolbox

`ops.job_events` holds what each job's runs did each day: a `"start"` row when a run starts,
then `"finish"`, `"retry"` or `"fail"`. Each job runs at most once a day, so a run is a job and
a day.

>>> from sqlglot_composer import *
>>> job_events = example_database.job_events
>>> jobs = example_database.jobs

### A block that takes arguments

A block is a plain function. Its arguments are what changes from one Statement to the next,
usually the days, and it gives back `derived("starts", statement(...))`, a Derived table other
Statements read like a table. `SELECT_DISTINCT` keeps each run once, so the block's key is
job_id and dt, and joins on both don't warn:

>>> def starts_between(first_day, last_day):
...     return derived("starts", statement(
...         SELECT_DISTINCT(job_events.job_id, job_events.dt),
...         FROM(job_events),
...         WHERE(equals(job_events.event_type, "start"),
...               between(job_events.dt, first_day, last_day)),
...     ))
>>> def finishes_between(first_day, last_day):
...     return derived("finishes", statement(
...         SELECT_DISTINCT(job_events.job_id, job_events.dt),
...         FROM(job_events),
...         WHERE(equals(job_events.event_type, "finish"),
...               between(job_events.dt, first_day, last_day)),
...     ))

Check a block on its own before building on it: read all its columns with a Statement and run
it. Over two days:

>>> recent_starts = starts_between("2026-09-23", "2026-09-24")
>>> run(statement(SELECT(all_columns(recent_starts)), FROM(recent_starts)),
...     send=example_database.send)
   job_id          dt
0       1  2026-09-23
1       1  2026-09-24
2       2  2026-09-23
3       2  2026-09-24

### A block built from other blocks: an anti-join

A run that started but has no finish is still going, or failed. To find them, keep each start
with no matching finish: SQL calls this an anti-join. `LEFT_JOIN` keeps every start, and gives a
start with no finish NULL in finishes' columns; `is_null` keeps just those.

This block reads two blocks, so it takes them as arguments rather than building them itself.
The Statement that uses it builds each block once, and hands the same one to every piece that
reads it:

>>> def unfinished_runs(starts, finishes):
...     return derived("unfinished_runs", statement(
...         SELECT(starts.job_id, starts.dt),
...         FROM(starts),
...         LEFT_JOIN(finishes, ON=all_of(equals(finishes.job_id, starts.job_id),
...                                       equals(finishes.dt, starts.dt))),
...         WHERE(is_null(finishes.job_id)),
...     ))

The days live inside the blocks, so `ON=` needs only the match. A day bound written on the
LEFT_JOIN's table in `WHERE` would throw away the very starts with no finish; the last mistake
below shows the Toolbox refusing it.

### A Statement built from the library

Over the 14 days, the unfinished runs, with each job's name:

>>> starts = starts_between("2026-09-11", "2026-09-24")
>>> finishes = finishes_between("2026-09-11", "2026-09-24")
>>> unfinished = unfinished_runs(starts, finishes)
>>> runs_to_look_at = statement(
...     SELECT(jobs.job_name, unfinished.dt),
...     FROM(unfinished),
...     JOIN(jobs, ON=equals(jobs.job_id, unfinished.job_id)),
... )
>>> text = show_hive(runs_to_look_at)
WITH starts AS (
  SELECT DISTINCT
    job_events.job_id,
    job_events.dt
  FROM ops.job_events AS job_events
  WHERE
    job_events.event_type = 'start'
    AND job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
), finishes AS (
  SELECT DISTINCT
    job_events.job_id,
    job_events.dt
  FROM ops.job_events AS job_events
  WHERE
    job_events.event_type = 'finish'
    AND job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
), unfinished_runs AS (
  SELECT
    starts.job_id,
    starts.dt
  FROM starts
  LEFT JOIN finishes
    ON finishes.job_id = starts.job_id AND finishes.dt = starts.dt
  WHERE
    finishes.job_id IS NULL
)
SELECT
  jobs.job_name,
  unfinished_runs.dt
FROM unfinished_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = unfinished_runs.job_id;
>>> run(runs_to_look_at, send=example_database.send)
       job_name          dt
0  invoice_sync  2026-09-24
1  report_build  2026-09-18

The Toolbox puts each block at the top of the Hive, once, in the order they read each other.
report_build failed on 2026-09-18, and invoice_sync is still running on 2026-09-24.

### A semi-join as a block

To keep each job that has at least one match, each once, join to a list that holds each match
once: SQL calls this a semi-join. A plain `JOIN` straight to job_events would repeat a job once
per event. The block is that list:

>>> def jobs_that_started(first_day, last_day):
...     return derived("jobs_that_started", statement(
...         SELECT_DISTINCT(job_events.job_id),
...         FROM(job_events),
...         WHERE(equals(job_events.event_type, "start"),
...               between(job_events.dt, first_day, last_day)),
...     ))
>>> started = jobs_that_started("2026-09-11", "2026-09-24")
>>> run(statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     JOIN(started, ON=equals(started.job_id, jobs.job_id)),
... ), send=example_database.send)
   job_id      job_name
0       1  nightly_load
1       2  invoice_sync
2       3  report_build

The same block gives the anti-join too: `LEFT_JOIN` it, and keep the jobs with no match.
cache_warm never ran:

>>> run(statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     LEFT_JOIN(started, ON=equals(started.job_id, jobs.job_id)),
...     WHERE(is_null(started.job_id)),
... ), send=example_database.send)
   job_id    job_name
0       4  cache_warm

### Keep each block's name the same

The name you give `derived` is what the Hive calls the block, `WITH starts AS (...)`, and what a
Lineage titles its box. Keep it the same whatever the days, so every day's Hive and Lineage read
alike and can be compared line by line, and give each different block a name of its own. A name
of the form `starts` or `unfinished_runs`, saying what one row is, does both.

### Put the library in a file

At work the blocks go in building_blocks/job_events.py, which imports its Table references
from Level 0, and each Statement imports what it needs:

    from building_blocks.job_events import finishes_between, starts_between, unfinished_runs

## Check it worked

Each run either finished or didn't, so the finished runs and the unfinished ones add up to all
of them. Read each block alone:

>>> len(run(statement(SELECT(all_columns(starts)), FROM(starts)), send=example_database.send))
28
>>> len(run(statement(SELECT(all_columns(finishes)), FROM(finishes)), send=example_database.send))
26
>>> len(run(runs_to_look_at, send=example_database.send))
2

28 runs started, 26 finished, and 2 didn't.

## Common mistakes

### Building one block twice in a Statement

A block built from blocks that builds them itself is easy to call, but a Statement that reads
it and the inner block too then holds two Derived tables called `starts`, one from each call.
The Toolbox can't tell they are the same, so it refuses:

>>> def unfinished_between(first_day, last_day):
...     return unfinished_runs(starts_between(first_day, last_day),
...                            finishes_between(first_day, last_day))
>>> still_going = unfinished_between("2026-09-11", "2026-09-24")
>>> statement(
...     SELECT(still_going.job_id, still_going.dt),
...     FROM(still_going),
...     JOIN(starts, ON=all_of(equals(starts.job_id, still_going.job_id),
...                            equals(starts.dt, still_going.dt))),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  statement(...) reads two different Derived tables called 'starts'.
...

Build each block once, keep it in a variable, and pass that variable to every block that reads
it, as `unfinished_runs(starts, finishes)` does. Two blocks copied from each other and both
still called `starts` are refused the same way: give each its own name.

### Putting the day in a block's name

A name that holds the day, such as `f"starts_{first_day}"`, changes every day. With a day
written `2026-09-23` it can't even be a name, since a Derived table's name is letters, digits
and underscores:

>>> def starts_on(day):
...     return derived(f"starts_{day}", statement(
...         SELECT_DISTINCT(job_events.job_id),
...         FROM(job_events),
...         WHERE(equals(job_events.event_type, "start"), equals(job_events.dt, day)),
...     ))
>>> starts_on("2026-09-23")
Traceback (most recent call last):
...
ValueError:
  What happened:  derived('starts_2026-09-23', ...) needs a plain name.
...

Keep the name fixed, `derived("starts", ...)`, and let the days be the block's arguments.

### Bounding the LEFT_JOIN's table in WHERE

Written without a block, an anti-join on job_events itself needs its days bounded, and `WHERE`
is the first place people put them. But a job with no match has NULL in every job_events
column, its day too, so a day bound in `WHERE` would drop the very jobs the anti-join is for.
The Toolbox refuses it:

>>> statement(
...     SELECT(jobs.job_id, jobs.job_name),
...     FROM(jobs),
...     LEFT_JOIN(job_events, ON=equals(job_events.job_id, jobs.job_id), many_matches=True),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"), is_null(job_events.job_id)),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  WHERE has job_events.dt BETWEEN '2026-09-11' AND '2026-09-24', a condition on job_events, which LEFT_JOIN brought in.
...

Move the day into `ON=`, as the message says, or use a block such as `jobs_that_started`,
which holds its days inside.

## Next

- Use the blocks in a pipeline of Saved tables: [A layered pipeline](#a_layered_pipeline).
- Look things up as of each day, a join on the day as well as the key:
  [Look things up as of a day](#look_things_up_as_of_a_day).
- The gallery's [jobs that never ran](examples.html#jobs_that_never_ran), the semi-join and
  anti-join written without blocks, its [job in steps](examples.html#step_by_step), and its
  Worked example of [`derived`](examples.html#derived).
"""
