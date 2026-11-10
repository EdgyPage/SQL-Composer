DONE: Made mart_dev.team_fails in the Dev Database with the Toolbox from from_your_team/weekly_fails.hql, and checked it against mart.team_fails: both Partitions (dt=2026-09-23, dt=2026-09-24) passed the compare, and my own SELECT of both gives the same 3 rows.

1. Copied the Toolbox's sqlglot_composer into my_work/team_project, ran project.start() (plain Python).
2. admin/databases.py: DEV = {"database": "mart_dev", "location_root": "/data/team"}, PROD = {"database": "team_prod", "location_root": "/data/team"}. Not promoted.
3. convert.ipynb: the connect line replaced with team_connection's lines; NAME = "team_fails", FILES = [the path to from_your_team/weekly_fails.hql, read where it is], RENAME = {"mart.team_fails": "team_fails"}, PARTITIONS = [{"dt": "2026-09-23"}].
4. Ran "Run up to your Decisions" and "Run the rest" with run_notebook.py: no Decision open (Key (team, dt) proposed, location from DEV's location_root); created, written, compared.
5. Filled in the two TODO lines of references/mart_dev__team_fails.py.

Table location, by DESCRIBE FORMATTED: /data/team/mart_dev.db/team_fails. project.check() reports nothing blocking: the proposed Key and three CONVERSION opt-outs (reads_all_partitions, many_matches), left as written.

Where the docs made me work harder: the README is about 117 KB, so finding the convert steps meant searching its headings; run_notebook.py --cells numbers code cells, not notebook cells, and the README's "--cells 1-3,6" doesn't say which (I used --list); the README doesn't say whether a Table reference's TODO line blocks the run (it doesn't); nothing in the convert notebook says how to run "Run the rest" again for a finished batch (the README does, further on).
