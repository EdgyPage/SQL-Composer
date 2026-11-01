# A calculation's type, from what it reads

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

Found by ticket 03's Excel scenarios, while their reference ends were built: a new table from a
query leaves each calculated column's type a Decision, written "string" as a guess, though Hive
types it. `SUM(r.duration_mins)`, `AVG(...)`, `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`,
`COALESCE(SUM(...), 0)` and `COUNT(r.run_id)` each came out untyped: only `count_rows()` gives a
type (`bigint`). A user with no context must answer each by hand, and a guessed "string" written
into a Table reference is wrong for every one of them.

## Done when

- Each calculation gives the type Hive gives it, where what it reads tells it:
  - a count, `bigint`;
  - a sum, `bigint` of whole numbers and `double` of a `float` or `double`;
  - an average, `double`;
  - a smallest or largest value, its column's type;
  - `if_else`, `first_match` and `mapped`, the type their values share, a whole number widened to
    the wider of two, a NULL taking the other's;
  - `fill_null`, its column's type, else its value's;
  - arithmetic on two numbers, the wider, and a division `double`;
  - a literal, its own: `int`, `double`, `string`, `boolean`, `date`.
  - a Hive function whose type is fixed, that type: a conversion writes `COUNT(r.run_id)` and
    `UPPER(...)` as `hive_function`, so without it the Question's `COUNT(r.run_id)` stays
    untyped.
- A calculation whose type nothing tells stays untyped, a Decision, as now.
- Tests hold each rule, and ticket 03's Excel scenarios leave no type to answer for any column a
  rule types.
- CHANGES.md's `## 8.2` names it.

## Answer

Built 2026-11-01, found by ticket 03.

- `tables.py`: `literal_type` (a whole number past an int's range a `bigint`), `shared_type`,
  `WHOLE_NUMBERS`, `FRACTIONS`; `arithmetic` types its result, a division a double.
  `calculations.py`: `aggregate_type` for each aggregate, `values_type` for `if_else`,
  `first_match` and `mapped`, `fill_null` its column's or its value's, and `HIVE_FUNCTION_TYPES`
  for the Hive functions whose type is fixed (`count`, as a conversion writes `COUNT(col)`, the
  string functions, `length`, `year`, `month`, `day`, `datediff`).
- `tests/test_calculation_types.py`: a query of twelve calculations converted, each typed in its
  Table reference; one test per rule, on the calculation itself (a smallest value, widening,
  whole numbers with fractions, a NULL beside a value, `fill_null` of an untold column, a number
  times a fraction, boolean, date, a bigint literal); values sharing no type left untold; and a
  calculation whose type nothing tells still a Decision. `tests/journeys/test_usability_scenarios.py`
  holds ticket 03's Excel ends to leave no type guessed.
- Two tests that leaned on a guess changed with it: `tests/test_conversions.py`'s CASE of text
  values is now a string with nothing to check, and `tests/test_batches.py` names a type to
  check with `REVERSE(...)`, which nothing types. The intermediate Example project's converted
  references are regenerated with their types.
- No timestamp literal: the Toolbox refuses a date and time written into Hive, so none reaches a
  type.
- A stacking test whose first Statement's `count_rows() * 1` was untyped now uses a calculation
  that is (`hive_function("abs", ...)`), as the test means.
- Code review: Spec asked for each rule's test, a test that the Excel ends leave no type, and
  the Hive functions in the Done-when list (both added); a literal past an int's range is now a
  bigint. Standards: `shared_type` no longer drops an empty type silently.
