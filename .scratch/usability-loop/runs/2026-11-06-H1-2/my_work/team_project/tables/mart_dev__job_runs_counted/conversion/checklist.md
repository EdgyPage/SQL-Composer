# Checklist: mart_dev.job_runs_counted

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__job_runs_counted.py is made.

## Notes, which block nothing

- FROM(r, reads_all_partitions=True), in the logic cell, keeps what the original did, as its `# CONVERSION:` mark says until you delete it. Without reads_all_partitions=True the Toolbox refuses the logic, saying: FROM(r) reads ops.job_runs, but filters none of its partition columns: dt. If you want to, change what made it needed, such as a WHERE on the partition column, then take the opt-out off; the compare step checks the rows either way.
- project.convert proposed its Key, (job_id, dt), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
- The original was one target of a FROM with several INSERTs.
