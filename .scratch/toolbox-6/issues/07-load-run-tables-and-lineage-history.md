# Load, run_tables and lineage history

Type: task
Status: open
Blocked by: 06
Size: M

## Question

Map Notes, "load", "run_tables", "Lineage". `project.load("db.table")` returns the `# logic`
cell's functions and refuses one that calls `run`; `run_tables(day, send=..., tables=None)`
orders writers before readers and refuses a loop; `export_lineage`'s default name inside a
Project. Write the ADR on loading the logic cell rather than importing a .py.

## Done when

- Lineage across two Table folders, through `load`, is tested.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
