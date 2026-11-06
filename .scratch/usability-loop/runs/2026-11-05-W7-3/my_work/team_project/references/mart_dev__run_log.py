"""mart_dev.run_log - one run of one job that the run log holds, with its job and day."""
from sqlglot_composer import Table

run_log = Table(
    "mart_dev.run_log",
    columns={
        "run_id": "bigint",
        "job_id": "bigint",
        "dt": "string",
    },
    partitioned_by=["dt"],
    key=["run_id"],
    location="/data/team/mart_dev.db/run_log",
)

from building_blocks.run_values import period_end  # a Run value, for TAGS or SEED
# What each Script tag stands for, as Hive. Answer each under "tags" in the convert notebook's decisions cell: project.write_decisions writes it here, over what is here. A line still holding the tag itself is unanswered.
TAGS = {
    "PERIOD_END": period_end,  # bare, at run_log.hql, line 6. Answer it with its quotes, such as "'2026-09-24'", or a number, such as "5".
}

# The Partitions seed() copies from the original, by partition column: {} copies them
# all. Answer "seed" in the decisions cell, such as {"dt": {"from": "2026-01-01"}}.
SEED = {"dt": {"from": "2026-09-24"}}

# --- Aliases ------------------------------------------------------------------------------
# Your own names for this table's columns and conditions, written by hand below.
# Import one beside the table: from references.mart_dev__run_log import run_log, <alias>
#
# A column Alias is a shorter name for one column, for you: the Hive, and the DataFrame you
# get back, still call the column by its own name. To rename an output, use AS(...).
#     <alias> = run_log.run_id
# A condition Alias names a condition on this table alone, for WHERE or
# count_rows(where=...). Add what it calls, such as equals, to the import at the top.
#     <alias> = equals(run_log.run_id, <value>)
