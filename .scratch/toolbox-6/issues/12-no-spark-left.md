# No Spark left in the code

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

The user (2026-10-20), while ticket 05 started: "Remove all mentions of spark in the code for
consistency". Ticket 02 removed Spark Composer, but the one Toolbox still spoke of Spark: in
docstrings and refusals, in two refusals made only for Spark, in the how-tos, the README's "If
your send runs the Hive on Spark", the Example projects' READMEs, the tests' names, and the
offline policy's pyspark guards.

## Done when

- No file a user copies or reads (the Toolbox, its pages, the how-tos, the README, the Example
  projects and the Templates), and no test or tool, names Spark; what records history keeps it
  (CHANGES.md, the ADRs, the dated offline audit, CLAUDE.md's and the drift reviewer's pointer to
  the tag `last-spark-composer`, and the tracker).
- What only Spark needed goes: the refusal of a Spark DataFrame from a send, the refusal of the
  table properties Spark keeps for itself, the README's Spark section, and the offline policy's
  pyspark and Spark-setting guards. What still serves Hive stays, reworded: the reserved words
  kept in backticks, `week_start` and `month_start`'s CAST to text, the aggregates' list, and
  reading DESCRIBE with the table properties on one line.
- CHANGES.md's 6.0 says what a user loses.
- The pytest run passes, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-20 on branch `toolbox-6/12-no-spark`.

- The Toolbox: every docstring, comment and message that said "Hive and Spark" says Hive;
  `refuse_a_spark_dataframe` and `SPARK_RESERVES` are gone with their tests; Spark-only advice
  (CASCADE, DROP PARTITION with `<`, the broadcast hint, column statistics, a PRIMARY KEY) is
  gone from `admin`, `clauses`, `tables` and `upkeep`; `spark-sql` in the list of programs to
  paste into became Beeline or DBeaver.
- The reserved words, the aggregates and the argument counts in `trees.py` keep their lists,
  now described as Hive's and the wider SQL's, so the Hive written is unchanged: the golden
  corpus changed only in three case names (`spark_words` became `standard_words`).
- Docs: the README's Spark section and its link, how-tos 01, 04, 10, 11, 12, 23, 27, 31-34, 36
  and 37, two Worked example Statements, both Example projects' READMEs and CONTEXT.md's Toolbox
  entry. CHANGES.md's 6.0 says which refusals went.
- Tests and tools: the offline policy drops `pyspark.sql.connect`, `pyspark.install`, the Spark
  settings in strings and `SparkSession.builder.remote` (its decision to keep them, in ticket
  02, is reversed by the user's ask); Spark-named fixtures and ids are renamed (`one_line`,
  `COMPACT_DESCRIBE`, `other_composer`).

## Reviews

- Beginner reader (2026-10-20): the refusal of a send's answer read "gave back a DataFrame,
  where a pandas DataFrame goes" for another library's DataFrame (now `kind_name` names the
  library, "a polars DataFrame", in `run` and in `write_table_reference`'s DESCRIBE, with a
  test); the ROLLUP reason, the CAST in `week_start` and `month_start`, and the is_total in
  HAVING refusal had lost their reasons (each now says its own); two long lines and a dangling
  "too" in how-tos 10 and 36 rewrapped; the README's send line reads "For example".
- Spec (2026-10-20): the grep is clean outside history. Made-up reasons fixed: "Hive has no week
  function" (Hive has weekofyear: now "no function for the Monday of a week"); the reserved
  words' last lines are other warehouses' words, not the SQL standard's; "names Hive reserves"
  became "reserved words", since the list is wider than Hive's. The is_total refusal stays: it
  serves Hive too, since without the column a subtotal row can't be told from the rows it totals.
- Standards (2026-10-20): long and orphaned lines rewrapped (`run`, `create_table`, how-tos 10
  and 37). Answered: `trees.py` loses the Spark versions its lists were checked against, as the
  user asked; the lists themselves are unchanged. The offline policy's smaller surface is the
  user's ask ("Remove all mentions of spark in the code"); pyspark isn't in requirements.txt, so
  no file of the repo can import it.
