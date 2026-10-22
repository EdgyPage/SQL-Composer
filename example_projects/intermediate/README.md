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

## Every file of this Project

The file map of Start a Project, the first step of the download's README, filled in: each
file, the Project action that made it, and what was filled in by hand.

| Path | Made by | What was filled in |
|---|---|---|
| `intermediate/`, this Project's folder | by hand | nothing |
| `sqlglot_composer/` | you: copy it in from the download, before you run anything | nothing: never edit a file inside it |
| the notebook `project.start()` was run from | by hand, in Jupyter; not kept here | nothing |
| `warehouse.py` | `project.start()` | nothing: it is left as `start` writes it, running on the Example database |
| `admin/`: add_references, change_a_saved_table, check_project, check_references, new_block, new_table, refresh_reference_sheet, remove_table and run_tables, each an .ipynb | `project.start()` | nothing |
| `admin/admin_log.md`, the Admin log | `project.start()`, then each Project action added an entry | nothing |
| `admin/registry.csv`, the registry | `project.start()`, then each Project action that made a Table folder, a Table reference or a Building block added a row | nothing |
| `admin/templates/`, the Templates | `project.start()` | nothing |
| `references/ops__job_events.py`, `references/ops__job_owners.py`, `references/ops__region_costs.py`, `references/ops__region_budgets.py` and `references/ops__team_notes.py` | `project.add_references([...], query=query)` | their TODO lines, and an Alias, `ends_a_run`, the events that end a run, for ops.job_events, read by `building_blocks/events_per_job.py` |
| `references/mart__job_day_costs.py`, `references/mart__job_day_facts.py`, `references/mart__team_days.py`, `references/mart__job_events_checks.py`, `references/mart__budget_overruns.py` and `references/mart__job_notes.py` | `project.new_table(...)` | their `<...>` and TODO lines |
| `references/ops.py` and `references/mart.py`, the Database modules | each Project action that added a Table reference | nothing |
| `references/reference_sheet.csv`, the Reference sheet | `project.refresh_reference_sheet()` | nothing |
| `building_blocks/costs_per_job.py`, `building_blocks/days_rewritten.py`, `building_blocks/events_per_job.py` and `building_blocks/owner_on_day.py`, the Building blocks | `project.new_block(...)`, one Building block to a file | its `<...>` and TODO lines; `days_rewritten.py` and `owner_on_day.py` hold a number and a join, not a Derived table, so their Template's code was written over |
| `tables/mart__job_day_costs/mart__job_day_costs.ipynb`, and the same for each of the other five Saved tables | `project.new_table("mart.job_day_costs")`, and so on; `template="quality_checks"` for mart.job_events_checks | its `<...>` lines |
| `lineage/` in each Table folder, the table's Lineage | its notebook's lineage cell | nothing |
| admin/removed/, what is archived | `project.remove_table(...)`, `project.remove_reference(...)` and `project.remove_block(...)` | nothing: nothing is archived here, so there is none yet |

This README was written by hand, as an Example project's own note: a Project of yours needs
none.

`ops.region_costs` is partitioned by region, then dt, which `add_references` read from the
table into `references/ops__region_costs.py`, and writes its days like 20260924:
`building_blocks/costs_per_job.py` writes them like 2026-09-24, as the project's other
tables do.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only what reads ops tables,
and `admin/run_tables.ipynb`, with no execute, prints every write in order, writers first, and
sends nothing.
