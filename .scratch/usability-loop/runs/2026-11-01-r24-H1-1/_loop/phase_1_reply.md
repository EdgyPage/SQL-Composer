DONE: Converted your team's weekly.hql into three Saved tables in mart_dev, compared each with its original on both Partitions, and promoted them to team_prod. Every table is written in its Database, and each new table's folder is /data/team/<database>.db/<name>. The originals in mart are untouched.

Work folder: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-H1-1\my_work\team_project (the Project: the Toolbox copied in as sqlglot_composer, started with project.start(), warehouse.py pointed at team_connection.conn, admin/databases.py with DEV = "mart_dev" and PROD = "team_prod").

What was done, in the order the convert and promote Workflows give:
1. Saved weekly.hql as admin/workflows/convert/weekly.hql. Set the convert names cell: NAME = 'weekly', FILES = ['weekly.hql'], DATABASE = 'mart', RENAME mapping each mart.<name> to <name>, so the copies are mart_dev.team_fails, mart_dev.job_runs_counted and mart_dev.job_fails_counted. Ran project.convert. The temporary failed_runs was folded into mart_dev.team_fails as a Derived table, as the Workflow does for staging tables.
2. Decisions: location for each table, /data/team/mart_dev.db/<name>. The proposed Keys were kept. I filled the two TODO lines of each new Table reference. The batch's folder is now admin/workflows/convert/finished/weekly/.
3. Checked the mart_dev and team_prod databases were empty before creating anything. Created the three tables, ran the seed step (nothing reads itself, so none), then wrote them with run_tables.
4. Compared each with its original with project.compare_batch: all three passed on the latest Partition, dt = 2026-09-24. I also ran it with partition={"dt": "2026-09-23"}: all three passed.
5. Promote: names cell TABLES = ["mart_dev.team_fails", "mart_dev.job_runs_counted", "mart_dev.job_fails_counted"]. project.promote produced team_prod.team_fails, team_prod.job_runs_counted and team_prod.job_fails_counted, with location= set to /data/team/team_prod.db/<name>. Created the three prod tables, ran the seed step (none), wrote them with run_tables, and refreshed the Reference sheet.
6. Verified read-only: each team_prod table has the same Partitions (2026-09-23, 2026-09-24) and the same row counts and per-dt sums as its original. project.check() reports the convert batch done and nothing open.

Points you should know:
- Three conversion marks remain in the Table notebooks (reads_all_partitions=True on the FROM of ops.job_runs and ops.job_owners, and many_matches=True on the join to job_owners). They keep what the original did; the compare passed with them.
- Dev and prod tables are external tables with ORC storage (the Toolbox default), while the original CREATE statements had no STORED AS clause.
- I did not re-run the compare on prod (the Workflow doesn't), I checked prod by row counts and per-dt sums.

Friction I hit (for the usability report):
- Jupyter is unavailable, so I ran the notebooks with run_notebook.py. Its --cells numbers follow the code cells in order, not the notebook's visible steps. I first ran --cells 5 for the promote call, which was write_decisions, and got a NameError. --list showed the right number, 4.
- The convert how-to says DATABASE is the database of a table the Hive names without one. It does not say what that means for a TEMPORARY table like failed_runs. I set DATABASE = 'mart', which made it mart.failed_runs (folded, so it never reached a warehouse).
- The convert steps don't say how to compare a second Partition once the batch has moved to finished/. The how-to shows compare_batch with partition=, and it worked from a script after the move.

Files: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-H1-1\my_work\team_project\admin\workflows\convert\convert.ipynb, C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-H1-1\my_work\team_project\admin\workflows\promote\promote.ipynb, and the three Table references under C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-H1-1\my_work\team_project\references\ (mart_dev__*.py and team_prod__*.py).
