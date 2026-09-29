# Split the suite into shared, sqlglot-edition and repo tests

Type: task
Status: claimed
Blocked by: 07

## Question

Most tests are about the Toolbox's behaviour and will run against both Editions. Some are about
sqlglot itself, and some are about the repo. Separate them:

- `tests/sqlglot_edition/` takes what only the sqlglot edition can pass:
  `test_escaping_cases.py`; `test_escaping_toolbox.py:81-85`, `:117-154` and `:209-245`;
  `test_example_database.py:56-59` and `:118-136`; `test_statements.py:160-162`;
  `test_worked_example_regrouping.py:42-45` and `:58-75`;
  `test_worked_example_latest_and_top_n.py:60-65`; `test_example_gallery.py:182-187` and
  `:271-273`; `test_import_self_check.py:181-251`.
- `tests/repo/` takes the repo-level tests (hooks, export, pointers, levels, toolbox checks),
  with their `ROOT` fixed. They run once, in the default run.
- Edition-only files get unique basenames (`test_sqlglot_*.py`, `test_spark_*.py`), with a repo
  test that every basename under `tests/` is unique (pytest's prepend import mode refuses
  duplicates).
- `pytest_ignore_collect` skips the other Edition's folder, and a `UsageError` stops a run that
  names it explicitly.
- A repo test checks that shared tests import neither sqlglot nor pyspark.

## Done when

The Definition of done in `CLAUDE.md` holds, the total test count is unchanged (moved, none lost),
`grep -l sqlglot tests/*.py` finds only prose, and pytest is green at both sqlglot ends.
