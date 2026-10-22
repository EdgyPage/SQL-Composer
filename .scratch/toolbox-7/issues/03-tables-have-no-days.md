# Tables have no days

Type: task
Status: claimed
Blocked by: 02
Size: XL

## Question

The user (2026-10-21): "There's an assumption throughout the entire codebase that tables are
built with days in mind. It's distracting and annoying and incorrect. Get rid of all of those
DAYS assumptions and other assumptions on how I create tables. Assume the canonical way I create
a table is something like SET namespace location (known by me), CREATE table at LOCATION
filepath_string_{db}.db/table." Then: "different tables have different partitions", "not every
table has keys", and of paths: "I'll navigate that on my own in a throwaway easy to configure
config file." The map's "No days" and ADR 0011 hold the design.

What exists (2026-10-21), from the inventory that day:
- `date_partition` is a required argument of `Table`, with no default (`tables.py:665`).
- `partitioned_by=` is refused without it (`tables.py:982`).
- `run_tables(day)` calls `write_day(day)`.
- A dated Saved table can't be filled from an undated table (`running.py:280`).
- These need a day:
  - the Date bound Load limit
  - the dates cap
  - the one-day, kept-day, date-format and time-of-day Guards
  - the four `by_day` Guards
  - `admin.drop_days`
  - `repair_partitions`
- `create_table` adds `/<db>/<table>` to `location=` and needs an absolute path
  (`tables.py:888`).

A table with no days already creates, writes whole and shows in Lineage
(`tests/test_write_no_day.py`).

The user settled the two open questions on 2026-10-21; the map's "No days" Notes hold them.

## Done when

- **Table**:
  - `Table(name, columns, *, partitioned_by=None, key=None, ...)`, with no
    `date_partition` and no `date_format`. Passing either is refused, naming `partitioned_by=`.
  - Partition columns may be any columns, of any type, in the order Hive partitions by.
  - `write_table_reference` writes every partition column DESCRIBE reports, with no guess at a
    day.
  - `check_table_reference` checks them against DESCRIBE.
- **Reads**:
  - A read of a partitioned table that filters none of its partition columns is refused
    (a Load limit), with `reads_all_partitions=True` as its opt-out.
  - An unpartitioned table is never refused.
  - "At both ends" and `set_load_limits(dates=...)` are gone.
  - `last_n_days`, `between`, `week_start` and `month_start` work on any date column, as
    written, and count as a filter on a partition column when they name one.
- **Writes**:
  - `INSERT_OVERWRITE(t)` and `INSERT_INTO(t)` into a partitioned table write
    `PARTITION(<its columns>)` filled from the rows. The settings that needs are shown and sent
    with the write, as `settings_needed` does now.
  - `partition={"region": "EU"}` writes those partitions as static values, and the rest
    dynamically.
  - A write fills from any table, partitioned or not.
  - These are gone:
    - the one-day-per-write Guard
    - the kept-day Guards
    - the date-formats Guard
    - the time-of-day Guard
    - `by_day` and its Guards
    - `day_partition`
    - `writes_one_day`
- **Keys**:
  - A Key names one row of the table, with no day dropped from it.
  - A table with no Key is written unchecked and needs no `unproven_key=True`.
  - A join onto a table with no Key keeps the repeated-rows Warning. Its message says
    `many_matches=True` is right when the user knows the match is one row, and no longer
    tells every table to declare a Key.
  - `check_key(t, query=..., where=None, reads_all_partitions=False)` reads what `where=`
    picks, as the map says.
- **Projects**:
  - `run_tables(tables=None, query=..., execute=...)` takes no day.
  - A Table notebook's logic defines `write()`, which takes nothing.
  - `project.load` requires `write`.
  - The run_tables notebook has no `DAY`.
  - The Templates keep working with `write()` and lose their day placeholders. 04 replaces
    them.
- **Storage**:
  - `location=` is the table's folder exactly as written. Nothing is added to it, and it
    needn't be absolute.
  - Two Saved tables naming one folder, or one inside the other, are still refused.
  - `check_table_reference` compares the folder as written with DESCRIBE's Location.
  - External only, ORC unless the reference says Parquet, and no TRUNCATE or MERGE all stay.
- **Upkeep and admin**:
  - `repair_partitions` works on any partitioned table.
  - `compute_statistics(t, partition=None, columns=False)` counts one partition or the whole
    table.
  - `admin.drop_partitions(t, where=...)` replaces `admin.drop_days`, refusing a condition on
    anything but partition columns.
  - `admin.add_columns` cascades on any partitioned table.
  - `admin.move_to_own_folder` copies a table whole or a partition at a time.
- **Lineage**:
  - No text, arrow or legend speaks of days.
  - A write into partitions adds no arrow; a static `partition={...}` is one line on the
    write's box.
- **The Reference sheet**: its `date_partition` column becomes `partition`, which is "yes" for
  each partition column.
- The Example database, the Worked examples, the how-tos, the Example projects and the README
  still run, changed only as far as these names need. 04 and 07 rework them.
- CHANGES.md's "To update from 6.x" covers:
  - each `date_partition=` and `date_format=` in a Table reference;
  - each `write_day(day)`;
  - `run_tables(day)`;
  - `by_day`;
  - `drop_days`;
  - `compute_statistics(day=)`;
  - a `location=` that relied on the folder being added.
- CONTEXT.md, in the words grilled on 2026-10-21:
  - **Table reference**: "its columns and their types, its Partitions and its Key, where it has
    them, and the filters that concern that table alone".
  - **Key**: "The columns whose values name exactly one row of a table: the table's primary
    key, declared on its Table reference. Not every table has one, and nothing is checked
    against a Key a table doesn't have. The warehouse never checks it; the Toolbox does, before
    writing a Saved table that has one and when joining, ...", with the rest as it is.
  - **Partition**: "A slice of a table: the rows that share one value of each column the table
    is partitioned by. Each table has its own partition columns, of any kind - a date, a region,
    a load - or none, and a Statement should constrain them rather than read the table whole."
    Its _Avoid_ adds `Date partition`.
  - **Date partition** is removed.
  - **Saved table**: "its files are in a folder of its own, which its Table reference names
    along with how it is stored", with the rest as it is.
  - **Admin statement**: "such as dropping a table or some of its Partitions".
  - **Statistics**: "about a table's Partitions and their columns".
  - **Template**: "the tables, columns, values and names".
- CLAUDE.md's Definition of done, the beginner reader included.
