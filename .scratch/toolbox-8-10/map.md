# Toolbox 8.10: SORT_ARRAY on newer sqlglot, compares that don't run the user's params, and Table references added for you

Label: wayfinder:map

The user (2026-11-24), with 8.9 exported to main: "notes for a small version change. research
SQL breaking verison arraysort and sortarray. Update conversion comparision workflows to
account for params not being actually runable." Then: "notes for small version change. Add
references automatically in relevant workflows." And: "the new version change will be 8.10,
just add this to an accessible section of notes for myself". The user named the version 8.10.
Nothing is built yet: these are the notes, and the decisions under "Not yet specified" are the
user's to settle before any ticket is written.

## For you, in short

1. **SORT_ARRAY breaks on sqlglot 30.24.0 and later.** sqlglot removed `exp.SortArray`, and
   the Toolbox reads it (`converting.py`'s `leave_out_sort_arrays_true`). The Toolbox says it
   supports sqlglot "30.19.0 up to (not including) 31", so a user who installs 30.24 or newer
   gets an error on every Conversion. 8.10 makes the Toolbox work on both sides of that change,
   or narrows the range.
2. **A compare fails when the user's script has params.** A query alone (no original table)
   is compared by sending its `statement.hql` as written, with `<PARM="X"/>` and
   `${hivevar:x}` still in it, so it can't run and the batch never reaches `finished/`.
3. **Table references added for you.** The convert Workflow already adds the ones it needs;
   `new_table` with QUERIES, `new_run_value` and the sources Decision still refuse and send
   you to the references Workflow first.
4. **Ask whether a table is aggregate or historical.** An aggregate table is rebuilt whole by
   each write; a historical table keeps every past Partition, so it is only useful once its
   history is loaded at the start. Today only a Conversion's table whose write reads itself
   gets that first load (its Seed). 8.10 asks about each table, so a historical one gets its
   history loaded too.

## Notes

### SORT_ARRAY and ARRAY_SORT (researched 2026-11-24, on sqlglot 30.23.0 and 30.34.0)

What each engine has, from its own docs and source:

- **Hive**: `sort_array(array)`, one argument, since 0.9.0, ascending; no `array_sort`.
  Hive's master branch still checks for exactly one argument (`GenericUDFSortArray`,
  `checkArgsSize(args, 1, 1)`), and its `FunctionRegistry` registers `sort_array` and
  `sort_array_by` only. Where Hive puts NULLs isn't in its docs (sqlglot assumes first).
  Sources: https://cwiki.apache.org/confluence/display/Hive/LanguageManual+UDF and
  https://github.com/apache/hive/blob/master/ql/src/java/org/apache/hadoop/hive/ql/udf/generic/GenericUDFSortArray.java
- **Spark**: `sort_array(e[, asc])` since 1.5.0, NULLs first ascending and last descending;
  `array_sort(e)` since 2.4.0 (SPARK-23921), NULLs always last; `array_sort(e, comparator)`
  since 3.0.0 (SPARK-29020). From 3.2.2 a comparator returning NULL is an error unless
  `spark.sql.legacy.allowNullComparisonResultInArraySort` is set.
- **Trino**: `array_sort` only, NULLs last. **Databricks**: both, as Spark.

What sqlglot does:

- **To 30.23.0** (the pin): two classes, `exp.SortArray` (`this`, `asc`, `nulls_first`) and
  `exp.ArraySort` (`this`, `expression`). Spark to Hive: `ARRAY_SORT(x)` becomes
  `SORT_ARRAY(x)`, quietly moving NULLs from last to first; `SORT_ARRAY(x, FALSE)` is kept,
  which Hive refuses (8.7's ticket 10 keeps it with a finding); a comparator is dropped with a
  warning.
- **30.24.0 (2026-10-20), the breaking change**: sqlglot PR #8643, commit
  https://github.com/tobymao/sqlglot/commit/094509aad83fff575f1b4d198e4d03c21c432e58, "merge
  SortArray into ArraySort with explicit NULL ordering". `exp.SortArray` is gone; `ArraySort`
  carries `asc` and `nulls_first`. The Hive generator still writes `SORT_ARRAY(x)` but warns
  that Hive's sorts only ascending with NULLs first. It is the only change from sqlglot 25.0 to
  30.34.0 that touches these for Hive or Spark.
- **On 30.34.0**: `SORT_ARRAY(x, FALSE)` from Spark becomes `SORT_ARRAY(x)`, so the descending
  order is lost with only a warning (sqlglot's default is to warn; `ErrorLevel.RAISE` raises
  `UnsupportedError`).

What that means for the Toolbox:

- `leave_out_sort_arrays_true` (`converting.py`, around line 592) finds `exp.SortArray`
  nodes, so it fails on sqlglot 30.24.0 and later; `trees.py`'s arity table has
  `"sort_array": (1, 2)`.
- 8.7's rules (its map's "SORT_ARRAY" section) stay right on any version: `TRUE` is left out,
  since ascending is Hive's only order, and `FALSE` is kept with a finding that Hive may refuse
  it. On 30.24+ the `FALSE` case must be caught before sqlglot quietly drops it.
- An `ARRAY_SORT(x)` read from someone else's Spark-flavoured Hive moves NULLs from last to
  first when it becomes `SORT_ARRAY(x)`. The Toolbox gives no finding for that today.
- CI runs only the pin, so nothing tests the range above it.

### Compares and the user's params (2026-11-24, 8.9 at 478606c0)

How step 7 of the convert Workflow compares, `project.compare_batch` (cell 22 of
`admin/workflows/convert/convert.ipynb`): it never runs the original script nor the converted
Statements. Both tables are already written by step 6, so it reads `SELECT <columns> FROM
<dev table>` against the original's table through the user's `query`, matches rows on every
column (`comparisons.compare_with_original`), and writes `conversion/compare.md`. A partitioned
table is compared on the latest Partition both hold, plus each one in `PARTITIONS`.

- **When the original is a table**, its params don't reach the compare. An open Script tag is
  a Decision, so the run stops at step 2 before the dev table exists. A tag answered with a
  value the original's last run didn't use makes the latest Partition differ, and the compare
  fails without saying why.
- **When the original is a query alone** (`_original_of` gives None), `_compare_one`
  (`project.py`, around line 6708) sends `conversion/statement.hql` as the original, exactly as
  the script wrote it:
  - a bare `<PARM="X"/>` can't be read, since `compare_with_original` parses without
    `readable_tags` (only `compare_hive` uses it), and the result is "couldn't compare:
    compare_with_original: sqlglot can't read the original as Hive: ...";
  - a quoted `'<PARM="X"/>'` reaches the warehouse as text, so the rows differ;
  - `${hivevar:x}` goes through unfilled, since `with_hivevar_values` fills only the
    Statement side's Hivevars and no `SET hivevar` is sent;
  - a Run value is never applied to the original.

  Either way the compare is Failed, the batch stays out of `finished/`, and promote refuses it.
- Tests today: `tests/test_compare_step.py` (a table compared whole, a query alone, whatever
  stops a compare is its result), `tests/test_hivevars.py` (only the Statement side's Hivevars
  are filled), `tests/test_script_tags.py` (`compare_hive` reads a bare tag). None covers
  `compare_batch` on a query alone holding a tag or Hivevar.

### Table references in the Workflows (2026-11-24, 8.9 at 478606c0)

A Table reference is `references/<db>__<table>.py`, added by `project.add_references` (step 1
of the references Workflow), which DESCRIBEs the table and proposes a Key; the Reference sheet
is rebuilt by its step 4.

| Where | Today |
|---|---|
| convert | adds them for you: `_write_missing_references` DESCRIBEs each table read with no reference, and a workbook's sources come from its rows. A DESCRIBE that fails skips that table, and each table reading it ("it reads X, which has no Table reference") |
| new_table with QUERIES | refuses: "{table}'s query reads {X}, which has no Table reference." and "Add it first with the references Workflow" |
| new_table from a Template | no refusal of its own; the user writes the imports |
| `project.new_run_value(latest_partition=...)` | refuses: "{name} has no Table reference, ..., so nothing was written." |
| the sources Decision (`write_decisions`) | refuses: "sources: {given} has no Table reference: add it first, with project.add_references(...)" |
| promote | reads only dev tables; one without a reference is refused, rightly |
| schedule | reads no outside table |

### Aggregate or historical, and a historical table's first load (2026-11-24, 8.9 at 478606c0)

The user: "ask about initial loading of historical results to emphasize if a table is supposed
to be an aggregate table or a historical table. Historical tables need initial loads to make
them viable."

- **Aggregate**: each write replaces the whole table (an INSERT OVERWRITE with no Partition,
  or one that rewrites every Partition). It needs no first load: its first write is already
  complete.
- **Historical**: each write adds or replaces one Partition, such as the run's date, and what
  reads it expects the past ones to be there. A new copy holds only the Partitions written
  since its first run, so the history is short until it is loaded.

What the Toolbox does today:

- The Seed (glossary) is the only first load. A Conversion writes `seed()` into a Table
  notebook only when `converting.reads_itself` finds the write reading its own table, as an
  incremental INSERT does (`project.py` around line 4136, `converting.with_seed`). It copies
  the original's Partitions, limited by the SEED Decision.
- A historical table whose write doesn't read itself, such as `INSERT OVERWRITE ... PARTITION
  (dt = <run date>)` from source tables, gets no seed. Its dev and prod copies start with one
  Partition. Its compare still passes, since that compare reads only the latest Partition and
  each one in `PARTITIONS`, so nothing tells the user the history is missing.
- A table made with `new_table` has no original to copy, so a first load there would mean
  running its write once for each past Partition (a Run value over a range), not a copy. No
  Workflow does that today.
- Nothing asks which kind a table is. The glossary has no term for either kind yet, and it
  lists "backfill, preload, bootstrap" under the Seed's _Avoid_, so "initial load" needs a
  glossary decision too: either the Seed widens to cover it, or it gets a term of its own.

A proposal the user accepts, as 8.5's are, could come from the Hive itself: a partitioned table
whose write names one Partition is proposed historical, and one rewritten whole is proposed
aggregate.

### The version

8.10 follows 8.9. `upgrades.version_numbers` compares versions as numbers, so 8.10 sorts after
8.9 there, and no version is compared as text elsewhere in the Toolbox, `tools/` or the tests
(checked 2026-11-24). Its change notes go under `## 8.10` in `CHANGES.md`, in the shape of
8.9's (a line on what's new, `### To update from 8.9`, `### What's new`, `### Fixed`). Like
every raise it needs a `to_8_10` Upgrade step in `STEPS`, even one with nothing to change, and
the Example projects frozen as 8.9 left them in `tests/upgrade_from/8.9/`.

## Tickets

None yet: written once the questions below are settled.

## Not yet specified

Each is the user's decision.

1. **SORT_ARRAY on newer sqlglot.** Make the Toolbox read both shapes (`SortArray` up to
   30.23, `ArraySort` with `asc` from 30.24) and add a CI job at a sqlglot from 30.24 on; or
   cap the range below 30.24 for now. And whether an `ARRAY_SORT(x)` that becomes
   `SORT_ARRAY(x)` gets a finding about NULLs moving first.
2. **Compares with params.** For a query alone: fill its tags and Hivevars from the answered
   Decisions, Run values and Hivevar defaults before sending it, so the original reads what
   the dev table read; or skip that compare with a plain reason ("it holds `<PARM="X"/>`,
   which only your program fills") and let the batch finish without it; or both, filling where
   every value is known and skipping where one isn't. And whether a table original whose
   latest Partition came from different param values is flagged instead of failing.
3. **References added for you.** Which of `new_table` with QUERIES, `new_run_value` and the
   sources Decision add the missing reference themselves, as convert does, and whether each
   says what it added. What happens when its DESCRIBE fails there.
4. **Aggregate or historical.** Whether it is a new Decision for every table, proposed from the
   Hive, and which Workflows ask it (convert, new_table, or both). For a historical table:
   whether a Conversion seeds it from the original even when its write doesn't read itself;
   how a `new_table` one is loaded (its write run once for each past Partition, and how far
   back); and whether a check warns when a historical table holds fewer Partitions than its
   original. And the names: two glossary terms for the kinds, and whether the first load is
   the Seed widened or a term of its own.
5. **One version or more.** Whether all four fit 8.10, or the SORT_ARRAY fix ships alone.

## Ideas for later

- **First-load ranges proposed from the Statement** (the user, 2026-11-27: "iniital loading can
  automatically populate ranges based on statement and start off with last month, last two
  months, etc"). The Toolbox reads the historical table's partition column and how its write
  fills it, then offers ranges to pick from, counted back from the latest Partition: last
  month, last two months, and so on. The pick becomes the first load's limit (SEED's range
  today). This is a later idea, not part of decision 4.

## Out of scope

- Changing how the convert Workflow writes or runs tables: only its compare step changes.
- Supporting sqlglot 31.
