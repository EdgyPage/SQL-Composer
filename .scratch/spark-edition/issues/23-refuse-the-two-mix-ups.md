# Refuse the two mix-ups a Spark user will make

Type: task
Status: resolved
Blocked by: 16

## Question

Two mistakes become easy once both folders sit side by side, and today each fails with a message
that doesn't say what went wrong.

1. **An object made by the other Edition's folder**, such as a Table reference whose Level 0 file
   imports `sql_composer` passed to `spark_composer`'s FROM. Today it fails `isinstance`
   (`sql_composer/clauses.py:254`) or is called "not a single value" (`tables.py:415-423`).
   Detect it by its class's module being another `*_composer` package, written without that
   package's name so the swap can't corrupt it. Check at every isinstance entry point:
   `clauses.py:148-254`, `conditions.py:127`, `calculations.py:34-50`, `tables.py:408-423` and
   `running.py:254`.
2. **A send that returns a Spark DataFrame** (`send=spark.sql` without `.toPandas()`). Today
   `run` skips the row Load limit because the result has no `__len__`
   (`sql_composer/running.py:298`), and `_describe`, `_newest_partition_value` and `check_key`
   fail with a raw AttributeError or TypeError. Detect it by its type's module, in `run`
   (`running.py:296-299`), `_describe` (`tables.py:707-710`), `_newest_partition_value`
   (`tables.py:731-733`) and `check_key` (`tables.py:905-907`). The usual fix: end your send with
   `.toPandas()`.

Both are shared four-part refusals with no opt-out, tested in both runs with fake classes.

## Done when

The Definition of done in `CLAUDE.md` holds, including the beginner reader over both messages; a
CHANGES 3.0 draft line is written.

## Answer

Both mix-ups are refused with a four-part message, with no opt-out, in the shared
`refusals.py` (`66cb063`; reworked in `ca35622`, `74ac43b`, `9d0e97d` and `6e50afa` after the
reviews and the beginner reader).

- **An object the other Edition's folder made.** `refuse_what_the_other_edition_made` knows each
  folder by the module its object's class is in, and the shared text names neither Edition. An
  object is taken for the other Edition's when its folder ends in `_composer` and isn't this one.
  - It is asked wherever the Toolbox checks what it was given, before any refusal that would
    call the object the wrong kind of thing:
    - FROM, JOIN and its ON, all_columns, SELECT, AS, WHERE, GROUP_BY and ORDER_BY;
    - statement, derived, the conditions and the calculations;
    - a value in a condition, arithmetic between columns;
    - to_hive, by_day, export_lineage and the table checks.
  - The message calls the object what a user calls it: a Table reference, a Derived table, a
    column, a condition, a clause, descending(...) or a Statement. It says which folder made
    it and that the function was called from this one. Its fix gives both ways, whichever
    folder the notebook uses: change the notebook's import, or the one in the file the object
    came from.
- **A send that gives back Spark's own DataFrame.** `refuse_a_spark_dataframe` knows it by a
  `toPandas` on its class, so the shared text names no library, and a pandas frame with a
  column of that name is taken.
  - It is asked wherever the Toolbox reads what a send gave back: `run` for a read, DESCRIBE's
    reader and SHOW PARTITIONS' reader. So write_table_reference and check_key refuse, and
    check_table_reference reports it.
  - A write's frame is given back unrefused, since Spark has carried out the write by the time
    its send returns. Refused, it would be sent again, and INSERT_INTO would add its rows twice.
  - The fix to paste is `send=lambda hive: spark.sql(hive).toPandas()`, which `run`'s docstring
    now gives too.
- **Tests.** `tests/test_mix_ups.py` fakes both, so both runs test every place above.
- **CHANGES.** The Spark DataFrame refusal is under 2.1, since a 2.1 re-export ships it. The
  other folder's object is in `.scratch/spark-edition/changes-3.0-draft.md`, which ticket 26
  folds into CHANGES.

**Not done, and why:**

- **The Spark DataFrame is known by `toPandas`, not by its module's name,** which the spec
  asked for. The shared files may not name pyspark (`tools/editions.py`,
  `FORBIDDEN_IN_SHARED`), and `toPandas` catches Spark Connect's DataFrames too.
- **An object is the other Edition's when its folder's name ends in `_composer`.** The spec
  asked that neither name be written in the shared files, and a third folder with that ending
  is unlikely beside these two.

## Comments

**Code review (2026-09-30), `66cb063`.** No hard violation beyond these, now fixed.

- **Fixed in `ca35622`:**
  - `run` refused a write's frame after Spark had carried the write out (also D67).
  - Arithmetic between columns wasn't checked, nor was all_columns.
  - The message named classes (a Named, a Ordering) and sent every kind to a Table
    reference's file.
  - The why said the Editions write different Hive.
  - The Spark DataFrame refusal named commands the user never sent, and `hasattr` on a pandas
    frame read its columns.
  - The CHANGES draft misstated check_table_reference.
  - The mix-ups' section header left the Load limits' empty (D68).
- **Answered, not changed:**
  - The two refusals keep names outside the Guard and Load limit families: they are misuse
    TypeErrors, as the modules' other type checks are, and `tests/test_mix_ups.py` holds them.
  - The `_composer` ending: see above.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D67-D69 | `66cb063` | `ca35622` |
| D70 | `ca35622` | `74ac43b` |
| D71 | `74ac43b` | `9d0e97d` |
| D72 | `9d0e97d` | `6e50afa` |

`6e50afa` was clean. D70 to D72 each caught the fix naming the wrong kind of object or file. It
now names the object's kind and says to change the line in the file it came from.

**Beginner reader:** [report](../reports/23-beginner-reader.md), read at `66cb063`. The reader made
both mistakes for real, with a local SparkSession and a Table reference file importing the other
folder.

- **Changed:**
  - Stop 10 (the costliest): after `run(drop_table(...), send=spark.sql)` the refusal claimed
    nothing had run, and following its fix would have sent a write twice. A write is no longer
    refused.
  - Stop 4: the fix now gives both ways, and never sends the reader to rewrite every generated
    Table reference.
  - Stops 5 and 6: user words replace class names.
  - Stop 7: the call is named once.
  - Stop 8: all_columns now refuses where the mix-up happens.
  - Stops 9 and 11: the Spark refusal names no command the reader didn't send, and gives the
    lambda to paste.
  - Stop 2: `run`'s docstring says send gives back a pandas DataFrame, and what it is on Spark.
- **Answered, not changed:**
  - Stop 3: the message now says "folder", not Edition.
  - Stop 12: check_table_reference reports rather than refuses, as its docstring promises.
