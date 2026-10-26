"""Conversions: Hive someone else wrote, made the user's own code. Toolbox 7.2's tickets 05 to 07.

project.scan_hive says what a Conversion of the Hive would make, and changes nothing;
project.convert writes the Conversion folder, admin/conversions/<name>/, whose notebook's logic
builds the same query from the Toolbox's own functions, adding each opt-out a refusal names,
marked # CONVERSION:; project.finish_conversion makes it a Saved table's Table folder and Table
reference; project.remove_conversion archives one. They run here on the Example database.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import compare_hive, example_database, project, set_admin_log, to_hive

NOW = datetime.datetime(2026, 10, 26, 9, 30, 0)
project_files = toolbox_module("project_files")

# Hive as someone else wrote it: a CTE, aliases, a long IN list, a lookup CASE and a join.
HIVE = """\
WITH base AS (
  SELECT r.job_id, r.status, r.duration_mins
  FROM ops.job_runs r
  WHERE r.dt = '2026-09-24' AND r.status IN ('FAILED', 'SUCCESS', 'RETRY', 'TEST')
)
SELECT j.job_name,
       CASE b.status WHEN 'FAILED' THEN 'failed' WHEN 'SUCCESS' THEN 'passed' END AS outcome,
       b.duration_mins
FROM base b JOIN ops.jobs j ON b.job_id = j.job_id
"""


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


@pytest.fixture
def converted(started: Path) -> Path:
    project.convert("job_outcomes", HIVE, query=example_database.query, database="ops")
    return started / "admin" / "conversions" / "job_outcomes"


def files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


# --- start and the admin notebook -----------------------------------------------------------------


def test_start_makes_the_conversions_folder_and_its_notebook(started: Path) -> None:
    assert (started / "admin" / "conversions").is_dir()
    cells = json.loads((started / "admin" / "convert.ipynb").read_text(encoding="utf-8"))["cells"]
    code = "".join("".join(cell["source"]) for cell in cells)
    assert 'HIVE = """' in code and "project.scan_hive(HIVE)" in code
    assert '# project.finish_conversion("your_name", table="mart.your_table")' in code


# --- scan_hive ------------------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_a_scan_says_what_a_conversion_would_make_and_changes_nothing(started: Path) -> None:
    before = files(started)
    said = repr(project.scan_hive(HIVE, database="ops"))
    assert said.splitlines()[0] == "9 lines of Hive, one query reading ops.job_runs and ops.jobs."
    assert "No Table reference yet for ops.job_runs and ops.jobs" in said
    assert "line 4: the IN list of 4 values is the constant STATUS_VALUES" in said
    assert "the CASE on b.status is the constant OUTCOME_BY_STATUS" in said
    assert files(started) == before


def test_a_scan_reads_a_file(started: Path) -> None:
    (started / "report.hql").write_text(HIVE, encoding="utf-8")
    assert repr(project.scan_hive(file="report.hql", database="ops")).startswith("9 lines")


@pytest.mark.parametrize(("hive", "file", "said"), [
    (None, None, "was given no Hive"),
    (HIVE, "report.hql", "was given both the Hive and file="),
])
def test_the_hive_is_given_once(started: Path, hive: str | None, file: str | None,
                                said: str) -> None:
    with pytest.raises(ValueError, match=said):
        project.scan_hive(hive, file=file)


def test_hive_a_conversion_cant_take_is_refused_saying_what_to_do(started: Path) -> None:
    with pytest.raises(ValueError, match="a Conversion can't take this Hive: it holds 2 "
                       "statements"):
        project.scan_hive("SELECT 1 FROM ops.jobs; SELECT 2 FROM ops.jobs")


# --- convert ----------------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_convert_writes_the_conversion_folder(converted: Path, started: Path) -> None:
    assert files(converted) == ["job_outcomes.ipynb", "original.hql", "scan.md"]
    assert (converted / "original.hql").read_text(encoding="utf-8") == HIVE
    assert project_files.Registry(started).listed(project_files.CONVERSION_FOLDER,
                                                  "job_outcomes")
    assert (started / "references" / "ops__job_runs.py").is_file()
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert "- Call: `project.convert(\"job_outcomes\", ...)`" in log


@pytest.mark.needs_example_database
def test_the_conversion_gives_the_same_query_as_the_original(converted: Path) -> None:
    statement = project.load("job_outcomes").converted()
    assert compare_hive(statement, HIVE).ok
    assert "WITH base AS" in to_hive(statement)


@pytest.mark.needs_example_database
def test_the_opt_outs_the_original_took_are_added_and_marked(converted: Path) -> None:
    """ops.jobs's Table reference has no Key yet, so the join may repeat rows: the original
    took that chance, so the Conversion takes it too, marked for you to decide."""
    scan = (converted / "scan.md").read_text(encoding="utf-8")
    assert "Opt-out added, marked # CONVERSION: at its line: JOIN(j, many_matches=True)" in scan
    said = repr(project.check())
    assert "Marked by project.convert(...) for you to check" in said
    assert "# CONVERSION: many_matches=True, as the original did; check it" in said
    assert "Conversions not finished yet" in said and "admin/conversions/job_outcomes/" in said


@pytest.mark.needs_example_database
def test_convert_reads_a_file_and_keeps_it_as_given(started: Path) -> None:
    (started / "report.hql").write_text(HIVE, encoding="utf-8")
    project.convert("from_file", file="report.hql", query=example_database.query,
                    database="ops")
    kept = started / "admin" / "conversions" / "from_file" / "original.hql"
    assert kept.read_text(encoding="utf-8") == HIVE


@pytest.mark.needs_example_database
def test_a_name_taken_is_refused(converted: Path) -> None:
    with pytest.raises(FileExistsError):
        project.convert("job_outcomes", HIVE, query=example_database.query, database="ops")


@pytest.mark.parametrize("name", ["Team", "team-runs", "mart.team", "class", "", 5])
def test_a_name_that_isnt_plain_is_refused(started: Path, name: object) -> None:
    with pytest.raises(ValueError, match="isn't a plain lowercase name"):
        project.convert(name, HIVE, query=example_database.query, database="ops")


def test_a_table_with_no_reference_needs_your_query(started: Path) -> None:
    with pytest.raises(TypeError, match="query"):
        project.convert("job_outcomes", HIVE, database="ops")
    assert not (started / "admin" / "conversions" / "job_outcomes").exists()


# --- finish_conversion and remove_conversion ------------------------------------------------------


@pytest.mark.needs_example_database
def test_finishing_makes_the_saved_tables_folder_and_reference(converted: Path,
                                                               started: Path) -> None:
    said = repr(project.finish_conversion("job_outcomes", table="mart.job_outcomes"))
    assert said.startswith("Finished the Conversion job_outcomes as mart.job_outcomes")
    folder = started / "tables" / "mart__job_outcomes"
    assert sorted(path.name for path in folder.iterdir()) == [
        "lineage", "mart__job_outcomes.ipynb", "original.hql"]
    reference = (started / "references" / "mart__job_outcomes.py").read_text(encoding="utf-8")
    assert '"job_name": "string",' in reference
    assert '"outcome": <COLUMN_TYPE>,' in reference
    assert 'partitioned_by=["<PARTITION_COLUMN>"],  # name one of its columns' in reference
    assert "location=<LOCATION>," in reference
    assert not converted.exists()
    assert "job_outcomes" not in project_files.Registry(started).in_force(
        project_files.CONVERSION_FOLDER)


@pytest.mark.needs_example_database
def test_the_finished_tables_write_inserts_the_converted_rows(converted: Path,
                                                               started: Path) -> None:
    project.finish_conversion("job_outcomes", table="mart.job_outcomes")
    reference = started / "references" / "mart__job_outcomes.py"
    reference.write_text(reference.read_text(encoding="utf-8")
                         .replace("<COLUMN_TYPE>", '"string"')
                         .replace('["<PARTITION_COLUMN>"]', "[]")
                         .replace("<LOCATION>", '"/data/mart.db/job_outcomes"'),
                         encoding="utf-8")
    write = to_hive(project.load("mart.job_outcomes").write())
    assert write.splitlines()[0] == "WITH base AS ("
    assert "INSERT OVERWRITE TABLE mart.job_outcomes" in write


@pytest.mark.needs_example_database
def test_a_partition_the_original_wrote_is_carried_over(started: Path) -> None:
    hive = ("INSERT OVERWRITE TABLE theirs.x PARTITION (dt='2026-09-24') "
            "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'")
    project.convert("runs", hive, query=example_database.query, database="ops")
    project.finish_conversion("runs", table="mart.runs")
    reference = (started / "references" / "mart__runs.py").read_text(encoding="utf-8")
    assert 'partitioned_by=["dt"],  # filled in from the original\'s PARTITION(...)' in reference
    cells = json.loads((started / "tables" / "mart__runs" / "mart__runs.ipynb")
                       .read_text(encoding="utf-8"))["cells"]
    logic = next("".join(cell["source"]) for cell in cells
                 if "".join(cell["source"]).startswith("# logic"))
    assert 'return statement(INSERT_OVERWRITE(runs, partition={"dt": "2026-09-24"}), *rows())' \
        in logic


@pytest.mark.needs_example_database
def test_a_conversion_removed_is_archived(converted: Path, started: Path) -> None:
    said = repr(project.remove_conversion("job_outcomes"))
    assert said.startswith("Moved admin/conversions/job_outcomes/ to admin/removed/")
    assert not converted.exists()
    assert "Conversions not finished yet" not in repr(project.check())
