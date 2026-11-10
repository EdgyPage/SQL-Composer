DONE: Made the Scheduled run team_week in my_project and ran it top to bottom with WEEK as text, 2026-09-16.

1. Read the README's Scheduled runs section, the mart.team_days notebook and reference, the upstream tables' logic (mart__job_day_costs and mart__job_day_facts both have write_days(first_day, last_day)), and the scheduled_run Template.
2. NEW_RUNS = ["team_week"] in admin/scheduled_runs.ipynb, cells 1-3 run with run_notebook.py: made scheduled_runs/team_week/team_week.ipynb; NEW_RUNS set back to [].
3. Filled the two cells: START_FROM: str = "" and WEEK: datetime.date | None = None; a week_days() helper giving WEEK's Monday and Sunday as text; statements() giving job_day_costs, job_day_facts and team_days (write_days) and week_totals (SELECT). The setup cell's connection was already filled.
4. Built with --cells 1-4 -p WEEK 2026-09-16: Monday 2026-09-14 to Sunday 2026-09-20, in the order job_day_costs, job_day_facts, team_days, week_totals; the build added no writes of its own.
5. Ran the whole notebook with -p WEEK 2026-09-16 (exit 0): three writes worked, week_totals gave 2 rows in results["week_totals"].

Friction (not blocking): the README never names write_days, the call a run needs to write a table for chosen days; it says the build adds the writes of each table read but not that a write you put in statements() takes that one's place (the code does); the Template shows only run_value(function) for a value worked out each build, while reading WEEK inside statements() also works, and the README doesn't say which to pick.
