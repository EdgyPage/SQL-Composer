DONE: Made mart_dev.team_fails from from_your_team/weekly_fails.hql with the Toolbox's convert Workflow. It is written in the Dev Database at /data/team/mart_dev.db/team_fails, and it matches the original mart.team_fails on both of its Partitions.

What I did, all inside the work folder C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W1-1:
1. Copied main/sqlglot_composer into my_work/team_project/ and ran project.start() there. Edited my_work/team_project/warehouse.py to replace `conn = example_database` with the team_connection lines (sys.path.append of the work folder, then `from team_connection import conn`). Set admin/databases.py to DEV = "mart_dev", PROD = "team_prod".
2. Saved the script as my_work/team_project/admin/workflows/convert/weekly_fails.hql. Filled the convert notebook's names cell (NAME = 'team_fails', FILES = ['weekly_fails.hql'], RENAME = {'mart.team_fails': 'team_fails'}, so the copy is mart_dev.team_fails; left out, it would have been mart_dev.team_fails_mart). Ran step 1 (project.convert). It added Table references for ops.job_runs and ops.job_owners from DESCRIBE.
3. Answered the one open Decision in the decisions cell: DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}. Ran write_decisions. Filled in the Table reference's description line and removed its does_not_add_up TODO (fails is a COUNT, so nothing there is an average or ratio). Key (team, dt) was proposed by convert and left as proposed.
4. Ran the table notebook's preview and Hive cells, and exported its Hive. The compare_hive check said the Hive matches the original's query.
5. Ran the convert steps in order: create (the CREATE EXTERNAL TABLE with LOCATION '/data/team/mart_dev.db/team_fails', confirmed by DESCRIBE FORMATTED), seed (nothing to seed, since the script doesn't read its own table), and write (run_tables: "worked"). Then compare_batch: passed on dt = '2026-09-24', the latest Partition both hold.
6. compare_batch reports only the latest Partition, so I also ran compare_batch with partition={"dt": "2026-09-23"} (the README's step for another Partition). It passed, with 2 rows on each side. Partition row counts match: 2026-09-23 has 2 rows and 2026-09-24 has 1 in both tables. project.check() reports nothing open, and the batch folder moved to admin/workflows/convert/finished/team_fails/.

Files that matter (under my_work/team_project/ unless noted):
- warehouse.py, admin/databases.py
- admin/workflows/convert/convert.ipynb (names and decisions cells filled)
- admin/workflows/convert/weekly_fails.hql
- references/mart_dev__team_fails.py (location set; description filled)
- tables/mart_dev__team_fails/conversion/compare.md (both Partitions passed)
- tables/mart_dev__team_fails/mart_dev__team_fails.hql
- admin/sent.csv (create and write recorded)

Left as the converter wrote them, for you to decide: the table's logic cell has three opt-outs marked `# CONVERSION:` (FROM(r, reads_all_partitions=True), JOIN(o, many_matches=True), JOIN(o, reads_all_partitions=True)). The Toolbox refuses the logic without them, and the compare shows the rows match. Their marks say what to change if you want the opt-outs gone. I did not promote the table to team_prod, since the task didn't ask for it.

Housekeeping: I used a scratch helper script in the system scratchpad to edit the notebook's JSON, and removed it afterwards. Nothing else was written outside the work folder. Friction points for the docs: the README's step 9 says the compare step checks the latest Partition only, which I followed; and there were no blocking problems in the Workflow steps.
