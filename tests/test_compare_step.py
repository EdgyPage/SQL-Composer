"""The convert Workflow's compare step: each table a batch made in dev, compared with its
original on the latest Partition both hold. Toolbox 8.0, ticket 16.

project.compare_batch(name, query=query) reads each dev table's rows and its original's
through the user's query, on the last Partition SHOW PARTITIONS lists for both, or the one
partition= gives; a table with no Partitions is compared whole. Each result is written in the
table's conversion/compare.md. Once every table passes, the batch's folder moves to
admin/workflows/convert/finished/, and check stops listing it.

The Example database holds no dev table, so these tests stand in a warehouse that reads each
dev table as Hive the test gives, and answers SHOW PARTITIONS from a list.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import example_database, project, set_admin_log

NOW = datetime.datetime(2026, 10, 31, 9, 30, 0)
DEV = "mart_dev.failed_ops_reports"
ORIGINAL = "ops_reports.failed"
FAILED = """\
INSERT OVERWRITE TABLE ops_reports.failed PARTITION (dt='2026-09-24')
SELECT r.run_id, r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24' AND r.status = 'FAILED';
"""
# What the original table holds, and its dev copy once written: each its Example rows.
FAILED_ROWS = "SELECT run_id, job_id, dt FROM ops.job_runs WHERE status = 'FAILED'"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in, a batch converted from FAILED; left off
    Python's path afterwards with its modules, which a convert puts there."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    (tmp_path / "failed.hql").write_text(FAILED, encoding="utf-8")
    project.convert("failed", files=["failed.hql"], query=example_database.query,
                    database="ops")
    yield tmp_path
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


def warehouse(partitions: dict[str, list[str]],
              rows: dict[str, str]) -> Callable[[str], pd.DataFrame]:
    """A query reading the Example database, with each table `rows` names read as the Hive
    given for it, and SHOW PARTITIONS of each table `partitions` names answered from its
    list."""
    def query(hive: str) -> pd.DataFrame:
        words = hive.split()
        if words[:2] == ["SHOW", "PARTITIONS"]:
            return pd.DataFrame({"partition": partitions[words[2]]})
        for table, stands_for in rows.items():
            hive = hive.replace(table, f"({stands_for})")
        return example_database.query(hive)
    return query


def compared(root: Path) -> str:
    path = root / "tables" / "mart_dev__failed_ops_reports" / "conversion" / "compare.md"
    return path.read_text(encoding="utf-8")


BOTH_DAYS = ["dt=2026-09-23", "dt=2026-09-24"]
SAME = warehouse({DEV: BOTH_DAYS, ORIGINAL: ["dt=2026-09-22", *BOTH_DAYS]},
                 {DEV: FAILED_ROWS, ORIGINAL: FAILED_ROWS})


def test_a_table_is_compared_on_the_latest_partition_both_hold(started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME))
    assert f"{DEV}: passed, on dt = '2026-09-24'" in report
    text = compared(started)
    assert text.startswith(f"# {DEV} against {ORIGINAL}\n")
    assert "Passed: compared on dt = '2026-09-24', the latest Partition both hold" in text


def test_once_every_table_passes_the_batch_is_finished_and_no_longer_listed(
        started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME))
    assert "admin/workflows/convert/finished/failed/" in report
    convert = started / "admin" / "workflows" / "convert"
    assert (convert / "finished" / "failed" / "written.json").is_file()
    assert not (convert / "failed").exists()
    assert "failed: " not in repr(project.check())
    # Its tables are still there to promote.
    assert project.batch_tables("failed") == [DEV]


def test_rows_that_differ_fail_and_are_named_and_the_batch_stays(started: Path) -> None:
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-24'")["run_id"][0]
    fewer = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: f"{FAILED_ROWS} AND run_id <> {left_out}", ORIGINAL: FAILED_ROWS})
    report = repr(project.compare_batch("failed", query=fewer))
    assert f"{DEV}: failed, on dt = '2026-09-24'" in report
    text = compared(started)
    assert "Failed: compared on dt = '2026-09-24'" in text
    assert "1 row is in the original and not in the Statement" in text
    assert (started / "admin" / "workflows" / "convert" / "failed").is_dir()
    assert "convert.ipynb, failed: " in repr(project.check())


def test_the_partition_you_give_is_the_one_compared(started: Path) -> None:
    project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})
    assert "compared on dt = '2026-09-23', the Partition you gave" in compared(started)


def test_no_partition_in_common_fails_naming_the_latest_of_each(started: Path) -> None:
    apart = warehouse({DEV: ["dt=2026-09-24"], ORIGINAL: ["dt=2026-09-22", "dt=2026-09-23"]},
                      {DEV: FAILED_ROWS, ORIGINAL: FAILED_ROWS})
    report = repr(project.compare_batch("failed", query=apart))
    assert f"{DEV}: failed, no Partition in common" in report
    text = compared(started)
    assert "Failed: no Partition in common" in text
    assert "dt=2026-09-24" in text and "dt=2026-09-23" in text


def test_a_table_with_no_partitions_is_compared_whole(started: Path) -> None:
    hive = "SELECT r.run_id, r.status FROM ops.job_runs r WHERE r.dt = '2026-09-24'"
    project.convert("spare", hive, query=example_database.query, database="ops")
    # The same rows, read by an alias of their own, as the Example database's executor can't
    # read one table twice by one alias.
    copy = "SELECT c.run_id, c.status FROM ops.job_runs c WHERE c.dt = '2026-09-24'"
    alone = warehouse({}, {"mart_dev.spare": copy})
    report = repr(project.compare_batch("spare", query=alone))
    assert "mart_dev.spare: passed, every row" in report
    text = (started / "tables" / "mart_dev__spare" / "conversion" / "compare.md").read_text(
        encoding="utf-8")
    assert text.startswith("# mart_dev.spare against its query, in conversion/statement.hql\n")


def test_tables_names_which_are_compared(started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME, tables=[DEV]))
    assert f"{DEV}: passed" in report


def test_a_table_the_batch_didnt_make_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match="mart_dev.nothing"):
        project.compare_batch("failed", query=SAME, tables=["mart_dev.nothing"])


def test_a_batch_cant_be_named_finished(started: Path) -> None:
    with pytest.raises(ValueError, match="finished"):
        project.convert("finished", "SELECT r.run_id FROM ops.job_runs r "
                        "WHERE r.dt = '2026-09-24'", query=example_database.query,
                        database="ops")


def test_the_workflows_compare_step_calls_compare_batch(started: Path) -> None:
    assert ('failed: 2. Tick each box' in repr(project.check()))
    step = toolbox_module("workflows").CONVERT.steps[-1]
    assert step.call == "project.compare_batch(NAME, query=query)"
