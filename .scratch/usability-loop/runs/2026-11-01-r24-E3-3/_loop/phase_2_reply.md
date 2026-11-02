DONE: The daily summary is now the Saved table mart_dev.daily_runs, in dev, at /data/team/mart_dev.db/daily_runs, and it passed its compare against the original query.

What I did, in order:
1. Read the Steps sheet of my_work/daily_runs_formula.xlsx and ran main/copilot/workbook_text.py on it. That wrote my_work/daily_runs_formula.txt.
2. Asked Copilot to convert the workbook, attaching files 15, 11 and 12 and the workbook text. Its reply is in copilot_reply_1.md in the work folder. Its Hive for the daily Table reads ops.job_runs, filters out blank and TEST statuses, and groups by dt, with the two dates typed in.
3. Built the Project at my_work/daily_runs_project/. I copied sqlglot_composer into it and ran project.start(). Then I set warehouse.py to import conn from team_connection, with the work folder on sys.path. I set DEV to mart_dev and PROD to team_prod in admin/databases.py.
4. Saved Copilot's query as admin/workflows/convert/daily.hql. In the convert notebook's names cell I set NAME = "daily_runs" and FILES = ["daily.hql"]. Then I ran the convert step, which made the Table folder tables/mart_dev__daily_runs/ and the Table reference references/mart_dev__daily_runs.py.
5. In the decisions cell I answered the one open Decision, location = /data/team/mart_dev.db/daily_runs, and ran write_decisions. The key (dt) was proposed by convert and I kept it.
6. I filled in the table reference's one-row description. I left its does_not_add_up as [], since runs and total minutes both add up across days.
7. Ran the create, seed and write steps (the seed step seeded nothing, since the table doesn't read itself). Then ran the compare step. It reported passed, with 2 rows each and the key holding. The batch folder moved to admin/workflows/convert/finished/daily_runs/.
8. project.check() reports the batch done.

Mistakes and notes:
- I ran cell 8 (run_tables) before write_decisions. It stopped at once, with "its Table reference has no location=", and sent.csv was still empty. Then I ran write_decisions and the steps in order. sent.csv now holds one create and one write, both for mart_dev.daily_runs.
- The Total Row was left out, as the task said.
- Keep in mind: the daily dt groups ('2026-09-23', '2026-09-24') are typed into the Hive, as the workbook's summary Table does. A later day won't appear in mart_dev.daily_runs until someone adds it to the query.
- The Toolbox notes a reads_all_partitions=True opt-out at tables/mart_dev__daily_runs/mart_dev__daily_runs.ipynb, cell 3, line 37, marked CONVERSION. It was kept from the original and does not block anything.

Key files:
- my_work/daily_runs_project/admin/workflows/convert/daily.hql
- my_work/daily_runs_project/admin/workflows/convert/convert.ipynb
- my_work/daily_runs_project/references/mart_dev__daily_runs.py
- my_work/daily_runs_project/tables/mart_dev__daily_runs/conversion/compare.md
- my_work/daily_runs_project/admin/sent.csv
