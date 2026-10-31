# Checklist: mart.team_failures

Tick each box, [x], once it is done: the convert Workflow waits on every box.

- [x] Decide the `# CONVERSION:` mark for JOIN(o, reads_all_partitions=True), in the logic cell: keep it, as the original did, or change what made it needed; then delete the mark.
- [x] Check the type of team_name in references/mart__team_failures.py: it is written "string", since neither its query nor DESCRIBE of the original told it.
- [x] Check the type of fails in references/mart__team_failures.py: it is written "string", since neither its query nor DESCRIBE of the original told it.
- [x] Fill in location= in references/mart__team_failures.py: the folder its files go in.
- [x] Choose its Key in references/mart__team_failures.py, or leave key=None if no columns name one row.
