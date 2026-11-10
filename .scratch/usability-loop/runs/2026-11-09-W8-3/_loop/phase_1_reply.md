DONE: Made the Scheduled run team_week in the Project and ran it top to bottom as the scheduler does.

- Made by project.new_scheduled_run through admin/scheduled_runs.ipynb (NEW_RUNS = ["team_week"], cells 1-3 run, then NEW_RUNS = [] put back).
- Parameters: START_FROM: str = "" and WEEK: datetime.date = datetime.date(2026, 9, 16), read from text by its hint; not a None default, as the run needs a day.
- # scheduled: week_first_day() is WEEK's Monday, week_last_day() that Monday plus 6 days; statements() gives job_day_costs.write_days, job_day_facts.write_days, team_days.write_days and team_days.week_totals for those days, in order. write_days, not the default writes: the build adds each table's write(), the last 3 days ending 2026-09-24, not WEEK's week; writing the three tables in statements() means the build adds none of its own.
- Build (default WEEK): 4 Statements in order, 2026-09-14 to 2026-09-20.
- Run: run_notebook.py ...team_week.ipynb -p WEEK 2026-09-16, "every cell ran" (exit 0); each worked; week_totals gave 2 rows in results["week_totals"]; mart.team_days holds exactly 2026-09-14 to 2026-09-20.

Friction: the README's Scheduled runs steps don't say a run can write a table for a chosen period: it takes write_days in statements(), seen only in the Table notebook's logic docstrings; the README's parameter examples all use "| None" defaults, with no word on a plain default; editing a notebook's source by hand needs its quotes escaped in the JSON (my first try broke the file).
