"""A day written another way, and a second partition

For: Intermediate

## Goal

Read a table whose days are written like `20260911` rather than `2026-09-11`, and which is
split by region before it is split by day. You write its Table reference, finish the line
`write_table_reference` leaves to you, and bound its days in a Statement, so the warehouse
reads only the days you ask for.

## When you'd use it

When DESCRIBE lists more than one partition column, or SHOW PARTITIONS lists days written
some other way, such as `dt=20260911` or `dt=2026/09/11`. Big tables are often split by
country, region or source first, and by day inside each.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *

### See how the table is split

DESCRIBE lists a table's columns, then, under `# Partition Information`, the columns it is
partitioned by: the warehouse keeps each region's rows in a folder of their own, and each day's
in a folder inside that. The Example database's `ops.region_costs` holds each job's cost in
cents, partitioned by region, then by day:

>>> example_database.send("DESCRIBE ops.region_costs")
                  col_name  data_type                       comment
0                   job_id     bigint
1               cost_cents     bigint  NULL until the bill comes in
2                   region     string
3                       dt     string
4                                None                          None
5  # Partition Information       None                          None
6               # col_name  data_type                       comment
7                   region     string
8                       dt     string

SHOW PARTITIONS lists each folder, one row each. The last five show both regions, and days
written as `20260924`, the year, then the month, then the day, with nothing between:

>>> partitions = example_database.send("SHOW PARTITIONS ops.region_costs")
>>> partitions.tail(5)
                partition
13  region=eu/dt=20260924
14  region=us/dt=20260911
15  region=us/dt=20260914
16  region=us/dt=20260918
17  region=us/dt=20260921

### Write its Table reference

`write_table_reference` sends the same two commands through your send and writes the Table
reference for you, as `region_costs.py` in the folder you're working in:

>>> path = write_table_reference("ops.region_costs", send=example_database.send)

Look at its line starting `date_partition=`. The Date partition is the one column of days that
every Statement must bound at both ends, and `write_table_reference` looks for it in the first
partition column only. Here that is region, which holds `"eu"` and `"us"`, not days, so it
can't be the Date partition: it writes `date_partition=None` and a TODO. The TODO names both
partition columns, says the newest region, `'us'`, isn't a day the Toolbox could bound, and
asks you to name dt, the column that holds the days, yourself.

### Finish the Table reference

Change the TODO line into two lines: `date_partition="dt",` names the Date partition, and
`date_format="%Y%m%d",` says how its days are written, in the codes Python's dates use: `%Y` is
the year, `%m` the month and `%d` the day. Fill in the other two TODOs while you are there: one
row is one job's cost in one region on one day, so the key is job_id, region and dt; and
cost_cents is a plain amount, which adds up, so `does_not_add_up=[]` stays empty.

Try the finished reference in your notebook first, as below; once the next step says it
matches, copy it into `region_costs.py` and import it from there in every notebook:

>>> region_costs = Table(
...     "ops.region_costs",
...     columns={
...         "job_id": "bigint",
...         "cost_cents": "bigint",  # NULL until the bill comes in
...         "region": "string",
...         "dt": "string",
...     },
...     date_partition="dt",
...     date_format="%Y%m%d",
...     key=["job_id", "region", "dt"],
...     does_not_add_up=[],
... )

### Check it against the table

`check_table_reference` compares the Table reference with the table as it is now:

>>> check_table_reference(region_costs, send=example_database.send)
ops.region_costs matches its Table reference.
Notes:
  - the table is also partitioned by region, which a Statement may bound too.

It matches. The note is about region: it is a partition too, so a Statement that needs only one
region can say so and read fewer folders, as the last step shows. The Toolbox doesn't ask you
to, since a region isn't a day. `check_key` checks your key on the newest day:

>>> check_key(region_costs, send=example_database.send)
ops.region_costs: the key (job_id, region, dt) holds on 20260924.

### Bound its days

Write the days the way the table writes them. Each region's cost over the week from
2026-09-18 to 2026-09-24:

>>> cost_per_region = statement(
...     SELECT(region_costs.region, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260918", "20260924")),
...     GROUP_BY(region_costs.region),
... )
>>> text = show_hive(cost_per_region)
SELECT
  region_costs.region,
  SUM(region_costs.cost_cents) AS cost_cents
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt BETWEEN '20260918' AND '20260924'
GROUP BY
  region_costs.region;
>>> run(cost_per_region, send=example_database.send)
  region  cost_cents
0     eu        1610
1     us         450

A Python date works in its place, and so does `last_n_days(region_costs.dt, 7)`: the Toolbox
writes each day as `date_format=` says. A condition shows the Hive it becomes:

>>> import datetime
>>> between(region_costs.dt, datetime.date(2026, 9, 18), datetime.date(2026, 9, 24))
region_costs.dt BETWEEN '20260918' AND '20260924'

### Bound the second partition too

To read one region, add a condition on region to `WHERE`. The warehouse then opens only that
region's folders. Each job's cost in eu over the same week:

>>> eu_cost_per_job = statement(
...     SELECT(region_costs.job_id, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(equals(region_costs.region, "eu"),
...           between(region_costs.dt, "20260918", "20260924")),
...     GROUP_BY(region_costs.job_id),
... )
>>> text = show_hive(eu_cost_per_job)
SELECT
  region_costs.job_id,
  SUM(region_costs.cost_cents) AS cost_cents
FROM ops.region_costs AS region_costs
WHERE
  region_costs.region = 'eu' AND region_costs.dt BETWEEN '20260918' AND '20260924'
GROUP BY
  region_costs.job_id;
>>> run(eu_cost_per_job, send=example_database.send)
   job_id  cost_cents
0       1         820
1       2         790

Job 2's cost for 2026-09-24 is NULL, since its run is still going and isn't billed yet. SUM,
which `sum_of` writes, leaves a NULL out, so job 2's week adds up the four days it was billed.

## Check it worked

`check_table_reference` said the Table reference matches, and the Hive writes the days as the
table does, `'20260918'`. The two Statements also agree: eu's jobs add up to eu's cost in the
first one, 1610.

>>> eu_jobs = run(eu_cost_per_job, send=example_database.send)
>>> int(eu_jobs["cost_cents"].sum())
1610

## Common mistakes

### Keeping date_partition=None

A Table reference with `date_partition=None` has no Date partition for the Toolbox to check, so
nothing stops a Statement that reads every day of every region. Here is the reference as
`write_table_reference` left it:

>>> unfinished = Table("ops.region_costs", columns={"job_id": "bigint",
...     "cost_cents": "bigint", "region": "string", "dt": "string"}, date_partition=None)
>>> check_table_reference(unfinished, send=example_database.send)
ops.region_costs matches its Table reference.
Notes:
  - the table is partitioned by region, dt: if one holds days, name it in date_partition=...

It says it matches, since no column in it is wrong: something is missing, not wrong. The note
is the part to act on. Until you do, a Statement without a day builds and runs without a word,
and adds up all 14 days:

>>> every_day = statement(
...     SELECT(unfinished.region, AS(sum_of(unfinished.cost_cents), "cost_cents")),
...     FROM(unfinished),
...     GROUP_BY(unfinished.region),
... )
>>> run(every_day, send=example_database.send)
  region  cost_cents
0     eu        3460
1     us        1160

On a real table that is every day it has ever held. Name dt, and the same Statement is refused
until it bounds its days.

### Naming dt without its date_format

Without `date_format=`, the Toolbox expects days written the usual way, like `2026-09-25`.
`check_table_reference` gives the line to add:

>>> without_format = Table("ops.region_costs", columns={"job_id": "bigint",
...     "cost_cents": "bigint", "region": "string", "dt": "string"}, date_partition="dt")
>>> check_table_reference(without_format, send=example_database.send)
ops.region_costs differs from its Table reference.
Problems:
  - the newest dt, '20260924', isn't written like date_format='%Y-%m-%d', the usual one: change the line to date_format="%Y%m%d",
Notes:
  - the table is also partitioned by region, which a Statement may bound too.

A Statement written with the table's own days is refused until you add it:

>>> statement(
...     SELECT(without_format.job_id),
...     FROM(without_format),
...     WHERE(between(without_format.dt, "20260918", "20260924")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  between(region_costs.dt, ...) compares the Date partition region_costs.dt with '20260918', which isn't a day written like '2026-09-25'.
...

### Writing the day the usual way

Once `date_format="%Y%m%d"` is in the Table reference, a day written with dashes is refused,
since it would match no folder:

>>> statement(
...     SELECT(region_costs.job_id),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "2026-09-18", "2026-09-24")),
... )
Traceback (most recent call last):
...
ValueError:
  What happened:  between(region_costs.dt, ...) compares the Date partition region_costs.dt with '2026-09-18', which isn't a day written like '20260925'.
...

The day in the message is today, written the table's way: it shows how to write a day, not
which day to read. Write `"20260918"`, or pass `datetime.date(2026, 9, 18)`.

## Next

- Look things up as of each day in a table that keeps a copy of itself every day:
  [Look things up as of a day](#look_things_up_as_of_a_day).
- Rewrite the last few days of a Saved table on every run:
  [Incremental loads and late data](#incremental_loads_and_late_data).
- The gallery's Worked examples of
  [`write_table_reference`](examples.html#write_table_reference),
  [`check_table_reference`](examples.html#check_table_reference) and
  [`Table`](examples.html#Table).
"""
