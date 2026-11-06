"""Building blocks in prod: promote copies each Building block a promoted table imports into
building_blocks/prod/. Toolbox 8.5, ticket 10.

Each block a promoted table's notebook or Table reference imports, directly or through another
block, Run values among them, gets a prod copy, building_blocks/prod/<name>.py, which the prod
table's notebook and Table reference import in its place. Dev's blocks change freely; prod's
only when promoted again, which archives the prod copy into admin/removed/ first, and
project.check() names a prod copy edited by hand. A block that names the Dev Database is
refused, as before.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project, set_admin_log, to_hive

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
PROD_PER_JOB = "mart.fails_per_job_ops_reports"
FAILED_ROWS = "SELECT run_id, job_id, dt FROM ops.job_runs WHERE status = 'FAILED'"
PER_JOB_ROWS = ("SELECT job_id, COUNT(*) AS fails, dt FROM ops.job_runs WHERE status = "
                "'FAILED' GROUP BY job_id, dt")
SETTINGS = ('DEV = {"database": "mart_dev", "location_root": "/data/team/dev"}\n'
            'PROD = {"database": "mart", "location_root": "/data/team/prod"}\n')
# Two blocks: the one the notebook imports, which imports the other.
WORDS = 'FAILED = "FAILED"\n'
STATUSES = "from building_blocks.words import FAILED\n\nSTATUSES = [FAILED]\n"
IMPORTED = "from building_blocks.statuses import STATUSES\n"


def warehouse() -> Callable[[str], pd.DataFrame]:
    """The Example database, each table of the batch read as the rows it holds."""
    rows = {FAILED: FAILED_ROWS, "ops_reports.failed_runs": FAILED_ROWS,
            PER_JOB: PER_JOB_ROWS, "ops_reports.fails_per_job": PER_JOB_ROWS}

    def query(hive: str) -> pd.DataFrame:
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": ["dt=2026-09-24"]})
        for table, stands_for in rows.items():
            hive = hive.replace(table, f"({stands_for})")
        return example_database.query(hive)
    return query


def notebook_path(root: Path, table: str) -> Path:
    stem = table.replace(".", "__")
    return root / "tables" / stem / f"{stem}.ipynb"


def logic(root: Path, table: str) -> str:
    cells = toolbox_module("notebooks").read_cells(notebook_path(root, table))
    return next(text for kind, text in cells if kind == "code" and text.startswith("# logic"))


def import_the_block(root: Path, table: str) -> None:
    """The table's logic imports the statuses block, as its author writes it."""
    notebooks = toolbox_module("notebooks")
    path = notebook_path(root, table)
    cells = [(kind, text.replace("from references import mart_dev\n",
                                 "from references import mart_dev\n" + IMPORTED, 1))
             for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project whose batch is converted and compared, fails_per_job's logic importing the
    statuses block, which imports the words block."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    (tmp_path / "admin" / "databases.py").write_text(SETTINGS, encoding="utf-8")
    blocks = tmp_path / "building_blocks"
    (blocks / "words.py").write_text(WORDS, encoding="utf-8")
    (blocks / "statuses.py").write_text(STATUSES, encoding="utf-8")
    (blocks / "unused.py").write_text("UNUSED = 1\n", encoding="utf-8")
    (tmp_path / "weekly.hql").write_text(WEEKLY, encoding="utf-8")
    project.convert("weekly", files=["weekly.hql"], query=example_database.query,
                    database="ops")
    for table in (FAILED, PER_JOB):
        project.write_decisions({table: {"key": None}})
    import_the_block(tmp_path, PER_JOB)
    forget_the_projects_modules()
    project.compare_batch("weekly", query=warehouse())
    yield tmp_path
    forget_the_projects_modules()


def prod_block(root: Path, name: str) -> Path:
    return root / "building_blocks" / "prod" / f"{name}.py"


def test_promote_copies_each_block_a_table_imports_and_each_they_import(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    assert "from building_blocks.prod.statuses import STATUSES\n" in logic(started,
                                                                            PROD_PER_JOB)
    assert "from building_blocks.prod.words import FAILED\n" in prod_block(
        started, "statuses").read_text(encoding="utf-8")
    assert 'FAILED = "FAILED"' in prod_block(started, "words").read_text(encoding="utf-8")
    assert not prod_block(started, "unused").exists()
    # Dev stays the source, as it was.
    assert IMPORTED in logic(started, PER_JOB)
    forget_the_projects_modules()
    assert "INSERT OVERWRITE TABLE mart.fails_per_job_ops_reports" in to_hive(
        project.load(PROD_PER_JOB).write())
    assert "prod_building_block,words," in (started / "admin" / "registry.csv").read_text(
        encoding="utf-8")


def test_a_block_changed_in_dev_reaches_prod_only_when_promoted_again(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    (started / "building_blocks" / "words.py").write_text('FAILED = "FAIL"\n', encoding="utf-8")
    assert '"FAILED"' in prod_block(started, "words").read_text(encoding="utf-8")
    assert "Edited by hand" not in repr(project.check())
    report = repr(project.promote([FAILED, PER_JOB]))
    assert '"FAIL"' in prod_block(started, "words").read_text(encoding="utf-8")
    assert list((started / "admin" / "removed").glob("*-words.py"))
    assert "building_blocks/prod/words.py" in report
    assert "Edited by hand" not in repr(project.check())


def test_check_names_a_prod_block_edited_by_hand(started: Path) -> None:
    project.promote([FAILED, PER_JOB])
    prod_block(started, "words").write_text('FAILED = "BROKEN"\n', encoding="utf-8")
    assert ("Edited by hand, which project.promote writes over: building_blocks/prod/words.py "
            "(change building_blocks/words.py and promote it again)") in repr(project.check())


def test_a_block_imported_through_another_naming_the_dev_database_is_refused(
        started: Path) -> None:
    (started / "building_blocks" / "words.py").write_text(
        "from references import mart_dev\n\nRUNS = mart_dev.failed_runs_ops_reports\n"
        'FAILED = "FAILED"\n', encoding="utf-8")
    with pytest.raises(ValueError, match=f"{PER_JOB}: its Building block words reads the "
                       "Dev Database"):
        project.promote([FAILED, PER_JOB])
    assert not (started / "building_blocks" / "prod").exists()


def test_a_run_value_promotes_decisions_cell_gives_reads_its_blocks_prod_copy(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A Run value given only in promote's decisions cell, for a prod seed limit, is a block no
    # dev table imports, so promote copied none: the prod reference reads a prod copy all the
    # same, written as its import is pointed at it.
    monkeypatch.chdir(tmp_path)
    project.start()
    (tmp_path / "building_blocks" / "first_days.py").write_text(
        "import datetime\n\n\ndef first_day() -> datetime.date:\n"
        "    return datetime.date(2026, 9, 1)\n", encoding="utf-8")
    mark = toolbox_module("decisions").RUN_VALUE_MARK
    reference = tmp_path / "references" / "mart__fails.py"
    reference.write_text(f"from building_blocks.first_days import first_day{mark}\n"
                         'SEED = {"dt": {"from": first_day}}\n', encoding="utf-8")
    record = tmp_path / "admin" / "workflows" / "promote" / "promoted.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text('{"mart.fails": {"dev": "mart_dev.fails", "seeded": true}}',
                      encoding="utf-8")
    said = project.prod_run_values_pointed(["mart.fails"])
    assert reference.read_text(encoding="utf-8").startswith(
        f"from building_blocks.prod.first_days import first_day{mark}")
    copy = tmp_path / "building_blocks" / "prod" / "first_days.py"
    assert copy.read_text(encoding="utf-8").startswith("# A prod copy project.promote made of")
    assert any("first_days" in line for line in said)
    assert "building_blocks/prod/first_days.py" in record.read_text(encoding="utf-8")
    # Run again, it changes nothing.
    assert project.prod_run_values_pointed(["mart.fails"]) == []
    forget_the_projects_modules()
