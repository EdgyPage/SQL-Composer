# The Saved table's storage

Type: task
Status: resolved
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

## Answer

Built in both Editions (the shared code in `composer_core/`, each Edition's `writing.py`
writing the same Hive):

- **Table(...) takes a Saved table's storage**: `location=` (the folder the user's Saved tables
  go in; the Toolbox always adds `<database>/<table>`, lower case), `purge=` (written as
  `'external.table.purge'`), `properties=`, `stored_as=` ("ORC", the default, or "PARQUET"),
  `compression=` (per format: `orc.compress` or `parquet.compression`), `partitioned_by=`,
  `bucketed_by=` with `buckets=`, and `sorted_by=`. Each is checked as the reference is made:
  storage without `location=` is refused (a table someone else owns has none), as is a
  `location=` that isn't a whole path or already ends with the table's own folder, any option
  create_table couldn't write, properties the Toolbox writes from its own arguments, and the
  properties Spark reserves (`comment`, `owner`, ...; found when Spark's parser refused a
  golden case). **Two Saved tables at one folder are refused**: a Table reference whose folder
  equals, or nests inside or around, another Saved table's in the same Python.
- **create_table writes `CREATE EXTERNAL TABLE`** with PARTITIONED BY (the day, then
  `partitioned_by`), CLUSTERED BY ... SORTED BY ... INTO n BUCKETS, STORED AS, LOCATION and
  TBLPROPERTIES, and refuses a Table reference with no `location=`.
- **check_table_reference** sends DESCRIBE FORMATTED for a Saved table (one with `location=`)
  and compares: external or managed, its folder (Hive's `hdfs://namenode:8020/...` matches
  `/...`), file format, Partitions after the day, Buckets, and purge, compression and
  properties where given. It reads Hive 3's layout (labels with colons, Table Parameters
  rows, `Order(col:...)`) and Spark's (`Type`, `Table Properties [a=b, ...]`, backticks). A
  table not at its own folder is a problem naming `admin.move_to_own_folder(t, send=...)`; one
  at its own folder under another folder says which `location=` to write.
- **Writes into a table with `partitioned_by=`** are `PARTITION(dt = '<day>', region)`, the
  later Partitions last in SELECT. `show_hive` (and so every Example project's dry run) prints
  the Session setting ahead of such a write; `run` sends the write alone. How it is printed,
  for ticket 03 to reconcile: `composer_core/running.py` holds `DYNAMIC_PARTITIONS` (the two
  `SET hive.exec.dynamic.partition...` settings) and `settings_needed(s)`, which returns a
  comment line `-- The Session setting "dynamic_partitions": this write fills <cols> from its
  rows.` and the `SET ...;` lines; `show_hive` joins them above the Statement's Hive. Ticket 03
  can replace `DYNAMIC_PARTITIONS` with its shipped set and keep or reword the comment.
- **Docs**: Table, create_table, drop_table, check_table_reference, INSERT_OVERWRITE, show_hive
  and run docstrings; a new Intermediate how-to, 31 "Choose how a Saved table is stored",
  with "Why there are no indexes" (the Intermediate group is now 19-31); how-tos 03, 10, 12,
  14, 22 and 23, the Worked example's `runs_to_review` (now `purge=True`), the Example
  projects' six Saved tables, and the starter Template (`<BASE_LOCATION>`, `purge=True`) give
  their Saved tables a `location=`; golden-corpus cases `edge:storage:*` and
  `edge:write:partitioned_by:*`; CONTEXT.md's Saved table; CHANGES.md 5.0; the README's ACID
  note.
- Tests: `tests/test_saved_table_storage.py` (both Editions), and on a real Spark with Hive
  support (Linux and CI only; not run here, Windows lacking winutils):
  `test_spark_hive_tables.py` makes each table in pytest's folder (`in_folder`), checks the
  table is EXTERNAL at its folder, reads every option back through check_table_reference,
  and writes a day by region.

### Review

code-review (Standards and Spec), and what was done:

- Fixed: refusals that named a column the user meant to keep (`partitioned_by` given twice),
  a `buckets=` the user never gave, and a missing period; "base" replaced with the
  glossary's own wording; the shared-folder sentence and the move fix written once
  (`SHARING`, `MOVE_IT`); the "ends with its own folder" refusal no longer fires on a base
  merely named like the table (`reports.tables` at `/data/tables`); folders compared without
  their storage's name in the two-at-one-folder refusal; Bucket and sort columns compared in
  lower case; a send with no Location is now a problem, not a note; the docstring no longer
  claims more than one DESCRIBE can see (a table at its own folder, with another's files put
  there, is found by checking the other table); a managed table gets one problem, not also a
  folder one.
- Answered: the fixes name `admin.move_to_own_folder` and `admin.set_properties`, which
  ticket 04 builds (the map says check_table_reference points to the first); the Session
  setting is named "dynamic_partitions" as ticket 03 will ship it. `_set_storage` setting
  Table's private attributes, and tables.py's growth (a storage module of its own), were
  left as they are: the Toolbox keeps a Table reference's code in tables.py, and a class to
  bundle the storage would be one more thing to study.
- Recorded (Spec): compression and properties left out of a Table reference aren't compared,
  as check_table_reference's docstring says. Spark may refuse to write a Hive table with
  Buckets: how-to 31 says to ask first.

### Beginner reader

Run on everything above. Its costliest stops, and what changed:

1. The admin functions named as fixes don't exist yet: left, as they arrive with ticket 04 in
   the same 5.0; CHANGES now says 4.x tables (managed) are reported and moved with
   `admin.move_to_own_folder`, and writing them still works until then.
2. "dynamic_partitions" named but nothing takes it, and how to send a SET: INSERT_OVERWRITE's
   docstring and how-to 31 now show `send("SET ...")` without its `;`, and say the connection
   keeps it and sending again does no harm; show_hive's and run's docstrings say what
   show_hive prints and run doesn't send. Ticket 03's `hive_settings("dynamic_partitions")`
   will take the name.
3. drop_table and purge: drop_table's docstring now leads with purge and says a rebuild needs
   `purge=True` before creating; the starter Template has `purge=True`.

Also fixed from its report: how-to 31's refusal line, "external" and "managed" defined where
first used, `purge` left out vs `purge=False`, compression per format, partitioned_by's column
in `columns`, Buckets explained, "a array", the fix example for a property's value, "remove
all three", the nested-folder refusal's wording, a region that drops out of the source
keeping its old rows, and the README's ACID sentence.

### Open for the user

- **Where the base folder is kept.** The map says "a plain string in settings.py, such as
  `BASE_LOCATION`", but settings.py is Level 0 beside the Table references, and a script
  can't import from its own Level (tests/repo/test_levels.py), so each Saved table's Table
  reference writes `location="/data/your_team/tables"` itself. To keep it once in
  settings.py, the Level rule would let Table references import settings.py, which imports
  nothing of the project. The user decides.
- `purge=` has no default (left out, nothing is written, so Hive keeps the files on a drop);
  the Template and the Worked example set `purge=True`.
- Spark's built-in Hive metastore may not honour `external.table.purge` on DROP; the Spark
  tests keep each table in a fresh folder so they don't depend on it.
