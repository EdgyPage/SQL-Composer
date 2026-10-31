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
