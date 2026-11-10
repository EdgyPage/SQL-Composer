# %%
# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table to start from, as a run that failed prints it; "" sends all
WEEK: datetime.date | None = None  # a day of the week to add up, such as "2026-09-23"; None
# adds up the week of the latest day ops.job_events holds

# %%
# scheduled
# The Statements this run sends, each by its name: a SELECT's rows come back in results by it.
# A Table notebook's logic gives them through project.load, such as
#     "week_totals": project.load("mart.team_days").week_totals(FIRST_DAY, LAST_DAY),
# and a Statement of your own is composed here with statement(...). A function of this cell
# that gives a value each time it is built, through run_value(...), is a Run value too.
from sqlglot_composer import latest_partition, run_value
from references.ops__job_events import job_events


def week_first_day() -> datetime.date:
    """The Monday that starts WEEK's week, or, when WEEK is None, the week of the latest day
    ops.job_events holds, the day the tables this run writes end on."""
    if WEEK is None:
        day = latest_partition(job_events.dt, query)
    else:
        day = WEEK
    return day - datetime.timedelta(days=day.weekday())


def week_last_day() -> datetime.date:
    """The Sunday that ends the week week_first_day starts."""
    return week_first_day() + datetime.timedelta(days=6)


def statements() -> dict[str, Statement]:
    """What this run sends, by name: the build adds the writes of each table they read."""
    team_days = project.load("mart.team_days")
    return {
        "week_totals": team_days.week_totals(run_value(week_first_day),
                                             run_value(week_last_day)),
    }
