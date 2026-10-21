# The project module

Type: task
Status: resolved
Blocked by: 01, 05
Size: L

## Question

Map Notes, "Projects". `sqlglot_composer/project.py`, imported by name: `start`, `new_table`,
`remove_table`, `remove_reference`, `register`, `check`, the registry, the Admin log's entries
for Project actions (and Admin statements logging to `admin/admin_log.md` inside a Project), the
admin notebooks `start` writes, and `.ipynb` written as plain JSON. The shipped Templates move
inside `sqlglot_composer/` so `start` can copy them.

## Done when

- Each refusal (folder exists, already registered, Project already started) and each archive
  is tested.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built 2026-10-21 on branch `toolbox-6/06-project-module`.

- `sqlglot_composer/project.py`, imported by name like `admin`: `start`, `new_table`,
  `remove_table`, `remove_reference`, `register` and `check`, each returning a short report
  that prints as it reads. A Project is found by walking up from the folder Python is working
  in to the one holding `admin/registry.csv`, so an action runs from any notebook inside it.
- `start()` makes `admin/` (the notebooks `new_table`, `remove_table`, `check_project` and
  `change_a_saved_table`, `templates/`, an empty `registry.csv` and the Admin log),
  `references/`, `building_blocks/`, `tables/` and `send.py`; it refuses a folder holding any
  of them, and one inside a Project. Tickets 07 and 08 add the notebooks of their actions
  (`run_tables`, `add_references`, `refresh_reference_sheet`).
- **The shipped Templates are text in `sqlglot_composer/project_templates.py`**, not a
  `templates/` folder inside the Toolbox: the Toolbox stays one flat folder, which its import
  self-check, the export's allowlist and stamps, and its tests all rely on; `start()` writes
  each into `admin/templates/<name>.py`, where it is the user's to edit. This ticket ships
  `daily_table` and `saved_table_reference`; ticket 09 adds the rest. A placeholder of the
  user's stands where code goes, never in quotes (`DAY = <DAY>`), as in the other Templates.
- `new_table` fills `<DB>`, `<TABLE>` and `<NAME>`, writes the notebook as nbformat 4.4 JSON
  (cells split on `# %%`, text cells on `# %% [markdown]`), makes `lineage/`, and writes the
  Saved table's reference unless one is there (kept, and then not registered). It refuses a
  Table folder that is there, a table the registry lists, an unknown Template, a name with no
  database, and a table named like a Python word.
- `remove_reference` refuses while the table's Table folder is there, since its notebook
  imports the reference. `check()` changes nothing and logs nothing.
- The Admin log: Project actions log as "Project action" entries with a Files line; an Admin
  or Unchecked statement run inside a Project (by its script's folder, or else the folder
  Python is working in) logs to the Project's `admin/admin_log.md`. The log's heading names
  Project actions.
- Wired as `admin` is: `__init__.py`, the registry's file list, the docstring tests, the
  gallery and the export's cheat sheet.

## Reviews
