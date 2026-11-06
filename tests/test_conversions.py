"""Conversions: Hive someone else wrote, made the user's own code. Toolbox 7.2's tickets 05
to 07, and 8.0's 14, which makes one query a batch of one.

project.scan_hive says what a Conversion of the Hive would make, and changes nothing;
project.convert writes a Saved table in the Dev Database, mart_dev.<name> for one query alone,
whose notebook's logic builds the same query from the Toolbox's own functions, adding each
opt-out a refusal names, marked # CONVERSION:, and its Table folder's conversion/ keeps the
statement, the scan and a checklist; project.remove_conversion archives the batch's folder.
They run here on the Example database. Batches of several scripts are tests/test_batches.py's.
"""

from __future__ import annotations

import datetime
import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

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
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    # Left off Python's path afterwards with its modules, which a convert puts there.
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    yield tmp_path
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


@pytest.fixture
def converted(started: Path) -> Path:
    """The Table folder of the Conversion of HIVE, one query alone: mart_dev.job_outcomes."""
    project.convert("job_outcomes", HIVE, query=example_database.query, database="ops")
    return started / "tables" / "mart_dev__job_outcomes"


def conversion_file(root: Path, name: str, file: str) -> str:
    """A file of a one-query Conversion's conversion/ folder, in mart_dev.<name>'s Table
    folder."""
    return (root / "tables" / f"mart_dev__{name}" / "conversion" / file).read_text(
        encoding="utf-8")


def files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*")
                  if path.is_file())


# --- start and the admin notebook -------------------------------------------------------------


def test_start_makes_the_convert_workflows_notebook(started: Path) -> None:
    assert not (started / "admin" / "conversions").exists()
    cells = json.loads((started / "admin" / "workflows" / "convert" / "convert.ipynb")
                       .read_text(encoding="utf-8"))["cells"]
    code = "".join("".join(cell["source"]) for cell in cells)
    # Toolbox 8.0: the calls read the names cell; no finish_conversion is left to call.
    assert "NAME = ''" in code and "FILES = []" in code and "HIVE = None" in code
    assert "project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE," in code
    assert "staging=STAGING)" in code
    assert "finish_conversion" not in code


# --- scan_hive --------------------------------------------------------------------------------


def test_a_scan_says_what_a_conversion_would_make_and_changes_nothing(started: Path) -> None:
    before = files(started)
    said = repr(project.scan_hive(HIVE, database="ops"))
    assert (said.splitlines()[0]
            == "9 lines of Hive, one query reading ops.job_runs and ops.jobs.")
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


@pytest.mark.parametrize(("written", "operator"), [
    ("IF(AND(r.status <> 'TEST', r.dt <> '2026-09-23'), 1, 0)", "a AND b"),
    ("IF(OR(r.status = 'FAILED', r.status IS NULL), 1, 0)", "a OR b")])
def test_hive_sqlglot_cant_read_is_refused_naming_its_line_and_an_excel_function(
        started: Path, written: str, operator: str) -> None:
    hive = f"SELECT r.run_id,\n  {written} AS kept\nFROM ops.job_runs r"
    with pytest.raises(ValueError) as refused:
        project.convert("kept", hive, query=example_database.query, database="ops")
    said = str(refused.value)
    # sqlglot's line, from the Hive's first; no file named, as the Hive was given as text.
    assert "can't read its Hive (" in said and "line 2, Col:" in said and operator in said
    assert "writes no table" not in said and "hive.hql" not in said


def test_other_hive_sqlglot_cant_read_is_refused_without_the_excel_advice(
        started: Path) -> None:
    # Hive's own x AND (y OR z) is no Excel AND(...): the fix says to correct the Hive.
    hive = ("SELECT r.run_id FROM ops.job_runs r\nWHERE r.dt = '2026-09-24' AND (r.status = "
            "'FAILED' OR r.job_id IN (1,")
    with pytest.raises(ValueError) as refused:
        project.convert("broken", hive, query=example_database.query, database="ops")
    said = str(refused.value)
    assert "sqlglot can't read its Hive (" in said and "line 2, Col:" in said
    assert "Correct the Hive there" in said and "no AND() or OR() function" not in said


def test_convert_makes_one_query_a_saved_table_in_dev(converted: Path, started: Path) -> None:
    assert files(converted) == [
        "conversion/checklist.md", "conversion/in_dev.hql", "conversion/scan.md",
        "conversion/statement.hql", "mart_dev__job_outcomes.ipynb"]
    assert conversion_file(started, "job_outcomes", "statement.hql") == HIVE.strip() + ";\n"
    assert project_files.Registry(started).listed(project_files.CONVERSION_FOLDER,
                                                  "job_outcomes")
    assert (started / "references" / "ops__job_runs.py").is_file()
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert "- Call: `project.convert(\"job_outcomes\", ...)`" in log


def test_the_conversion_gives_the_same_query_as_the_original(converted: Path) -> None:
    statement = project.load("mart_dev.job_outcomes").preview()
    assert compare_hive(statement, HIVE).ok
    assert "WITH base AS" in to_hive(statement)


def test_the_opt_outs_the_original_took_are_added_and_marked(converted: Path,
                                                             started: Path) -> None:
    """ops.jobs's Table reference has no Key yet, so the join may repeat rows: the original
    took that chance, so the Conversion takes it too, marked for you to decide."""
    scan = conversion_file(started, "job_outcomes", "scan.md")
    assert "Opt-out added, marked # CONVERSION: at its line: JOIN(j, many_matches=True)" in scan
    checklist = conversion_file(started, "job_outcomes", "checklist.md")
    assert ("- JOIN(j, many_matches=True), in the logic cell, keeps what the original did, as "
            "its `# CONVERSION:` mark says") in checklist
    said = repr(project.check())
    assert "Noted by project.convert(...), which blocks nothing" in said
    assert "# CONVERSION: many_matches=True, as the original did; check it" in said


# The original reads ops.job_runs three times, filtering none of its Partitions: the
# Conversion adds reads_all_partitions=True to each read, as the original took that chance.
READS_THRICE = """\
WITH fails AS (SELECT job_id, COUNT(*) AS n FROM ops.job_runs WHERE status = 'FAILED'
               GROUP BY job_id),
     retries AS (SELECT job_id, COUNT(*) AS n FROM ops.job_runs WHERE status = 'RETRY'
                 GROUP BY job_id)
SELECT a.job_id, f.n AS fails, r.n AS retries
FROM ops.job_runs a
LEFT JOIN fails f ON a.job_id = f.job_id
LEFT JOIN retries r ON a.job_id = r.job_id
"""


def test_a_checklist_note_says_what_the_toolbox_refused_beside_its_opt_out(
        started: Path) -> None:
    # Toolbox 8.2, 23: W3-1 and E1-3 saw the note say only that the mark keeps what the
    # original did, not what the Toolbox would have refused without it.
    project.convert("thrice", READS_THRICE, query=example_database.query, database="ops")
    checklist = conversion_file(started, "thrice", "checklist.md")
    assert ("- FROM(job_runs, reads_all_partitions=True), in the logic cell, keeps what the "
            "original did, as its `# CONVERSION:` mark says until you delete it. Without "
            "reads_all_partitions=True the Toolbox refuses the logic, saying: FROM(job_runs) "
            "reads ops.job_runs, but filters none of its partition columns: dt. If you want "
            "to, change what made it needed, such as a WHERE on the partition column, then "
            "take the opt-out off; the compare step checks the rows either way.") in checklist


def test_batch_md_and_the_checklist_say_each_note_once(started: Path) -> None:
    # Toolbox 8.2, 23: a run saw one note three times, for a query reading one table thrice.
    project.convert("thrice", READS_THRICE, query=example_database.query, database="ops")
    checklist = conversion_file(started, "thrice", "checklist.md")
    assert checklist.count("- FROM(job_runs, reads_all_partitions=True), in the logic") == 1
    batch = (started / "admin" / "workflows" / "convert" / "thrice" / "batch.md").read_text(
        encoding="utf-8")
    assert batch.count("# CONVERSION: FROM(job_runs, reads_all_partitions=True)") == 1
    # Each mark in the logic cell is still listed by check(), at its own line.
    said = repr(project.check())
    assert said.count("# CONVERSION: reads_all_partitions=True, as the original did") >= 2


def test_check_gives_the_next_step_before_the_conversion_notes(started: Path) -> None:
    # Toolbox 8.2, 23: the notes came first, and read as a blocker.
    project.convert("thrice", READS_THRICE, query=example_database.query, database="ops")
    said = repr(project.check())
    next_step = said.index("The next step of each Workflow you have started")
    assert next_step < said.index("Noted by project.convert(...), which blocks nothing")


def test_convert_reads_a_file_where_it_is(started: Path) -> None:
    # Toolbox 8.5, ticket 03: never copied, batch.md naming where it is.
    (started / "report.hql").write_text(HIVE, encoding="utf-8")
    project.convert("from_file", file="report.hql", query=example_database.query,
                    database="ops")
    batch = started / "admin" / "workflows" / "convert" / "from_file"
    assert "1 script, each read where it is: report.hql." in (batch / "batch.md").read_text(
        encoding="utf-8")
    assert not (batch / "scripts").exists()


@pytest.mark.parametrize("name", ["Team", "team-runs", "mart.team", "class", "", 5])
def test_a_name_that_isnt_plain_is_refused(started: Path, name: object) -> None:
    with pytest.raises(ValueError, match="isn't a plain lowercase name"):
        project.convert(name, HIVE, query=example_database.query, database="ops")


def test_a_table_with_no_reference_needs_your_query(started: Path) -> None:
    with pytest.raises(TypeError, match="query"):
        project.convert("job_outcomes", HIVE, database="ops")
    assert not (started / "tables" / "mart_dev__job_outcomes").exists()


# --- The Saved table it makes -----------------------------------------------------------------


def test_its_table_reference_has_the_types_the_query_knows(converted: Path,
                                                           started: Path) -> None:
    reference = (started / "references" / "mart_dev__job_outcomes.py").read_text(
        encoding="utf-8")
    # A CASE of text values is a string, as Hive gives it (8.2's ticket 08): nothing to guess.
    assert '"outcome": "string",\n' in reference
    assert "<" not in reference.split("# --- Aliases")[0]
    checklist = conversion_file(started, "job_outcomes", "checklist.md")
    assert "- types:" not in checklist
    assert "- location: the folder its files go in" in checklist


def test_its_write_inserts_the_converted_rows(converted: Path, started: Path) -> None:
    # write() takes only a Saved table with its location=, the checklist's box for it.
    reference = started / "references" / "mart_dev__job_outcomes.py"
    lines = reference.read_text(encoding="utf-8").splitlines()
    lines = ['    location="/data/mart_dev.db/job_outcomes",' if line.startswith(
        "    location=None") else line for line in lines]
    reference.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write = to_hive(project.load("mart_dev.job_outcomes").write())
    assert write.splitlines()[0] == "WITH base AS ("
    assert "INSERT OVERWRITE TABLE mart_dev.job_outcomes" in write


def test_a_partition_the_original_wrote_is_carried_over(started: Path) -> None:
    hive = ("INSERT OVERWRITE TABLE theirs.x PARTITION (dt='2026-09-24') "
            "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'")
    project.convert("runs", hive, query=example_database.query, database="ops")
    reference = (started / "references" / "mart_dev__x_theirs.py").read_text(encoding="utf-8")
    assert 'partitioned_by=["dt"],' in reference
    # dt is one of the table's columns, though the query doesn't give it, so Table takes it.
    assert '"dt": "string",' in reference
    cells = json.loads((started / "tables" / "mart_dev__x_theirs" / "mart_dev__x_theirs.ipynb")
                       .read_text(encoding="utf-8"))["cells"]
    logic = next("".join(cell["source"]) for cell in cells
                 if "".join(cell["source"]).startswith("# logic"))
    assert ('return statement(INSERT_OVERWRITE(x_theirs, partition={"dt": "2026-09-24"}), '
            "*rows())") in logic


def test_a_static_partitions_row_compare_reads_every_partition(started: Path) -> None:
    """Its query gives no dt, so the hint can't keep one Partition by it."""
    hive = ("INSERT OVERWRITE TABLE theirs.x PARTITION (dt='2026-09-24') "
            "SELECT run_id, status FROM ops.job_runs WHERE dt = '2026-09-24'")
    project.convert("runs", hive, query=example_database.query, database="ops")
    notebook = started / "tables" / "mart_dev__x_theirs" / "mart_dev__x_theirs.ipynb"
    code = "".join("".join(cell["source"]) for cell in
                   json.loads(notebook.read_text(encoding="utf-8"))["cells"])
    assert "reads_all_partitions=True))" in code
    assert "compare_with_original(preview(), ORIGINAL, query=query, partition=" not in code


def test_a_conversion_removed_is_archived_and_its_tables_stay(converted: Path,
                                                              started: Path) -> None:
    said = repr(project.remove_conversion("job_outcomes"))
    assert said.startswith("Moved admin/workflows/convert/job_outcomes/ to admin/removed/")
    assert converted.is_dir()


# --- Shapes, round trip -----------------------------------------------------------------------

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
    "union_all_three_of_one_table": """\
SELECT r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-23' UNION ALL
SELECT r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24' UNION ALL
SELECT r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-25'""",
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
    "hive_variable_in_an_unchecked_condition": """\
SELECT r.run_id FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status RLIKE concat('^', ${hivevar:prefix})""",
    "in_sub_query_in_a_cte": """\
WITH a AS (SELECT r.run_id, r.job_id FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.job_id IN (SELECT j.job_id FROM ops.jobs j))
SELECT a.run_id FROM a""",
}


@pytest.mark.parametrize("name", list(SAME_QUERY))
def test_each_shape_converts_to_the_same_query(started: Path, name: str) -> None:
    project.convert(f"shape_{name}", SAME_QUERY[name], query=example_database.query,
                    database="ops")
    said = repr(compare_hive(project.load(f"mart_dev.shape_{name}").preview(),
                             SAME_QUERY[name]))
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
                      "DISTRIBUTE BY r.job_id is dropped"),
    "a_count_written_as_a_sum": (
        "SELECT r.job_id, COALESCE(SUM(CASE WHEN r.status = 'FAILED' THEN 1 END), 0) AS f\n"
        "FROM ops.job_runs r WHERE r.dt = '2026-09-24' GROUP BY r.job_id",
        "SUM(CASE WHEN r.status = 'FAILED' THEN 1 END) becomes count_rows(where=...)"),
    "a_bare_sum_of_ones": (
        "SELECT r.job_id, SUM(CASE WHEN r.status = 'FAILED' THEN 1 END) AS f\n"
        "FROM ops.job_runs r WHERE r.dt = '2026-09-24' GROUP BY r.job_id",
        "it gives 0 where the SUM gave NULL"),
}


def logic_of(started: Path, table: str) -> str:
    """The text of a converted table's logic cell, as its notebook holds it."""
    notebook = started / "tables" / f"mart_dev__{table}" / f"mart_dev__{table}.ipynb"
    sources = ["".join(cell["source"])
               for cell in json.loads(notebook.read_text(encoding="utf-8"))["cells"]]
    return next(text for text in sources if text.startswith("# logic"))


def test_a_cte_of_rows_typed_in_keeps_its_key(started: Path) -> None:
    # Toolbox 8.2, 15: Copilot's team list as a CTE of typed-in rows, each team once, has its
    # Key, so the write keyed on team is let through with no opt-out.
    hive = """\
WITH team_names AS (SELECT 'data' AS team UNION ALL SELECT 'finance' UNION ALL SELECT 'web')
SELECT n.team, COUNT(r.run_id) AS runs FROM team_names n
LEFT JOIN ops.jobs j ON j.team = n.team
LEFT JOIN ops.job_runs r ON r.job_id = j.job_id AND r.dt = '2026-09-24'
GROUP BY n.team"""
    project.convert("teams", hive, query=example_database.query, database="ops")
    logic = logic_of(started, "teams")
    assert '}, key=["team"])' in logic
    assert "unproven_key" not in logic
    project.write_decisions({"mart_dev.teams": {"location": "/data/mart_dev/teams"}})
    forget_the_projects_modules()
    project.load("mart_dev.teams").write()


@pytest.mark.parametrize(("rows", "key"), [
    ("SELECT 'data' AS team, 'a' AS kind UNION ALL SELECT 'web', 'a'", '}, key=["team"])'),
    ("SELECT 'data' AS team, 'a' AS kind UNION ALL SELECT 'data', 'b'",
     '}, key=["team", "kind"])'),
    ("SELECT 'data' AS team, 'a' AS kind UNION ALL SELECT 'data', 'a'", None),
    ("SELECT 1 AS n, 'a' AS kind UNION ALL SELECT 1.0, 'a'", None),
])
def test_a_cte_of_rows_typed_in_has_the_key_its_rows_show(started: Path, rows: str,
                                                           key: str | None) -> None:
    # Toolbox 8.2, 15: the first column alone when it never repeats, else every column when
    # no row repeats, else none; 1 and 1.0 are one value, as Hive compares them.
    first = rows.split(" AS ")[1].split(",")[0]
    hive = f"WITH listed AS ({rows})\nSELECT l.{first}, l.kind FROM listed l"
    project.convert("typed", hive, query=example_database.query, database="ops")
    logic = logic_of(started, "typed")
    assert "unchecked_derived(" in logic
    if key is None:
        assert "}, key=[" not in logic
    else:
        assert key in logic


LISTED_JOBS = "(SELECT 1 AS job_id UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 99)"
MINUTES = ("(SELECT job_id, SUM(duration_mins) AS minutes FROM ops.job_runs "
           "WHERE dt = '2026-09-24' GROUP BY job_id)")


@pytest.mark.parametrize("hive", [
    f"SELECT c.job_id, COALESCE(m.minutes, 0) AS minutes\nFROM {LISTED_JOBS} c\n"
    f"LEFT JOIN {MINUTES} m ON c.job_id = m.job_id",
    f"SELECT c.job_id, COALESCE(m.minutes, 0) AS minutes\nFROM {MINUTES} m\n"
    f"JOIN {LISTED_JOBS} c ON c.job_id = m.job_id",
], ids=["in_from", "joined"])
def test_a_subquery_of_rows_typed_in_converts_as_a_cte_of_them_does(started: Path,
                                                                     hive: str) -> None:
    # Toolbox 8.2, 16: Copilot's job list as a subquery, in FROM or joined, stays Hive alone,
    # its column typed and its Key kept, and the query around it is Toolbox code giving the
    # original's rows.
    project.convert("listed", hive, query=example_database.query, database="ops")
    logic = logic_of(started, "listed")
    assert 'unchecked_derived("c", ' in logic
    assert '"job_id": "int",' in logic
    assert '}, key=["job_id"])' in logic
    assert "unchecked_hive(" not in logic
    converted = example_database.query(to_hive(project.load("mart_dev.listed").preview()))
    original = example_database.query(hive)
    assert sorted(map(tuple, converted.to_numpy().tolist())) == sorted(
        map(tuple, original.to_numpy().tolist()))


def test_a_column_of_rows_typed_in_whose_values_differ_in_type_is_left_untyped(
        started: Path) -> None:
    # Toolbox 8.2, 16: 1 and 2.5 are an int and a double, so the list says no type of its own.
    hive = ("SELECT l.n, l.team FROM (SELECT 1 AS n, 'data' AS team UNION ALL SELECT 2.5, "
            "'web') l")
    project.convert("mixed", hive, query=example_database.query, database="ops")
    logic = logic_of(started, "mixed")
    assert '"n": None,' in logic
    assert '"team": "string",' in logic


@pytest.mark.parametrize("pasted", [
    "\n\nSELECT r.job_id\nFROM ops.job_runs r\nWHERE r.dt = '2026-09-24'\n",
    "SELECT r.job_id\nFROM ops.job_runs r\nWHERE r.dt = '2026-09-24'",
    "SELECT r.job_id\nFROM ops.job_runs r\nWHERE r.dt = '2026-09-24'\n\n",
], ids=["after_a_line_break", "quotes_closed_on_its_last_line", "a_blank_line_after"])
def test_hive_pasted_any_way_is_kept_from_its_first_line_to_its_last(started: Path,
                                                                     pasted: str) -> None:
    # Toolbox 8.2, 18: HIVE = """ then a line break, as most people paste, gives Hive whose
    # first line is empty; the batch keeps it from its first line of Hive, as the person reads
    # it, so batch.md's line numbers are theirs, ending on one line break, as a file does.
    project.convert("pasted", pasted, query=example_database.query, database="ops")
    batch = started / "admin" / "workflows" / "convert" / "pasted"
    assert "hive.hql line 1, `SELECT r.job_id" in (batch / "batch.md").read_text(
        encoding="utf-8")
    assert (batch / "scripts" / "hive.hql").read_text(encoding="utf-8") == (
        "SELECT r.job_id\nFROM ops.job_runs r\nWHERE r.dt = '2026-09-24'\n")


def test_a_count_written_as_a_sum_gives_the_originals_rows(started: Path) -> None:
    # Toolbox 8.2, 10: inside COALESCE(..., 0), count_rows(where=...) gives what the SUM gave.
    hive = WRITTEN_ANOTHER_WAY["a_count_written_as_a_sum"][0]
    project.convert("counted", hive, query=example_database.query, database="ops")
    converted = example_database.query(to_hive(project.load("mart_dev.counted").preview()))
    original = example_database.query(hive)
    assert converted.sort_values("job_id").values.tolist() == (
        original.sort_values("job_id").values.tolist())
    assert "gives 0 where the SUM gave NULL" not in conversion_file(started, "counted",
                                                                     "scan.md")


@pytest.mark.parametrize("name", list(WRITTEN_ANOTHER_WAY))
def test_each_shape_written_another_way_builds_and_says_how(started: Path, name: str) -> None:
    hive, said = WRITTEN_ANOTHER_WAY[name]
    project.convert(f"shape_{name}", hive, query=example_database.query, database="ops")
    project.load(f"mart_dev.shape_{name}").preview()
    assert said in conversion_file(started, f"shape_{name}", "scan.md")


# --- Each SQL mapping, run --------------------------------------------------------------------

# One day of ops.job_runs, which each query below reads.
# Both days of ops.job_runs, which each query below reads: nine runs, one TEST, two FAILED,
# run 98's status NULL, and durations from 5 to 40, so each condition keeps some rows and not
# others, and a NULL under a NOT shows whether the conversion keeps what Hive keeps.
DAYS = "FROM ops.job_runs r WHERE r.dt BETWEEN '2026-09-23' AND '2026-09-24'"
# Hive a Conversion writes as Toolbox code, with no piece of it left Hive, each by what it
# maps: Toolbox 8.2, 17.
MAPPED = {
    "a_negative_number": f"SELECT r.run_id, r.duration_mins * -1 AS negated {DAYS}",
    "true_and_false": ("SELECT r.run_id, CASE WHEN r.status = 'FAILED' THEN TRUE ELSE FALSE "
                       f"END AS failed {DAYS}"),
    "null_in_a_case": ("SELECT r.run_id, CASE WHEN r.status = 'TEST' THEN NULL ELSE "
                       f"r.duration_mins END AS mins {DAYS}"),
    "if": f"SELECT r.run_id, IF(r.duration_mins > 15, 'long', 'short') AS size {DAYS}",
    "brackets_round_arithmetic": ("SELECT r.run_id, (r.duration_mins + 1) * 2 AS doubled "
                                  f"{DAYS}"),
    "is_null": f"SELECT r.run_id {DAYS} AND r.status IS NULL",
    "is_not_null": f"SELECT r.run_id {DAYS} AND r.status IS NOT NULL",
    "not_of_an_or": (f"SELECT r.run_id {DAYS} AND NOT (r.status = 'TEST' OR "
                     "r.status = 'FAILED')"),
    "not_of_an_and": (f"SELECT r.run_id {DAYS} AND NOT (r.status = 'SUCCESS' AND "
                      "r.duration_mins < 20)"),
    "not_of_a_comparison": f"SELECT r.run_id {DAYS} AND NOT r.duration_mins > 20",
    "not_of_not": f"SELECT r.run_id {DAYS} AND NOT (NOT r.status = 'FAILED')",
    "and_inside_or": (f"SELECT r.run_id {DAYS} AND (r.status = 'FAILED' OR (r.status = "
                      "'SUCCESS' AND r.duration_mins > 15))"),
    # Conditions an Excel workbook filters its raw data by, as Copilot writes them in Hive
    # (Toolbox 8.2, 19).
    "if_over_an_and": ("SELECT r.run_id, IF(r.status <> '' AND r.status <> 'TEST', 1, 0) AS "
                       f"kept {DAYS}"),
    "if_over_and_or_not": ("SELECT r.run_id, IF((r.status = 'FAILED' OR r.duration_mins > 25) "
                           f"AND NOT r.job_id = 1, 1, 0) AS needs_look {DAYS}"),
    "case_over_an_or": ("SELECT r.run_id, CASE WHEN r.status = 'FAILED' OR r.status = 'TEST' "
                        f"THEN r.duration_mins ELSE 0 END AS flagged_mins {DAYS}"),
    "in_a_list": f"SELECT r.run_id {DAYS} AND r.status IN ('FAILED', 'TEST')",
    "not_in_a_list": f"SELECT r.run_id {DAYS} AND r.status NOT IN ('TEST', 'FAILED')",
    "a_range_on_one_column": (f"SELECT r.run_id {DAYS} AND r.duration_mins > 10 AND "
                              "r.duration_mins <= 30"),
    "between_and_an_or": (f"SELECT r.run_id {DAYS} AND r.duration_mins BETWEEN 10 AND 20 AND "
                          "(r.job_id = 2 OR r.status IS NULL)"),
    "an_or_of_ands": (f"SELECT r.run_id {DAYS} AND ((r.job_id = 2 AND r.duration_mins < 20) "
                      "OR (r.job_id = 3 AND NOT r.duration_mins >= 30))"),
    "a_pattern_any_case": f"SELECT r.run_id {DAYS} AND LOWER(r.status) LIKE '%ail%'",
    "a_count_of_a_condition_over_a_group": (
        "SELECT r.run_id, COUNT(CASE WHEN r.status = 'FAILED' AND r.duration_mins >= 20 THEN 1 "
        f"END) OVER (PARTITION BY r.job_id) AS long_failed {DAYS}"),
    "a_sum_of_a_condition_by_group": (
        "SELECT r.job_id, COALESCE(SUM(CASE WHEN r.duration_mins > 10 AND "
        "r.duration_mins <= 30 AND (r.status <> 'TEST' OR r.status IS NULL) THEN "
        f"r.duration_mins END), 0) AS mid_mins {DAYS} GROUP BY r.job_id"),
    "count_over_a_group": ("SELECT r.run_id, COUNT(*) OVER (PARTITION BY r.job_id) AS "
                           f"runs_of_job {DAYS}"),
    "first_value": ("SELECT r.run_id, FIRST_VALUE(r.run_id) OVER (PARTITION BY r.job_id "
                    f"ORDER BY r.run_id) AS first_run {DAYS}"),
    "a_running_total": ("SELECT r.run_id, SUM(r.duration_mins) OVER (PARTITION BY r.job_id "
                        "ORDER BY r.run_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) "
                        f"AS so_far {DAYS}"),
    "order_by_a_position": (f"SELECT r.job_id, COUNT(*) AS runs {DAYS} GROUP BY r.job_id "
                            "ORDER BY 2 DESC, 1 LIMIT 2"),
    "order_by_a_name": (f"SELECT r.job_id, COUNT(*) AS runs {DAYS} GROUP BY r.job_id "
                        "ORDER BY runs DESC, r.job_id LIMIT 2"),
}
# The mappings whose condition keeps some runs and drops others.
FILTERING = ("is_null", "is_not_null", "not_of_an_or", "not_of_an_and", "not_of_a_comparison",
             "not_of_not", "and_inside_or", "in_a_list", "not_in_a_list",
             "a_range_on_one_column", "between_and_an_or", "an_or_of_ands",
             "a_pattern_any_case")


@pytest.mark.parametrize("name", list(MAPPED))
def test_each_mapping_is_toolbox_code_giving_the_originals_rows(started: Path,
                                                                name: str) -> None:
    hive = MAPPED[name]
    project.convert(f"mapped_{name}", hive, query=example_database.query, database="ops")
    assert "unchecked_" not in logic_of(started, f"mapped_{name}")
    converted = example_database.query(
        to_hive(project.load(f"mart_dev.mapped_{name}").preview()))
    original = example_database.query(hive)
    # Each condition keeps some of the nine runs and drops others, so the rows tell.
    assert name not in FILTERING or 0 < len(original) < 9
    assert list(converted.columns) == list(original.columns)
    assert sorted(map(repr, converted.to_numpy().tolist())) == sorted(
        map(repr, original.to_numpy().tolist()))
