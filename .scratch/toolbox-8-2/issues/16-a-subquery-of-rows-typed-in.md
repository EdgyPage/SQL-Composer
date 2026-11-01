# A subquery of rows typed in converts as a CTE of them does

Type: task
Status: open
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
