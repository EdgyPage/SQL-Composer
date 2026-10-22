# The user's Saved tables are external, each in a folder of its own

Status: accepted; in part superseded by ADR 0011 (7.0): `location=` is used as written, with no folder added, Partitions are any columns, and `admin.drop_partitions` replaces `drop_days`

Hive 3 has two kinds of table. A managed, transactional table keeps its files where Hive chooses,
and takes `MERGE`, `UPDATE` and `DELETE`, at the cost of compaction and of being hard for other
tools to read. An external table keeps its files at a location the user gives, and is rewritten
with `INSERT OVERWRITE`. The user's admin policy has them create external tables only; the tables
other teams own, managed or not, they may only read.

So in 5.0:

- **Every Saved table is external**, at the user's base location plus a folder of its own, which
  the Toolbox always adds. Two Saved tables at one folder are refused, and `check_table_reference`
  reports one whose folder is shared or isn't its own: two external tables in one folder read each
  other's files, and an overwrite of a day in one can delete the other's files for that day. The
  user's tables were found sharing a folder on 2026-10-15; `admin.move_to_own_folder` and its
  how-to move them out.
- **A Saved table's storage is on its Table reference**: location, purge (`external.table.purge`,
  since dropping an external table leaves its files unless it is set), any other table
  properties, file format and compression, Partitions after the day, Buckets and sort order.
- **`MERGE`, `UPDATE`, `DELETE` and `TRUNCATE` are left out**: none works on an external table. A
  day is changed by writing it again with `INSERT OVERWRITE`, which can be sent any number of
  times; old days go with `admin.drop_days`.

## Considered options

- **Both kinds, chosen per Saved table**, so `MERGE` and the rest could run on a managed one. Not
  needed: the user may create external tables only.
- **A location option, off by default, for a folder per table.** Rejected: a table sharing a folder
  is never right, so the folder of its own is always added.

## Consequences

- Reading managed tables is unchanged: a SELECT doesn't care what kind of table it reads.
- Should policy ever allow managed tables, this decision is the one to reopen.
