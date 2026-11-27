# SORT_ARRAY on both sqlglot shapes, and a CI job at 30.34.0

Type: task
Status: open
Blocked by: -
Size: M

## Question

sqlglot 30.24.0 removed `exp.SortArray` and gave `exp.ArraySort` `asc` and `nulls_first`, inside
the range the Toolbox says it supports (30.19.0 up to 31). Make the Toolbox give the same Hive
and the same findings on both (round 1, Q1 and Q2; round 3, Q1 to Q3; the map's "SORT_ARRAY and
ARRAY_SORT" note and its measured cost under round 2).

## Done when

- **"Which shape" is answered once**, in `engine.py`, by whether sqlglot has `exp.SortArray`,
  never by its version number; the places below ask it.
- **`Converter.leave_out_sort_arrays_true`** (`converting.py`) finds `ArraySort` where
  `SortArray` is gone. On 30.24+ Hive's `SORT_ARRAY(x)` reads as `asc` None and `nulls_first`
  TRUE, and `SORT_ARRAY(x, TRUE)` as `asc` TRUE; the TRUE is left out with 8.7's finding, as
  today.
- **`SORT_ARRAY(x, FALSE)` is kept as written** on both, with 8.7's "kept" finding: on 30.24+
  it is written as text, since sqlglot refuses it under the Toolbox's `ErrorLevel.RAISE`
  ("Hive's SORT_ARRAY only sorts ascending with NULLs first").
- **Spark's `ARRAY_SORT(x)`** becomes `SORT_ARRAY(x)` on both, and on 30.24+ sqlglot's own
  sentence is kept as its finding; no finding of the Toolbox's own ("only plan for sqlglot").
- **The Python a Conversion writes** for the node leaves out `nulls_first`, so
  `hive_function("sort_array", ...)` holds no `True` it didn't have.
- **`hive_function("sort_array", x, False)`** (`trees.py`'s arity table) writes on both.
- **CI**: `.github/workflows/dev.yml` runs a second job at sqlglot 30.34.0; `engine.py`'s
  `_NEWEST_TESTED` is 30.34.0, so the "newer than tested" note stays quiet up to it. The pin
  stays 30.23.0, and `requirements.txt` and `requirements-dev.txt` are unchanged.
- **Tests**: the SORT_ARRAY tests of `tests/test_converting.py`, `tests/test_conversions.py`
  and `tests/test_statements.py` pass at both sqlglot versions; a test of `ARRAY_SORT(x)` read
  as Spark-flavoured Hive. Checked locally at 30.34.0 the way the map's measurement was (the
  suite in a copy, against the same copy at 30.23.0), since `.venv` holds the pin.
