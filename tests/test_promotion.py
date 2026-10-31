"""Promotion: a prod copy of dev Saved tables' code, which reads the prod copies of each other.
Toolbox 8.0, ticket 17.

project.promote(tables) writes a prod copy of each dev Table folder and Table reference, named
for the Prod Database, admin/databases.py's PROD, `_<their db>` kept unless rename= says
otherwise. Every promoted notebook that reads another promoted table names its prod copy. It
refuses, before writing anything, a table whose checklist has a box unticked, whose compare
hasn't passed, or that reads a dev table not promoted with it. Dev stays the source:
promoting again replaces the prod copy, archiving the old, and check reports one edited by hand.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import example_database, project, set_admin_log, to_hive

NOW = datetime.datetime(2026, 10, 31, 9, 30, 0)
WEEKLY = """\
CREATE TABLE ops_reports.failed_runs AS
SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
CREATE TABLE IF NOT EXISTS ops_reports.fails_per_job (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING) STORED AS ORC;
INSERT OVERWRITE TABLE ops_reports.fails_per_job PARTITION (dt='2026-09-24')
SELECT f.job_id, COUNT(*) AS fails FROM ops_reports.failed_runs f GROUP BY f.job_id;
"""
FAILED = "mart_dev.failed_runs_ops_reports"
PER_JOB = "mart_dev.fails_per_job_ops_reports"
# What each original holds, and its dev copy once written: the same rows.
FAILED_ROWS = "SELECT run_id, job_id, dt FROM ops.job_runs WHERE status = 'FAILED'"
PER_JOB_ROWS = ("SELECT job_id, COUNT(*) AS fails, dt FROM ops.job_runs WHERE status = "
                "'FAILED' GROUP BY job_id, dt")


def warehouse() -> Callable[[str], pd.DataFrame]:
    """A query reading the Example database, each table of the batch, dev copy and original,
    read as the rows it holds, and SHOW PARTITIONS of each answered with one day."""
    rows = {FAILED: FAILED_ROWS, "ops_reports.failed_runs": FAILED_ROWS,
            PER_JOB: PER_JOB_ROWS, "ops_reports.fails_per_job": PER_JOB_ROWS}

    def query(hive: str) -> pd.DataFrame:
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": ["dt=2026-09-24"]})
        for table, stands_for in rows.items():
            hive = hive.replace(table, f"({stands_for})")
        return example_database.query(hive)
    return query


def fill_in(root: Path, table: str) -> None:
    """Tick each box of a dev table's checklist, and fill in its location=."""
    stem = table.replace(".", "__")
    box = root / "tables" / stem / "conversion" / "checklist.md"
    box.write_text(box.read_text(encoding="utf-8").replace("- [ ] ", "- [x] "),
                   encoding="utf-8")
    path = root / "references" / f"{stem}.py"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "location=None,", f'location="/data/team/mart_dev.db/{stem.split("__")[1]}",'),
        encoding="utf-8")


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project whose DEV and PROD are filled in, with a batch converted, each box ticked,
    and its tables compared, passing; left off Python's path afterwards with its modules."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"')
                         .replace('"<PROD_DATABASE>"', '"mart"'), encoding="utf-8")
    (tmp_path / "weekly.hql").write_text(WEEKLY, encoding="utf-8")
    project.convert("weekly", files=["weekly.hql"], query=example_database.query,
                    database="ops")
    for table in (FAILED, PER_JOB):
        fill_in(tmp_path, table)
    forget_the_projects_modules()
    project.compare_batch("weekly", query=warehouse())
    yield tmp_path
    forget_the_projects_modules()


def forget_the_projects_modules() -> None:
    """Put away the modules a Project's notebooks import, which convert and load put there."""
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


def logic(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    cells = toolbox_module("notebooks").read_cells(root / "tables" / stem / f"{stem}.ipynb")
    return next(text for kind, text in cells if kind == "code" and text.startswith("# logic"))


def reference(root: Path, table: str) -> str:
    return (root / "references" / f"{table.replace('.', '__')}.py").read_text(encoding="utf-8")


def test_each_table_gets_a_prod_copy_that_reads_the_others_prod_copies(started: Path) -> None:
    report = repr(project.promote([FAILED, PER_JOB]))
    assert "mart.failed_runs_ops_reports" in report
    assert "mart.fails_per_job_ops_reports" in report
    assert 'Table(\n    "mart.failed_runs_ops_reports"' in reference(
        started, "mart.failed_runs_ops_reports")
    prod = logic(started, "mart.fails_per_job_ops_reports")
    assert "from references import mart\n" in prod
    assert "mart.failed_runs_ops_reports" in prod and "mart_dev" not in prod
    hive = to_hive(project.load("mart.fails_per_job_ops_reports").write())
    assert "INSERT OVERWRITE TABLE mart.fails_per_job_ops_reports" in hive
    assert "FROM mart.failed_runs_ops_reports" in hive
    # Dev stays the source, as it was.
    assert "mart_dev.failed_runs_ops_reports" in logic(started, PER_JOB)


def test_a_rename_names_the_prod_copy(started: Path) -> None:
    project.promote([FAILED, PER_JOB], rename={PER_JOB: "fails_per_job"})
    assert (started / "tables" / "mart__fails_per_job").is_dir()
    hive = to_hive(project.load("mart.fails_per_job").write())
    assert "INSERT OVERWRITE TABLE mart.fails_per_job PARTITION" in hive


def test_a_location_naming_the_dev_database_names_the_prod_one(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    assert 'location="/data/team/mart.db/failed_runs_ops_reports"' in reference(
        started, "mart.failed_runs_ops_reports")


def test_a_location_you_filled_in_is_kept_when_promoted_again(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    path = started / "references" / "mart__failed_runs_ops_reports.py"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "/data/team/mart.db/failed_runs_ops_reports", "/data/prod/failed_runs"),
        encoding="utf-8")
    project.promote([FAILED, PER_JOB])
    assert 'location="/data/prod/failed_runs"' in path.read_text(encoding="utf-8")


def test_a_box_unticked_or_a_compare_not_passed_is_refused_before_anything_is_written(
        started: Path) -> None:
    box = started / "tables" / "mart_dev__fails_per_job_ops_reports" / "conversion" / (
        "checklist.md")
    box.write_text(box.read_text(encoding="utf-8") + "- [ ] One more decision.\n",
                   encoding="utf-8")
    compared = started / "tables" / "mart_dev__failed_runs_ops_reports" / "conversion" / (
        "compare.md")
    compared.unlink()
    with pytest.raises(ValueError) as refused:
        project.promote([FAILED, PER_JOB])
    said = str(refused.value)
    assert f"{PER_JOB}: its conversion/checklist.md has a box unticked" in said
    assert f"{FAILED}: its compare hasn't passed" in said
    assert not list((started / "tables").glob("mart__*"))


def test_a_table_reading_a_dev_table_not_promoted_with_it_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match=f"{PER_JOB}: it reads {FAILED}, which isn't promoted "
                       "with it"):
        project.promote(PER_JOB)


def test_promoting_again_archives_the_old_copy(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    project.promote([FAILED, PER_JOB])
    assert list((started / "admin" / "removed").glob("*-mart__failed_runs_ops_reports"))


def test_check_reports_a_prod_copy_edited_by_hand(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    notebook = (started / "tables" / "mart__failed_runs_ops_reports" /
                "mart__failed_runs_ops_reports.ipynb")
    notebook.write_text(notebook.read_text(encoding="utf-8").replace(
        "# logic", "# logic, changed by hand"), encoding="utf-8")
    said = repr(project.check())
    assert ("Edited by hand, which project.promote writes over: "
            "tables/mart__failed_runs_ops_reports/mart__failed_runs_ops_reports.ipynb") in said


def test_promoted_tables_gives_each_prod_name(started: Path) -> None:
    project.promote([FAILED, PER_JOB], rename={PER_JOB: "fails_per_job"})
    assert project.promoted_tables([FAILED, PER_JOB]) == [
        "mart.failed_runs_ops_reports", "mart.fails_per_job"]
    # Neither reads itself, so neither needs a seed.
    assert project.promoted_tables([FAILED, PER_JOB], seeded=True) == []


def test_a_prod_database_not_filled_in_is_refused(started: Path) -> None:
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(
        'PROD = "mart"', 'PROD = "<PROD_DATABASE>"'), encoding="utf-8")
    with pytest.raises(ValueError, match="PROD in admin/databases.py isn't filled in"):
        project.promote(FAILED)


def test_the_promote_workflow_has_no_fiddling_and_a_done_function_for_each_step() -> None:
    workflows = toolbox_module("workflows")
    for step in workflows.PROMOTE.steps:
        assert step.kind != workflows.FIDDLING, step.name
        assert step.done is not None, step.name


# --- What ticket 17's reviews found ----------------------------------------------------------


def change_logic(root: Path, table: str, old: str, new: str) -> None:
    """Change a Table notebook's code by hand, as its author might."""
    notebooks = toolbox_module("notebooks")
    stem = table.replace(".", "__")
    path = root / "tables" / stem / f"{stem}.ipynb"
    cells = [(kind, text.replace(old, new)) for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))


def test_a_database_imported_beside_another_is_named_for_prod(started: Path) -> None:
    change_logic(started, PER_JOB, "from references import mart_dev\n",
                 "from references import mart_dev, ops\n")
    project.promote([FAILED, PER_JOB])
    prod = logic(started, "mart.fails_per_job_ops_reports")
    assert "from references import mart, ops\n" in prod


def test_a_renamed_table_imported_beside_another_keeps_its_dev_name_in_the_code(
        started: Path) -> None:
    change_logic(started, PER_JOB, "import fails_per_job_ops_reports  #",
                 "import (\n    INSERT_OVERWRITE_UNUSED,\n    fails_per_job_ops_reports,\n)  #")
    project.promote([FAILED, PER_JOB], rename={PER_JOB: "per_job"})
    assert "    per_job as fails_per_job_ops_reports,\n" in logic(started, "mart.per_job")


def test_a_renamed_reference_keeps_its_columns_and_names_itself(started: Path) -> None:
    project.promote([FAILED, PER_JOB], rename={FAILED: "failed"})
    text = reference(started, "mart.failed")
    assert 'failed = Table(\n    "mart.failed",' in text
    assert "from references.mart__failed import failed, <alias>" in text
    assert '"run_id": "bigint"' in text


def test_a_building_block_reading_the_dev_database_is_refused(started: Path) -> None:
    (started / "building_blocks" / "dev_runs.py").write_text(
        "from references import mart_dev\n\nRUNS = mart_dev.failed_runs_ops_reports\n",
        encoding="utf-8")
    change_logic(started, PER_JOB, "from references import mart_dev\n",
                 "from references import mart_dev\nfrom building_blocks.dev_runs import RUNS\n")
    with pytest.raises(ValueError, match=f"{PER_JOB}: its Building block dev_runs reads the "
                       "Dev Database"):
        project.promote([FAILED, PER_JOB])


def test_a_table_only_created_is_promoted_by_its_table_reference(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"')
                         .replace('"<PROD_DATABASE>"', '"mart"'), encoding="utf-8")
    (tmp_path / "lookup.hql").write_text(
        "CREATE TABLE ops_reports.lookup (job_id BIGINT);\n"
        "INSERT OVERWRITE TABLE ops_reports.uses SELECT l.job_id FROM ops_reports.lookup l;\n",
        encoding="utf-8")
    project.convert("lookup", files=["lookup.hql"], query=example_database.query,
                    database="ops")
    uses = "mart_dev.uses_ops_reports"
    fill_in(tmp_path, uses)
    forget_the_projects_modules()
    rows = "SELECT job_id FROM ops.jobs"
    copies = {uses: rows, "ops_reports.uses": rows}

    def query(hive: str) -> pd.DataFrame:
        for table, stands_for in copies.items():
            hive = hive.replace(table, f"({stands_for})")
        return example_database.query(hive)

    project.compare_batch("lookup", query=query)
    report = repr(project.promote([uses, "mart_dev.lookup_ops_reports"]))
    assert ("Promoted mart_dev.lookup_ops_reports to mart.lookup_ops_reports: "
            "references/mart__lookup_ops_reports.py") in report
    assert not (tmp_path / "tables" / "mart__lookup_ops_reports").exists()
    assert "mart.lookup_ops_reports" in logic(tmp_path, "mart.uses_ops_reports")
    forget_the_projects_modules()


def test_a_prod_copy_archived_by_remove_table_isnt_said_edited(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    project.remove_table("mart.failed_runs_ops_reports")
    assert "Edited by hand" not in repr(project.check())


def test_promoting_again_under_another_name_forgets_the_old_one(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    project.promote([FAILED, PER_JOB], rename={FAILED: "failed"})
    assert project.promoted_tables(FAILED) == ["mart.failed"]


def test_only_a_whole_folder_named_for_the_dev_database_is_renamed(started: Path) -> None:
    path = started / "references" / "mart_dev__failed_runs_ops_reports.py"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "/data/team/mart_dev.db/", "/data/mart_dev_team/mart_dev.db/"), encoding="utf-8")
    report = repr(project.promote([FAILED, PER_JOB]))
    expected = "/data/mart_dev_team/mart.db/failed_runs_ops_reports"
    assert f'location="{expected}"' in reference(started, "mart.failed_runs_ops_reports")
    assert f"its location= is {expected}, made from dev's: check it" in report


def test_the_prod_copy_says_it_is_one_and_leaves_dev_records_behind(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    folder = started / "tables" / "mart__failed_runs_ops_reports"
    notebooks = toolbox_module("notebooks")
    cells = notebooks.read_cells(folder / "mart__failed_runs_ops_reports.ipynb")
    assert cells[0][1].startswith(f"A prod copy project.promote made of {FAILED}:")
    assert not (folder / "conversion" / "checklist.md").exists()
    assert not (folder / "conversion" / "compare.md").exists()
    assert "mart_dev" not in (folder / "conversion" / "in_dev.hql").read_text(encoding="utf-8")


def test_promoted_tables_refuses_several_not_promoted_in_one_sentence(started: Path) -> None:
    with pytest.raises(ValueError, match=f"{FAILED} and {PER_JOB} are not promoted"):
        project.promoted_tables([FAILED, PER_JOB])
