# Checklist: mart_dev.run_log

Written again each time its Decisions are written: don't tick or edit it. Answer each open Decision in the decisions cell of admin/workflows/convert/convert.ipynb.

## Open Decisions

None: each Decision in references/mart_dev__run_log.py is made.

## Notes, which block nothing

- Make each unchecked_ piece a Toolbox function where you can.
- Its write reads its own table, which in dev starts empty. So the convert Workflow's seed step, after it creates the table, copies the original's rows into it once, with its seed(). It copies every Partition unless SEED, in its Table reference, limits them. To copy only those you need, answer "seed" in the decisions cell, such as {"dt": {"from": "2026-01-01"}}. A table with no Partitions copies every row. The seed step's line shows the WHERE it sends.
