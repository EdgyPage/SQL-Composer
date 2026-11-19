# Pivot workbooks for tests

Type: task
Status: open
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
