# Run the suite against `spark_composer`

Type: task
Status: claimed
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

In `tests/conftest.py`, add `"spark"` to `EDITION_CHOICES`, whose keys then match
`EDITION_FOLDERS`: fold the two into one table of each `--edition`'s Edition and test folder, so
adding an Edition is one edit (ticket 08's review).

## Done when

The Definition of done in `CLAUDE.md` holds; `python -m pytest --edition spark` collects with no
errors and the alias tests pass; every remaining failure is an assertion failure, listed in this
ticket for tickets 17-19; the default run is green at both ends.

## Answer

`python -m pytest --edition spark` runs the shared tests against Spark Composer.

- **The alias.** `editions.use(SPARK_COMPOSER)`, called from `pytest_configure` before any
  Toolbox import:
  - refuses if `sql_composer` is already imported;
  - sets `sys.modules["sqlglot"] = None`;
  - aliases `sql_composer` and each of its modules to Spark Composer's;
  - puts a finder first on the import path that refuses any other `sql_composer.*` module.
- **The conftest.** It holds one table of each `--edition`'s Edition and test folder.
- **Guard tests.** `tests/spark_edition/test_spark_alias.py` fails if `sql_composer` isn't Spark
  Composer, if sqlglot can be imported, or if an unaliased module loads.
  `test_spark_independence.py` imports every Toolbox module, Worked example and tool, then fails
  on any module loaded from `sql_composer/` or from sqlglot.
- **The tools.** `tools/example_gallery.py` and `tools/hive_corpus.py` take `--edition spark` when
  run, and take the folder, the product and the golden's path from the package they import.
  SQL Composer's gallery and golden are unchanged.

**Not yet met: "collects with no errors".** Four shared test modules build Hive while they load,
and Spark Composer's writer was still a stub, so the Spark run stopped at collection. The alias
tests themselves pass. Ticket 17's writer is what the collection needs, and it comes right after,
with the run's remaining failures listed there.
