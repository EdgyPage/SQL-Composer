# %% [markdown]
# # Scheduled run: <NAME>
#
# Fill in every `<...>` in the code cells below, brackets and all: the notebook won't run with
# one left. They are:
#   - `<RESULT_NAME>`: the name a SELECT's rows come back by, in quotes, such as
#     `"week_totals"`;
#   - `<SAVED_TABLE>`: a Saved table whose Table notebook's logic it uses, such as
#     `mart.team_days`;
#   - `<LOGIC_FUNCTION>`: the function of that logic it calls, with what it takes, such as
#     `week_totals(FIRST_DAY, LAST_DAY)`, two parameters, or `write()`.
#
# Follow the steps in order, as written.
#
# ## Terms
#
# - **Scheduled run**: this notebook, which an outside scheduler runs top to bottom: building
#   the Statements and their Hive in the Build cell, then sending them in the Run cell.
# - **Parameter**: a value the scheduler passes in, one of the names in the `# parameters`
#   cell, read by its type hint: `"2026-11-01"` given for a `datetime.date` is that date.
# - **Run value**: what a Python function gives each time a Statement is built, such as the
#   latest Partition of a table; `run_values=` gives one a value of yours for this run.
#
# ## Steps
#
# 1. **Name the parameters.** Goal: each value the scheduler passes in. Action: write each in
#    the `# parameters` cell as a name, its type hint and its default, such as
#    `RUN_DATE: datetime.date | None = None`; keep `START_FROM`. Done when each has a hint;
#    then step 2.
# 2. **Connect.** Goal: this run's account. Action: in the setup cell, write your connection
#    in the `connect(...)` line and delete its `#`. Done when the setup cell runs; then step 3.
# 3. **Name the Statements.** Goal: what this run sends. Action: write each in the dict
#    `statements()` gives, in the `# scheduled` cell, by name. If it is a Table notebook's
#    logic, load it: `project.load("mart.team_days").week_totals(FIRST_DAY, LAST_DAY)`. If
#    it is your own, compose it there, with `statement(...)`. Done when each is named; then
#    step 4.
# 4. **Build.** Goal: the Hive, in order, to read before anything is sent. Action: run the
#    cells down to the Build cell. If a table it would write is written elsewhere, name it in
#    `leave_out=`. Done when it prints each Statement's Hive in order; then step 5.
# 5. **Run.** Goal: the Statements sent and the SELECTs' rows back. Action: run the Run cell,
#    or have the scheduler run the notebook. Done when it ends with no error; each SELECT's
#    rows are in `results` by the name `statements()` gives it, such as
#    `results["week_totals"]`.
#
# ## What the build prints
#
# First each parameter as used, then each Statement in the order it is sent, headed like
# `-- 3 of 7: mart.team_days (read by week_totals)`, and its Hive. The writes of each table of
# this Project the Statements read are added, all the way up, before what reads them.
#
# Made by `project.new_scheduled_run("<NAME>")` from `admin/templates/scheduled_run.py`.
#
# ## Self-check
#
# - No code cell holds a `<...>`.
# - Each parameter in the `# parameters` cell has a type hint.
# - The Build cell prints each Statement's Hive, in order, and sends nothing.

# %%
# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
# RUN_DATE: datetime.date | None = None  # such as "2026-11-01", passed in as text

# %%
# Setup: the Project on Python's path, the Toolbox and your connection
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import Statement, project, statement
from warehouse import connect, execute, query

# Your connection to the warehouse. Each notebook runs on its own, so each connects here, at
# its top, before it calls query or execute: write yours in the line below and delete its #,
# such as connect(your_library.connect(...)). A connection kept in a file outside the Project,
# such as team_connection.py, is imported by these lines, written in that line's place:
#     sys.path.append("C:/work/connections")  # the folder team_connection.py is in
#     from team_connection import conn
#     connect(conn)
# connect(your_connection)

# %%
# scheduled
# The Statements this run sends, each by its name: a SELECT's rows come back in results by it.
# A Table notebook's logic gives them through project.load, such as
#     "week_totals": project.load("mart.team_days").week_totals(FIRST_DAY, LAST_DAY),
# and a Statement of your own is composed here with statement(...). A value worked out each
# time the run is built goes in as run_value(function), a function of this cell, such as
# week_totals(run_value(week_start), ...): import run_value from sqlglot_composer here.


def statements() -> dict[str, Statement]:
    """What this run sends, by name: the build adds the writes of each table they read."""
    return {
        "<RESULT_NAME>": project.load("<SAVED_TABLE>").<LOGIC_FUNCTION>,
    }

# %%
# Build: the Statements, in order, and their Hive, printed; nothing sent
# It reads the parameters first, then builds each Statement, adding the writes of each table
# of this Project they read. run_values={"period_end": RUN_DATE} gives a parameter of yours,
# RUN_DATE, to each Run value whose function is named period_end, in the writes added too;
# leave_out=["mart.daily_job_runs"] leaves out that table's write, and what only it reads.
built = project.build_run(statements, run_values={}, leave_out=[])

# %%
# Run: each one sent, in the build's order
# Each write is sent through execute and each SELECT through query; each SELECT's rows are in
# results by the name statements() gives it, such as results["week_totals"]. One that fails
# stops the rest, and the run prints the START_FROM to send the rest from.
results = built.run(query, execute)
