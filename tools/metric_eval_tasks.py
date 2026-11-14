"""The tasks Copilot file 19, Metric request, is measured on (Toolbox 8.7, tickets 11 and 17).

Each task is a new metric a user wants on the Example database's tables, as they first say it,
vaguely, and the answer key they keep to themselves: what they really mean, in plain words,
which the stand-in user answers Copilot's questions from. Both the stand-in user and Copilot
are given the tables' column definitions, `COLUMN_DEFINITIONS`, as the user would paste them.

A task's requirements key, `required`, is what its Metric request must establish: the metric
columns, each quantity tied to its source column by the definitions, the grain and every
condition on which rows exist, the formula, the days counted, what is left out, the edge cases,
and, where the data can't give the metric, the missing data named with a fix. Each requirement
is a rule a request's text is read by: patterns that must be found in one part, or that must
not be. No numbers are worked out: as the user put it (2026-11-13), "LLMs are not to do math
with. Correct SQL is easy once the task is defined and sql will be generated from another model
that has databases indexed, a task not for copilot. Hone business requirements for a model with
better access." Each task's `example` is a request that meets its key, which a test holds.

A request is scored for direction, not exactness: it passes with every essential element (the
source columns or the named gap, the grain and its conditions, and what a task marks), more of
the helpful ones met than not, and nothing invented. The user: "I am more concerned with
directional correctness than exact correctness. Messy or incomplete data definitions are
anticipated." So the definitions are messy, as real ones are.

Twelve tasks are dev, which file 19 may be tuned on, and five are held out, asked once per
version of the Copilot files. Four muddle their columns, as users do: one column asked for
where two are meant ("one asked, two meant"), or two where one is ("two asked, one meant").
Three bring sample rows. Five ask for what the data can't give, or gives only in part
(`missing`): a column no table has (M11, M14), a grain the tables don't hold (M15), a column
with no definition (M16) and a date whose definition is too vague to decide (M17). They pass
on a request that names the gap, suggests the fix and heads the right way with what is there.
The user again: "Simply suggest fixes; do not invent answers to make users happy just to give
them something."
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Required:
    """One element a Metric request must hold: patterns, each found (case aside) in one part of
    the request's column sections, or anywhere in it where `part` is ""; or, with `absent`,
    none of them found there."""

    what: str  # the element in words, as a failed score line names it
    part: str  # a part's label, such as "Left out", or "" for the whole request
    patterns: tuple[str, ...]
    absent: bool = False
    # Essential: the source columns or the named gap, the grain and its conditions, nothing
    # invented. The rest are helpful: a request passes with more of them met than not.
    essential: bool = False


@dataclass(frozen=True)
class MetricTask:
    """A new metric a user wants: what they say first, what they mean, and what its Metric
    request must hold."""

    id: str
    split: str  # dev or held_out
    opening: str  # what the user says first: the vague goal, and any sample rows
    answer_key: str  # what the user means, kept from Copilot: the stand-in user answers from it
    columns: int  # how many column sections the request has
    required: tuple[Required, ...]
    example: str  # a Metric request that meets the key
    muddled: str = ""  # "one asked, two meant", "two asked, one meant", or ""
    sample_rows: bool = False
    missing: bool = False  # whether the tables can't give the metric


# The column definitions the user pastes, as their data dictionary gives them: messy, as real
# ones are. Some are vague, some missing, a unit or two unstated, and the costs table's dt is
# a "load date" where the runs table's is the day a run ran.
COLUMN_DEFINITIONS = """\
ops.jobs
  job_id - job id
  job_name - name
  team - owning team
  region - location
ops.job_runs (partitioned by dt)
  run_id - run id
  job_id - job id
  status - run state (SUCCESS / FAILED / TEST, NULL while running)
  duration_mins - run length
  avg_retry_secs
  dt - partition date
ops.run_alerts (partitioned by dt)
  alert_id - alert id
  run_id - run id
  severity - alert level (low / high)
  dt - partition date
ops.scheduler_runs (partitioned by dt)
  run_id
  job_id
  dt
ops.job_events (partitioned by dt)
  event_id - event id
  job_id - job id
  event_type - what happened (start / finish / retry / fail)
  minutes - elapsed
  dt - partition date
ops.job_owners (partitioned by dt)
  job_id - job id
  team - team
  owner - owner, if any
  dt - snapshot date
ops.region_costs (partitioned by region, dt)
  job_id - job id
  cost_cents - cost; NULL until billed
  region - region
  dt - load date, yyyyMMdd
ops.region_budgets (partitioned by region)
  job_id - job id
  budget_cents - budget
  region - region
ops.team_notes
  team
  note
  written_on
"""


# How the stand-in user answers, whatever the task.
USER_RULES = """\
- Answer only what Copilot asks, from your answer key, in a sentence or two, as someone who
  knows the business would. You pasted the column definitions; you may name their columns.
- If Copilot asks whether your tables record something, or what a column holds, answer from
  your key; if your key doesn't say, from the column definitions; if neither says, say you
  don't know.
- If Copilot's recommended answer matches your key, accept it. If it doesn't, say what your
  key says.
- If Copilot pushes back on something your key settles, listen, then keep your key's answer.
- If Copilot asks something your key doesn't settle, say you don't mind and take its
  recommendation.
- When Copilot has no more questions, or once you have answered ten, say: "That's all, please
  write the Metric request."
"""


# --- The patterns many keys share ---------------------------------------------------------

EVERY_DAY = (r"every day|all (the )?days|all (the )?dates|every date|whole (table|history)"
             r"|all (of )?(its |the )?history|all together|no (date )?(range|limit)"
             r"|all (the )?rows")
PERCENT = r"100|percent|%"
NOT_ROUNDED = (r"not rounded|unrounded|no rounding|without rounding|full precision"
               r"|n[o']t round|do not round|as it comes")
FINISHED = r"finish|SUCCESS|FAILED|complet"
NULL_RUN = r"NULL|still (going|running)|in progress|unfinished|running"


def left_out(what: str, pattern: str) -> Required:
    """A kind of row Left out must name."""
    return Required(f"{what} left out", "Left out", (pattern,))


def grain(*patterns: str) -> Required:
    """What One row per must say: what a row is, and each condition on which rows exist."""
    return Required("the grain and its conditions", "One row per", patterns, essential=True)


def quantities(*patterns: str) -> Required:
    """The source columns the Quantities must name."""
    return Required("the quantities by their columns", "Quantities", patterns, essential=True)


def values(*patterns: str) -> Required:
    """The values of the source columns the request names."""
    return Required("the columns' values", "", patterns)


def gap(pattern: str) -> tuple[Required, Required]:
    """Where the data can't give the metric: a "Missing data:" line naming what is missing,
    and a fix after it."""
    return (Required("the missing data named", "", (rf"Missing data:[^\n]*({pattern})",),
                     essential=True),
            Required("a fix suggested", "", (r"\bFix:[ \t]*\S",), essential=True))


EVERY_DAY_COUNTED = Required("every day counted", "Days counted", (EVERY_DAY,))
TEST_OUT = left_out("TEST runs", r"\bTEST\b")
NULL_OUT = left_out("runs still going", NULL_RUN)
UNROUNDED = Required("not rounded", "", (NOT_ROUNDED,))


def request(name: str, *columns: tuple[str, tuple[str, ...]]) -> str:
    """A Metric request in file 19's form: each column's name and its nine parts' text."""
    labels = ("What it is", "Formula", "Quantities", "One row per", "Days counted", "Left out",
              "Edge cases", "How to check", "Open questions")
    sections = [f"# Metric request: {name}\n"]
    for column, parts in columns:
        lines = [f"{number}. {label}: {text}"
                 for number, (label, text) in enumerate(zip(labels, parts), start=1)]
        sections.append(f"## Column: {column}\n" + "\n".join(lines) + "\n")
    return "\n".join(sections)


TASKS = (
    MetricTask(
        id="M01",
        split="dev",
        opening="I'd like a new metric: each job's failure rate.",
        answer_key="""\
- One column, the failure rate, one row per job (job_id), over every day the runs table
  (ops.job_runs) holds, all together, not per day.
- Failure rate = failed runs / finished runs x 100, a percent, not rounded.
- A failed run has status FAILED. A finished run has status SUCCESS or FAILED.
- TEST runs are started by hand: leave them out entirely.
- Runs still going have status NULL: leave them out too.
- Each row of ops.job_runs is one run: a retried run counts once.
- Leave out a job with no finished runs.
""",
        columns=1,
        required=(
            Required("a percent", "Formula", (PERCENT,)),
            quantities(r"\bstatus\b"),
            values(r"FAILED", r"SUCCESS"),
            grain(r"job", FINISHED),
            EVERY_DAY_COUNTED, TEST_OUT, NULL_OUT,
            Required("a retried run counted once", "", (r"\bonce\b",)),
            UNROUNDED,
        ),
        example=request("job failure rate", ("failure_rate_pct", (
            "the share of a job's finished runs that failed, as a percent.",
            "failure_rate_pct = 100 x failed runs / finished runs",
            "failed runs: rows of ops.job_runs whose status is FAILED; finished runs: rows "
            "whose status is SUCCESS or FAILED.",
            "job (job_id) with at least one finished run.",
            "every day ops.job_runs holds, as one total.",
            "TEST runs; runs still going (status NULL).",
            "a retried run is one row, counted once; a job with no finished run has no row.",
            "a job whose runs are all TEST or NULL has no row.",
            "none. Not rounded.",
        ))),
    ),
    MetricTask(
        id="M02",
        split="dev",
        opening=("Can you add a workload column for each team per day? Something that shows "
                 "how busy they were."),
        answer_key="""\
- You really want two columns: how many runs, and how many minutes they took. If Copilot asks
  "one column or two?", say two: runs and minutes. If it offers one blended score, say no:
  two plain columns.
- One row per team per day. The team is the jobs table's team (ops.jobs); the day is the runs
  table's dt (ops.job_runs).
- Runs: every run that day but TEST runs, which are started by hand. Runs still going (status
  NULL) count: they are work.
- Minutes: the duration_mins of those same runs, added up.
- A team with no runs that day: leave it out.
""",
        columns=2,
        required=(
            quantities(r"duration_mins"),
            grain(r"\bteam\b", r"\bdt\b|day", r"at least one|with (a |any )?runs?"
                  r"|had (a |any )?runs?|\bran\b"),
            TEST_OUT,
            Required("runs still going counted", "Left out", (NULL_RUN,), absent=True),
            Required("runs still going named as counted", "", (NULL_RUN,)),
            Required("the minutes added up", "Formula", (r"sum|total|add",)),
            EVERY_DAY_COUNTED,
        ),
        example=request(
            "team workload",
            ("runs", (
                "how many runs a team's jobs had on a day.",
                "runs = count of runs",
                "runs: rows of ops.job_runs, each job's team from ops.jobs.team.",
                "team (ops.jobs.team) per day (ops.job_runs.dt), with at least one run.",
                "every day ops.job_runs holds, a row each.",
                "TEST runs.",
                "runs still going (status NULL) count as runs.",
                "a team with only TEST runs on a day has no row that day.",
                "none. Not rounded.")),
            ("minutes", (
                "the minutes those runs took.",
                "minutes = sum of duration_mins of those runs",
                "duration_mins of ops.job_runs.",
                "team per day (dt), with at least one run.",
                "every day ops.job_runs holds, a row each.",
                "TEST runs.",
                "runs still going (status NULL) count, with their minutes so far.",
                "the same rows as runs.",
                "none."))),
        muddled="one asked, two meant",
    ),
    MetricTask(
        id="M03",
        split="dev",
        opening="""\
I want to see how often each job goes over its budget. Here are some rows I copied from the
cost and budget tables:

job_id | cost_cents | region | dt       | budget_cents
1      | 250        | eu     | 20260916 | 150
2      | 200        | eu     | 20260914 | 200
2      | NULL       | eu     | 20260924 | 200
3      | 410        | us     | 20260914 | 350
""",
        answer_key="""\
- One column: the share of the job's billed days that went over budget, as a percent, not
  rounded.
- Over budget: cost_cents more than budget_cents. A cost equal to the budget is not over (job
  2 on 20260914).
- A billed day has a cost_cents. A day whose cost_cents is NULL, its bill not in yet (job 2 on
  20260924), is left out of both counts.
- One row per job, over every day the costs table (ops.region_costs) holds, all together.
- The budget is in ops.region_budgets, for the same job and the same region.
- A job with no billed days: leave it out.
""",
        columns=1,
        required=(
            Required("a percent", "Formula", (PERCENT,)),
            quantities(r"cost_cents", r"budget_cents"),
            Required("the budget for the same region", "", (r"region",)),
            Required("a cost equal to the budget is not over", "Edge cases", (r"equal|same",)),
            Required("a NULL cost left out", "", (r"NULL|blank|bill",)),
            grain(r"job", r"billed|cost|at least one"),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request("over budget", ("over_budget_pct", (
            "the share of a job's billed days whose cost was over its budget, as a percent.",
            "over_budget_pct = 100 x billed days over budget / billed days",
            "billed days: rows of ops.region_costs whose cost_cents is not NULL; over budget: "
            "cost_cents more than budget_cents of ops.region_budgets for the same job and "
            "region.",
            "job (job_id) with at least one billed day.",
            "every day ops.region_costs holds, as one total.",
            "days whose cost_cents is NULL, the bill not in yet.",
            "a cost equal to the budget is not over.",
            "job 2 on 20260914 (200 against 200) is not over; job 2 on 20260924 (NULL) is left "
            "out.",
            "none. Not rounded.",
        ))),
        sample_rows=True,
    ),
    MetricTask(
        id="M04",
        split="dev",
        opening=("I need two new columns for each job: its retries and its fails. We want to "
                 "spot the unreliable jobs."),
        answer_key="""\
- You said two columns because you think of retries and fails as two things, but all you will
  do with them is add them up and rank the jobs by the sum. If Copilot asks what you will do
  with the two, say that. If it asks whether they are really one, or suggests one column,
  agree: one column, retries plus fails, the job's trouble events.
- They are in the events table, ops.job_events, whose event_type is start, finish, retry or
  fail. Each event row counts once.
- One row per job that has any events, over every day the table holds, all together. A job
  with events but no retries or fails shows 0.
""",
        columns=1,
        required=(
            quantities(r"event_type"),
            values(r"retry", r"fail"),
            grain(r"job", r"event"),
            Required("a job with none shows 0", "", (r"\b0\b|zero",)),
            left_out("start and finish events", r"start|finish"),
            Required("each event row once", "", (r"\bonce\b",)),
            EVERY_DAY_COUNTED,
        ),
        example=request("job trouble", ("trouble_events", (
            "how many retries and fails a job had.",
            "trouble_events = retry events + fail events",
            "rows of ops.job_events whose event_type is retry or fail.",
            "job (job_id) with at least one event.",
            "every day ops.job_events holds, as one total.",
            "start and finish events.",
            "a job with events but no retry or fail shows 0; each event row counts once.",
            "a job with only start and finish events shows 0.",
            "none.",
        ))),
        muddled="two asked, one meant",
    ),
    MetricTask(
        id="M05",
        split="held_out",
        opening="Give me a slowness column for each job, so I can see which ones drag.",
        answer_key="""\
- You really want two columns. If Copilot asks "one column or two?", say two. If it offers
  one blended score, say no.
- First: the average minutes (duration_mins) of the job's successful runs (status SUCCESS),
  not rounded.
- Second: how many of the job's finished runs (status SUCCESS or FAILED) took 30 minutes or
  more. 30 itself counts.
- TEST runs, started by hand, and runs still going (status NULL) are left out of both.
- One row per job with a finished run, over every day the runs table (ops.job_runs) holds,
  all together.
""",
        columns=2,
        required=(
            quantities(r"duration_mins", r"\bstatus\b"),
            values(r"SUCCESS"),
            Required("30 minutes itself counts", "", (
                r"30[^\n]*(or more|includ|counts|at least|and over|and above|or longer)"
                r"|(at least|including|exactly)[^\n]*30|>= ?30|≥ ?30",)),
            TEST_OUT, NULL_OUT,
            grain(r"job", FINISHED),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request(
            "job slowness",
            ("avg_success_minutes", (
                "the average minutes of a job's successful runs.",
                "avg_success_minutes = sum of duration_mins / count, over successful runs",
                "duration_mins of rows of ops.job_runs whose status is SUCCESS.",
                "job (job_id) with at least one finished run.",
                "every day ops.job_runs holds, as one total.",
                "TEST runs; runs still going (status NULL).",
                "a job with finished runs but no SUCCESS shows NULL.",
                "a job with one SUCCESS run shows that run's minutes.",
                "none. Not rounded.")),
            ("long_runs", (
                "how many of a job's finished runs took 30 minutes or more.",
                "long_runs = count of finished runs with duration_mins of 30 or more",
                "rows of ops.job_runs whose status is SUCCESS or FAILED.",
                "job (job_id) with at least one finished run.",
                "every day ops.job_runs holds, as one total.",
                "TEST runs; runs still going (status NULL).",
                "a run of exactly 30 minutes counts.",
                "a run of 29 minutes doesn't count.",
                "none."))),
        muddled="one asked, two meant",
    ),
    MetricTask(
        id="M06",
        split="held_out",
        opening="How noisy is each job's alerting? I want a number per job.",
        answer_key="""\
- One column: alerts per run, the alerts the job's runs raised (ops.run_alerts, any severity)
  divided by the job's finished runs (status SUCCESS or FAILED in ops.job_runs), not rounded.
- A finished run with no alerts still counts as a run, with 0 alerts.
- TEST runs, started by hand, and runs still going (status NULL) are left out, and their
  alerts with them.
- One row per job with a finished run, over every day the tables hold, all together.
""",
        columns=1,
        required=(
            quantities(r"run_alerts|alert", r"\bstatus\b"),
            Required("alerts divided by runs", "Formula", (r"alert", r"/|divided|per|over")),
            Required("no invented kind of alert", "Formula",
                     (r"action|acknowledg|closed|ignored|noisy alert",), absent=True,
                     essential=True),
            Required("a run with no alerts counts", "", (r"\b0\b|zero|no alerts?",)),
            TEST_OUT, NULL_OUT,
            grain(r"job", FINISHED),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request("alert noise", ("alerts_per_run", (
            "how many alerts a job's finished runs raised, per run.",
            "alerts_per_run = alerts raised by finished runs / finished runs",
            "alerts: rows of ops.run_alerts, any severity, joined to their run by run_id; "
            "finished runs: rows of ops.job_runs whose status is SUCCESS or FAILED.",
            "job (job_id) with at least one finished run.",
            "every day the tables hold, as one total.",
            "TEST runs and their alerts; runs still going (status NULL) and their alerts.",
            "a finished run with no alerts counts as a run with 0 alerts.",
            "a job whose finished runs raised no alerts shows 0.",
            "none. Not rounded.",
        ))),
    ),
    MetricTask(
        id="M07",
        split="dev",
        opening="I'd like a column showing how serious each job's alerts are.",
        answer_key="""\
- One column: the share of the job's alerts that are high severity, as a fraction from 0 to 1,
  not a percent, not rounded.
- The alerts are in the alerts table (ops.run_alerts); each alert belongs to a run, and the
  run to a job (ops.job_runs). Every alert counts, whatever its run's status.
- One row per job with at least one alert, over every day the tables hold, all together.
""",
        columns=1,
        required=(
            quantities(r"severity"),
            values(r"\bhigh\b"),
            Required("each alert tied to its job by its run", "", (r"run_id|job_runs",)),
            Required("a fraction, not a percent", "Formula", (PERCENT,), absent=True),
            Required("a fraction from 0 to 1", "", (r"fraction|0 (to|and) 1|between 0",)),
            grain(r"job", r"alert"),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request("alert severity", ("high_alert_share", (
            "the share of a job's alerts that are high severity, a fraction from 0 to 1.",
            "high_alert_share = high alerts / alerts",
            "alerts: rows of ops.run_alerts, each joined by run_id to ops.job_runs for its "
            "job_id; high alerts: those whose severity is high.",
            "job (job_id) with at least one alert.",
            "every day the tables hold, as one total.",
            "nothing: every alert counts, whatever its run's status.",
            "a job whose alerts are all low shows 0.",
            "a job with one high and three low alerts shows a quarter.",
            "none. Not rounded.",
        ))),
    ),
    MetricTask(
        id="M08",
        split="dev",
        opening=("Is each job getting slower? I want to see how it changed from one day to "
                 "the next."),
        answer_key="""\
- One column: the job's total minutes on the latest day the runs table (ops.job_runs) holds,
  minus its total minutes on the day before that. Minutes, not a percent; a drop is negative.
- Count only finished runs, status SUCCESS or FAILED: TEST runs are started by hand and runs
  still going (status NULL) haven't finished, so both are left out.
- A job with no finished run on one of the two days counts 0 minutes on that day.
- One row per job with a finished run on either of the two days.
""",
        columns=1,
        required=(
            Required("the latest day minus the day before", "Formula", (
                r"minus|-|−|difference|less|change",
                r"latest|last|most recent|newest|today",
                r"day before|previous|prior|yesterday|earlier")),
            Required("minutes, not a percent", "Formula", (r"percent|%",), absent=True),
            quantities(r"duration_mins", r"\bstatus\b"),
            Required("the latest day and the day before counted", "Days counted",
                     (r"latest|last|most recent|newest",)),
            TEST_OUT, NULL_OUT,
            Required("a day with no finished run counts 0", "Edge cases", (r"\b0\b|zero",)),
            grain(r"job", FINISHED),
        ),
        example=request("day-on-day minutes", ("minutes_change", (
            "how much a job's finished-run minutes changed from one day to the next.",
            "minutes_change = minutes on the latest day - minutes on the day before",
            "minutes: the sum of duration_mins of rows of ops.job_runs whose status is SUCCESS "
            "or FAILED, by their dt.",
            "job (job_id) with a finished run on either of the two days.",
            "the latest dt ops.job_runs holds, and the day before it.",
            "TEST runs; runs still going (status NULL).",
            "a job with no finished run on one of the days counts 0 minutes that day; a drop "
            "is negative.",
            "a job with the same minutes on both days shows 0.",
            "none. Minutes, not a percent.",
        ))),
    ),
    MetricTask(
        id="M09",
        split="dev",
        opening="How many people look after each team's jobs?",
        answer_key="""\
- One column: how many different owners the team's jobs had, over every day the owners table
  (ops.job_owners) holds, all together. A person counts once however many jobs or days.
- The team is the owners table's team on that day, not the jobs table's: a job that moved
  team counts its owner in the team it was in that day.
- A blank owner (NULL) is nobody: it isn't a person and isn't counted.
- One row per team in the owners table. A team whose jobs nobody owns shows 0.
""",
        columns=1,
        required=(
            quantities(r"\bowner\b"),
            Required("each person once", "", (r"distinct|different|unique|once",)),
            Required("the team as the owners table gives it that day", "", (
                r"job_owners|owners table", r"that day|on (the|each) day|at the time"
                r"|each day's|day by day|on that dt|per day",)),
            Required("a NULL owner is nobody", "", (r"NULL|blank|nobody",)),
            Required("a team nobody owns shows 0", "", (r"\b0\b|zero",)),
            grain(r"\bteam\b"),
            EVERY_DAY_COUNTED,
        ),
        example=request("owners per team", ("owners", (
            "how many different people owned a team's jobs.",
            "owners = count of different owner values",
            "owner of ops.job_owners, each person once, in the team ops.job_owners.team gives "
            "on that day.",
            "team in ops.job_owners.",
            "every day ops.job_owners holds, as one total.",
            "rows whose owner is NULL: nobody owns the job.",
            "a team whose jobs nobody owns shows 0; a job that moved team counts its owner in "
            "the team it was in that day.",
            "a team with one owner over every day shows 1.",
            "none.",
        ))),
    ),
    MetricTask(
        id="M10",
        split="dev",
        opening="Can each job get a speed label, so I can sort the slow ones out?",
        answer_key="""\
- One column, a text label from the job's average minutes per finished run (status SUCCESS
  or FAILED), not rounded before it is banded.
- The labels, in lower case exactly: quick under 20 minutes; slow from 20 up to but not
  including 30; very slow at 30 minutes or more. 20 itself is slow, 30 itself is very slow.
- TEST runs, started by hand, and runs still going (status NULL) are left out.
- One row per job with a finished run, over every day the runs table (ops.job_runs) holds.
""",
        columns=1,
        required=(
            Required("the three labels", "", (r"\bquick\b", r"\bslow\b", r"very slow")),
            Required("the limits 20 and 30", "", (r"\b20\b", r"\b30\b")),
            Required("20 is slow and 30 very slow", "Edge cases", (r"\b20\b", r"\b30\b")),
            quantities(r"duration_mins", r"\bstatus\b"),
            TEST_OUT, NULL_OUT,
            grain(r"job", FINISHED),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request("job speed", ("speed", (
            "a label for how long a job's finished runs take on average.",
            "speed = quick if average minutes < 20; slow if 20 <= average < 30; very slow if "
            "average >= 30",
            "average minutes: the mean of duration_mins of rows of ops.job_runs whose status "
            "is SUCCESS or FAILED.",
            "job (job_id) with at least one finished run.",
            "every day ops.job_runs holds, as one total.",
            "TEST runs; runs still going (status NULL).",
            "an average of exactly 20 is slow; exactly 30 is very slow.",
            "a job averaging 19.9 minutes is quick.",
            "none. The average is not rounded before it is labelled.",
        ))),
    ),
    MetricTask(
        id="M11",
        split="dev",
        opening="How fast does each team react when one of its runs fails? A number per team.",
        answer_key="""\
- You mean the time from a run failing to someone on the team picking it up, in minutes.
- You don't think anything records when someone picks a failure up: if Copilot asks, say so.
- You want the real reaction time, not something else in its place. If Copilot offers a
  stand-in, such as a count of failures, say no: you want to know what you would need.
- One row per team, over every day the tables hold.
""",
        columns=1,
        required=(
            *gap(r"react|pick|respon|acknowledg|notic|time"),
            grain(r"\bteam\b"),
            values(r"FAILED"),
            Required("the team by its table", "", (
                r"jobs\.team|job_owners\.team|jobs table|owners table",)),
            Required("minutes as the unit", "", (r"minute",)),
        ),
        example=request("team reaction time", ("reaction_minutes", (
            "the minutes from a run failing to someone on the team picking it up.",
            "reaction_minutes = time picked up - time failed, averaged per team",
            "failed runs: rows of ops.job_runs whose status is FAILED; the time picked up: "
            "no column holds it.",
            "team (ops.jobs.team).",
            "every day the tables hold.",
            "runs that didn't fail.",
            "none settled while the data is missing.",
            "once the data is there: a failure picked up at once shows 0.",
            "Missing data: nothing records when anyone picks a failure up, and dt holds only "
            "the day. Fix: ask your chatbot whether a table records when a failure is picked "
            "up, or add a picked-up time to the runs table.",
        ))),
        missing=True,
    ),
    MetricTask(
        id="M12",
        split="dev",
        opening="""\
I want two columns per team: minutes spent on failed runs and minutes spent on good runs.
Some rows from the runs table, with each job's team:

run_id | team    | status  | duration_mins | dt
96     | finance | SUCCESS | 18            | 2026-09-23
97     | finance | FAILED  | 30            | 2026-09-23
98     | finance | NULL    | 15            | 2026-09-23
102    | finance | FAILED  | 20            | 2026-09-24
""",
        answer_key="""\
- You said two columns, but all you will do is divide the first by the two added up, to see
  how much of the team's time failures waste. If Copilot asks what you will do with them, say
  that; if it asks whether they are really one, or offers one column, agree: one column.
- The one column: minutes of failed runs (status FAILED) as a percent of minutes of finished
  runs (status SUCCESS or FAILED), not rounded.
- TEST runs, started by hand, and runs still going (status NULL, as run 98) are left out of
  both.
- The team is the jobs table's team (ops.jobs); the runs are in ops.job_runs.
- One row per team with a finished run, over every day the runs table holds.
""",
        columns=1,
        required=(
            Required("a percent", "Formula", (PERCENT,)),
            quantities(r"duration_mins", r"\bstatus\b"),
            values(r"FAILED", r"SUCCESS"),
            Required("the team from the jobs table", "", (r"ops\.jobs\b|jobs table|jobs\.team",)),
            TEST_OUT, NULL_OUT,
            grain(r"\bteam\b", FINISHED),
            EVERY_DAY_COUNTED, UNROUNDED,
        ),
        example=request("minutes lost to failures", ("failed_minutes_pct", (
            "the share of a team's finished-run minutes spent on runs that failed, a percent.",
            "failed_minutes_pct = 100 x failed minutes / finished minutes",
            "failed minutes: duration_mins of rows of ops.job_runs whose status is FAILED; "
            "finished minutes: those whose status is SUCCESS or FAILED; the team from "
            "ops.jobs.team.",
            "team with at least one finished run.",
            "every day ops.job_runs holds, as one total.",
            "TEST runs; runs still going (status NULL), such as run 98.",
            "a team with no failed run shows 0.",
            "on the pasted rows, run 98 is left out and runs 96, 97 and 102 count.",
            "none. Not rounded.",
        ))),
        muddled="two asked, one meant",
        sample_rows=True,
    ),
    MetricTask(
        id="M13",
        split="held_out",
        opening="When did each job first blow its budget?",
        answer_key="""\
- One column: the first billed day the job's cost was over its budget, as the day is
  written in the costs table (ops.region_costs), such as 20260916.
- Over budget: cost_cents more than budget_cents. A cost equal to the budget is not over.
- The budget is in ops.region_budgets, for the same job and the same region.
- A day whose cost_cents is NULL, its bill not in yet, is never over.
- One row per job that was over budget on at least one day, over every day the costs table
  holds.
""",
        columns=1,
        required=(
            quantities(r"cost_cents", r"budget_cents"),
            Required("the first day", "", (r"first|earliest|min",)),
            Required("a cost equal to the budget is not over", "Edge cases", (r"equal|same",)),
            Required("a NULL cost is never over", "", (r"NULL|blank|bill",)),
            Required("the budget for the same region", "", (r"region",)),
            grain(r"job", r"over|at least one|exceed"),
            EVERY_DAY_COUNTED,
        ),
        example=request("first over budget", ("first_over_budget_day", (
            "the first billed day a job's cost was over its budget.",
            "first_over_budget_day = the earliest dt whose cost_cents > budget_cents",
            "cost_cents and dt of ops.region_costs; budget_cents of ops.region_budgets for the "
            "same job and region.",
            "job (job_id) over budget on at least one day.",
            "every day ops.region_costs holds.",
            "days whose cost_cents is NULL.",
            "a cost equal to the budget is not over.",
            "a job over budget on two days shows the earlier.",
            "none.",
        ))),
    ),
    MetricTask(
        id="M14",
        split="held_out",
        opening="""\
I want to know how often each team gets paged at night. Some alerts I copied:

alert_id | run_id | severity | dt
1        | 97     | high     | 2026-09-23
5        | 101    | high     | 2026-09-24
6        | 102    | high     | 2026-09-24
""",
        answer_key="""\
- A page is a high-severity alert. At night means between 10 pm and 6 am.
- You don't think the tables keep the time of day, only the day: if Copilot asks, say so.
- You want night pages, not all pages: if Copilot offers every high alert in its place, say
  no: you want to know what you would need for night pages.
- One row per team, over every day the tables hold.
""",
        columns=1,
        required=(
            *gap(r"hour|time|night|clock"),
            Required("a page as a high alert", "", (r"\bhigh\b",)),
            grain(r"\bteam\b"),
            Required("the alerts table named", "", (r"run_alerts",)),
            Required("the team reached through the run and the job", "", (
                r"run_id|job_id|job_runs|ops\.jobs\b",)),
        ),
        example=request("night pages", ("night_pages", (
            "how many high-severity alerts a team's runs raised between 10 pm and 6 am.",
            "night_pages = count of high alerts raised at night",
            "alerts: rows of ops.run_alerts whose severity is high; at night: no column holds "
            "the time.",
            "team (ops.jobs.team).",
            "every day the tables hold.",
            "low alerts.",
            "none settled while the data is missing.",
            "once the data is there: an alert at 9 pm doesn't count.",
            "Missing data: ops.run_alerts keeps only the day (dt), not the time of day. Fix: "
            "ask your chatbot whether any table keeps an alert's time, or add a raised-at time "
            "to ops.run_alerts.",
        ))),
        sample_rows=True,
        missing=True,
    ),
    MetricTask(
        id="M15",
        split="dev",
        opening="What does each run cost us? I want a cost per run.",
        answer_key="""\
- You want each run's own cost, one row per run, over every day the tables hold.
- You think costs are billed per job per day, not per run: if Copilot asks, say so.
- If Copilot offers to split a job's day's cost evenly over its runs that day, say that would
  do as an estimate, if the request calls it one and says what a true cost per run needs.
- A day whose cost isn't billed yet (NULL) is left out.
""",
        columns=1,
        required=(
            *gap(r"per run|each run|by run|run level|grain|per job per day|per day|a day"),
            quantities(r"cost_cents"),
            grain(r"\brun\b"),
            Required("the costs table named", "", (r"region_costs",)),
            Required("the runs table named", "", (r"job_runs|run_id",)),
            Required("a NULL cost left out", "", (r"NULL|not (yet )?billed|unbilled",)),
            Required("the two tables' dates told apart", "", (
                r"yyyyMMdd|format|load date|20260924|written differently|partition date",)),
        ),
        example=request("cost per run", ("est_cost_per_run_cents", (
            "an estimate of what one run cost: its job's billed cost for the day, split evenly "
            "over that job's runs that day.",
            "est_cost_per_run_cents = the job's cost_cents that day / the job's runs that day",
            "cost_cents of ops.region_costs for the job and day; runs: rows of ops.job_runs "
            "(run_id) for the same job and day.",
            "run (run_id) whose job has a billed cost that day.",
            "every day the tables hold.",
            "days whose cost_cents is NULL, not billed yet.",
            "ops.region_costs.dt is a load date written yyyyMMdd; ops.job_runs.dt is written "
            "2026-09-24, so the two are matched as days.",
            "a job with one run on a day gives that run the day's whole cost.",
            "Missing data: costs are billed per job per day, not per run. Fix: ask your "
            "chatbot whether any table bills runs one by one, or ask for a run-level cost; "
            "until then, the column is an estimate.",
        ))),
        missing=True,
    ),
    MetricTask(
        id="M16",
        split="dev",
        opening="How much time does each job waste on retries?",
        answer_key="""\
- You mean the total seconds a job's runs spent waiting between retries, one row per job,
  over every day the tables hold.
- You've seen a column about retry seconds, but you don't know exactly what it holds or what
  it is an average of: if Copilot asks, say you don't know.
- You don't know where the number of retries a run had is kept: if asked, say you don't know.
- TEST runs, started by hand, are left out.
""",
        columns=1,
        required=(
            *gap(r"avg_retry_secs|definition|defined|retr"),
            quantities(r"avg_retry_secs"),
            grain(r"\bjob\b"),
            Required("the number of retries asked for", "", (
                r"how many retries|number of retries|retry count|count of retries"
                r"|retry events|retries a run|retries each run",)),
            Required("the events table's retries named as a lead", "", (
                r"job_events|event_type",)),
            Required("seconds as the unit", "", (r"second|secs",)),
            TEST_OUT, EVERY_DAY_COUNTED,
        ),
        example=request("retry waste", ("retry_wait_secs", (
            "the seconds a job's runs spent waiting between retries, all added up.",
            "retry_wait_secs = sum over runs of (average seconds between retries x retries)",
            "avg_retry_secs of ops.job_runs, whose definition is missing; the number of "
            "retries per run: not known, perhaps the retry rows of ops.job_events (event_type "
            "retry).",
            "job (job_id) with at least one run.",
            "every day ops.job_runs holds, as one total.",
            "TEST runs.",
            "a run with no retries adds 0 seconds.",
            "once defined: a run with two retries 3 seconds apart adds 6 seconds.",
            "Missing data: avg_retry_secs has no definition, and the number of retries per run "
            "isn't known. Fix: ask your chatbot what avg_retry_secs is an average of, and "
            "whether ops.job_events' retry rows count a run's retries.",
        ))),
        missing=True,
    ),
    MetricTask(
        id="M17",
        split="held_out",
        opening="How much does each owner's work cost a day?",
        answer_key="""\
- You mean: for each owner and day, the total cost of the jobs they owned that day.
- The owner is in the owners table (ops.job_owners), a row per job per day; a NULL owner is
  nobody, left out.
- The cost is in the costs table (ops.region_costs), added up over the job's regions. A cost
  not billed yet (NULL) is left out.
- You assume the costs table's date is the day the cost was for, but you aren't sure: if
  Copilot asks what its dt means, say you don't know whether the load date is the billed day.
- One row per owner per day with at least one billed cost.
""",
        columns=1,
        required=(
            *gap(r"load date|\bdt\b|date|day"),
            quantities(r"cost_cents", r"\bowner\b"),
            grain(r"owner", r"day|\bdt\b|date"),
            Required("a NULL owner left out", "", (r"NULL|nobody|no owner",)),
            Required("a NULL cost left out", "", (r"NULL|not (yet )?billed|unbilled",)),
            Required("the job joins them", "", (r"job_id|same job|by job",)),
            Required("the regions added up", "", (r"region",)),
            Required("the two tables' dates told apart", "", (
                r"yyyyMMdd|format|20260924|written differently|snapshot",)),
        ),
        example=request("owner cost per day", ("owner_cost_cents", (
            "the billed cost of the jobs an owner owned on a day.",
            "owner_cost_cents = sum of cost_cents of the jobs the owner owned that day",
            "owner of ops.job_owners, by job_id and its snapshot dt; cost_cents of "
            "ops.region_costs for the same job, every region added up.",
            "owner per day with at least one billed cost.",
            "every day the tables hold.",
            "rows whose owner is NULL (nobody); costs whose cost_cents is NULL, not billed yet.",
            "ops.region_costs.dt is a load date written yyyyMMdd; ops.job_owners.dt is written "
            "2026-09-24.",
            "an owner of two jobs on a day shows the two jobs' costs added.",
            "Missing data: whether ops.region_costs.dt, its load date, is the day the cost was "
            "for. Fix: ask your chatbot or the table's owner what the load date is; if it is "
            "the day after, match each cost to the day before.",
        ))),
        missing=True,
    ),
)

BY_ID = {task.id: task for task in TASKS}
