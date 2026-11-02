DONE: mart_dev.team_report is written in dev, and its compare passed, every row (3 rows each).

Copilot's reply (copilot_reply_1.md) gave one final, teams. I saved its Hive as my_work/team_project/admin/workflows/convert/team_report.hql, with `ops` in place of `<database>`. The Hive has no angle-bracket names left.

What I did, in my_work/team_project (the Project):
1. Copied sqlglot_composer in and ran project.start(). Set warehouse.py to `sys.path.append(r"...\2026-11-01-r24-E2-3")` and `from team_connection import conn`. Set admin/databases.py to DEV = "mart_dev", PROD = "team_prod".
2. Ran main/copilot/workbook_text.py with -I on my_work/team_report_formula.xlsx, which wrote my_work/team_report_formula.txt.
3. In convert.ipynb, the names cell is NAME = "team_report" and FILES = ["team_report.hql"]. The decisions cell is DECISIONS = {"mart_dev.team_report": {"location": "/data/team/mart_dev.db/team_report"}}.
4. Ran the convert cells in order: convert (cell 4), write_decisions (cell 5), create (cell 6), seed (cell 7, which seeded nothing because no table reads itself), run_tables (cell 8), compare (cell 9). Each step ran through run_notebook.py with --cells.
5. The Project's own check is clean. project.check() reports "Done: each convert batch below", and the team_report batch has moved to admin/workflows/convert/finished/team_report/.

Things to know:
- Copilot's Hive reads ops.job_runs and ops.jobs, with the team join from the XLOOKUP. It writes the summary's groups (data, finance, web) into the query, as the map notes, so a team added later won't appear until the query is changed.
- The convert wrote two opt-outs, reads_all_partitions=True and many_matches=True, marked `# CONVERSION:` in tables/mart_dev__team_report/mart_dev__team_report.ipynb. The notes say they keep what the original did and block nothing. I left them.
- The Key (team) was proposed by convert and accepted; no answer was needed.
- Two TODO lines in references/mart_dev__team_report.py are unfilled: a one-line description of a row, and does_not_add_up=[]. The notes say they wait on nothing.

Paths:
- Table reference: my_work/team_project/references/mart_dev__team_report.py
- Table folder: my_work/team_project/tables/mart_dev__team_report/
- Compare report: my_work/team_project/tables/mart_dev__team_report/conversion/compare.md
- Send log: my_work/team_project/admin/sent.csv (a create and a write of mart_dev.team_report)

I did not touch _loop/ or the main/ download, and I wrote nothing to the warehouse beyond the one table in mart_dev.
