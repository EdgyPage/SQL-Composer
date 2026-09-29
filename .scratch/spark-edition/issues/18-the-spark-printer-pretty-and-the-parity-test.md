# The Spark printer, pretty: Statements, CTEs, writes, DDL, and the parity test

Type: task
Status: open
Blocked by: 17

## Question

Port sqlglot 30.19.0's pretty layout, the one `to_hive` prints: `too_wide`, `format_args`,
expressions, connectors, brackets, CASE, IN, windows, SELECT, the query modifiers, WITH, INSERT
with its PARTITION, CREATE with its properties, DESCRIBE and SHOW. Each helper names its sqlglot
origin in a comment.

- Generate `tests/hive_corpus/spark_composer.txt` in the Spark run. It is staleness-tested there
  and needs no Java.
- `tests/repo/test_edition_parity.py` diffs the two goldens by case id and allows only
  `DECLARED_DIFFERENCES` rows. Each row holds a key, a plain-words why, an example pair and the
  case ids it explains, and every listed case must really differ, so a row can't go stale.
- A test holds `LAYOUT_MIRRORS_SQLGLOT` equal to the sqlglot pin in `requirements-dev.txt`, so
  raising the pin forces the printer update in the same change.
- Move the shared asserts that show a declared row into per-edition files:
  `tests/test_statements.py:84`, `tests/test_lineage.py:317-324`, and the hive_function rewrite
  asserts.

## Done when

The Definition of done in `CLAUDE.md` holds; the parity test passes; every shared exact-text test
and text-only doctest passes in the Spark run, and only Example-database tests skip, with their
reason; the default run is green.
