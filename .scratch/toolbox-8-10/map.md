# Toolbox 8.10: SORT_ARRAY on newer sqlglot, compares that never stop you, Table references added for you, and History tables seeded

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

## Settled (grilling, 2026-11-27)

Round 1, the user's answers:

1. **SORT_ARRAY**: read both sqlglot shapes, with a CI job at a newer sqlglot, "if it's just
   one function call affected". Only `Converter.leave_out_sort_arrays_true` reads
   `exp.SortArray` (plus `Finding`'s docstring and `trees.py`'s arity table, which names
   `sort_array` by text); the suite run on 30.34.0 measures the rest.
2. **No finding of the Toolbox's own** for `ARRAY_SORT` becoming `SORT_ARRAY` (NULLs moving
   first, a comparator dropped): "only plan for sqlglot", its change alone.
3. **A compare of a query alone with params**: fill where every value is known (answered
   Script tags, Hivevar defaults, and each Run value as recorded when the dev table was
   written, never called again); skip with a plain reason where one isn't.
4. **A skipped compare doesn't block**: `compare.md` lists it as not compared, with why, and
   promote names each table it promotes uncompared.
5. **A table original that differs by its answered tags stays a fail**, with a hint in
   `compare.md`, and blocks no next step. The user: "I can't/won't be trying to version slect
   statement snapshots on timestamps."
6. **Every Workflow that needs a Table reference adds it**, as convert does, saying what it
   added. The user: "I want every step to be automatic if it's supported and expected
   behavior."
7. **Rebuilt table and History table** (CONTEXT.md), by what a write does to the rows already
   there, not by what its query computes.
8. **Seed widened** (CONTEXT.md): a History table's one-time load of past rows, copied from its
   Original or written by its own write for each past Partition, with a limit. The user: "if we
   could infer what the date partition is, load the last month, two months, or four months,
   or some other single param a user could fill in. My data environment is intensly
   fractured with drop, create pairs, no pairs, assumptions about different tables
   existing... I want to be able to have a historical table that is usable from day one by
   loading in relevant data from a subset of all available partitions." So the "Ideas for
   later" item is in scope now.
9. **The kind is a Decision for every table** convert and `new_table` write, proposed from
   the Hive, accepted as 8.5's proposals are.

Round 2, the user's answers:

1. **No compare result blocks anything**, a plain fail included; each failed or skipped table
   is named in obvious language, in `compare.md` and when promote runs. The user: "I check the
   data day to day while in dev, so a promote to prod is not a Toolbox call, it's mine. I
   can't encode every things that could be explaining failure differences, especially in
   records loaded in different times, so note the warnings in obvious language, but don't stop
   the user." This widens round 1's answers 4 and 5.
2. **The Seed limit's single value**: `"seed": {"months": N}` in the decisions cell, for one
   table or under `all_tables`, counted back from the newest Partition the source holds, not
   today; proposed as 1. The value, range and list forms stay.
3. **The date partition**: the user asked whether DESCRIBE gives the partition information
   programmatically. It does: the Toolbox already reads DESCRIBE's "# Partition Information"
   rows for each partition column and its type (`describe.py`), and SHOW PARTITIONS for the
   values (`run_values.latest_partition`), both through the user's `query`. Round 3 confirms
   the rule.
4. **A Seed with nothing to copy from** runs its write once for each past date, oldest first,
   with that date as the Run value. The user: "whatever gets the partititons to come out
   nicely in the expected file structure": each run writes the one Partition folder
   (`dt=2026-11-27/`) a scheduled write writes, so the Seed's folders are the ones every later
   write adds to.
5. **A Seed's failed Partition doesn't stop it**: it carries on and lists each Partition not
   loaded with the warehouse's error, and `check_project` warns while a History table lacks
   Partitions its Seed limit named.
6. **The kind is proposed by the write**: DROP then CREATE and INSERT, or `INSERT OVERWRITE
   TABLE` with no PARTITION, is Rebuilt; `INSERT OVERWRITE ... PARTITION (dt = <value>)` or
   `INSERT INTO` is History; a dynamic `PARTITION (dt)` overwrite gets no proposal.
7. **One version, 8.10, for all of it.**

And on sqlglot: "can we just infer what version of sqlglot is imported and run smallish if
statements where it matters?" Yes, by asking sqlglot for what it has (`exp.SortArray` there or
not), not by its version number; round 3 has where.

What supporting both costs, measured 2026-11-27 on a copy of 2224948b (not a git checkout, so
the tests that need git are left out by comparing against the same copy on 30.23.0):

- **Unpatched on 30.34.0**: 420 more tests fail than on 30.23.0, nearly all with "module
  'sqlglot.expressions' has no attribute 'SortArray'".
- **With one line changed** (`leave_out_sort_arrays_true` finding `ArraySort` when `SortArray`
  is gone, and a `FALSE` kept as text): 35 left, every one about SORT_ARRAY, plus the
  Toolbox's own "Note: sqlglot 30.34.0 is newer than any version sqlglot Composer was tested
  on" (`engine.py`), which two tests see in their output. Nothing else in the Toolbox breaks on
  30.34.0.
- **What the 35 need**, each a small branch on whether sqlglot has `exp.SortArray`:
  1. `leave_out_sort_arrays_true` finds `ArraySort` on 30.24+, where Hive's `SORT_ARRAY(x)`
     reads as `asc` None and `nulls_first` TRUE, and `SORT_ARRAY(x, TRUE)` as `asc` TRUE.
  2. A `FALSE` kept as written: 30.24+ refuses to write it ("Hive's SORT_ARRAY only sorts
     ascending with NULLs first", raised since the Toolbox writes Hive with
     `ErrorLevel.RAISE`), so it is written as text, as 30.23 writes it.
  3. The Python a Conversion writes for the node leaves out `nulls_first`, so no `True`
     appears in `hive_function("sort_array", ...)`.
  4. `hive_function("sort_array", x, False)` (`trees.py`) writes on both.
- **Spark's `ARRAY_SORT(x)`**: 30.23 writes `SORT_ARRAY(x)`; 30.24+ refuses it, as NULLs last
  can't be written in Hive. Read as Hive, both write `SORT_ARRAY(x)`.
- `engine.py` already checks sqlglot's behaviour when the Toolbox is imported and holds
  `_NEWEST_TESTED`, so it is where "which shape" is answered once.

Round 3, the user: "all your recommendations".

1. **`SORT_ARRAY(x, FALSE)` on 30.24+** is written as text, so both sqlglot versions give
   `SORT_ARRAY(x, FALSE)` and 8.7's finding.
2. **Spark's `ARRAY_SORT(x)` on 30.24+** gives `SORT_ARRAY(x)` as on 30.23, with sqlglot's own
   sentence ("Hive's SORT_ARRAY only sorts ascending with NULLs first") kept as its finding.
3. **"Which shape"** is answered once, in `engine.py`, and the four places ask it. The pin stays
   30.23.0; a second CI job runs at 30.34.0, and `_NEWEST_TESTED` rises to 30.34.0.
4. **A date partition** is one whose every SHOW PARTITIONS value reads as a date (`2026-11-27`
   or `20261127`). "N months" counts calendar months back from the newest Partition, both ends
   included; values keep their written form in the Seed's WHERE.
5. **A per-date Seed runs the write as of each past day**: that day goes wherever the write
   reads today (`current_date`, or a Run value for today), so a write that targets yesterday
   is run as of the day after. Only the run's today changes, never the logic.
6. **A Seed day with no rows** keeps its empty Partition, is listed as "no rows" in the Seed's
   report, and counts as missing in `check_project`'s Warning.
7. **A Seed runs on its own**, first, in whichever step writes the table (convert's write step,
   `new_table`'s, promote's), whenever a History table holds no Partitions yet; no cell sends
   it by hand, and a rerun never loads twice.
8. **Prod's Seed** copies from the Original when there is one; a History table with none copies
   from its dev table, the days the user has checked.
9. **`to_8_10`** proposes each existing table's kind from its Hive and writes it in as answered,
   keeps every `seed()` and SEED as they are, and runs no Seed: those tables already hold
   Partitions.

Round 4, the user: "all your recommendations".

1. **A History table with no Partitions** (an `INSERT INTO` append) is copied whole from its
   Original; with none, `"seed": {"months": N}` counts back from today, the one case that
   does, and runs the write as of each day. Its Seed runs only while it holds no rows.
2. **Docs**: a new how-to 34, "Load a History table's past days" (the kind Decision,
   `"seed": {"months": N}`, the Seed's report), a pointer from how-tos 06 and 09, a line on the
   kind Decision in Copilot files 06 and 07 (each kept under 9,000 characters), and `## 8.10`
   in `CHANGES.md`.
3. **Example projects**: every table gets its kind (as `to_8_10` writes it), and one daily table
   of the intermediate project shows `"seed": {"months": 1}` for how-to 34. No new tables.
4. **Tickets in this order**: SORT_ARRAY on both shapes and its CI job; Table references added;
   compares; Rebuilt and History tables; the Seed widened; `check_project`'s Warning; docs and
   Example projects; the version.
5. **Usability**: one dev scenario after the docs ticket (a converter whose batch holds a
   History table whose date Hive computes), then the held-out scenario once before the export,
   each only on the user's yes.

Every branch is settled; the tickets wait on the user's confirming the plan below.

## Tickets

Written 2026-11-27, once the user confirmed the plan ("Yes, write the tickets").

- [01 SORT_ARRAY on both sqlglot shapes, and a CI job at 30.34.0](issues/01-sort-array-on-both-sqlglots.md)
- [02 Table references added for you](issues/02-references-added-for-you.md)
- [03 Compares that fill the user's params, and never stop the user](issues/03-compares-that-never-stop-you.md)
- [04 Rebuilt or History: each table's kind, a Decision proposed from its write](issues/04-rebuilt-or-history.md)
- [05 The Seed widened: a History table usable from its first day](issues/05-the-seed-widened.md)
- [06 check_project warns while a History table lacks its Seed's days](issues/06-check-project-warns-of-missing-days.md)
- [07 The docs and the Example projects](issues/07-the-docs-and-example-projects.md)
- [08 8.10: the Upgrade step and the raise](issues/08-eight-point-ten.md)

One at a time, by number, the user's habit; 01 first, since anyone on sqlglot 30.24.0 or newer
is broken today. 01 to 04 block nothing of each other; 05 waits on 04, 06 on 05, 07 on 01 to
06, and 08 on all. The real dependencies are in each ticket's `Blocked by:`.

## Not yet specified

Each is the user's decision. All five are settled above (rounds 1 to 4, 2026-11-27); the list
is kept as it was asked.

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
  today). In scope since round 1's answer 8.

## Out of scope

- Changing how the convert Workflow writes or runs tables: only its compare step changes.
- Supporting sqlglot 31.
