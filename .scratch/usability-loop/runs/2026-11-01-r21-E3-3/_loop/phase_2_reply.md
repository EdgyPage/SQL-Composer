DONE: Built mart_dev.daily_runs from the colleague's Daily summary, and it is written in the Dev Database at /data/team/mart_dev.db/daily_runs. Its rows match the colleague's Daily summary: 2026-09-23 has 3 runs and 60 minutes, 2026-09-24 has 4 runs and 100 minutes. Nothing was written to team_prod, and nothing in from_your_team/ or _loop/ was touched.

What I did, in order:
1. Read the Toolbox README (main/.github/README.md), its "Have Copilot write it" section and its Workflows. The Steps sheet of my_work/daily_runs_formula.xlsx says to attach Copilot files 15, 11 and 12 with the workbook as text.
2. Ran main/copilot/workbook_text.py on the workbook, which wrote my_work/daily_runs_formula.txt. I asked Copilot to convert it. Its answer is at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\copilot_reply_1.md.
3. Started a Project at my_work/project (a copy of the Toolbox's sqlglot_composer, plus admin/, references/, building_blocks/, tables/ and warehouse.py). I set warehouse.py to import conn from team_connection, and set admin/databases.py to DEV = "mart_dev", PROD = "team_prod".
4. References workflow: named ops.job_runs (the source the colleague's Raw sheet names, "Copied from ops.job_runs"). Filled the TODO lines (one row is one job run, Key run_id, does_not_add_up avg_retry_secs). check_key passed on the latest partition, 2026-09-24. check_table_reference says it matches the warehouse.
5. Convert workflow: saved Copilot's daily query as admin/workflows/convert/daily_runs.hql with <database> filled in as ops, and left out the Total Row query. Named the batch daily_runs. Answered the location Decision as /data/team/mart_dev.db/daily_runs and accepted the proposed Key dt. Then ran create, seed (nothing to seed), write, and compare. The compare passed. project.check() now shows only a note about reads_all_partitions, which blocks nothing.

Things you should know before you use it:
- The Hive hard-codes the two dates in the sample, '2026-09-23' and '2026-09-24', as typed groups, which is how the workbook's Daily sheet was built. A later day in ops.job_runs will not appear in the table. The query also reads all partitions (the convert's opt-out, reads_all_partitions=True), because the dates aren't a WHERE on dt.
- Source is ops.job_runs. The colleague's note gives that name, and Copilot's <database> was filled from it.
- Key: the Toolbox proposed dt, which fits one row per day. I accepted it.
- I ran the convert's first cell a second time by mistake. It regenerated the batch's fresh/ copy but kept my reference edits; I checked that.

Files:
- Table reference: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\my_work\project\references\mart_dev__daily_runs.py
- Saved query: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\my_work\project\admin\workflows\convert\finished\daily_runs\scripts\daily_runs.hql
- Project's warehouse and databases: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\my_work\project\warehouse.py and ...\my_work\project\admin\databases.py
