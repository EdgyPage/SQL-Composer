"""Write the workbooks `tests/test_workbook_text.py` reads `copilot/workbook_text.py` on, into
`tests/fixtures/workbook_text/`.

Each is a copy of the empty Formula workbook, filled in, with its Power Queries saved as Excel
saves them (`tools/excel_queries.py`), so a person can open it in Excel to see that it opens.
Beside each, `<name>.txt` is what the script writes of it, or, for one it refuses, its refusal.

    .venv/Scripts/python tools/workbook_fixtures.py

It writes a workbook only when what it holds differs from the one there: a new build differs
in its bytes, the times its parts were saved, though nothing in it does.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "copilot"), str(ROOT / "tools")]

import workbook_text  # noqa: E402
from excel_eval_tasks import OWNER_TABLE, jobs_table, runs_table, table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402

FOLDER = ROOT / "tests" / "fixtures" / "workbook_text"
# docProps/core.xml holds the time a workbook was built, which differs each build.
BUILT_AT = "docProps/core.xml"

FIXTURES = {
    # A query, the Table it loads, and a summary whose formulas read that Table.
    "01_query_table_formula": FormulaWorkbook(
        (runs_table(),
         ExcelTable("ok_runs", ("run_id", "job_id", "duration_mins"),
                    "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE status = "
                    "'SUCCESS' ORDER BY run_id", loaded_by="ok_runs"),
         ExcelTable("ok_by_job", ("job_id", "ok_mins"),
                    "SELECT DISTINCT job_id FROM ops.job_runs ORDER BY job_id",
                    {"ok_mins": "=SUMIFS(ok_runs[duration_mins],ok_runs[job_id],[@job_id])"})),
        queries=(("ok_runs", f"""let
    Source = {table("job_runs")},
    Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),
    Kept = Table.SelectColumns(Ok, {{"run_id", "job_id", "duration_mins"}})
in
    Kept"""),),
        as_typed=True),
    # A connection-only query, read by a query that loads a Table.
    "02_query_reads_query": FormulaWorkbook(
        (jobs_table(), OWNER_TABLE,
         ExcelTable("owners_by_team", ("team", "owner"),
                    "SELECT DISTINCT j.team, o.owner FROM ops.jobs j JOIN ops.job_owners o ON "
                    "j.job_id = o.job_id ORDER BY j.team, o.owner",
                    loaded_by="owners_by_team")),
        queries=(("staffed", f"""let
    Jobs = {table("jobs")},
    Owners = {table("job_owners")},
    Joined = Table.NestedJoin(Jobs, {{"job_id"}}, Owners, {{"job_id"}}, "o", JoinKind.Inner),
    Expanded = Table.ExpandTableColumn(Joined, "o", {{"owner"}})
in
    Expanded"""), ("owners_by_team", """let
    Source = staffed,
    Kept = Table.Distinct(Table.SelectColumns(Source, {"team", "owner"}))
in
    Kept""")),
        as_typed=True),
    # A loop: Table looped reads the Table query back loads, and query back reads looped.
    "03_loop": FormulaWorkbook(
        (runs_table(),
         ExcelTable("looped", ("run_id", "mins"),
                    "SELECT run_id FROM ops.job_runs ORDER BY run_id",
                    {"mins": "=XLOOKUP([@run_id],back[run_id],back[duration_mins])"}),
         ExcelTable("back", ("run_id", "duration_mins"),
                    "SELECT run_id, duration_mins FROM ops.job_runs ORDER BY run_id",
                    loaded_by="back")),
        queries=(("back", f"""let
    Source = {table("looped")}
in
    Source"""),),
        as_typed=True),
}


def expected(workbook: bytes) -> str:
    """What the script writes of a workbook, or, when it refuses one, its refusal."""
    try:
        return workbook_text.workbook_text(workbook)
    except workbook_text.LoopError as error:
        return f"Refused: {error}\n"


def contents(workbook: bytes) -> dict[str, bytes]:
    """Each part of a workbook but the one holding when it was built."""
    with zipfile.ZipFile(io.BytesIO(workbook)) as parts:
        return {name: parts.read(name) for name in parts.namelist() if name != BUILT_AT}


def main() -> int:
    """Write each fixture and its text, unless the one there holds the same."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, described in FIXTURES.items():
        built = saved(described)
        path = FOLDER / f"{name}.xlsx"
        if not path.exists() or contents(path.read_bytes()) != contents(built):
            path.write_bytes(built)
            print(f"Wrote {path.relative_to(ROOT).as_posix()}.")
        (FOLDER / f"{name}.txt").write_text(expected(path.read_bytes()), encoding="utf-8",
                                            newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
