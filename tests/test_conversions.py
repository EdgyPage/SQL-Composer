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
    assert 'HIVE = """' in code and "project.scan_hive(HIVE, database=DATABASE)" in code
    assert '# project.convert("your_name", HIVE, query=query, database=DATABASE)' in code
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
    # dt is one of the table's columns, though the query doesn't give it, so Table takes it.
    assert '"dt": "string",  # the original\'s partition column' in reference
    cells = json.loads((started / "tables" / "mart__runs" / "mart__runs.ipynb")
                       .read_text(encoding="utf-8"))["cells"]
    logic = next("".join(cell["source"]) for cell in cells
                 if "".join(cell["source"]).startswith("# logic"))
    assert 'return statement(INSERT_OVERWRITE(runs, partition={"dt": "2026-09-24"}), *rows())' \
        in logic


@pytest.mark.needs_example_database
def test_a_static_partitions_row_compare_reads_every_partition(started: Path) -> None:
    """Its query gives no dt, so the hint can't keep one Partition by it."""
    hive = ("INSERT OVERWRITE TABLE theirs.x PARTITION (dt='2026-09-24') "
            "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'")
    project.convert("runs", hive, query=example_database.query, database="ops")
    notebook = started / "admin" / "conversions" / "runs" / "runs.ipynb"
    code = "".join("".join(cell["source"]) for cell in
                   json.loads(notebook.read_text(encoding="utf-8"))["cells"])
    assert "reads_all_partitions=True))" in code and 'partition={"dt"' not in code


@pytest.mark.needs_example_database
def test_a_conversion_kept_whole_as_hive_is_refused_before_anything_is_made(
        started: Path) -> None:
    project.convert("kept", "SELECT j.job_id FROM ops.jobs j", query=example_database.query,
                    database="ops")
    notebook = started / "admin" / "conversions" / "kept" / "kept.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))
    cells["cells"][2]["source"] = ["# logic\n", "from sqlglot_composer import unchecked_hive\n",
                                   "\n", "def converted():\n",
                                   "    return unchecked_hive('SELECT job_id FROM ops.jobs')\n"]
    notebook.write_text(json.dumps(cells), encoding="utf-8")
    with pytest.raises(TypeError, match="not a Statement"):
        project.finish_conversion("kept", table="mart.kept")
    assert not (started / "tables" / "mart__kept").exists()
    assert not (started / "references" / "mart__kept.py").exists()


@pytest.mark.needs_example_database
def test_convert_says_each_count_plainly_and_each_opt_out(converted: Path,
                                                          started: Path) -> None:
    said = repr(project.convert("again", HIVE, query=example_database.query, database="ops"))
    assert "Converted again: 9 lines of Hive" in said
    assert ("0 pieces kept as Hive, 2 named constants, 1 opt-out marked # CONVERSION: for you "
            "to check: JOIN(j, many_matches=True).") in said
    one = repr(project.convert("one", "SELECT j.job_id FROM ops.jobs j",
                               query=example_database.query, database="ops"))
    assert one.startswith("Converted one: 1 line of Hive")


@pytest.mark.needs_example_database
def test_a_conversion_removed_is_archived(converted: Path, started: Path) -> None:
    said = repr(project.remove_conversion("job_outcomes"))
    assert said.startswith("Moved admin/conversions/job_outcomes/ to admin/removed/")
    assert not converted.exists()
    assert "Conversions not finished yet" not in repr(project.check())


# --- Shapes, round trip ---------------------------------------------------------------------------

# Hive written to break a Conversion, each converted in a started Project and its Statement
# compared with the original: the same query, once both are written out the same way.
SAME_QUERY = {
    "deep_ctes": """\
WITH a AS (SELECT r.job_id, r.status FROM ops.job_runs r WHERE r.dt = '2026-09-24'),
b AS (SELECT a.job_id, a.status FROM a WHERE a.status = 'FAILED'),
c AS (SELECT b.job_id, COUNT(*) AS n FROM b GROUP BY b.job_id)
SELECT c.job_id, c.n FROM c""",
    "cte_read_twice": """\
WITH a AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.dt = '2026-09-24')
SELECT x.job_id FROM a x JOIN a y ON x.job_id = y.job_id AND x.dt = y.dt""",
    "one_table_two_aliases": """\
SELECT r1.run_id, r2.run_id AS other FROM ops.job_runs r1
JOIN ops.job_runs r2 ON r1.job_id = r2.job_id AND r1.dt = r2.dt WHERE r1.dt = '2026-09-24'""",
    "quoted_names": "SELECT `j`.`job_id`, `j`.`team` AS `the team` FROM `ops`.`jobs` `j`",
    "comments": """\
-- top comment
SELECT j.job_id, /* inline */ j.team -- trailing
FROM ops.jobs j""",
    "mixed_case": "select J.Job_Id, j.TEAM from OPS.JOBS j Where j.Team = 'data'",
    "having": """\
SELECT r.job_id, COUNT(*) AS n FROM ops.job_runs r WHERE r.dt = '2026-09-24'
GROUP BY r.job_id HAVING COUNT(*) > 2""",
    "left_join": """\
SELECT j.job_id, r.status FROM ops.jobs j LEFT JOIN ops.job_runs r
ON j.job_id = r.job_id AND r.dt = '2026-09-24'""",
    "order_by_and_limit": "SELECT j.job_id FROM ops.jobs j ORDER BY j.job_id DESC LIMIT 10",
    "distinct": "SELECT DISTINCT j.team FROM ops.jobs j",
    "union_all": """\
SELECT j.job_id FROM ops.jobs j UNION ALL
SELECT r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'""",
    "rows_frame": """\
SELECT r.job_id, SUM(r.duration_mins) OVER (PARTITION BY r.job_id ORDER BY r.dt ASC
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS s FROM ops.job_runs r WHERE r.dt = '2026-09-24'""",
    "grouping_sets": """\
SELECT r.job_id, r.status, COUNT(*) AS n FROM ops.job_runs r WHERE r.dt = '2026-09-24'
GROUP BY r.job_id, r.status GROUPING SETS ((r.job_id), (r.status))""",
    "plain_values": "SELECT j.job_id, 1 AS one, 'x' AS tag, NULL AS nothing FROM ops.jobs j",
    "a_piece_kept_inside_a_case": """\
SELECT r.run_id,
  CASE
    WHEN r.status = 'FAILED' THEN regexp_replace(r.status, 'F', 'f')
    WHEN r.duration_mins > 5 THEN CAST(r.duration_mins AS STRING)
    ELSE 'x'
  END AS label
FROM ops.job_runs r WHERE r.dt = '2026-09-24'""",
    "hive_variable": "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '${hivevar:run_date}'",
    "in_sub_query_in_a_cte": """\
WITH a AS (SELECT r.run_id, r.job_id FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.job_id IN (SELECT j.job_id FROM ops.jobs j))
SELECT a.run_id FROM a""",
}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", list(SAME_QUERY))
def test_each_shape_converts_to_the_same_query(started: Path, name: str) -> None:
    project.convert(name, SAME_QUERY[name], query=example_database.query, database="ops")
    said = repr(compare_hive(project.load(name).converted(), SAME_QUERY[name]))
    assert said.startswith("The Statement's Hive and the original are the same query")


# Hive the Toolbox writes another way, each converted in a started Project: its Statement
# builds, and the scan says what changed.
WRITTEN_ANOTHER_WAY = {
    "select_star": ("SELECT * FROM ops.jobs",
                    "the * of jobs becomes its columns, job_id, job_name, team, region"),
    "star_in_a_cte": ("WITH a AS (SELECT j.* FROM ops.jobs j WHERE j.team = 'data')\n"
                      "SELECT a.job_id, a.team FROM a",
                      "the * of j becomes its columns, job_id, job_name, team, region"),
    "sub_query_in_from": ("SELECT s.job_id FROM (SELECT j.job_id FROM ops.jobs j) s",
                          "the sub-query s becomes a Derived table"),
    "with_rollup": ("SELECT r.job_id, r.status, COUNT(*) AS n FROM ops.job_runs r\n"
                    "WHERE r.dt = '2026-09-24' GROUP BY r.job_id, r.status WITH ROLLUP",
                    "becomes GROUP_BY(rollup(r.job_id, r.status))"),
    "cube": ("SELECT r.job_id, r.status, COUNT(*) AS n FROM ops.job_runs r\n"
             "WHERE r.dt = '2026-09-24' GROUP BY CUBE(r.job_id, r.status)",
             "becomes GROUP_BY(cube(r.job_id, r.status))"),
    "distribute_by": ("SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'\n"
                      "DISTRIBUTE BY r.job_id SORT BY r.run_id",
                      "line 2: DISTRIBUTE BY r.job_id is dropped"),
}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", list(WRITTEN_ANOTHER_WAY))
def test_each_shape_written_another_way_builds_and_says_how(started: Path, name: str) -> None:
    hive, said = WRITTEN_ANOTHER_WAY[name]
    project.convert(name, hive, query=example_database.query, database="ops")
    project.load(name).converted()
    scan = (started / "admin" / "conversions" / name / "scan.md").read_text(encoding="utf-8")
    assert said in scan
