# Writing a Statement out as Python

Type: task
Status: resolved
Blocked by: 05
Size: L

## Question

The second half of a Conversion: the objects ticket 05 reads, written out as the Python the user
would have written, in a Table notebook's shape, so the result is code to read, edit and keep,
"more maintainable patterns", not a Statement built at run time.

Before writing the tests: show the user one converted sample, the notebook as it will land,
since the map leaves the notebook's exact shape open.

Settled while building (2026-10-26): ticket 05 writes the Python straight from sqlglot's tree
(see its "Python first"), so this ticket is the notebook around that Python, the opt-outs found
by running it, and the round trip. The user is shown the converted sample in the Answer and in
the how-to (ticket 09), since a goal session doesn't stop to ask.

## Done when

- A Toolbox function (internal, for ticket 07) writes, from ticket 05's result, the source of a
  notebook in a Table notebook's shape: a first cell of named constants (every long list and
  lookup), imports from the Project's Database modules, the logic cell (`# logic` first) with one
  function per CTE giving back a Derived table and one giving back the Statement, and a cell that
  shows its Hive.
- The names it writes come from the original where they're good Python names (a CTE's name, a
  column's alias), else plain made-up ones it never repeats.
- Each Unchecked piece is written as its call, and each opt-out a Guard needs carries
  `# CONVERSION: the original did this; check it` at its line.
- Round trip, as a test on every sample of ticket 05's: the written Python, run, gives back a
  Statement whose Hive is the original's once both are normalised by sqlglot. The writer refuses
  to give back source that fails this, saying where they differ.
- The written source passes the repo's lint and reads like a Worked example: one Clause function
  a line where it fits, SQL order, the Toolbox's own names.
- CLAUDE.md's Definition of done. Nothing public changes, so no beginner read.

## Answer

Built 2026-10-26 on dev, with ticket 07 (see 05's "Python first").

- `Translation.logic()` writes the Conversion's logic cell: the imports (the Toolbox names used,
  `from references import ops` per Database), the named constants, each table and CTE, and, for
  one SELECT, `rows() -> list[Clause]` with `converted() -> Statement` returning
  `statement(*rows())`, else `converted()` returning the Stack or the Unchecked statement.
  Names come from the Hive (aliases, CTE names, a column's name for a constant), made plain and
  unique; a Python keyword or builtin gets `_t`.
- `saved_table_logic(...)` makes the logic cell, as the user left it, a Table notebook's:
  `create()`, `preview()` and `write()`, write() through `rows()` with the original's INSERT
  mode and static partition, or through `converted()` as a Derived table.
- The round trip: `convert` loads the notebook it wrote (`project.load(name)`, so the logic
  runs exactly where a user's would, the one reviewed `exec`), builds the Statement, adds each
  opt-out a refusal names, and compares its Hive with the original's by `compare_hive`, saying
  so in its report and scan.md. It doesn't refuse a Conversion whose Hive differs: the 80% the
  user asked for is still theirs, and the report says where they differ.
- The sample shown: the user is shown one in ticket 09's how-to; tests/test_conversions.py
  holds one end to end.

## Reviews

Reviewed with tickets 05 and 07, as one change: see
[07's Reviews](07-the-conversion-folder.md#reviews).
