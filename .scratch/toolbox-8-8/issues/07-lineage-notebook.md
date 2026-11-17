# admin/lineage.ipynb

Type: task
Status: open
Blocked by: 03, 05
Size: S

## Question

Where the user records and asks for the difference by hand (Q15).

## Done when

- **`project.start()` writes `admin/lineage.ipynb`**, owned by no one Workflow, like
  `check_project.ipynb`:
  1. a text cell saying what the Lineage state and the Lineage difference are, and that each
     Project action and each Table notebook's cell 5 records already;
  2. a cell finding the Project, as the other admin notebooks do;
  3. `project.record_lineage_state()`;
  4. `SINCE = None` and `TABLES = None`, each with a comment of what it takes, then
     `project.export_lineage_difference(since=SINCE, tables=TABLES)`.
- It needs no `connect(...)` (Q6), and says so.
- `admin/scheduled_runs.ipynb` is unchanged.
- The Example projects hold it; `project.py`'s Project layout docstring and CLAUDE.md's "A
  Project's admin folder" name it and `admin/lineage/lineage_state.csv`.
