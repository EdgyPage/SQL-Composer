# How-tos and the README tutorial

Type: task
Status: resolved
Blocked by: 04, 09
Size: L

## Question

Map Notes, "The docs". How-to 01 "Start a Project", 02 "Add your tables' references", new "Add
a Saved table", "Lineage across your tables", "The Reference sheet"; the rest moved to the
Project's layout and import names; the README tutorial's steps filled in; CHANGES.md's 6.0
section finished. The last ticket before the 6.0 export.

The how-tos also take in 5.x's `notebook_start` and `keep_table_references_true` Templates,
which ticket 09a removed, as steps: writing a first Table reference and a first Statement, and
checking a Project's references against their tables every week.

## Done when

- The how-to page and the README tutorial walk start, references, a table and lineage, in order.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on branch `toolbox-6/10-how-tos-and-readme`.

- How-to 1 is "Start a Project" (`#start_a_project`): the Project's parts, the Admin log,
  send.py, the two path lines a Table notebook starts with, then the first Statement it held
  before. How-to 2 is "Add your tables' references" (`#add_your_tables_references`):
  `project.add_references`, the TODOs, Aliases and descriptions, the checks, and the skip of a
  table already there. The old slugs `#start_a_notebook` and `#import_column_names` are gone,
  and CHANGES.md says what to link to instead.
- New: 11 "Add a Saved table" (`new_table`, filling in the reference and the notebook's
  `<...>`, `load`, `run_tables`), 16 "Lineage across your tables" (a Table folder's lineage/
  history, `load` of the tables it reads) and 17 "The Reference sheet". Getting started is now
  1 to 21 and Intermediate 22 to 40; the files were renamed, their slugs kept.
- A how-to has no Jupyter, so 11 and 16 fill a notebook's `<...>` by reading the .ipynb as JSON
  and replacing each placeholder in its code cells, saying so; 11 writes the filled Table
  reference with `Path.write_text`, as how-tos already write files.
- `notebook_start` is how-tos 1, 2 and 4; `keep_table_references_true` is a step of how-to 21,
  a weekly notebook importing each reference from references/.
- 03, 08, 14, 22, 25, 26 and 37 name references/, building_blocks/, a Table folder's lineage/
  and admin/admin_log.md; 13 points to `run_tables`.
- The how-to page lists the files of a step that writes more than 8 (`LIST_AFTER`), such as
  `project.start()`, by name only, and pins Project actions' times as it pins a lineage's; the
  doctest test pins them too, so the page and the test agree.
- `add_references`' report lists three files or more as "a, b and c".
- The README's eight steps: Install, Start a Project, A first Statement, Your own tables, Filter
  count and join, Save a table every day (now with `new_table` and `run_tables`), Where each
  column comes from (now with lineage across tables), and Keep the Project in order (Levels,
  `check`, `remove_table`, the weekly check), in place of 5.x's "Lay out a project". Its
  examples run in a temp folder, since step 2 starts a Project.
- CHANGES.md's 6.0: the how-tos' new start and numbers, the Reference sheet's condition
  Aliases, and export_lineage's Table folder rule as it now is.
- Closes drift items D213, D214 and D215.

### Reviews

- Spec (2026-10-21): the beginner reader's report and the drift items' closing were still to
  come, and are below and in `.scratch/drift.md`. Answered: `_and` (now `_as_a_sentence`),
  `LIST_AFTER` and the Project actions' pinned times serve the how-tos the ticket asked for,
  and CHANGES.md's rewordings say what 6.0 does now; the Example gallery's Worked examples
  keep 5.x's `statements/`, `table_references/` and `building_blocks/` labels, outside this
  ticket, and are offered to the user as a follow-up; the fixture path
  `01_start_a_notebook.py` in test_export_clean is renamed all the same.
- Standards (2026-10-21): "one-time actions" is now "a notebook per Project action";
  `lineage_pinned` is `times_pinned`, `_and` is `_as_a_sentence`; ragged prose rewrapped in
  CHANGES.md, the README, how-tos 02, 08, 11, 16, 26 and 37; a long assert split. Answered: the
  fill-in loop and the start preamble repeat across 11, 16 and 17 because a how-to stands
  alone; `add_references`' two report branches word "its" and "their".
- Beginner reader (2026-10-21; costliest: a later how-to's `project.start()` in your own
  Project, admin notebooks against calling `project.*`, the daily table's Hive): every how-to
  after 1 says to leave `project.start()` out in your own Project, and the README says so too;
  the README and how-tos 1 and 11 say a Project action from any notebook is the same as its
  admin notebook's, and "by hand" means your file explorer; how-to 11 says why the key holds
  dt, which `<...>` take quotes, what `PRIMARY KEY ... DISABLE NOVALIDATE` is, and shows
  `rows`' docstring on GROUP_BY; 16 states the lineage folder rule whole and what
  mart.jobs_by_runs counts; how-to 1 says what the Script line's commit is, that your own
  list holds sqlglot_composer, and counts three lines, not two; the README's send is a whole
  `def`; 02 says to add `equals` to the import; 11 lists backfill and who runs run_tables;
  17 says why `csv` rather than `read_csv`. Answered: the Load limit, Problem, the admin
  module and the registry are each explained where they first matter; the how-to page shows
  each written file above the prose that names it.
