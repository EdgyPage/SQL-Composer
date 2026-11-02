DONE: mart_dev.team_report is built in dev, passes its compare, and sits at /data/team/mart_dev.db/team_report.

What I did, in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E2-2 (my_work/project is the Project):
1. Ran main\copilot\workbook_text.py on my_work\team_report_formula.xlsx, which wrote my_work\team_report_formula.txt.
2. Asked Copilot to convert it with files 15, 11 and 12 and that text. Its answer is in copilot_reply_1.md. It has one final, the teams summary, with job_runs as a step and jobs as a source. I filled its <database> with ops, which the warehouse's SHOW DATABASES confirmed.
3. Copied main\sqlglot_composer into my_work\project and ran project.start(). warehouse.py now imports conn from team_connection.
4. Ran project.add_references for ops.jobs and ops.job_runs, filled in their TODO lines (keys job_id and run_id), and checked both.
5. Set DEV = "mart_dev" and PROD = "team_prod" in admin/databases.py. Saved Copilot's query as admin/workflows/convert/teams.hql.
6. Named the batch NAME = "team_report", FILES = ["teams.hql"] in the convert notebook. Ran its convert cell. It made tables/mart_dev__team_report with its checklist.
7. Answered the location decision as /data/team/mart_dev.db/team_report in the decisions cell, which wrote it into references/mart_dev__team_report.py. Filled in that reference's two TODO lines.
8. Ran create, seed (nothing to seed) and write for the table, then compare. The compare passed, and the batch moved to admin/workflows/convert/finished/team_report/. project.check() reports nothing open.

Checks: mart_dev.team_report has 3 rows (data 4 runs / 67 mins, finance 5 / 113, web 0 / 0), which match the workbook's teams sheet. Its Location is /data/team/mart_dev.db/team_report.

Not done, as the task didn't ask: no promote to team_prod. I did not touch _loop/ or any table someone else made.

Notes: earlier the warehouse.py edit failed on a backslash escape in a heredoc, and I fixed it with the Edit tool.
