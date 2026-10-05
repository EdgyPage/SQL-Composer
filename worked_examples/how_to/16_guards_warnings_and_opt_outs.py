"""Guards, Warnings and opt-outs

For: Getting started

## Goal

Know the three ways the Toolbox stops a Statement, or warns about it, as you build it, read
what each says, and decide, case by case, whether to make the message's usual fix or to add
its opt-out. Most of the time the fix is right; this how-to shows the cases where the opt-out
is.

## When you'd use it

Whenever a Statement stops with a message, or builds with a Warning, and before you add an
opt-out to make one go away.

The three kinds:

- A Guard refuses a Statement that would silently give a wrong answer, such as a sum that
  counts some rows twice. It stops with a `GuardRefused`.
- A Warning lets the Statement through, but says why a number may come out wrong. It is
  used where the risky Statement is often the one you meant.
- A Load limit refuses a Statement that would cost the cluster or your notebook too much;
  its answer would have been right. It stops with a `LoadRefused`.
  [Keep queries small with Load limits](#keep_queries_small_with_load_limits) covers those.

Every message has the same four parts: what happened, why it matters, the usual fix, and the
opt-out, which is a keyword to add to one of your own calls, or "none" when there is no way
around it.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> jobs = example_database.jobs
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts

### A Guard with no opt-out

Some mistakes are never what you meant, so their Guard has no opt-out. A calculation needs a
name, or the warehouse makes one up:

>>> SELECT(count_rows())
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  SELECT has a calculation with no name: COUNT(*).
  Why it matters: Without a name, the warehouse makes one up, such as _c0 or count(1), and that is the name pandas would show you.
  Usual fix:      Name it with AS, as in SELECT(AS(count_rows(), "runs")).
  Opt-out:        none - a calculation always needs a name.

The Guard stops at the call that made the mistake, `SELECT`, before the Statement is built.
Make the usual fix, `AS(count_rows(), "runs")`, and go on.

### A Warning whose usual fix is right

How many minutes did each job run on 2026-09-24, counting only the runs that raised an alert?
Joining each run to its alerts looks right, but a run can raise several alerts. The Toolbox
knows, since the Table reference of `ops.run_alerts` says one alert, not one run, makes a row:
its key is `run_alerts.alert_id`. So it builds the Statement, with a Warning at the JOIN:

>>> alert_minutes = statement(
...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(run_alerts.dt, "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )

In a notebook, the Warning shows under the cell, at your own line; it doesn't stop anything.
Run the Statement, and the numbers are too big:

>>> run(alert_minutes, send=example_database.send)
   job_id  minutes
0       1       70
1       2       20
2       3       60

Job 1's runs that day took 10 and 40 minutes, 50 in all, but run 101 raised three alerts, so
its 10 minutes were counted three times. The Warning's usual fix is right here: group the
alerts first, so there is one row per run, and join that. A Derived table does it:
`derived("alerts_per_run", statement(...))` gives a Statement a name, so another Statement
can read it like a table. It is never saved; the Hive writes it at the top, as `WITH alerts_per_run AS (...)`.
See [`derived`](examples.html#derived).

>>> alerts_per_run = derived("alerts_per_run", statement(
...     SELECT(run_alerts.run_id, AS(count_rows(), "alerts")),
...     FROM(run_alerts),
...     WHERE(equals(run_alerts.dt, "2026-09-24")),
...     GROUP_BY(run_alerts.run_id),
... ))
>>> alert_minutes = statement(
...     SELECT(job_runs.job_id, AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     JOIN(alerts_per_run, ON=equals(alerts_per_run.run_id, job_runs.run_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(job_runs.job_id),
... )
>>> run(alert_minutes, send=example_database.send)
   job_id  minutes
0       1       50
1       2       20
2       3       30

No Warning this time. The Toolbox takes a Derived table's `GROUP_BY` columns as its key, so
it knows `alerts_per_run` has one row per run, and each run matches once. Its Hive:

>>> text = show_hive(alert_minutes)
WITH alerts_per_run AS (
  SELECT
    run_alerts.run_id,
    COUNT(*) AS alerts
  FROM ops.run_alerts AS run_alerts
  WHERE
    run_alerts.dt = '2026-09-24'
  GROUP BY
    run_alerts.run_id
)
SELECT
  job_runs.job_id,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
JOIN alerts_per_run
  ON alerts_per_run.run_id = job_runs.run_id
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  job_runs.job_id;

### A Warning whose opt-out is right

How many runs failed per job, keeping the jobs that had none? `LEFT_JOIN` keeps every job,
with or without a matching run. With `LEFT_JOIN`, the conditions on the joined table, its days
and the status too, go in `ON=`: in WHERE they would undo the `LEFT_JOIN`, as the Guard below
shows. Each job matches many runs, so the Toolbox warns again:

>>> failed_per_job = statement(
...     SELECT(jobs.job_name,
...            AS(count_rows(where=is_not_null(job_runs.run_id)), "failed_runs")),
...     FROM(jobs),
...     LEFT_JOIN(job_runs, ON=all_of(
...         equals(job_runs.job_id, jobs.job_id),
...         between(job_runs.dt, "2026-09-23", "2026-09-24"),
...         equals(job_runs.status, "FAILED"),
...     )),
...     GROUP_BY(jobs.job_name),
... )

But this time one row per matching run is exactly what is wanted: each job's row is repeated
once per failed run, and the Statement counts those repeats. The numbers are right:

>>> run(failed_per_job, send=example_database.send)
       job_name  failed_runs
0    cache_warm            0
1  invoice_sync            1
2  nightly_load            0
3  report_build            1

So add the Warning's opt-out, `many_matches=True`, to the call it names, `LEFT_JOIN`. It says
to the next reader, and to the Toolbox, that the repeats are meant, and the Warning goes:

>>> failed_per_job = statement(
...     SELECT(jobs.job_name,
...            AS(count_rows(where=is_not_null(job_runs.run_id)), "failed_runs")),
...     FROM(jobs),
...     LEFT_JOIN(job_runs, ON=all_of(
...         equals(job_runs.job_id, jobs.job_id),
...         between(job_runs.dt, "2026-09-23", "2026-09-24"),
...         equals(job_runs.status, "FAILED"),
...     ), many_matches=True),
...     GROUP_BY(jobs.job_name),
... )

`count_rows(where=is_not_null(job_runs.run_id))` counts only rows with a run: a job with no
failed run still gets one row from `LEFT_JOIN`, with nothing in `job_runs`' columns, and that
row shouldn't count as a failure.

### A Guard whose opt-out is almost never right

Put the condition on the status in `WHERE` instead of in `LEFT_JOIN`'s `ON=`, and a Guard
stops it:

>>> statement(
...     SELECT(jobs.job_name,
...            AS(count_rows(where=is_not_null(job_runs.run_id)), "failed_runs")),
...     FROM(jobs),
...     LEFT_JOIN(job_runs, ON=all_of(
...         equals(job_runs.job_id, jobs.job_id),
...         between(job_runs.dt, "2026-09-23", "2026-09-24"),
...     ), many_matches=True),
...     WHERE(equals(job_runs.status, "FAILED")),
...     GROUP_BY(jobs.job_name),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  WHERE has job_runs.status = 'FAILED', a condition on job_runs, which LEFT_JOIN brought in.
...

`WHERE` runs after the join, and a job with no failed run has nothing in `job_runs`' columns,
so the condition throws it away again: `LEFT_JOIN` would quietly act as `JOIN`. The usual fix,
moving the condition into `ON=`, is the Statement above. The opt-out, `keeps_only_matches=True`,
keeps the Statement as written. It is right only if you want the jobs that have a match, and
then `JOIN` says so plainly, with no opt-out needed.

### When an opt-out is right

Each opt-out says "I know, and I mean it". Add one only when the message's "why it matters"
doesn't apply to what you want:

- `many_matches=True` on a `JOIN` or `LEFT_JOIN`: when one row per match is the point, such as
  counting matches, or listing each alert beside its run.
- `reads_all_partitions=True` on `FROM` or a join: for a small table you truly need every day
  of, such as a calendar table.
- `returns_all_rows=True` on `statement(...)`: when you know the result fits in your notebook.
- `adds_up=True` on a sum: when what the Toolbox takes for a column that doesn't add up, such
  as an average or a column the Table reference lists in `does_not_add_up=[...]`, really does.
  For a listed column, the Table reference is then wrong: fix its list, rather than opt out in
  every Statement.
- `sorts_everything=True` on `ORDER_BY`: for a result you know is small, as
  [Keep queries small with Load limits](#keep_queries_small_with_load_limits) shows.
- `CROSS_JOIN` in place of `JOIN` with no `ON=`: when you mean every row with every row, such
  as every job with every day.
- `keeps_only_matches=True` on `LEFT_JOIN`: almost never; write `JOIN`.

When the opt-out would hide a mistake, make the fix instead, however long it takes.

### Catch a refusal in your own code

A Guard raises `GuardRefused`, and a Load limit `LoadRefused`, both Toolbox names. A loop
that builds many Statements can catch them, note which one was refused, and go on. The
message's first line is blank, so its second, `str(refused).splitlines()[1]`, is What happened:

>>> try:
...     statement(SELECT(job_runs.run_id), FROM(job_runs))
... except LoadRefused as refused:
...     print("Not built:", str(refused).splitlines()[1].strip())
Not built: What happened:  FROM(job_runs) reads ops.job_runs, but nothing bounds its Date partition dt at both ends.

## Check it worked

The fixed Statements build with no Warning and no refusal, and their numbers match what the
tables hold: job 1's runs with alerts took 10 + 40 = 50 minutes, and two of the four jobs had
a failed run.

>>> run(alert_minutes, send=example_database.send)["minutes"].tolist()
[50, 20, 30]
>>> run(failed_per_job, send=example_database.send)["failed_runs"].tolist()
[0, 1, 0, 1]

## Common mistakes

### Reaching for the opt-out first

Add the Guard's opt-out to make the message go away, and the Statement runs, but the jobs
with no failed run are gone, and nothing says so:

>>> only_failed = statement(
...     SELECT(jobs.job_name,
...            AS(count_rows(where=is_not_null(job_runs.run_id)), "failed_runs")),
...     FROM(jobs),
...     LEFT_JOIN(job_runs, ON=all_of(
...         equals(job_runs.job_id, jobs.job_id),
...         between(job_runs.dt, "2026-09-23", "2026-09-24"),
...     ), many_matches=True, keeps_only_matches=True),
...     WHERE(equals(job_runs.status, "FAILED")),
...     GROUP_BY(jobs.job_name),
... )
>>> run(only_failed, send=example_database.send)
       job_name  failed_runs
0  invoice_sync            1
1  report_build            1

Read the message's "why it matters" first, and make the usual fix unless it doesn't apply.

### The opt-out on the wrong call

An opt-out goes on the call the message names, such as `LEFT_JOIN(job_runs, ON=...,
many_matches=True)`. On another call, Python itself refuses the keyword:

>>> statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
...     many_matches=True,
... )
Traceback (most recent call last):
...
TypeError: statement() got an unexpected keyword argument 'many_matches'

Copy the opt-out from the message as it is written: it names the call, such as
`LEFT_JOIN(job_runs, ON=..., many_matches=True)`.

### Comparing with None

`equals(job_runs.status, None)` looks like a way to find the runs with no status, but in SQL
nothing equals a missing value, so it would match no rows. A Guard with no opt-out stops it:

>>> equals(job_runs.status, None)
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  equals(job_runs.status, None) compares with None.
...

Use `is_null(job_runs.status)`, as the message says.

## Next

- Keep queries small with the Load limits you switch on:
  [Keep queries small with Load limits](#keep_queries_small_with_load_limits).
- Build many Statements in a loop, and catch the ones refused:
  [Generate Statements in a loop](#generate_statements_in_a_loop).
- The gallery's Worked examples of what each one catches:
  [repeated rows](examples.html#repeated_rows),
  [a LEFT_JOIN then WHERE](examples.html#left_join_then_where),
  [None in equals](examples.html#none_in_equals) and
  [adding up again](examples.html#regrouping), and the
  [`GuardRefused`](examples.html#GuardRefused) entry.
"""
