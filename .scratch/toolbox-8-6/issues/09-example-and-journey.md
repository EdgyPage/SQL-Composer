# A Scheduled run in the Example project, and its journey

Type: task
Status: open
Blocked by: 06, 07, 08
Size: M

## Question

The intermediate Example project shows a Scheduled run working, and a journey counts the
user's actions.

## Done when

- `tools/example_project.py` makes `scheduled_runs/weekly_team/` in the intermediate Project:
  a `WEEK: datetime.date | None` parameter, a Run value of its own for the week's first day,
  `load("mart.team_days").week_totals(...)` as its SELECT, and `mart.team_days`' upstream
  pulled in. Its built Hive and lineage committed, made by hand as the map says.
- A journey in `tests/journeys/`: make the run, fill its cells, run it through as a scheduler
  would (every cell, a parameter given as text), then once with a failure and its START_FROM.
  Its actions in `KNOWN_ACTIONS`.
- The starter Project gets the empty `scheduled_runs/` only.

## Answer
