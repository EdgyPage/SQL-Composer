# Checklist: mart.team_failures

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

- kind: Rebuilt or History table, nothing proposed, as its INSERT OVERWRITE fills dt from its rows' own values, PARTITION (dt), so it may replace every Partition or only some: answer "rebuilt" if each write replaces the whole table, "history" if it keeps the rows already there, in references/mart__team_failures.py

## Notes, which block nothing

- JOIN(o, reads_all_partitions=True), in the logic cell, keeps what the original did, as its `# CONVERSION:` mark says until you delete it. Without reads_all_partitions=True the Toolbox refuses the logic, saying: JOIN(o, ON=...) reads ops.job_owners, but filters none of its partition columns: dt. If you want to, change what made it needed, such as a WHERE on the partition column, then take the opt-out off; the compare step checks the rows either way.
- project.convert proposed its Key, (team, dt), from its query: if it is wrong, answer "key" in the decisions cell, such as "key": ["a", "b"], or "key": None when no columns name one row.
- If it is a History table, which each write adds to, its copy in dev starts with none of the past rows its original holds. So the convert Workflow's write step first loads them, its Seed, once, copied from its original: SEED, in its Table reference, picks which, such as {"months": 1}, one month back from the newest Partition. To load others, answer "seed" in the decisions cell, such as {"dt": {"from": "2026-01-01"}}. A table with no Partitions copies every row. A Rebuilt table has no Seed. The write step's report says what its Seed loaded.
