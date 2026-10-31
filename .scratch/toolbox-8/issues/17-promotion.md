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

### Review (098a483)

Code review: the Standards and Spec axes (`review-standards`, `review-spec`, on Sonnet), the
drift review (D344 to D346), and the beginner reader
([report](../reports/17-beginner-reader.md)). Fixed in the next commit:

- **Spec, imports:** a renamed table imported beside others, or in brackets, and a Database
  imported beside another (`from references import mart_dev, ops`), are named for prod
  (`_renamed_in_imports`).
- **Spec, a table only created** (a Table reference, no folder) is promoted by its Table
  reference alone, so one that reads it can be promoted with it.
- **Spec, a Building block that reads the Dev Database** is refused: it serves dev and prod
  alike, so promote can't name prod in it.
- **Spec, a prod copy archived by remove_table** isn't reported as edited (D345 too); one
  promoted again under another name forgets the old.
- **Spec, the prod Table reference** renames the table's own name only, never a column's, which
  is in quotes; its Aliases comment imports its own name.
- **Spec, dev text in the prod copy:** the prod Table folder holds its notebook, opening with a
  line saying it is a copy, without the compare cells, and statement.hql and in_dev.hql, the
  latter naming prod; the checklist, scan, compare and lineage stay dev's.
- **Spec, the location guess:** only a whole folder named for the Dev Database (`mart_dev` or
  `mart_dev.db`) is renamed, and the report says the location= was made from dev's, to check.
  Kept rather than dropped: it saves a step for the common layout, and is said, not silent.
- **Beginner reader:** rename= remembered, and refused with a database in it; the prod Table
  reference held, but its location=; a table with a <...> left refused, the example showing it;
  "decided" gone; the promote Workflow's TABLES asks for dev names; plainer docstrings.
- **Standards:** `_in_prod` is `_prod_text`; "is/are" agrees with the count; the Dev and Prod
  Database travel as one tuple; `promoted_record` read once in `prod_inputs`, and written by
  `workflows.write_promoted_record`; "prod copy" is in CONTEXT.md's **Promotion**; the Project
  action entry rewrapped; promote's loop is `_promote_one`.
- **D344:** check's docstring names the prod copies it reports. **D346:** seed()'s docstring
  fits a prod copy, and CONTEXT's **Seed** too.

Answered, not changed:

- **Standards, `promoted_record`'s hint** stays `dict[str, dict[str, object]]`: a TypedDict is
  machinery the standard keeps out.
- **Standards, `split_table_name(x)[1]` repeated:** one call each, as elsewhere in the file.
- **Spec, the decision and seed steps** beyond "promote, then run_tables": a table that reads
  itself needs its seed in prod as in dev, and the location= a decision only you can make.
