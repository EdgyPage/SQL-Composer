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

### Review (73e335d)

Code review: the Standards and Spec axes (`review-standards`, `review-spec`, on Sonnet), and
the drift review (D337 to D339). Fixed in the next commit:

- **Spec, CTE pieces:** a stacked piece with its own CTEs was wrapped as `SELECT * FROM (...)`,
  which no Stack can name, and two pieces' CTEs of one name clashed. Now every piece's CTEs
  go in the one WITH at the write's top, and one named as an earlier piece's is renamed
  `<name>_<its piece's number>`, its piece reading it by the new name, still called by the
  old, so its columns are found (`converting._ctes_taken_off`). Tested with two pieces each
  with a CTE `x`, run on the Example database.
- **Spec, a write kept whole as Hive:** an incremental INSERT whose query stays an Unchecked
  statement, as `> (SELECT MAX(...) FROM t)` does, had a write() that couldn't run
  (`derived(...)` refuses an Unchecked statement, and `statement` wasn't imported). Its write()
  is now its INSERT, an Unchecked statement too (`ConvertedQuery.kept_whole`, `saved_table_logic`'s
  `whole_hive`), and `statement` is imported wherever write() uses it. The convert Workflow
  counts such a write as one: an Unchecked statement sent for the table besides its seed
  (`workflows.was_written`). Tested from convert through create, seed and write to the compare
  step.
- **Spec, the seed's Partitions:** a partitioned seed fills each Partition from its rows, so the
  seed step and its checklist box now send `hive_settings("dynamic_partitions")` first; the
  Workflow notebooks import `hive_settings`.
- **Standards:** no `x or default` (`_untyped_as_string`); `static_partition` reads
  `_static_values`; a write's part in batch.md is one of three names (`_FIRST`, `_STACKED`,
  `_REPLACED`) shared by both sites; `_write_table_files` takes the seed's Hive, and the caller
  records the seeded table; `static` is `static_values`.
- **Glossary:** **Seed** is in CONTEXT.md (D339); batch.md says "stacked into <table>'s write"
  rather than "a piece", which stays a word of the code alone.
- **Drift:** D337 (statement.hql holds each statement of a table's write: convert's docstring,
  the notebook's first cell, CONTEXT.md's Conversion folder) and D338 (`_convert_one_table`'s
  docstring).

Answered, not changed:

- **Standards 3, `_read_statements` repeats `_read_statement`'s table and reads:** the two set
  them for different trees (one target's INSERT, with the shared FROM, against the whole
  statement), two lines each; a helper would hide which tree.
- **Standards 6, `batch_tables(name, seeded=False)`:** one list of the batch's tables, the flag
  narrowing it to those the seed step sends; the Workflow's steps read both, and this ticket
  names the seed step.
- **Spec (b), an INSERT INTO and an INSERT OVERWRITE of different Partitions:** both are kept
  and the write takes the first one's mode, so the overwrite's Partition is added to rather
  than replaced on a run again. No one write can do both; the first write into an empty dev
  table gives the same rows, and the compare step (ticket 16) checks them.
