# The intermediate Example project

A Project made for the Example database's tables `ops.job_events`, `ops.job_owners` and
`ops.region_costs`, laid out as yours is: everything here was made by the `project` module's
Project actions, then filled in by hand, as you fill in your own. It builds on the starter
Example project: read that one first.

Rows can come in late here, a bill a day or two after its day, so every table writes its last
3 days again on each run, and a day written again replaces itself. The number 3 is written
once, in `building_blocks/days_rewritten.py`, which every table reads.

It builds four Saved tables, each in a Table folder of its own, each from a different
Template:

- `mart.job_day_costs`, from `incremental_load`: each job's cost per day, all regions added
  up, from `ops.region_costs`, which writes its days like 20260924;
- `mart.job_day_facts`, from `as_of_lookup`: each job's events, runs and minutes per day,
  beside the team that owned the job that day, looked up in `ops.job_owners`' snapshots;
- `mart.team_days`, from `weekly_rollup`: each team's day, read from the two tables above, so
  it is written after them, and `week_totals`, which adds the saved days up into weeks;
- `mart.job_events_checks`, from `quality_checks`: each day's row count of `ops.job_events`,
  and checks for repeated keys and NULLs.

## What each folder holds

```
intermediate/
├── send.py                  your send: here, the Example database's
├── admin/                   one notebook per Project action, and the Templates
├── references/              a Table reference per table, and the Reference sheet
│   ├── ops__job_events.py, ops__job_owners.py, ops__region_costs.py
│   ├── mart__job_day_costs.py, mart__job_day_facts.py, mart__team_days.py,
│   │   mart__job_events_checks.py
│   └── reference_sheet.csv
├── building_blocks/         costs_per_job_day.py, days_rewritten.py,
│                            events_per_job_day.py, owner_on_day.py
└── tables/                  a Table folder per Saved table, each with its lineage/
```

`references/ops__region_costs.py`'s Date partition was filled in by hand: the table is
partitioned by region first, which holds no days, so `add_references` left it as a TODO.
`references/ops__job_events.py` ends with an Alias, `ends_a_run`, the events that end a run,
which `building_blocks/events_per_job_day.py` reads.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only what reads ops tables,
and `admin/run_tables.ipynb`, with no send, prints every write of the last 3 days in order,
writers first, and sends nothing.
