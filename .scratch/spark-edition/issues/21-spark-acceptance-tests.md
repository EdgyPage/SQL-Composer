# Spark acceptance tests: Spark's own parser, literal read-back, and real writes on Linux

Type: task
Status: resolved
Blocked by: 04, 20

## Question

The printer is held to sqlglot by the goldens; hold the text to Spark itself too. In
`tests/spark_edition/`, with an in-process session fixture used only there:

- parse every golden text, with `spark.sql.ansi.enforceReservedKeywords` on and off;
- analyse and run every corpus SELECT on the Example tables, with ANSI on and off;
- read back every escaping case with a SELECT;
- check each shared argument-count row against Spark's `WRONG_NUM_ARGS`, and the backtick list
  against Spark's keywords;
- assert each declared row's behaviour (NULLIF gives NULL on a zero divisor under both ANSI
  settings).

A Linux-only Hive-support fixture keeps Derby and the warehouse in `tmp_path` and checks:

- `create_table` makes an ORC table (its serde shows in `DESCRIBE FORMATTED`); `create_table`
  twice refuses, and `may_exist=True` doesn't;
- `INSERT_OVERWRITE` twice leaves every other day alone; `INSERT_INTO` appends;
- `drop_table` twice is a no-op;
- `write_table_reference`, `check_table_reference` and `check_key` work on real `DESCRIBE` and
  `SHOW PARTITIONS` output, including a `%Y/%m/%d` partition and a NULL day;
- every corpus SELECT gives the same frame on real Hive tables as on the Example database.

Until ticket 25, a strict xfail names the row each failing test waits for.

## Done when

The Definition of done in `CLAUDE.md` holds; green in CI at both pyspark ends; the Hive-support
tests skip on Windows with their reason shown; nothing is written outside `tmp_path`.

## Answer

Two test modules hold the Toolbox's Hive to Spark itself (`95a1804`; reworked in `ab24181`,
`c152466` and `31b1161` after the code review). Both use a Spark in pytest's own Python, built
by `tests/spark_edition/in_process_spark.py`, set up as the Example database's is, with every
file it writes in pytest's temporary folder.

- **`test_spark_reads_the_hive.py`**, on Windows and Linux, with the in-memory catalog:
  - **Parsing.** Spark parses every piece of Hive in both goldens: each Statement's Hive, and
    each command a warehouse case sent. It tries each with ANSI off, with ANSI on, and with ANSI
    on and keywords enforced. SQL Composer's JSON and UUID types are strict xfails naming
    ticket 25.
  - **Running.** Every query in Spark Composer's golden runs with ANSI on and off: 320 queries,
    on the Example database's tables with their rows, and on the corpus's own tables, empty. The
    one on `mart.daily_runs` runs only on Linux, since Spark can't make a database on Windows
    without winutils.
    - Spark refuses one query, as it should: `date_format`'s pattern `YYYY-MM`, written as
      given, gives DATETIME_PATTERN_RECOGNITION. The test expects it and says why: sqlglot's
      rewrite to `yyyy` changes the pattern's meaning, the hive_function row's point.
  - **Reading back.** Every value the Toolbox writes, and every name, reads back as itself.
    contains and starts_with match 6 texts against 13 hard values as Python would.
  - **hive_function's shared list.** Spark has each function, and takes each count of arguments
    its row lets through. Each function the list calls an aggregate gives one row for three.
  - **Backticks.** Two strict xfails name ticket 25: every word Spark reserves under ANSI, and
    every word its defaults won't take as a table's name (anti, semi, minus...), must be written
    in backticks.
  - **The declared rows.** NULLIF gives NULL where Spark would stop on a zero divisor, the
    float row's two numbers are a DECIMAL and a DOUBLE, hive_function's NVL runs as written,
    and Spark has neither JSON nor UUID.
- **`test_spark_hive_tables.py`**, on Linux only, with Hive support, its metastore (Derby) in
  the temporary folder. Each Statement goes through `lambda hive: spark.sql(hive).toPandas()`:
  - create_table makes an ORC table, refuses the second time, and doesn't with may_exist;
  - the Saved-table Worked example's steps:
    - INSERT_OVERWRITE replaces only its day, row for row, sent once or twice;
    - INSERT_INTO adds to its day;
    - a week_start goes into a string column;
  - drop_table sent twice does nothing the second time;
  - write_table_reference, check_table_reference and check_key read a `%Y/%m/%d` day and a row
    with no day;
  - every golden query runs on real tables, and each on the Example database's tables gives the
    rows it gives.
- **Beside the tests:**
  - `pyproject.toml` ignores the two warnings the spike found pyspark raising in pytest's own
    Python, and pytest shows every skip's reason.
  - Off Windows, the Example database's Spark gives its launcher's Java `-XX:-UsePerfData`, so
    a start leaves nothing in /tmp.

**The Done-when, as it held:**

- **Green at both pyspark ends on Linux.** A throwaway branch ran both Spark jobs (run
  36745530341): 2807 passed at 3.5.0 and at 4.0.4. The 6 xfails are strict and name ticket 25,
  and the 4 skips are Windows-only tests. `dev`'s own CI runs them from now on.
- **The Hive-support tests skip on Windows with their reason shown.** "Spark can't make a
  database on Windows without winutils, so this runs on Linux, as in CI".
- **Nothing is written outside tmp_path.** That run listed /tmp and the repo before and after:
  the only new thing was pytest's own folder.

**Not done, and why:**

- **SQL Composer's golden is parsed, not run.** Its Hive is written for Hive, where a division
  by 0 gives NULL. With ANSI on, Spark stops on the same text, which is the division row's
  point.
- **9 queries read only the corpus's own tables, which are empty.** For them, only an error in
  reading the query can show, not one in running it.
- **The ResourceWarning filter applies to the whole suite.** Python gives that warning when a
  socket is collected, in whichever test is running then, so a module can't hold it. The review
  checked that it hides no socket of the Toolbox's own: those are multiprocessing Connections,
  which close without a warning.

## Comments

**Code review (2026-09-30), `95a1804` and `ab24181`.** No hard violation.

- **Fixed in `c152466`:**
  - The backtick check read only ANSI's reserved words, so it would have passed without anti,
    minus and semi. It now also reads the words Spark's defaults won't take as a table's name.
  - The argument check counted a function Spark doesn't have as taking its arguments. It now
    checks the function exists.
  - The declared-row tests read their rows.
  - INSERT_OVERWRITE's day is compared row for row.
  - One rule for Windows' missing databases.
  - A golden's Hive carries its case and part.
  - Clearer names, and skip reasons shown.
- **Fixed in `31b1161`:** the helper imports pyspark, so it moved into `tests/spark_edition/`, as
  `tests/repo/test_suite_layout.py` requires.
- **Answered, not changed:**
  - The helper's folder list mirrors the Example database's, which its settings need.
  - `-XX:-UsePerfData` is written where each Java starts, each with the reason there.
  - `_FOLDER` holds the one folder, since a session-wide fixture would need a conftest in
    `tests/spark_edition/`, and two conftests would share one module name.

**Drift reviews.** `ab24181` was clean; the rest touched only tests.

**Beginner reader:** not run. Nothing a beginner sees changed.
