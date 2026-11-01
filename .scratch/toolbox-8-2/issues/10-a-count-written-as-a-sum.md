# A count written as a SUM converts to count_rows

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Found by round one (E1-1, E1-3): converting `SUM(CASE WHEN c THEN 1 END)`, the way Copilot and
most hand-written Hive count the rows where a condition holds, stops on the Toolbox's own
refusal, "sum_of(1) was given 1 where a column goes". Each converter mended it by hand to
`count_rows(where=...)`.

## Done when

- A SUM over a CASE with one WHEN, no ELSE and THEN 1 converts to `count_rows(where=...)`.
- Inside `COALESCE(..., 0)` it gives the same rows, and the scan says what it became.
- Bare, the scan also says it gives 0 where the SUM gave NULL, for a group with no such row.
- Tests in `tests/test_conversions.py` hold each.

## Answer

`Converter.aggregate` writes a SUM over a CASE of one WHEN, no ELSE and THEN 1 as
`count_rows(where=...)` through `count_where`, which notes a changed finding, and says it gives 0
where the SUM gave NULL unless it is inside `COALESCE(..., 0)`. `tests/test_conversions.py`
holds both shapes' scans, and the COALESCE shape's rows against the original's.

## Review

- Standards: `said`/`filled` renamed `finding`, and the COALESCE test is
  `_is_filled_with_zero`, which also checks the SUM is COALESCE's first value; `name` held once
  per branch. Spec: the COALESCE test now asserts its scan carries no "gives 0" warning.
- A windowed `SUM(CASE WHEN c THEN 1 END) OVER (...)` goes through `windowed`, not
  `aggregate`, and is unchanged: outside this ticket, which names the grouped form.
