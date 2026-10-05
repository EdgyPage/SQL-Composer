# Example database tables for the intermediate level

Type: task
Status: resolved
Blocked by: 03
Size: M

## Question

Three new tables, rows as plain literal lists: a 14-day event table (rollups, backfills,
incremental loads), a daily snapshot of each job's team (as-of lookups), and a cost table
partitioned by region then dt, its days written like 20260911 (a second partition and a
date_format). Pandas twins in conftest's example_rows; DESCRIBE and SHOW PARTITIONS answered;
each Edition's Example database runs them, with a pandas stand-in where sqlglot's executor
can't.

## Done when

- Every existing golden, gallery entry and result is unchanged.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in the commit that resolves this ticket.

- **The names.** `ops.job_events`, `ops.job_owners` and `ops.region_costs`, reached as
  `example_database.job_events` and so on: plain, in the ops database beside the first three,
  and each says what one row is about (a job's event, a job's owner, a region's cost). No new
  glossary word.
- **The tables**, in `composer_core/example_database.py`, so both Editions get them. All three
  hold 14 days, 2026-09-11 (a Friday) to 2026-09-24, so `week_start` gives three weeks; today
  stays 2026-09-25, the day after the last day. 141 rows in all, as literal lists.
  - `job_events` (57 rows; key `event_id`): event_id, job_id, event_type (start / finish / retry
    / fail), minutes (since the run started), dt. nightly_load runs daily (one retry on 09-16),
    invoice_sync on weekdays and is still running on 09-24 (a start, no finish), report_build on
    four days (a retry on 09-14, a fail on 09-18); cache_warm never runs, as in ops.jobs.
  - `job_owners` (56 rows; key `job_id`, `dt`): job_id, team, owner, dt, every job on every
    day. report_build moves from data (ana) to finance (chloe) on 2026-09-18, so its newest
    team agrees with ops.jobs; cache_warm's owner is NULL.
  - `region_costs` (28 rows; key `job_id`, `region`, `dt`): job_id, cost_cents (bigint), region
    (eu, us), dt written like 20260911 (`date_format="%Y%m%d"`), partitioned by region, then dt.
    London and Paris jobs are billed in eu, New York's in us; invoice_sync's 09-24 cost is NULL,
    as it is still running.
  - They keep a record of their own: no run_id, and they don't match job_runs run for run (the
    docstring says so).
- **send.** DESCRIBE lists each table's partition columns after its columns, region then dt for
  region_costs (`_PARTITIONS` names the one table partitioned by two columns); SHOW PARTITIONS
  lists `region=eu/dt=20260911` style. The unknown-table refusal names all six tables.
- **write_table_reference on region_costs** is unchanged behaviour: region, the first partition,
  holds no day, so it writes `date_partition=None` with the TODO architecture-review ticket 01
  made ("if dt holds the days, name it"). Named, check_table_reference then gives the line
  `date_format="%Y%m%d",`, and on the shipped Table reference it notes the second partition.
  It does not find dt and its date_format by itself; teaching it to is a change to a decided
  behaviour, so it is left to the user (how-to 19 can show the two steps).
- **sqlglot's executor** (sqlglot 30.19.0) runs plain SELECTs, GROUP BY, COUNT(DISTINCT),
  joins on job and day (the as-of lookup), LEFT JOIN, if_else, fill_null, a Derived table and
  BETWEEN on the compact days. It can't run `week_start` (no NEXT_DAY), `month_start` (no
  TRUNC), so no week or month rollup, nor `row_number` (newest snapshot per key); the newest
  per key by `max_of(dt)` runs. Those how-tos need the gallery's pandas stand-in. Spark
  Composer's Example database loads the three from `_TABLES`, with no list of its own, and runs
  every test here.
- **Tests.** `tests/test_example_database_intermediate.py` (shared): DESCRIBE, SHOW PARTITIONS,
  write_table_reference's exact text, check_table_reference, check_key, a query per table
  against pandas from `example_rows`, between and last_n_days on the compact days, a
  `datetime.date` bound, a dashed day refused, and each key unique.
- **What else changed.** The module docstring lists the six tables, so both galleries were
  regenerated (that entry and the intro, "the made-up tables" and "the Example database's last
  day"); the README template says six tables, and test_export_clean with it. The goldens are
  unchanged.

