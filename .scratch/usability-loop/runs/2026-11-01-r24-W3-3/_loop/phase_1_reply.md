DONE: Made mart_dev.failed_runs with the Toolbox from the team's query, checked it against the query, and it matches row for row. Work is in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project (the Project; the Toolbox copy is in its sqlglot_composer\ folder). Nothing in main\, from_your_team\ or _loop\ was edited.

What I did, in order:
1. Copied sqlglot_composer into my_work\team_project and ran project.start() from a script in that folder.
2. warehouse.py: replaced `conn = example_database` with the sys.path.append(r"...\2026-11-01-r24-W3-3") line and `from team_connection import conn`.
3. admin\databases.py: DEV = "mart_dev", PROD = "team_prod".
4. references Workflow (admin\workflows\references\references.ipynb): TABLES = ["ops.job_runs"]; ran step 1 (add_references). Key: checked run_id with the notebook's check_key recipe on both partitions (dt=2026-09-23 and dt=2026-09-24), both held, so DECISIONS = {"ops.job_runs": {"key": ["run_id"]}}; ran the write-decisions and refresh-reference-sheet steps; filled its TODO lines (docstring; does_not_add_up=["avg_retry_secs"]).
5. new_table Workflow (admin\workflows\new_table\new_table.ipynb): copied from_your_team\failed_runs.hql to admin\workflows\new_table\failed_runs.hql; names cell TABLES = ["mart_dev.failed_runs"], QUERIES = {"failed_runs": "failed_runs.hql"}; ran steps 1 to 8 in order. Its decision DECISIONS = {"mart_dev.failed_runs": {"location": "/data/team/mart_dev.db/failed_runs"}}; key job_id was proposed and is correct, so left as proposed; filled its docstring line.
6. Preview gave 2 rows; create and write sent to the warehouse (admin\sent.csv records both); compare_batch says "passed, every row", and the convert batch moved to admin\workflows\convert\finished\failed_runs\. Read back from the warehouse: mart_dev.failed_runs matches the team query, (2,1) and (3,1).
7. Ran the Table notebook top to bottom with run_notebook.py: every cell ran; its checklist says None open; it wrote its lineage and mart_dev__failed_runs.hql.

Key files:
- Table notebook: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project\tables\mart_dev__failed_runs\mart_dev__failed_runs.ipynb
- Table reference: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project\references\mart_dev__failed_runs.py
- Hive file: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project\tables\mart_dev__failed_runs\mart_dev__failed_runs.hql
- Compare report: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\team_project\tables\mart_dev__failed_runs\conversion\compare.md
- My helper for setting a notebook's code cell (my own script, not from the docs): C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W3-3\my_work\nbtool.py

Points where the docs were unclear or inconsistent (for the usability report):
- The new_table convert step's printed "Next:" line says to answer the decisions "then run its next steps", but the notebook's order is: preview, then reference_from_logic, then the decisions. I followed the notebook's order.
- Without Jupyter, the notebook files are CRLF JSON, and the Read tool shows them as cells rather than raw JSON, so editing a names cell needs a helper; the phase file's description was enough to write one.
- The convert note `# CONVERSION: reads_all_partitions=True` is kept as the original did. The team's query reads every partition of ops.job_runs with no dt filter; I left it, as the docs say to.
- The Table notebook's `refresh_reference_sheet("mart_dev.failed_runs")` cell takes a string where the other steps take a list; it ran without error.
