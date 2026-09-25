"""NaN in a list: leaving out the jobs a DataFrame lists leaves out every run.

Why: pandas writes a blank cell as NaN, Hive can only read it as NULL, and a NULL in
`NOT IN (...)` makes the test match no rows at all.
"""

import pandas as pd

from sql_composer import (
    AS, FROM, SELECT, WHERE, count_rows, equals, example_database, is_not_in, statement,
)

job_runs = example_database.job_runs

DAY = "2026-09-24"

# The jobs to leave out, as they might come from a spreadsheet: one cell was left blank.
# pandas reads the blank as NaN, and turns the whole column into floats: [2.0, nan].
LEAVE_OUT = pd.DataFrame({"job_id": [2, None]})


def careless():
    """What most people write first. The Guard refuses the NaN, with no opt-out.

    In Hive it would count 0 runs, when 3 runs on the day are from jobs not left out.
    """
    return statement(
        SELECT(AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY), is_not_in(job_runs.job_id, LEAVE_OUT.job_id.tolist())),
    )


def fixed():
    """Drop the NaN first with pandas' dropna(): the 3 runs of the other jobs come back."""
    leave_out = LEAVE_OUT.job_id.dropna().tolist()
    return statement(
        SELECT(AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY), is_not_in(job_runs.job_id, leave_out)),
    )
