DONE: mart_dev.daily_runs is made in the Dev Database and written, with the 2 rows the colleague's workbook gives. Nothing was promoted to team_prod, since the task asked only for the Dev table.

What I did, all inside my_work/ (nothing in _loop/ was touched):
1. Read the README, the Steps sheet of my_work/daily_runs_formula.xlsx, and Copilot files 15, 11 and 12. I ran main/copilot/workbook_text.py on the workbook, which wrote my_work/daily_runs_formula.txt.
2. Asked Copilot to convert the workbook (QUESTION/ATTACH, as the loop asks). Its reply is at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-1\copilot_reply_1.md. Its one final, daily_runs, reads ops.job_runs, which the sample says it was copied from. Copilot's Hive matches the sample: 2026-09-23 gives 3 runs and 60 minutes; 2026-09-24 gives 4 runs and 100 minutes.
3. Built a Project at my_work/project: copied the Toolbox's sqlglot_composer into it and ran project.start(). Set warehouse.py's conn to team_connection's conn, with the work folder on the path. Set admin/databases.py to DEV = "mart_dev" and PROD = "team_prod".
4. Saved the query as my_work/project/admin/workflows/convert/daily_runs.hql. Filled the convert notebook's names cell with NAME = "daily_runs" and FILES = ["daily_runs.hql"]. Ran the convert Workflow one step at a time with run_notebook.py: convert, then the decisions cell, then write_decisions, create, seed, write, and compare.
5. The only open Decision was location, which I answered in the decisions cell as "/data/team/mart_dev.db/daily_runs". I filled the two TODO lines in its Table reference (references/mart_dev__daily_runs.py): a one-line description of a row, and does_not_add_up left empty because neither column is an average, ratio or distinct count.

Results:
- Dev table: mart_dev.daily_runs. Its Table folder is my_work/project/tables/mart_dev__daily_runs/. Its notebook is mart_dev__daily_runs.ipynb in that folder, and its Table reference is references/mart_dev__daily_runs.py.
- The warehouse shows 2026-09-23 with runs 3 and total 60, and 2026-09-24 with runs 4 and total 100. The compare step passed on every row. The batch moved to admin/workflows/convert/finished/daily_runs/.
- Before writing, mart_dev and team_prod were both empty, and the warehouse listed only the ops database, so nothing was overwritten.

Things to check:
- The converted read of ops.job_runs is not bounded by dt. The Toolbox added reads_all_partitions=True, which keeps what the original Hive did. It is marked in the logic cell at line 37 of tables/mart_dev__daily_runs/mart_dev__daily_runs.ipynb. A dt condition would avoid reading every partition, but it would change the query, so I left it alone.
- The location is set in the Table reference and was used in create. I did not check the warehouse's stored location with DESCRIBE.
- The Project's check() now shows only that note. It has no open items.
