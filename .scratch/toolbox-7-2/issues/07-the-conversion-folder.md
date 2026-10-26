# The scan, the Conversion folder and finish_conversion

Type: task
Status: resolved
Blocked by: 02, 06
Size: L

## Question

The Project actions a user runs, from the admin folder, to bring one query of someone else's
under their control. The user (2026-10-26): "We'll need to be able to find the tables and scan
if they need to go in to the references and then convert that sql to code. This conversion can
largely exists inside the admin section." The Hive comes pasted or from a file ("I don't think I
can get access to an hql file, so plan for a and b"). "Demand a conversion name which I can
supply"; the table's final name and location are the user's, with "a partition column that fails
if the column doesn't exist so I am reminded to fill it in".

## Done when

- `project.scan_hive(hive=... | file=...)` reports, with line numbers, the tables read and which
  have no Table reference, what converts, what stays Unchecked, each `# CONVERSION:` opt-out, and
  the count ("412 lines, 9 Unchecked expressions, 1 Unchecked derived table"). It writes nothing
  and sends nothing.
- `project.convert("<name>", hive=... | file=..., query=query)` refuses a name that isn't a plain
  lowercase Python name, or one taken; adds the missing Table references through `query`, as
  `add_references` does; and writes `admin/conversions/<name>/`: `original.hql` (the Hive as
  given), `scan.md` (the scan), and `<name>.ipynb` (ticket 06's notebook, with ticket 08's check
  cells). The Registry lists the Conversion folder; the Admin log has the action.
- `project.finish_conversion("<name>", table="<db>.<table>")` makes the Table folder and the
  Saved table's Table reference, its columns from the Statement's output, `location=` a
  placeholder, `partitioned_by=` pre-filled from the original's `PARTITION(...)` or else a
  placeholder; the reference refuses a partition column that isn't one of its columns, naming it
  and saying to fill it in. The notebook's logic moves into the Table notebook; the Conversion
  folder is archived to `admin/removed/`, its Registry row marked finished.
- `project.remove_conversion("<name>")` archives one abandoned, as `remove_table` does.
- `project.start()` makes `admin/conversions/` and `admin/convert.ipynb`: a notebook with a cell
  to paste Hive into, one to name a file instead, then the scan, the Conversion and the finish,
  each commented. Ticket 02's 7.1 → 7.2 step adds both to a 7.1 Project.
- `project.check()` lists each `# CONVERSION:` mark left in the Project, and each Conversion
  folder not yet finished.
- Each Project action is public, typed, with a Worked example opening its docstring.
- CLAUDE.md's Definition of done, the beginner reader included.

## Glossary

New, under "The user's own scripts":

> **Conversion**:
> A Project action that reads one query of Hive someone else wrote and writes the user's own
> code for it, in a Conversion folder: Table references for the tables it reads that have none,
> and a notebook whose Statement gives the same rows. What no Toolbox function writes yet is
> left as Unchecked pieces, and each risk the original took is marked `# CONVERSION:` for the
> user to decide.
> _Avoid_: migration, port, translation, import, upgrade

> **Conversion folder**:
> The folder in a Project's admin folder holding one Conversion until it becomes a Table folder:
> the Hive as given, the scan of it, and the converted notebook with the cells that compare it
> with the original. Finishing it moves its logic into a new Table folder, under the Saved
> table's name the user gives then.
> _Avoid_: staging folder, draft, scratch folder

**Registry** gains Conversion folders in its list. **Project action**'s list gains converting
and finishing a Conversion.

## Answer

Built 2026-10-26 on dev, with 05 and 06.

- `project.scan_hive(hive=... | file=..., database=)`, `project.convert(name, hive | file=,
  query=, database=)`, `project.finish_conversion(name, table=)` and
  `project.remove_conversion(name)`, each a Project action logged in the Admin log (scan_hive
  changes nothing and isn't logged). `database=` names the Database of a table the Hive names
  without one (default `default`, as Hive's).
- The Conversion folder, `admin/conversions/<name>/`: `original.hql` exactly as given (pasted or
  from a file), `scan.md`, and `<name>.ipynb`: what it is, the Project three folders up, the
  logic cell, then compare_hive's cell and compare_with_original's (commented, with a partition
  to fill in). A new `FileKind`, `CONVERSION_FOLDER`, kept out of `KINDS` so register never
  adopts one; the Registry lists it while in force.
- `project.load("<name>")` runs a Conversion's logic as it does a Table notebook's: a name
  with no dot is a Conversion's, which must define `converted()`.
- `finish_conversion` calls `new_table` (so its Admin log has that entry too), then writes the
  Table notebook (the Conversion's logic with create, preview and write; trying it, lineage, the
  checks, the Reference sheet) and the Table reference: the columns from the Statement's
  outputs with the types it knows, `<COLUMN_TYPE>` for the rest, `partitioned_by` from the
  original's PARTITION or `["<PARTITION_COLUMN>"]`, which Table refuses until it names a
  column, `key=None` with a TODO, and `location=<LOCATION>`. `original.hql` is copied into the
  Table folder for the checks; the Conversion folder is archived.
- `project.start()` makes `admin/conversions/` and `admin/convert.ipynb`, so the 7.1 to 7.2
  Upgrade step adds both. `project.check()` lists the Conversions not finished and each
  `# CONVERSION:` mark left.
- Tests: `tests/test_conversions.py`.

## Reviews

Tickets 05, 06 and 07 were reviewed as one change, 6642319 and 1a0ef3d; the fixes are in the
commit after b341cc5's merge of 03 and 08's fixes.

- Standards (2026-10-26): fixed: "translation", which the glossary avoids, is gone from the
  code (`converting.convert_query` gives a `ConvertedQuery`); `_logic`'s dead parameters and
  `_compared`'s unused root are gone; the Conversion notebook's check cells are found by a
  named constant, `_CHECK_CELLS`; plurals by one helper, `_counted`; a Conversion's name told
  from a table's by one, `_names_a_conversion`. Answered: the opt-outs a Conversion adds are
  named in convert's report and scan.md from what `with_opt_out` returns, so the scan's
  findings don't repeat them.
- Spec (2026-10-26): fixed: GROUP BY ... WITH ROLLUP, WITH CUBE, ROLLUP(), CUBE() and GROUPING
  SETS become Subtotals (`rollup`, `cube`, `grouping_sets`) where they were a whole Unchecked
  statement or a crash; a finding says why rollup and cube are written as the GROUPING SETS
  they stand for. Round trips are tested for deep CTEs, a CTE read twice, one table under two
  aliases, `*` and `t.*`, quoted names, comments, mixed case, HAVING, LEFT JOIN, ROWS frames,
  ORDER BY and LIMIT, DISTINCT, UNION ALL and a static PARTITION. A whole-Unchecked
  Conversion is refused plainly by finish_conversion, before it makes any file. A static
  partition column the query doesn't give is listed in the finished Table reference.
  Deviations kept, each recorded in its ticket's Answer: 06 reports a Hive mismatch rather than
  refusing it; each CTE is a module-level Derived table rather than a function; the constants
  sit in the logic cell. `original.hql` is written as given, its line endings as Python reads
  them; compare_hive reads them all alike.
- Beginner reader: [reports/05-07-beginner-reader.md](../reports/05-07-beginner-reader.md),
  stop by stop:
  - 1 (the first cell): fixed, convert.ipynb names the `HIVE` cell.
  - 2 (no database=): fixed, convert.ipynb has a `DATABASE` line that its scan and convert
    pass; how-to "Convert someone else's Hive" says what it is for.
  - 3 (findings out of order, CASE a line late, SET lines twice): fixed, in line order, CASE
    at its CASE, one finding for all the SET lines, INSERT at its INSERT.
  - 4 ("adds it" for three): fixed.
  - 5 (`t.*` crash): fixed, a `*` of a table with no Table reference is `*all_columns(t)`, and
    no reading error escapes as a traceback.
  - 6 (SET lines not compared): fixed by 08's fix, compare_hive passes over SET lines.
  - 7 (HIVE_SETTINGS unsent): answered, run_tables takes no Session settings in what write()
    gives, so write()'s docstring says to send `session_settings()` first.
  - 8 (how to decide a mark): fixed, check() says to keep the opt-out or give the Table
    reference what the Guard needs, such as key=; convert names each opt-out it added.
  - 9 (cell numbers): answered, cells are counted from 1 as Jupyter shows them, markdown too.
  - 10 (row compare with a static partition): fixed, the hint compares on a partition column
    the query gives, else with reads_all_partitions=True; 08's fix lets partition= name a
    partition column of a table read.
  - 11 (`*` expanded): fixed, a finding says the `*` became its columns.
  - 12 (`${hivevar:...}`): fixed, a "variable" finding says your query must put its value in.
  - 13 (DISTRIBUTE BY dropped, compare cut short): fixed, a "dropped" finding each, and
    compare_hive's whole verdict is kept.
  - 14 ("1 lines", "1 piece stay"): fixed.
  - 15 (LATERAL VIEW, CAST, IN (subquery) findings): fixed, every table read is listed, and
    each finding says its reason once.
  - 16 (whole-Unchecked finish): fixed, refused before anything is made.
  - 17 (finish under the Saved table's database): fixed, reading the original again no longer
    needs every table's columns, so the database doesn't matter there.
  - 18 (partition column not a column): fixed, it is listed as a string column.
  - 19 (fill in partitioned_by, already filled): fixed, asked only when it isn't.
  - 20 ("kept in admin/removed/"): fixed, "archived, kept as it was, in".
  - 21 (the day hard-coded): answered, the Conversion keeps the original's days; making one a
    parameter is the user's step, as in how-to "Save a table".
