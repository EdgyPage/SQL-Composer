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

#### 09a's reviews

- Spec (2026-10-21): the fold of `notebook_start` and `keep_table_references_true` into
  how-tos had no owner (now in ticket 10's Question); CHANGES.md now says what became of each
  5.x Template; a test ties the README's list to the Toolbox's. Answered, against the
  prototype's stubs: `weekly_rollup` saves days and `week_totals` reads weeks, since a write
  fills the one day its FROM table is bounded to, so no Saved table of weeks can be written;
  `quality_checks` saves each day's row count, since `run_tables` writes every table through
  its `write_day`; `incremental_load` rewrites its last days, as 5.x's did, and its
  `write_day` gives a list, which `run_tables` sends in turn; a read table's file is
  `<SOURCE_NAME>` (or `<CHECKED_NAME>`, `<SNAPSHOT_NAME>`) in the Toolbox's Templates, as
  `<NAME>` is the table's own.
- Standards (2026-10-21): widths (each Template text starts on its own line); CONTEXT.md's
  Template entry no longer speaks of two sets; "writes it as the partition" now names the
  Date partition; `null_counts` names its counts with a `column_name` helper; lineage's
  `stems` split into `written` and `chosen`. Answered: `week_totals` reads `dt`, the day the
  Saved table reference Template names, and says so; `_notebook` stays a function of strings.
- Beginner reader (2026-10-21): each notebook's text cell now says to fill in its Table
  reference first, and which columns, types and Key it lists; `as_of_lookup` says the
  snapshot's reference needs its Key; `<TOTAL>` and `<TOTAL_NAME>` are told apart; why the
  snapshot's day is in ON=; why the day is grouped on but not selected, in every Template;
  `quality_checks` says how a small day shows; the example day is the same everywhere; the
  Building block shows how a notebook reads it; `<NAME>` is named; the logic cell's second
  line numbers it 2.
