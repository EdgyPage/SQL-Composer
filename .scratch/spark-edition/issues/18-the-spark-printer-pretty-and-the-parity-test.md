# The Spark printer, pretty: Statements, CTEs, writes, DDL, and the parity test

Type: task
Status: resolved
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

## Answer

Both Editions' goldens are committed and held to each other (`926d431`, answered in `25a02d8`).

- **The layout** came with ticket 17's writer (`ec2b4ef`), ported from sqlglot 30.19.0. Every
  function of `spark_composer/writing.py` that copies sqlglot names its origin in a comment,
  DESCRIBE and SHOW PARTITIONS included.
- **Spark Composer's golden**, `tests/hive_corpus/spark_composer.txt`, holds the same 380 cases
  as SQL Composer's, written with `python tools/hive_corpus.py --edition spark` and no Java. Two
  cases are new in both, a wide IN list and a wide STRUCT, the layouts no case pinned.
- **No Java for the golden.** The gallery tool found a Worked example's Statement functions by
  calling each one, and `every_run()` in latest_and_top_n and regrouping runs a query, which on
  Spark needs the Example database. The Example database's send now refuses while the tool
  looks, so a function that sends is passed over unrun.
- **One corpus test for both Editions**, `tests/test_hive_corpus.py`, in place of the sqlglot
  one; `hive_corpus.cannot_write()` says why a Python can't write its Edition's golden.
- **`tests/repo/test_edition_parity.py`:**
  - both goldens hold the same cases in the same order;
  - a case may differ only if a row of `DECLARED_DIFFERENCES` lists it, and each listed case
    must differ;
  - each row's example is two different texts, found in one of its cases, each in its Edition's
    golden;
  - with what Spark Composer adds left out (NULLIF, the D of a float: `hive_corpus.py
    --as-written`), its corpus is SQL Composer's in every case but those a row that adds nothing
    lists, so the NULLIF and float rows waive nothing else in their cases;
  - `LAYOUT_MIRRORS_SQLGLOT` equals the sqlglot pin.
- **`DECLARED_DIFFERENCES`** rows are `Difference(why, sql_composer, spark_composer, cases,
  spark_composer_adds)`: division (2 cases) and float (2), which Spark Composer adds;
  hive_function (6); and, until 3.0, create_table's types (4) and hive_function's arguments (1),
  which ticket 25 takes out. The whys are in plain words for ticket 26's README section.
- **Not moved:** the shared asserts that show a declared row stay shared, with
  `in_this_edition`, so both Editions still run them (recorded in ticket 17).

The Spark run's failures all wait for ticket 22's gallery, and every skip is an Example
database test with its reason. The default run is green at both ends.

## Comments

**Code review (2026-09-29), `926d431`.**

- *Standards:*
  - **Fixed:**
    - The ticket-25 cases were a second list outside `DECLARED_DIFFERENCES`; they are rows now.
    - The `_call` comment was ungrammatical; the docstring claimed every helper names its origin.
    - The division why didn't show `x / y`.
    - The docstring's merged line.
    - `_golden` rebuilt the path and split the format that `hive_corpus.py` owns; it has
      `golden_path` and `cases_in` now.
    - The example was an ordered tuple; it is two named fields.
    - `SQL` and `SPARK` are `SQL_GOLDEN` and `SPARK_GOLDEN`.
  - **Answered, not changed:**
    - The rows' whys and the writer's docstring both explain the three differences. The rows are
      the one declaration, which the test and the README use; the docstring explains its own
      output to whoever lands in it from a traceback (ticket 17's beginner reader, stops 10-12).
    - `cannot_write()` returns a reason or None, like the engines' `example_database_cannot_run`.
    - The gallery tool's patched send stays: a naming rule would miss a function that sends
      under another name, and would rename Worked example functions.
- *Spec:*
  - **Fixed:**
    - Origin comments on DESCRIBE, SHOW PARTITIONS, the one-line kinds, `_parse_type` and
      `_nested`, and `_call` names `_add_date_sql`.
    - No case pinned a wide IN list or a wide STRUCT; two cases do now.
    - A listed case was a blanket waiver: an extra difference, a case under the wrong row, or an
      example that isn't a difference all passed. The as-written comparison and the example
      check make each fail; probed on a Div layout change outside NULLIF (17 cases fail).
    - The hive_function row's why didn't cover date_format, where sqlglot writes 'YYYY-MM' as
      'yyyy-MM', which means something else.
  - **Answered, not changed:** a hive_function case and a ticket-25 case can still differ in more
    ways than their row says; neither Edition can be mapped onto the other's spelling there.

**Drift reviews.** `926d431`: D43 and D44, both closed by `25a02d8`. `25a02d8`: D45, closed by
`95eeb6c`: two rows hold refusals, so a declared difference is said to be in what each Edition
shows, its Hive or its refusal.

No beginner reader: nothing a beginner sees changed. The rows' whys reach a beginner only
through ticket 26's README, whose beginner reader reads them.

