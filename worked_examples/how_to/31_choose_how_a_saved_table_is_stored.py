"""Choose how a Saved table is stored

For: Intermediate

## Goal

Say in a Saved table's Table reference how the warehouse keeps it: the folder of its own its
files go in, whether dropping it deletes them, their format, Partitions inside each day, and
Buckets. `create_table` writes all of it, and `check_table_reference` compares it with the
table. Along the way, see why the Toolbox has no indexes, and what makes reads fast instead.

## When you'd use it

When you create a Saved table, and when you check one you already have: every Saved table
needs at least its folder. The rest is for when a table grows: a big table read a region at a
time, or joined on the same column every day, can be kept so that reads touch fewer files.
[Save a table](#save_a_table) comes first, if you haven't saved one yet.

## Steps

### Import the Toolbox

>>> from sqlglot_composer import *
>>> region_costs = example_database.region_costs

### Give it a folder of its own

Every Saved table is an external table: its files are yours, in a folder you name. You give
`location=` the folder all your Saved tables go in, and the Toolbox adds the table's own
folder, its database and its name. mart.job_costs, each job's cost per region and day, goes
in /data/your_team/tables/mart/job_costs:

>>> job_costs = Table(
...     "mart.job_costs",
...     columns={
...         "job_id": "bigint",
...         "region": "string",  # eu or us, where the job is billed
...         "cost_cents": "bigint",
...         "dt": "string",
...     },
...     date_partition="dt",
...     key=["job_id", "region", "dt"],
...     location="/data/your_team/tables",
...     purge=True,
...     compression="ZLIB",
...     partitioned_by=["region"],
... )

A folder of its own matters because the warehouse reads every file in a table's folder. Two
tables in one folder read each other's rows, and an INSERT OVERWRITE of a day in one can delete
the other's files for that day. The Toolbox always adds the table's own folder, so two Table
references can't share one by mistake, and it refuses one whose folder would sit inside
another's.

### Say what dropping it does

`purge=True` makes dropping the table delete its files too. Left out, or `purge=False`, the
warehouse only forgets the table: its files stay in its folder, and a table created there
again reads the old rows back. Keep `purge=True` for a table you rebuild from its sources;
leave it out for one whose files you would want back.

### Choose its file format

`stored_as=` is the file format: `"ORC"`, the usual one, which Hive reads fastest, or
`"PARQUET"`, which more tools outside Hive read. `compression=` is how its files are packed:
ORC's `"ZLIB"` makes smaller files, `"SNAPPY"` faster ones. `properties=` takes any other
table property, such as `{"made_by": "daily_pipeline"}`. `create_table` writes them all:

>>> text = show_hive(create_table(job_costs, may_exist=True))
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_costs (
  job_id BIGINT,
  cost_cents BIGINT...
)
PARTITIONED BY (
  dt STRING,
  region STRING
)
STORED AS ORC
LOCATION '/data/your_team/tables/mart/job_costs'
TBLPROPERTIES (
  'external.table.purge'='true',
  'orc.compress'='ZLIB'
);

### Split each day by region

`partitioned_by=["region"]` makes Partitions inside each day: each day's folder holds a folder
per region, so a Statement that bounds the region reads only that region's files. A write
still fills one day, named in its first line, and fills each region from its rows, so its
SELECT lists region too; the Toolbox puts it last, where the warehouse reads it from. Here
ops.region_costs, whose days are written like 20260921, fills a day of mart.job_costs:

>>> def write_job_costs(day):
...     return statement(
...         INSERT_OVERWRITE(job_costs),
...         SELECT(region_costs.job_id, region_costs.region,
...                AS(sum_of(region_costs.cost_cents), "cost_cents")),
...         FROM(region_costs),
...         WHERE(equals(region_costs.dt, day)),
...         GROUP_BY(region_costs.job_id, region_costs.region),
...     )
>>> text = show_hive(write_job_costs("20260921"))
-- The Session setting "dynamic_partitions": this write fills region from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.job_costs PARTITION(dt = '2026-09-21', region)
SELECT
  region_costs.job_id,
  SUM(region_costs.cost_cents) AS cost_cents,
  region_costs.region
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt = '20260921'
GROUP BY
  region_costs.job_id,
  region_costs.region;

The region in PARTITION(...) has no value: the warehouse takes each row's region from the
SELECT's last column. Doing so is Hive's dynamic partitioning, which a Session setting switches
on, so `show_hive` prints its two SET lines first. `run` sends the write alone: send the
Session setting first, with `hive_settings`, before the first such write. The warehouse keeps
it for as long as your send's connection lasts, and sending it again does no harm. Here it
goes to the Example database, and `run` gives back nothing for it:

>>> run(hive_settings("dynamic_partitions"), send=example_database.send)

The day is written the Saved table's way, 2026-09-21, though the table it reads writes it
20260921.

INSERT OVERWRITE replaces only the regions its rows hold: a region with no rows that day keeps
whatever it held before. So if a region drops out of the table you read, its old rows for the
day stay in the Saved table until you drop that day.

### Add Buckets only to a big table

`bucketed_by=` with `buckets=` spreads each day's rows into that many files by the values of
some columns, and `sorted_by=` sorts the rows in each. A join on those columns can then pair
file with file instead of reading everything. It pays off only on big tables, tens of millions
of rows a day, joined on those columns; and changing it means writing the whole table again.
Where Spark writes the table, rather than Hive, ask whoever looks after it first: Spark may
refuse to write a table with Buckets, or write it without them. Most Saved tables need none:

>>> run_facts = Table(
...     "mart.run_facts",
...     columns={"run_id": "bigint", "job_id": "bigint", "minutes": "int", "dt": "string"},
...     date_partition="dt",
...     key=["run_id", "dt"],
...     location="/data/your_team/tables",
...     bucketed_by=["run_id"],
...     buckets=16,
...     sorted_by=["run_id"],
... )
>>> print(to_hive(create_table(run_facts)))
CREATE EXTERNAL TABLE mart.run_facts (
  run_id BIGINT,
  job_id BIGINT,
  minutes INT...
)
PARTITIONED BY (
  dt STRING
)
CLUSTERED BY (run_id) SORTED BY (run_id) INTO 16 BUCKETS
STORED AS ORC
LOCATION '/data/your_team/tables/mart/run_facts'

### Why there are no indexes

Hive removed indexes in its version 3, and Spark never had them, so the Toolbox writes none.
What makes a read fast instead:

- Partitions: a Statement that bounds the Date partition, as every Load limit insists, opens
  only those days' folders, and one that bounds a Partition inside them, such as region,
  opens fewer still.
- Fewer, larger files: a write per day makes one set of files per day, rather than many small
  ones; ORC and Parquet files keep each column's smallest and largest values, so the warehouse
  skips the parts of a file a condition rules out.
- Buckets, for big tables joined on the same columns, as above.
- Statistics: once the warehouse has counted a table's rows and values, it picks how to join
  it, such as sending a small table to every machine instead of sorting both.

## Check it worked

The write's rows come from its SELECT, which the Example database can run on its own: on
2026-09-21, two jobs billed in eu and one in us.

>>> costs_on_the_day = statement(
...     SELECT(region_costs.job_id, region_costs.region,
...            AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260921")),
...     GROUP_BY(region_costs.job_id, region_costs.region),
... )
>>> run(costs_on_the_day, send=example_database.send)
   job_id region  cost_cents
0       1     eu         130
1       2     eu         210
2       3     us         330

At work, once `create_table` has made the table, `check_table_reference` sends DESCRIBE
FORMATTED, which lists how the table is kept, and compares that too. A stand-in send plays a
table made by hand at a folder it shares with other tables, /data/your_team/tables itself,
as the warehouse would describe it:

>>> import pandas as pd
>>> def send_at_work(hive):
...     if hive.startswith("SHOW PARTITIONS"):
...         return pd.DataFrame({"partition": ["dt=2026-09-21/region=eu"]})
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("cost_cents", "bigint", ""),
...         ("# Partition Information", None, None), ("# col_name", "data_type", "comment"),
...         ("dt", "string", ""), ("region", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...         ("Table Parameters:", None, None),
...         ("", "external.table.purge", "true"), ("", "orc.compress", "ZLIB"),
...         ("# Storage Information", None, None),
...         ("InputFormat:", "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_costs, send=send_at_work)
mart.job_costs differs from its Table reference.
Problems:
  - it is at hdfs://namenode:8020/data/your_team/tables, not at its own folder /data/your_team/tables/mart/job_costs. A folder that isn't a table's own may hold other tables' files: two tables in one folder read each other's files, and an INSERT OVERWRITE of a day in one can delete the other's files for that day. Move it with admin.move_to_own_folder(t, send=...).

Everything else matches. The warehouse writes a folder in full, with `hdfs://namenode:8020`
before it, and the Toolbox compares the folder alone. Moving a table that shares a folder
means copying its days into a table made by `create_table`, then dropping the old one.

## Common mistakes

### Giving location= the table's own folder

`location=` is the folder all your Saved tables go in, not the table's own: the Toolbox adds
that. A folder copied from a table's own DESCRIBE FORMATTED is refused:

>>> Table("mart.job_costs", columns={"job_id": "bigint", "dt": "string"},
...       date_partition="dt", location="/data/your_team/tables/mart/job_costs")
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('mart.job_costs'): location='/data/your_team/tables/mart/job_costs' already ends with the table's own folder, mart/job_costs.
...

Write the folder above it, `location="/data/your_team/tables"`.

### Leaving the Partition out of the write

A write fills each region from its rows, so its SELECT must list region. Left out, it is
refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(job_costs),
...     SELECT(region_costs.job_id, AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260921")),
...     GROUP_BY(region_costs.job_id),
... )
Traceback (most recent call last):
...
composer_core.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_costs): it leaves out region.
...

### Storage on a table you only read

Only your own Saved tables are stored as you say. A Table reference with no `location=` is a
table someone else owns, and giving it storage is refused:

>>> Table("ops.job_runs", columns={"run_id": "bigint", "dt": "string"},
...       date_partition="dt", purge=True)
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('ops.job_runs') has purge= but no location=.
...

## Next

- Create a Saved table, write its days and rebuild it: [Save a table](#save_a_table).
- Check a Table reference against its table again after the table changes:
  [Keep a Table reference true over time](#keep_a_table_reference_true_over_time).
- Read a table split by region before its days:
  [A day written another way, and a second partition](#a_day_written_another_way).
- Every option in one place: the gallery's [`create_table`](examples.html#create_table) entry,
  and `help(Table)`.
"""
