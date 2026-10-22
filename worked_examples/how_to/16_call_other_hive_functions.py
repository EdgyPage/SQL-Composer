"""Call other Hive functions

For: Intermediate

## Goal

Call a Hive function the Toolbox has no function of its own for, such as upper or concat, with
`hive_function`. Then see three things worth knowing about the Hive the Toolbox writes: what a
division by 0 gives, how a Python float is written, and a function written by another name.

## When you'd use it

When the Hive you need has a function the Toolbox doesn't wrap: text functions such as upper,
concat or substr, or date functions such as datediff and date_format. And when the Hive you
see isn't quite what you typed.

It needs the Getting started how-tos [Build and run a first
statement](#build_and_run_a_first_statement) and [Count, join and stay
safe](#count_join_and_stay_safe).

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, and runs its
steps there:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

Then import the Toolbox, the Project's `ops` Database and your query:

>>> from sqlglot_composer import *
>>> from references import ops
>>> from warehouse import query, execute
>>> job_owners = ops.job_owners  # -> Table
>>> job_events = ops.job_events  # -> Table

### Call a function the Toolbox doesn't wrap

`hive_function` takes the function's name as text, then its arguments: columns, or values,
which it quotes for you. It gives back a Column, a calculation to name with `AS`. Here upper
writes each team in capitals, and concat joins each job's owner and team into one contact,
such as ana@data:

>>> contacts = statement(  # -> Statement
...     SELECT(job_owners.job_id,
...            AS(hive_function("upper", job_owners.team), "team"),
...            AS(hive_function("concat", fill_null(job_owners.owner, "nobody"), "@",
...                             job_owners.team), "contact")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> text = show_hive(contacts)  # -> str
SELECT
  job_owners.job_id,
  UPPER(job_owners.team) AS team,
  CONCAT(COALESCE(job_owners.owner, 'nobody'), '@', job_owners.team) AS contact
FROM ops.job_owners AS job_owners
WHERE
  job_owners.dt = '2026-09-24';
>>> run(contacts, query=query)  # -> DataFrame
   job_id     team        contact
0       1     DATA       ana@data
1       2  FINANCE    ben@finance
2       3  FINANCE  chloe@finance
3       4      WEB     nobody@web

The function concat gives NULL as soon as one of its arguments is NULL, so `fill_null` puts
"nobody" in where a job has no owner, as job 4, cache_warm, has none.

Before writing the call, `hive_function` checks it: for the functions it knows, such as upper,
substr or date_add, it refuses the wrong number of arguments, and it refuses a function that
works only over a window of rows, such as lag or rank. The Common mistakes below show both.

### Three things to know about the Hive

Each step below builds a Statement, shows the Hive the Toolbox writes for it, and runs it.

### Dividing by something that could be 0

How many retries each job's finished runs needed on 2026-09-24: the retries, divided by the
finishes.

>>> retries_per_finish = statement(  # -> Statement
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "retry"))
...               / count_rows(where=equals(job_events.event_type, "finish")),
...               "retries_per_finish")),
...     FROM(job_events),
...     WHERE(equals(job_events.dt, "2026-09-24")),
...     GROUP_BY(job_events.job_id),
... )
>>> text = show_hive(retries_per_finish)  # -> str
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'retry' THEN 1 END) / COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END) AS retries_per_finish
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-24'
GROUP BY
  job_events.job_id;
>>> run(retries_per_finish, query=query)  # -> DataFrame
   job_id  retries_per_finish
0       1                 0.0
1       2                 NaN

invoice_sync, job 2, is still running on 2026-09-24, so it has no finish, and its row divides
by 0. Hive gives that row NULL, which pandas shows as NaN, rather than stop.

### A Python float

The jobs whose finished runs took more than 15.5 minutes on average. `job_events.minutes`
holds the minutes since the run started, so on a `"finish"` row it is how long the run took.
15.5 is a Python float:

>>> long_runs = statement(  # -> Statement
...     SELECT(job_events.job_id, AS(count_rows(), "finished_runs")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"),
...           equals(job_events.event_type, "finish")),
...     GROUP_BY(job_events.job_id),
...     HAVING(more_than(average_of(job_events.minutes), 15.5)),
... )
>>> text = show_hive(long_runs)  # -> str
SELECT
  job_events.job_id,
  COUNT(*) AS finished_runs
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-11' AND '2026-09-24'
  AND job_events.event_type = 'finish'
GROUP BY
  job_events.job_id
HAVING
  AVG(job_events.minutes) > 15.5;
>>> run(long_runs, query=query)  # -> DataFrame
   job_id  finished_runs
0       2              9
1       3              3

A Python float is written as it is, 15.5, which Hive reads as a DOUBLE, SQL's float.

### A hive_function call written by another name

The function nvl gives its first argument, or its second where the first is NULL, as
`fill_null` does. Here it puts "none" in for cache_warm, job 4, which has no owner:

>>> owners = statement(  # -> Statement
...     SELECT(job_owners.job_id, AS(hive_function("nvl", job_owners.owner, "none"), "owner")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> text = show_hive(owners)  # -> str
SELECT
  job_owners.job_id,
  COALESCE(job_owners.owner, 'none') AS owner
FROM ops.job_owners AS job_owners
WHERE
  job_owners.dt = '2026-09-24';
>>> run(owners, query=query)  # -> DataFrame
   job_id  owner
0       1    ana
1       2    ben
2       3  chloe
3       4   none

The Hive says COALESCE, not nvl: the Toolbox writes a `hive_function` call as sqlglot reads it
back, sometimes by another name that does the same, as COALESCE for nvl, and sometimes with an
argument changed, as the Common mistakes below show for date_format. The result is the same.

## Check it worked

The function's name, in capitals, and each argument are in the Hive, and the result holds what
the function gives: every team in capitals, and a contact for every job.

>>> result = run(contacts, query=query)  # -> DataFrame
>>> list(result["team"])
['DATA', 'FINANCE', 'FINANCE', 'WEB']
>>> int(result["contact"].isna().sum())
0

`int(...)` makes the count a plain number, which numpy would otherwise print as np.int64(0).

## Common mistakes

### A column's name as text

`hive_function` quotes text for you, so `"team"` is the word team, not the column. Every row
gets the same value, and nothing stops it:

>>> shouting = statement(  # -> Statement
...     SELECT(job_owners.job_id, AS(hive_function("upper", "team"), "team")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> run(shouting, query=query)  # -> DataFrame
   job_id  team
0       1  TEAM
1       2  TEAM
2       3  TEAM
3       4  TEAM

Pass the column itself, `job_owners.team`, as the steps do.

### The whole call written as text

Only the function's name is text; its arguments go after it, one by one:

>>> hive_function("upper(job_owners.team)")
Traceback (most recent call last):
...
ValueError:
  What happened:  hive_function('upper(job_owners.team)', ...) isn't a function name.
...

### The wrong number of arguments

The function substr needs the text and where to start, and takes how many characters as a
third, if you want it. Given one, the warehouse would stop, so the Toolbox refuses it first:

>>> hive_function("substr", job_owners.owner)
Traceback (most recent call last):
...
TypeError:
  What happened:  hive_function('substr', ...) gives substr 1 argument, and substr takes 2 to 3 arguments.
...

### A NULL in concat

Without `fill_null`, a job with no owner gets no contact at all, not "@web":

>>> no_fill = statement(  # -> Statement
...     SELECT(job_owners.job_id,
...            AS(hive_function("concat", job_owners.owner, "@", job_owners.team),
...               "contact")),
...     FROM(job_owners),
...     WHERE(equals(job_owners.dt, "2026-09-24")),
... )
>>> run(no_fill, query=query)  # -> DataFrame
   job_id        contact
0       1       ana@data
1       2    ben@finance
2       3  chloe@finance
3       4            NaN

### YYYY for the year in date_format

In a date_format pattern, write yyyy for the year. YYYY is the year a week belongs to, which
differs from the year in the last days of December and the first of January.

>>> by_month = statement(  # -> Statement
...     SELECT(job_events.event_id,
...            AS(hive_function("date_format", job_events.dt, "YYYY-MM"), "month")),
...     FROM(job_events),
...     WHERE(equals(job_events.dt, "2026-09-24")),
... )

No message stops you: the Toolbox writes the pattern as sqlglot reads it back, here as
yyyy-MM, which is what you meant. Write yyyy anyway, so your Python says what its Hive does.

>>> text = show_hive(by_month)  # -> str
SELECT
  job_events.event_id,
  DATE_FORMAT(job_events.dt, 'yyyy-MM') AS month
FROM ops.job_events AS job_events
WHERE
  job_events.dt = '2026-09-24';

### A function that works over a window of rows

lag, lead, rank and the other window functions need OVER (...) after them, which
`hive_function` can't write, so it refuses them. For lag, lead, rank, dense_rank, ntile and
row_number, its message names the Toolbox's own function that writes it, such as `lag`, which
takes a `window`; for the others, such as percent_rank, it says to work it out in pandas.
[Look across rows](#look_across_rows) shows the ones the Toolbox writes.

## Next

- lag, rank and a rolling sum, each over a Window: [Look across rows](#look_across_rows).
- Hive written by hand, beside your Table references, where no Toolbox function fits:
  [Hand-written Hive with your Table
  references](#hand_written_hive_with_your_table_references).
- The gallery's [`hive_function`](examples.html#hive_function) entry, and
  [`fill_null`](examples.html#fill_null) for putting a value in where a column is NULL.
"""
