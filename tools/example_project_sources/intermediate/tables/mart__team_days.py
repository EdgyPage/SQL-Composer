# %% [markdown]
# # mart.team_days
#
# Each team's events, runs, minutes and cost per day, saved on every run, and read a week at
# a time.
#
# Why: once mart.job_day_costs and mart.job_day_facts have saved a day, each team's day comes
# from a few saved rows per job; and a week's numbers come from 7 saved days, not from every
# event and bill again.
#
# Made by `project.new_table("mart.team_days", template="weekly_rollup")`, then filled in. It
# reads the two Saved tables through their Table references, so it is written after them:
# `run_tables` sends it last. A job's day with no row in mart.job_day_costs, since it wasn't
# billed, keeps its events through LEFT_JOIN, with a NULL cost. `week_totals` adds the saved
# days up per week; all of its numbers add up, so a week of them means something.
#
# The Saved tables are in your warehouse, not in the Example database, so its preview can't
# run here. `team_day_from_job_events(DAY)` can: it groups the Building blocks' rows by team
# the same way, from ops.job_events and ops.job_owners themselves, without the costs. Its
# lineage, cell 4, draws all three tables, through the other two notebooks' logic.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the days it writes, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, LEFT_JOIN, SELECT, WHERE, Clause, Statement,
    all_of, between, create_table, equals, statement, sum_of, week_start,
)
from building_blocks.days_rewritten import first_day_written
from building_blocks.events_per_job_day import events_per_job_day
from building_blocks.owner_on_day import owner_on_day
from references.mart__job_day_costs import job_day_costs
from references.mart__job_day_facts import job_day_facts
from references.mart__team_days import team_days
from references.ops__job_owners import job_owners

DAY = "2026-09-24"  # the last day write() writes, the Example database's last day


def create() -> Statement:
    """Step 1: create mart.team_days from its Table reference, if it isn't there yet."""
    return create_table(team_days, may_exist=True)


def rows(first_day: str, last_day: str) -> list[Clause]:
    """The clauses every step below shares: each team's numbers per day of job_day_facts, the
    table in FROM. The costs are joined on their day as well as their job, so each day's facts
    meet only that day's costs; their days go in LEFT_JOIN's ON=, since a WHERE on
    job_day_costs would drop the days LEFT_JOIN keeps. The day comes last in SELECT:
    INSERT_OVERWRITE writes each day's rows into that day's Partition."""
    return [
        SELECT(
            job_day_facts.team,
            AS(sum_of(job_day_facts.events), "events"),
            AS(sum_of(job_day_facts.runs), "runs"),
            AS(sum_of(job_day_facts.minutes), "minutes"),
            AS(sum_of(job_day_costs.cost_cents), "cost_cents"),
            job_day_facts.dt,
        ),
        FROM(job_day_facts),
        LEFT_JOIN(job_day_costs,
                  ON=all_of(equals(job_day_costs.job_id, job_day_facts.job_id),
                            equals(job_day_costs.dt, job_day_facts.dt),
                            between(job_day_costs.dt, first_day, last_day))),
        WHERE(between(job_day_facts.dt, first_day, last_day)),
        GROUP_BY(job_day_facts.dt, job_day_facts.team),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows(first_day_written(DAY), DAY))


def write_days(first_day: str, last_day: str) -> Statement:
    """Every day from first_day to last_day, in one write."""
    return statement(INSERT_OVERWRITE(team_days), *rows(first_day, last_day))


def write() -> Statement:
    """Step 3, every run, once the two tables it reads have written the same days: the last 3
    days, ending on DAY, in one write."""
    return write_days(first_day_written(DAY), DAY)


def week_totals(first_day: str, last_day: str) -> Statement:
    """Each team's events, runs, minutes and cost per week, from the days this table saved.
    A week that first_day or last_day cuts through counts only its days in between."""
    return statement(
        SELECT(
            AS(week_start(team_days.dt), "week"),
            team_days.team,
            AS(sum_of(team_days.events), "events"),
            AS(sum_of(team_days.runs), "runs"),
            AS(sum_of(team_days.minutes), "minutes"),
            AS(sum_of(team_days.cost_cents), "cost_cents"),
        ),
        FROM(team_days),
        WHERE(between(team_days.dt, first_day, last_day)),
        # GROUP_BY takes the SELECT's name for the week, "week"; the Hive writes the
        # week_start(...) calculation out again there, as Hive needs it
        GROUP_BY("week", team_days.team),
    )


def team_day_from_job_events(day: str) -> Statement:
    """Each team's events, runs and minutes for a day, from ops.job_events and ops.job_owners
    themselves, through the Building blocks mart.job_day_facts saves: so it runs on the
    Example database. The costs are left out: ops.region_costs writes its days like 20260924,
    so it can't be joined on the day to ops.job_events."""
    events = events_per_job_day(day, day)
    return statement(
        SELECT(
            job_owners.team,
            AS(sum_of(events.events), "events"),
            AS(sum_of(events.runs), "runs"),
            AS(sum_of(events.minutes), "minutes"),
        ),
        FROM(events),
        owner_on_day(events.job_id, events.dt, first_day=day, last_day=day),
        GROUP_BY(job_owners.team),
    )

# %%
# 3. Try it: the Hive of each step, then each team's day from ops.job_events
show_hive([create(), write(), week_totals("2026-09-21", DAY)])
run(team_day_from_job_events(DAY), query=query)

# %%
# 4. Lineage: the three tables together, through the other two notebooks' logic, in a new pair
# in lineage/ named by the time and this table
costs = project.load("mart.job_day_costs")
facts = project.load("mart.job_day_facts")
export_lineage(costs.write(), facts.write(), write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__team_days.py
project.refresh_reference_sheet("mart.team_days")
