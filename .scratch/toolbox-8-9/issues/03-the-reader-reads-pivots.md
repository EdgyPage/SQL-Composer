# The reader reads PivotTables

Type: task
Status: resolved
Blocked by: 01, 02
Size: L

## Question

What the reader gives of each PivotTable, and how `workbook_text.py` shows it for the Copilot
path (round 3, Q7).

## Done when

- **The reader gives each pivot**: its name and sheet; its source (a Table, a query's Table, a
  range read as the Table it would be, the Data Model, OLAP); its Row, Column, Value and Report
  filter fields, each value's summary and Show Values As; calculated fields and calculated
  items with their formulas; date and number grouping; hidden items; each slicer and Timeline
  connected to it, with its saved selection; value filters; which totals it shows; its cells,
  each with the row and column items it stands for and its stored value.
- **The Order** holds pivots: a pivot reads its source; a Table formula's GETPIVOTDATA reads the
  pivot. A loop through a pivot is refused, as any loop is.
- **`workbook_text.py`** writes each as `PivotTable "name"` with all of the above, in place of
  "A PivotTable", and its line in the Order.
- Tests on ticket 02's fixtures: every field above read right; the text pinned.

## Answer

Built 2026-11-19 in `sqlglot_composer/workbook_reader.py` (still standard library only, no
relative import) and `copilot/workbook_text.py`, with tests in `tests/test_workbook_pivots.py`
(new), `tests/test_workbook_text.py` and `tests/test_workbook_reader.py`.

**What the reader gives.** `Sheet.pivot_tables` is now a `list[PivotTable]` (it was a count),
`Workbook.pivot_tables` gives every pivot sheet by sheet, and `Workbook.slicers` every slicer
and Timeline. The new data types:

- `PivotTable`: `name`, `sheet`, `ref` (its body), `source`, `rows` and `columns` (outermost
  first; `VALUES` among them where several values stand side by side), `values`,
  `report_filters`, `fields` (each cache field by name), `filters`, `slicers`,
  `grand_total_row` and `grand_total_column` (the totals it shows, not only the switches: a
  Grand Total column needs a Column field), `subtotals` (the fields whose subtotals show: an
  outer Row or Column field's), `layout` ("Compact Form", "Outline Form", "Tabular Form") and
  `cells`.
- `PivotSource`: `kind` (`EXCEL_TABLE`, `RANGE`, `DATA_MODEL`, `OLAP`, `DATA_CONNECTION`,
  `OTHER_WORKBOOK`, `CONSOLIDATION`), `name`, `table` (the Table, or for a range the `Table`
  it would be, named by its defined name or as `Runs!A1:F10`), `model_tables` and `pieces`
  (what the Order reads: the Table, the range, or each Table or query loading a Data Model
  table the pivot reads, through `x15:modelTable` and its connection).
- `PivotField`: `items` (in the pivot's order, a blank as None, a grouped field's labels),
  `hidden`, `formula` (a calculated field's), `calculated_items` (item to formula),
  `grouping`, `subtotals` (`[AUTOMATIC]`, the chosen functions, or none) and
  `shows_items_with_no_data`.
- `PivotValue`: `caption`, `field`, `summary` (Excel's word: Sum, Count, Average, Max, Min,
  Product, Count Numbers, StdDev, StdDevp, Var, Varp, Distinct Count; or `DAX_MEASURE`),
  `shown_as` (Excel's words, the x14 `pivotShowAs` read over `showDataAs`), `base_field`,
  `base_item` ("(previous)" and "(next)" for Excel's two special items).
- `Grouping` (`by`: Seconds to Years, "Number" for bins, "Items" for groups made by hand;
  `field`, `start`, `end`, `interval`, `groups`), `ReportFilter` (`field`, `selected`, empty
  for (All)), `PivotFilter` (`kind` `VALUE_FILTER`, `LABEL_FILTER` or `DATE_FILTER`, `test` in
  Excel's words, `values`, `by`, and a Top 10's `unit`), `Slicer` and `Timeline` (`name` as
  their defined name, `field`, `caption`, `sheet`, `pivots`, and `selected` or `start` and
  `end`), `PivotCell` (`at`, `value`, `row`, `column`, `stored`) and `PivotLine` (`items`, as
  (field, item) pairs, and `total`: "", `TOTAL` or a custom subtotal's function, or
  `GRAND_TOTAL`).

**Decisions.**

- A cell's items are those GETPIVOTDATA would name: an outer item's own row, where compact
  form shows its subtotal, names that item alone; a Grand Total line names none. A blank line
  has no cells, and a cell the sheet holds nothing in is `stored=None`.
- The cells a pivot fills, its body and its Report filters, are its own, taken off its sheet's
  other cells, so "A3: Row Labels" and the like are gone from the text.
- The items a slicer or a Report filter of several items leaves out are its own, not hidden
  on the field (Excel marks them `h="1"` on the field too); a Timeline's own `dateBetween`
  filter, named as the Timeline, is not a pivot filter; a slicer's and a Timeline's defined
  names (`Slicer_status`, `NativeTimeline_dt`, `#N/A`) are left out of `defined_names`.
- A Data Model value is Excel's own when its caption is "<summary> of <column>" and its
  hierarchy is hidden or names its `aggregatedColumn`; any other is a `DAX_MEASURE`, by its
  name. A source is the Data Model when its connection is ThisWorkbookDataModel (or its command
  is Model), an OLAP cube when its connection reads one or its cache has hierarchies, else a
  data connection.
- The Order gains two kinds of piece: `PIVOT_TABLE` (`PivotTable "name"`, by its sheet and
  name, `Pivot!PivotTable1`, where two pivots share a name) and `RANGE` (`Range
  "Runs!A1:F10"`). A pivot reads its source's pieces; a Table whose formula has GETPIVOTDATA
  naming a cell of a pivot (its body or its Report filters, on the formula's sheet or the one
  named) reads the pivot; a loop through a pivot is refused with the same LoopError, its links
  in Excel's words (`PivotTable "PivotTable1" reads Excel Table "job_runs"; Excel Table
  "job_runs"'s formulas read PivotTable "PivotTable1"`). A GETPIVOTDATA in a cell outside any
  Table adds nothing to the Order: the ticket asks for a Table formula's, and a cell outside a
  Table is no piece (file 11's X1).
- Read as Excel saves it, past what ticket 02's tool doesn't write: layouts by `compact` and
  `outline`, custom subtotals, label, value and date filters (`stringValue1`, custom filters,
  Q1 to Q4, M1 to M12), groups made by hand (`discretePr`), items marked missing (`m="1"`) or
  collapsed, a place past the items there (None), extra attributes, OLAP members by caption,
  an OLAP slicer's selections. Tests change a fixture's part as Excel would save it for each.

**A gap ticket 04 found, fixed here: a Table named alone.** The Order now sees a Table a
formula names with no `[` after it, as `jobs` in `=VLOOKUP([@job_id],jobs,2,FALSE)`, outside
strings, quoted sheet names and brackets, and not a function's (followed by `(`), a sheet's
(followed by `!`) or a cell's (`$A$1`). A test holds that a Table named only in a string is
not read. The three older fixtures' text is unchanged; of the 84 Excel evaluation tasks, X13
and X32 (`VLOOKUP([@job_id],jobs,2,TRUE)`) now have `Excel Table "job_runs", its formulas
read Excel Table "jobs"`, with jobs before job_runs, which was missing; their text for the
evaluations changes in the Order alone. Ticket 04's workaround (reading every source before
any Table) can go.

**The text.** In place of "A PivotTable", each pivot on its sheet, after the sheet's cells and
charts, in Excel's words:

    PivotTable "PivotTable1", A3:D8
      Source: Excel Table "job_runs"
      Rows: job_id
      Columns: status
      Value "Sum of duration_mins": Sum of duration_mins, Show Values As % of Column Total
      Filter avg_retry_secs: (All)
      Items hidden on status: TEST
      Timeline "dt" on sheet "Pivot", field dt: selected 2026-09-24; connected to PivotTable1
      Totals shown: Grand Total row, Grand Total column
      Cells: each value cell, what Excel last stored in it, then the Value it shows and the Rows and Columns items it stands for:
        C5: 0.625 (62.50%; Sum of duration_mins; Rows job_id 1; Columns status SUCCESS)
        D8: 1 (100.00%; Sum of duration_mins; Rows Grand Total; Columns Grand Total)

and likewise `Calculated Field "hours" = duration_mins/60`, `Calculated Item "done" on status
= SUCCESS+FAILED`, `Field "Years" groups dt By Years, Starting at 2026-09-23, Ending at
2026-09-25`, `Value
Filter on job_id: Top 2 Items by Sum of hours`, `Slicer "status" on sheet "Pivot", field
status: selected FAILED, SUCCESS; connected to PivotTable1, runs_by_day`, `Filter status:
(Multiple Items) SUCCESS, FAILED`, `Source: the range Runs!A1:F10, read as the Table it would
be: run_id | ...`, `Source: the Data Model, its tables job_runs, loaded from Excel Table
"job_runs"`, `Value "Total": the DAX measure Total`. The Order shows `PivotTable "x", reads
...`, `Range "..."`, and `Excel Table "t", its formulas read PivotTable "x"`. The seven pivot
fixtures' `.txt` are regenerated by `tools/workbook_fixtures.py`; the three older ones' are
byte for byte the same.

**Tests.** The in-memory workbooks (`tests/test_workbook_pivots.py::built`, a new group in
`tests/workers.py`) are ticket 02's own cases, so their Hive gives rows the snapshot knows;
`tests/snapshot/known.txt` is unchanged.

**Left.** Two partials, known and named: a query loaded only into the Data Model still says
"connection only" in the text (ticket 05 or 07 may say "loads into the Data Model"); and
Excel's Report filter layout of more than one column (`colPageCount` > 1) is taken as one
column when the pivot's cells are taken off the sheet.

## Review

The code-review skill (Standards and Spec) and the beginner reader, on the pivot fixtures'
text as a person with Excel and pivot skills reads it, after the merge into dev (d7ad237a).
Every public name, field and constant of the reader is kept (tickets 05 and 06 read them);
only private names changed. The seven pivot fixtures' `.txt` regenerated; only 07's and 08's
change, in the lines below.

**Standards.**

1. **One way per job.** A quoted sheet's name is unquoted by one function, `_unquoted_sheet`
   (the range's defined name and GETPIVOTDATA's sheet). An OLAP name's last part, a field's or
   a member's caption, is read by one function, `_olap_last_part`, on one pattern, `MEMBER`
   (its value widened to any bracketed last part; a Report filter's member is told by its
   `&[`). A pivot's key, its sheet and name, is one function, `_pivot_key`, used by the
   pivots read, the slicers' pivots and the Order's pieces.
2. **Names.** `_add_pivot_tables` is split: `_read_pivot_tables` gives each pivot with its sheet
   and cache, `_add_pivot_tables` adds each to its sheet and takes its cells off, `_slicers`
   gives each slicer and Timeline with the pivots it names, and `_connect_slicers` connects
   them. Each XML element is named for its tag (`pivot_table_definition`, `cache_definition`,
   `cache_field`, `pivot_field_element`, `data_field`, `page_field`, `field_group`,
   `range_group`, `slicer_cache`, `timeline_cache`, `sheet_element`), and each list for what it
   holds (`pivot_cells`, `report_filters`, `lines`, `connections`). `_field_name` is gone:
   `_value_at(names, place) or ""`.
3. **Plain expressions.** Each conditional the review named is an `if`: `_pivot_pieces`,
   `_pivot_lines` (a blank and a Grand Total line apart, and the missing rowItems before the
   loop), the location's ref before `PivotTable(...)`, and, the same rule, `_Connection(...)`'s
   Table in `_connections`.
4. **Keywords.** `PivotTable(...)` is built with keywords, and `_Connection(...)` too.
5. **A record per field.** `_PivotCache` holds its definition and a `_CacheField` for each
   field (name, items, formula, grouping, calculated items, measure), in place of its four
   parallel lists and two dicts; `names` is a property. The fields of a pivot are built by
   `_pivot_fields`, its totals added by `_add_totals`. Clearing a field's hidden items for a
   Report filter or a slicer is one function, `_clear_hidden`, which says the rule.
6. `_items_text` has a docstring; `_slicer_text` tests `isinstance(..., Timeline)` once, a
   Timeline's selection written by `_timeline_selection`.

**The beginner reader.**

7. The docstring's sentence is split in two, and the Value field is "Value": "For each cell,
   the text gives the number Excel last stored in it, and a percentage as Excel shows it where
   the Value is shown as a %; then which Value it is, and the row and column items it stands
   for."
8. A date with no time of day is written as its day: `Timeline "dt" ...: selected 2026-09-24`,
   one day once where its first and last are the same, and two days as `2026-09-23 to
   2026-09-24`; a date grouping's `Starting at 2026-09-23, Ending at 2026-09-25` the same
   (`_day_text`). A Table's own date cells keep the text openpyxl gives them, which the Excel
   evaluation's view holds.
9. A cell whose Value is shown as a % (any Show Values As starting "%") has the percentage
   Excel shows, to two places, beside the stored number: `C5: 0.625 (62.50%; Sum of
   duration_mins; ...)`.

The Order's last line ("Each final's query reads the steps it needs as CTEs") is unchanged.

**Spec.** A GETPIVOTDATA outside a Table adds nothing to the Order, now said in the Answer;
the two partials stay named in **Left**.

Run after the fixes: `tests/test_workbook_reader.py`, `tests/test_workbook_text.py`,
`tests/test_workbook_pivots.py`, `tests/test_pivot_tables.py`, `tests/test_excel_eval.py`,
`tests/test_workbook_hive.py` and the repo checks (`test_toolbox_checks`, `test_standard`,
`test_local_paths`, `test_code_audit`, `test_offline_policy`, `test_dead_code`,
`test_faster_suite`): 912 passed.

- **The beginner reader** (2026-11-19, on Opus): [its report](../reports/beginner-reader-2026-11-19-ticket-03.md). Three of its five stops fixed (96038be9); two left for the user, as the report says.
