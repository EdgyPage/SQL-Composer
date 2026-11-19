# PivotTables into Hive, in code

Type: task
Status: resolved
Blocked by: 03, 04
Size: XL

## Question

Each pivot's Hive, as the map's Notes "PivotTables into Hive" and "Pivot filters" say. These
rules, with IDs, are what file 20 (ticket 11) writes for Copilot.

## Done when

- **The pivot's own final**: Row and Column fields the GROUP BY, a Column field as rows and
  marked; each value's aggregate; Show Values As a Window; a calculated field a Column over the
  sums; date and number grouping an expression in the GROUP BY; Distinct Count
  `COUNT(DISTINCT)`; a calculated item a column beside the real rows, a ratio item the ratio of
  the conditional sums.
- **Each total level shown** is a final of its own, `<pivot> (grand total)`, `<pivot> (by
  <field>)`; none when the pivot shows none.
- **Each Pivot filter** is the condition it is, its values written in, and noted for ticket 08's
  Decision: a Report filter, hidden items, a slicer's selection on each pivot it is connected
  to, a Timeline's dates, a value filter as a rank Window.
- **GETPIVOTDATA** is a LEFT JOIN on the pivot as a CTE, on the fields it names.
- **A pivot's source**: a Table, a query's Table, a range, or a Data Model pivot of plain sums
  from the query feeding it; refused and named: a DAX measure, OLAP, "Show items with no data".
- **Its name**: its own in snake case, or, for Excel's default, a name proposed for ticket 07's
  Decision, `<sheet name>_pivot`.
- **The rules have IDs**, each a test.

## Answer

Built 2026-11-19 in `sqlglot_composer/workbook_pivot_hive.py` (new; in the registry's
`PYTHON_FILES` and `LIBRARY_FILES`, and in `docs/agents/standards.md`'s list of the files that
may name sqlglot's types), with tests in `tests/test_workbook_pivot_hive.py` (67 tests). No public
name: nothing in `public.py` or `__init__` (ticket 07 gives the user's call).

**Where it plugs in** (ticket 04's seam). `workbook_hive.py`: `_piece_tree` has a branch for a
`PivotTable` piece (`pivot_tree`) and one for a `Range` piece a pivot reads (`range_read`, which
sets the range's read in place and gives no tree of its own); `workbook_hive()` adds
`pivot_total_finals` beside `_total_row_finals`; `_left_alone` no longer names PivotTables;
`_functions()` adds `PIVOT_FUNCTIONS` (GETPIVOTDATA). `workbook_formulas.py`: the join record
`PivotJoin(alias, read, keys)` beside `Lookup` and `Totals`, written by `_join_hive` (a LEFT JOIN
on the fields named, a CROSS JOIN where none are) and kept by `_drop_unread_joins` as a
`Totals` is. Two more small changes there, outside the seam as written: `check_named_refusals`
no longer refuses a GETPIVOTDATA's pivot cell (`Pivot!$A$3`, which X1 refused as "a cell outside
a Table"), and `snake_case` is a function of its own, which `hive_name` and this file both call.

**What it gives.** Each pivot's own final, keyed as every final is, by its name in the
workbook (`PivotTable1`, or `Pivot!PivotTable1` where two pivots share a name); each total
level it shows as `PivotTable1 (by job_id)`, `PivotTable1 (by Years and duration_mins)`,
`PivotTable1 (grand total)`, each with the pivot final's CTEs; and notes of the map's kinds
(MARK, REFUSED) with the rule IDs below. A pivot that GETPIVOTDATA reads is a step: its CTE, no
total-level finals and no name proposed. The names ticket 07 needs: `pivot_table_names(workbook)`
(each final's name to its table's: PN1, PN2). The records ticket 08 needs:
`pivot_filters(workbook)`, a list of `PivotFilterWritten(pivot, kind, field, values, items, by,
bottom)`, `items` being every item the pivot cache holds of the field, for its "at least"
counts. Also public in the module: `PivotLevel`, `levels_shown`, `level_final_name`,
`level_select`, `own_level`, `pivot_of`, `pivot_pieces`, `is_read`, `field_key`,
`value_aggregate`, `value_column_name`, `filter_conditions`, `getpivotdata_hive`.

**The rules, by their IDs** (each a test named for it; file 20, ticket 11, writes the same IDs):

- **PR1** Row and Column fields are the GROUP BY, each field a column, Row fields first, then
  each value, its column its caption in snake case: `SELECT job_id, dt, SUM(duration_mins) AS
  sum_of_duration_mins FROM <database>.job_runs GROUP BY job_id, dt`. A field's column is its
  name as file 11's N1 and N2 write it.
- **PR2** A Column field is written as rows, one per item, never a column per item, marked
  "Column field <name>: written as rows".
- **PR3** A date grouping is an expression in the GROUP BY and the SELECT, giving Excel's label:
  Years `YEAR(d)`, Quarters `CONCAT('Qtr', QUARTER(d))`, Months `DATE_FORMAT(d, 'MMM')`, Days
  (one day each) `DATE_FORMAT(d, 'd-MMM')`. A coarser level is a column named as Excel names its
  field (`Years`); the grouped field keeps its own name (`dt` holds `Sep`).
- **PR4** A number grouping is a CASE giving each bin's label: `CASE WHEN x < 0 THEN '<0' WHEN x
  < 10 THEN '0-9' .. WHEN x <= 49 THEN '40-49' ELSE '>49' END`.
- **PR5** Items grouped by hand: a CASE giving each group's name, `CASE WHEN f IN (a, b) THEN
  'Group1' ELSE f END`.
- **PV1** Each summary its aggregate: Sum SUM, Count and Count Numbers COUNT, Average AVG, Max
  MAX, Min MIN, StdDev STDDEV_SAMP, StdDevp STDDEV_POP; Var `POWER(STDDEV_SAMP(x), 2)` and Varp
  `POWER(STDDEV_POP(x), 2)`, because sqlglot writes VAR_SAMP as `VARIANCE`, which in Hive is the
  population's.
- **PV2** Distinct Count is `COUNT(DISTINCT x)`.
- **PV3** A calculated field is its formula over the Sum of each field it names:
  `duration_mins/60` is `SUM(duration_mins) / 60`; a quoted name (`'Unit Price'`) and `^`
  (POWER) read too.
- **PV4** % of Grand, Row or Column Total: `v / SUM(v) OVER (...)`, over nothing, the level's
  Row fields, or its Column fields: `SUM(x) / SUM(SUM(x)) OVER (PARTITION BY status)`.
- **PV5** Running Total In: `SUM(SUM(x)) OVER (PARTITION BY <other fields> ORDER BY <base> ROWS
  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`; a grouped base field in the order of
  `MIN(<its column>)`.
- **PV6** Difference From, % Of and % Difference From a base item: the item's value is
  `MAX(CASE WHEN <base> = <item> THEN SUM(x) END) OVER (PARTITION BY <other fields>)`; a
  difference is NULL on the base item's own row, where Excel leaves it blank.
- **PV7** Rank Largest to Smallest: `RANK() OVER (PARTITION BY <other fields> ORDER BY SUM(x)
  DESC)`; Smallest to Largest ascending.
- **PV8** At a total level that doesn't group by a Show Values As's base field: NULL, as Excel
  shows it blank, marked.
- **PC1** A calculated item adding items up is a column beside the real rows, named for the
  item (and the value, `<item>_<value>`, where there are several): `SUM(SUM(CASE WHEN status IN
  ('SUCCESS', 'FAILED') THEN duration_mins END)) OVER (PARTITION BY <the row's other fields>)
  AS done`, the same on each of their rows.
- **PC2** Any other calculated item, such as a ratio, is its formula over each item's own
  conditional sum, each summed over the row's other fields: `SUM(SUM(CASE WHEN status =
  'SUCCESS' THEN x END)) OVER () / SUM(SUM(CASE WHEN status = 'FAILED' THEN x END)) OVER ()`.
- **PC3** At a total level without the item's field, the item is added into the total, as Excel
  adds it, an item with no rows counting 0, marked: `SUM(x) + COALESCE(SUM(CASE WHEN status IN
  (..) THEN x END), 0)`.
- **PL1** Each total level the pivot shows is a final of its own: the Grand Total row groups by
  the Column fields alone, the Grand Total column by the Row fields alone, an outer field's
  subtotals by it and the fields outside it, and each where they meet; `<pivot> (by <fields>)`,
  or `<pivot> (grand total)` for none. Never a Subtotal row (no ROLLUP) in the pivot's final.
- **PL2** A pivot showing no total has its own final alone. Subtotals of functions the person
  chose (Sum and Count, say) are refused and named, with no final.
- **PF1** A Report filter of some items: `f = x` or `f IN (..)`, a blank as `f IS NULL`; (All)
  is no condition.
- **PF2** Items hidden on a Row or Column field: `f <> x` or `NOT f IN (..)`, a blank item kept
  with `f IS NULL OR`, a hidden blank dropped with `NOT f IS NULL AND`.
- **PF3** A slicer's selection, on each pivot it is connected to: `f IN (..)`; none when it keeps
  every item.
- **PF4** A Timeline's dates: `d BETWEEN 'start' AND 'end'`, on the date column itself.
- **PF5** A Top or Bottom value filter of a number of items on the outermost Row or Column
  field: `f IN (SELECT f FROM (SELECT f, RANK() OVER (ORDER BY SUM(x) DESC) AS place FROM
  <source> WHERE <the other filters> GROUP BY f) AS ranked WHERE place <= 2)`.
  Every Pivot filter's condition is in the WHERE of the read of the source, before grouping, at
  every level, and is marked "Pivot filter: <kind> <field>, <what it keeps>: a Decision of its
  table" (rule PF1 to PF5), its kind in CONTEXT.md's words: Report filter, hidden items,
  slicer, Timeline, value filter.
- **PG1** GETPIVOTDATA naming every Row and Column field is a LEFT JOIN of the pivot, a CTE, on
  the fields it names, each matched to the Hive of the item it names, reading the value's column:
  `WITH PivotTable1 AS (..) SELECT m.job_id, p.sum_of_duration_mins AS mins FROM
  <database>.job_mins AS m LEFT JOIN PivotTable1 AS p ON m.job_id = p.job_id`; marked NULL where
  Excel shows #REF!.
- **PG2** GETPIVOTDATA naming fewer fields reads the total level it names, as its own query
  joined (a CROSS JOIN for the grand total); a total the pivot doesn't show is refused, NULL.
- **PS1** A Table: FROM what the Table is read as, `<database>.<table>` or a step's CTE; a
  source with no Hive refuses the pivot.
- **PS2** A query's Table: FROM the Table the query loads, as PS1.
- **PS3** A plain range: the Table it would be, `<database>.<sheet>` in brackets
  (`<database>.<runs>`), marked to fill in.
- **PS4** A Data Model pivot of one model table: FROM the Table or query feeding it; several
  model tables refused.
- **PN1** A pivot's own name in snake case is its table's (`runs_by_day`).
- **PN2** Excel's default name (`PivotTable1`) proposes `<sheet name>_pivot` (`pivot_pivot`,
  `ranked_pivot`, then `pivot_pivot_2`), marked for the Decision.
- **PX1** A DAX measure: NULL in its place, named.
- **PX2** An OLAP cube, a data connection, another workbook or multiple consolidation ranges:
  refused, no final.
- **PX3** "Show items with no data" on a Row or Column field: refused, no final.
- **PX4** The rest that has no Hive here, refused and named: Product; Show Values As Index, % of
  Parent Totals, % Running Total In, a base field that isn't a Row or Column field, the
  (previous) and (next) base items; label and date filters, and value filters of a percent, a
  sum or on an inner field; grouping by seconds, minutes, hours or days of more than one; a
  calculated item beside a value that isn't a plain Sum; a calculated formula of more than
  names, numbers and + - * / ^. A value's refusal is NULL in its place; a refusal of the
  pivot's rows leaves it with no final.

**The rows check** (a preview of ticket 09): every pivot of fixtures 04, 05, 07, 08, 09 and 10,
and of ten workbooks built as `tests/test_pivot_tables.py`'s cases (every summary, each Show
Values As, a calculated field, date groups, two Row and two Column fields, Report filters,
hidden items, Top and Bottom, the Data Model's Distinct Count), run on the stand-in Hive
(`excel_eval.stand_in_hive`, the Example database's rows, with QUARTER added in the test),
gives every value the pivot's cells stored, cell by cell, at each total level, within a relative
1e-9. A cell for a calculated item is read from its column; a cell of a level the pivot doesn't
show (09's subtotals) stores nothing and has no final. GETPIVOTDATA's column is checked against
the pivot's own cells, and NULL for job 4, which the pivot has no row for. Fixture 06 isn't in
it: its pivot reads a query's Table, whose M ticket 05 converts; today it is refused, PS1, named.

**Decisions.**

- A final is keyed by the pivot's name in the workbook, as every final is; the table it becomes
  comes from `pivot_table_names`.
- A pivot's rows that can't be written (its source, a grouping, a filter, "Show items with no
  data") refuse the whole pivot, with no final; one value that can't is NULL in its place.
- Each total level reads the source again, never the pivot's final as a CTE: an Average, a
  StdDev or a Distinct Count can't be added up from the groups below.
- A total level's map names only what is its own (PV8, PC3); the rest is named once, on the
  pivot.
- No `-- Pivot filter:` comment is written into the code path's Hive: its Pivot filters are the
  `PivotFilterWritten` records and the MARK notes. Ticket 07 may write the comment too, so both
  paths' Hive carry it.

**For ticket 17 (Hive that stays small).** Windows over one read do Show Values As and the
calculated items; each filter is in the WHERE of the source's read, before grouping; the
pivot's CTE carries only its fields and values. Shapes that read a source twice within one
final, as the right rows need:

- **PF5**: a Top or Bottom value filter's IN subquery reads the source a second time (in the
  pivot's final and in each total level's). The right totals (an Average or a Distinct Count of
  the kept items alone) need the kept items before grouping, so it stays a second read.
- **PG2**: GETPIVOTDATA reading a total level joins that level's own query, a second read of the
  source beside the pivot's CTE where the same Table reads both.
- A pivot over a step Table reads that step's CTE, which ticket 04's `_with_steps` writes with
  every column of the Table, read or not.

**Left.** Fixture 06's rows once ticket 05 converts its query. A query loading only the Data
Model is `left out` by `piece_roles`, so a Data Model pivot over one has no source today (ticket
05 or 07). A running total over text items runs in Hive's order, where Excel's is A to Z
whatever the case, blanks last. The code-review skill hasn't run on this ticket.
