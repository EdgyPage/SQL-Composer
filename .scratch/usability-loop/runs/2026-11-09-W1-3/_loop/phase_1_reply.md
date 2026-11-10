DONE: Made mart_dev.team_fails from from_your_team/weekly_fails.hql with the Toolbox, checked it against mart.team_fails; the table is at /data/team/mart_dev.db/team_fails.

1. Read main/.github/README.md: sections 1 and 9, The Workflows and the convert Workflow's chart and cells.
2. Copied the Toolbox into my_work/team_project/, ran project.start().
3. admin/databases.py: DEV = {"database": "mart_dev", "location_root": "/data/team"}; PROD left as placeholders (nothing promoted).
4. convert.ipynb: NAME = "team_fails", FILES = [the absolute path to from_your_team/weekly_fails.hql] (read where it is), RENAME = {"mart.team_fails": "team_fails"}; the connection cell's sys.path.append, from team_connection import conn, connect(conn); later PARTITIONS = [{"dt": "2026-09-23"}].
5. Ran cells 1-3 with run_notebook.py, then cells 1,2,12 for the second Partition; no Decision open; the batch finished and moved to finished/team_fails/.
6. compare.md: passed on dt=2026-09-23 (2 rows each) and dt=2026-09-24 (1 row each); a conn.query over both tables agreed; the create has LOCATION '/data/team/mart_dev.db/team_fails'; project.check() reports nothing open.
7. Filled in the Table reference's description TODO; the proposed Key (team, dt) kept.

Friction: section 1 has no step for a run without a notebook (print(project.start()) from a script worked); convert's step 1 "Save the scripts ... beside it" was unclear whether FILES may point outside the Project (the FILES bullet says so, and it worked); "Run up to your Decisions" ran to the end with none waiting (the README says so, but a reader may expect a pause); SHOW CREATE TABLE through the team connection was refused ("Table  must have at least one column"), the connection's executor, not the docs.
