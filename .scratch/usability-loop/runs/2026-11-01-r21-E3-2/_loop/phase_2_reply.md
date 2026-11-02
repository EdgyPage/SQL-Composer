DONE: mart_dev.daily_runs is built and written in the Dev Database (mart_dev), at /data/team/mart_dev.db/daily_runs, from the Daily summary of my_work/daily_runs_formula.xlsx. Its compare passed.

What I did, in order:
1. Read the workbook's Steps sheet. Step 12 says to run workbook_text.py on the workbook and to ask Copilot with Copilot files 15, 11 and 12. I ran main/copilot/workbook_text.py on my_work/daily_runs_formula.xlsx and wrote my_work/daily_runs_formula.txt. Then I asked Copilot (QUESTION/ATTACH) to convert it.
2. Copilot's reply is at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-2\copilot_reply_1.md. Its Hive for `daily` reads `<database>.job_runs`. The workbook says the source is ops.job_runs, so I used ops. Copilot's second block is the Total Row query. I did not keep it, because only mart_dev.daily_runs was asked for.
3. Set up a Project under my_work/mart_project/: I copied the download's sqlglot_composer folder beside it and ran project.start(). Then I set warehouse.py's conn to team_connection's conn, and set DEV = "mart_dev" and PROD = "team_prod" in admin/databases.py.
4. Saved Copilot's Hive as admin/workflows/convert/daily_runs.hql, with <database> set to ops. Ran the convert Workflow with NAME = "daily_runs" and FILES = ["daily_runs.hql"]. It made mart_dev.daily_runs, with its Table reference at references/mart_dev__daily_runs.py.
5. Answered the one open Decision, location, as /data/team/mart_dev.db/daily_runs, in the decisions cell. Ran write_decisions, then create, then run_tables (write). Skipped the seed step, because the table doesn't read itself. Ran compare_batch: "mart_dev.daily_runs: passed, every row". The batch moved to admin/workflows/convert/finished/daily_runs/.
6. Filled in the Table reference's two TODO lines (what one row is, and the does_not_add_up note). project.check() names no next step; it only notes the convert's opt-out, which blocks nothing.

Check of the result: SELECT * FROM mart_dev.daily_runs gives 2026-09-23: runs 3, total 60; 2026-09-24: runs 4, total 100. These match the workbook's own Daily sheet (12+18+30 = 60, 10+20+30+40 = 100). SHOW TABLES IN mart_dev lists only daily_runs, so no table of anyone else's was touched.

Not done, as the task didn't ask: nothing promoted to team_prod.

Files:
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-2\my_work\mart_project
- Convert batch and its Hive: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-2\my_work\mart_project\admin\workflows\convert\daily_runs.hql (and finished\daily_runs under admin\workflows\convert)
- Table folder: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-2\my_work\mart_project\tables\mart_dev__daily_runs
- Helper scripts I wrote in my_work (not part of the Toolbox): my_work\setup_convert.py, my_work\set_names.py, my_work\set_decisions.py, and my_work\mart_project\start_project.py.
