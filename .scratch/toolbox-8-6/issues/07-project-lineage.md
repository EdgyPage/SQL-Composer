# The Project's lineage and its loops

Type: task
Status: open
Blocked by: 04
Size: L

## Question

Loops and tables two runs write made "evident in the lineage trace ... in the whole project"
(Q7), by hand only (Q17).

## Done when

- `project.export_project_lineage()` writes an HTML page and a Markdown twin in
  `admin/lineage/`: every Saved table as a box, an arrow from each table to each that reads
  it, each Scheduled run that writes a table named on it, a table more than one writes marked,
  a loop drawn red with its tables listed at the top. It builds each run (04) without sending,
  so it reads the warehouse only for Run values.
- `project.check()` reports a loop among the Project's tables, naming each table in it and
  the logic cell to mend, loading each table's logic; it changes nothing.
- `admin/scheduled_runs.ipynb`, made by `project.start()`, holds these calls, run by hand.
- Nothing here runs from a Scheduled run's notebook.

## Answer
