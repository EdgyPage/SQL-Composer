# The pivot tasks and their baseline

Type: task
Status: resolved
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
- **The baseline**: each split answered without file 20, on Haiku and Sonnet, recorded in the
  ledger, in `.eval-local/`.
- `docs/copilot-eval.md`'s Excel section names the new tasks.

## Answer

Built 2026-11-19 on d7ad237a (ticket 03 merged), in `tools/excel_eval_tasks.py`,
`tools/excel_eval.py` and `tests/test_excel_eval.py`; `docs/copilot-eval.md`'s Excel section
names the tasks and how a pivot task is scored. Everything is done but **the baseline, which
is the lead's**: it spawns proxy models, and runs once ticket 03's text fixes are in.

### The tasks

40 new tasks, each a workbook from ticket 02's tool (`FormulaWorkbook(pivots=, slicers=)`,
queries on a Power Query sheet), with a reference Hive per final, the pivot's total levels'
included. `COVERAGE` gains 35 pivot kinds (`pivot_rows` to `pivot_combination`), and each has a
task in each split, as the existing test holds. 124 tasks now, 62 a split.

Dev, X85 to X104:

| Task | Cases |
|---|---|
| X85 | Row field, Sum, grand total, a Table source, a renamed pivot |
| X86 | a Column field (as rows, marked), the default name `PivotTable1` on sheet "Runs by status" (mark `runs_by_status_pivot`), its four total levels |
| X87 | every summary but Distinct Count, side by side (Sum, Count, Average, Max, Min, StdDev, Var) |
| X88 | % of grand total (its grand total 1), rank |
| X89 | % of row and % of column total, a Column field, totals off |
| X90 | running total in, difference from job 1 (blank on its base item), totals off |
| X91 | a calculated field, a Top 2 value filter, the filtered grand total |
| X92 | a calculated item `done = SUCCESS+FAILED`, a column beside the real rows |
| X93 | dates grouped by months ("Sep"), a Row field's subtotals `(by dt)` |
| X94 | number bins of ten, as their labels ("10-19") |
| X95 | a Report filter of two items, an (All) Report filter (no condition), items hidden on a Row field |
| X96 | a slicer on two pivots |
| X97 | a Timeline, over a plain range |
| X98 | a query's Table as the source |
| X99 | GETPIVOTDATA in a Table's formula (the pivot a CTE, LEFT JOINed) |
| X100 | Distinct Count, a Data Model pivot, its grand total not the sum of its rows |
| X101 | subtotals off |
| X102 | combination: a query (M join) feeding a pivot with a slicer, read back by GETPIVOTDATA under IFERROR in a summary Table |
| X103 | combination: a Table's XLOOKUP and arithmetic columns as the source, two values, a Report filter |
| X104 | combination: a query's Table.Group feeding a pivot with a Column field and a Top 2 filter, four total levels |

Held out, X105 to X124, written before file 20:

| Task | Cases |
|---|---|
| X105 | Row field with a blank item, a plain range source, renamed |
| X106 | Average across a Column field (totals are averages of rows, not of averages), the default name on "Daily" |
| X107 | every summary but Distinct Count, by status, blanks among them |
| X108 | % of grand total with a Column field, all four total levels shown |
| X109 | % of row total across a Column field, rank by status |
| X110 | % of column total, running total in a Column field (dt) |
| X111 | difference from a day, a Bottom 2 value filter that keeps the blank status |
| X112 | a ratio calculated field (ratio of the sums), a Report filter of one item |
| X113 | a ratio calculated item `FAILED/(SUCCESS+FAILED)` over a Column field |
| X114 | dates grouped by quarters and years, the Years subtotal |
| X115 | number bins as a Column field, four total levels |
| X116 | items hidden on a field with a blank item (the blank kept), a slicer on two pivots |
| X117 | a Timeline over a query's Table, an (All) Report filter |
| X118 | GETPIVOTDATA naming two fields, a Column field |
| X119 | Distinct Count by status, a Data Model pivot |
| X120 | two Row fields, the outer one's subtotals, the grand total off |
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
Values As a Window; a value filter a RANK Window; each Pivot filter the condition it is, its
values written in, under `-- Pivot filter: <kind> <field>`, kinds in CONTEXT.md's words
(`pivot_filter`); a pivot that a Table's GETPIVOTDATA reads a step, a CTE, with no final of its
own; a default name a mark proposing `<sheet name>_pivot` in snake case.

**Decided while building:**

- Where Excel's Grand Total would be blank (running total, difference from, rank), the task
  turns it off, so no final is a row of NULLs. Where a calculated item would make Excel's
  totals add it in (its double count), the task turns the totals off too (X92, X113, X124).
- The second pivot of a slicer pair shows no grand total (X96, X116), so no two finals of a
  task give the same rows and each is scored on its own.
- GETPIVOTDATA for an item the pivot doesn't have is `#REF!` in Excel and NULL here (X99,
  X121, job 4), 0 under IFERROR (X102).
- The Data Model's blank member reads as "(blank)" from the reader, a plain pivot's as None:
  the stored-values test reads both as NULL. Ticket 03 or 06 may want them the same.

**Left out, and why:**

- Two values across a Column field, and label, date and "greater than" value filters: ticket
  02's tool refuses them, and the map's cases don't need them (its value filter is "such as Top
  10", covered by Top and Bottom). `tools/pivot_tables.py` is unchanged.
- "Show items with no data", a DAX measure and an OLAP source, the refused cases: the tool
  doesn't write them, and the last two need a model only Excel writes. They wait for the manual
  round's workbooks the user builds in Excel.
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
  reply's SQL counts. A miss is `unnamed: Pivot filter: slicer status`. The marks expected are
  read from the references themselves (`pivot_filters_marked`), so there is no second list to
  drift; a test holds each reference's marks to the Pivot filters its workbook describes.
- A final's map name drops its `(...)` level (`named_by`), as a Total Row's did.
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
correct (95 cases); a reply with its marks stripped is unnamed, and one missing the mark on the
second pivot of a slicer is too; thirteen wrong answers lose `correct` (the blank dropped by a
hidden item, a Column field written wide, a ROLLUP row in the pivot's own final, a ratio item
over every status, a calculated field as a mean of ratios, a Distinct Count's grand total as a
sum, a Top 2 that keeps three, a Bottom read as a Top, a slicer left off the second pivot, a
Timeline's dates widened, a % of total over each day, GETPIVOTDATA as an inner join, a running
total over the whole pivot); column order and numeric text; the pivots' names; the text; the
manual round's files. `tests/snapshot/known.txt` knows the 147 new sets of rows the pivots' Hive
and the references give on the Example database.

Run: `tests/test_excel_eval.py`, `test_pivot_tables.py`, `test_formula_workbook.py`,
`test_eval_rounds.py`, `test_eval_ladder.py`, `test_eval_sources.py`, `test_workbook_hive.py`,
and the repo checks (`test_toolbox_checks`, `test_standard`, `test_local_paths`,
`test_code_audit`, `test_offline_policy`, `test_dead_code`, `test_faster_suite`): 1237 passed.
Not run: the whole suite, the code-review skill.

### For the baseline (the lead's)

Arm A0 on each split, `--tasks` X85 to X104 and X105 to X124, on Haiku and Sonnet, recorded in
the ledger, as `docs/copilot-eval.md`'s steps say. Arm C still loads files 15, 11 and 12 only:
ticket 11 adds file 20 to `EXCEL_FILES`. The proxies' text is `workbook_text.py`'s, so a change
from ticket 03's fixes (Timeline dates, percentages) changes every pivot task's memo key: run
the baseline after they merge. For tickets 06 and 13: these references set the shape the code
path must give, total levels' names and grouped keys' labels included.
