# A Table notebook's logic is loaded from its logic cell

Status: accepted

In a Project, each Saved table the user builds has a Table notebook, and the Statements that
create and write it are defined in one of its cells, the logic cell, whose first line is
`# logic`. Other code needs those Statements: a second table's notebook, to draw lineage across
both; `project.run_tables`, to write every table in order; the tests, to run the Example
projects. `project.load("db.table")` reads the notebook as the JSON it is, takes the logic
cell alone, and runs it, giving back the functions it defines.

Running a cell's text means `exec`, which the offline policy refuses in the Toolbox as dynamic
code (ADR 0004): it could reach the network unseen. The user allowed one reviewed site
(2026-10-21), `project.load`, since the cell is the user's own code, in their own Project. `load`
keeps to the cell's purpose: it refuses a cell that calls `run`, which would send Hive just by
loading, and runs nothing else from the notebook.

## Considered options

- **The logic in a `.py` file in each Table folder, imported by name.** Rejected: the notebook
  is where the user reads and edits the table, and a second file would split it in two; an
  import by a name not written out is dynamic code to the policy too.
- **No `load`: each notebook repeats the logic it reads.** Rejected: lineage across tables and
  `run_tables` need the same Statements the notebook writes with, not copies that drift.

## Consequences

- The logic cell only imports and defines: its imports, Toolbox names, references and Building
  blocks, are in the cell itself, so it runs alone. The Templates say so.
- `load` drops the Project's `references` and `building_blocks` modules Python already holds
  before running the cell, so it reads them as they are on disk now.
- Notebooks are read as plain JSON, never with a notebook library.
