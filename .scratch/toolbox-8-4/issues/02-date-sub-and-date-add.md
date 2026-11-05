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

## Answer
Built 2026-11-05.

- **`_Converter.days_moved`**, called from `function` for sqlglot's `TsOrDsAdd`: Hive's
  `date_sub(x, n)` (read as `DATE_ADD(x, n * -1, DAY)`) becomes `hive_function("date_sub", x,
  n)`, and `date_add(x, n)` becomes `hive_function("date_add", x, n)`, with `x` and `n` each a
  column, a literal, a Script tag or a calculation, written as any value is. No
  `unchecked_column("DAY")`.
- **The Hive**: the Toolbox writes `hive_function("date_sub", x, 14)` as `DATE_ADD(x, 14 *
  -1)`, as sqlglot writes Hive's date_sub; Hive reads both the same, and `compare_hive` with
  the original matches. The ticket's "date_sub staying date_sub" is that: the same call, as
  the Toolbox writes every Hive function, in its usual form.
- **A unit other than DAY**, which no Hive text gives, stays an Unchecked expression, refused
  with its note (`Unconvertible`).
- **Tests**, `tests/test_date_windows.py`: four shapes convert with no Unchecked part, a column
  for the days among them; a converted date_sub's Statement matches the original's Hive and
  runs on the Example database. CHANGES.md's `## 8.4` opens with it.
