# The Workbook check

Type: task
Status: resolved
Blocked by: 07
Size: L

## Question

The check of a Formula workbook's Hive against the workbook's own numbers, offline (round 1,
Q9; round 2, Q7; round 3, Q5; CONTEXT.md's Workbook check).

## Done when

- **A new Toolbox file**, in the registry's `LIBRARY_FILES`, runs each final's Hive on sqlglot's
  executor, each `<database>.<table>` standing in for the workbook's typed rows of that Table,
  and compares its rows with the values Excel last stored: a Table's cells, a Total Row's, a
  pivot's.
- **A match**: numbers within a relative 1e-9 on stored values; a blank matches NULL only where
  file 11's M1 marks it; rows matched on the final's Key or its GROUP BY, in any order.
- **A difference** is one line a cell in the convert notebook ("Region East, Mar: Excel 1,204,
  Hive 1,198"), and blocks nothing. A piece the executor can't run is named, with why.
- **It never reads the warehouse** and never calls `query`.
- **The Copilot path**: a batch of `.hql` files with the workbook beside them checks each `.hql`
  whose name is a final's.
- Tests: a match and a difference for each kind of final; an `.hql` from Copilot checked; the
  offline trap holds.

## Answer

Built 2026-11-19. **No new public name**: the check runs at the end of `project.convert` of a
batch holding a workbook, and the person reads it in convert's report and in batch.md.

**Two new Toolbox files**, both in the registry's `PYTHON_FILES` and `LIBRARY_FILES`, and in
standards.md's list of files that may name sqlglot's types:

- `sqlglot_composer/hive_executor.py`: Hive run on sqlglot's executor over rows held in memory,
  `run_on_executor(tree, schema, rows, functions) -> (columns, rows)`. This is the Example
  database's machinery moved into the Toolbox without changes ("one way per job"): GROUPING
  SETS and ROLLUP, window functions, a group's column beside an aggregate, escaped LIKE, CASE
  on one column, CAST to text, stacked reads told apart, and joined tables kept apart. Where
  the Example database refused, it now raises `MissingPart(missing)` for a part it can't run,
  and `NtileWithNoParts(parts)` for NTILE below 1. `executor_counts_right()` is the
  COUNT(DISTINCT) check. `HIVE_DAYS` holds date_add and next_day, which the executor is now
  taught only while it runs (`_functions_taught`); they used to stay in sqlglot's ENV for good.
  A table made while a window is worked out goes in its own database, `made_by_the_executor`,
  not `ops`. Every `dialect=` goes through three new functions in `writing.py`
  (`qualified_hive`, `optimized_hive`, `executed_hive`), as the escaping test requires.
  `example_database/executor.py` now holds only its tables, its refusals and `run_query`. Its
  messages are unchanged, and no snapshot hash moved.
- `sqlglot_composer/workbook_check.py`: `check_workbook(workbook, file, finals, database) ->
  WorkbookCheck`. Each `FinalHive(final, table, hive, script="")` gives a `CheckedFinal`
  (`compared`, `differences`, `unstored`, `not_checked`). Also `report_lines(check)`,
  `batch_md_lines(check)` and `is_same(excel, hive, blank_marked)`.

**What it does.** A final's Hive reads tables as `<database>.<table>`, or bare in convert's
`database`. Each one stands for the workbook's Table of that name, or for a plain range's rows,
found by the table name PS3 proposes for the range. The rows hold each column's stored values,
with a day as its text. CTEs are left alone. A table the workbook has no Table for is named:
"it reads ops.job_events, which is no Table of the workbook, so the workbook holds no rows to
run it over". The rows are then compared with what Excel stored:

- a **Table** final (formula columns over its own rows, a summary Table, or a query's Table):
  rows are matched on the Keys sheet's Key, else on the final's GROUP BY outputs, else on its
  typed columns, else on every column, in any order. Each cell of a matched row is compared,
  and a row found on one side only is its own line;
- a **Total Row** (`<Table> (Total Row)`): each formula total's stored value is compared with
  the final's one row;
- a **pivot** and **each total level**: each stored cell is compared with the row of its
  level's final that holds its items, in its value's column (or a calculated item's own
  column). A column the pivot needs that the Hive doesn't give is said once. A row of a level
  that no cell stands for is its own line.

**A match**: numbers within a relative 1e-9 (and within 1e-12 of zero, as in ticket 06's
`is_same`), on stored values; a day matched as its date; blank matches NULL; an Excel error
(#DIV/0!, #REF!, ...) counts as NULL, as ticket 10 treats GETPIVOTDATA's #REF!. **How M1 is
read here:** Excel's 0 or "" (or a blank) matches Hive's NULL (or 0 or "") only in a formula
column that the code path's M1 marks; anywhere else it is a difference. If the grilling meant
something else, say so.

**The reader** (`workbook_reader.py`) gains `Column.stored` and `Column.total_stored`: the value
Excel last stored in each cell. A formula's result comes from its `<v>`: "" for an empty text,
None where the file holds no result. `Sheet.results` holds the result of each formula cell on
the sheet, which a range's rows read. openpyxl, and so the dev tool, stores no formula results.
Such a column is named rather than compared: "not compared: hours, as the workbook holds no
value Excel stored for them: a file saved by a tool, not by Excel, holds none. Open it in
Excel, save it, and convert again to compare them."

**What the executor can't run, and how that is reported.** While it runs, the check also
teaches it these Hive functions, beside the day functions: to_date (YEAR, MONTH and DAY read
through it), date_format, quarter, stddev_samp, stddev_pop and var_pop. The Example database's
limits are unchanged. Anything else the executor lacks is named, never guessed at: "pivot, from
PivotTable1: not checked: its Hive uses FLOOR, which the small executor the check runs on
hasn't got. Compare it with the workbook by hand." The same goes for Hive sqlglot can't read, a
script of more than one statement, NTILE of no parts, and any other error that stops the
executor (its first line is shown). VARIANCE stays a named failure, because sqlglot reads
Hive's population VARIANCE and VAR_SAMP as the same thing.

**The report text.** In convert's report the check comes after the other lines and before
"Next:". batch.md gets the same text under "## The Workbook check of runs.xlsx", with each
difference as an item under its final. A real run, with a Copilot `.hql` whose filter keeps
SUCCESS alone:

    The Workbook check of runs.xlsx: each final's Hive run on this computer over the workbook's
    own Tables, and its rows compared with the values Excel last stored. The workbook's rows are
    an old sample, so the warehouse's rows will differ from them: this compares the Hive with
    the workbook alone, never with the warehouse, and a difference stops nothing.
    pivot.hql, Copilot's Hive of PivotTable1: 2 differences from the workbook (3 cells compared):
      job_id 2: Excel 38, Hive 18
      job_id 3: Excel 60, Hive 30
    runs_by_day, from runs_by_day: matches the workbook, 2 cells compared.
    pivot_grand_total, from PivotTable1 (grand total): matches the workbook, 1 cell compared.
    runs_by_day_grand_total, from runs_by_day (grand total): matches the workbook, 1 cell compared.
    For each difference, check the final's Hive, in its table's logic cell, against the
    workbook's formula, query or PivotTable; a rule's mark in its checklist may explain it.
    Convert again after a change to check again.

A repeated line, such as one for each extra row of a level, is said once with "(8 times)". A
workbook with no converted finals gets no check, since the report already says why each final
was skipped.

**What a beginner sees.** The report text above, the batch.md section, and the end of
`project.convert`'s workbook paragraph in its docstring. The convert notebook's text is
unchanged. Ticket 15 (the docs) could add a sentence there, but that would regenerate every
convert notebook.

**In project.py**, the new code is in functions of its own: `_workbook_checks` (a Copilot
script that stands for a final is checked in the final's place, and the workbook is read again
from where the batch names it), `_with_workbook_checks`, and `_BatchFiles.workbook_checks`, plus
one line each in `_convert_batch` and `_write_batch_index`. Nothing changed in `decisions.py`,
`workbook_conversion.py`, `workflows.py` or `copilot/`.

**It never reads the warehouse.** It takes no query. A test converts with a query that records
every call, and every call is a DESCRIBE. The offline trap runs under every test.

**Found by the check, for the lead:** fixture 10's `PivotTable2 (grand total)` Hive (rank
Show Values As, PV8) is `SELECT NULL AS sum_of_duration_mins FROM ops.job_runs`. With no
aggregate and no GROUP BY, it gives one row per row of job_runs (9 rows), where the pivot shows
one blank cell. Ticket 06's own row test reads only the first row, so it never saw this. It is
left as it is, because it is ticket 06's and file 20's Hive and also ticket 10's references; a
test holds that the check names it. The fix would be to make it one row, for example with a
GROUP BY of nothing or no FROM.

**Tests:** `tests/test_workbook_check.py` (25 tests):
- the reader's stored values;
- a match and a difference for a Table's formula columns (on the Keys sheet's Key), a query's
  Table, a Total Row, a pivot and a total level;
- pivot fixtures 05, 07, 08 and 09 each match;
- an unstored column is named, and a missing value column is said once;
- fixture 10's extra level rows are named;
- FLOOR is named, and so is a table outside the workbook;
- the match rules;
- convert's report and batch.md;
- a Copilot `.hql` beside its workbook, both matching and differing, blocking nothing;
- query is never called.

`tests/test_workbook_reader.py`'s Column comparisons now include the new fields, and
`tests/workers.py` groups the module's workbooks. `tests/snapshot/known.txt` has 25 new hashes.
The convert tests' report hashes from before the check are left for the lead.

**Left.** The code-review skill and the beginner reader haven't run (the lead runs them). The
report's text is new to a beginner.
