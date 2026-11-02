DONE: mart_dev.daily_runs is made in the Dev Database, at /data/team/mart_dev.db/daily_runs, and its compare passed. Read back from mart_dev: 2026-09-23 has 3 runs and 60 total minutes, 2026-09-24 has 4 runs and 100 total minutes, which matches the workbook's clean rows by hand.

What I did:
1. Read the Steps sheet of my_work/daily_runs_formula.xlsx and the README's "Have Copilot write it" and convert sections. I ran main/copilot/workbook_text.py on the workbook, which wrote my_work/daily_runs_formula.txt.
2. Asked Copilot with files 15, 11 and 12 and that text. Its reply is at copilot_reply_1.md in the work folder. Copilot named daily_runs as the summary final and left the Total Row as its own final. I used only the daily_runs query.
3. Saved the query as my_work/team_project/admin/workflows/convert/daily_runs.hql, with `<database>` filled in as `ops`, since the workbook's job_runs sheet says "Copied from ops.job_runs". I did not save the Total Row query, because the task asks only for mart_dev.daily_runs.
4. Made the Project in my_work/team_project: copied main/sqlglot_composer in and ran project.start(). I set admin/databases.py to DEV = "mart_dev" and PROD = "team_prod". In warehouse.py I replaced `conn = example_database` with `from team_connection import conn`, after a sys.path.append of the work folder.
5. Ran the convert Workflow (admin/workflows/convert/convert.ipynb) with NAME = "daily_runs" and FILES = ["daily_runs.hql"], as the README says for one query alone. Steps run: convert, write the decision, create, seed (nothing to seed), write, compare. I answered its one open Decision, location, in the decisions cell as "/data/team/mart_dev.db/daily_runs". Before creating anything I checked that no mart_dev tables existed.
6. Filled in the two TODO lines of references/mart_dev__daily_runs.py, the one-line description and does_not_add_up. Project.check() now shows everything registered, and the batch is done.

Things the user should know:
- The Hive hard-codes the two dates '2026-09-23' and '2026-09-24', which the workbook's summary groups typed in. A later day will not appear until the query gets a row for it.
- The workbook's CleanRuns Power Query was not saved in the file, so the Hive comes from its M text, as Copilot's map says. The table filter matches the typed CleanRuns rows.
- The convert step added a CONVERSION mark, reads_all_partitions=True, to the table notebook, as the original did. I left it as it is, since the compare passed.

Files:
- Hive: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-2\my_work\team_project\admin\workflows\convert\daily_runs.hql
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-2\my_work\team_project
- Table notebook: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-2\my_work\team_project\tables\mart_dev__daily_runs\mart_dev__daily_runs.ipynb
- Compare result: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-2\my_work\team_project\tables\mart_dev__daily_runs\conversion\compare.md (it says "passed, every row")

I did not touch _loop/ or main/.
