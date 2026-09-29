# Run the suite against `spark_composer`

Type: task
Status: open
Blocked by: 08, 15

## Question

Make `python -m pytest --edition spark` run the same shared tests, which keep
`from sql_composer import ...`, against the PySpark edition.

In `pytest_configure`, `editions.use("spark")`:

- refuses if `sql_composer` is already imported;
- sets `sys.modules["sqlglot"] = None`, so any sqlglot import fails loudly;
- imports every `spark_composer` file and aliases `sql_composer` and each `sql_composer.X` to it;
- adds a meta-path finder that refuses any other `sql_composer.*` import.

The import-stop and export tests already read the Edition's folder, product and version from
`conftest.edition()` (ticket 07), so they follow the alias; the report names the Edition it
tested. Add `tests/spark_edition/test_spark_alias.py` and
`test_spark_independence.py`, so a failed alias can never pass silently as a sqlglot run. Make
`tools/example_gallery.py` and `tools/hive_corpus.py` alias-aware: they call `editions.use`
before any Toolbox import, take module prefixes from the package name, and put the product in
page text.

## Done when

The Definition of done in `CLAUDE.md` holds; `python -m pytest --edition spark` collects with no
errors and the alias tests pass; every remaining failure is an assertion failure, listed in this
ticket for tickets 17-19; the default run is green at both ends.
