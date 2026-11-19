# Pivot workbooks for tests

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

How dev writes workbooks holding PivotTables, which openpyxl can't author, with stored values to
check against (round 2, Q8).

## Done when

- **A dev tool**, on `tools/formula_workbook.py`, adds to a Formula workbook a pivot as Excel
  saves one: its cache definition and records, its table definition, its cells with their
  stored values, and any slicer, slicer cache and Timeline, over a Table, a query's Table or a
  plain range.
- It can write each case the map's Notes list: Row and Column fields, every summary, Show
  Values As, calculated fields and items, date and number grouping, Distinct Count, grand
  totals and subtotals on and off, each kind of Pivot filter, a slicer on two pivots,
  GETPIVOTDATA in a Table's formula, a default name and a renamed one.
- **Stored values** are worked out from a reference Hive on the Example database's rows, and the
  map says they test the reader and the conversion, not Excel's arithmetic.
- **Each written workbook opens in Excel** without a repair prompt: checked by hand by the user
  on a few, the ticket naming which.
- **Queries** go on a Power Query sheet, never a saved DataMashup, so no `ALLOWED` entry is
  needed. Any workbook the user builds in Excel and wants committed, or a Data Model pivot,
  waits for the user's OK to an `ALLOWED` entry; until then it stays in `.eval-local/`.
- `tools/workbook_fixtures.py` writes a few pivot fixtures into `tests/fixtures/workbook_text/`.

## Answer

Built 2026-11-19, in `tools/pivot_tables.py`, on `tools/formula_workbook.py`, with tests in
`tests/test_pivot_tables.py`.

- **What it writes.** `pivot_tables.with_pivots(saved, worked)` adds to a saved workbook, as
  Excel saves them (ECMA-376 Part 1, 18.10; [MS-XLSX] for the x14 and x15 extensions): each
  pivot cache's definition and records (`xl/pivotCache/`), each pivot's definition
  (`xl/pivotTables/`), each slicer's cache, slicers part and drawing (`xl/slicerCaches/`,
  `xl/slicers/`, `xl/drawings/`), each Timeline's cache and Timelines part (`xl/timelineCaches/`,
  `xl/timelines/`), the defined names `Slicer_<field>` and `NativeTimeline_<field>`, the
  workbook's `<pivotCaches>` and extension lists, the sheets' drawing and extension lists, and
  every relationship and content type. Each pivot's cells, with their stored values, are
  written onto its sheet with openpyxl, before the save.
- **How a workbook says it.** `FormulaWorkbook` gains `pivots`, `slicers` (a `Slicer` or a
  `Timeline` each) and `queries_on_sheet` (its queries typed on a Power Query sheet, "Query
  <name>:" with the M below, in place of a saved DataMashup); `ExcelTable` gains `dates` (columns
  written as dates) and `in_a_table` (False writes a plain range). `pivot_tables` describes a
  pivot with `Pivot(source, rows, values, name="PivotTable1", sheet="Pivot", at, columns,
  report_filters, hidden, top, calculated_fields, calculated_items, dates, bins, subtotals_off,
  grand_total_row, grand_total_column, source_rows, data_model)`, a value with
  `Value(field, summary="sum", shown_as, base_field, base_item, name)`, and a value filter with
  `Top(field, count, value=0, bottom=False)`. `formula_workbook.saved` writes the whole file;
  `formula_workbook.worked_pivots(described)` gives each pivot worked out
  (`pivot_tables.work_out`), with its lines, cells and the Hive each value was worked out by.
- **The cases it writes**, each a test that opens the zip and checks its parts and values: Row
  and Column fields (two of each, too); Sum, Count, Average, Max, Min, StdDev, Var, and Distinct
  Count (a Data Model pivot); % of grand, row and column total, running total, difference from,
  and rank (the x14 `pivotShowAs` extension); a calculated field; a calculated item, which
  Excel's totals add up; date grouping by months, quarters and years (Excel's Quarters and
  Years fields) and number bins; grand totals and subtotals on and off; a Report filter of one
  item, of several, and of all; hidden items; a slicer connected to two pivots; a Timeline's
  days; a Top and a Bottom value filter; GETPIVOTDATA in a Table's formula; a default name and a
  renamed one; over a Table, a query's Table (its query on a Power Query sheet) and a plain
  range. Every written workbook is checked to be a whole package (each part's content type,
  each relationship's target, each part well formed) and to load in openpyxl.
- **Stored values** are worked out by Hive on the Example database's rows, with its own
  executor: one Hive per total level and value, a Window for Show Values As, and the value
  filter's kept items by a Hive of their own; never typed by hand. The tool's docstring says
  they test the reader and the conversion, not Excel's arithmetic (the map's Testing note says
  so already), and where they may differ: a blank where Excel shows an error, a tie in a rank.
- **What it refuses**, with a ValueError naming it: more than one value with a Column field, a
  pivot with no Row field, a value filter on any but the outermost Row or Column field, a
  calculated item with values other than Sums shown as themselves, a calculated formula of more
  than arithmetic, a slicer across two caches, a source with formulas and no `source_rows`, and
  a Data Model pivot with more than Row fields and values. Layout is compact form only.
- **The Data Model pivot** (Distinct Count) is an OLAP cache over the connection
  ThisWorkbookDataModel, with no records, its Table added to the model by a worksheet
  connection. Its model (`xl/model/item.data`, a database only Excel writes) isn't written, so
  Excel can't open it: it is for the reader's tests, built in memory. None is committed: the
  offline policy refuses its `xl/connections.xml`, which a test shows; committing one needs the
  user's OK to an `ALLOWED` entry.
- **The fixtures**: `tools/workbook_fixtures.py` writes seven more into
  `tests/fixtures/workbook_text/`, each with its `.txt` as today's `workbook_text.py` writes it
  ("A PivotTable" a pivot): `04_pivot_rows_columns`, `05_pivot_slicer_two_pivots`,
  `06_pivot_query_sheet`, `07_pivot_groups`, `08_pivot_timeline_filters`,
  `09_pivot_plain_range`, `10_pivot_calculated_item_rank`. None saves a connection, a query table
  or a DataMashup: the offline policy and the code audit read them clean, with no new `ALLOWED`
  or `AUDITED` entry.
- **Also changed**: `tools/excel_queries.py`'s two relationship helpers are public now
  (`relationship`, `with_relationships`), so both writers share them;
  `tests/snapshot/known.txt` knows the 79 new sets of rows the pivots' Hive gives;
  `tests/workers.py` groups the pivot tests' fixture.

### Open in Excel by hand (dev has no Excel)

Open each of these from `tests/fixtures/workbook_text/` and check that Excel opens it with no
"We found a problem with some content" prompt, then the line given:

1. `04_pivot_rows_columns.xlsx`: click in the pivot on sheet Pivot. The PivotTable Fields pane
   shows job_id in Rows, dt in Columns, Sum of duration_mins in Values. PivotTable Analyze >
   Refresh changes no number (D8 stays 180).
2. `05_pivot_slicer_two_pivots.xlsx`: a slicer "status" on sheet Pivot, SUCCESS and FAILED
   selected. Slicer > Report Connections ticks PivotTable1 and runs_by_day. Clicking TEST in
   the slicer changes both pivots.
3. `06_pivot_query_sheet.xlsx`: PivotTable Analyze > Fields, Items & Sets > Calculated Field
   lists hours = duration_mins/60; the job_id filter shows a Top 2 value filter; after
   Formulas > Calculate Now, job_hours' hours for job 1 is 1.0333.
4. `07_pivot_groups.xlsx`: right-click a date in the pivot, Group: Months, Quarters and Years
   are ticked; right-click a column label, Group: starting at 0, ending at 49, by 10.
5. `08_pivot_timeline_filters.xlsx`: a Timeline "dt" on sheet Pivot with 24 September 2026
   selected; status TEST is unticked in its filter; the value shows as % of Column Total.
6. `10_pivot_calculated_item_rank.xlsx`: Fields, Items & Sets > Calculated Item on status lists
   done = SUCCESS+FAILED; on sheet Ranked the value shows as Rank Largest to Smallest, base
   field job_id.

If one opens with a repair, the repair log Excel offers (the link in its message) names the
part it dropped: that part is the one to fix.
