# A subquery of rows typed in converts as a CTE of them does

Type: task
Status: resolved
Blocked by: 15
Size: S

## Question

Found by the held-out round (E4-1): Copilot's Hive lists a summary's typed-in groups as a
subquery in FROM, `FROM (SELECT 1 AS job_id UNION ALL SELECT 2 ...) c LEFT JOIN ...`, and a
Conversion keeps the whole query as an Unchecked statement, "a SELECT with no FROM, which
statement(...) needs". Ticket 15 converts a CTE of the same rows into an Unchecked derived
table with its Key, the rest of the query Toolbox code.

## Done when

- A subquery in FROM or a join that only lists rows typed in converts as the CTE of those rows
  does: an `unchecked_derived(...)` named for its alias, with the Key its rows show, and the
  query around it Toolbox code. Held by tests in `tests/test_conversions.py`.

## Answer

`Converter.source` writes a sub-query that only lists rows typed in, in FROM or joined, as an
`unchecked_derived(...)` named for its alias, through `unchecked_derived_call`, which a CTE of
rows typed in now shares: the Key its rows show, as ticket 15 has it, and each column's type,
from its values, `_types_of_rows_typed_in`, None where the rows' values differ in type, such as
1 and 2.5. The query around it is Toolbox code giving the original's rows. Held by
`tests/test_conversions.py` (the list in FROM and joined; a column of mixed types). The test
ticket 13 wrote reached its kept-whole path through such a sub-query, so it is now
`test_a_query_reading_a_list_typed_in_has_its_columns_typed`, its types still told, now with
the list's Key; ticket 13's kept-whole typing has a test of its own again, a query of values
alone, under its old name.

## Review

- Standards: no hard finding. The converter's method is `unchecked_derived_call`, named for the
  Python it returns, not the function it writes; "no type" is None alone; the check for rows
  typed in is `is not None` in both places.
- Spec: the joined side is tested (an inner join: the Toolbox has no RIGHT JOIN); the types are
  asserted in the conversion's logic; a column whose rows differ in type is left untyped, not
  typed from its first row; CHANGES.md says the CTE of rows typed in gains types too; ticket
  13's kept-whole path, a query of values alone, is tested again.
