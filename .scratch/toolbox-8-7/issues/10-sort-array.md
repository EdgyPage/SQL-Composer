# SORT_ARRAY's TRUE

Type: task
Status: open
Blocked by: -
Size: S

## Question

The user's Hive refuses `SORT_ARRAY(x, TRUE)`: "SemanticException [Error 10015]: sortarray
requires 1 positional argument(s), got 2". On sqlglot 30.23.0, 16 shapes of
`CONCAT_WS(' | ', SORT_ARRAY(COLLECT_SET(x)))` convert to one argument. The `True` comes only
from a source that already says `SORT_ARRAY(..., TRUE)`, Spark's form, which sqlglot keeps.
The user's words: "I don't necessarily want to box in the conversions should the underlying
sql change capability." (Q6, Q23, Q25.)

## Done when

- A Conversion reading `SORT_ARRAY(x, TRUE)` writes `hive_function("sort_array", x)`, with a
  `changed` finding: "SORT_ARRAY sorts ascending by default; its TRUE is left out, as Hive's
  takes one argument".
- `SORT_ARRAY(x, FALSE)` is kept as written, with a finding that Hive's `SORT_ARRAY` takes one
  argument, so your Hive may refuse it.
- `hive_function("sort_array", ...)` still takes one or two arguments: nothing is narrowed.
- Tests, written first: the user's line with and without `TRUE`, and the shapes of the
  2026-11-13 sweep (in a CTE, a subquery, an INSERT, CASE, COALESCE, a join, nested twice,
  DISTINCT, an index, a window, lower case, beside a Script tag).
