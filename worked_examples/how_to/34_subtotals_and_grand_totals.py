"""Subtotals and grand totals

For: Intermediate

## Goal

Count runs for each team and job, and in the same result each team's subtotal and the grand
total over every team, with `GROUP_BY(rollup(...))`; then label the subtotal rows with
`is_total`, so they can't be mistaken for rows whose column is really empty.

## When you'd use it

For a report that shows the parts and their totals together: runs per job with each team's
total, costs per region and day with each region's total, any table a spreadsheet would end
with a "Total" row.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> jobs = example_database.jobs

### Count per team and job, with subtotals

`rollup(jobs.team, jobs.job_name)` in `GROUP_BY` groups by both, as
`GROUP_BY(jobs.team, jobs.job_name)` does, then adds a subtotal row for each team, over all
its jobs, and one for every row, the grand total:

>>> runs_per_job = statement(
...     SELECT(jobs.team, jobs.job_name, AS(count_rows(), "runs"),
...            AS(sum_of(job_runs.duration_mins), "minutes")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(rollup(jobs.team, jobs.job_name)),
... )
>>> text = show_hive(runs_per_job)
SELECT
  jobs.team,
  jobs.job_name,
  COUNT(*) AS runs,
  SUM(job_runs.duration_mins) AS minutes
FROM ops.job_runs AS job_runs
JOIN ops.jobs AS jobs
  ON jobs.job_id = job_runs.job_id
WHERE
  job_runs.dt = '2026-09-24'
GROUP BY
  jobs.team,
  jobs.job_name
  GROUPING SETS (
    (jobs.team, jobs.job_name),
    jobs.team,
    ()
  );
>>> run(runs_per_job, send=example_database.send)
      team      job_name  runs  minutes
0     None          None     4      100
1     data          None     2       50
2     data  nightly_load     2       50
3  finance          None     2       50
4  finance  invoice_sync     1       20
5  finance  report_build     1       30

[sqlglot_composer only]
Pasted into your own notebook, this `run`, and each `run` of subtotals below, stops with a
RuntimeError saying the Example database can't run this Hive: sqlglot Composer's Example
database runs Hive with sqlglot, which can't make subtotals. The results here were worked out
in pandas from the same rows, to show what the Hive gives. Your warehouse runs the Hive as it
is, and Check it worked below runs on the Example database too.
[end]

The Hive spells out each level as one set of `GROUPING SETS`: each team and job, each team,
and `()`, nothing, for one row over all of them. In a subtotal row the columns it adds up are
empty, NULL, which pandas shows as `None`: `"job_name"` in a team's subtotal, and `"team"` too
in the grand total.

### Tell a subtotal row from a real NULL

A column can be empty in a real row too. On 2026-09-23 one run was still going, with no
`job_runs.status` yet, so a rollup of `job_runs.status` has two rows with `None`:

>>> runs_per_status = statement(
...     SELECT(job_runs.status, AS(if_else(is_total(job_runs.status), 1, 0), "subtotal"),
...            AS(count_rows(), "runs")),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-23")),
...     GROUP_BY(rollup(job_runs.status)),
... )
>>> run(runs_per_status, send=example_database.send)
    status  subtotal  runs
0     None         0     1
1     None         1     5
2   FAILED         0     1
3  SUCCESS         0     2
4     TEST         0     1

`is_total(job_runs.status)` holds on a subtotal row that adds `job_runs.status` up, and
nowhere else, so the first row is the running run, and the second the grand total of all five.

### Label the subtotal rows

`if_else(is_total(...), ...)` puts a word of your own in place of the empty column:

>>> labelled = statement(
...     SELECT(AS(if_else(is_total(jobs.team), "every team", jobs.team), "team"),
...            AS(if_else(is_total(jobs.job_name), "every job", jobs.job_name), "job"),
...            AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(rollup(jobs.team, jobs.job_name)),
... )
>>> run(labelled, send=example_database.send)
         team           job  runs
0        data     every job     2
1        data  nightly_load     2
2  every team     every job     4
3     finance     every job     2
4     finance  invoice_sync     1
5     finance  report_build     1

### Keep only the subtotals

`is_total` in `HAVING` keeps or leaves out subtotal rows, since `HAVING` tests the rows
`GROUP_BY` made, subtotals included. Here only each team's total and the grand total. The
column it tests, `jobs.job_name`, must be one `SELECT` returns, since Spark looks for it there:

>>> team_totals = statement(
...     SELECT(jobs.team, jobs.job_name, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(rollup(jobs.team, jobs.job_name)),
...     HAVING(is_total(jobs.job_name)),
... )
>>> run(team_totals, send=example_database.send)
      team job_name  runs
0     None     None     4
1     data     None     2
2  finance     None     2

### Other sets of subtotals

`rollup` adds up from the last column back to the first: each team over its jobs, never each
job over its teams. For every mix, use `cube(jobs.team, jobs.region)`: each team over every
region, each region over every team, and the grand total. To pick the sets yourself, list
them with `grouping_sets([jobs.team], [jobs.region], [])`. A plain column beside a rollup is in
every set, so `GROUP_BY(job_runs.dt, rollup(jobs.team))` totals each day's teams, and never
adds days together.

## Check it worked

Each team's subtotal is its jobs' runs added up, and the grand total all of them. A plain
`GROUP_BY`, which the Example database runs in either Edition, counts the same:

>>> runs_per_team = statement(
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(jobs.team),
... )
>>> run(runs_per_team, send=example_database.send)
      team  runs
0     data     2
1  finance     2

2 and 2 are the team subtotals above, and they add up to the grand total, 4.

## Common mistakes

### Adding up a column of subtotals

Each run is counted in its job's row, its team's subtotal and the grand total, so adding up the
whole `"runs"` column in pandas counts every run three times:

>>> int(run(runs_per_job, send=example_database.send)["runs"].sum())
12

Add up only the rows that aren't subtotals, or read the grand total's own row.

### Writing subtotals into a Saved table

A Saved table holds one row for each Key, and subtotal rows repeat the rows they add up: a sum
over the table would count each run twice. A write from subtotals is refused:

>>> team_runs = Table(
...     "mart.team_runs",
...     columns={"team": "string", "runs": "bigint", "dt": "string"},
...     date_partition="dt",
...     key=["team", "dt"],
...     location="/data/your_team/tables",
... )
>>> statement(
...     INSERT_OVERWRITE(team_runs),
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24")),
...     GROUP_BY(rollup(jobs.team)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  INSERT_OVERWRITE(team_runs) writes rows made by GROUP_BY(rollup(jobs.team)).
...

Write the plain `GROUP_BY(jobs.team)`, and add the subtotals in the Statement that reads the
Saved table.

### is_total in WHERE

`WHERE` picks the rows before `GROUP_BY` makes any subtotal, so there is none to test there:

>>> statement(
...     SELECT(jobs.team, AS(count_rows(), "runs")),
...     FROM(job_runs),
...     JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24"), is_total(jobs.team)),
...     GROUP_BY(rollup(jobs.team)),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  WHERE has is_total(jobs.team).
...

Test it in `HAVING`, as Keep only the subtotals does.

## Next

- [Count and add up per group](#count_and_add_up_per_group): GROUP_BY without subtotals.
- [Week and month rollups](#week_and_month_rollups): groups of days into weeks and months.
- The gallery's [`rollup`](examples.html#rollup), [`cube`](examples.html#cube),
  [`grouping_sets`](examples.html#grouping_sets) and [`is_total`](examples.html#is_total).
"""

import pandas as pd

from sqlglot_composer import (
    FROM, JOIN, SELECT, WHERE, all_columns, equals, example_database, run, statement,
)

job_runs = example_database.job_runs
jobs = example_database.jobs


def runs_on(day):
    """Each run of the day, with its job's team and name, read with a Statement the Example
    database can run."""
    return run(statement(SELECT(all_columns(job_runs), jobs.team, jobs.job_name),
                         FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                         WHERE(equals(job_runs.dt, day))), send=example_database.send)


def _rollup(rows, columns, totals):
    """The rows of a rollup over `columns`: each level, from all of them down to none, with the
    columns a level adds up as None and a 1 in `level` where they are."""
    found = []
    for size in range(len(columns), -1, -1):
        # One more column, the same on every row, so the grand total is a group too.
        grouped = rows.assign(every=0).groupby(columns[:size] + ["every"], dropna=False,
                                               as_index=False).agg(**totals)
        for column in columns[size:]:
            grouped[column] = None
        grouped["level"] = 1 if size < len(columns) else 0
        found.append(grouped.drop(columns="every"))
    found = pd.concat(found, ignore_index=True)
    for column in columns:
        found[column] = found[column].astype(object).where(found[column].notna(), None)
    return found


def _sorted(frame, columns):
    """The rows as the Example database gives them: sorted by every column, None first."""
    keys = [frame[column].map(lambda value: (value is not None and value == value, value))
            for column in columns]
    order = sorted(range(len(frame)), key=lambda i: tuple(key.iloc[i] for key in keys))
    return frame.iloc[order][columns].reset_index(drop=True)


def runs_per_job_in_pandas():
    """runs_per_job's result, computed in pandas, not by running this Hive."""
    rows = runs_on("2026-09-24")
    found = _rollup(rows, ["team", "job_name"],
                    {"runs": ("run_id", "count"), "minutes": ("duration_mins", "sum")})
    return _sorted(found, ["team", "job_name", "runs", "minutes"])


def runs_per_status_in_pandas():
    """runs_per_status's result, computed in pandas, not by running this Hive."""
    rows = runs_on("2026-09-23")
    rows["status"] = rows["status"].astype(object).where(rows["status"].notna(), None)
    found = _rollup(rows, ["status"], {"runs": ("run_id", "count")})
    found["subtotal"] = found["level"]
    return _sorted(found, ["status", "subtotal", "runs"])


def labelled_in_pandas():
    """labelled's result, computed in pandas, not by running this Hive."""
    found = runs_per_job_in_pandas()
    team = found["team"].where(found["team"].notna(), "every team")
    job = found["job_name"].where(found["job_name"].notna(), "every job")
    labelled = pd.DataFrame({"team": team, "job": job, "runs": found["runs"]})
    return _sorted(labelled, ["team", "job", "runs"])


def team_totals_in_pandas():
    """team_totals' result, computed in pandas, not by running this Hive."""
    found = runs_per_job_in_pandas()
    return found[found["job_name"].isna()][["team", "job_name", "runs"]].reset_index(drop=True)
