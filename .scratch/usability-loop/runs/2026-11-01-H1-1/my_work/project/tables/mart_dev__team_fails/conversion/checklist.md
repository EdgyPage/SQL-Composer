# Checklist: mart_dev.team_fails

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__team_fails.py is made.

## Notes, which block nothing

- The `# CONVERSION:` mark for FROM(r, reads_all_partitions=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- The `# CONVERSION:` mark for FROM(o, reads_all_partitions=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- The `# CONVERSION:` mark for JOIN(w, many_matches=True), in the logic cell, keeps what the original did; change what made it needed only if you want to, and the compare step checks the rows either way.
- project.convert proposed its Key, (team, dt), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
