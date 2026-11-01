# Checklist: mart_dev.team_report

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__team_report.py is made.

## Notes, which block nothing

- The `# CONVERSION:` mark for LEFT_JOIN(j, many_matches=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- The `# CONVERSION:` mark for FROM(r, reads_all_partitions=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- Make each unchecked_ piece a Toolbox function where you can.
