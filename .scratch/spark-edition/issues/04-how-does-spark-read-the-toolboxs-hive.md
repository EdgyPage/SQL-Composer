# How does Spark read the Toolbox's Hive, and which Hive claims hold on Spark?

Type: research
Status: resolved
Blocked by: 02, 03

## Question

The PySpark edition sends the same Hive text through `spark.sql()`. Establish, with a throwaway
script against pyspark 3.5.0 and 4.0.4, with ANSI on and off and
`spark.sql.ansi.enforceReservedKeywords` on and off:

- whether Spark's parser accepts every text in the golden corpus (ticket 3), including
  `WITH ... INSERT OVERWRITE TABLE ... PARTITION(...) SELECT` and `CREATE TABLE ... STORED AS ORC`
  under Hive support;
- whether every escaping case in `tests/escaping_cases.py` reads back to the value written,
  including BEL, FF, VT, BS, NUL, SUB, `%`, `_` and LIKE's backslash;
- the result types of DATE_ADD, NEXT_DAY(..., 'MO'), TRUNC(..., 'MM'), UNIX_TIMESTAMP and
  FROM_UNIXTIME on STRING partitions (including `yyyyMMdd`), and of `CAST(... AS STRING)` around
  them;
- `x / 0` against `x / NULLIF(0, 0)` under both ANSI settings;
- the type of the literals `0.5` and `0.5D`;
- Spark's reserved and strict keywords against `HIVE_RESERVED` (`sql_composer/tables.py:42-55`);
- `WRONG_NUM_ARGS` for each candidate row of the shared hive_function argument table;
- what `spark.sql.parser.escapedStringLiterals=true` does to the text.

Also build a claims table: every docstring sentence and refusal "why" that states Hive
behaviour, whether it holds on Spark, and a wording true of both. Known so far:
`refusals.py:45` and `:80` (Hive's `_c0`), `clauses.py:137-138` (NULL on divide-by-zero),
`clauses.py:437` (grouping by a SELECT name), `refusals.py:358-363` and `clauses.py:493-495`
(sorting on one machine), `clauses.py:569` (Hive under Tez), `tables.py:1027-1028`
(AlreadyExistsException), `calculations.py:222-223`, and `example_database.py:3-7`.

## Done when

A findings file on a `research/spark-reads-hive` branch, named in a `Findings:` line here, gives
each probe's result for each version and setting, marks each 3.0 change (ticket 25) and each
argument-table row as needed or not with evidence, and gives every claim a proposed wording. It
is linked from tickets 14 and 25.
Findings: [findings/04-spark-reads-the-hive.md](../findings/04-spark-reads-the-hive.md)

## Answer

Measured on Windows 11 with pyspark 3.5.0 and 4.0.4, with ANSI on and off and
`enforceReservedKeywords` on and off.

- **Spark's parser** takes every golden text in every mode and version, `WITH ... INSERT` and
  `STORED AS ORC` included, except `create_table` with type `json` or `uuid`
  (UNSUPPORTED_DATATYPE).
- **Escaping:** every escaping case reads back as written except BEL, FF and VT, which come back as
  the letters a, f and v. That confirms the 2.1 refusal. With `escapedStringLiterals=true` no
  value escapes its quotes, but every backslash is kept, so it goes in the README's settings check.
- **Dates:** NEXT_DAY, TRUNC and DATE_ADD return DATE, and under ANSI a DATE mixed with a string
  such as `'none'` raises. `CAST(... AS STRING)` gives Hive's string in every mode.
- **Division:** `x / 0` and `x / y` with y = 0 raise DIVIDE_BY_ZERO under ANSI;
  `x / NULLIF(y, 0)` gives NULL in every mode.
- **Literals:** `0.5` is DECIMAL on Spark (DOUBLE on Hive); `0.5D` and `1e-05` are DOUBLE.
- **Reserved words:** 28 words outside `HIVE_RESERVED` need backticks on Spark; backticks fix
  every one in every context. Five of them (`any`, `except`, `minus`, `current_user`,
  `recursive`) already break SQL Composer's own `to_hive` today.
- **Argument counts:** WRONG_NUM_ARGS doesn't change with ANSI. Between versions only lag, lead,
  like and mode differ. The findings give a shared row for each candidate function.

**All four 3.0 changes (ticket 25) are needed,** with the evidence in the findings' "3.0 changes"
section. That section also gives the exact CAST text, the 28 words, the strict type list and the
shared argument rows. **The claims table** gives every Hive claim in the shared files a wording
true of both engines, for ticket 14.

The throwaway probe scripts stayed in the scratchpad, as ticket 02's did. The findings file is
committed on `dev` beside ticket 02's instead of on a `research/spark-reads-hive` branch, so the
tickets that cite it can link it.

## Comments

**Defaults chosen for what the research found but no ticket decided (2026-09-29).** These are
recorded in the map's Notes for the user to change:

- **A float literal** is written by the PySpark edition as a DOUBLE (`0.5D`), so a result is a
  float in pandas as on Hive. This is a third declared difference (ticket 17), and SQL
  Composer's Hive stays as it is.
- **A literal zero divisor** also gets `NULLIF`: the division row covers every divisor that
  isn't a non-zero number (ticket 17).
- **Window functions through `hive_function`** (lag, lead, rank, dense_rank, ntile, row_number,
  cume_dist, percent_rank, nth_value) are refused by the shared list, since `hive_function` can't
  write OVER (ticket 25).
