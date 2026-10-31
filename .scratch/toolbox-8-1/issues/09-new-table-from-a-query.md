# new_table from a query, made in dev and promoted

Type: task
Status: open
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
