# The intermediate Example project

A Project made for the Example database's tables `ops.job_events`, `ops.job_owners`,
`ops.region_costs`, `ops.region_budgets` and `ops.team_notes`, laid out as yours is. It builds
on the starter Example project: read that one first.

Its tables are of every kind: `ops.job_events` and `ops.job_owners` are partitioned by dt, the
day, `ops.region_costs` by region and then dt, `ops.region_budgets` by region alone, and
`ops.team_notes` not at all, with no Key. Its Saved tables are too.

It builds six Saved tables, each in a Table folder of its own, five made from the
`saved_table` Template and one from `quality_checks`:

- `mart.job_day_costs`: each job's cost per day, all regions added up, from
  `ops.region_costs`, which writes its days like 20260924. An incremental load: each run
  writes its last 3 days again.
- `mart.job_day_facts`: each job's events, runs and minutes per day, beside the team that
  owned the job that day, looked up in `ops.job_owners`' snapshots: an as-of lookup, also
  writing its last 3 days.
- `mart.team_days`: each team's day, read from the two tables above, so it is written after
  them, and `week_totals`, a weekly rollup that adds the saved days up into weeks.
- `mart.job_events_checks`, from `quality_checks`: the row count of each dt of
  `ops.job_events`, and checks for repeated keys and NULLs.
- `mart.budget_overruns`: each job's budget in its region, and the days its cost went over,
  partitioned by region, with a write per region.
- `mart.job_notes`: each team note beside the jobs the team owned on the day it was written,
  not partitioned and with no Key, so each write replaces the whole table.

Rows can come in late here, a bill a day or two after its day, so the three tables that count
or add up rows per day write their last 3 days again on each run, and a day written again
replaces itself. The number 3 is written once, in `building_blocks/days_rewritten.py`, which
those tables read. `mart.job_events_checks` checks only the dt its `READS` names: a check is of
the rows in on the day it runs, and a check written again later would hide what was missing
then.

## What each folder holds

```
intermediate/
├── warehouse.py             your query and execute: here, the Example database's
├── admin/                   one notebook per Project action, and the Templates
├── references/              a Table reference per table, and the Reference sheet
│   ├── ops__job_events.py, ops__job_owners.py, ops__region_costs.py,
│   │   ops__region_budgets.py, ops__team_notes.py
│   ├── mart__job_day_costs.py, mart__job_day_facts.py, mart__team_days.py,
│   │   mart__job_events_checks.py, mart__budget_overruns.py, mart__job_notes.py
│   └── reference_sheet.csv
├── building_blocks/         costs_per_job.py, days_rewritten.py,
│                            events_per_job.py, owner_on_day.py
└── tables/                  a Table folder per Saved table, each with its lineage/
```

## How each file was made

- `project.start()` made `admin/`, its notebooks and `templates/`, and `warehouse.py`, which
  is left as `start` writes it.
- `project.add_references(...)` wrote `references/ops__*.py` from each table's DESCRIBE; each
  file's TODO lines were then filled in by hand, and an Alias written below one.
- `project.new_table(...)` made each Table folder, its notebook and its Table reference,
  `references/mart__*.py`; each notebook and Table reference was then filled in by hand.
- The files in `building_blocks/` and this README were written by hand: no Project action
  makes them.
- Each notebook's lineage cell exported its `lineage/` pair, and
  `project.refresh_reference_sheet()` wrote `references/reference_sheet.csv`.
- `admin/admin_log.md` and `admin/registry.csv` hold what each Project action did, as it ran.

`ops.region_costs` is partitioned by region, then dt, which `add_references` read from the
table into `references/ops__region_costs.py`, and writes its days like 20260924:
`building_blocks/costs_per_job.py` writes them like 2026-09-24, as the project's other
tables do.
`references/ops__job_events.py` ends with an Alias, `ends_a_run`, the events that end a run,
which `building_blocks/events_per_job.py` reads.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only what reads ops tables,
and `admin/run_tables.ipynb`, with no execute, prints every write in order, writers first, and
sends nothing.
