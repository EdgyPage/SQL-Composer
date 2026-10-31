"""A Conversion of a batch: several scripts of Hive, each of several statements, made Saved
tables in the user's Dev Database. Toolbox 8.0, ticket 13.

project.convert(name, files=[...]) splits each script into its statements and orders them by
what reads what; each table the batch creates becomes a Saved table in the Dev Database,
named <table>_<its database>, with a Table folder and a Table reference, and every statement
that reads it reads that name. Tables it only reads keep their names. It runs here on the
Example database.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import example_database, project, set_admin_log

NOW = datetime.datetime(2026, 10, 31, 9, 30, 0)

# Two scripts as another team wrote them, the second reading the table the first creates. The
# second is given first: the batch orders them by what reads what.
WEEKLY = """\
SET hive.exec.parallel=true;
DROP TABLE IF EXISTS ops_reports.failed_runs;
CREATE TABLE ops_reports.failed_runs AS
SELECT r.run_id, r.job_id, r.dt
FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
"""
DAILY = """\
CREATE TABLE IF NOT EXISTS ops_reports.fails_per_job (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING) STORED AS ORC;
INSERT OVERWRITE TABLE ops_reports.fails_per_job PARTITION (dt='2026-09-24')
SELECT f.job_id, COUNT(*) AS fails
FROM ops_reports.failed_runs f
GROUP BY f.job_id;
ANALYZE TABLE ops_reports.fails_per_job COMPUTE STATISTICS;
"""
DEV = "mart_dev"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', f'"{DEV}"'), encoding="utf-8")
    (tmp_path / "daily.hql").write_text(DAILY, encoding="utf-8")
    (tmp_path / "weekly.hql").write_text(WEEKLY, encoding="utf-8")
    return tmp_path


@pytest.fixture
def batch(started: Path) -> str:
    return repr(project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                                query=example_database.query, database="ops"))


def batch_folder(root: Path) -> Path:
    return root / "admin" / "workflows" / "convert" / "ops_reports"


def reference(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    return (root / "references" / f"{stem}.py").read_text(encoding="utf-8")


def logic(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    cells = toolbox_module("notebooks").read_cells(root / "tables" / stem / f"{stem}.ipynb")
    return next(text for kind, text in cells if kind == "code" and text.startswith("# logic"))


# --- Its Dev Database ----------------------------------------------------------------------


def test_a_batch_needs_the_dev_database_filled_in(started: Path) -> None:
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(f'"{DEV}"',
                                                                         '"<DEV_DATABASE>"'),
                         encoding="utf-8")
    with pytest.raises(ValueError, match="DEV in admin/databases.py"):
        project.convert("ops_reports", files=["weekly.hql"], query=example_database.query)
    assert not (started / "tables" / "mart_dev__failed_runs_ops_reports").exists()


def test_check_names_databases_py_once_a_conversion_is_started(started: Path) -> None:
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(f'"{DEV}"',
                                                                         '"<DEV_DATABASE>"'),
                         encoding="utf-8")
    assert "databases.py" not in repr(project.check())
    notebooks = toolbox_module("notebooks")
    path = started / "admin" / "workflows" / "convert" / "convert.ipynb"
    number = next(number for number, (kind, text) in enumerate(notebooks.read_cells(path), 1)
                  if kind == "code" and text.startswith("NAME ="))
    notebooks.write_cell_text(path, number, 'NAME = "ops_reports"')
    assert "admin/databases.py: fill in DEV" in repr(project.check())


# --- Names in dev --------------------------------------------------------------------------


def test_each_table_the_batch_creates_is_a_saved_table_in_dev(started: Path,
                                                               batch: str) -> None:
    for table in ("mart_dev.failed_runs_ops_reports", "mart_dev.fails_per_job_ops_reports"):
        stem = table.replace(".", "__")
        assert (started / "tables" / stem / f"{stem}.ipynb").is_file(), table
        assert f'"{table}"' in reference(started, table)
    # A table it only reads keeps its name, and its Table reference comes from DESCRIBE.
    assert (started / "references" / "ops__job_runs.py").is_file()
    assert not (started / "references" / "mart_dev__job_runs_ops.py").exists()


def test_a_statement_that_reads_a_created_table_reads_its_dev_copy(started: Path,
                                                                    batch: str) -> None:
    fails = logic(started, "mart_dev.fails_per_job_ops_reports")
    assert "from references import mart_dev" in fails
    assert "mart_dev.failed_runs_ops_reports" in fails
    assert "ops_reports" not in fails.replace("_ops_reports", "")


def test_the_statements_are_in_the_order_of_what_reads_what(started: Path, batch: str) -> None:
    index = (batch_folder(started) / "batch.md").read_text(encoding="utf-8")
    assert index.index("failed_runs_ops_reports") < index.index("fails_per_job_ops_reports")
    # Each script is kept as it was given.
    scripts = batch_folder(started) / "scripts"
    assert (scripts / "daily.hql").read_text(encoding="utf-8") == DAILY
    assert (scripts / "weekly.hql").read_text(encoding="utf-8") == WEEKLY


def test_each_statement_that_becomes_nothing_or_hive_is_listed(started: Path,
                                                               batch: str) -> None:
    index = (batch_folder(started) / "batch.md").read_text(encoding="utf-8")
    assert "DROP TABLE IF EXISTS ops_reports.failed_runs" in index
    assert "SET hive.exec.parallel" in index
    # The statement no step makes stays Hive, an Unchecked statement, its names swapped.
    assert 'unchecked_hive("ANALYZE TABLE mart_dev.fails_per_job_ops_reports' in index


# --- Table references ----------------------------------------------------------------------


def test_a_create_gives_its_tables_columns_types_and_partitions(started: Path,
                                                               batch: str) -> None:
    text = reference(started, "mart_dev.fails_per_job_ops_reports")
    assert '"job_id": "bigint"' in text and '"fails": "bigint"' in text
    assert '"dt": "string"' in text and 'partitioned_by=["dt"]' in text
    assert "<COLUMN_TYPE>" not in text and "key=None" in text


def test_a_create_as_select_takes_its_columns_from_its_query(started: Path,
                                                             batch: str) -> None:
    text = reference(started, "mart_dev.failed_runs_ops_reports")
    assert '"run_id": "bigint"' in text and '"job_id": "bigint"' in text
    assert '"dt": "string"' in text and "<COLUMN_TYPE>" not in text


def test_a_source_whose_describe_fails_is_named_and_the_rest_written(started: Path) -> None:
    (started / "more.hql").write_text(
        "CREATE TABLE ops_reports.notes AS SELECT n.team FROM ops.no_such_table n;\n" + WEEKLY,
        encoding="utf-8")
    report = repr(project.convert("ops_reports", files=["more.hql"],
                                  query=example_database.query, database="ops"))
    assert "ops.no_such_table" in report
    assert (started / "tables" / "mart_dev__failed_runs_ops_reports").is_dir()


# --- Refusals ------------------------------------------------------------------------------


def test_two_tables_that_read_each_other_are_refused(started: Path) -> None:
    # In one script, a read before its table's write reads the table as it was; across two
    # scripts, each must come first.
    (started / "x.hql").write_text("INSERT OVERWRITE TABLE a.x SELECT y.id FROM a.y y;\n",
                                   encoding="utf-8")
    (started / "y.hql").write_text("INSERT OVERWRITE TABLE a.y SELECT x.id FROM a.x x;\n",
                                   encoding="utf-8")
    with pytest.raises(ValueError, match=r"a\.x.*a\.y|a\.y.*a\.x"):
        project.convert("loop", files=["x.hql", "y.hql"], query=example_database.query)


def test_two_tables_with_one_dev_name_are_refused_until_one_is_renamed(started: Path) -> None:
    # x in a_b and x_a in b are both x_a_b in dev.
    (started / "clash.hql").write_text(
        "CREATE TABLE a_b.x AS SELECT j.job_id FROM ops.jobs j;\n"
        "CREATE TABLE b.x_a AS SELECT j.job_id FROM ops.jobs j;\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"a_b\.x.*b\.x_a"):
        project.convert("clash", files=["clash.hql"], query=example_database.query)
    assert not (started / "tables" / "mart_dev__x_a_b").exists()
    project.convert("clash", files=["clash.hql"], query=example_database.query,
                    rename={"b.x_a": "x_a_other"})
    assert (started / "tables" / "mart_dev__x_a_b").is_dir()
    assert (started / "tables" / "mart_dev__x_a_other").is_dir()


def test_one_query_still_converts_as_one(started: Path) -> None:
    project.convert("failed", "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'",
                    query=example_database.query)
    assert (started / "admin" / "conversions" / "failed" / "failed.ipynb").is_file()


# --- What the spec review found -------------------------------------------------------------


def convert_script(root: Path, text: str) -> str:
    (root / "script.hql").write_text(text, encoding="utf-8")
    return repr(project.convert("script", files=["script.hql"], query=example_database.query,
                                database="ops"))


def test_a_comment_above_a_truncate_still_makes_its_insert_into_an_overwrite(
        started: Path) -> None:
    convert_script(started, "CREATE TABLE ops_reports.tot (job_id BIGINT);\n"
                            "-- empty it first\nTRUNCATE TABLE ops_reports.tot;\n"
                            "INSERT INTO ops_reports.tot SELECT j.job_id FROM ops.jobs j;\n")
    assert "INSERT_OVERWRITE(tot_ops_reports" in logic(started, "mart_dev.tot_ops_reports")
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert "`TRUNCATE TABLE ops_reports.tot`: nothing: the write after it" in index


def test_msck_repair_becomes_nothing(started: Path) -> None:
    convert_script(started, "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n"
                            "MSCK REPAIR TABLE ops_reports.tot;\n")
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert "`MSCK REPAIR TABLE ops_reports.tot`: nothing: write() adds" in index


def test_a_statement_sqlglot_reads_as_a_command_still_gets_its_names_swapped(
        started: Path) -> None:
    convert_script(started, "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n"
                            "LOAD DATA INPATH '/landing/tot' INTO TABLE ops_reports.tot;\n")
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert "INTO TABLE mart_dev.tot_ops_reports" in index


def test_a_create_with_no_write_still_gets_its_table_reference(started: Path) -> None:
    convert_script(started,
                   "CREATE TABLE ops_reports.lonely (a INT) PARTITIONED BY (dt STRING);\n"
                   "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n")
    text = reference(started, "mart_dev.lonely_ops_reports")
    assert '"a": "int"' in text and 'partitioned_by=["dt"]' in text
    # It has no logic, so no Table folder, and the report says so.
    assert not (started / "tables" / "mart_dev__lonely_ops_reports").exists()


def test_the_report_names_a_table_only_created_apart(started: Path) -> None:
    report = convert_script(
        started, "CREATE TABLE ops_reports.lonely (a INT);\n"
                 "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n")
    assert "into 1 Saved table in mart_dev: mart_dev.tot_ops_reports." in report
    assert ("A Table reference alone, since the scripts create it and never write it: "
            "mart_dev.lonely_ops_reports.") in report


def test_a_table_read_before_the_batch_writes_it_is_read_as_it_was(started: Path) -> None:
    # The first statement reads ops.jobs before the second writes it: it reads the original.
    convert_script(started,
                   "CREATE TABLE ops_reports.before AS SELECT j.job_id FROM ops.jobs j;\n"
                   "INSERT OVERWRITE TABLE ops.jobs SELECT j.job_id, j.job_name, j.team, "
                   "j.region FROM ops.jobs j;\n")
    before = logic(started, "mart_dev.before_ops_reports")
    assert "ops.jobs" in before and "jobs_ops" not in before


def test_a_table_that_reads_itself_is_named_and_kept_as_hive(started: Path) -> None:
    report = convert_script(
        started, "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n"
                 "INSERT INTO TABLE ops_reports.grows SELECT g.job_id "
                 "FROM ops_reports.grows g;\n")
    assert "mart_dev.grows_ops_reports (it reads its own table" in report
    assert not (started / "tables" / "mart_dev__grows_ops_reports").exists()
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert ("a write to mart_dev.grows_ops_reports its notebook doesn't make, kept as Hive"
            in index)


# --- What the beginner reader found ----------------------------------------------------------


def test_a_rename_of_a_table_the_scripts_dont_write_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match="rename= names team_failures"):
        project.convert("ops_reports", files=["weekly.hql"], query=example_database.query,
                        database="ops", rename={"team_failures": "teams"})
    assert not batch_folder(started).exists()


def test_a_batch_run_again_is_refused_before_anything_is_written(started: Path,
                                                                batch: str) -> None:
    with pytest.raises(FileExistsError, match="mart_dev.failed_runs_ops_reports"):
        project.convert("again", files=["daily.hql", "weekly.hql"],
                        query=example_database.query, database="ops")
    assert not (started / "admin" / "conversions" / "failed_runs_ops_reports").exists()
    assert not (started / "admin" / "workflows" / "convert" / "again").exists()


def test_a_type_neither_its_query_nor_describe_tells_is_named_to_check(started: Path) -> None:
    report = convert_script(
        started, "CREATE TABLE ops_reports.labels AS SELECT j.job_id, "
                 "CASE WHEN j.team = 'a' THEN 'x' ELSE 'y' END AS label FROM ops.jobs j;\n")
    assert 'Types to check, each written as "string"' in report
    assert "mart_dev.labels_ops_reports.label" in report
