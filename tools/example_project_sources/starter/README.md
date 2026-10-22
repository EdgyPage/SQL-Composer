# The starter Example project

A Project made for the Example database's tables `ops.jobs`, `ops.job_runs` and
`ops.run_alerts`, laid out as yours is. It is much like the Project the Getting started
how-tos build, one step at a time, but not the same:

- it also holds `mart.alerts_per_job`, which no how-to makes;
- it lacks what the how-tos add to show one thing each: the Table references of
  `ops.region_budgets` and `ops.team_notes`, which Count, join and stay safe adds,
  `mart.run_speed`, which Follow lineage makes, and `ops.scheduler_runs`, which Keep the
  Project in order adopts;
- its files are in full where a how-to shortens them, such as its Table references' comments.

It builds four Saved tables, each in a Table folder of its own, each made from the
`saved_table` Template and partitioned by dt, the day, as `ops.job_runs` and `ops.run_alerts`
are:

- `mart.alerts_per_severity`: how many low and high alerts were raised each day. Its notebook
  is the Template filled in and nothing else: a count per group of the rows `READS` picks.
  Read it beside its Table reference, `references/mart__alerts_per_severity.py`, to see what
  each `<...>` became.
- `mart.daily_job_runs`: each job's runs, failed runs and minutes per day, its rows from a
  Building block, `building_blocks/runs_per_job.py`, given `READS`.
- `mart.alerts_per_job`: each job's alerts and high alerts per day, each alert joined to its
  run; its `READS` filters both tables.
- `mart.team_day`: each team's day, read from `mart.daily_job_runs` and `ops.jobs`, so it is
  written after mart.daily_job_runs.

Each notebook's logic cell sets `READS`, the rows its `write()` reads, as the Template does:

| Saved table | its write() reads |
|---|---|
| `mart.alerts_per_severity` | `equals(run_alerts.dt, "2026-09-24")`: the alerts raised on 2026-09-24 |
| `mart.daily_job_runs` | `equals(job_runs.dt, "2026-09-24")`: the runs of 2026-09-24, through the Building block |
| `mart.alerts_per_job` | `all_of(equals(run_alerts.dt, "2026-09-24"), between(job_runs.dt, "2026-09-23", "2026-09-24"))`: the alerts raised on 2026-09-24, and the runs of that day and the day before, since a run can raise an alert after midnight |
| `mart.team_day` | `equals(daily_job_runs.dt, "2026-09-24")`: the day mart.daily_job_runs saved |

Each write fills the Partitions of the dt its rows hold, so to write another day, change the
day in `READS`.

## Every file of this Project

The file map of Start a Project, the first step of the download's README, filled in: each
file, the Project action that made it, and what was filled in by hand.

| Path | Made by | What was filled in |
|---|---|---|
| `starter/`, this Project's folder | by hand | nothing |
| `sqlglot_composer/` | you: copy it in from the download, before you run anything | nothing: never edit a file inside it |
| the notebook `project.start()` was run from | by hand, in Jupyter; not kept here | nothing |
| `warehouse.py` | `project.start()` | nothing: it is left as `start` writes it, running on the Example database |
| `admin/`: add_references, change_a_saved_table, check_project, check_references, new_block, new_table, refresh_reference_sheet, remove_table and run_tables, each an .ipynb | `project.start()` | nothing |
| `admin/admin_log.md`, the Admin log | `project.start()`, then each Project action added an entry | nothing |
| `admin/registry.csv`, the registry | `project.start()`, then each Project action that made a Table folder, a Table reference or a Building block added a row | nothing |
| `admin/templates/`, the Templates | `project.start()` | nothing |
| `references/ops__jobs.py`, `references/ops__job_runs.py` and `references/ops__run_alerts.py` | `project.add_references([...], query=query)` | their TODO lines, and Aliases: `minutes` and `failed` for ops.job_runs, read by the Building block, and `high` for ops.run_alerts, read by mart.alerts_per_job's notebook |
| `references/mart__alerts_per_severity.py`, `references/mart__daily_job_runs.py`, `references/mart__alerts_per_job.py` and `references/mart__team_day.py` | `project.new_table(...)` | their `<...>` and TODO lines |
| `references/ops.py` and `references/mart.py`, the Database modules | each Project action that added a Table reference | nothing |
| `references/reference_sheet.csv`, the Reference sheet | `project.refresh_reference_sheet()` | nothing |
| `building_blocks/runs_per_job.py`, a Building block | `project.new_block("runs_per_job")` | its `<...>` and TODO lines |
| `tables/mart__alerts_per_severity/mart__alerts_per_severity.ipynb`, and the same for mart__daily_job_runs, mart__alerts_per_job and mart__team_day | `project.new_table("mart.alerts_per_severity")`, and so on | its `<...>` lines |
| `lineage/` in each Table folder, the table's Lineage | its notebook's lineage cell | nothing |
| `lineage/` at the Project's top, the Lineage of a Statement exported outside a Table notebook | `export_lineage(...)`, from a notebook in the Project's folder | nothing: every export here is a Table notebook's, so there is none |
| admin/removed/, what is archived | `project.remove_table(...)`, `project.remove_reference(...)` and `project.remove_block(...)` | nothing: nothing is archived here, so there is none yet |

This README was written by hand, as an Example project's own note: a Project of yours needs
none.

## Running it

Copy the `sqlglot_composer` folder into this folder first, as a Project holds it. Then open a
notebook in Jupyter and run its cells top to bottom: each Table notebook in `tables/`, or an
admin notebook such as `admin/run_tables.ipynb`. The Example database can be read but not
written, so a notebook's cell 3 prints each write's Hive and runs only the preview, and
`run_tables`, with no execute, prints every write in order, writers first, and sends nothing.
`admin/check_references.ipynb` compares each Table reference with its table: each Saved table,
which only a warehouse holds, reports that DESCRIBE failed, as expected on the Example
database.

At work, write your two functions, query and execute, in `warehouse.py`, and `admin/run_tables.ipynb`'s last
cell writes every table: each notebook's `write()`, which writes the rows its `READS` picks,
sending the Session setting "dynamic_partitions" first, since each write fills dt from its
rows.
