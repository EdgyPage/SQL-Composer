DONE: mart_dev.failed_runs is made with the Toolbox, written in dev, and compared against the team's query, which passed on every row (2 rows each, key job_id holds). It is not promoted to team_prod, since the task only asked for the dev table.

What I did, in order, inside my_work/team_project (a Project of mine, copied with the Toolbox from main/sqlglot_composer):
1. Ran project.start(). Its first step "Connect your warehouse" in the README is what I followed for warehouse.py: I replaced `conn = example_database` with `sys.path.append(...work folder...)` and `from team_connection import conn`.
2. admin/databases.py: DEV = "mart_dev", PROD = "team_prod".
3. Copied from_your_team/failed_runs.hql unchanged into admin/workflows/convert/failed_runs.hql. The convert Workflow's names cell is NAME = "failed_runs", FILES = ["failed_runs.hql"], which the README's convert section describes as the one-file query rule that makes mart_dev.failed_runs.
4. Ran convert cells 1,2,4 (project.convert). It proposed Key ["job_id"] and one open Decision, location.
5. Answered DECISIONS = {"mart_dev.failed_runs": {"location": "/data/team/mart_dev.db/failed_runs"}} in the decisions cell and ran cells 1,2,3,5 (write_decisions).
6. Filled the reference's one-line description and the does_not_add_up TODO (no column is an average, ratio or distinct count).
7. Ran convert cells 1,2,6 (create), 1,2,7,8 (seed says nothing to seed, then write), and 1,2,9 (compare_batch).
8. Ran the table notebook's export_hive cell (cells 1,2,5) to write the .hql file.
9. project.check() reports every Table folder, Table reference and Building block registered, and the batch done.

Files (absolute):
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\references\mart_dev__failed_runs.py (location=/data/team/mart_dev.db/failed_runs, key job_id)
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\tables\mart_dev__failed_runs\mart_dev__failed_runs.ipynb (logic; keeps the original's `# CONVERSION: reads_all_partitions=True` mark, since the query reads all partitions of ops.job_runs)
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\tables\mart_dev__failed_runs\mart_dev__failed_runs.hql (generated Hive: CREATE EXTERNAL TABLE ... LOCATION '/data/team/mart_dev.db/failed_runs', then INSERT OVERWRITE)
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\tables\mart_dev__failed_runs\conversion\compare.md (Passed)
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\admin\workflows\convert\finished\failed_runs\ (batch folder after the compare)
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-1\my_work\team_project\admin\sent.csv (create and write of mart_dev.failed_runs recorded)

Documentation friction I hit, for the usability report:
- The convert names cell needed an edit that the Edit tool refuses on .ipynb ("Use the NotebookEdit to edit this file"), and NotebookEdit is not among my tools. I wrote a small JSON cell-text replacer at my_work\tools\fill_cell.py and used it for the names, decisions and step cells.
- I ran the wrong cell once: I counted the table notebook's cells from my own dump (which included markdown) instead of `--list`, so I ran the compare-Hive cell (6) before the export_hive cell (5). It only printed, so nothing changed. The docs are clear once `--list` is used; the mistake was mine.
- The convert step's "Done when" and the README's convert section do not say whether a batch's table must also be promoted for a dev-only job. I stopped at compare, which their Self-check treats as done.
- Nothing else was blocked. I did not read or change anything in _loop/.

I did not promote mart_dev.failed_runs to team_prod because the task asked only for the dev table; promotion is the convert Workflow's step 6, if you want it.
