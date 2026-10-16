# The admin module

Type: task
Status: resolved
Blocked by: 02, 03
Size: M

## Question

Map family 4 and ADR 0006. `from sqlglot_composer import admin` (not in the star import):
`drop_table` (moved from the ordinary names), `drop_days(t, before=)`, `add_columns(t, send=)`,
`set_properties(t, ...)`, `move_to_own_folder(t, send=)`. Each an ordinary Statement, its
description (what it changes, what can't be undone) printed by show_hive before its Hive, refused on a table that isn't one
of the user's Saved tables, logged in the Admin log when run. A how-to, "Move a Saved table to its
own folder".

## Done when

- Each admin Statement's Hive in the golden corpora; the refusals; the log entry; the how-to's
  move run on the Example database where it can.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built in the Composer core, so both Editions show the same (no Edition writing or engine file
changed).

**What was built**

- `composer_core/admin.py`, a new core file registered in `tools/editions.py`'s CORE_FILES.
  Each Edition's `__init__.py` ends with `from composer_core import admin`, so
  `from sqlglot_composer import admin` (and `from spark_composer import admin`) works, while
  `admin` stays out of `__all__` and the star import; the two files still differ only in their
  names. `import sqlglot_composer.admin` doesn't work (it isn't a file of the Edition's folder).
  `admin.__all__`: `drop_table`, `drop_days`, `add_columns`, `set_properties`,
  `move_to_own_folder`.
- `tables.need_saved_table(t, what)`: the one check that a call that changes a table was given
  one of the user's Saved tables (a Table reference with `location=`), refusing text, a Derived
  table and a table someone else owns. Ticket 08 (upkeep) is told the same name.
- Each function makes an ordinary Statement (`Statement._ddl` set, so it can't be a Derived
  table, be split by by_day or drawn by Lineage) with `_admin_call` set (the call as the Admin
  log names it, such as `admin.drop_days(mart.daily_runs, before="2025-01-01")`) and
  `_admin_about`, the items `show_hive` prints first as `--` comment lines, wrapped: what it
  changes, what can't be undone (whether files go with purge off), and "Check first:" a
  command to send by hand (DESCRIBE FORMATTED, SHOW PARTITIONS or DESCRIBE). `to_hive` and
  `run` send the Hive alone. The ALTER TABLEs are written by admin.py itself from pieces the
  Edition writes (table name, values, column types) and kept in `Statement._admin_hive`, which
  `to_hive` returns without the read-back self-check: sqlglot 25.24 can't read
  `ADD COLUMNS ... CASCADE`, and sqlglot's own layout of ALTER differs between its versions
  ("DROP IF EXISTS   PARTITION(..."), so the Toolbox lays them out itself.
  - `admin.drop_table(t)`: `DROP TABLE IF EXISTS`, moved out of the ordinary names (78 public
    names now).
  - `admin.drop_days(t, before=)`: `ALTER TABLE t DROP IF EXISTS PARTITION (dt < '<day>')`,
    the day written in the table's date_format (as_date checks it). Spark refuses a comparison
    there, said in its docstring.
  - `admin.add_columns(t, send=)`: sends DESCRIBE, adds the Table reference's columns the table
    lacks, `ALTER TABLE t ADD COLUMNS (...) CASCADE` (CASCADE only with a Date partition: old
    days get the columns too, so a day written again keeps them; Spark refuses CASCADE, said).
    Refuses no new column, a new Partition, a new column before one the table has, and a
    column with no or a wrong type.
  - `admin.set_properties(t)`: `ALTER TABLE t SET TBLPROPERTIES (...)` from the Table
    reference's purge=, compression= and properties=; refuses a reference with none.
  - `admin.move_to_own_folder(t, send=)`: sends DESCRIBE FORMATTED and SHOW PARTITIONS and
    gives back a list of Statements: CREATE EXTERNAL TABLE IF NOT EXISTS `<t>_moving` at the
    table's own folder (create_table's tree); one INSERT OVERWRITE per day; a comparison
    (per-day COUNT(*) of both, LEFT JOIN, rows where they differ) whose `run` refuses when it
    gives back rows (`Statement._admin_check`), before anything is dropped; for an external
    table, `SET TBLPROPERTIES ('external.table.purge'='false')` so the drop keeps the shared
    folder's files; DROP; `ALTER TABLE <t>_moving RENAME TO <t>` (a renamed external table
    keeps its folder). Each step's call is `admin.move_to_own_folder(<t>, send=...)[n]`.
    Refuses a table already at its own folder, one lacking a Table reference column, no
    Location, and (after review) a table with no Date partition whose own folder is inside the
    old one.
- `run` logs each Admin statement in the Admin log (ticket 03's hook), the comparison's refusal
  logged as failed. `export_lineage` leaves Admin statements out (map family 9), and refuses a
  call given only Admin statements.
- Ticket 02's and 03's texts now match what was built: `_SET_IT` and the Unchecked note say
  `admin.set_properties(t)`; a test holds every `admin.<name>(...)` they write to the
  function's real parameters. The Example database's refusal names create_table and the admin
  module rather than drop_table.
- Docs: each function's docstring with an example; the cheat sheet gains an `admin.py` group
  (`tools/export_clean.py`) and a README sentence on importing it; the gallery gives each
  `admin.<name>` an entry and lists `admin.*` among an example's names; how-to 34 "Move a
  Saved table to its own folder" (Intermediate, now 19-34, after 05 took 33); how-tos 10 and 23 and the Saved
  table Worked example call `admin.drop_table` (23 shows `admin.add_columns` for its new
  column); CHANGES 5.0 (To update, New, Refused now); CONTEXT.md's Admin statement and Saved
  table (managed table defined there).
- Golden corpora: `edge:admin:*` (36 cases, both Editions; the three move cases whose copy has
  a Key join the `primary_key` row of DECLARED_DIFFERENCES); the corpus shows an Admin
  statement's show_hive too.
- Tests: `tests/test_admin_module.py` (both Editions); test_admin_log, test_mix_ups,
  test_tables, the public-name tests (78 after the merge with 05 and 06, plus ADMIN_NAMES), test_docstrings and
  test_example_gallery cover `admin.*`; conftest points the Admin log into pytest's folder for
  every test. On a real Spark (Linux CI only, not run here): admin.drop_table, and the whole
  move of a table made by hand in a shared folder, its rows, name and folder checked.
- The how-to's move "run on the Example database where it can": the Example database is never
  written to, so the how-to builds and prints the move from a stand-in warehouse, runs
  check_table_reference before and after, and runs a day's source on the Example database; the
  move itself runs on real Spark tables in CI.

Not written test-first throughout: the tests came with the code in one pass, then ran against
both Editions.

**Code review** (code-review skill, since 5b82ba1).

Standards: no hard violation. Fixed: how-to 34's four-clause sentence; "managed table" added to
the glossary (Saved table's entry); `MOVING` made private (`_MOVING`); the TBLPROPERTIES writer
written once. Answered, left: `_ddl` holding the changed table for an ALTER while its Hive is
in `_admin_hive` (keeps every "isn't a query" check as it was); admin.py using tables.py's
private helpers and setting Statement's private attributes (as create_table does; the core is
one package); the steps' call set in one loop after they are built; `(t, copy_of)` passed
together to the step helpers; the gallery's and export's `admin.<name>` lists (two tools, each
its own reader); `_column_definition`'s message naming create_table's types when add_columns
calls it (they are create_table's types).

Spec: fixed: Lineage now leaves Admin statements out; a table with no Date partition isn't
moved into a folder inside its old one (it could read the copy's files); the drop step says
when rows with no day go with the old table. Answered: `set_properties(t)` takes no more
arguments (the Table reference is what it sets, as create_table writes it); the move doesn't
run on the Example database, which is never written to (above). Open: rows with no day
(below).

**Beginner reader**: [report](../reports/04-beginner-reader.md). Fixed: the module docstring's
"with location=" (now "with no location= is a table someone else owns"); purge told one way
everywhere (the table's own `external.table.purge` decides, purge=True asks for it,
`admin.set_properties(t)` sets it on a table made before; drop_days' refusal and how-to 23 set
it before a drop); "managed" defined; Spark's refusals said plainly; add_columns' column order
and what CASCADE prevents; one shape for the stand-in DESCRIBE answers; set_properties' undo
and refusal wording; the move's steps as a list ("two days take seven Statements, moves[0] to
moves[6]"), "the folder the Table reference gives it", rows with no day "go with the old
table"; the comparison's refusal says NaN means missing and how to find a day's copy step;
how-to 34's `...` explained, its `move()` gives back the steps for `run(moves[-1], ...)`, and
"Check it worked" says what the Example database query shows; how-to 10 says when a rebuild is
the choice and when add_columns is; how-to 23 quotes the column and says why send goes in
twice; CHANGES wording; the cheat-sheet lines now say what each function does in plain words.
Left: `from sqlglot_composer import drop_table` gives Python's own ImportError (CHANGES says
why); `import sqlglot_composer.admin` doesn't work.

**Open for the user**

- **Rows with no day in a move.** Rows whose Date partition is empty (SHOW PARTITIONS lists
  `__HIVE_DEFAULT_PARTITION__`) aren't copied, and go with the old table; show_hive says so in
  the first step and the drop. Copying them needs a dynamic-partition write whose NULL day Hive
  and Spark read differently, so it wasn't built. Refuse such a move instead (there is no
  opt-out to let it through), or keep the notes?
- **`set_properties(t)`** sets what the Table reference says rather than taking properties as
  arguments (the ticket wrote `set_properties(t, ...)`).
- **The move is a list of Statements**, not one Statement: the comparison has to run, and stop
  the move, between the copies and the drop.
- **`drop_days` and `add_columns ... CASCADE` are Hive 3's**, which Spark refuses: both
  Editions write the same Hive, as the map asks, and the docstrings say so.
