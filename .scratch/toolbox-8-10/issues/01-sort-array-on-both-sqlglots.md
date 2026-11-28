# SORT_ARRAY on both sqlglot shapes, and a CI job at 30.34.0

Type: task
Status: resolved
Blocked by: -
Size: M
Spec: [specs/01-sort-array-on-both-sqlglots.md](../specs/01-sort-array-on-both-sqlglots.md)

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

## Answer

Built 2026-11-27.

- **One answer**: `engine.sort_array_class()` gives the class Hive's SORT_ARRAY reads as,
  `getattr(exp, "SortArray", exp.ArraySort)`, asked of what sqlglot holds. No other Toolbox
  file names `SortArray` (`test_only_the_engine_asks_which_array_sort_sqlglot_has`).
- **The converter** (`leave_out_sort_arrays_true`) finds that class; where it is `ArraySort`,
  it also clears `nulls_first`, so the Python holds only the Hive's own arguments. 8.7's TRUE
  and "kept" findings are unchanged.
- **The writer** (`writing._hive_with_hints`): where SORT_ARRAY reads as `ArraySort`, the
  Toolbox's Hive writes a second argument as given (`_sort_array_hive`), `SORT_ARRAY(x,
  FALSE)` as 30.23.0 writes it; anything else, a comparator included, goes to sqlglot's own
  Hive writer, which refuses a comparator in the same words on both. Done in the dialect, as
  the variances are, so `hive_function("sort_array", x, False)`, a query kept whole and
  `to_hive`'s read-back all write the same on both: `trees.py`'s arity table is unchanged.
- **The version**: `engine._PIN` (30.23.0) is new, for what the install fixes name, so no
  message a user reads changes; `_NEWEST_TESTED` is 30.34.0, for the note alone. dev's Example
  database's fix names `_PIN`. `dev.yml` runs the matrix `["30.23.0", "30.34.0"]`; CLAUDE.md's
  CI lines say so. The requirements files are unchanged.
- **Tests**, run at 30.23.0 and at 30.34.0 (a copy installed apart, first on PYTHONPATH):
  `tests/test_converting.py`, `tests/test_statements.py`, `tests/test_conversions.py`,
  `tests/sqlglot_checks/`, and of `tests/repo/`, `test_toolbox_checks.py`, `test_dead_code.py`,
  `test_standard.py`, `test_code_audit.py`, `test_offline_policy.py`, `test_local_paths.py`
  and `test_pointers.py`: all pass at both. New: `ARRAY_SORT(x)` in every SORT_ARRAY shape
  gives the same Python and findings as `SORT_ARRAY(x)`; FALSE kept in a query kept whole;
  `hive_function("sort_array", ...)` with none, TRUE and FALSE writes the same Hive; no note at
  30.23.0, 30.24.0 or 30.34.0, a note above. The 7 snapshot texts the new tests make hash the
  same at both versions, and are added to `tests/snapshot/known.txt`.
- **Where the spec's premise didn't hold**: sqlglot gives no sentence for `ARRAY_SORT(x)` read
  as Hive, at either version. Its "Hive's SORT_ARRAY only sorts ascending with NULLs first"
  comes only from sqlglot's Spark reader, which sets `nulls_first` FALSE; the Toolbox reads as
  Hive, where `ARRAY_SORT(x)` carries no NULL order. So no finding is kept for it on either,
  which is still "only plan for sqlglot": sqlglot says nothing, and neither does the Toolbox.
- **Left**: the whole suite at 30.34.0 runs on CI's new job (and on the merged branch), not
  here. A comparator, `ARRAY_SORT(x, (a, b) -> ...)`, stops `convert_query` with sqlglot's
  UnsupportedError on both versions, as before this ticket. No text a beginner sees changed,
  so the beginner reader didn't run.
