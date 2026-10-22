# %% [markdown]
# # <DB>.<TABLE>
#
# TODO: say in one line what one row of <DB>.<TABLE> is.
#
# A table that looks each row up as of its own day: each day's rows, counted per value a
# snapshot table held for them on that day, such as the team that owned each job then.
#
# Made by `project.new_table("<DB>.<TABLE>", template="as_of_lookup")` from
# `admin/templates/as_of_lookup.py`, which filled in the database, the table and its file's name,
# <NAME>. Run the cells top to bottom, once you have filled in two things.
#
# First, this table's Table reference, `references/<NAME>.py`: its `<...>` and TODO lines.
# It lists the columns write_day saves, as its SELECT names them: here <LOOKED_UP_COLUMN>,
# typed as the snapshot types it, and "row_count", a count, "bigint"; then "dt", the day. Its
# key is [<LOOKED_UP_COLUMN>, "dt"].
#
# The snapshot's own Table reference must declare its Key too, such as key=["job_id", "dt"]:
# its key column and its day, so that each row matches one snapshot row. Without it, the join
# warns that a row may match several.
#
# Then every `<...>` left in this notebook: the notebook won't run with one left. They are:
#
#   - `<SOURCE_NAME>` and `<SOURCE_TABLE>`: the table it reads, by its file in
#     references/ and its name there, such as `ops__job_runs` and `job_runs`;
#   - `<DATE_PARTITION>`: that table's Date partition, its day column, such as `dt`;
#   - `<MATCH_COLUMN>`: its column holding the key looked up, such as `job_id`;
#   - `<SNAPSHOT_NAME>` and `<SNAPSHOT>`: the snapshot table, one row per key per day, by its
#     file in references/ and its name there, such as `ops__job_owners` and `job_owners`;
#   - `<SNAPSHOT_MATCH_COLUMN>`, `<SNAPSHOT_DATE_PARTITION>` and `<LOOKED_UP_COLUMN>`: its
#     key column, its day column, and the column looked up, such as `job_id`, `dt` and `team`;
#   - `<DAY>`: a day both tables have, in quotes, such as `"2026-09-24"`.
#
# The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
# 4 its lineage; 5 its rows in the Reference sheet. The logic only imports and defines, so
# `project.load("<DB>.<TABLE>")` can run it from anywhere else, for lineage across your
# tables and for `admin/run_tables.ipynb`.

# %%
# 1. The Project, your query, and a day to try things on
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.cwd().parents[1]))  # the Project folder: two up from here

from sqlglot_composer import export_lineage, project, run, show_hive
from warehouse import query

DAY = <DAY>  # a day to try the cells on, in quotes, such as "2026-09-24"

# %%
# logic
# 2. The logic: imports and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, LEFT_JOIN, SELECT, WHERE, Clause, Statement,
    all_of, between, count_rows, create_table, equals, statement,
)
from references.<NAME> import <TABLE>  # this table's own Table reference
# the rows looked up for, such as: from references.ops__job_runs import job_runs
from references.<SOURCE_NAME> import <SOURCE_TABLE>
# the snapshot, such as: from references.ops__job_owners import job_owners
from references.<SNAPSHOT_NAME> import <SNAPSHOT>


def create() -> Statement:
    """Step 1: create <DB>.<TABLE> from its Table reference, if it isn't there yet."""
    return create_table(<TABLE>, may_exist=True)


def rows(day: str) -> list[Clause]:
    """The day's rows per value looked up as of the day: the clauses preview and write_day
    share. A row with no snapshot that day is counted under NULL. The day stays in GROUP_BY, so the days stay apart, and out of SELECT: INSERT_OVERWRITE
    writes it as this table's Date partition, the day the table read is bounded to."""
    return [
        SELECT(<SNAPSHOT>.<LOOKED_UP_COLUMN>, AS(count_rows(), "row_count")),
        FROM(<SOURCE_TABLE>),
        # The snapshot's day goes in ON=, not WHERE: a WHERE on it would drop the rows LEFT_JOIN
        # keeps for having no snapshot. Matching the days alone doesn't bound the snapshot's
        # days, which every read must, so between(...) bounds them too.
        LEFT_JOIN(<SNAPSHOT>, ON=all_of(  # all_of: every condition in it must hold
            equals(<SNAPSHOT>.<SNAPSHOT_MATCH_COLUMN>, <SOURCE_TABLE>.<MATCH_COLUMN>),
            equals(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, <SOURCE_TABLE>.<DATE_PARTITION>),
            between(<SNAPSHOT>.<SNAPSHOT_DATE_PARTITION>, day, day),
        )),
        WHERE(between(<SOURCE_TABLE>.<DATE_PARTITION>, day, day)),
        GROUP_BY(<SOURCE_TABLE>.<DATE_PARTITION>, <SNAPSHOT>.<LOOKED_UP_COLUMN>),
    ]


def preview(day: str) -> Statement:
    """Step 2: the rows write_day(day) would save, as a SELECT to run and check first."""
    return statement(*rows(day))


def write_day(day: str) -> Statement:
    """Step 3, every day: save the day's rows, replacing whatever the day held."""
    return statement(INSERT_OVERWRITE(<TABLE>), *rows(day))

# %%
# 3. Try it: the Hive of each step, then the rows
show_hive([create(), write_day(DAY)])
run(preview(DAY), query=query)

# %%
# 4. Lineage: a new pair in lineage/, named by the time and this table, beside the ones before
export_lineage(write_day(DAY))

# %%
# 5. The Reference sheet: this table's rows, from references/<NAME>.py
project.refresh_reference_sheet("<DB>.<TABLE>")
