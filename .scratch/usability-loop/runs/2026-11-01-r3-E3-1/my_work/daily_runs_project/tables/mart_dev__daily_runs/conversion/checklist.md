# Checklist: mart_dev.daily_runs

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/new_table/new_table.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__daily_runs.py is made.

## Notes, which block nothing

- The `# CONVERSION:` mark for FROM(job_runs, reads_all_partitions=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- project.convert proposed its Key, (dt), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
