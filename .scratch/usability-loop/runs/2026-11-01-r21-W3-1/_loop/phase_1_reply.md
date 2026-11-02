DONE: Made mart_dev.failed_runs with the Toolbox, through the convert Workflow, and checked it against the team's query. It has 2 rows, and compare passed on every row (key job_id holds). Table location is /data/team/mart_dev.db/failed_runs. Work is in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W3-1\my_work\team_project.

What I did, in order:
1. Read main/.github/README.md, sections 1 and 9 and the Workflows section (convert). Installed requirements with pip (already satisfied).
2. Copied main/sqlglot_composer into my_work/team_project/, then ran project.start() from a plain script (start.py), as the README allows.
3. Set warehouse.py to `from team_connection import conn` (sys.path appended with the work folder). Set admin/databases.py to DEV = "mart_dev", PROD = "team_prod".
4. Copied from_your_team/failed_runs.hql to admin/workflows/convert/failed_runs.hql. Set the convert names cell to NAME = 'failed_runs' and FILES = ['failed_runs.hql'].
5. Ran convert.ipynb cells 1-2,4 (project.convert). It made a Table folder tables/mart_dev__failed_runs/ and reference references/mart_dev__failed_runs.py, and added an opt-out `# CONVERSION: reads_all_partitions=True` on its FROM line.
6. Answered the one open Decision (location) in the decisions cell: {"mart_dev.failed_runs": {"location": "/data/team/mart_dev.db/failed_runs"}}. Ran cells 1-3,5 (write_decisions). Accepted the proposed key (job_id).
7. Filled in the reference's two TODO lines (a one-line description of a row, and does_not_add_up with a note).
8. Ran cell 6 (create), skipped step 5 (seed, since no table reads itself, as the Workflow says), ran cell 8 (run_tables, written), and cell 9 (compare_batch: passed).
9. The batch folder moved to admin/workflows/convert/finished/failed_runs/. project.check() names no next step for the batch, only a non-blocking note on the CONVERSION mark. A query of mart_dev.failed_runs returns 2 rows.
Not done, as not asked: the promote Workflow (team_prod).

Friction and gaps, for whoever reads the docs:
- Answering a Decision without Jupyter means hand-editing the notebook's JSON. Quotes inside the decisions cell must be escaped as \" in the file. I first wrote a broken line, which made the whole notebook fail to parse, and had to repair it. The README says to edit the JSON file but not how to escape the Decision line; one example of the escaped form would help.
- The convert step adds the `# CONVERSION: reads_all_partitions=True` opt-out without saying what refused the query. The scan.md says "Opt-out added" and the checklist says it "keeps what the original did", but not what the Toolbox would have refused. A beginner will not know whether to keep it.
- The README's sections 1 and 9 assume Jupyter for each step. Without it, I used small scripts (start.py, check_now.py, verify_table.py) and run_notebook.py for the cells. This worked.
- The check output says "Noted by project.convert(...), which blocks nothing" before the actual next step. It is easy to read it as a blocker.
