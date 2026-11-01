# A CTE of rows typed in keeps its Key

Type: task
Status: resolved
Blocked by: 05
Size: S

## Question

Found by round two (E2-1, E2-2): Copilot writes a summary's typed-in group values, such as
the teams a workbook lists, as a CTE of rows typed in, `SELECT 'data' AS team UNION ALL ...`,
so a group with no data keeps its row. A Conversion keeps that CTE as an Unchecked derived
table with no Key, so the write keyed on team is refused; one converter opted out with
unproven_key=True, one named key= on the derived table by hand.

## Done when

- A CTE that only lists rows typed in, each its first column's value once, keeps that column
  as its Key; rows that differ only in later columns keep every column; rows that repeat keep
  none. Held by tests in `tests/test_conversions.py`.

## Answer

`Converter.add_cte` writes `key=[...]` on the `unchecked_derived(...)` of such a CTE, from
`_key_of_rows_typed_in`, which reads its rows with `_rows_typed_in`. The write keyed on the list
is let through with no opt-out; a list whose rows repeat has no Key, as before.

## Review

- Spec: a parametrized test holds each case: the first column alone, every column when only
  a later one differs, none when rows repeat, and none for 1 and 1.0, which `_compared_as_hive`
  writes one way, as Hive compares them. The tests read the logic cell's text, not the
  notebook's JSON.
- Standards: the stand-in warehouse's `_value_of` is plain ifs, takes a negative number, and
  refuses anything not typed in; `_rows_typed_in`'s docstring says its values are Python source.
