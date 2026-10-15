# The Saved table's storage

Type: task
Status: open
Blocked by: -
Size: L

## Question

Map family 2 and ADR 0007. On a Saved table's Table reference: `location=` (a base path
plus the table's own folder, always added; two at one folder refused), `purge=` and
`properties=` (TBLPROPERTIES), `stored_as=`, `compression=`, `partitioned_by=` (Partitions after
the day, filled per row by the write, with the "dynamic_partitions" Session setting printed ahead
of it), `bucketed_by=`/`buckets=`/`sorted_by=`. create_table writes `CREATE EXTERNAL TABLE` with
all of it; check_table_reference compares it with `DESCRIBE FORMATTED`, and reports a Saved table
whose folder is shared or isn't its own.

## Done when

- Each option written and compared, in both Editions; a shared folder reported and refused.
- A how-to section on why there are no indexes, and what makes reads fast instead.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).
