# PivotTables into Hive, in code

Type: task
Status: open
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
