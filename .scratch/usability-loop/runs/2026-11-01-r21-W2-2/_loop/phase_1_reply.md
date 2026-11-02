DONE: Made mart_dev.runs_per_day with the Toolbox and wrote it to the Dev Database. It holds one row per job and day of ops.job_runs for 2026-09-23 and 2026-09-24 (6 rows: job_id, runs, dt), partitioned by dt, with its location set to /data/team/mart_dev.db/runs_per_day. The table is written and checked: a SELECT on it returns the same 6 rows as the preview, and SHOW PARTITIONS lists dt=2026-09-23 and dt=2026-09-24.

What I did, in order:
1. Copied main/sqlglot_composer into my_work/runs_project and ran project.start(). Read the README (sections 1 to 6, the Workflows, and the how-to for Save a table) and the new_table and references notebooks it points to.
2. warehouse.py: replaced `conn = example_database` with a sys.path.append of the work folder and `from team_connection import conn`. admin/databases.py: DEV = "mart_dev", PROD = "team_prod".
3. references Workflow, with TABLES = ["ops.job_runs"]: project.add_references wrote references/ops__job_runs.py. Its Key decision was key=["run_id"], which I checked with check_key on dt 2026-09-23 and 2026-09-24. I filled in its TODO lines and refreshed the Reference sheet.
4. new_table Workflow, with TABLES = ["mart_dev.runs_per_day"] and QUERIES = {}: project.new_table made tables/mart_dev__runs_per_day/. Its logic cell (code cell 2 of its Table notebook) is between(job_runs.dt, "2026-09-23", "2026-09-24") grouped by job_id and dt, with count_rows as "runs", PARTITIONED_BY = ["dt"]. I ran preview, reference_from_logic (columns job_id bigint, runs bigint, dt string, Key job_id and dt, both proposed), then answered the location decision in DECISIONS, then project.write_decisions.
5. Ran create and write through execute (run_tables). sent.csv records the create and the write. Then the notebook's lineage, Hive (mart_dev__runs_per_day.hql) and Reference sheet cells.
6. project.check() reports every Table folder, Table reference and Building block registered.

Files:
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W2-2\my_work\runs_project
- Logic and Table notebook: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W2-2\my_work\runs_project\tables\mart_dev__runs_per_day\mart_dev__runs_per_day.ipynb
- Table reference: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W2-2\my_work\runs_project\references\mart_dev__runs_per_day.py
- Hive file: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W2-2\my_work\runs_project\tables\mart_dev__runs_per_day\mart_dev__runs_per_day.hql

Friction the docs could have made clearer (no blocking errors):
- The README never says what the Key of ops.job_runs should be. I took key=["run_id"] from the how-to example and verified it with check_key.
- In the notebooks, `--cells` numbers count code cells only. In new_table, the decisions cell is code cell 3 and write_decisions is code cell 7. This is easy to misread from the notebook's own cell numbers.
- In a Windows Python string, a path with backslashes breaks (unicode escape). Forward slashes work for sys.path.append.
- Running a Python script from the scratchpad folder hit a stray inspect.py there that shadows the standard library. Running with -I fixed it. This is my environment, not the Toolbox.
