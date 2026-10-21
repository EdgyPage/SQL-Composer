# How-tos and the README tutorial

Type: task
Status: claimed
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
