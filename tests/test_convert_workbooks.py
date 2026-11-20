"""The convert Workflow reads a Formula workbook (Toolbox 8.9, ticket 07; ADR 0016).

`project.convert(..., files=["runs.xlsx"])` takes an Excel workbook, alone or beside `.hql`
scripts. Each final's Hive, as `workbook_hive.py` writes it with the batch's database filled
in, is kept in the batch's scripts/ as Hive given as text is, and converted as every batch's
Hive is: a Table folder and a Table reference each, the checklist, `# CONVERSION:` marks and
Unchecked pieces. What the workbook's map says of each final is a note of its checklist. A
pivot keeping Excel's default name, and a final named as a table it reads, get a proposed
name, a Decision, which an answer renames; a pivot over a plain range reads the database table
proposed for its sheet, a Decision too. Each Pivot filter is recorded for its table, the same
record from a workbook's pivot as from a Copilot `.hql` whose condition carries `-- Pivot
filter: <kind> <field>`, for ticket 08's Decision, and the workbook and final each table came
from, for ticket 09's Workbook check. Each workbook of each kind runs end to end here, on the
Example database.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

import example_database
from sqlglot_composer import project, run_execute, run_query, set_admin_log, to_hive
from sqlglot_composer.pivot_filters import pivot_filters_in, pivot_filters_of_batch
from sqlglot_composer.workbook_conversion import FinalOrigin
from sqlglot_composer.workbook_hive import hive_texts, workbook_hive
from sqlglot_composer.workbook_pivot_hive import (
    HIDDEN_ITEMS,
    REPORT_FILTER,
    SLICER,
    TIMELINE,
    TOP_FILTER,
    ConvertedPivotFilter,
    pivot_filters,
)
from sqlglot_composer.workbook_reader import read_workbook
from sqlglot_composer.workflows import CONVERT

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]

from excel_eval_tasks import RUNS, rows, runs_table, table  # noqa: E402
from formula_workbook import ExcelTable, FormulaWorkbook, saved  # noqa: E402
from pivot_tables import Pivot, Top, Value  # noqa: E402

workbook_conversion = toolbox_module("workbook_conversion")
FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
NOW = datetime.datetime(2026, 11, 19, 9, 30, 0)
DEV = "mart_dev"
HOURS = runs_table(formulas={"hours": "=[@duration_mins]/60"})
HOURS_ROWS = ("SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt, "
              "duration_mins / 60 AS hours FROM ops.job_runs ORDER BY run_id")
LONG_RUNS = ExcelTable("long_runs", ("run_id", "job_id", "minutes"),
                       "SELECT run_id, job_id, duration_mins FROM ops.job_runs WHERE "
                       "duration_mins > 15 ORDER BY run_id", loaded_by="long_runs")
LONG_RUNS_M = f"""let
    Source = {table("job_runs")},
    Kept = Table.SelectColumns(Source, {{"run_id", "job_id", "duration_mins"}}),
    Long = Table.SelectRows(Kept, each [duration_mins] > 15),
    Renamed = Table.RenameColumns(Long, {{{{"duration_mins", "minutes"}}}})
in
    Renamed"""
# A workbook of each kind, built as the dev tool saves one, its query on a Power Query sheet.
BUILT = {
    "formulas": FormulaWorkbook((HOURS,)),
    "power_query": FormulaWorkbook((runs_table(), LONG_RUNS),
                                   queries=(("long_runs", LONG_RUNS_M),),
                                   queries_on_sheet=True),
    "total_row": FormulaWorkbook((ExcelTable(
        "job_runs", ("run_id", "job_id", "duration_mins", "hours"),
        rows("job_runs", ("run_id", "job_id", "duration_mins")),
        {"hours": "=[@duration_mins]/60"},
        totals={"run_id": "Total",
                "duration_mins": "=SUBTOTAL(109,job_runs[duration_mins])"}),)),
    "mix": FormulaWorkbook(
        (HOURS, LONG_RUNS), queries=(("long_runs", LONG_RUNS_M),), queries_on_sheet=True,
        pivots=(Pivot("job_runs", ("job_id",), (Value("hours"),), name="hours_by_job",
                      source_rows=HOURS_ROWS),)),
    "marks": FormulaWorkbook((runs_table(formulas={
        "hours": "=[@duration_mins]/60", "next_month": "=EDATE([@dt],1)",
        "found": '=INDIRECT("A1")'}),), chart=True),
    "top": FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("job_id",), (Value("duration_mins"),), top=Top("job_id", 2)),)),
    "sources_alone": FormulaWorkbook((runs_table(),)),
    # A column named as no database names one: its Hive holds <hours_run>, to fill in.
    "unplain": FormulaWorkbook((ExcelTable(
        "run_hours", (*RUNS, "Hours Run"), rows("job_runs", RUNS),
        {"Hours Run": "=[@duration_mins]/60"}),)),
}
# Each kind's tables in dev, in the order the batch makes them.
TABLES = {
    "formulas": ["job_runs_report"],
    "power_query": ["long_runs"],
    "total_row": ["job_runs_report", "job_runs_report_total_row"],
    "pivot": ["pivot", "pivot_by_job_id", "pivot_by_dt", "pivot_grand_total"],
    "slicer": ["pivot", "runs_by_day", "pivot_grand_total", "runs_by_day_grand_total"],
    "mix": ["hours_by_job", "long_runs", "hours_by_job_grand_total"],
    "range": ["pivot"],
}
FIXTURE_OF = {"pivot": "04_pivot_rows_columns", "slicer": "05_pivot_slicer_two_pivots",
              "timeline": "08_pivot_timeline_filters", "range": "09_pivot_plain_range"}
# A Copilot reply's Hive for fixture 05's PivotTable1, its Pivot filter marked above its
# condition as Copilot file 20 has Copilot write it.
COPILOT_PIVOT = """\
SELECT
  job_id,
  SUM(duration_mins) AS sum_of_duration_mins
FROM ops.job_runs
WHERE
  -- Pivot filter: slicer status
  status IN ('FAILED', 'SUCCESS')
GROUP BY
  job_id;
"""


@pytest.fixture(scope="module")
def books() -> dict[str, bytes]:
    """Each workbook of BUILT, saved as the dev tool saves one, and each fixture FIXTURE_OF
    names."""
    found = {name: saved(described) for name, described in BUILT.items()}
    for kind, fixture in FIXTURE_OF.items():
        found[kind] = (FIXTURES / f"{fixture}.xlsx").read_bytes()
    return found


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in, left off Python's path afterwards with its
    modules, which a convert puts there, so another test reads its own."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', f'"{DEV}"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def given(root: Path, books: dict[str, bytes], kind: str, name: str = "runs.xlsx") -> str:
    """The workbook of `kind`, saved in the Project as `name`: its name."""
    (root / name).write_bytes(books[kind])
    return name


def converted(root: Path, books: dict[str, bytes], kind: str, **arguments: object) -> str:
    """convert's report of the workbook of `kind`, alone in the batch book."""
    return repr(project.convert("book", files=[given(root, books, kind)],
                                query=example_database.query, database="ops", **arguments))


def checklist(root: Path, table: str) -> str:
    stem = f"{DEV}__{table}"
    return (root / "tables" / stem / "conversion" / "checklist.md").read_text(encoding="utf-8")


def batch_folder(root: Path, name: str = "book") -> Path:
    return root / "admin" / "workflows" / "convert" / name


# --- A workbook of each kind, end to end ---------------------------------------------------


@pytest.mark.parametrize("kind", list(TABLES))
def test_each_final_of_a_workbook_is_a_saved_table_in_dev(
        started: Path, books: dict[str, bytes], kind: str) -> None:
    report = converted(started, books, kind)
    tables = [f"{DEV}.{name}" for name in TABLES[kind]]
    assert f"of runs.xlsx, {len(tables)} statement" in report
    assert project.batch_tables("book") == tables
    for name in TABLES[kind]:
        stem = f"{DEV}__{name}"
        assert (started / "tables" / stem / f"{stem}.ipynb").is_file()
        assert (started / "references" / f"{stem}.py").is_file()
        assert "# Checklist: " in checklist(started, name)
    # It reads the sources in the database convert names, which has their Table references.
    source = "ops__runs.py" if kind == "range" else "ops__job_runs.py"
    assert (started / "references" / source).is_file()


@pytest.mark.parametrize("kind", [kind for kind in TABLES if kind != "range"])
def test_each_table_a_workbook_made_runs_on_the_example_database(
        started: Path, books: dict[str, bytes], kind: str) -> None:
    converted(started, books, kind)
    for made in project.batch_tables("book"):
        assert run_query(project.load(made).preview(), example_database.query) is not None


def test_each_finals_hive_is_kept_in_the_batchs_scripts_and_the_workbook_read_where_it_is(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    folder = batch_folder(started)
    scripts = sorted(path.name for path in (folder / "scripts").iterdir())
    assert scripts == sorted(f"{name}.hql" for name in TABLES["slicer"])
    hive = (folder / "scripts" / "pivot.hql").read_text(encoding="utf-8")
    assert "FROM ops.job_runs" in hive and "<database>" not in hive
    assert "/* Pivot filter: slicer status */" in hive
    batch = (folder / "batch.md").read_text(encoding="utf-8")
    assert ("runs.xlsx, a workbook read where it is, each of its 4 finals kept as its Hive in "
            "scripts/: pivot.hql, ") in batch
    # The workbook itself is never copied.
    assert not list(folder.rglob("*.xlsx"))


def test_the_batch_records_the_workbook_and_the_final_each_table_came_from(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    origins = workbook_conversion.final_origins_of_batch(started, "book")
    assert origins[f"{DEV}.pivot"] == FinalOrigin("runs.xlsx", "PivotTable1")
    assert origins[f"{DEV}.runs_by_day_grand_total"] == FinalOrigin(
        "runs.xlsx", "runs_by_day (grand total)")
    assert workbook_conversion.final_origins_of_batch(started, "none") == {}


def test_a_workbook_converts_beside_scripts_in_one_batch(
        started: Path, books: dict[str, bytes]) -> None:
    (started / "failed.hql").write_text(
        "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24' AND r.status = "
        "'FAILED'\n", encoding="utf-8")
    files = ["failed.hql", given(started, books, "formulas")]
    report = repr(project.convert("book", files=files, query=example_database.query,
                                  database="ops"))
    assert "Converted book: 1 script and 1 final of runs.xlsx, 2 statements" in report
    assert project.batch_tables("book") == [f"{DEV}.failed", f"{DEV}.job_runs_report"]
    batch = (batch_folder(started) / "batch.md").read_text(encoding="utf-8")
    assert ("1 script, each read where it is: failed.hql; runs.xlsx, a workbook read where it "
            "is, its final kept as its Hive in scripts/: job_runs_report.hql.") in batch
    assert [path.name for path in (batch_folder(started) / "scripts").iterdir()] == [
        "job_runs_report.hql"]


def test_file_names_one_workbook_as_files_does(started: Path, books: dict[str, bytes]) -> None:
    project.convert("book", file=given(started, books, "formulas"),
                    query=example_database.query, database="ops")
    assert project.batch_tables("book") == [f"{DEV}.job_runs_report"]


def test_the_conversion_marks_and_unchecked_pieces_are_a_batchs(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "pivot")
    notes = checklist(started, "pivot")
    # Its read of job_runs, filtered on no Partition, keeps what the original did.
    assert "FROM(job_runs, reads_all_partitions=True), in the logic cell" in notes
    batch = (batch_folder(started) / "batch.md").read_text(encoding="utf-8")
    assert "# CONVERSION: FROM(job_runs, reads_all_partitions=True)" in batch


# --- The map's notes, table by table -------------------------------------------------------


def test_each_mark_refusal_and_thing_left_alone_is_in_its_tables_checklist(
        started: Path, books: dict[str, bytes]) -> None:
    report = converted(started, books, "marks")
    notes = checklist(started, "job_runs_report")
    assert ("From the workbook, marked (rule F6, in Copilot file 11): job_runs[next_month]: "
            in notes)
    assert ("Next: check the values it gives are the ones you want, as the compare step shows "
            "them.") in notes
    assert ("From the workbook, refused (rule X1, in Copilot file 11 or 12): job_runs[found]: "
            "NULL in its place") in notes
    assert ("Next: it is NULL, or left out, in the table: if you need it, write it yourself in "
            "the table's logic cell.") in notes
    # The chart belongs to no table: batch.md lists it, and the report says so.
    batch = (batch_folder(started) / "batch.md").read_text(encoding="utf-8")
    assert "## The workbook runs.xlsx" in batch
    assert ("- From the workbook, left alone (rule X1, in Copilot file 11 or 12): Sheet "
            "\"Summary\": a bar chart") in batch
    assert ("1 thing in runs.xlsx belongs to no table, such as a chart left alone or a "
            "PivotTable refused: batch.md lists it, each with what to do.") in report


def test_a_pivot_filter_is_in_its_tables_checklist(started: Path,
                                                   books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    for name in ("pivot", "pivot_grand_total", "runs_by_day"):
        assert "From the workbook, marked (rule PF3, in Copilot file 20): " in checklist(
            started, name)
        assert ("Pivot filter: slicer status, FAILED and SUCCESS kept: a Decision of its "
                "table.") in checklist(started, name)


# --- A table's name, a Decision -----------------------------------------------------------


def decide(answers: dict[str, dict[str, object]]) -> str:
    """write_decisions' report of `answers`, for the batch book's tables."""
    return repr(project.write_decisions(answers, tables=project.batch_tables("book")))


def test_a_pivots_default_name_is_a_decision_check_lists(
        started: Path, books: dict[str, bytes]) -> None:
    report = converted(started, books, "slicer")
    assert ("Named as proposed, a Decision of each in its checklist: mart_dev.pivot, for "
            'PivotTable1 of runs.xlsx. Answer "name" in the decisions cell: "proposed" keeps '
            "it, or a name of your own renames the table.") in report
    assert ('"name": "proposed",  # keeps pivot; or a name of your own, such as '
            '"runs_by_job", renames the table') in report
    notes = checklist(started, "pivot")
    assert ("- name: pivot, proposed for PivotTable1 of runs.xlsx: keep it with \"proposed\", "
            "or answer a name of your own, which renames the table") in notes
    assert ("Its name, pivot, is proposed: PivotTable1 is Excel's default name, so it is named "
            "for its sheet, Pivot.") in notes
    assert "name: pivot, proposed" in repr(project.check())
    # Its total levels' tables are named with it, and wait on it; runs_by_day is its own name.
    assert "name:" not in checklist(started, "pivot_grand_total")
    assert "name:" not in checklist(started, "runs_by_day")


def test_answering_proposed_keeps_the_name(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({f"{DEV}.pivot": {"name": "proposed"}})
    assert project.batch_tables("book")[0] == f"{DEV}.pivot"
    assert "name:" not in checklist(started, "pivot").split("## Notes")[0]
    reference = (started / "references" / f"{DEV}__pivot.py").read_text(encoding="utf-8")
    assert 'NAME = "pivot"  # for PivotTable1 of runs.xlsx' in reference


def test_answering_a_name_renames_the_table_and_its_total_levels(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    report = decide({f"{DEV}.pivot": {"name": "runs_by_job",
                                      "location": "/data/team/mart_dev.db/runs_by_job"}})
    assert f"Renamed {DEV}.pivot to {DEV}.runs_by_job: its Table folder is " in report
    assert f"Renamed {DEV}.pivot_grand_total to {DEV}.runs_by_job_grand_total" in report
    assert project.batch_tables("book") == [
        f"{DEV}.runs_by_job", f"{DEV}.runs_by_day", f"{DEV}.runs_by_job_grand_total",
        f"{DEV}.runs_by_day_grand_total"]
    assert not (started / "tables" / f"{DEV}__pivot").exists()
    assert not (started / "references" / f"{DEV}__pivot.py").exists()
    reference = (started / "references" / f"{DEV}__runs_by_job.py").read_text(encoding="utf-8")
    assert f'"{DEV}.runs_by_job"' in reference and 'location="/data/team/' in reference
    # Its notebook builds and runs under its new name, its answers and Pivot filter kept.
    assert run_query(project.load(f"{DEV}.runs_by_job").preview(), example_database.query
                     ) is not None
    assert "INSERT OVERWRITE TABLE mart_dev.runs_by_job" in to_hive(
        project.load(f"{DEV}.runs_by_job").write())
    kept = pivot_filters_of_batch(started, "book")
    assert kept[f"{DEV}.runs_by_job"][0].final == f"{DEV}.runs_by_job"
    origins = workbook_conversion.final_origins_of_batch(started, "book")
    assert origins[f"{DEV}.runs_by_job"] == FinalOrigin("runs.xlsx", "PivotTable1")
    assert (batch_folder(started) / "scripts" / "runs_by_job.hql").is_file()
    assert f"{DEV}.pivot," not in (batch_folder(started) / "batch.md").read_text(
        encoding="utf-8")
    assert "name:" not in checklist(started, "runs_by_job").split("## Notes")[0]


def test_converting_again_keeps_the_name_answered(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({f"{DEV}.pivot": {"name": "runs_by_job"}})
    converted(started, books, "slicer")
    assert project.batch_tables("book")[0] == f"{DEV}.runs_by_job"
    assert not (started / "tables" / f"{DEV}__pivot").exists()


def test_a_table_renamed_is_placed_in_its_own_folder_under_the_location_root(
        started: Path, books: dict[str, bytes]) -> None:
    """A location placed under DEV's location_root moves with the name; the old name's folder
    would be another table's, the one it was converted as."""
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(
        '"<DEV_LOCATION_ROOT>"', '"/data/team/dev"'), encoding="utf-8")
    converted(started, books, "slicer")
    decide({f"{DEV}.pivot": {"name": "runs_by_job"}})
    reference = (started / "references" / f"{DEV}__runs_by_job.py").read_text(encoding="utf-8")
    assert f'    location="/data/team/dev/{DEV}.db/runs_by_job",  # under its' in reference
    assert project.load(f"{DEV}.runs_by_job") is not None


def test_answering_a_name_again_renames_it_again(started: Path,
                                                 books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({f"{DEV}.pivot": {"name": "runs_by_job"}})
    decide({f"{DEV}.runs_by_job": {"name": "job_minutes"}})
    assert project.batch_tables("book")[0] == f"{DEV}.job_minutes"


@pytest.mark.parametrize(("name", "why"), [
    ("Runs By Job", "give a plain lowercase name"),
    ("runs_by_day", "mart_dev.runs_by_day has a Table reference already"),
])
def test_a_name_that_cant_be_given_is_refused_and_nothing_written(
        started: Path, books: dict[str, bytes], name: str, why: str) -> None:
    converted(started, books, "slicer")
    with pytest.raises(ValueError, match=why):
        decide({f"{DEV}.pivot": {"name": name}})
    assert (started / "tables" / f"{DEV}__pivot").is_dir()


def test_a_table_created_in_dev_keeps_its_name(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({f"{DEV}.pivot": {"location": "/data/team/mart_dev.db/pivot"}})
    run_execute(project.load(f"{DEV}.pivot").create(), example_database.execute)
    with pytest.raises(ValueError, match="is created in dev already"):
        decide({f"{DEV}.pivot": {"name": "runs_by_job"}})


def test_a_table_with_no_name_to_decide_refuses_a_name(started: Path,
                                                       books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    with pytest.raises(ValueError, match="has no name to decide"):
        decide({f"{DEV}.runs_by_day": {"name": "day_runs"}})


def test_a_final_named_as_a_table_it_reads_is_proposed_a_report(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "total_row")
    assert ("Its name, job_runs_report, is proposed: job_runs is the name of a table in the "
            "database it reads") in checklist(started, "job_runs_report")
    decide({f"{DEV}.job_runs_report": {"name": "run_hours"}})
    assert project.batch_tables("book") == [f"{DEV}.run_hours", f"{DEV}.run_hours_total_row"]


# --- A range's database table, a Decision --------------------------------------------------


def test_a_pivot_over_a_range_reads_the_table_proposed_for_its_sheet(
        started: Path, books: dict[str, bytes]) -> None:
    report = converted(started, books, "range")
    assert project.batch_tables("book") == [f"{DEV}.pivot"]
    assert ("Wrote references/ops__runs.py from the cells a PivotTable reads, each type a "
            "guess") in report
    notes = checklist(started, "pivot")
    assert ("- sources: ops.runs, proposed as the database table Runs!A1:F10 samples: keep it "
            'with "proposed", or answer the table it samples') in notes
    assert '"sources": {\n            "ops.runs": "proposed",' in report


def test_answering_a_ranges_table_points_the_logic_at_it(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "range")
    project.add_references("ops.job_runs", query=example_database.query)
    report = decide({f"{DEV}.pivot": {"sources": {"ops.runs": "ops.job_runs"}}})
    assert (f"{DEV}.pivot: its logic reads ops.job_runs now, in place of ops.runs") in report
    assert "sources:" not in checklist(started, "pivot").split("## Notes")[0]
    hive = to_hive(project.load(f"{DEV}.pivot").preview())
    assert "ops.job_runs" in hive and "ops.runs" not in hive
    assert run_query(project.load(f"{DEV}.pivot").preview(), example_database.query
                     ) is not None


def test_a_ranges_table_answered_needs_its_table_reference(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "range")
    with pytest.raises(ValueError, match="ops.region_runs has no Table reference"):
        decide({f"{DEV}.pivot": {"sources": {"ops.region_runs": "x", "ops.runs":
                                             "ops.region_runs"}}})


# --- The Pivot filter record, from either path ---------------------------------------------


def test_a_workbooks_pivot_filter_is_recorded_for_its_table(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    kept = pivot_filters_of_batch(started, "book")
    every = ("FAILED", "SUCCESS", "TEST", None)
    assert kept[f"{DEV}.pivot"] == [ConvertedPivotFilter(
        f"{DEV}.pivot", SLICER, "status", ("FAILED", "SUCCESS"), every)]
    assert set(kept) == {f"{DEV}.{name}" for name in TABLES["slicer"]}
    record = json.loads((batch_folder(started) / "written.json").read_text(encoding="utf-8"))
    assert record["pivot_filters"][f"{DEV}.runs_by_day"][0]["kind"] == SLICER


def test_a_kept_pivot_filter_reads_back_as_the_workbook_gave_it_its_days_as_dates(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "timeline")
    given_by_the_workbook = [dataclasses.replace(each, final=f"{DEV}.pivot")
                             for each in pivot_filters(read_workbook(books["timeline"]))]
    kept = pivot_filters_of_batch(started, "book")[f"{DEV}.pivot"]
    assert kept == given_by_the_workbook
    assert [each.kind for each in kept] == [HIDDEN_ITEMS, TIMELINE]


def test_a_copilot_scripts_pivot_filter_gives_the_record_the_workbook_does(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    (book,) = pivot_filters_of_batch(started, "book")[f"{DEV}.pivot"]
    # The query alone in a batch of one script is named for the batch.
    (started / "copilot.hql").write_text(COPILOT_PIVOT, encoding="utf-8")
    project.convert("pivot", files=["copilot.hql"], query=example_database.query,
                    database="ops", overwrite=True)
    (copilot,) = pivot_filters_of_batch(started, "pivot")[f"{DEV}.pivot"]
    # Hive alone holds no pivot cache: every value the field takes is the workbook's alone.
    assert copilot == dataclasses.replace(book, field_values=())
    assert ("Pivot filter: slicer status, FAILED and SUCCESS kept, as its Hive marks it: a "
            "Decision of its table.") in checklist(started, "pivot")


def test_a_copilot_script_beside_its_workbook_stands_for_its_final(
        started: Path, books: dict[str, bytes]) -> None:
    (started / "pivot.hql").write_text(COPILOT_PIVOT, encoding="utf-8")
    report = repr(project.convert("book", files=["pivot.hql", given(started, books, "slicer")],
                                  query=example_database.query, database="ops"))
    assert ("pivot.hql is PivotTable1 of runs.xlsx's Hive, as Copilot writes it: it is "
            "converted in place of the workbook's own.") in report
    (copilot,) = pivot_filters_of_batch(started, "book")[f"{DEV}.pivot"]
    # Every value its field takes is the workbook's, as the batch holds the workbook.
    assert copilot.field_values == ("FAILED", "SUCCESS", "TEST", None)
    assert workbook_conversion.final_origins_of_batch(started, "book")[f"{DEV}.pivot"] == (
        FinalOrigin("runs.xlsx", "PivotTable1"))
    assert not (batch_folder(started) / "scripts" / "pivot.hql").exists()


@pytest.mark.parametrize("fixture", ["05_pivot_slicer_two_pivots", "08_pivot_timeline_filters",
                                     "10_pivot_calculated_item_rank"])
def test_the_code_paths_hive_gives_back_each_pivot_filter_of_its_workbook(fixture: str) -> None:
    book = read_workbook(FIXTURES / f"{fixture}.xlsx")
    texts = hive_texts(workbook_hive(book, database="ops"))
    for pivot_filter in pivot_filters(book):
        read = pivot_filters_in(texts[pivot_filter.final], pivot_filter.final)
        assert dataclasses.replace(pivot_filter, field_values=()) in read


def test_a_value_filters_record_from_the_code_paths_hive(books: dict[str, bytes]) -> None:
    book = read_workbook(books["top"])
    (top,) = pivot_filters(book)
    text = hive_texts(workbook_hive(book, database="ops"))["PivotTable1"]
    assert pivot_filters_in(text, "PivotTable1") == [dataclasses.replace(top, field_values=())]
    assert top.kind == TOP_FILTER and top.ranked_by == "Sum of duration_mins"


@pytest.mark.parametrize(("where", "expected"), [
    ("-- Pivot filter: Report filter status\nstatus = 'SUCCESS'",
     ConvertedPivotFilter("t", REPORT_FILTER, "status", ("SUCCESS",), ())),
    ("-- Pivot filter: hidden items status\n(status IS NULL OR status <> 'TEST')",
     ConvertedPivotFilter("t", HIDDEN_ITEMS, "status", ("TEST",), ())),
    ("-- Pivot filter: hidden items job_id\nNOT job_id IN (3, 4)",
     ConvertedPivotFilter("t", HIDDEN_ITEMS, "job_id", (3, 4), ())),
    ("-- Pivot filter: Timeline dt\ndt BETWEEN '2026-09-23' AND '2026-09-24'",
     ConvertedPivotFilter("t", TIMELINE, "dt", (datetime.datetime(2026, 9, 23),
                                               datetime.datetime(2026, 9, 24)), ())),
    ("-- Pivot filter: value filter job_id\njob_id IN (SELECT job_id FROM (SELECT job_id, "
     "RANK() OVER (ORDER BY SUM(duration_mins) ASC) AS item_rank FROM ops.job_runs GROUP BY "
     "job_id) AS ranked WHERE item_rank <= 1)",
     ConvertedPivotFilter("t", TOP_FILTER, "job_id", (1,), (), "Sum of duration_mins", True)),
])
def test_a_mark_above_a_condition_is_read_as_its_kind_of_pivot_filter(
        where: str, expected: ConvertedPivotFilter) -> None:
    text = f"SELECT job_id, COUNT(*) AS runs FROM ops.job_runs\nWHERE\n{where}\nGROUP BY job_id"
    assert pivot_filters_in(text, "t") == [expected]


def test_each_mark_above_a_condition_joined_by_and_is_read_for_its_own() -> None:
    text = ("SELECT job_id FROM ops.job_runs\nWHERE\n"
            "  -- Pivot filter: slicer status\n  status IN ('FAILED', 'SUCCESS')\n"
            "  -- Pivot filter: Report filter dt\n  AND dt = '2026-09-24'\n"
            "  AND\n  -- Pivot filter: hidden items job_id\n  job_id <> 3")
    assert pivot_filters_in(text, "t") == [
        ConvertedPivotFilter("t", SLICER, "status", ("FAILED", "SUCCESS"), ()),
        ConvertedPivotFilter("t", REPORT_FILTER, "dt", ("2026-09-24",), ()),
        ConvertedPivotFilter("t", HIDDEN_ITEMS, "job_id", (3,), ())]


def test_hive_with_no_mark_has_no_pivot_filter() -> None:
    assert pivot_filters_in("SELECT 1 AS x FROM ops.jobs WHERE job_id = 1", "t") == []


# --- What the convert Workflow's notebook says ---------------------------------------------


def test_the_convert_notebook_says_files_takes_a_workbook() -> None:
    inputs = {each.name: each for each in CONVERT.inputs}
    assert '["runs.xlsx"]' in inputs["FILES"].about
    assert "never a workbook, which you name here" in inputs["FILES"].about
    assert "workbook" not in inputs["RENAME"].about


# --- Refusals ------------------------------------------------------------------------------


def test_a_workbook_whose_pieces_read_each_other_in_a_loop_is_refused(started: Path) -> None:
    shutil.copy(FIXTURES / "03_loop.xlsx", started / "runs.xlsx")
    with pytest.raises(ValueError) as refused:
        project.convert("book", files=["runs.xlsx"], query=example_database.query)
    message = str(refused.value)
    assert "runs.xlsx: Its pieces read each other in a loop: Power Query \"back\"" in message
    assert "Why it matters: each piece must come after every piece it reads" in message
    assert "Usual fix:      in Excel, break one of these links" in message
    assert not batch_folder(started).exists()


def test_a_workbook_with_nothing_to_convert_is_refused(started: Path,
                                                       books: dict[str, bytes]) -> None:
    with pytest.raises(ValueError, match="runs.xlsx holds nothing to convert"):
        converted(started, books, "sources_alone")


def test_a_workbook_each_final_of_which_holds_a_name_to_fill_in_is_refused(
        started: Path, books: dict[str, bytes]) -> None:
    with pytest.raises(ValueError, match=r"holds a name to fill in: run_hours of runs.xlsx "
                                         r"\(<hours_run>\)"):
        converted(started, books, "unplain")


def test_a_final_holding_a_name_to_fill_in_beside_others_is_skipped_and_kept(
        started: Path, books: dict[str, bytes]) -> None:
    given(started, books, "unplain", "unplain.xlsx")
    report = repr(project.convert("book", files=[given(started, books, "formulas"),
                                                 "unplain.xlsx"],
                                  query=example_database.query, database="ops"))
    assert ("Skipped, each with why: run_hours of unplain.xlsx (its Hive holds <hours_run>"
            in report)
    kept = batch_folder(started) / "scripts" / "run_hours_report.hql"
    assert "<hours_run>" in kept.read_text(encoding="utf-8")


def test_an_xls_is_refused(started: Path) -> None:
    (started / "runs.xls").write_bytes(b"old")
    with pytest.raises(ValueError, match="an .xls, Excel's older kind of workbook"):
        project.convert("book", files=["runs.xls"], query=example_database.query)


def test_a_file_named_xlsx_that_isnt_a_workbook_is_refused(started: Path) -> None:
    (started / "runs.xlsx").write_text("SELECT 1", encoding="utf-8")
    with pytest.raises(ValueError, match="isn't a workbook Excel saved"):
        project.convert("book", files=["runs.xlsx"], query=example_database.query)


def test_a_workbook_that_isnt_there_is_refused_with_a_workbooks_example(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match=r'such as files=\["runs.xlsx"\]'):
        project.convert("book", files=["runs.xlsx"], query=example_database.query)


def test_two_workbooks_finals_of_one_name_are_refused(
        started: Path, books: dict[str, bytes]) -> None:
    files = [given(started, books, "formulas"), given(started, books, "formulas", "two.xlsx")]
    with pytest.raises(ValueError, match="a final of another workbook of the batch is named "
                                         "job_runs_report too"):
        project.convert("book", files=files, query=example_database.query, database="ops")
