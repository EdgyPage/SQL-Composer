"""A day written another way, and a second partition

For: Intermediate

## Goal

Read a table whose days are written like `20260911` rather than `2026-09-11`, and which is
partitioned by region before it is partitioned by day. You write its Table reference, finish the
lines `write_table_reference` leaves to you, and filter its partitions in a Statement, writing
each day as the table writes it, so the warehouse reads only the days you ask for.

## When you'd use it

When DESCRIBE lists more than one partition column, or SHOW PARTITIONS lists days written
some other way, such as `dt=20260911` or `dt=2026/09/11`. Big tables are often split by
country, region or source first, and by day inside each. If DESCRIBE and SHOW PARTITIONS are
new to you, [Add your tables' references](#add_your_tables_references) and [Describe a table by
hand](#describe_a_table_by_hand) start with them.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *

### See how the table is split

DESCRIBE lists a table's columns, then, under `# Partition Information`, the columns it is
partitioned by: the warehouse keeps each region's rows in a folder of their own, and each day's
in a folder inside that. The Example database's `ops.region_costs` holds each job's cost in
cents, partitioned by region, then by day:

>>> example_database.query("DESCRIBE ops.region_costs")
                  col_name  data_type                       comment
0                   job_id     bigint
1               cost_cents     bigint  NULL until the bill comes in
2                   region     string
3                       dt     string
4                                 NaN                           NaN
5  # Partition Information        NaN                           NaN
6               # col_name  data_type                       comment
7                   region     string
8                       dt     string

SHOW PARTITIONS lists each folder, one row each. The last five show both regions, and days
written as `20260924`, the year, then the month, then the day, with nothing between:

>>> partitions = example_database.query("SHOW PARTITIONS ops.region_costs")
>>> partitions.tail(5)
                partition
13  region=eu/dt=20260924
14  region=us/dt=20260911
15  region=us/dt=20260914
16  region=us/dt=20260918
17  region=us/dt=20260921

### Write its Table reference

`write_table_reference` sends DESCRIBE through your query and writes the Table reference for
you, as ops__region_costs.py in the folder you're working in:

>>> path = write_table_reference("ops.region_costs", query=example_database.query)

Look at its line starting `partitioned_by=`. It lists both partition columns, in the order
DESCRIBE gives them, `partitioned_by=["region", "dt"]`, and nothing in it is a guess: to the
Toolbox, dt is a column of text like any other, compared exactly as you write it. The two lines
it can't know are left as TODOs: the Key, and the columns that don't add up.

### Finish the Table reference

Fill in the two TODOs: one row is one job's cost in one region on one day, so the key is job_id,
region and dt; and cost_cents is a plain amount, which adds up, so `does_not_add_up=[]` stays
empty.

Try the finished reference in your notebook first, as below; once the next step says it
matches, copy it into ops__region_costs.py and import it from there in every notebook:

>>> region_costs = Table(
...     "ops.region_costs",
...     columns={
...         "job_id": "bigint",
...         "cost_cents": "bigint",  # NULL until the bill comes in
...         "region": "string",
...         "dt": "string",
...     },
...     partitioned_by=["region", "dt"],
...     key=["job_id", "region", "dt"],
...     does_not_add_up=[],
... )

### Check it against the table

`check_table_reference` compares the Table reference with the table as it is now:

>>> check_table_reference(region_costs, query=example_database.query)
ops.region_costs matches its Table reference.

It matches. `check_key` checks your key on the rows `where=` picks, here the newest day,
written the table's way:

>>> check_key(region_costs, query=example_database.query,
...           where=equals(region_costs.dt, "20260924"))
ops.region_costs: the key (job_id, region, dt) holds where region_costs.dt = '20260924'.

### Filter its days

Every read of a partitioned table must filter at least one of its partition columns, and here
the days are the one to filter. Write them the way the table writes them. Each region's cost
over the week from 2026-09-18 to 2026-09-24:

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
>>> run(cost_per_region, query=example_database.query)
  region  cost_cents
0     eu        1610
1     us         450

Hive compares the days as text, and days written this way sort as the days do, so `between`
picks the week.

### Filter the second partition too

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
>>> run(eu_cost_per_job, query=example_database.query)
   job_id  cost_cents
0       1         820
1       2         790

Job 2's cost for 2026-09-24 is NULL, since its run is still going and isn't billed yet. SUM,
which `sum_of` writes, leaves a NULL out, so job 2's week adds up the four days it was billed.

## Check it worked

`check_table_reference` said the Table reference matches, and the Hive writes the days as the
table does, `'20260918'`. The two Statements also agree: eu's jobs add up to eu's cost in the
first one, 1610.

>>> eu_jobs = run(eu_cost_per_job, query=example_database.query)
>>> int(eu_jobs["cost_cents"].sum())
1610

## Common mistakes

### Leaving partitioned_by= out

A Table reference with no `partitioned_by=` says the table isn't partitioned, so nothing
stops a Statement that reads every day of every region. `check_table_reference` says so, and
gives the line to add:

>>> unfinished = Table("ops.region_costs", columns={"job_id": "bigint",
...     "cost_cents": "bigint", "region": "string", "dt": "string"})
>>> check_table_reference(unfinished, query=example_database.query)
ops.region_costs differs from its Table reference.
Problems:
  - the table is partitioned by region, dt: change the line to partitioned_by=["region", "dt"],

Until you add it, a Statement that filters nothing builds and runs without a word, and adds
up all 14 days:

>>> every_day = statement(
...     SELECT(unfinished.region, AS(sum_of(unfinished.cost_cents), "cost_cents")),
...     FROM(unfinished),
...     GROUP_BY(unfinished.region),
... )
>>> run(every_day, query=example_database.query)
  region  cost_cents
0     eu        3460
1     us        1160

On a real table that is every day it has ever held. With `partitioned_by=` in the Table
reference, the same Statement is refused until it filters a partition column:

>>> statement(
...     SELECT(region_costs.region, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     GROUP_BY(region_costs.region),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.LoadRefused:
  What happened:  FROM(region_costs) reads ops.region_costs, but filters none of its partition columns: region, dt.
...

### Writing the day the usual way

No message stops you here. The Toolbox compares a day exactly as you write it, so a day
written with dashes matches no row of this table, and the Statement gives nothing:

>>> with_dashes = statement(
...     SELECT(region_costs.job_id, region_costs.cost_cents),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "2026-09-18", "2026-09-24")),
... )
>>> run(with_dashes, query=example_database.query)
Empty DataFrame
Columns: [job_id, cost_cents]
Index: []

A Python date, and `last_n_days`, are written with dashes too, so on this table write the days
as text, like `"20260918"`:

>>> import datetime
>>> between(region_costs.dt, datetime.date(2026, 9, 18), datetime.date(2026, 9, 24))
region_costs.dt BETWEEN '2026-09-18' AND '2026-09-24'

### Joining it on the day to a table that writes days the usual way

`ops.job_events` writes its days like `2026-09-18`. Hive compares the days as text, so
`equals(region_costs.dt, job_events.dt)` in `ON=` matches no row: `'20260918'` never equals
`'2026-09-18'`. Write one side the other's way with a Hive function, as [Call other Hive
functions](#call_other_hive_functions) shows: Hive's regexp_replace takes the dashes out.

>>> job_events = example_database.job_events
>>> equals(region_costs.dt, hive_function("regexp_replace", job_events.dt, "-", ""))
region_costs.dt = REGEXP_REPLACE(job_events.dt, '-', '')

## Next

- Look things up as of each day in a table that keeps a copy of itself every day:
  [Look things up as of a day](#look_things_up_as_of_a_day).
- Keep a Table reference true as its table changes: [Keep a Table reference true over
  time](#keep_a_table_reference_true_over_time).
- Rewrite the last few days of a Saved table on every run:
  [Incremental loads and late data](#incremental_loads_and_late_data).
- The gallery's Worked examples of
  [`write_table_reference`](examples.html#write_table_reference),
  [`check_table_reference`](examples.html#check_table_reference) and
  [`Table`](examples.html#Table).
"""
