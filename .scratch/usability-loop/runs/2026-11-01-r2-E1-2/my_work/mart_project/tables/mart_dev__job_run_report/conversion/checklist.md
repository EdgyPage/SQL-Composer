# Checklist: mart_dev.job_run_report

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__job_run_report.py is made.

## Notes, which block nothing

- The `# CONVERSION:` mark for FROM(job_runs, reads_all_partitions=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- project.convert proposed its Key, (job_id), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
