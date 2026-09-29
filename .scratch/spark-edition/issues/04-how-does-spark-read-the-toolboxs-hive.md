# How does Spark read the Toolbox's Hive, and which Hive claims hold on Spark?

Type: research
Status: open
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
