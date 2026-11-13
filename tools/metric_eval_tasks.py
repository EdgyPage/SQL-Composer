"""The tasks Copilot file 19, Metric request, is measured on (Toolbox 8.7, ticket 11).

Each task is a new metric a user wants on the Example database's tables, as they first say it,
vaguely, and the answer key they keep to themselves: what they really mean, in plain words,
which the stand-in user answers Copilot's questions from. Its reference is the Hive a chatbot
should write from a good Metric request, and its key's numbers, written out by hand, are what
that Hive gives on the Example database; a test holds the two the same. Its naive Hive is the
reading the vague goal invites, which gives other numbers, so a chatbot that guesses fails.

Four tasks are dev, which file 19 may be tuned on, and two are held out, asked once per
version of the Copilot files. Three muddle their columns, as users do: one column asked for
where two are meant ("one asked, two meant"), or two where one is ("two asked, one meant").
One brings sample rows, pasted from the tables.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricTask:
    """A new metric a user wants: what they say first, what they mean, and its numbers."""

    id: str
    split: str  # dev or held_out
    opening: str  # what the user says first: the vague goal, and any sample rows
    answer_key: str  # what the user means, kept from Copilot: the stand-in user answers from it
    reference: str  # the Hive that gives the key's numbers on the Example database
    key_columns: tuple[str, ...]  # the reference's columns: what names a row, then the metric
    key_rows: tuple[tuple[object, ...], ...]  # the key's numbers, worked out by hand
    naive: str  # the Hive the vague goal invites, which gives other numbers
    muddled: str = ""  # "one asked, two meant", "two asked, one meant", or ""
    sample_rows: bool = False


# How the stand-in user answers, whatever the task.
USER_RULES = """\
- Answer only what Copilot asks, from your answer key, in a sentence or two, as someone who
  knows the business but not the tables would. Give a column name only where the key says you
  know it.
- If Copilot's recommended answer matches your key, accept it. If it doesn't, say what your
  key says.
- If Copilot pushes back on something your key settles, listen, then keep your key's answer.
- If Copilot asks something your key doesn't settle, say you don't mind and take its
  recommendation.
- When Copilot has no more questions, or once you have answered ten, say: "That's all, please
  write the Metric request."
"""

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
- You know the column names status and job_id.
""",
        reference="""SELECT job_id,
  100.0 * SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(*) AS failure_rate
FROM ops.job_runs
WHERE status IN ('SUCCESS', 'FAILED')
GROUP BY job_id""",
        key_columns=("job_id", "failure_rate"),
        key_rows=((1, 0.0), (2, 50.0), (3, 50.0)),
        naive="""SELECT job_id,
  100.0 * SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(*) AS failure_rate
FROM ops.job_runs
GROUP BY job_id""",
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
- You know the column names team, status, duration_mins and dt.
""",
        reference="""SELECT j.team, r.dt, COUNT(*) AS runs, SUM(r.duration_mins) AS minutes
FROM ops.job_runs r
JOIN ops.jobs j ON r.job_id = j.job_id
WHERE r.status IS NULL OR r.status <> 'TEST'
GROUP BY j.team, r.dt""",
        key_columns=("team", "dt", "runs", "minutes"),
        key_rows=(("data", "2026-09-23", 1, 12), ("data", "2026-09-24", 2, 50),
                  ("finance", "2026-09-23", 3, 63), ("finance", "2026-09-24", 2, 50)),
        naive="""SELECT j.team, r.dt, SUM(r.duration_mins) AS workload
FROM ops.job_runs r
JOIN ops.jobs j ON r.job_id = j.job_id
GROUP BY j.team, r.dt""",
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
- Worked on your rows: job 1's 250 is over 150; job 2's 200 is not over 200; job 2's NULL
  isn't counted; job 3's 410 is over 350.
- You know the column names cost_cents, budget_cents, region and dt.
""",
        reference="""SELECT c.job_id,
  100.0 * SUM(CASE WHEN c.cost_cents > b.budget_cents THEN 1 ELSE 0 END) / COUNT(*)
    AS over_budget_pct
FROM ops.region_costs c
JOIN ops.region_budgets b ON c.job_id = b.job_id AND c.region = b.region
WHERE c.cost_cents IS NOT NULL
GROUP BY c.job_id""",
        key_columns=("job_id", "over_budget_pct"),
        key_rows=((1, 100 / 14), (2, 200 / 9), (3, 25.0)),
        naive="""SELECT c.job_id,
  SUM(CASE WHEN c.cost_cents > b.budget_cents THEN 1 ELSE 0 END) AS days_over_budget
FROM ops.region_costs c
JOIN ops.region_budgets b ON c.job_id = b.job_id AND c.region = b.region
GROUP BY c.job_id""",
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
- You know the column names event_type and job_id.
""",
        reference="""SELECT job_id,
  SUM(CASE WHEN event_type IN ('retry', 'fail') THEN 1 ELSE 0 END) AS trouble_events
FROM ops.job_events
GROUP BY job_id""",
        key_columns=("job_id", "trouble_events"),
        key_rows=((1, 1), (2, 0), (3, 2)),
        naive="""SELECT job_id,
  SUM(CASE WHEN event_type = 'retry' THEN 1 ELSE 0 END) AS retries,
  SUM(CASE WHEN event_type = 'fail' THEN 1 ELSE 0 END) AS fails
FROM ops.job_events
GROUP BY job_id""",
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
- You know the column names status and duration_mins.
""",
        reference="""SELECT job_id,
  AVG(CASE WHEN status = 'SUCCESS' THEN duration_mins END) AS avg_success_minutes,
  SUM(CASE WHEN duration_mins >= 30 THEN 1 ELSE 0 END) AS long_runs
FROM ops.job_runs
WHERE status IN ('SUCCESS', 'FAILED')
GROUP BY job_id""",
        key_columns=("job_id", "avg_success_minutes", "long_runs"),
        key_rows=((1, 62 / 3, 1), (2, 18.0, 0), (3, 30.0, 2)),
        naive="""SELECT job_id, AVG(duration_mins) AS slowness
FROM ops.job_runs
GROUP BY job_id""",
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
- You know the column names run_id, severity and status.
""",
        reference="""SELECT r.job_id,
  COUNT(a.alert_id) / COUNT(DISTINCT r.run_id) AS alerts_per_run
FROM ops.job_runs r
LEFT JOIN ops.run_alerts a ON a.run_id = r.run_id
WHERE r.status IN ('SUCCESS', 'FAILED')
GROUP BY r.job_id""",
        key_columns=("job_id", "alerts_per_run"),
        key_rows=((1, 4 / 3), (2, 0.5), (3, 2.0)),
        naive="""SELECT r.job_id, COUNT(*) AS alerts
FROM ops.run_alerts a
JOIN ops.job_runs r ON a.run_id = r.run_id
GROUP BY r.job_id""",
    ),
)

BY_ID = {task.id: task for task in TASKS}
