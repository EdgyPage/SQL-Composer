# Templates and Example projects as Projects

Type: task
Status: claimed
Blocked by: 07, 08
Size: L

## Question

Map Notes, "Templates", "Example projects". The Table-notebook Templates in `# %%` form, the
Saved-table reference and Building block Templates; `notebook_start` and
`keep_table_references_true` folded into how-tos. Both Example projects rebuilt as Projects,
generated with pinned times, tested through `load` and `run_tables`.

## Done when

- The export ships both Example projects as Projects, and their tests pass.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built in two parts, each reviewed on its own: 09a, the Templates (2026-10-21, branch
`toolbox-6/09a-templates-in-the-toolbox`), then 09b, the Example projects as Projects.

### 09a: the Templates in the Toolbox

- `sqlglot_composer/project_templates.py` holds the five Table notebook Templates
  (`daily_table`, `incremental_load`, `weekly_rollup`, `as_of_lookup`, `quality_checks`), all
  built by `_notebook` around the same five code cells, each listing its placeholders with an
  example in its text cell; and the `saved_table_reference` and `building_block` Templates.
  `start()` writes all seven into `admin/templates/`; `new_table`'s `template=` takes only a
  Table notebook Template (one in `# %%` cells).
- `incremental_load`'s `write_day(day)` gives the writes of its last days, a list;
  `run_tables` sends each in turn, and its lineage cell passes them all.
- `export_lineage` from a Table notebook, of Statements of several tables of which one writes
  that notebook's table, goes in that Table folder's `lineage/` too: lineage across tables, as
  the prototype's team_day showed.
- The repo's `templates/` folder is gone, with the export's copy of it, the README's generated
  list (the README now names each Template), `test_templates.py` and the Level tests of
  Templates; `notebook_start` and `keep_table_references_true` become how-to steps (ticket
  10). `tests/test_project_templates.py` makes each Template into a notebook, fills it in for
  the Example database, loads it and runs its preview.
