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

**Two new Toolbox files**, though the ticket said one. Both are in the registry's
`PYTHON_FILES` and `LIBRARY_FILES`, and in standards.md's list of files that may name sqlglot's
types. The second is the Example database's executor, moved into the Toolbox whole, so that
running Hive on sqlglot's executor is done in one place (one way per job). The lead kept both
files and amended ADR 0016's Consequences (ad941a7b):

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

**A match**: numbers within a relative 1e-9, on stored values, with a floor of 1e-12 at zero,
as in ticket 06's `is_same`, where a relative test can't hold (the lead's call: it stays); a day
matched as its date; blank matches NULL. **An Excel error** (#DIV/0!, #REF!, ...) where Hive
gives NULL compares as NULL but is not silent: each such cell is listed under its final, "job_id
1, dt 2026-09-23: the workbook shows #REF!, and the Hive gives NULL", and counted apart from
matches and differences (the lead's call). Against a Hive value, it is a difference. **The
check's reading of M1** (the lead's call: keep it): Excel's 0 or "" (or a blank) matches Hive's
NULL (or 0 or "") only in a formula column that the code path's M1 marks; anywhere else it is a
difference.

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
limits are unchanged. Anything else the executor lacks is named, never guessed at: "mart_dev.pivot, from
PivotTable "PivotTable1": not checked: the check can't run FLOOR on this computer. ..." The same goes for Hive sqlglot can't read, a
script of more than one statement, NTILE of no parts, and any other error that stops the
executor (its first line is shown). VARIANCE stays a named failure, because sqlglot reads
Hive's population VARIANCE and VAR_SAMP as the same thing.

**The report text.** In convert's report, `_batch_report` puts the check after the line
naming batch.md and before "Next:". batch.md gets the same text under "## The Workbook check of
runs.xlsx", starting "It ran ...", with each difference as an item under its final. A real
run, with a Copilot `.hql` whose filter keeps SUCCESS alone:

    The Workbook check of runs.xlsx ran the Hive of each table the workbook gave, on this
    computer, over the workbook's own Tables, and compared its rows with the values the
    workbook shows, as last saved. A difference means the Hive doesn't give what the workbook's
    formula, query or PivotTable gave on the same rows: look at each one, though none stops
    anything. The workbook's rows are an old sample, so the warehouse's rows will differ from
    them: this compares the Hive with the workbook alone, never with the warehouse.
    pivot.hql, Copilot's Hive of PivotTable "PivotTable1": 1 of 3 cells match the workbook;
    below, 2 differences:
      job_id 2: Excel 38, Hive 18
      job_id 3: Excel 60, Hive 30
    mart_dev.runs_by_day, from PivotTable "runs_by_day": every cell matches the workbook, 2
    cells compared.
    mart_dev.pivot_grand_total, from PivotTable "PivotTable1" (grand total): every cell matches
    the workbook, 1 cell compared.
    For each difference, compare the table's Hive, in the `# logic` cell of its notebook, with
    the workbook's formula, query or PivotTable; the rule its checklist names may explain it.
    Convert again after a change to check again.

When a level's Hive gives one set of items several times, the rows are said once: "Grand
Total: the Hive gives 9 rows where the PivotTable shows one: fix the Hive, in the `# logic`
cell of its table's notebook". A final the check can't run reads "not checked: the check can't
run FLOOR on this computer. To compare it by hand, run its table's preview() on your warehouse
and look for the same rows in the workbook, though the warehouse's rows may have moved on." A
workbook with no converted finals gets no check, since the report already says why each final
was skipped. The Review below lists every wording the beginner reader changed.

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

**Tests:** `tests/test_workbook_check.py` (26 tests):
- the reader's stored values;
- a match and a difference for a Table's formula columns (on the Keys sheet's Key), a query's
  Table, a Total Row, a pivot and a total level;
- pivot fixtures 05, 07, 08 and 09 each match;
- an unstored column is named, and a missing value column is said once;
- fixture 10's extra level rows are named;
- an Excel error is listed apart;
- FLOOR is named, and so is a table outside the workbook;
- the match rules;
- convert's report and batch.md;
- a Copilot `.hql` beside its workbook, both matching and differing, blocking nothing;
- query is never called.

`tests/test_workbook_reader.py`'s Column comparisons now include the new fields, and
`tests/workers.py` groups the module's workbooks. `tests/snapshot/known.txt` is dev's, plus
this ticket's hashes (57 after the review), with none of its own left stale. The convert tests'
report hashes from before the check are left for the lead.

## Review

The code-review skill, the beginner reader and the lead's calls (2026-11-19), all answered in
`fix(8.9): ticket 09's review: ...`, after a rebase onto dev's ad941a7b (tickets 07, 11 and
17).

**The lead's calls.**

1. **Two Toolbox files stay.** The Answer now says why: the executor moved whole, one way per
   job. The lead amended ADR 0016's Consequences (ad941a7b).
2. **Blank and NULL as read here stay**, as the check's reading of M1. The Answer and the
   module docstring say so.
3. **An Excel error is no longer silently NULL.** It still compares as NULL, but each such
   cell is listed under its final ("job_id 1, dt 2026-09-23: the workbook shows #REF!, and the
   Hive gives NULL") in `CheckedFinal.errors`. These cells are counted apart from matches and
   differences: "5 of 6 cells match the workbook; below, 0 differences and 1 cell where the
   workbook shows an Excel error and the Hive gives NULL, neither a match nor a difference:".
   All three comparisons go through one helper, `_compare_cell`.
4. **The 1e-12 floor at zero stays**, and the Answer and module docstring say so.

**Standards.**

5. **One way per job.**
   - `tests/sqlglot_checks/test_sqlglot_workbook_pivot_hive.py`'s `is_same`, `cell_value` and
     the old `cells_differing` are gone. `cells_differing` now runs `check_workbook` over the
     workbook's own Tables and lists each difference, each Excel error and each final not
     checked. Its one-cell test reads in the check's words ("PivotTable1: job_id 1, dt
     2026-09-23: Excel 18, Hive 17"). PV8's one-row total level, which ticket 13 fixes, is left
     out there by `PV8_BEFORE_TICKET_13`, with a note to take it out once ticket 13 lands; the
     check's own test still names it.
   - **`tests/test_excel_eval.py`'s stored-values test is kept, for the lead to decide.** It
     holds each task's reference Hive to the evaluation scorer's own rules: columns by place,
     since a reference names its columns freely, and numbers to six places. The check matches
     by name, so it can't stand in. Run over the 40 pivot tasks' references, `check_workbook`
     names a missing value column on most of them (`sum_of_duration_mins`, the code path's
     name). It can't run X87's VAR_SAMP or X90's CAST, and X97 and X105 read tables their
     workbooks don't hold. Using it there would mean rewriting the references to the code
     path's names, which is ticket 13's or 14's work. Say if you want that.
   - **`is_formula`.** The reader's `_is_formula` is public now, and the only one:
     `workbook_formulas.is_formula_text`, a third copy, is gone. Its five uses, the pivot
     Hive's one use and the check all call `workbook_reader.is_formula`.
   - **Other names.** `sqlglot_reason` is gone; the check imports `reason_without_place` by its
     own name. `_as_held` is now `_hive_value`, "a value the workbook saved, as Hive holds it".
     `_place_of`, a name `stacking.py` has too, is now `_workbook_name_of`.
6. **`_workbook_checks` and the report.**
   - The `id(final)` maps are gone from project.py. `BatchWorkbooks.finals_to_check(workbook,
     texts, dev)` gives the `FinalHive` list, using `copilot_script_of(final)`.
   - The splice is gone too. `_batch_report` places `_workbook_check_lines(files.workbook_checks)`
     after the batch.md line and before "Next:", and its docstring says so. `report_lines`
     returns only the check's own lines.
   - The reporting stays in `workbook_check.py`, as its last group of functions; a file of its
     own didn't read plainer.

**The beginner reader** ([its report](../reports/beginner-reader-2026-11-19-ticket-09.md)), each
a fix:

7. `ABOUT` is now a sentence with a verb, says "each table the workbook gave" instead of
   "final", and says what a difference means and that it is the person's to look at.
8. Each name is marked: the Saved table by its full name (`mart_dev.pivot`), and the
   workbook's piece as the texts name it (`PivotTable "PivotTable1"`, `Excel Table
   "job_runs"`, `the Total Row of Excel Table "job_runs"`). `FinalHive.table` is now the full
   name.
9. A row the pivot doesn't show says which side is wrong and what to do: "the Hive gives 9
   rows where the PivotTable shows one: fix the Hive, in the `# logic` cell of its table's
   notebook" (`_rows_not_shown`). A Table's extra or missing rows say so too.
10. "not checked: the check can't run FLOOR on this computer. To compare it by hand, run its
   table's preview() on your warehouse and look for the same rows in the workbook, though the
   warehouse's rows may have moved on."
11. `NEXT` now names "the `# logic` cell of its notebook" and "the rule its checklist names".
12. "the values the workbook shows, as last saved" everywhere a person reads it.
   `project.convert`'s docstring says "list each cell where the two differ, each on a line of
   its own; a difference stops nothing, but is yours to look at."

**Tests after the review:** 5,537 passed, 3 skipped, across every file the change touches (the
new tests, the convert and workbook tests, `tests/sqlglot_checks`, `tests/repo/`, docstrings,
the import self-check, the Excel eval and the Example database's).

**Left.** The code-review skill's sub-agents' runs are the lead's to record in the ledger.

## Follow-up

After ticket 08 (2026-11-19): a table whose Pivot filter is answered "fold", "batch" or
"tables" was rewritten from the Hive it was converted from, so its rows are no longer the
PivotTable's selection. When a convert runs again, the check still runs the Hive the table was
converted from (the workbook's own, or Copilot's script), never the one the answers wrote, and
now says so in a line under the final's own:

    mart_dev.pivot: checked as converted, before its Pivot filter's answer "fold"; the table
    now holds every status.

"batch" says "the table now holds every status, a Partition per status, each run writing
one"; "tables", on the first table per value, which keeps the workbook's final, "the table now
holds status FAILED alone". Two filters answered read "its Pivot filters' answers "fold" on
status and "tables" on dt". Each table per value made beside the first stands for no final of
the workbook, so it is not checked, and a line says why:

    mart_dev.pivot_success, mart_dev.pivot_test and mart_dev.pivot_blank: not checked: each
    is a table per value, made beside mart_dev.pivot_failed by its Pivot filter's answer
    "tables", and the workbook holds no PivotTable of one value's rows alone to compare it
    with.

"keep" is checked and reported as before. batch.md gets the same lines, as items.

- `workbook_check.FinalHive` gains `as_converted` and `beside`; `_pivot_filter_lines` says
  them after the final's own lines (the "checked as converted" line only where it was
  checked). The module docstring says so.
- `pivot_filters.answered_since_converted(keyed, answers, held)` gives the words.
- `project._as_converted(root, final)` fills both from `_pivot_filter_tables`, the tables per
  value in the order of their values; `_workbook_checks` passes each final through it.
- Tests (`tests/test_workbook_check.py`): fold, batch and tables, each converted again and
  matching as converted, the line in the report and in batch.md; the tables beside the first
  named; "keep" as today. 6 new hashes in `tests/snapshot/known.txt`, none left stale (the
  touched test files' hashes compared before and after).

Left, from ticket 08: converting again writes the files write_decisions rewrote to the batch's
fresh/, and after "tables" batch.md too, as they are no longer the batch's as it wrote them;
the new test reads batch.md's fresh copy where there is one.
