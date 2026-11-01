# A conversion's files name the right notebook and database

Type: task
Status: open
Blocked by: 04
Size: S

## Question

Found by round one:

- a table `new_table` made has a Table notebook header and a checklist.md that send its
  Decisions to convert.ipynb's decisions cell, not new_table's (W3-1, W3-2);
- batch.md lists a new_table or Excel query's table as `default.<name>` (W3-1, E3-2);
- scan.md says a bare SELECT has "its INSERT OVERWRITE" (E2-2).

## Done when

- Each file names the Workflow that made the table, its database as the Project's Dev
  Database, and a bare SELECT as a query, each held by a test.
