DONE: mart_dev.daily_runs is built in the Dev Database at /data/team/mart_dev.db/daily_runs, with 2 rows, and its compare passed. Copilot's answer is in C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-1\copilot_reply_1.md.

What I did, in order:
1. Converted the workbook with Copilot as the Steps sheet says (step 12). I ran `main\copilot\workbook_text.py` on `my_work\daily_runs_formula.xlsx`, which wrote `my_work\daily_runs_formula.txt`, and asked Copilot with files 15, 11 and 12 plus that text. Copilot gave one final, `daily` (the Daily summary), with its Total Row left out as the Steps sheet allows. Its one `<...>` was `<database>`, which I filled with `ops`, as the Raw sheet's note says the rows were copied from ops.job_runs.
2. Made the Project in `my_work\project\`: copied `main\sqlglot_composer` in and ran `project.start()`.
3. Set `my_work\project\warehouse.py` to `from team_connection import conn` (with the work folder appended to sys.path), and `admin\databases.py` to DEV = "mart_dev", PROD = "team_prod".
4. Wrote `my_work\project\admin\workflows\convert\daily_runs.hql` from Copilot's Hive, with `ops.job_runs`.
5. Set the convert notebook's names cell to NAME = "daily_runs", FILES = ["daily_runs.hql"], then ran its steps by cell: convert (cells 1, 2, 4), the decision (cell 3, DECISIONS = {"mart_dev.daily_runs": {"location": "/data/team/mart_dev.db/daily_runs"}}), write_decisions (cell 5), create (cell 6), seed (cell 7, nothing to seed), write (cell 8), compare (cell 9).

Check results:
- Read back from the warehouse: mart_dev.daily_runs has (2026-09-23, 3, 60) and (2026-09-24, 4, 100). I checked both against the workbook's Clean rows by hand: they match.
- DESCRIBE FORMATTED gives Location /data/team/mart_dev.db/daily_runs.
- `project.check()` reports the batch finished, and admin/sent.csv records the create and the write.

Things you should know:
- The Hive hard-codes the two dt groups, '2026-09-23' and '2026-09-24', as Copilot's file 15 specifies. A later day will not appear in the table until its group is added to the query.
- The Toolbox's generated logic has a `# CONVERSION: reads_all_partitions=True` mark, which it adds because the Hive reads ops.job_runs without filtering its partition column dt. `project.check()` says this blocks nothing and the compare confirmed the rows.
- The reference `references/mart_dev__daily_runs.py` still has two TODO lines (one-line description of a row, and any average or distinct-count columns). They block nothing, and I left them.
- Nothing under `_loop/` was touched. The original workbook and `from_your_team/` are unchanged.

Files I wrote or changed, all under the work folder:
- `my_work\daily_runs_formula.txt`
- `my_work\project\` (the Project, including warehouse.py and admin\databases.py)
- `my_work\project\admin\workflows\convert\daily_runs.hql`
- `my_work\project\admin\workflows\convert\convert.ipynb` (names and decisions cells)
- `my_work\project\admin\workflows\convert\finished\daily_runs\`
- `my_work\project\tables\mart_dev__daily_runs\`
- `my_work\project\references\mart_dev__daily_runs.py`
