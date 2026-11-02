DONE: mart_dev.job_run_report is written in mart_dev, at /data/team/mart_dev.db/job_run_report, from the colleague's Report sheet, and its compare passed (3 rows, same as the query).

What I did, in order:
1. Read the Toolbox README (section 1 Start a Project, the Have Copilot write it section, the convert Workflow) and the Formula workbook's Steps sheet.
2. Ran `main/copilot/workbook_text.py` on `my_work/run_report_formula.xlsx`, which wrote `my_work/run_report_formula.txt`.
3. Asked Copilot with files 15, 11, 12 and that text. Its reply (`copilot_reply_1.md`) gave one query for the final job_report, with `<database>` as the only name to fill in.
4. Wrote that query as `admin/workflows/convert/job_run_report.hql` with `<database>` replaced by `ops` (it reads ops.job_runs, per the workbook's Runs note), and set the convert names cell to NAME = 'job_run_report', FILES = ['job_run_report.hql'].
5. Set up a Project in `my_work/mart_project`: copied `sqlglot_composer` in and ran `project.start()` from `start.py`. In `warehouse.py`, `conn` now comes from `team_connection`. In `admin/databases.py`, DEV = "mart_dev" and PROD = "team_prod".
6. Ran the convert Workflow: convert, the decisions cell with location "/data/team/mart_dev.db/job_run_report", write decisions, create, seed (no table reads itself), write, compare. The compare passed. The batch folder moved to admin/workflows/convert/finished/job_run_report/.
7. Filled in the TODO lines I could: the mart_dev.job_run_report reference (one-line description, does_not_add_up=["avg_duration_mins"]) and the ops.job_runs reference (description, key=["run_id"], does_not_add_up=["avg_retry_secs"]). The key check on ops.job_runs passed on its latest Partition. Check the last two against your own knowledge of the table: I chose them from the column names and the sample, the warehouse didn't confirm them.

Left as they are: the three `# CONVERSION: reads_all_partitions=True` opt-outs in the table's logic cell (project.check() lists them as noted, blocking nothing). The Hive has no dt filter, so it reads all partitions, as the original did.

Things to know:
- The Runs sample has one row with a blank status and avg_retry_secs (run_id 98) and one with status TEST. Copilot's Hive counts them in the totals as the workbook's Excel formulas do, and the compare agreed.
- The colleague's Excel workbook wasn't changed, and no table other than mart_dev.job_run_report was written. Prod (team_prod) wasn't touched.

Files:
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-2\my_work\mart_project
- Copilot's Hive as saved: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-2\my_work\mart_project\admin\workflows\convert\job_run_report.hql
- Compare result: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-2\my_work\mart_project\tables\mart_dev__job_run_report\conversion\compare.md
- Copilot's reply: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E1-2\copilot_reply_1.md
