# The starter Example project

A Project made for the Example database's tables `ops.jobs`, `ops.job_runs` and
`ops.run_alerts`, laid out as yours is.

It builds three Saved tables, each in a Table folder of its own, each made from the
`saved_table` Template and partitioned by dt, the day, as `ops.job_runs` and `ops.run_alerts`
are:

- `mart.daily_job_runs`: each job's runs, failed runs and minutes per day, from a Building
  block, `building_blocks/runs_per_job.py`;
- `mart.alerts_per_job`: each job's alerts and high alerts per day;
- `mart.team_day`: each team's day, read from the two tables above and `ops.jobs`, so it is
  written after them.

## What each folder holds

```
starter/
├── warehouse.py             your query and execute: here, the Example database's
├── admin/                   a notebook per Project action or check, and the Templates
│   ├── admin_log.md         every Project action, in the order it ran
│   ├── registry.csv         every Table folder and Table reference made, and when
│   └── templates/           the Templates new_table makes notebooks from
├── references/              a Table reference per table, and the Reference sheet
│   ├── ops__jobs.py, ops__job_runs.py, ops__run_alerts.py
│   ├── mart__daily_job_runs.py, mart__alerts_per_job.py, mart__team_day.py
│   └── reference_sheet.csv
├── building_blocks/
│   └── runs_per_job.py
└── tables/                  a Table folder per Saved table
    ├── mart__daily_job_runs/  its notebook, and lineage/, its past Lineage
    ├── mart__alerts_per_job/
    └── mart__team_day/
```

## How each file was made

- `project.start()` made `admin/`, its notebooks and `templates/`, and `warehouse.py`, which
  is left as `start` writes it.
- `project.add_references(...)` wrote `references/ops__*.py` from each table's DESCRIBE; each
  file's TODO lines were then filled in by hand, and Aliases written below the Table reference.
- `project.new_table(...)` made each Table folder, its notebook and its Table reference,
  `references/mart__*.py`; each notebook and Table reference was then filled in by hand.
- `project.new_block("runs_per_job")` made `building_blocks/runs_per_job.py` from the
  `building_block` Template, which was then filled in by hand.
- This README was written by hand, as an Example project's own note: a Project of yours needs
  none.
- Each notebook's lineage cell exported its `lineage/` pair, and
  `project.refresh_reference_sheet()` wrote `references/reference_sheet.csv`.
- `admin/admin_log.md` and `admin/registry.csv` hold what each Project action did, as it ran.

`references/ops__job_runs.py` and `references/ops__run_alerts.py` end with Aliases, names
written by hand below the Table reference: `minutes` and `failed` for ops.job_runs, read by
the Building block, and `high` for ops.run_alerts, read by mart.alerts_per_job's notebook.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom: each Table notebook in `tables/`, or an
admin notebook such as `admin/run_tables.ipynb`. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only the preview, and
`run_tables`, with no execute, prints every write in order, writers first, and sends nothing.
`admin/check_references.ipynb` compares each Table reference with its table: the Saved
tables, which only a warehouse holds, are reported as not found.

At work, write your query and execute in `warehouse.py`, and `admin/run_tables.ipynb`'s last
cell writes every table: each notebook's `write()`, which writes the dt its `DAY` names.
