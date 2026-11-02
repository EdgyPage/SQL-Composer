DONE: Made mart_dev.team_fails with the Toolbox, from from_your_team/weekly_fails.hql, and checked it against mart.team_fails. Nothing was promoted, since the job asked only for the Dev copy.

What I did:
- Copied the Toolbox's sqlglot_composer folder from main/ into my_work/team_project/ and ran project.start() there. Set warehouse.py to import conn from team_connection (with sys.path.append of the work folder, as the message says). Set admin/databases.py to DEV = "mart_dev", PROD = "team_prod".
- Saved weekly_fails.hql beside admin/workflows/convert/convert.ipynb, and filled its names cell: NAME = "team_fails", FILES = ["weekly_fails.hql"], RENAME = {"mart.team_fails": "team_fails"} (so the copy is mart_dev.team_fails, not mart_dev.team_fails_mart).
- Ran step 1 (convert), then answered the one open Decision in the decisions cell: location = "/data/team/mart_dev.db/team_fails". The proposed Key (team, dt) was kept, since it matches the query's GROUP BY. Ran the write-decisions step.
- Filled the two TODO lines in references/mart_dev__team_fails.py (the one-row description and does_not_add_up, which is none, since fails is a count).
- Step 4 created mart_dev.team_fails (sent.csv records the create). Step 5 seeded nothing, since the script does not read its own table. Step 6 wrote it (sent.csv records the write).
- Step 7 (compare_batch) passed on dt = '2026-09-24'. The Workflow's compare note says the other Partition was not compared, so I ran compare_batch with partition={"dt": "2026-09-23"} from a small script in my_work (not a new notebook cell). It passed too. The batch moved to admin/workflows/convert/finished/team_fails/, and project.check() names it done.
- Independent check with team_connection: SELECT of mart.team_fails and mart_dev.team_fails, all rows, ORDER BY dt, team. The two frames are equal (3 rows: data 7 and finance 7 on 2026-09-23, finance 14 on 2026-09-24).

Table folder: /data/team/mart_dev.db/team_fails (its location in references/mart_dev__team_fails.py). The original mart.team_fails was only read, never written.

Notes for the usability loop:
- The convert how-to and README steps worked in order; nothing blocked me. The one step I had to work out was that the other Partition needs its own compare_batch call, which the compare note hints at but the notebook's cells don't provide.
- project.check() lists three "# CONVERSION" opt-outs in the logic cell (reads_all_partitions, many_matches). They block nothing, and the compare passed on both Partitions, so I left them.
- Paths: work folder C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-W1-3; Project folder ...\my_work\team_project; the batch notebook ...\my_work\team_project\admin\workflows\convert\convert.ipynb; compare report ...\my_work\team_project\tables\mart_dev__team_fails\conversion\compare.md. Nothing under main/ or _loop/ was edited.
