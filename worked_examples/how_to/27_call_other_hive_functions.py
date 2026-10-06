"""Call other Hive functions, and see where the Editions differ

For: Intermediate

## Goal

Call a Hive function the Toolbox has no function of its own for, such as upper or concat, with
`hive_function`. Then see the three places where the two Editions write different Hive for the
same Statement, and why each gives the same result.

## When you'd use it

When the Hive you need has a function the Toolbox doesn't wrap: text functions such as upper,
concat or substr, or date functions such as datediff and date_format. And when you read the
Hive one Edition wrote beside Hive the other wrote, say from a colleague, and some lines differ.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> job_owners = example_database.job_owners
>>> job_events = example_database.job_events
>>> job_runs = example_database.job_runs

### Call a function the Toolbox doesn't wrap

`hive_function` takes the function's name as text, then its arguments: columns, or values,
which it quotes for you. Here upper writes each team in capitals, and concat joins each
job's owner and team into one contact, such as ana@data:

>>> contacts = statement(
...     SELECT(job_owners.job_id,
...            AS(hive_function("upper", job_owners.team), "team"),
...            AS(hive_function("concat", fill_null(job_owners.owner, "nobody"), "@",
...                             job_owners.team), "contact")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-24", "2026-09-24")),
... )
>>> text = show_hive(contacts)
SELECT
  job_owners.job_id,
  UPPER(job_owners.team) AS team,
  CONCAT(COALESCE(job_owners.owner, 'nobody'), '@', job_owners.team) AS contact
FROM ops.job_owners AS job_owners
WHERE
  job_owners.dt BETWEEN '2026-09-24' AND '2026-09-24';
>>> run(contacts, send=example_database.send)
   job_id      team        contact
0       1      DATA       ana@data
1       2   FINANCE    ben@finance
2       3   FINANCE  chloe@finance
3       4       WEB     nobody@web

The function concat gives NULL as soon as one of its arguments is NULL, so `fill_null` puts
"nobody" in where a job has no owner, as job 4, cache_warm, has none.

Before writing the call, `hive_function` checks it: for the functions it knows, such as upper,
substr or date_add, it refuses the wrong number of arguments, and it refuses a function that
works only over a window of rows, such as lag or rank. The Common mistakes below show both.

### Where the two Editions write different Hive

The two Editions take the same Statements and give the same results, but in three places they
write different Hive, each for a reason. The README lists them too, under "Where the two
Editions' Hive differs". Each step below builds a Statement with one of them, shows the Hive
this Edition writes, and runs it. After the three, each line that differs is listed as both
Editions write it.

### Dividing by something that could be 0

How many retries each job's finished runs needed on 2026-09-24: the retries, divided by the
finishes.

>>> retries_per_finish = statement(
...     SELECT(job_events.job_id,
...            AS(count_rows(where=equals(job_events.event_type, "retry"))
...               / count_rows(where=equals(job_events.event_type, "finish")),
...               "retries_per_finish")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-24", "2026-09-24")),
...     GROUP_BY(job_events.job_id),
... )
>>> text = show_hive(retries_per_finish)
SELECT
  job_events.job_id,
  COUNT(CASE WHEN job_events.event_type = 'retry' THEN 1 END) / ... AS retries_per_finish
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-24' AND '2026-09-24'
GROUP BY
  job_events.job_id;
>>> run(retries_per_finish, send=example_database.send)
   job_id  retries_per_finish
0       1                 0.0
1       2                 NaN

invoice_sync, job 2, is still running on 2026-09-24, so it has no finish, and its row divides
by 0. Both Editions give that row NULL, which pandas shows as NaN, rather than stop.

### A Python float

The jobs whose finished runs took more than 15.5 minutes on average. `job_events.minutes` holds
the minutes since the run started, so on a `"finish"` row it is how long the run took. 15.5 is a
Python float:

>>> long_runs = statement(
...     SELECT(job_events.job_id, AS(count_rows(), "finished_runs")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-11", "2026-09-24"),
...           equals(job_events.event_type, "finish")),
...     GROUP_BY(job_events.job_id),
...     HAVING(more_than(average_of(job_events.minutes), 15.5)),
... )
>>> text = show_hive(long_runs)
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
  AVG(job_events.minutes) > 15.5...;
>>> run(long_runs, send=example_database.send)
   job_id  finished_runs
0       2              9
1       3              3

### A hive_function call

The function nvl gives its first argument, or its second where the first is NULL, as
`fill_null` does. Here it puts "none" in for run 98, which is still running and has no status
yet:

>>> statuses = statement(
...     SELECT(job_runs.run_id, AS(hive_function("nvl", job_runs.status, "none"), "status")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-23")),
... )
>>> text = show_hive(statuses)
SELECT
  job_runs.run_id,
  ...(job_runs.status, 'none') AS status
FROM ops.job_runs AS job_runs
WHERE
  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-23';
>>> run(statuses, send=example_database.send)
   run_id   status
0      95  SUCCESS
1      96  SUCCESS
2      97   FAILED
3      98     none
4      99     TEST

### The three, listed

[sqlglot_composer only]
This page is sqlglot Composer's, so the Hive above is sqlglot Composer's. Here is each line
that differs, as each Edition writes it, and why. Both give the same results.

- Dividing. sqlglot Composer writes the divisor as it is,
  `COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END)`, and Spark Composer writes
  `NULLIF(COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END), 0)`. With ANSI mode on
  (Spark's setting for following the SQL standard strictly), Spark 4's default, Spark stops the
  whole query when it divides by 0, where Hive gives NULL; NULLIF(y, 0) is NULL when y is 0, so
  that row gets NULL, as in Hive.
- A float. sqlglot Composer writes `HAVING AVG(job_events.minutes) > 15.5`, and Spark Composer
  `HAVING AVG(job_events.minutes) > 15.5D`. Spark reads 15.5 as a DECIMAL, an exact decimal,
  where Hive reads a DOUBLE, SQL's float; the D marks a DOUBLE, and doesn't mean days.
- A hive_function call. sqlglot Composer writes `COALESCE(job_runs.status, 'none') AS status`,
  and Spark Composer `NVL(job_runs.status, 'none') AS status`. sqlglot Composer writes the call
  as sqlglot reads it back: sometimes by another name that does the same, as COALESCE for nvl,
  and sometimes with an argument changed, as a date_format pattern 'YYYY-MM' written
  'yyyy-MM'. Spark Composer writes it as you gave it, its name in capitals.

None of the three changes a result: each Edition writes what its own warehouse needs to give
the same answer.
[end]
[spark_composer only]
This page is Spark Composer's, so the Hive above is Spark Composer's, with a note under each
line it adds to. Here is each line that differs, as each Edition writes it, and why. Both give
the same results.

- Dividing. Spark Composer writes the divisor as
  `NULLIF(COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END), 0)`, and sqlglot
  Composer as it is, `COUNT(CASE WHEN job_events.event_type = 'finish' THEN 1 END)`. With ANSI
  mode on (Spark's setting for following the SQL standard strictly), Spark 4's default, Spark
  stops the whole query when it divides by 0, where Hive gives NULL; NULLIF(y, 0) is NULL when
  y is 0, so that row gets NULL, as in Hive.
- A float. Spark Composer writes `HAVING AVG(job_events.minutes) > 15.5D`, and sqlglot
  Composer `HAVING AVG(job_events.minutes) > 15.5`. Spark reads 15.5 as a DECIMAL, an exact
  decimal, where Hive reads a DOUBLE, SQL's float; the D marks a DOUBLE, and doesn't mean days.
- A hive_function call. Spark Composer writes `NVL(job_runs.status, 'none') AS status`, the
  call as you gave it, its name in capitals. sqlglot Composer writes
  `COALESCE(job_runs.status, 'none') AS status`: it writes the call as sqlglot reads it back,
  sometimes by another name that does the same, as COALESCE for nvl, and sometimes with an
  argument changed, as a date_format pattern 'YYYY-MM' written 'yyyy-MM'.

None of the three changes a result: each Edition writes what its own warehouse needs to give
the same answer.
[end]

## Check it worked

The function's name, in capitals, and each argument are in the Hive, and the result holds what
the function gives: every team in capitals, and a contact for every job.

>>> result = run(contacts, send=example_database.send)
>>> list(result["team"])
['DATA', 'FINANCE', 'FINANCE', 'WEB']
>>> result["contact"].isna().sum()
0

## Common mistakes

### A column's name as text

`hive_function` quotes text for you, so `"team"` is the word team, not the column. Every row
gets the same value, and nothing stops it:

>>> shouting = statement(
...     SELECT(job_owners.job_id, AS(hive_function("upper", "team"), "team")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-24", "2026-09-24")),
... )
>>> run(shouting, send=example_database.send)
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

>>> no_fill = statement(
...     SELECT(job_owners.job_id,
...            AS(hive_function("concat", job_owners.owner, "@", job_owners.team),
...               "contact")),
...     FROM(job_owners),
...     WHERE(between(job_owners.dt, "2026-09-24", "2026-09-24")),
... )
>>> run(no_fill, send=example_database.send)
   job_id        contact
0       1       ana@data
1       2    ben@finance
2       3  chloe@finance
3       4           None

### YYYY for the year in date_format

In a date_format pattern, write yyyy for the year. YYYY is the year a week belongs to, which
Spark refuses in a pattern.

>>> by_month = statement(
...     SELECT(job_events.event_id,
...            AS(hive_function("date_format", job_events.dt, "YYYY-MM"), "month")),
...     FROM(job_events),
...     WHERE(between(job_events.dt, "2026-09-24", "2026-09-24")),
... )

[sqlglot_composer only]
With sqlglot Composer no message stops you: it writes the pattern as sqlglot reads it back,
here as yyyy-MM, which is what you meant. Write yyyy anyway, so the same notebook gives the
same Hive with Spark Composer, which writes the pattern as you gave it, and Spark refuses YYYY.

>>> text = show_hive(by_month)
SELECT
  job_events.event_id,
  DATE_FORMAT(job_events.dt, 'yyyy-MM') AS month
FROM ops.job_events AS job_events
WHERE
  job_events.dt BETWEEN '2026-09-24' AND '2026-09-24';
[end]
[spark_composer only]
Spark Composer writes the pattern as you gave it, and Spark refuses it when the Statement runs:

>>> run(by_month, send=example_database.send)
Traceback (most recent call last):
...
RuntimeError:
  What happened:  Spark couldn't run this Hive on the Example database: [INCONSISTENT_BEHAVIOR_CROSS_VERSION.DATETIME_PATTERN_RECOGNITION] ...
...

Write `"yyyy-MM"`, and it gives each day's month, such as 2026-09.
[end]

### A function that works over a window of rows

lag, lead, rank and the other window functions need OVER (...) after them, which
`hive_function` can't write, so it refuses them, and its message gives the pandas line that
does the same. [Finish in pandas](#finish_in_pandas) shows them.

## Next

- [Finish in pandas](#finish_in_pandas): lag, rank and a rolling sum, worked out on the rows
  `run` gives back.
- The gallery's [`hive_function`](examples.html#hive_function) entry, and
  [`fill_null`](examples.html#fill_null) for putting a value in where a column is NULL.
- [Test your own Statements](#test_your_own_statements): check that a Statement gives the
  numbers you meant, whichever Edition writes it.
"""
