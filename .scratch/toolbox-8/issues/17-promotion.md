# Promotion

Type: task
Status: resolved
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
- Each step has its done function (ticket 12 left them out). The promote Workflow's steps (promote, then `run_tables` in prod, a permission) are in its step
  list, with no fiddling edge in the graph.
- CONTEXT.md gains **Promotion**.

## Answer

Built 2026-10-31.

- **`project.promote(tables, *, rename=None)`**, a Project action, one name or many: for each
  dev table, a prod copy of its Table folder and Table reference, named
  `<PROD>.<its name>`, `_<their db>` kept, unless `rename={dev name: prod name}` says
  otherwise. PROD is read from `admin/databases.py` and refused until filled in.
- **Prod reads prod:** every promoted notebook's code names each promoted table's prod copy,
  by its name, its files' name and its Database module (`_in_prod`); a renamed one is imported
  under its dev name, so the code that uses it reads as it did. A table it reads that isn't
  promoted is refused, so prod never reads dev.
- **Refused before anything is written**, naming each: a table not in the Dev Database or with
  no Table folder; a checklist box unticked; a Conversion's table whose compare hasn't passed
  (a table new_table made has no compare, and needs none); a dev table read but not promoted.
- **Location, settled here:** the prod Table reference's `location=` is the one you filled in
  when promoted before; else the dev one with the Dev Database's name made the Prod
  Database's (and the table's, when renamed); else None, a TODO, which the Workflow's second
  step, a decision, asks you to fill in. A dev location that doesn't name the Dev Database is
  never copied, as prod would then write over dev's files.
- **Dev stays the source:** promoting again archives the prod Table folder and Table reference
  into admin/removed/ and writes them afresh. `admin/workflows/promote/promoted.json` records
  each prod copy's dev table, whether it reads itself, and each file's hash; `check()` reports
  each prod file changed since, saying to change the dev copy and promote again. A prod
  copy's lineage/ starts empty and its compare.md isn't copied: both are dev's.
- **The promote Workflow**, every step with its done function and none fiddling: promote (a
  file step, `project.promote(TABLES)`), fill in each prod `location=` (a decision), create
  each in prod, seed each that reads itself, write each (permissions, through
  `project.promoted_tables(TABLES)`, which gives the prod names from the record).
- CONTEXT.md gains **Promotion**; the Project action entry names comparing and promoting.
- Tests: `tests/test_promotion.py`.
- D343 fixed here: remove_conversion's docstring names the finished folder.
