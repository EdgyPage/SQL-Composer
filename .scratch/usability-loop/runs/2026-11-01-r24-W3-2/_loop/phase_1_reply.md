Made mart_dev.failed_runs from from_your_team/failed_runs.hql with the Toolbox, written in dev and checked against the query. Its compare passed.

Result
- The table: mart_dev.failed_runs, location /data/team/mart_dev.db/failed_runs. The warehouse shows it in mart_dev with 2 rows (job_id 2 and 3, fails 1 each), the same as the query's own rows.
- Nothing was promoted to team_prod. The task did not ask for it, and the convert Workflow's promote step was not run.
- Nothing already in mart_dev or team_prod was touched. Before creating, SHOW TABLES IN mart_dev and SHOW TABLES IN team_prod were both empty, so there was no existing table of someone else's to protect.

What I did, in order
1. Copied main/sqlglot_composer into my_work/team_project and ran project.start() from a plain Python call, print(project.start()), because Jupyter can't open here. The README's "Start a Project" steps 1 to 4 covered this.
2. Edited warehouse.py: replaced `conn = example_database` with the sys.path.append line and `from team_connection import conn`, as the README's step 5 shows. Checked that query and execute reach the connection.
3. Set admin/databases.py: DEV = "mart_dev", PROD = "team_prod".
4. Copied from_your_team/failed_runs.hql into admin/workflows/convert/ and filled the convert notebook's names cell: NAME = "failed_runs", FILES = ["failed_runs.hql"]. The README's convert section says this makes mart_dev.failed_runs.
5. Ran the convert Workflow's cells with run_notebook.py: cell 4 (convert), then the decisions cell with {"mart_dev.failed_runs": {"location": "/data/team/mart_dev.db/failed_runs"}}, then cells 5 (write decisions), 6 (create), 7 (seed, which correctly sent nothing), 8 (run_tables), and 9 (compare_batch with query=query). Compare output: "Passed: every row". The batch moved to admin/workflows/convert/finished/failed_runs/.
6. Filled the Table reference's TODO lines: a one-line description and deleting the does_not_add_up TODO, since fails is a count.
7. Ran the table notebook's cells top to bottom with run_notebook.py. It ran with no errors and exported the lineage and the .hql file.
8. project.check() reports the registry as complete, with the batch done.

Files
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project
- Convert notebook: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project\admin\workflows\convert\convert.ipynb
- Table reference: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project\references\mart_dev__failed_runs.py
- Table folder: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project\tables\mart_dev__failed_runs
- Generated Hive: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project\tables\mart_dev__failed_runs\mart_dev__failed_runs.hql
- Compare result: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-2\my_work\team_project\tables\mart_dev__failed_runs\conversion\compare.md

Things to look at
- The converted logic has `FROM(r, reads_all_partitions=True)` with a `# CONVERSION:` mark that says "check it". The Toolbox added it on its own, because the query filters no dt partition column and would otherwise be refused. I kept it, since it matches the original, but the user may want to review it.
- The Table reference's key=["job_id"] was proposed by the Toolbox and is correct, since the query groups by job_id. No key answer was needed.
- The main/ folder and _loop/ were not written to by me. My Project's own copy of the Toolbox is the one that was imported.
- The convert how-to's example uses the Starter project, but the README's Start a Project steps worked for this task. Both paths led to the convert Workflow.

DONE: converted from_your_team/failed_runs.hql into mart_dev.failed_runs (location /data/team/mart_dev.db/failed_runs) with the Toolbox, written in dev, and its compare against the query passed. Not promoted to team_prod. Project is at my_work/team_project.
