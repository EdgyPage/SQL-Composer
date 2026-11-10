<!-- sqlglot Composer 8.6 - copy it, then edit your copy -->
# Checklist: mart.team_failures

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart__team_failures.py is made.

## Notes, which block nothing

- JOIN(o, reads_all_partitions=True), in the logic cell, keeps what the original did, as its `# CONVERSION:` mark says until you delete it. Without reads_all_partitions=True the Toolbox refuses the logic, saying: JOIN(o, ON=...) reads ops.job_owners, but filters none of its partition columns: dt. If you want to, change what made it needed, such as a WHERE on the partition column, then take the opt-out off; the compare step checks the rows either way.
- project.convert proposed its Key, (team, dt), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
