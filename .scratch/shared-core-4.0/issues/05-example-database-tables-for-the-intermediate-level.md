# Example database tables for the intermediate level

Type: task
Status: open
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
