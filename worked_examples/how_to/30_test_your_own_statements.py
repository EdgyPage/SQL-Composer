"""Test your own Statements

For: Intermediate

## Goal

Check that a Statement gives the numbers you meant, not just numbers. Work out the same answer
a second way, in pandas, from the rows themselves, and compare the two with plain `assert`s in
your notebook, on several ranges of days. A careless Statement fails; the fixed one passes.

## When you'd use it

When a Statement's numbers will be read by other people, before you save them to a table or
send them on, and after every change to a Building block it reads. The Toolbox's Guards and
Warnings catch mistakes of a known shape, such as a missing day bound or a join that repeats
rows; only a test catches a Statement that counts the wrong thing.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> import pandas as pd
>>> job_events = example_database.job_events

### A careless Statement

The question: over a range of days, how many runs did each job finish, and how many minutes did
those runs take? `ops.job_events` has a row per event, and a run's finish event says how many
minutes it took. This first try counts every row of each job, and adds up every row's minutes:

>>> def careless_finished_runs(first_day, last_day):
...     return statement(
...         SELECT(job_events.job_id,
...                AS(count_rows(), "finished"),
...                AS(sum_of(job_events.minutes), "minutes")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day)),
...         GROUP_BY(job_events.job_id),
...     )
>>> run(careless_finished_runs("2026-09-18", "2026-09-24"), send=example_database.send)
   job_id  finished  minutes
0       1        14       82
1       2         9       79
2       3         4       45

The Toolbox lets it through: nothing in it has a known wrong shape. Do these numbers look right?
Hard to say by eye.

### A second answer, in pandas

Fetch the rows themselves, every column of every event on those days, and work out the answer
in pandas, which counts in a way of its own: keep the finish events, then count them and add up
their minutes, per job. This is an oracle, an answer you trust because you can read each step
of it:

>>> def events(first_day, last_day):
...     every_event = statement(
...         SELECT(all_columns(job_events)),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day)),
...     )
...     return run(every_event, send=example_database.send)
>>> def oracle(rows):
...     finishes = rows[rows["event_type"] == "finish"]
...     return finishes.groupby("job_id", as_index=False).agg(
...         finished=("event_id", "count"), minutes=("minutes", "sum"))
>>> oracle(events("2026-09-18", "2026-09-24"))
   job_id  finished  minutes
0       1         7       82
1       2         4       79
2       3         1       33

Fetching every row is fine for a test over a few days; it is what the Statement saves you from
on the whole table.

### Compare the two with assert

`assert` stops with an AssertionError when what follows it is False, and does nothing when it
is True. `same_rows` puts each DataFrame's rows in one order, by `"job_id"`, and turns them
into a list of plain dicts, which compare with `==` as Python lists do:

>>> def same_rows(result, expected):
...     return (result.sort_values("job_id").to_dict("records")
...             == expected.sort_values("job_id").to_dict("records"))
>>> def check(make_statement, first_day, last_day):
...     result = run(make_statement(first_day, last_day), send=example_database.send)
...     expected = oracle(events(first_day, last_day))
...     message = f"{first_day} to {last_day}:\\n{result}\\n{expected}"
...     assert same_rows(result, expected), message
>>> check(careless_finished_runs, "2026-09-18", "2026-09-24")
Traceback (most recent call last):
...
AssertionError: 2026-09-18 to 2026-09-24:
...

The careless Statement fails: it counts each run's start event too, and adds up the minutes of
retries and fails. Its "minutes" happen to match for jobs 1 and 2, only because a start
event's minutes are 0, which is why one range of days, and a check by eye, aren't enough.

### Fix the Statement, and test it on several ranges of days

Keep only the finish events, in `WHERE`:

>>> def finished_runs(first_day, last_day):
...     return statement(
...         SELECT(job_events.job_id,
...                AS(count_rows(), "finished"),
...                AS(sum_of(job_events.minutes), "minutes")),
...         FROM(job_events),
...         WHERE(between(job_events.dt, first_day, last_day),
...               equals(job_events.event_type, "finish")),
...         GROUP_BY(job_events.job_id),
...     )

Test it on ranges of days chosen to hold the awkward cases: the whole 14 days; 2026-09-14, with
a retry; 2026-09-18, when report_build failed; and 2026-09-24, when invoice_sync started but
hadn't finished. `check` prints nothing when every `assert` holds:

>>> for first_day, last_day in [("2026-09-11", "2026-09-24"), ("2026-09-14", "2026-09-14"),
...                             ("2026-09-18", "2026-09-18"), ("2026-09-24", "2026-09-24")]:
...     check(finished_runs, first_day, last_day)

### Check what you know

Some facts you know without any oracle. Write them as `assert`s too: each job appears once,
and on 2026-09-24 invoice_sync, job 2, started but didn't finish, so it isn't there.

>>> last_day = run(finished_runs("2026-09-24", "2026-09-24"), send=example_database.send)
>>> assert last_day["job_id"].is_unique
>>> assert 2 not in set(last_day["job_id"])
>>> last_day
   job_id  finished  minutes
0       1         1       10

Keep these cells at the end of your notebook, and run them after every change: a test that
passed once proves only that the Statement was right then.

## Check it worked

The careless Statement fails its test, and the fixed one passes on every range of days. Run
the fixed one's test once more, for the whole 14 days: it prints nothing, so every `assert`
held.

>>> check(finished_runs, "2026-09-11", "2026-09-24")

## Common mistakes

### Comparing two DataFrames with ==

`==` between two DataFrames compares them cell by cell and gives back a third DataFrame, of
True and False. `assert` can't say whether a whole DataFrame is true, so it stops:

>>> result = run(finished_runs("2026-09-18", "2026-09-24"), send=example_database.send)
>>> expected = oracle(events("2026-09-18", "2026-09-24"))
>>> assert result == expected
Traceback (most recent call last):
...
ValueError: The truth value of a DataFrame is ambiguous...

Compare lists of rows, as `same_rows` does, or use pandas' own `pd.testing.assert_frame_equal`.

### Comparing rows in the order they came back

The Example database gives rows in a fixed order, but your warehouse gives them in no fixed
order. Compare without sorting, and a right answer fails whenever the order differs, as it does
here, with the shortest first:

>>> shortest_first = expected.sort_values("minutes")
>>> result.to_dict("records") == shortest_first.to_dict("records")
False
>>> same_rows(result, shortest_first)
True

Put both in one order before comparing, as `same_rows` does with `"job_id"`.

### An oracle that asks the Statement

An oracle built from the Statement's own result, such as `run(finished_runs(...))` again,
always agrees with it, careless or not. Work the oracle out from the rows themselves, as
`oracle` does from `events`, and in another way than the Statement does.

## Next

- [Check data quality with Statements](#check_data_quality): checks on the data itself, so a
  Statement you've tested gets rows you can trust.
- [Review a change with Lineage](#review_a_change_with_lineage): see what a change does to
  every Statement it reaches, then run these tests again.
- [Finish in pandas](#finish_in_pandas): more of what pandas does with the rows `run` gives
  back.
"""
