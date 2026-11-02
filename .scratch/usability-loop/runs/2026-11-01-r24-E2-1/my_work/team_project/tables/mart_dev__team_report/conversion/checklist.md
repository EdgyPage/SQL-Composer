# Checklist: mart_dev.team_report

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__team_report.py is made.

## Notes, which block nothing

- LEFT_JOIN(j, many_matches=True), in the logic cell, keeps what the original did, as its `# CONVERSION:` mark says until you delete it. Without many_matches=True the Toolbox refuses the logic, saying: LEFT_JOIN(j) matches on job_id, but j declares no Key, so the Toolbox can't tell whether one row matches or several. If you want to, change what made it needed, such as a WHERE on the partition column, then take the opt-out off; the compare step checks the rows either way.
- FROM(r, reads_all_partitions=True), in the logic cell, keeps what the original did, as its `# CONVERSION:` mark says until you delete it. Without reads_all_partitions=True the Toolbox refuses the logic, saying: FROM(r) reads ops.job_runs, but filters none of its partition columns: dt. If you want to, change what made it needed, such as a WHERE on the partition column, then take the opt-out off; the compare step checks the rows either way.
- Make each unchecked_ piece a Toolbox function where you can.
- project.convert proposed its Key, (team), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
