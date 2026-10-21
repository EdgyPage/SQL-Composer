# sqlglot Composer 6.0, exported 2026-10-21 07:05 - copy it, then edit your copy
"""days_rewritten - the days each run writes again: its own, and the two before it.

Why: a bill or an event can come in a day or two after its day was saved, so each table of
the project that counts or adds up rows writes its last 3 days on each run, and naming the 3
once here keeps them alike.

A day written again replaces itself, so writing a day twice does no harm.
mart.job_events_checks writes only its day, since a check is of what was in on the day it ran.
"""

import datetime

DAYS_REWRITTEN = 3  # each run writes its own day and the 2 days before it


def first_day_written(day):
    """The first day a run for `day` writes: first_day_written("2026-09-24") is
    "2026-09-22"."""
    first_day = datetime.date.fromisoformat(day) - datetime.timedelta(days=DAYS_REWRITTEN - 1)
    return first_day.isoformat()
