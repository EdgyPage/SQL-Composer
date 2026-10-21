# The starter Example project

A Project made for the Example database's tables `ops.jobs`, `ops.job_runs` and
`ops.run_alerts`, laid out as yours is: everything here was made by the `project` module's
Project actions, then filled in by hand, as you fill in your own.

It builds three Saved tables, each in a Table folder of its own:

- `mart.daily_job_runs`: each job's runs, failed runs and minutes per day, from a Building
  block, `building_blocks/runs_per_job_day.py`;
- `mart.alerts_per_job`: each job's alerts and high alerts per day;
- `mart.team_day`: each team's day, read from the two tables above and `ops.jobs`, so it is
  written after them.

## What each folder holds

```
starter/
├── send.py                  your send: here, the Example database's
├── admin/                   one notebook per Project action, and the Templates
│   ├── admin_log.md         every Project action, in the order it ran
│   ├── registry.csv         every Table folder and Table reference a Project action made
│   └── templates/           the Templates new_table makes notebooks from
├── references/              a Table reference per table, and the Reference sheet
│   ├── ops__jobs.py, ops__job_runs.py, ops__run_alerts.py   add_references wrote these
│   ├── mart__daily_job_runs.py, mart__alerts_per_job.py, mart__team_day.py
│   └── reference_sheet.csv
├── building_blocks/
│   └── runs_per_job_day.py
└── tables/                  a Table folder per Saved table
    ├── mart__daily_job_runs/  its notebook, and lineage/, its past Lineage
    ├── mart__alerts_per_job/
    └── mart__team_day/
```

`references/ops__job_runs.py` and `references/ops__run_alerts.py` end with Aliases, names
written by hand below the Table reference: `minutes` and `failed` for ops.job_runs, read by
the Building block, and `high` for ops.run_alerts, read by mart.alerts_per_job's notebook.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom: each Table notebook in `tables/`, or an
admin notebook such as `admin/run_tables.ipynb`. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only the preview, and
`run_tables`, with no send, prints every write in order, writers first, and sends nothing.

At work, write your send in `send.py`, and `admin/run_tables.ipynb`'s last cell writes a day
of every table.
