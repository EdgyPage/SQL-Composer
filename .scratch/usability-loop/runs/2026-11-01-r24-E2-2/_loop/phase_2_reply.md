DONE: mart_dev.team_report is written in dev from the Teams summary, through the convert Workflow, and its compare passed. It is at /data/team/mart_dev.db/team_report.

What I did, in order:
1. Read the README (Start a Project, the Workflows, Have Copilot write it), Copilot files 00, 11, 12 and 15, and the Formula workbook's Steps sheet. I ran main/copilot/workbook_text.py on my_work/team_report_formula.xlsx, which wrote my_work/team_report_formula.txt.
2. Asked Copilot to convert the workbook (QUESTION and ATTACH, as phase_2.md says). Its reply is in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\copilot_reply_1.md. The map: sources ops.jobs and ops.job_runs. job_runs is a step, read as a CTE. The final is teams, a summary with a GROUP BY, named team_report by the batch name. Copilot wrote no `<...>`, so nothing needed filling in.
3. Made the Project at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\my_work\team_project: a copy of the Toolbox, project.start(), and warehouse.py now sets conn from team_connection (via sys.path). admin/databases.py has DEV = "mart_dev" and PROD = "team_prod".
4. Saved the Hive as admin/workflows/convert/team_report.hql, and set the convert names cell to NAME = "team_report", FILES = ["team_report.hql"].
5. Ran the convert cell. Its one open Decision was location, which I answered in the decisions cell as "/data/team/mart_dev.db/team_report". The proposed Key (team) was right for one row per team, so I left it.
6. Filled the Table reference's TODO lines (references/mart_dev__team_report.py): the row description, and the does_not_add_up line deleted.
7. Ran create (create) and the seed check (none reads itself), then write (write), then compare (passed).

The dev table holds, read back from mart_dev.team_report: data 4 runs, 67 minutes; finance 5 runs, 113 minutes; web 0 runs, 0 minutes. I checked these against the job_runs rows by hand. web has no runs in job_runs because its only job, cache_warm, has none.

Things to know:
- Copilot's Hive hard-codes the three team names (data, finance, web). A team added later won't appear unless it is added to that list, as Copilot's map notes.
- project.check() notes two CONVERSION opt-outs kept from the original (reads_all_partitions=True and many_matches=True, in the logic cell). Both are the original's behaviour, and the compare passed with them.
- The convert batch folder moved to admin/workflows/convert/finished/team_report/, as the compare step says. The team_report.hql I wrote is still in admin/workflows/convert/.
- Earlier in this run I called SubagentHandback with a STUCK report while the Copilot question was pending, before the coordinator's message arrived. The report was delivered; this one completes the job.
- Nothing outside my_work/team_project and the work folder was written. _loop/ was not touched. The ops tables and the team's /data folders other than mart_dev.db/team_report were not changed.

Key paths:
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\my_work\team_project\admin\workflows\convert\team_report.hql
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\my_work\team_project\tables\mart_dev__team_report\mart_dev__team_report.ipynb
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\my_work\team_project\tables\mart_dev__team_report\conversion\compare.md
- C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E2-2\my_work\team_project\admin\sent.csv (the create and write records)
