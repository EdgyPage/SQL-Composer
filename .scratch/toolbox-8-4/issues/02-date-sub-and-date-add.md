# date_sub and date_add convert to Hive's two arguments

Type: task
Status: open
Blocked by: 01
Size: S

## Question

sqlglot reads `date_sub(x, 14)` as `DATE_ADD(x, 14 * -1, DAY)`, and the Conversion writes
`hive_function("date_add", x, 14 * -1, unchecked_column("DAY"))`: refused for `DAY`, and not
Hive, whose `date_add` takes two arguments (map, "What the user hit").

## Done when

- `date_sub(x, n)` and `date_add(x, n)`, with `x` a column, a literal date, a Script tag or a
  calculation, and `n` a number or a column, convert to Python whose Hive is the original's
  two-argument call, `date_sub(x, 14)` staying `date_sub`, with no `unchecked_column("DAY")`.
- `compare_hive` of the converted Statement and the original says they match.
- A `DATE_ADD` whose unit isn't a day, if sqlglot gives one, stays an Unchecked expression with
  its note, never a wrong call.
- 01's unit tests for these shapes hold the new output.
