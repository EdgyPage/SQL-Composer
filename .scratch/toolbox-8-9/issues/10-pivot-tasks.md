# The pivot tasks and their baseline

Type: task
Status: claimed
Blocked by: 02, 03
Size: L

## Question

The Excel evaluation's pivot tasks, written before file 20 as 7.2 wrote its tasks before file
11 (round 3, Q9).

## Done when

- **About 40 tasks, 20 dev and 20 held-out**, in `tools/excel_eval_tasks.py`, each a workbook
  from ticket 02's tool with a reference Hive per final: each case in the map's Notes alone,
  and a combinations tier mixing pivots with formulas and M (such as a query feeding a pivot
  with a slicer, read back by GETPIVOTDATA).
- **The scorer** scores a pivot's finals and its totals' finals, and counts its Pivot filter
  marks (the `-- Pivot filter:` comment) under `named`.
- **The baseline** (open: the lead's): each split answered without file 20, on Haiku and
  Sonnet, recorded in the ledger, in `.eval-local/`.
- `docs/copilot-eval.md`'s Excel section names the new tasks.

## Answer

Built 2026-11-19 on d7ad237a (ticket 03 merged), in `tools/excel_eval_tasks.py`,
`tools/excel_eval.py` and `tests/test_excel_eval.py`; `docs/copilot-eval.md`'s Excel section
names the tasks and how a pivot task is scored. Everything is done but **the baseline, which
stays open and is the lead's**: it spawns proxy models, and runs once ticket 03's text fixes are
in. The review's fixes (below) rebased it onto 16afc196.

### The tasks

40 new tasks, each a workbook from ticket 02's tool (`FormulaWorkbook(pivots=, slicers=)`,
queries on a Power Query sheet), with a reference Hive per final, the pivot's total levels'
included. `COVERAGE` gains 37 pivot kinds (`pivot_rows` to `pivot_combination`), and each has a
task in each split, as the existing test holds. 124 tasks now, 62 a split.

Dev, X85 to X104:

| Task | Cases |
|---|---|
| X85 | Row field, Sum, grand total, a Table source, a renamed pivot |
| X86 | a Column field (as rows, marked), the default name `PivotTable1` on sheet "Runs by status" (mark `runs_by_status_pivot`), its four total levels |
| X87 | every summary but Distinct Count, side by side (Sum, Count, Average, Max, Min, StdDev, Var) |
| X88 | % of grand total (its grand total 1), rank |
| X89 | % of row and % of column total, a Column field, totals off |
| X90 | running total in job_id across a Column field, its totals shown: blank, NULL, where job_id isn't a key (ticket 06's PV8); difference from job 1 (blank on its base item), totals off |
| X91 | a calculated field, a Top 2 value filter, the filtered grand total |
| X92 | a calculated item `done = SUCCESS+FAILED`, a column beside the real rows, its grand total on: the item added into it, marked (ticket 06's PC3) |
| X93 | dates grouped by months ("Sep"), a Row field's subtotals `(by dt)` |
| X94 | number bins of ten, as their labels ("10-19") |
| X95 | a Report filter of two items, an (All) Report filter (no condition), items hidden on a Row field |
| X96 | a slicer on two pivots |
| X97 | a Timeline, over a plain range |
| X98 | a query's Table as the source |
| X99 | GETPIVOTDATA in a Table's formula (the pivot a CTE, LEFT JOINed) |
| X100 | Distinct Count, a Data Model pivot, its grand total not the sum of its rows |
| X101 | subtotals off |
| X102 | combination: a query (M join) feeding a pivot with a slicer, read back by GETPIVOTDATA under IFERROR in a summary Table, all from one read of the query's step |
| X103 | combination: a Table's XLOOKUP and arithmetic columns as the source, two values, a Report filter |
| X104 | combination: a query's Table.Group feeding a pivot with a Column field and a Top 1 filter, four total levels |

Held out, X105 to X124, written before file 20:

| Task | Cases |
|---|---|
| X105 | Row field with a blank item, a plain range source, renamed |
| X106 | Average across a Column field (totals are averages of rows, not of averages), the default name on "Daily" |
| X107 | every summary but Distinct Count, by status, blanks among them |
| X108 | % of grand total with a Column field, all four total levels shown |
| X109 | % of row total across a Column field, rank by status |
| X110 | % of column total; running total in a Column field (dt), its totals shown: NULL in the Grand Total column (ticket 06's PV8) |
| X111 | difference from a day, a Bottom 2 value filter that keeps the blank status |
| X112 | a ratio calculated field (ratio of the sums), a Report filter of one item |
| X113 | a ratio calculated item `FAILED/(SUCCESS+FAILED)` over a Column field |
| X114 | dates grouped by quarters and years, the Years subtotal |
| X115 | number bins as a Column field, four total levels |
| X116 | items hidden on a field with a blank item (the blank kept), a slicer on two pivots |
| X117 | a Timeline over a query's Table, an (All) Report filter |
| X118 | GETPIVOTDATA naming two fields, a Column field |
| X119 | Distinct Count by status, a Data Model pivot |
| X120 | a calculated item over a Column field, every total on: the item a column at the levels its field is a key of, added into the others, marked (ticket 06's PC3) |
| X121 | combination: a query (M AddColumn) feeding two pivots and a slicer on both, one read by GETPIVOTDATA |
| X122 | combination: a Table's VLOOKUP and IF columns as the source, a Column field, a Top 1 value filter |
| X123 | combination: a Table's XLOOKUP column, a Timeline, % of grand total by count, a Column field |
| X124 | combination: a query's Table with a formula column, a Report filter, a calculated item over a Column field |

**The reference Hive** follows the map's conversion rules, not the tool's executor-shaped Hive:
a pivot's final is its fields, outermost Row field first, then its values, then each
calculated item; a Column field written as rows (and the task marks "written as rows"); each
total level the pivot shows its own final, `<pivot> (grand total)` or `<pivot> (by <field>)`;
a calculated item a column, `SUM(CASE WHEN field IN (...) THEN v END)` over the row's other
keys, a ratio item the ratio of conditional sums; a grouped field's key the label the pivot
shows (`DATE_FORMAT(dt, 'MMM')`, `CONCAT('Qtr', QUARTER(dt))`, `YEAR(dt)`, a CASE for bins); Show
Values As a Window, NULL at a level where Excel shows a blank; a value filter a RANK Window,
or for a Top 1 over a Column field the item whose total is the largest; a calculated item added
into each total its field isn't a key of, as Excel adds it, and marked; each Pivot filter the condition it is, its
values written in, under `-- Pivot filter: <kind> <field>`, kinds in CONTEXT.md's words
(`pivot_filter`); a pivot that a Table's GETPIVOTDATA reads a step, a CTE, with no final of its
own; a default name a mark proposing `<sheet name>_pivot` in snake case.

**Decided while building:**

- Where Excel's Grand Total would be blank (running total, difference from, rank), most tasks
  turn it off; X90 and X110 keep theirs on, NULL there, as ticket 06's PV8 says. A calculated
  item's totals are off in X113 and X124, and on in X92 and X120, added into, as PC3 says. The
  mark for that is any of "added into the total", "added to the total", "counted twice" or
  "double count" (`ADDED_IN`).
- X120 took the place of a task of two Row fields with subtotals and the grand total off: X114
  holds subtotals and X109, X110 and X113 totals off in the held-out split.
- The second pivot of a slicer pair shows no grand total (X96, X116), so no two finals of a
  task give the same rows and each is scored on its own.
- GETPIVOTDATA for an item the pivot doesn't have is `#REF!` in Excel and NULL here (X99,
  X121, job 4), 0 under IFERROR (X102).
- The Data Model's blank member reads as "(blank)" from the reader, a plain pivot's as None:
  the stored-values test reads both as NULL. Ticket 03 or 06 may want them the same.

**Left out, and the manual round's:** two values across a Column field; label, date and
"greater than" value filters; "Show items with no data"; a DAX measure; an OLAP source. Ticket
02's tool refuses or doesn't write each, and the last two need a model only Excel writes, so
each is the manual round's, in a workbook the user builds in Excel and keeps in `.eval-local/`.
The map's value filter, "such as Top 10", is covered by Top and Bottom; `tools/pivot_tables.py`
is unchanged.
- **Distinct Count is built in memory** (X100, X119, `data_model=True`): its text is the
  reader's, from the saved bytes, and nothing is committed. `excel_eval.py workbooks` writes
  those two without their pivot (Excel can't open one with no model), and the doc says to make
  it by hand in the manual round.

### The scorer (`tools/excel_eval.py`)

- **A pivot's finals**, its own and each total level's, are correct when one query gives their
  rows with **its columns in any order** (each column tried only where it holds the same
  values), **a number as text the number** (a Years item "2026"). A Table's final keeps its
  column order.
- **Pivot filter marks count under `named`, per final**: the query that gives a final's rows
  must hold each mark the final's reference holds, kind by any of its words ("value filter",
  "Top", "Bottom" for a value filter) and the field; where no query gives the rows, any of the
  reply's queries counts. A mark is read from the comments sqlglot keeps on the parsed tree, so
  `-- Pivot filter: ...` above a condition and `/* Pivot filter: ... */` after it, as the code
  path writes it, are one mark. A miss is `unnamed: Pivot filter: slicer status`. The marks expected are
  read from the references themselves (`pivot_filters_marked`), so there is no second list to
  drift; a test holds each reference's marks to the Pivot filters its workbook describes.
- A final's map name drops its `(...)` level (`table_or_pivot_of`), as a Total Row's did.
- `workbook_names` knows a pivot's names: its own, its fields, its values' captions, its
  calculated fields and items.
- The stand-in Hive has `QUARTER`.
- `PLACEHOLDER` no longer reads `<= 49 THEN '40-49' ELSE '>` as a `<...>`: a placeholder holds
  no quote and starts with no `=`.
- `workbooks` writes a pivot task's file as Excel saves it (pivots, slicers, Timelines), but a
  Data Model pivot's.

### Tests (`tests/test_excel_eval.py`)

Each new reference scores a pass (the existing test, now over 124); and for the pivot tasks:
each pivot final's reference gives **the values the pivot stored**, cell by cell, read back by
the reader (a Workbook check in small: every value cell is its final's row's value, every row a
line the pivot shows, every total level shown a final; five references broken by hand while
building each failed it); each Pivot filter is marked in each final it ends up in; a reply
without any one final is not
correct (104 cases); a reply with its marks stripped is unnamed, and one missing the mark on the
second pivot of a slicer is too; thirteen wrong answers lose `correct` (the blank dropped by a
hidden item, a Column field written wide, a ROLLUP row in the pivot's own final, a ratio item
over every status, a calculated field as a mean of ratios, a Distinct Count's grand total as a
sum, a Top 2 that keeps three, a Bottom read as a Top, a slicer left off the second pivot, a
Timeline's dates widened, a % of total over each day, GETPIVOTDATA as an inner join, a running
total over the whole pivot); column order and numeric text; the pivots' names; the text; the
manual round's files; both forms of a mark. `tests/snapshot/known.txt` knows the 160 new sets of
rows the pivots' Hive and the references give on the Example database.

Run: `tests/test_excel_eval.py`, `test_pivot_tables.py`, `test_formula_workbook.py`,
`test_eval_rounds.py`, `test_eval_ladder.py`, `test_eval_sources.py`, `test_workbook_hive.py`,
and the repo checks (`test_toolbox_checks`, `test_standard`, `test_local_paths`,
`test_code_audit`, `test_offline_policy`, `test_dead_code`, `test_faster_suite`), and after the
review `test_workbook_text.py` and `test_workbook_pivots.py` too: 1372 passed. Not run: the whole
suite.

### For the baseline (the lead's)

Arm A0 on each split, `--tasks` X85 to X104 and X105 to X124, on Haiku and Sonnet, recorded in
the ledger, as `docs/copilot-eval.md`'s steps say. Arm C still loads files 15, 11 and 12 only:
ticket 11 adds file 20 to `EXCEL_FILES`. The proxies' text is `workbook_text.py`'s, so a change
from ticket 03's fixes (Timeline dates, percentages) changes every pivot task's memo key: run
the baseline after they merge. For tickets 06 and 13: these references set the shape the code
path must give, total levels' names and grouped keys' labels included.

## Review

The coordinator's review of a1dc4d07, rebased onto 16afc196 (ticket 03's review fixes, ticket
17's plan); each finding answered here, the fixes in one commit, `fix(8.9): ticket 10's review:
...`.

1. **Lean references (ticket 17's rule).** Fixed, every final checked against the pivot's
   stored values again:
   - A CTE read twice in one query is read once: X104 and X122 (now Top 1) take each item's
     total by a window over the step's rows and the largest by a window over those (a Top 1 is
     the item whose total is the largest, ties kept, as Excel's); X102 gives the summary's teams
     and the pivot's FAILED minutes by one conditional sum over one read of the query's step,
     the slicer's mark before the CASE's WHEN (sqlglot drops a comment inside a WHEN); X124's
     calculated item, and X113's, are windows over one read (X113 read job_runs twice).
   - A CTE carries only the columns its final reads, each total level included: the steps are
     functions of the keys their final groups by (`selected`, `ok_jobs`, `top_jobs`,
     `named_hours`, `top_job_days`, `quiet_statuses`, `runs_hours`, `top_team`), so a grand
     total's step carries no key; RUNS_NAMED, OK_REGIONS, the runs_hours step, the sized step
     and the ok step lost the run_id and duration_mins nothing read; X117's grand total's step
     dropped job_id; X123 joins job_runs only in the finals that read the run's status, with no
     CTE.
   - What stays: a Top 2 or Bottom 2 on a pivot of one grain (X91, X111) ranks the step's
     grouped rows in a second CTE, each read once. X104 went from Top 2 to Top 1: Hive's RANK
     over one row per job needs the job grain, a second read, and a window over the job/day rows
     can't give Excel's Top 2 with ties (DENSE_RANK keeps three where two tie first), so the
     task is a Top 1, which one read gives exactly.
2. **One reader of the mark.** Fixed: `marks_in`, reading the comments sqlglot keeps on the
   parsed tree, is the only one; the text regex is gone. Where no query gives a final's rows the
   marks of every parsed query count. A test scores X95 with its marks as `-- ...` above each
   condition and as `/* ... */` after it, the code path's form: both named.
3. **Names.** Fixed: `named_by` is `table_or_pivot_of` (the name of the Table or PivotTable a
   final belongs to); `answer_giving` is `place_of_answer_giving`, its docstring saying it gives
   a position; `_run_queries` is `_scored_queries`, which returns the queries' score and each
   final's marks for `score` to add its prose checks to, and reads the queries in
   `_read_queries`, which returns them.
4. **Docstrings.** Fixed: `_as_pivot_rows`, `has_a_data_model_pivot`.
5. **Ticket 06's PC3 and PV8.** Added, the tool writes both, and the count stays 40:
   - PC3, a calculated item with its totals on, added into them and marked: X92 (dev, its grand
     total on) and X120 (held out, over a Column field, every total on; it replaced a duplicate
     of X114's subtotals and X109's totals off).
   - PV8, Show Values As NULL where Excel shows a blank: X90 (dev, a running total in job_id
     across dt, its Grand Total row and grand total NULL) and X110 (held out, a running total in
     dt, its Grand Total column and grand total NULL).
   New kinds `pivot_calculated_item_total` and `pivot_shown_as_blank` hold each in both splits.
   The stored-values test now places a calculated item's cell at any level its field is a key
   of.
6. **The ticket.** Fixed: `Status: claimed`, the baseline's Done-when line open and named as the
   lead's; the cases left out named as the manual round's.

Also found while rerunning: `tests/test_workbook_text.py`'s
`test_each_tasks_text_is_the_one_openpyxl_reads_its_queries_read_back` ran on every task, and
openpyxl reads no PivotTable, so it failed on the 40 pivot tasks (it wasn't among the tests run
for a1dc4d07). It now runs on the formula tasks; the pivot tasks' text is held by the reader's
tests and the stored-values test.
