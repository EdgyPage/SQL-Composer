# new_table from a query, made in dev and promoted

Type: task
Status: resolved
Blocked by: 08
Size: L

## Question

new_table's notebook holds eight kinds of `<...>` to fill in; the converter already turns any
query into checked Toolbox code (map, "new_table": Q14, Q17).

## Done when

- new_table's names cell takes the query as Hive, as text or a .hql file, and the converter
  writes the table's logic from it: no `<...>` to fill in. The Template's notebook stays for a
  table started by hand.
- Such a table is made in the Dev Database, `<DEV>.<table>`, a Batch of one, with its Table
  reference from its logic (08), and is promoted like a Conversion's.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): a journey from a query to
  a prod table makes no hand edit but its Decisions.

## Settled with the user (2026-10-31)

new_table converts: its names cell gains `QUERIES = {"daily_runs": "daily_runs.hql"}`, each
table's query as Hive text or a .hql file. Its step 1 converts each into `<DEV>.<table>`, a
batch of one, and new_table gains a compare step, the table against its query, so promote
takes it as it takes any Conversion's table. One notebook, start to finish. (Asked: this, or
pointing the user to the convert Workflow with NAME and HIVE; the user chose this.)

## Answer

Built 2026-10-31.

- **The names cell's QUERIES** (`{"daily_runs": "daily_runs.hql"}`, by the table's name
  without its database, Hive text or a .hql file beside the notebook): step 1 is now
  `project.new_table(TABLES, queries=QUERIES)`. `project.new_table(..., queries=)` converts
  each table it names, `_new_table_from_query`, through convert's own batch code, a batch of
  one named for the table, so the logic, the Table reference (Key proposed, types from the
  references it reads) and the conversion folder are a Conversion's; the Template's notebook
  stays for each table started by hand. A table outside the Dev Database is refused, and so is
  a query for a table TABLES doesn't name.
- **One Workflow:** the batch's record says it was made for new_table (`made_for`), so the
  convert Workflow passes it over, and new_table's steps take it on: its logic loads, its
  reference is written already, its Decisions, its preview, create and write, and a new last
  step, compare each table made from a query with its query (`project.compare_batch`), done
  when it passed or its batch finished. promote then takes it, as a Conversion's table.
- **Checked before anything is made** (`project._refuse_queries_it_cant_make`): a query for
  a table the names don't hold; two names sharing one table's name; a table outside DEV; Hive
  that isn't one query alone (a CREATE or an INSERT is a batch for convert); and a source with
  no Table reference, which convert would DESCRIBE through a query new_table hasn't, refused
  saying to add it with the references Workflow.
- **Journeys:** `test_new_table_from_a_query_then_promote_it` runs from a query typed in the
  names cell, through a dry run that sends nothing, to the dev table holding the query's
  rows, then promote: no hand edit but its location, typed in the decisions cell.
- **Copilot:** the Workflows file grew past 8,000 characters, so it is split, with the user's
  leave (2026-10-31): file 13 converts and promotes, file 14 makes new tables, references,
  upgrades and changes.
- **Code review:** Standards: its own loop over the names (now `_run_for_each_name`, with
  `_new_table_one` choosing the query or the Template), the Next line cut by its prefix (now
  `_batch_report` writes it from the batch's `made_for`), `given` (`query_or_file`),
  `made_for` set after construction (a constructor argument), one name in two databases (now
  refused), the QUERIES check twice (`workflows.queries_given`). Spec: a source with no
  reference refused in convert's words, wrongly (now its own refusal), the DEV check inside the
  loop (now before any table is made), Hive that isn't one query (refused), a stale QUERIES key
  at the compare step (now only those TABLES names), the docstring silent on queries=, the
  Workflow's about text.
- **Beginner reader:** [09-beginner-reader.md](../reports/09-beginner-reader.md).
