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
