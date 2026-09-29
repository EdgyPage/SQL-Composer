# Refuse the two mix-ups a Spark user will make

Type: task
Status: open
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
