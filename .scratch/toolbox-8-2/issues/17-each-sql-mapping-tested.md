# Each SQL mapping a Conversion makes, tested

Type: task
Status: resolved
Blocked by: 07
Size: S

## Question

The goal names "enough tests to cover a decent portion of toolbox stated capabilities and sql
mappings". Over the whole suite the Toolbox is 95% covered and `converting.py`, which maps Hive
to Toolbox code, 92%: what the tests miss there is SQL a Conversion maps that no test converts
(a negative number, TRUE and FALSE, NULL, IF, IS NULL and IS NOT NULL, NOT of a condition, AND
inside OR, brackets round arithmetic, COUNT(*) OVER, FIRST_VALUE, a ROWS frame, ORDER BY a
position or a name), and SQL no Clause function writes whose reason no test reads (a RANGE
frame, JOIN USING, RIGHT JOIN, TABLESAMPLE, ORDER BY on a whole UNION, COUNT(DISTINCT a, b),
= NULL, a sub-query with no name).

## Done when

- Each mapping above is converted, on the Example database, into Toolbox code with no piece
  left Hive, giving the original's rows, in `tests/test_conversions.py`.
- Each form no Clause function writes stays Hive, its finding saying why, in
  `tests/test_converting.py`.
- A mapping the tests find wrong is fixed, or recorded here.

## Answer

`tests/test_conversions.py::test_each_mapping_is_toolbox_code_giving_the_originals_rows` converts
17 Hive forms on the Example database, each read over both days of ops.job_runs: nine runs, one
TEST, two FAILED, run 98's status NULL, durations 5 to 40, so each condition keeps some rows
and drops others (asserted) and a NULL under a NOT shows whether the conversion keeps what Hive
keeps. Each is Toolbox code with no piece left Hive, giving the original's columns and rows.
`tests/test_converting.py::test_what_no_clause_function_writes_stays_hive_and_says_why` holds the
reason of each of 8 forms no Clause function writes.

The tests found `NOT (a OR b)` left Hive: only NOT IN, IS NOT NULL and NOT a = b converted.
`Converter.negated` now writes NOT of a comparison as its opposite (`_OPPOSITES`), NOT of NOT
as the condition, and NOT of AND or OR by De Morgan, each part's opposite, through
`condition_or_unchecked`, so a part no function negates stays Hive alone, bracketed, as
`test_not_of_an_or_keeps_hive_only_for_the_part_no_function_negates` holds. Each keeps the rows
NOT keeps under SQL's three-valued logic: NOT (a > b) and a <= b are both unknown for a NULL,
and De Morgan holds for unknown too. CHANGES' 8.2 says so.

## Review

- Standards: no hard finding. `_OPPOSITES` is laid out as `_COMPARISONS` is; a part no function
  negates stays Hive alone rather than the whole NOT. The all_of/any_of writer `condition` and
  `negated` share in shape is left, as the file repeats it at each site.
- Spec: the cases read two days, with a NULL status, a TEST and SUCCESS runs either side of each
  threshold, where one day of four runs let several cases pass whatever they wrote; each
  filtering case is asserted to keep some rows and drop others; the NOT fix is recorded here.
