# CHANGES 3.0, a draft

Ticket 26 of the PySpark work writes these lines into `CHANGES.md` when 3.0 ships, in both
folders. Like `CHANGES.md` itself, they name neither folder, since both folders ship it as it is.
Each ticket that changes what a user sees adds its line here as it goes.

- **Two mix-ups are refused plainly** (ticket 23).
  - An object made by the other Edition's folder, such as a Table reference whose file imports
    it, is refused saying which folder made it and to import from one folder only.
  - A send that gives back a Spark DataFrame, as `send=spark.sql` without `.toPandas()` does, is
    refused saying to end the send with `.toPandas()`. Before, `run` skipped its row limit for
    it, and `write_table_reference`, `check_table_reference` and `check_key` stopped with
    Python's own error.
