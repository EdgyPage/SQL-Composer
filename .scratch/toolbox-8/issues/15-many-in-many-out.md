# Multi-inserts, many writes to one table, and a table that reads itself

Type: task
Status: resolved
Blocked by: 14
Size: M

## Question

The user (2026-10-30): "Perhaps something that exports to multiple tables too." And an
incremental script's table reads itself, which in dev starts empty.

## Done when

- A multi-insert (`FROM src INSERT OVERWRITE TABLE a … INSERT OVERWRITE TABLE b …`) gives one
  Saved table per target, each reading the shared FROM. Today's refusal of several INSERTs goes.
- Several statements writing one table give one Saved table whose logic stacks the pieces in
  script order (a Stack, UNION ALL), each piece's filter kept.
- A table whose statement reads itself gets a seed step in the convert Workflow, a permission: a
  call that copies the original's rows into the dev copy once, logged in `sent.csv`; `write()`
  then runs as written. The checklist says why.
- Each case has a test on the Example database, and a how-to example in ticket 19.

## Answer

Built 2026-10-31.

- **A multi-insert** (`converting._read_statements`): a FROM with several INSERTs is read as an
  INSERT per target, each its query with the shared FROM, so each becomes a Saved table of
  its own, noted "was one target of a FROM with several INSERTs". scan_hive, which reads one
  query, still refuses it, saying to convert it.
- **Several writes to one table** (`_pieces_of`, `converting.stacked_hive`): one Saved table, its
  write the first piece's INSERT over the UNION ALL of each piece's query, in script order,
  each piece's columns named as the first's, since Hive fills a table by place and a Stack
  matches by name. Settled here: a later INSERT OVERWRITE replaces the writes before it, so the
  stack starts at the last; when the pieces give different Partitions their values, none
  replaces another, every piece is kept, and each gives its values as columns, the write
  filling each Partition from its rows. batch.md says which write is the first, a piece, or
  replaced.
- **A table that reads itself**: its Table reference is written first (CREATE, DESCRIBE of the
  original, or its SELECT's names), so its query reads its own copy in dev; its notebook gets
  `seed()`, an Unchecked statement copying the original's rows (`SELECT *`), and its checklist a
  box saying why. The convert Workflow's steps are now convert, the checklist, create each
  table (`project.load(t).create()` for each), seed each that reads itself
  (`project.batch_tables(NAME, seeded=True)`), write each (`run_tables`), and compare; the
  seed step is done when sent.csv records each seed, an Unchecked statement.
- Tests on the Example database for each; the how-to example is ticket 19's.
- D334 to D336 fixed here: how-to 01 says the fresh copy goes into the batch's folder;
  `table_reference_text` says it always writes location=; and the create steps now send each
  table's `create()` themselves, in convert and in new_table, rather than naming a cell no
  notebook has.
