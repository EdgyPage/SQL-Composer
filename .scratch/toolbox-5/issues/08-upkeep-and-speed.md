# Upkeep and speed

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

Map family 8. repair_partitions(t) (MSCK REPAIR TABLE), compute_statistics(t, day) (ANALYZE
... COMPUTE STATISTICS, and FOR COLUMNS), explain(s); the first two refused on a table that
isn't the user's. The shipped Session settings for map-joins, statistics on write and merging
small files documented beside them.

## Done when

- Each written in both Editions; a how-to on speed: Partitions, files, Buckets, statistics,
  broadcast joins and explain.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built in both Editions, the shared code in a new core file, `composer_core/upkeep.py`
(registered in `tools/editions.py`'s `CORE_FILES`). Public names go from 67 to 70.

**What was built**

- `repair_partitions(t)` writes `MSCK REPAIR TABLE <table>`. It refuses a table that isn't one
  of the user's Saved tables, and a Saved table with no Date partition (Spark refuses MSCK on
  an unpartitioned table, and there are no day folders to find).
- `compute_statistics(t, day=None, columns=False)` writes
  `ANALYZE TABLE <table> PARTITION(dt = '<day>'[, region]) COMPUTE STATISTICS`, with
  ` FOR COLUMNS a, b` when `columns=True` (every column but the Partitions) or a list (the
  table's own column attributes, `[t.job_id]`, or names). The columns are always listed:
  Spark refuses a bare `FOR COLUMNS`, Hive takes the list. The day is written the table's
  way (`as_date(..., compared=False)`, whose refusal now says "was given the day" and drops
  the last_n_days hint); a Saved table with no Date partition takes no day. Refused: a
  missing day, several days (with a loop as the fix), a day for a table with none, a
  Partition column, another table's column, and anything but True or a list.
- `explain(s)` writes `EXPLAIN ` before exactly what `to_hive(s)` gives, the automatic LIMIT
  too, and refuses what to_hive would (the dates cap). `run(explain(s), send=...)` gives back
  the plan as text: the DataFrame's only column joined by lines (Hive gives a row per line,
  Spark one row), as a `str` that prints itself in a notebook (`running.HivePlan`). It refuses
  an Unchecked statement (fix: `unchecked_hive("EXPLAIN ...")`), Session settings, anything
  not a Statement, and a Statement made by create_table, drop_table, repair_partitions,
  compute_statistics or explain, naming which.
- `need_saved_table(t, what)` in `composer_core/tables.py`: the shared refusal of a table
  that isn't one of the user's Saved tables (no `location=`), for ticket 04 too. `what` is the
  call's name as the user writes it ("repair_partitions", "admin.drop_days"); the message
  reads `repair_partitions(job_runs): ops.job_runs isn't one of your Saved tables: its Table
  reference has no location=.`
- Each is a Statement with `_ddl` set (Node kinds `Repair`, `Analyze`, `Explain` in
  `trees.KINDS`), so by_day, derived and export_lineage refuse them as they refuse
  create_table. Writers: sqlglot Composer holds each as an `exp.Command` (sqlglot 25 reads all
  three only as a Command and 30 has an `Analyze` tree of its own, so a Command writes the same
  Hive on both); its `read_back` reads them back through the parts sqlglot reads (the table
  and PARTITION as a write's target, the columns as a SELECT, the Statement after EXPLAIN),
  never the whole command, so sqlglot logs nothing. Spark Composer prints them by hand. Both
  write the same Hive: no `DECLARED_DIFFERENCES` row.
- `running.day_partition(table, day)` is the `PARTITION(dt = '<day>', region)` a write used
  inline, now shared with compute_statistics.
- Example databases: neither runs `repair_partitions` or `compute_statistics` (global temp
  views, and the sqlglot executor; the send's refusal now says its tables are nothing to
  change or count again, and that to_hive shows any Statement). Spark Composer's answers an
  `EXPLAIN` of a query with Spark's plan; sqlglot Composer's engine refuses it ("its executor
  has no EXPLAIN"). The gallery shows only the plan's first line, since Spark numbers the
  columns under it afresh each run.
- Checked on pyspark 4.0.4's parser: `MSCK REPAIR TABLE t`, `ANALYZE TABLE t PARTITION(dt =
  'x', region) COMPUTE STATISTICS [FOR COLUMNS a, b]` (Spark drops the PARTITION for column
  statistics and counts the whole table: the docstring and how-to say so) and `EXPLAIN` of a
  SELECT, a WITH and an INSERT are all taken; bare `FOR COLUMNS` is refused.
- `create_table(t, may_exist=True)` was not rebuilt: its docstring now says it is safe to
  send again, that it doesn't compare the table (check_table_reference does), and points to
  repair_partitions; its golden case `create_table:may_exist` and Spark's real-table test
  already cover both Editions.
- The shipped Session settings: hive_settings' "map_joins" now says explain shows whether
  Hive chose a map join, and "statistics_on_write" that compute_statistics counts a day
  written without it; compute_statistics' and explain's docstrings name them, and the
  how-to sends "merge_small_files", "statistics_on_write" and "map_joins".
- A how-to, Intermediate 33 "Keep reads and joins fast" (`#keep_reads_and_joins_fast`):
  reading only the days needed (Partitions), files few and large ("merge_small_files"),
  statistics ("statistics_on_write", compute_statistics), map joins ("map_joins"), Buckets,
  explain, and repair_partitions; it links `#choose_how_a_saved_table_is_stored` for "Why
  there are no indexes" and for Partitions and Buckets rather than repeating them, and says
  which Example database can't run what. **The one sentence on ticket 05's `broadcast=True`**
  is its own paragraph at the end of the step "Let Hive copy a small table to every worker":
  "Where Hive still sorts both sides, `JOIN(jobs, ON=..., broadcast=True)` asks it by name to
  copy jobs to every worker." Drop it if 05 doesn't land.
- Tests: `tests/test_upkeep.py` (both Editions, Spark's Example database's plan included);
  golden cases `edge:upkeep:*` (each EDGE table, awkward and Spark-reserved names, a compact
  day, no Date partition, the refusals, explain of a read, a write, Derived tables and a
  create_table); three Linux-only cases in `tests/spark_edition/test_spark_hive_tables.py`
  (repair_partitions finds the day of a table dropped without purge and made again, sent
  twice; compute_statistics counts a day and a column, sent twice, read back through
  DESCRIBE FORMATTED; explain of a write gives Spark's plan and writes nothing): not run
  here, Windows lacking winutils, so CI is their only check.
- Docs: CHANGES.md 5.0 "New"; CONTEXT.md gains Statistics and Plan; how-to range 19 to 33
  (`tools/how_to_page.py`, `tests/test_how_tos.py`, `tests/repo/test_export_clean.py`); the
  galleries, how-to pages, both golden corpora and the Example projects regenerated.

**Code review** (code-review skill, since 5b82ba1). Standards, no hard violation; done:
"upkeep" taken out of prose (CHANGES heading, module docstring, comments), since it isn't a
glossary word and sits near the Admin statement's avoided "maintenance"; the Statistics
glossary entry reworded; "each step's Statistics line" now "each step's line headed
"Statistics:"", Hive's own label; sqlglot's EXPLAIN check made case-blind like the core's.
Answered: Statistics and Plan are written lower case, as Warehouse is, being Hive's own
words; the Example database's refusal keeps its "only answers SELECT, ..." line (how-to 10
shows it), its fix reworded instead; `need_saved_table`'s docstring names admin.drop_days as
ticket 04's use, on purpose; `_columns_counted` takes None as False and a single column
without a list, for the beginner; `_upkeep` repeats create_table's two lines rather than
touch tables.py's; the kind-to-name map `_MADE_BY` and the writers' own dispatch were left
apart, as each Edition's writer is its own file. Spec, nothing missing; answered:
- explain refuses create_table and the like, though the ticket says "any Statement": Hive's
  EXPLAIN of DDL shows no plan worth reading, and "only reads" is about queries and writes;
  the refusal names the function. Open to the user.
- export_lineage refuses the three, as it refuses create_table, where map family 9 says "left
  out": refusing is what leaves them out today; skipping them silently in a list passed whole
  is a change for every Statement of this kind (create_table, drop_table, the admin module),
  so it is left for ticket 09 or the user.
- repair_partitions' refusal of a Saved table with no Date partition wasn't asked for:
  kept, as Spark refuses MSCK there and there is nothing to find.
- `HivePlan` (a str that prints itself in a notebook) and the Spark Example database's
  EXPLAIN are small additions serving "Hive's plan as text" and "whether the Example
  databases can run them".

**Beginner reader:** [report](../reports/08-beginner-reader.md), 27 stops. Done: the first
lines of repair_partitions ("lists the days in a Saved table's folder") and
compute_statistics ("counts a Saved table's rows for one day"); "since" is "because";
"where" for "whereas" reworded; the two-pronoun sentence; a table with no Date partition
(date_partition=None) said; the Spark column-count warning now advises naming few columns;
**columns= now takes the table's column attributes** (`columns=[daily_runs.job_id]`, the
docstring's example), as the rest of the Toolbox does, and refuses another table's column by
name; the badly written day's refusal no longer says "compares" or suggests last_n_days;
explain's docstring split into paragraphs and a list, the automatic LIMIT tied to
set_load_limits(rows=...), and the Example database's plan said per what it runs on; the
Example database's refusal fix names to_hive of any Statement; the how-to's "list of days
true", the map_joins step now runs the setting as the earlier ones, the "after" Statistics
line shown in full, the day rule limited to a table with a Date partition; the CHANGES entry
is a list; CONTEXT's Statistics wording. Left: stop 22, the `broadcast=True` sentence, kept
as the orchestrator asked (above); stop 14, explain's example reads job_runs, as every
Statement example in the docstrings does; stop 23, the Edition-only markers, which the page
strips.

**Open for the user**

- explain refuses a Statement made by create_table, drop_table, repair_partitions,
  compute_statistics or explain, rather than taking "any Statement" literally.
- export_lineage refuses these Statements (as create_table's) rather than skipping them in a
  list; the map's family 9 may mean skipping.
- compute_statistics takes `columns=` beyond the ticket's `compute_statistics(t, day)`: True,
  or a list of the table's columns.
