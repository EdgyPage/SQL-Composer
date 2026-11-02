DONE: mart_dev.job_run_report is written in dev, from the colleague's Formula workbook, through Copilot and the convert Workflow, at LOCATION '/data/team/mart_dev.db/job_run_report'. It has 3 rows and passed its compare against the query.

Results check: job 1 has 4 runs, 0 failed, avg 16.75; job 2 has 3 runs, 1 failed, avg 17.67; job 3 has 2 runs, 1 failed, avg 30. I worked these out by hand from the workbook's job_runs rows and they match.

What I did, in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3:
1. Read the Steps sheet and ran main/copilot/workbook_text.py, which wrote my_work/run_report_formula.txt.
2. Asked Copilot with files 15, 11 and 12 and the .txt. Its reply is in copilot_reply_1.md in the work folder. Its Hive reads <database>.job_runs, which I filled with ops, the database the workbook's job_runs note names. Copilot reported no Parameters, no Keys and no typed-over values. This is the only question I asked, of the 5 allowed.
3. Made the Project at my_work/job_run_report: copied main/sqlglot_composer in, ran project.start(), and set warehouse.py to import conn from team_connection.py. admin/databases.py has DEV = "mart_dev" and PROD = "team_prod".
4. Saved the Hive as admin/workflows/convert/job_run_report.hql. The names cell has NAME = "job_run_report" and FILES = ["job_run_report.hql"], so the table takes the batch's name. The table is job_run_report, not job_report, because convert names a one-file batch's table after the batch.
5. Ran the convert Workflow cells: convert (1-2,4), the decisions cell with location /data/team/mart_dev.db/job_run_report (1-3,5), create (1-3,6), write (1-3,8) and compare (1-3,9). The key job_id was proposed and accepted, so it needed no answer.
6. Filled the two TODO lines in references/mart_dev__job_run_report.py. The description is one row per job, and does_not_add_up is ["avg_duration_mins"].

Notes for the docs:
- batch.md and checklist.md repeat the same "# CONVERSION: FROM(job_runs, reads_all_partitions=True)" note three times.
- The convert step 5 text says a step is done once step 4 is when no table reads itself. I skipped it on that basis, and did not run its seed cell.
- Probe scripts I wrote in my_work/ (start_project.py, check_rows.py, show_create.py) are not part of the deliverable.

Paths:
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\my_work\job_run_report
- Hive: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\my_work\job_run_report\admin\workflows\convert\job_run_report.hql
- Table reference: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\my_work\job_run_report\references\mart_dev__job_run_report.py
- Table notebook and compare: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-3\my_work\job_run_report\tables\mart_dev__job_run_report\
