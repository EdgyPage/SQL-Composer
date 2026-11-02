DONE: Made mart_dev.runs_per_day with the Toolbox (sqlglot Composer 8.2) and wrote it to the Dev Database. Its location is /data/team/mart_dev.db/runs_per_day, and it is partitioned by dt. The table has one row per job and day for 2026-09-23 and 2026-09-24, with job_id, runs and dt. The 6 rows read back as: 09-23 has job 1 = 2, job 2 = 2, job 3 = 1; 09-24 has job 1 = 2, job 2 = 1, job 3 = 1. Nothing was promoted to team_prod, since the task didn't ask for it.

What I did, in order:
1. Copied the Toolbox's sqlglot_composer folder from main/ into my_work/mart_project/ and ran project.start().
2. Set warehouse.py's conn to the team connection, using the README's sys.path.append plus `from team_connection import conn` lines. Set admin/databases.py to DEV = "mart_dev" and PROD = "team_prod".
3. Ran the references Workflow for ops.job_runs. I answered its Key as ["run_id"], after checking with a direct query that run_id is unique (9 rows, 9 distinct). I also filled in its one-line description and does_not_add_up=["avg_retry_secs"], and check_references.ipynb passed.
4. Ran the new_table Workflow with TABLES = ["mart_dev.runs_per_day"] and QUERIES = {}, since I wrote the logic myself. Its Table notebook logic is: SELECT job_id, COUNT(*) AS runs, dt FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY job_id, dt, partitioned by dt. The Table reference's Key is proposed from the logic as (job_id, dt). I answered the location decision, filled in its TODO lines, ran preview (rows matched my direct check), then ran create and write. admin/sent.csv records both. Then I ran the Table notebook's lineage, export_hive and Reference sheet cells. project.check() reports everything registered.

Files, all under C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W2-3\my_work\mart_project\:
- tables\mart_dev__runs_per_day\mart_dev__runs_per_day.ipynb (logic), mart_dev__runs_per_day.hql, lineage\
- references\mart_dev__runs_per_day.py and references\ops__job_runs.py
- admin\workflows\new_table\new_table.ipynb and admin\workflows\references\references.ipynb (names and decisions cells filled)
- admin\databases.py and warehouse.py
Helper scripts I made are in my_work\ (set_cell.py, fill_md.py, and some check scripts). I did not touch _loop/, main/ or run_notebook.py.

Usability notes, where the docs made me stop or guess:
- The Save a table how-to and new_table's step 1 say to give each source table a Table reference with the references Workflow first. I only found that by reading the Template and the Workflow, so it is worth saying up front in the new_table text.
- The Table notebook's Template says to fill each <...> and to add `between` to the import, but the placeholder list is spread across the header, the logic cell and the markdown. The markdown TODO line ("say in one line what one row ... is") must be edited by hand, and it is easy to miss.
- I had to answer the references Key before I knew whether run_id was unique. The how-to only says to check it later with check_key, so a reader has no guidance on how to test it first.
- The Table reference's TODO lines (description, does_not_add_up) "wait on nothing" according to the Workflow output, so they are easy to leave in; I filled them by hand.
- Editing a notebook without Jupyter means editing its JSON. The run_notebook.py --list and --cells flow worked well for this, with the Workflow's cell numbers counted from the code cells only.
