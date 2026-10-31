# A Conversion writes Table folders, a checklist, and runs again safely

Type: task
Status: resolved
Blocked by: 13
Size: L

## Question

The user (2026-10-30): "Why do I have to create manual files when the answer of what to do was
already given back to me as code? If we know the code, then implement it." Running again: "make
two functions one for overwrite, one that doesn't", settled as `overwrite=True` ("much better").

## Done when

- A Conversion writes `tables/<dev>__<table>/` for each table itself, with `create()`,
  `preview()` and `write()`; `finish_conversion` is gone, and its admin notebook cell with it.
- `tables/<t>/conversion/` holds the statement the table came from, its checklist items and,
  after ticket 16, its compare result. `admin/workflows/convert/<name>/` holds only the scripts
  as given, their order, and the tables that came from them.
- Each `# CONVERSION:` decision gets the default that keeps the original's rows, a box on the
  table's checklist and a line on the instance's; nothing is a placeholder a CREATE answers.
- A statement that can't convert is an Unchecked statement in its own Table folder, listed; the
  batch goes on.
- Running `convert` again rewrites a file whose hash is the one it wrote, keeps an edited one
  and writes the fresh one beside it, listed; `overwrite=True` replaces every file, archiving
  each first.
- Each step has its done function (ticket 12 left them out). The convert Workflow's first two steps (convert, the checklist) are in its step list, and the
  graph's fiddling count for convert falls by every hand step they remove.
- CONTEXT.md's Conversion folder entry says it is the batch's index.
- From ticket 13's beginner reader: no Conversion or finish_conversion call the user never made
  shows in the Admin log, admin/removed/ or a notebook; a CREATE's STORED AS reaches its Table
  reference; the checklist names each guessed type, location= and the SET lines a write needs
  sent first; `tables/<t>/conversion/` keeps the statement as the script wrote it; the batch
  is the convert Workflow's instance, so check() and do_next() name its next step; the convert
  notebook's names cell takes FILES.

## Answer

Built 2026-10-31.

- **Every Conversion is a batch, and makes its Saved tables itself.** `project.convert` writes
  each table's Table folder, notebook and Table reference directly (`_convert_one_table`), with
  no call to `convert` or `finish_conversion` inside it, so the Admin log, admin/removed/ and
  the notebooks name only the user's own call. One query alone is a batch of one, its table
  `<dev>.<name>` (`converting.QUERY`). `finish_conversion`, the Conversion's own notebook and
  its `load(name)` path are gone; `remove_conversion` archives a batch's folder, and the
  Conversion folder (`CONVERSION_FOLDER`) is now `admin/workflows/convert/<name>/`.
- **Its Statement is built before its folder is written**: the logic cell is run by
  `run_logic`, which `load` now uses too, adding each opt-out a refusal names. The offline
  policy's reviewed `exec` moved from `load` to `run_logic` (the user's OK, 2026-10-31).
- **`tables/<t>/conversion/`** keeps `statement.hql` (as the script wrote it), `in_dev.hql` (the
  Hive its logic was built from, which the compare cell reads), `scan.md` and `checklist.md`: a
  box for each `# CONVERSION:` mark (its default, the opt-out, keeps the original's rows), each
  type neither the query nor DESCRIBE told ("string" meanwhile), `location=` unless the CREATE
  gave it, the Key, the SET lines to send first, each unchecked piece, and a refusal to mend.
  A CREATE's STORED AS (ORC or PARQUET) and LOCATION reach the Table reference.
- **Running again** (`_BatchFiles`): `written.json` records each file's hash and the batch's
  tables; a file still as written is written afresh, one changed (or not the batch's) is kept
  and the fresh one written beside it as `.new`, and `overwrite=True` archives each into
  admin/removed/ first.
- **The convert Workflow**: four steps, convert (a call to the warehouse, for DESCRIBE), the
  checklist (done when no box is open), run_tables (done when sent.csv has each write), and
  compare (ticket 16 gives it its done function). Its names cell takes FILES. Each batch is an
  instance (`batch_instances`, `instances_of`), so check() and do_next() name its next step,
  as "convert.ipynb, <name>: ...". Fiddling for convert is 0.
- The Intermediate Example project fills in DEV (`mart`), converts team_failures as a batch of
  one with `rename=`, ticks its checklist and archives the batch's folder. How-to 27, how-to
  01, the README template, Copilot file 07, CONTEXT.md's Conversion and Conversion folder, and
  CHANGES.md follow.

Settled differently from Done when:
- **A statement that isn't a write**, such as ANALYZE, stays an `unchecked_hive(...)` line in
  batch.md rather than a Table folder of its own: it makes no table, and a Table folder is a
  table's. A write that can't convert stays an Unchecked statement in its own table's folder,
  as before.
- **The convert step is a call to the warehouse, not a file step**: it sends DESCRIBE through
  the user's query, which do_next never does.
- **scan.md's line numbers** are of in_dev.hql, the Hive rewritten in dev, which the compare
  cell reads; statement.hql keeps the script's own text.
