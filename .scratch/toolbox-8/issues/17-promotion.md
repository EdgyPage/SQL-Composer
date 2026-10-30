# Promotion

Type: task
Status: open
Blocked by: 16
Size: M

## Question

The user (2026-10-30): "I have two dbs that I own, a dev and a prod, so I can default to dev and
make the purposful decision to carry over the prod name in to the code." Dev stays the source;
prod is only ever generated. The map's "Promote" Notes hold the design.

## Done when

- `project.promote(tables)` writes a prod copy of each dev Table folder, named for the Prod
  Database, `_<their db>` kept unless `rename={...}` says otherwise, and every promoted notebook
  that reads another promoted table names its prod copy.
- It refuses a table whose checklist has a box unticked, whose compare hasn't passed, or that
  reads a dev table not promoted with it, naming each, before anything is written.
- Re-promoting replaces the prod copy, archiving the old; the check reports a prod folder edited
  by hand.
- The promote Workflow's steps (promote, then `run_tables` in prod, a permission) are in its step
  list, with no fiddling edge in the graph.
- CONTEXT.md gains **Promotion**.
