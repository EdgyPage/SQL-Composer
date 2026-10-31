# Staging tables: keep or fold

Type: task
Status: open
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
