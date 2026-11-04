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
import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import run_admin_notebook, toolbox_module

from sqlglot_composer import (
    example_database,
    project,
    run_execute,
    set_admin_log,
    unchecked_hive,
)

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


def test_once_every_table_passes_the_batch_is_finished_and_check_says_it_is_done(
        started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME))
    assert "admin/workflows/convert/finished/failed/" in report
    convert = started / "admin" / "workflows" / "convert"
    assert (convert / "finished" / "failed" / "written.json").is_file()
    assert not (convert / "failed").exists()
    # Toolbox 8.2, 23: W3-2 found check() silent once the batch was done, where the
    # Workflow's Self-check reads it.
    checked = repr(project.check())
    assert "convert.ipynb, failed: 7." not in checked
    assert checked.endswith(
        "Done: each convert batch below.\n"
        "  admin/workflows/convert/convert.ipynb, failed: every table the batch wrote passed "
        "its compare, and its folder is admin/workflows/convert/finished/failed/.")
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


@pytest.mark.parametrize("given, said", [
    ({"dt": "'2026-09-23'"}, "partition= gives dt in quotes of its own"),
    ("2026-09-23", "partition= is '2026-09-23', not a dict of each partition column's value"),
], ids=["quoted", "not a dict"])
def test_a_partition_not_as_show_partitions_lists_it_is_refused(
        started: Path, given: object, said: str) -> None:
    # Toolbox 8.3: step 2 teaches a bare tag's own quotes; a Partition's value takes none.
    with pytest.raises((ValueError, TypeError), match=said):
        project.compare_batch("failed", query=SAME, partition=given)


def test_the_compare_names_partition_to_compare_another(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    assert ('to compare one, set PARTITION = {"dt": "..."} in the convert notebook\'s names '
            "cell, run it, and run step 7 again") in compared(started)


def test_a_compare_of_another_partition_keeps_the_first_result_beside_it(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})
    text = compared(started)
    assert text.count(f"# {DEV} against {ORIGINAL}\n") == 1
    assert "## dt = '2026-09-23'\n\nPassed: compared on dt = '2026-09-23'" in text
    assert "## dt = '2026-09-24'\n\nPassed: compared on dt = '2026-09-24'" in text
    assert toolbox_module("workflows").compare_passed(started, DEV)


def test_a_compare_of_the_same_partition_replaces_its_result(started: Path) -> None:
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-23'")["run_id"][0]
    fewer = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: f"{FAILED_ROWS} AND run_id <> {left_out}", ORIGINAL: FAILED_ROWS})
    project.compare_batch("failed", query=SAME)
    project.compare_batch("failed", query=fewer, partition={"dt": "2026-09-23"})
    workflows = toolbox_module("workflows")
    # One Partition failing fails the table, though the other passed.
    assert not workflows.compare_passed(started, DEV)
    project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})
    text = compared(started)
    assert text.count("## dt = '2026-09-23'") == 1 and "Failed: " not in text
    assert workflows.compare_passed(started, DEV)


def test_a_partition_that_failed_fails_the_table_beside_one_that_passed(started: Path) -> None:
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-23'")["run_id"][0]
    fewer = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: f"{FAILED_ROWS} AND run_id <> {left_out}", ORIGINAL: FAILED_ROWS})
    project.compare_batch("failed", query=fewer, partition={"dt": "2026-09-23"})
    project.compare_batch("failed", query=SAME)
    text = compared(started)
    assert "## dt = '2026-09-23'\n\nFailed: " in text
    assert "## dt = '2026-09-24'\n\nPassed: " in text
    assert not toolbox_module("workflows").compare_passed(started, DEV)


def test_a_compare_md_from_before_8_2_is_read_then_written_over(started: Path) -> None:
    path = started / "tables" / "mart_dev__failed_ops_reports" / "conversion" / "compare.md"
    path.write_text(f"# {DEV} against {ORIGINAL}\n\nPassed: compared on dt = '2026-09-24', the "
                    "latest Partition both hold.\nCompared at 2026-10-31 09:30:00.\n",
                    encoding="utf-8")
    workflows = toolbox_module("workflows")
    assert workflows.compare_passed(started, DEV)
    project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})
    text = compared(started)
    # The result 8.1 wrote names no Partition, so the new one, which does, takes its place.
    assert text.count("Compared at ") == 1 and "## dt = '2026-09-23'" in text


def test_a_result_from_before_the_table_was_written_again_is_dropped(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})
    later = datetime.datetime(2026, 10, 31, 10, 0, 0)
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: later)
    run_execute(unchecked_hive(f"INSERT INTO TABLE {DEV} PARTITION (dt) {FAILED_ROWS}"),
                example_database.execute)
    project.compare_batch("failed", query=SAME)
    text = compared(started)
    assert "## dt = '2026-09-24'" in text and "## dt = '2026-09-23'" not in text
    assert toolbox_module("workflows").compare_passed(started, DEV)


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
    assert "failed: 2. Answer each table's open Decisions" in repr(project.check())
    step = toolbox_module("workflows").CONVERT.steps[-1]
    assert step.call == "project.compare_batch(NAME, query=query, partition=PARTITION)"


def test_the_compare_step_says_it_checks_the_latest_partition_and_how_to_check_another(
        ) -> None:
    # Toolbox 8.2, 23: H1 had to find partition= for itself.
    step = toolbox_module("workflows").CONVERT.steps[-1]
    assert "on the latest Partition both hold" in step.goal
    assert "If you want another Partition compared too, one your dev table holds" in step.action
    assert "its value with no quotes of its own, run the names cell" in step.action
    # Toolbox 8.3, 06: set in the names cell, with no cell of your own.
    assert '`{"dt": "2026-09-23"}`' in step.action
    assert "in a new cell" not in step.action


def test_the_seed_step_says_it_seeded_nothing_when_no_table_reads_itself(
        started: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Toolbox 8.2, 23: W1-1 saw the seed cell send its Session setting, and say nothing,
    # though no table of the batch reads itself.
    notebook = started / "admin" / "workflows" / "convert" / "convert.ipynb"
    code = [text for kind, text in toolbox_module("notebooks").read_cells(notebook)
            if kind == "code"]
    seed = toolbox_module("workflows").CONVERT.steps[4]
    assert seed.call in code
    said = run_admin_notebook(notebook, [code[0], 'NAME = "failed"', seed.call], capsys)
    assert said == "Seeded nothing: no table of the batch reads itself.\n"
    assert toolbox_module("workflows").sent_rows(started) == []

# --- What ticket 16's review found -----------------------------------------------------------


def test_a_batch_that_wrote_no_table_is_never_finished(started: Path) -> None:
    record = started / "admin" / "workflows" / "convert" / "failed" / "written.json"
    kept = json.loads(record.read_text(encoding="utf-8"))
    kept["originals"] = {}
    record.write_text(json.dumps(kept), encoding="utf-8")
    report = repr(project.compare_batch("failed", query=SAME))
    assert "finished" not in report
    assert record.is_file()


def test_a_finished_batchs_name_is_refused(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    with pytest.raises(FileExistsError, match="a batch named failed is finished"):
        project.convert("failed", files=["failed.hql"], query=example_database.query,
                        database="ops")


def test_a_partition_naming_no_partition_column_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match="partition= names day, which no table it compares"):
        project.compare_batch("failed", query=SAME, partition={"day": "2026-09-23"})


def test_a_write_after_a_passing_compare_makes_it_stale(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project.compare_batch("failed", query=SAME)
    workflows = toolbox_module("workflows")
    assert workflows.compare_passed(started, DEV)
    later = datetime.datetime(2026, 10, 31, 10, 0, 0)
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: later)
    run_execute(unchecked_hive(f"INSERT INTO TABLE {DEV} PARTITION (dt) {FAILED_ROWS}"),
                example_database.execute)
    assert not workflows.compare_passed(started, DEV)


def test_what_stops_a_compare_is_its_result_whole(started: Path) -> None:
    def query(hive: str) -> pd.DataFrame:
        raise RuntimeError("The warehouse said no.\nIts second line says why.")

    report = repr(project.compare_batch("failed", query=query))
    assert f"{DEV}: failed, couldn't compare: The warehouse said no." in report
    assert "Its second line says why." in compared(started)


# --- What ticket 16's beginner reader found ---------------------------------------------------


def test_a_partition_you_give_that_neither_holds_fails_and_finishes_nothing(
        started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME, partition={"dt": "2030-01-01"}))
    assert (f"{DEV}: failed, there is no Partition where dt = '2030-01-01' in {DEV} and "
            f"{ORIGINAL}: give one both hold") in report
    assert "finished" not in report


def test_a_finished_batch_is_archived_by_remove_conversion_which_frees_its_name(
        started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    project.remove_conversion("failed")
    convert = started / "admin" / "workflows" / "convert"
    assert not (convert / "finished" / "failed").exists()
    assert list((started / "admin" / "removed").glob("*-failed"))
    project.convert("failed", files=["failed.hql"], query=example_database.query,
                    database="ops")
    assert (convert / "failed" / "written.json").is_file()


def test_compare_md_says_what_the_statement_is(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    assert (f"Below, the Statement is {DEV}'s rows, and the original {ORIGINAL}'s."
            in compared(started))


# --- The Key, checked by the compare (Toolbox 8.1, ticket 04) -------------------------------


def test_a_key_the_rows_break_fails_the_compare_naming_the_rows(started: Path) -> None:
    # Each run of the day, one run_id given them all: the two sides match, and run_id repeats.
    repeated = "SELECT 7 AS run_id, job_id, dt FROM ops.job_runs"
    query = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: repeated, ORIGINAL: repeated})
    project.write_decisions({DEV: {"key": ["run_id"]}})
    report = repr(project.compare_batch("failed", query=query))
    assert f"{DEV}: failed, on dt = '2026-09-24'" in report
    text = compared(started)
    assert "but its Key (run_id) repeats" in text
    assert "the key (run_id) repeats" in text


def test_a_key_the_rows_keep_passes(started: Path) -> None:
    project.write_decisions({DEV: {"key": ["run_id"]}})
    assert f"{DEV}: passed" in repr(project.compare_batch("failed", query=SAME))
