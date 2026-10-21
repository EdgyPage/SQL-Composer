# The project module

Type: task
Status: open
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
