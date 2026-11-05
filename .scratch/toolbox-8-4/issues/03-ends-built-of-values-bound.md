# An end built of values bounds a partition read

Type: task
Status: open
Blocked by: 02
Size: M

## Question

`between(dt, low, high)` bounds nothing once an end is a Column, so the partition Load limit
refuses `between(dt, date_sub(PERIOD_END, 14), PERIOD_END)`, though the read is bounded; and
`at_most(dt, script_tag(...))` bounds where `between` with the same end doesn't (map, Q4).

## Done when

- A value expression is one built only of values: literals, Script tags, Run values (05), and
  `date_sub`/`date_add` of them by a number. Any condition holding a partition column to a
  value expression bounds it, as it does a literal: `between`, `at_least`, `at_most`,
  `equals`, `is_in`, and the rest that bound today.
- An end that reads a column, a subquery or an Unchecked expression still bounds nothing.
- `between`'s "starts after it ends" refusal is checked only where both ends are plain values.
- The Hive is as the original wrote it: the bound is the Guard's knowledge, nothing is
  worked out in Python.
- 01's journey gets past the Load limit on its windows.

## Answer
Built 2026-11-05.

- **`script_tags.is_built_of_values`**: a Column built of values alone, its tree only Literals, Nulls,
  Booleans, Script tags, brackets and sums of them, and `date_add`/`date_sub`
  (`_DAYS_MOVED`) of them. It reads no column.
- **Conditions**: `_comparison` (`equals`, `at_least`, `at_most`, `greater_than`,
  `less_than`) counts such a Column as a bound where it counted a Script tag alone; `between`
  bounds when each Column end is one. An end that reads a column, calls another function or
  is Unchecked Hive still bounds nothing. Ticket 05's Run value joins `is_built_of_values` there.
- **"starts after it ends"** is refused only for two plain values: a Script tag's is Hive
  text, so which end comes first is Hive's to say.
- **The Hive** is as the original wrote it: the bound is what the Load limit knows, nothing
  worked out in Python.
- **Tests**, `tests/test_date_windows.py`: five conditions built of values bound `dt`, three
  reading a column, another function or Unchecked Hive are refused, and between's order is
  checked only on plain values. 01's journey gets past the Load limit on its windows.

## Review

Code review (with 01 and 02):

- **Fixed:** the predicate is `is_built_of_values` (and `_is_built_of_values`), its name
  saying what it holds, as `is_` names a bool; `_DAYS_MOVED` is private to `script_tags.py`.
- **Answered:** `is_in`, `is_not_in` and `last_n_days` take plain values only, so no value
  expression reaches them; `not_equals` bounds nothing, as before. Sums, NULL and TRUE/FALSE
  are values too, and say so in the docstring. The shared "value, so it bounds" line in
  `between` and `_comparison` stays two lines: a helper's name would say no more.
