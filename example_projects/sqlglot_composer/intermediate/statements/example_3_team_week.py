# sqlglot Composer 4.1, exported 2026-10-06 15:49 - copy it, then edit your copy
"""Example 3: examples 1 and 2 combined into each team's days and weeks.

Why: once examples 1 and 2 have saved a day, each team's events, minutes and costs come from a
few saved rows per job, counted for the team that owned each job that day.

It reads the two Saved tables through their Table references, like any other table:
mart.job_day_facts for each job's events, minutes and team that day, and mart.job_day_costs
for its cost. Both write their days like 2026-09-24, so they join on the job and the day. It
saves each team's day in mart.team_days, whose Table reference is
table_references/team_days.py. The steps are theirs: create(), preview(day) and
write_days(first_day, last_day), run after examples 1 and 2 have written the same days.

A write fills one day of a Saved table, so mart.team_days holds days, not weeks.
week_totals(first_day, last_day) reads them and adds each team's week up, grouping the days
by week_start, the Monday that starts each day's week. Adding a week's days up is right for
events, runs, minutes and cents, which all add up; a count of different jobs wouldn't, since a
job that ran on two days would be counted twice.

The Saved tables are in your warehouse, not in the Example database, so preview and
week_totals can't run here. team_day_from_job_events(day) can: it counts each team's events,
runs and minutes for a day straight from ops.job_events and ops.job_owners, the way examples 2
and 3 do between them, without the costs.
"""

from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, LEFT_JOIN, SELECT, WHERE, all_of, between, by_day,
    create_table, equals, statement, sum_of, week_start,
)
from building_blocks.events_per_job_day import events_per_job_day
from building_blocks.owner_on_day import owner_on_day
from table_references.job_day_costs import job_day_costs
from table_references.job_day_facts import job_day_facts
from table_references.job_owners import job_owners
from table_references.team_days import team_days

LAST_DAY = "2026-09-24"  # the Example database's last day, which the previews read unless told


def create():
    """Step 1: create mart.team_days from its Table reference, if it isn't there yet."""
    return create_table(team_days, may_exist=True)


def preview(day=LAST_DAY):
    """Step 2: the rows write_days would save for the day, as a SELECT to run and check first.

    A job's day with no row in job_day_costs, since it wasn't billed, keeps its events through
    LEFT_JOIN, with a NULL cost, which sum_of leaves out. The costs' day goes in LEFT_JOIN's
    ON=, not in WHERE, since a WHERE on job_day_costs would drop the days LEFT_JOIN keeps;
    equals(job_day_costs.dt, day) bounds the Date partition at both ends, to one day.
    """
    return statement(
        SELECT(
            job_day_facts.team,
            AS(sum_of(job_day_facts.events), "events"),
            AS(sum_of(job_day_facts.runs), "runs"),
            AS(sum_of(job_day_facts.minutes), "minutes"),
            AS(sum_of(job_day_costs.cost_cents), "cost_cents"),
        ),
        FROM(job_day_facts),
        LEFT_JOIN(job_day_costs,
                  ON=all_of(equals(job_day_costs.job_id, job_day_facts.job_id),
                            equals(job_day_costs.dt, day))),
        WHERE(equals(job_day_facts.dt, day)),
        GROUP_BY(job_day_facts.team),
    )


def write_days(first_day, last_day):
    """Step 3, every run, once examples 1 and 2 have written the days: save each team's days.

    by_day cuts it into one write per day of job_day_facts, the table in FROM. GROUP_BY keeps
    that day, job_day_facts.dt, so no day's numbers are mixed with another's. The costs are
    joined on their day as well as their job, so each day's facts meet only that day's costs,
    and by_day leaves a joined table's bound as written, so job_day_costs' goes in LEFT_JOIN's
    ON= too, as between(job_day_costs.dt, ...).
    """
    return by_day(statement(
        INSERT_OVERWRITE(team_days),
        SELECT(
            job_day_facts.team,
            AS(sum_of(job_day_facts.events), "events"),
            AS(sum_of(job_day_facts.runs), "runs"),
            AS(sum_of(job_day_facts.minutes), "minutes"),
            AS(sum_of(job_day_costs.cost_cents), "cost_cents"),
        ),
        FROM(job_day_facts),
        LEFT_JOIN(job_day_costs,
                  ON=all_of(equals(job_day_costs.job_id, job_day_facts.job_id),
                            equals(job_day_costs.dt, job_day_facts.dt),
                            between(job_day_costs.dt, first_day, last_day))),
        WHERE(between(job_day_facts.dt, first_day, last_day)),
        GROUP_BY(job_day_facts.dt, job_day_facts.team),
    ))


def week_totals(first_day, last_day):
    """Each team's events, runs, minutes and cost per week, from mart.team_days' days.

    A week that first_day or last_day cuts through counts only its days in between: from
    2026-09-11, a Friday, the first week holds three days.
    """
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
        # "week" names the SELECT's week_start(...) column: the Hive repeats the calculation
        GROUP_BY("week", team_days.team),
    )


def team_day_from_job_events(day=LAST_DAY):
    """Try example 3's team grouping on the Example database: each team's events, runs and
    minutes for a day, from ops.job_events and ops.job_owners themselves.

    It reads the Building blocks example 2 reads, so the numbers are worked out exactly as
    example 2 saves them, then groups them by team as preview does. It leaves the costs out:
    ops.region_costs writes its days like 20260924, so it can't be joined on the day to
    ops.job_events, which writes them like 2026-09-24. Only example 1's Saved table, which
    writes the costs' days like 2026-09-24, can be.
    """
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
