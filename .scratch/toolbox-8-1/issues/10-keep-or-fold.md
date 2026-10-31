# Staging tables: keep or fold

Type: task
Status: resolved
Blocked by: 03
Size: L

## Question

A long script's staging table, a CREATE TEMPORARY or a scratch table DROPped at the end,
becomes a full Saved table today (map, "Staging tables": Q18).

## Done when

- A table the Batch writes and only the Batch reads is a keep-or-fold Decision, proposed
  fold for a TEMPORARY table or one the Batch DROPs, keep otherwise.
- Folded, it becomes a Derived table in each table that reads it, and is never created,
  written, compared or promoted; `batch.md` says where it went.
- A staging table that can't fold into one Derived table: settled here and recorded below,
  keeping it a Saved table where it can't.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the long-script journey's
  staging table folds, and its prod tables give the original's rows.

## Answer

Built 2026-10-31.

- **A staging table** (`converting.staging_tables`): one CREATE ... AS of the batch writes it,
  nothing else of the batch writes it, and a later statement reads it. Fold is proposed for a
  temporary table, or one a DROP later in its own script removes, a scratch table; keep for
  the rest. A DROP before the CREATE, as a script that starts afresh has, isn't one.
- **Folded** (`converting.fold_staging`, before the batch is planned): its query becomes a CTE,
  named for the table, of each statement that reads it, so the converter makes it a Derived
  table there; its CREATE ... AS and DROPs become nothing, noted "folded into <tables>: a
  Derived table there, never created or written" in batch.md. Never a Saved table, so never
  created, written, compared or promoted. convert's report names each table folded.
- **The Decision** is made before the convert, since folding changes the readers' logic:
  settled here as convert's `staging={"<table>": "keep" | "fold"}`, by the table's name as the
  Hive writes it, the convert notebook's names cell `STAGING = {}`; left out, the proposal. A
  name that isn't a staging table, or a choice but those two, is refused, naming the staging
  tables there are. Not a decisions-cell answer: those are written into a Table reference,
  which a folded table never gets.
- **What can't fold, settled:** a table written by more than one statement (stacked) or by an
  INSERT isn't a staging table, so it is kept a Saved table, as before; one a reader can't take
  (a reader kept as Hive, a multi-target FROM sqlglot didn't read, or one with a CTE of the
  same name) is kept, its note saying so. A staging table read only within one Partition folds
  as any other: its query is the reader's CTE, filtered as the reader filters it.
- **Tests:** test_batches' ticket 10 section (a scratch table DROPped after its read folded,
  a temporary one folded, one neither kept, staging= keeping one, a name that isn't one
  refused); the long-script journey, the user's own case, is no longer an xfail: its
  temporary staging table folds, and its prod tables give the original's rows.
- **Code review:** Standards: "staging table" not in the glossary (now in CONTEXT.md); the
  notes' constants beside `DROPPED`, and the kept note one too (`KEPT`); the dense scratch test
  a function (`_is_dropped_after`); `_takes_a_fold` named as a bool (`_is_foldable_into`); the
  report's line placed in the report with a comment. Left: the fold rewrites the statements'
  fields from converting.py's own functions, beside `_read_statements`, which makes them.
  Spec: a statement before the CREATE in its script got the fold, though it reads the table
  as it was (now `readers_after`; a test holds it); a staging query's own WITH nested inside
  the CTE (now hoisted before it; a test holds it); a name with backticks refused (stripped);
  a chain of two staging tables untested (a test holds it); the map's Notes (now record the
  settlement). Left, rare: a column qualified by the staging table's full db.table name.
- **Beginner reader:** [10-beginner-reader.md](../reports/10-beginner-reader.md).
