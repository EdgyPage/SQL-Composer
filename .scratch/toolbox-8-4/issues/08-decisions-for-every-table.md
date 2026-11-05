# Decisions for every table

Type: task
Status: open
Blocked by: 05
Size: M

## Question

Answering the same thing table by table is the convert notebook's busywork: "If Decisions can
hold a global var ie location_root, start_date, etc, that would be helpful." (map, "Decisions
for every table").

## Done when

- `DECISIONS["all_tables"]` answers for every table the Workflow's notebook names, in every
  Workflow with a decisions cell. It loads first, and a table's own answer overwrites it, kind
  by kind and, for tags, tag by tag.
- It takes `seed` (09), `location_root` and `tags`. `location_root` gives a table with no
  location of its own `<root>/<db>.db/<table>`. A Key or a type under it is refused, naming
  the tables to answer it for.
- A tag under `all_tables` that a table doesn't hold is passed over for that table; one no
  table of the notebook holds is refused, as 8.3's 04 refuses an answer that matches nothing.
- `project.check()` and step 1's printed `DECISIONS` (8.3's 05) offer `"all_tables"` with each
  Decision more than one table holds.
- `write_decisions` says which tables each `all_tables` answer was written into.
