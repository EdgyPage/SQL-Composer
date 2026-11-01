import json, sys
from pathlib import Path

path = Path(sys.argv[1])
raw = path.read_text(encoding="utf-8")
nb = json.loads(raw)

header = '''# mart_dev.runs_per_day

One row per job and day of ops.job_runs: how many runs that job had that day, for
2026-09-23 and 2026-09-24.

A Saved table worked out from a table it reads: a count per group of the rows READS picks.
It is partitioned by dt, the day each row is for.

Made by `project.new_table("mart_dev.runs_per_day")` from `admin/templates/saved_table.py`,
which filled in the database, the table and its file's name, mart_dev__runs_per_day.

The code cells: 1 the Project and your query; 2 the logic, which starts `# logic`; 3 try it;
4 its lineage; 5 its Hive, in mart_dev__runs_per_day.hql; 6 its rows in the Reference sheet.
The logic only imports and defines, so `project.load("mart_dev.runs_per_day")` can run it from
anywhere else, for lineage across your tables and for `admin/run_tables.ipynb`, which sends its
`write()`.
'''

logic = '''# logic
# 2. The logic: imports, the rows it reads, and functions only
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, Clause, Statement, between, count_rows,
    create_table, statement,
)
from references.mart_dev__runs_per_day import runs_per_day  # this table's own Table reference
from references.ops__job_runs import job_runs

# The rows write() reads: the runs of 2026-09-23 and 2026-09-24, a day each, as dt is ops.job_runs' partition.
READS = between(job_runs.dt, "2026-09-23", "2026-09-24")

# This table's partition columns, in the order its SELECT gives them, last: [] for none.
PARTITIONED_BY = ["dt"]


def create() -> Statement:
    """Step 1: create mart_dev.runs_per_day from its Table reference, if it isn't there yet."""
    return create_table(runs_per_day, may_exist=True)


def rows() -> list[Clause]:
    """The clauses preview and write share, so the two can never disagree: the runs of each
    job on each day, counted, for the days READS picks.

    A partitioned table's partition columns come last in SELECT, in its Table reference's
    order, named as it names them: INSERT_OVERWRITE fills each Partition from the rows' own
    values, and replaces only the Partitions they fill. They stay in GROUP_BY too, so each
    Partition's rows stay apart.
    """
    return [
        SELECT(
            job_runs.job_id,  # what each row is for
            AS(count_rows(), "runs"),
            job_runs.dt,  # this table's partition column, last
        ),
        FROM(job_runs),
        WHERE(READS),
        GROUP_BY(
            job_runs.job_id,
            job_runs.dt,  # kept, so each Partition's rows stay apart
        ),
    ]


def preview() -> Statement:
    """Step 2: the rows write() would save, as a SELECT to run and check first."""
    return statement(*rows())


def write() -> Statement:
    """Step 3: save the rows, replacing the Partitions they fill, or the whole table if it
    isn't partitioned: sent twice, it leaves the same rows, not twice as many."""
    return statement(INSERT_OVERWRITE(runs_per_day), *rows())
'''

cells = nb["cells"]
assert cells[0]["cell_type"] == "markdown"
assert cells[2]["cell_type"] == "code" and "# logic" in "".join(cells[2]["source"])
cells[0]["source"] = header.splitlines(keepends=True)
cells[2]["source"] = logic.splitlines(keepends=True)
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
print("ok")
