DONE: Made the Scheduled run team_week in my_project and ran it as the scheduler does; it ends with no error, and the team's warehouse holds mart.team_days for 2026-09-14 to 2026-09-20.

1. NEW_RUNS = ["team_week"] in admin/scheduled_runs.ipynb, cells 1-3 run, then NEW_RUNS = [] again: made scheduled_runs/team_week/team_week.ipynb, with entries in admin_log.md and registry.csv.
2. Filled in its cells from the README's Scheduled runs steps and the Template: START_FROM: str = "" kept, WEEK: datetime.date with no default (the scheduler always passes it; without -p the build refuses, "isn't set in this notebook"); week_days() gives WEEK's Monday and Sunday as text; statements() gives job_day_facts, job_day_costs and team_days by write_days(monday, sunday), then week_totals(monday, sunday). The build adds no last-3-days writes, as the steps write those tables.
3. Built with --cells 1-4 -p WEEK 2026-09-16: WEEK printed as datetime.date(2026, 9, 16), read from "2026-09-16"; four Statements in order, every range 2026-09-14 to 2026-09-20.
4. Ran top to bottom with -p WEEK 2026-09-16: exit 0, four Statements worked, week_totals gave 2 rows in results["week_totals"].
5. Checked the warehouse for 2026-09-07 to 2026-09-27: the three tables hold 09-14 to 09-20 only.

Notes: WEEK is saved bare, so a Jupyter run needs it set first; a day with no job events has no Partition; export_run_hive and export_run_lineage not run (optional); the .ipynb files are CRLF and the Edit tool refuses notebooks, so I edited them with small Python scripts in my_work/team_week/; some scratch files went to the session's scratchpad.
