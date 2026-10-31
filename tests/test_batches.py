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
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    example_database,
    hive_settings,
    project,
    run_execute,
    set_admin_log,
    to_hive,
)

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
    (tmp_path / "daily.hql").write_text(DAILY, encoding="utf-8")
    (tmp_path / "weekly.hql").write_text(WEEKLY, encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def forget_the_projects_modules() -> None:
    """Put away the modules a Project's notebooks import, which convert loaded."""
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


@pytest.fixture
def batch(started: Path) -> str:
    return repr(project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                                query=example_database.query, database="ops"))


def checklist(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    return (root / "tables" / stem / "conversion" / "checklist.md").read_text(encoding="utf-8")


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


def test_one_query_alone_is_a_saved_table_named_for_the_batch(started: Path) -> None:
    project.convert("failed", "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'",
                    query=example_database.query)
    assert (started / "tables" / "mart_dev__failed" / "mart_dev__failed.ipynb").is_file()
    assert '"run_id": "bigint"' in reference(started, "mart_dev.failed")


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
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert ("- ops_reports.lonely: mart_dev.lonely_ops_reports, its Table reference alone, "
            "references/mart_dev__lonely_ops_reports.py") in index


def test_a_table_read_before_the_batch_writes_it_is_read_as_it_was(started: Path) -> None:
    # The first statement reads ops.jobs before the second writes it: it reads the original.
    convert_script(started,
                   "CREATE TABLE ops_reports.before AS SELECT j.job_id FROM ops.jobs j;\n"
                   "INSERT OVERWRITE TABLE ops.jobs SELECT j.job_id, j.job_name, j.team, "
                   "j.region FROM ops.jobs j;\n")
    before = logic(started, "mart_dev.before_ops_reports")
    assert "ops.jobs" in before and "jobs_ops" not in before


# --- What the beginner reader found ----------------------------------------------------------


def test_a_rename_of_a_table_the_scripts_dont_write_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match="rename= names team_failures"):
        project.convert("ops_reports", files=["weekly.hql"], query=example_database.query,
                        database="ops", rename={"team_failures": "teams"})
    assert not batch_folder(started).exists()


def test_a_batch_run_again_writes_afresh_only_what_you_left_as_it_wrote_it(
        started: Path, batch: str) -> None:
    stem = "mart_dev__failed_runs_ops_reports"
    notebook = started / "tables" / stem / f"{stem}.ipynb"
    kept = notebook.read_text(encoding="utf-8").replace("# Try it", "# Mine, tried")
    notebook.write_text(kept, encoding="utf-8")
    report = repr(project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                                  query=example_database.query, database="ops"))
    assert notebook.read_text(encoding="utf-8") == kept
    fresh = f"admin/workflows/convert/ops_reports/fresh/tables/{stem}/{stem}.ipynb"
    assert (started / fresh).is_file() and fresh in report
    # A file left as the batch wrote it is written afresh, no fresh copy beside.
    assert not (batch_folder(started) / "fresh" / "references").exists()
    # The fresh copy, apart from your files, adds no mark for check() to list.
    assert "fresh/" not in repr(project.check())


def test_a_batch_run_again_with_overwrite_keeps_each_file_it_writes_over(
        started: Path, batch: str) -> None:
    stem = "mart_dev__failed_runs_ops_reports"
    notebook = started / "tables" / stem / f"{stem}.ipynb"
    notebook.write_text(notebook.read_text(encoding="utf-8").replace("# Try it", "# Mine"),
                        encoding="utf-8")
    project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                    query=example_database.query, database="ops", overwrite=True)
    assert "# Mine" not in notebook.read_text(encoding="utf-8")
    removed = started / "admin" / "removed"
    archived = list(removed.glob(f"*-ops_reports/tables/{stem}/*.ipynb"))
    assert len(archived) == 1 and "# Mine" in archived[0].read_text(encoding="utf-8")


def test_a_type_neither_its_query_nor_describe_tells_is_named_to_check(started: Path) -> None:
    convert_script(
        started, "CREATE TABLE ops_reports.labels AS SELECT j.job_id, "
                 "CASE WHEN j.team = 'a' THEN 'x' ELSE 'y' END AS label FROM ops.jobs j;\n")
    assert '- [ ] Check the type of label in references/mart_dev__labels_ops_reports.py' in (
        checklist(started, "mart_dev.labels_ops_reports"))


# --- Table folders, written directly (ticket 14) ----------------------------------------------


def test_each_table_keeps_its_statement_its_scan_and_its_checklist(started: Path,
                                                                  batch: str) -> None:
    conversion = started / "tables" / "mart_dev__failed_runs_ops_reports" / "conversion"
    statement = (conversion / "statement.hql").read_text(encoding="utf-8")
    assert statement.startswith("CREATE TABLE ops_reports.failed_runs AS")
    assert "mart_dev.failed_runs_ops_reports" in (conversion / "in_dev.hql").read_text(
        encoding="utf-8")
    assert (conversion / "scan.md").is_file()
    items = checklist(started, "mart_dev.failed_runs_ops_reports")
    assert "- [ ] Fill in location= in references/mart_dev__failed_runs_ops_reports.py" in items
    assert ("- [ ] Send the original's SET lines before you write it, as it sent them: "
            'run_execute(project.load("mart_dev.failed_runs_ops_reports").session_settings(), '
            "execute), then run_tables.") in items


def test_no_conversion_the_user_never_made_shows(started: Path, batch: str) -> None:
    assert not (started / "admin" / "removed").exists()
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert "finish_conversion" not in log and "new_table" not in log
    assert "finish_conversion" not in logic(started, "mart_dev.failed_runs_ops_reports")


def test_a_creates_stored_as_reaches_its_table_reference(started: Path, batch: str) -> None:
    assert 'stored_as="ORC"' in reference(started, "mart_dev.fails_per_job_ops_reports")


def test_check_names_the_batchs_next_step_and_ticking_the_boxes_moves_it_on(
        started: Path, batch: str) -> None:
    said = repr(project.check())
    assert ("admin/workflows/convert/convert.ipynb, ops_reports: 2. Tick each box of each "
            "table's checklist") in said
    for stem in ("mart_dev__failed_runs_ops_reports", "mart_dev__fails_per_job_ops_reports"):
        path = started / "tables" / stem / "conversion" / "checklist.md"
        path.write_text(path.read_text(encoding="utf-8").replace("- [ ] ", "- [x] "),
                        encoding="utf-8")
    assert "ops_reports: 3. Create each table in dev" in repr(project.check())


# --- What ticket 14's review found -----------------------------------------------------------


def test_a_write_that_cant_convert_is_still_made_and_the_batch_goes_on(started: Path) -> None:
    report = convert_script(
        started, "INSERT OVERWRITE TABLE ops_reports.bad SELECT r.run_id, y "
                 "FROM ops.job_runs r LATERAL VIEW explode(array(1, 2)) t AS y "
                 "WHERE r.dt = '2026-09-24';\n"
                 "CREATE TABLE ops_reports.tot AS SELECT j.job_id FROM ops.jobs j;\n")
    assert "mart_dev.tot_ops_reports" in report
    assert '"run_id": "string"' in reference(started, "mart_dev.bad_ops_reports")
    assert "- [ ] Check the type of run_id" in checklist(started, "mart_dev.bad_ops_reports")


def test_a_fresh_reference_for_one_you_changed_leaves_your_references_alone(
        started: Path, batch: str) -> None:
    path = started / "references" / "mart_dev__failed_runs_ops_reports.py"
    path.write_text(path.read_text(encoding="utf-8").replace("TODO: say", "Mine: say"),
                    encoding="utf-8")
    project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                    query=example_database.query, database="ops")
    assert (batch_folder(started) / "fresh" / "references"
            / "mart_dev__failed_runs_ops_reports.py").is_file()
    assert sorted(path.name for path in (started / "references").glob("mart_dev__*")) == [
        "mart_dev__failed_runs_ops_reports.py", "mart_dev__fails_per_job_ops_reports.py"]
    assert "Not registered" not in repr(project.check())


def test_a_batch_run_again_keeps_each_box_you_ticked(started: Path, batch: str) -> None:
    path = (started / "tables" / "mart_dev__failed_runs_ops_reports" / "conversion"
            / "checklist.md")
    ticked = path.read_text(encoding="utf-8").replace("- [ ] ", "- [x] ")
    path.write_text(ticked, encoding="utf-8")
    project.convert("ops_reports", files=["daily.hql", "weekly.hql"],
                    query=example_database.query, database="ops")
    assert path.read_text(encoding="utf-8") == ticked
    assert not (batch_folder(started) / "fresh").exists()


def test_a_batch_that_only_creates_has_no_box_to_tick(started: Path) -> None:
    convert_script(started, "CREATE TABLE ops_reports.lonely (a INT);\n")
    said = repr(project.check())
    assert "script: 2. Tick each box" not in said
    assert "script: 3. Create each table in dev" in said


def test_a_checklist_deleted_is_not_taken_as_ticked(started: Path, batch: str) -> None:
    for stem in ("mart_dev__failed_runs_ops_reports", "mart_dev__fails_per_job_ops_reports"):
        (started / "tables" / stem / "conversion" / "checklist.md").unlink()
    assert "ops_reports: 2. Tick each box" in repr(project.check())


def test_batch_md_lists_each_tables_marks(started: Path) -> None:
    convert_script(started, "CREATE TABLE ops_reports.both AS SELECT r.run_id, j.team "
                            "FROM ops.job_runs r JOIN ops.jobs j ON r.job_id = j.job_id "
                            "WHERE r.dt = '2026-09-24';\n")
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert "  - # CONVERSION: JOIN(j, many_matches=True), a box on its checklist" in index


# --- Many in, many out (ticket 15) -----------------------------------------------------------


def test_a_multi_insert_gives_a_saved_table_per_target(started: Path) -> None:
    convert_script(started, "FROM ops.job_runs r\n"
                            "INSERT OVERWRITE TABLE ops_reports.failed SELECT r.run_id\n"
                            "  WHERE r.dt = '2026-09-24' AND r.status = 'FAILED'\n"
                            "INSERT OVERWRITE TABLE ops_reports.passed SELECT r.run_id\n"
                            "  WHERE r.dt = '2026-09-24' AND r.status = 'SUCCESS';\n")
    for table in ("mart_dev.failed_ops_reports", "mart_dev.passed_ops_reports"):
        hive = to_hive(project.load(table).preview())
        assert "FROM ops.job_runs" in hive, table
    assert "'FAILED'" in to_hive(project.load("mart_dev.failed_ops_reports").preview())
    assert "'SUCCESS'" in to_hive(project.load("mart_dev.passed_ops_reports").preview())


def test_several_writes_to_one_table_stack_in_script_order(started: Path) -> None:
    convert_script(started,
                   "CREATE TABLE ops_reports.events (job_id BIGINT, kind STRING);\n"
                   "INSERT OVERWRITE TABLE ops_reports.events SELECT r.job_id, 'run' AS kind\n"
                   "  FROM ops.job_runs r WHERE r.dt = '2026-09-24';\n"
                   "INSERT INTO TABLE ops_reports.events SELECT a.run_id, 'alert' AS kind\n"
                   "  FROM ops.run_alerts a WHERE a.dt = '2026-09-24';\n")
    hive = to_hive(project.load("mart_dev.events_ops_reports").preview())
    assert "UNION ALL" in hive
    assert hive.index("'run'") < hive.index("'alert'")
    rows = example_database.query(hive)
    assert set(rows["kind"]) == {"run", "alert"}
    index = (started / "admin" / "workflows" / "convert" / "script" / "batch.md").read_text(
        encoding="utf-8")
    assert ("stacked into mart_dev.events_ops_reports's write after the one before it"
            in index)


def test_a_later_overwrite_replaces_the_writes_before_it(started: Path) -> None:
    convert_script(started,
                   "INSERT OVERWRITE TABLE ops_reports.last SELECT r.job_id\n"
                   "  FROM ops.job_runs r WHERE r.dt = '2026-09-23';\n"
                   "INSERT OVERWRITE TABLE ops_reports.last SELECT r.job_id\n"
                   "  FROM ops.job_runs r WHERE r.dt = '2026-09-24';\n")
    hive = to_hive(project.load("mart_dev.last_ops_reports").preview())
    assert "UNION ALL" not in hive and "2026-09-24" in hive and "2026-09-23" not in hive


def test_a_table_that_reads_itself_gets_a_seed_step_first(started: Path) -> None:
    report = convert_script(
        started, "CREATE TABLE ops_reports.grows AS SELECT j.job_id FROM ops.jobs j;\n"
                 "INSERT INTO TABLE ops_reports.grows SELECT r.job_id FROM ops.job_runs r\n"
                 "  WHERE r.dt = '2026-09-24'\n"
                 "  AND r.job_id NOT IN (SELECT g.job_id FROM ops_reports.grows g);\n")
    assert "Skipped" not in report
    logic = project.load("mart_dev.grows_ops_reports")
    seed = to_hive(logic.seed())
    assert seed == ("INSERT OVERWRITE TABLE mart_dev.grows_ops_reports "
                    "SELECT * FROM ops_reports.grows")
    assert project.batch_tables("script", seeded=True) == ["mart_dev.grows_ops_reports"]
    # Its write reads its own copy in dev, which the seed fills first.
    assert "FROM mart_dev.grows_ops_reports" in to_hive(logic.preview())
    assert "- [ ] Agree to seed it: its write reads its own table" in (
        checklist(started, "mart_dev.grows_ops_reports"))


# --- What ticket 15's review found -----------------------------------------------------------


def fill_in_its_location(root: Path, table: str) -> None:
    """Fill in a converted table's location=, as its checklist asks, so it can be written."""
    path = root / "references" / f"{table.replace('.', '__')}.py"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "location=None,", f'location="/data/{table.replace(".", "/")}",'), encoding="utf-8")
    forget_the_projects_modules()


def test_pieces_with_ctes_of_one_name_stack_each_reading_its_own(started: Path) -> None:
    convert_script(started,
                   "CREATE TABLE IF NOT EXISTS ops_reports.ev (run_id BIGINT, n BIGINT)\n"
                   "PARTITIONED BY (dt STRING);\n"
                   "INSERT OVERWRITE TABLE ops_reports.ev PARTITION (dt='2026-09-24')\n"
                   "WITH x AS (SELECT r.run_id, r.job_id FROM ops.job_runs r\n"
                   "  WHERE r.dt = '2026-09-24')\n"
                   "SELECT x.run_id, x.job_id AS n FROM x;\n"
                   "INSERT INTO TABLE ops_reports.ev PARTITION (dt='2026-09-24')\n"
                   "WITH x AS (SELECT a.run_id, a.alert_id FROM ops.run_alerts a\n"
                   "  WHERE a.dt = '2026-09-24')\n"
                   "SELECT x.run_id, x.alert_id AS n FROM x;\n")
    fill_in_its_location(started, "mart_dev.ev_ops_reports")
    table = project.load("mart_dev.ev_ops_reports")
    hive = to_hive(table.preview())
    assert "x_2 AS (" in hive and "FROM x_2 AS x" in hive
    rows = example_database.query(hive)
    assert list(rows.columns) == ["run_id", "n", "dt"] and len(rows) > 0
    assert "INSERT OVERWRITE TABLE mart_dev.ev_ops_reports PARTITION(dt)" in (
        to_hive(table.write()))


def test_an_incremental_insert_kept_as_hive_is_seeded_then_written(started: Path) -> None:
    dev = "mart_dev.inc_ops_reports"
    convert_script(started,
                   "CREATE TABLE IF NOT EXISTS ops_reports.inc (run_id BIGINT, job_id BIGINT)\n"
                   "PARTITIONED BY (dt STRING);\n"
                   "INSERT INTO TABLE ops_reports.inc PARTITION (dt='2026-09-24')\n"
                   "SELECT r.run_id, r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'\n"
                   "  AND r.run_id > (SELECT MAX(i.run_id) FROM ops_reports.inc i);\n")
    fill_in_its_location(started, dev)
    # Its query stays an Unchecked statement, so its write does too, reading its dev copy.
    write = to_hive(project.load(dev).write())
    assert write.startswith("INSERT INTO mart_dev.inc_ops_reports PARTITION(dt = '2026-09-24')")
    assert "FROM mart_dev.inc_ops_reports AS i" in write
    box = started / "tables" / "mart_dev__inc_ops_reports" / "conversion" / "checklist.md"
    box.write_text(box.read_text(encoding="utf-8").replace("- [ ] ", "- [x] "),
                   encoding="utf-8")
    run_execute(project.load(dev).create(), example_database.execute)
    said = repr(project.check())
    assert "script: 4. Seed each table" in said
    assert 'run_execute(hive_settings("dynamic_partitions"), execute)' in said
    run_execute(hive_settings("dynamic_partitions"), example_database.execute)
    run_execute(project.load(dev).seed(), example_database.execute)
    assert "script: 5. Write each table in dev" in repr(project.check())
    project.run_tables(tables=project.batch_tables("script"), execute=example_database.execute)
    assert "script: 6. Compare each table" in repr(project.check())
