# Ship both Editions as 3.0

Type: task
Status: open
Blocked by: 23, 25

## Question

Export both folders to `main` together, as 3.0.

- `EXPORTED` becomes every Edition, with a test.
- `docs/clean-branch-readme.md` covers both Editions: which folder to copy and what each needs
  (each range sentence tested against its `engine.py` constants); one set of runnable examples,
  run as doctests in both runs, with the line "with Spark Composer, write `spark_composer`
  wherever this page writes `sql_composer`"; a block showing
  `send=lambda hive: spark.sql(hive).toPandas()`; the Spark settings the text relies on (ANSI,
  `escapedStringLiterals`, `enforceReservedKeywords`) and the ACID caution, for a one-time check
  by hand; a generated section on where the two Editions' Hive differs; a gallery paragraph per
  Edition; and "copy a whole folder".
- Raise TOOLBOX_VERSION to "3.0" in every `.py` of both folders, quoting the user's decision of
  2026-09-29 (ticket 01).
- A `## 3.0` section in `CHANGES.md`, copied verbatim to both folders.
- A line on Editions in `.claude/agents/beginner-reader.md`.
- Close the folded version items, then run the export once.

## Done when

- Both runs and all four CI jobs pass on the exported commit.
- The code review has run with this ticket as its spec, and no drift item is open.
- The beginner reader has read the README and the cheat sheet as a sqlglot user and as a Spark
  user, and its report is linked.
- `main` holds exactly `.github/README.md`, `sql_composer/*` and `spark_composer/*`, stamped
  "<product> 3.0, exported <same time>", as one commit on top of 955dafd.
- The user pushes `main`, copies `spark_composer/` at work, and runs the README's first
  Statement with `send=lambda hive: spark.sql(hive).toPandas()` on a table they already query.
