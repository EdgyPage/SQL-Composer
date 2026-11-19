# The reader reads PivotTables

Type: task
Status: open
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
