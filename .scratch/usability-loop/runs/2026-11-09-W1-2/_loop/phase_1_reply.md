DONE: mart_dev.team_fails is made with the Toolbox, a copy of mart.team_fails, in the Project at my_work\team_project, written in mart_dev at /data/team/mart_dev.db/team_fails, and compared with the original on both Partitions the two share (dt = 2026-09-23 and 2026-09-24): both passed, 2 and 1 rows matched. Not promoted to team_prod: the task didn't ask for it.

What I did, in order:
1. Read the work folder's README (main\.github\README.md), section 9 "Convert someone else's Hive" and the Workflows' convert section.
2. Copied main\sqlglot_composer into my_work\team_project and ran project.start().
3. Filled in admin\databases.py: DEV = {"database": "mart_dev", "location_root": "/data/team"}, PROD = {"database": "team_prod", "location_root": "/data/team"}.
4. Copied from_your_team\weekly_fails.hql to admin\workflows\convert\weekly_fails.hql.
5. In admin\workflows\convert\convert.ipynb: replaced the commented connect line with the team_connection lines (sys.path.append to the work folder, from team_connection import conn, connect(conn)); NAME = 'team_fails', FILES = ['weekly_fails.hql'], RENAME = {"mart.team_fails": "team_fails"} (without it the copy would be mart_dev.team_fails_mart).
6. Ran cells 1-3 (run up to the Decisions): it did not stop at a Decision; it converted the script, wrote the Table reference and the Table folder, created and wrote the table, and compared it. Ran cells 1-2, 4, 5 again with PARTITIONS = [{"dt": "2026-09-23"}] to compare the second Partition too.

Points to note:
- project.check() reports no open items. It lists the Key (team, dt) as proposed from the query ("key": "proposed" accepts it), and three opt-outs the convert kept from the original script, marked # CONVERSION: reads_all_partitions=True on the FROM and one JOIN, many_matches=True on the other JOIN. They block nothing.
- The scratchpad folder held another session's files; my first fill_convert.py was overwritten before it ran (the notebook wasn't changed by it). I kept my scripts in my_work\scripts after that.
- The README's connect example uses forward slashes in sys.path.append; a Windows path with backslashes in a Python string failed on its escapes, so I used forward slashes.
