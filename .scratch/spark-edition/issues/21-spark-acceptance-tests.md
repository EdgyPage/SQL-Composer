# Spark acceptance tests: Spark's own parser, literal read-back, and real writes on Linux

Type: task
Status: open
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
