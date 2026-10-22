"""Choose how a Saved table is stored

For: Intermediate

## Goal

Say in a Saved table's Table reference how the warehouse keeps it: the folder of its own its
files go in, whether dropping it deletes them, their format, its Partitions, and Buckets.
`create_table` writes all of it, and `check_table_reference` compares it with the table. Along
the way, see why the Toolbox has no indexes, and what makes reads fast instead.

## When you'd use it

When you fill in a Saved table's Table reference, and when you check one you already have:
every Saved table needs at least its folder. The rest is for when a table grows: a big table
read a region at a time, or joined on the same column every run, can be kept so that reads
touch fewer files.

It needs [Save a table](#save_a_table), which makes a Saved table with `project.new_table`.

## Steps

### Start from the Intermediate Example project

Work in a copy of the Intermediate Example project, at its top: copy
`example_projects/intermediate/` from the download to a folder of your own, copy the
`sqlglot_composer` folder into it, as a Project holds it, and open a notebook there. This page
makes the same copy in its first step, from the download the Toolbox came in, into the folder
it runs in, which Python's path holds already, as Jupyter's does for a notebook's own folder:

>>> import shutil
>>> from pathlib import Path
>>> import sqlglot_composer
>>> download = Path(sqlglot_composer.__file__).parents[1]  # -> Path
>>> _ = shutil.copytree(download / "example_projects" / "intermediate", ".", dirs_exist_ok=True)

mart.job_region_costs will hold each job's cost in each region on each day, copied from
ops.region_costs, which the Project reads already. Make its Table folder and Table reference,
as [Save a table](#save_a_table) shows:

>>> from sqlglot_composer import *
>>> from sqlglot_composer import project
>>> from warehouse import query, execute
>>> project.new_table("mart.job_region_costs")
Made tables/mart__job_region_costs/: mart__job_region_costs.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__job_region_costs.py: fill in its <...> and TODO lines.

Its Table reference, filled in, says how the table is stored. Each line is explained below:

The file `references/mart__job_region_costs.py`, after you fill it in:

    \"\"\"mart.job_region_costs - one row per job, region and day: its cost there, in cents.\"\"\"
    from sqlglot_composer import Table

    job_region_costs = Table(
        "mart.job_region_costs",
        columns={
            "job_id": "bigint",
            "cost_cents": "bigint",
            "region": "string",
            "dt": "string",
        },
        partitioned_by=["region", "dt"],
        key=["job_id", "region", "dt"],
        location="/data/your_team/mart.db/job_region_costs",  # its own folder
        purge=True,  # dropping the table deletes its files
        compression="ZLIB",
        properties={"made_by": "mart__job_region_costs.ipynb"},
    )

>>> project.refresh_reference_sheet()
Wrote references/reference_sheet.csv: 49 rows, 12 tables.
Wrote references/mart.py: from references import mart gives mart.budget_overruns, mart.job_day_costs, mart.job_day_facts, mart.job_events_checks, mart.job_notes, mart.job_region_costs and mart.team_days.
Restart the kernel of a notebook that imported references, to see a table added since.
>>> from references import mart, ops
>>> job_region_costs, region_costs = mart.job_region_costs, ops.region_costs  # -> Table, Table

### Give it a folder of its own

Every Saved table is an external table: its files are yours, in a folder you name. You give
`location=` the table's own folder, and the Toolbox writes it exactly as you give it, adding
nothing. A folder named after the database and the table, such as
/data/your_team/mart.db/job_region_costs, keeps each table's folder apart.

A folder of its own matters because the warehouse reads every file in a table's folder. Two
tables in one folder read each other's rows, and an INSERT OVERWRITE of a Partition in one can
delete the other's files for that Partition. The Toolbox refuses a Table reference whose folder
is another Saved table's, or sits inside it.

A path you would rather not write out in every Table reference can start with a Hive
variable, such as `location="${hivevar:root}/mart.db/job_region_costs"`: the Toolbox writes
it as it is, and Hive fills it in from a `SET hivevar:root=/data/your_team` sent first, with
`hive_settings(..., sets=...)` as [Keep reads and joins fast](#keep_reads_and_joins_fast)
sends its settings.

### Say what dropping it does

`purge=True` makes dropping the table delete its files too. Left out, or `purge=False`, the
warehouse only forgets the table: its files stay in its folder, and a table created there
again gets the old rows back once `repair_partitions` lists their Partitions. Keep `purge=True`
for a table you rebuild from its sources; leave it out for one whose files you would want
back.

### Choose its file format

`stored_as=` is the file format: `"ORC"`, the usual one and what you get when you leave it
out, which Hive reads fastest, or `"PARQUET"`, which more tools outside Hive read.
`compression=` is how its files are packed: ORC's `"ZLIB"` makes smaller files, `"SNAPPY"`
faster ones. `properties=` takes any other table property. `create_table` writes them all:

>>> text = show_hive(create_table(job_region_costs, may_exist=True))  # -> str
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_region_costs (
  job_id BIGINT,
  cost_cents BIGINT,
  PRIMARY KEY (job_id, region, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (
  region STRING,
  dt STRING
)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_region_costs'
TBLPROPERTIES (
  'external.table.purge'='true',
  'orc.compress'='ZLIB',
  'made_by'='mart__job_region_costs.ipynb'
);

### Choose its Partitions

`partitioned_by=["region", "dt"]` keeps each region's rows in a folder of their own, and each
of its days in a folder inside that, as ops.region_costs does. A Statement that filters region
reads only that region's folders, and one that filters dt too reads fewer still. A table's
Partitions are whichever columns its reads filter most: a region, a day, a load, or none at
all, as the Example project's mart.job_notes has none.

A write fills each Partition from its rows' own values, so its SELECT names every partition
column, anywhere: the Toolbox puts them last, in the order `partitioned_by=` gives, where Hive
reads them from. Here ops.region_costs writes its days like 20260924, and mart.job_region_costs
keeps them that way, since the Toolbox writes each value exactly as it is given:

>>> def write_days(first_day: str, last_day: str) -> Statement:
...     return statement(
...         INSERT_OVERWRITE(job_region_costs),
...         SELECT(region_costs.job_id, region_costs.region, region_costs.dt,
...                AS(sum_of(region_costs.cost_cents), "cost_cents")),
...         FROM(region_costs),
...         WHERE(between(region_costs.dt, first_day, last_day)),
...         GROUP_BY(region_costs.job_id, region_costs.region, region_costs.dt),
...     )
>>> text = show_hive(write_days("20260922", "20260924"))
-- The Session setting "dynamic_partitions": this write fills region, dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.job_region_costs PARTITION(region, dt)
SELECT
  region_costs.job_id,
  SUM(region_costs.cost_cents) AS cost_cents,
  region_costs.region,
  region_costs.dt
FROM ops.region_costs AS region_costs
WHERE
  region_costs.dt BETWEEN '20260922' AND '20260924'
GROUP BY
  region_costs.job_id,
  region_costs.region,
  region_costs.dt;

The columns in PARTITION(...) have no value: the warehouse takes each row's region and dt
from the SELECT's last columns. Doing so is Hive's dynamic partitioning, which a Session
setting switches on, so `show_hive` prints its two SET lines first. `run` sends the write
alone: send the Session setting first, with `hive_settings`, before the first such write. The
warehouse keeps it for as long as your execute's connection lasts, and sending it again does
no harm. `project.run_tables()` sends it for you. Here it goes to the Example database's
execute, which prints each SET line:

>>> run(hive_settings("dynamic_partitions"), execute=execute)
execute: SET hive.exec.dynamic.partition=true
execute: SET hive.exec.dynamic.partition.mode=nonstrict

INSERT OVERWRITE replaces only the Partitions its rows hold: a region and day with no rows
keeps whatever it held before. So if a region drops out of the table you read, its old rows
stay in the Saved table until you drop them with the admin module's drop_partitions.

A write can name some Partitions itself instead, with `partition={...}`: here the eu region,
whose rows then leave region out of SELECT. The columns it names come first in
`partitioned_by=`, and the rest are filled from the rows:

>>> text = show_hive(statement(
...     INSERT_OVERWRITE(job_region_costs, partition={"region": "eu"}),
...     SELECT(region_costs.job_id, region_costs.dt,
...            AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(equals(region_costs.region, "eu"),
...           between(region_costs.dt, "20260922", "20260924")),
...     GROUP_BY(region_costs.job_id, region_costs.dt),
... ))
-- The Session setting "dynamic_partitions": this write fills dt from its rows.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart.job_region_costs PARTITION(region = 'eu', dt)
SELECT
  region_costs.job_id,
  SUM(region_costs.cost_cents) AS cost_cents,
  region_costs.dt
FROM ops.region_costs AS region_costs
WHERE
  region_costs.region = 'eu' AND region_costs.dt BETWEEN '20260922' AND '20260924'
GROUP BY
  region_costs.job_id,
  region_costs.dt;

### Add Buckets only to a big table

`bucketed_by=` with `buckets=` spreads each Partition's rows into that many files by the values
of some columns, and `sorted_by=` sorts the rows in each. A join on those columns can then pair
file with file instead of reading everything. It pays off only on big tables, tens of millions
of rows a Partition, joined on those columns; and changing it means writing the whole table
again. Most Saved tables need none. Say mart.event_facts, every event with its minutes, is
such a table, joined on job_id every run:

>>> project.new_table("mart.event_facts")
Made tables/mart__event_facts/: mart__event_facts.ipynb and lineage/, from
admin/templates/saved_table.py.
Wrote references/mart__event_facts.py: fill in its <...> and TODO lines.

The file `references/mart__event_facts.py`, after you fill it in:

    \"\"\"mart.event_facts - one row per event of a run, with its minutes.\"\"\"
    from sqlglot_composer import Table

    event_facts = Table(
        "mart.event_facts",
        columns={"event_id": "bigint", "job_id": "bigint", "minutes": "int", "dt": "string"},
        partitioned_by=["dt"],
        key=["event_id"],
        location="/data/your_team/mart.db/event_facts",
        bucketed_by=["job_id"],
        buckets=16,
        sorted_by=["job_id"],
    )

`from references import mart` ran before this file was filled in, so `mart` doesn't have it
until the kernel restarts; its own file gives it now:

>>> from references.mart__event_facts import event_facts
>>> print(to_hive(create_table(event_facts)))
CREATE EXTERNAL TABLE mart.event_facts (
  event_id BIGINT,
  job_id BIGINT,
  minutes INT,
  PRIMARY KEY (event_id) DISABLE NOVALIDATE
)
PARTITIONED BY (
  dt STRING
)
CLUSTERED BY (job_id) SORTED BY (job_id) INTO 16 BUCKETS
STORED AS ORC
LOCATION '/data/your_team/mart.db/event_facts'

### Why there are no indexes

Hive removed indexes in its version 3, so the Toolbox writes none. What makes a read fast
instead:

- Partitions: a Statement that filters a partition column, as every Load limit insists, opens
  only those Partitions' folders, and one that filters a second partition column too opens
  fewer still.
- Fewer, larger files: ORC and Parquet files keep each column's smallest and largest values,
  so the warehouse skips the parts of a file a condition rules out, and a few large files
  open faster than many small ones.
- Buckets, for big tables joined on the same columns, as above.
- Statistics: once the warehouse has counted a table's rows and values, it picks how to join
  it, such as sending a small table to every machine instead of sorting both.

[Keep reads and joins fast](#keep_reads_and_joins_fast) shows the last three at work.

## Check it worked

The write's rows come from its SELECT, which the Example database can run on its own: on
2026-09-24, one job billed in eu has its cost in, and one has its bill still to come.

>>> costs_on_the_day = statement(  # -> Statement
...     SELECT(region_costs.job_id, region_costs.region, region_costs.dt,
...            AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(equals(region_costs.dt, "20260924")),
...     GROUP_BY(region_costs.job_id, region_costs.region, region_costs.dt),
... )
>>> run(costs_on_the_day, query=query)  # -> DataFrame
   job_id region        dt  cost_cents
0       1     eu  20260924       100.0
1       2     eu  20260924         NaN

At work, once `create_table` has made the table, `check_table_reference` sends DESCRIBE
FORMATTED, which lists how the table is kept, and compares that too. A stand-in query plays a
table made by hand at a folder it shares with other tables, /data/your_team/tables, as the
warehouse would describe it:

>>> import pandas as pd
>>> def query_at_work(hive: str) -> pd.DataFrame:
...     return pd.DataFrame([
...         ("job_id", "bigint", ""), ("cost_cents", "bigint", ""),
...         ("# Partition Information", None, None), ("# col_name", "data_type", "comment"),
...         ("region", "string", ""), ("dt", "string", ""),
...         ("# Detailed Table Information", None, None),
...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
...         ("Table Type:", "EXTERNAL_TABLE", None),
...         ("Table Parameters:", None, None),
...         ("", "external.table.purge", "true"), ("", "orc.compress", "ZLIB"),
...         ("", "made_by", "mart__job_region_costs.ipynb"),
...         ("# Storage Information", None, None),
...         ("InputFormat:", "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat", None),
...     ], columns=["col_name", "data_type", "comment"])
>>> check_table_reference(job_region_costs, query=query_at_work)
mart.job_region_costs differs from its Table reference.
Problems:
  - it is at hdfs://namenode:8020/data/your_team/tables, not at /data/your_team/mart.db/job_region_costs, the folder location= names: change the line to location="hdfs://namenode:8020/data/your_team/tables", if that is the own folder of the table. A folder that isn't a table's own may hold other tables' files: two tables in one folder read each other's files, and an INSERT OVERWRITE of a Partition in one can delete the other's files for that Partition. Move it with admin.move_to_own_folder(t, query=...).

Everything else matches. The warehouse writes a folder in full, with `hdfs://namenode:8020`
before it, and the Toolbox compares the folder alone. [Move a Saved table to its own
folder](#move_a_saved_table_to_its_own_folder) moves a table that shares a folder.

## Common mistakes

### Giving two Saved tables one folder

`location=` is the table's own folder, and no other Saved table may use it, nor a folder
inside it. A second Table reference copied from the first, with its name changed and its
folder not, is refused:

>>> Table("mart.job_region_costs_eu", columns={"job_id": "bigint", "dt": "string"},
...       partitioned_by=["dt"], location="/data/your_team/mart.db/job_region_costs")
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('mart.job_region_costs_eu') would be at /data/your_team/mart.db/job_region_costs, the same folder as mart.job_region_costs (/data/your_team/mart.db/job_region_costs).
...

Give it a folder of its own, `location="/data/your_team/mart.db/job_region_costs_eu"`.

### Leaving a partition column out of the write

A write fills each partition column `partition=` doesn't name from its rows, so its SELECT
must list it. Left out, it is refused as you build it:

>>> statement(
...     INSERT_OVERWRITE(job_region_costs),
...     SELECT(region_costs.job_id, region_costs.dt,
...            AS(sum_of(region_costs.cost_cents), "cost_cents")),
...     FROM(region_costs),
...     WHERE(between(region_costs.dt, "20260922", "20260924")),
...     GROUP_BY(region_costs.job_id, region_costs.dt),
... )
Traceback (most recent call last):
...
sqlglot_composer.refusals.GuardRefused:
  What happened:  INSERT_OVERWRITE(job_region_costs): it leaves out region.
...

### Naming a later Partition but not an earlier one

Hive takes the partition columns in order: the ones a write names first, then the ones it
fills from the rows. So `partition={"dt": "20260924"}` alone, with region left to the rows,
is refused:

>>> INSERT_OVERWRITE(job_region_costs, partition={"dt": "20260924"})
Traceback (most recent call last):
...
ValueError:
  What happened:  INSERT_OVERWRITE(job_region_costs, partition=...) names dt, but not region, which comes before it in mart.job_region_costs's partitioned_by (region, dt).
...

Name region too, or leave dt to the rows.

### Storage on a table you only read

Only your own Saved tables are stored as you say. A Table reference with no `location=` is a
table someone else owns, and giving it storage is refused:

>>> Table("ops.other_costs", columns={"job_id": "bigint", "dt": "string"},
...       partitioned_by=["dt"], purge=True)
Traceback (most recent call last):
...
ValueError:
  What happened:  Table('ops.other_costs') has purge= but no location=.
...

## Next

- Move a table that shares a folder: [Move a Saved table to its own
  folder](#move_a_saved_table_to_its_own_folder).
- Statistics, small files and map joins: [Keep reads and joins fast](#keep_reads_and_joins_fast).
- Write some of a table's Partitions again: [Rewrite some partitions](#rewrite_some_partitions).
- Every option in one place: the gallery's [`create_table`](examples.html#create_table) entry,
  and `help(Table)`.
"""
