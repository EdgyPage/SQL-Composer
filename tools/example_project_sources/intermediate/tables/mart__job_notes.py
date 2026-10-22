# %% [markdown]
# # mart.job_notes
#
# Each note a team wrote, beside each job the team owned on the day it was written.
#
# Why: a note names only its team, and a team's jobs change, so the jobs a note is about are
# the ones the team owned that day, which ops.job_owners' snapshots say.
#
# Made by `project.new_table("mart.job_notes")` from `admin/templates/saved_table.py`, then
# filled in. It isn't partitioned and has no Key, so write() replaces the whole table, and
# nothing is checked against a Key it doesn't have. A note matches each job its team owned
# that day, several rows of ops.job_owners, which is what this table is for: the join says
# `many_matches=True`, so the Toolbox doesn't warn about it. ops.team_notes isn't partitioned,
# so it is read whole; ops.job_owners is, so the days FIRST_DAY to LAST_DAY are filtered in
# JOIN's ON=.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet.

# %%
# 1. The Project and your query
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run_query, show_hive
from warehouse import query

# %%
# logic
# 2. The logic: imports, the days it looks up, and functions only
from sqlglot_composer import (
    FROM, INSERT_OVERWRITE, JOIN, SELECT, Clause, Statement, all_of, between, create_table,
    equals, statement,
)
from references.mart__job_notes import job_notes
from references.ops__job_owners import job_owners
from references.ops__team_notes import team_notes

FIRST_DAY = "2026-09-11"  # the days of ops.job_owners a note's day is looked up in
LAST_DAY = "2026-09-24"


def create() -> Statement:
    """Step 1: create mart.job_notes from its Table reference, if it isn't there yet."""
    return create_table(job_notes, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share: each note, once for each job its team owned on the
    day it was written."""
    return [
        SELECT(job_owners.job_id, team_notes.team, team_notes.note, team_notes.written_on),
        FROM(team_notes),
        JOIN(job_owners,
             ON=all_of(equals(job_owners.team, team_notes.team),
                       equals(job_owners.dt, team_notes.written_on),
                       between(job_owners.dt, FIRST_DAY, LAST_DAY)),
             many_matches=True),  # a note is about every job its team owned that day
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, replacing the whole table: sent twice, it leaves the same rows,
    not twice as many."""
    return statement(INSERT_OVERWRITE(job_notes), *rows())

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write()])
run_query(preview(), query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write())

# %%
# 5. The Reference sheet: this table's rows, from references/mart__job_notes.py
project.refresh_reference_sheet("mart.job_notes")
