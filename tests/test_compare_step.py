"""The convert Workflow's compare step: each table a batch made in dev, compared with its
original on the latest Partition both hold. Toolbox 8.0, ticket 16.

project.compare_batch(name, query=query) reads each dev table's rows and its original's
through the user's query, on the last Partition SHOW PARTITIONS lists for both, or the one
partition= gives; a table with no Partitions is compared whole. Each result is written in the
table's conversion/compare.md. Once every table is compared, the batch's folder moves to
admin/workflows/convert/finished/, and check stops listing it: since Toolbox 8.10 (ticket 03)
whether each passed or not, a fail and a query alone that can't be filled in, not compared,
named first in plain words. A query alone is filled in first: its Script tags with their
answers, a Run value with the value its write recorded, and its Hivevars with their SET lines.

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

import example_database
from sqlglot_composer import (
    hivevar,
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
    # Since 8.10 the lines proposed in the Table reference convert added follow it.
    assert (
        "Done: each convert batch below.\n"
        "  admin/workflows/convert/convert.ipynb, failed: every table the batch wrote passed "
        "its compare, and its folder is admin/workflows/convert/finished/failed/.\n") in checked
    # Its tables are still there to promote.
    assert project.batch_tables("failed") == [DEV]


def test_rows_that_differ_fail_and_are_named_and_the_batch_finishes_all_the_same(
        started: Path) -> None:
    # Toolbox 8.10, ticket 03: no compare result stops the user; promotion is their call.
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-24'")["run_id"][0]
    fewer = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: f"{FAILED_ROWS} AND run_id <> {left_out}", ORIGINAL: FAILED_ROWS})
    report = repr(project.compare_batch("failed", query=fewer))
    assert f"{DEV}: failed, on dt = '2026-09-24'" in report
    assert (f"The batch is finished, though not every table passed: {DEV} failed its "
            "compare. That stops nothing: promote promotes each all the same, naming it") in (
        report)
    text = compared(started)
    assert "Failed: compared on dt = '2026-09-24'" in text
    assert "1 row is in the original and not in the Statement" in text
    # The warning comes first, under the heading, in plain words.
    heading, warning = text.split("\n\n")[1:3]
    assert heading.startswith("Below, the Statement is")
    assert warning.startswith(f"Warning: {DEV} failed its compare: the first result below "
                              "says why. That stops nothing")
    convert = started / "admin" / "workflows" / "convert"
    assert (convert / "finished" / "failed").is_dir() and not (convert / "failed").exists()
    checked = repr(project.check())
    assert "convert.ipynb, failed: 7." not in checked
    assert (f"convert.ipynb, failed: every table the batch wrote was compared, and its folder "
            f"is admin/workflows/convert/finished/failed/; {DEV} failed its compare: check "
            "its conversion/compare.md before you promote it.") in checked


def test_the_latest_partition_and_each_listed_are_compared_a_section_each(
        started: Path) -> None:
    # Toolbox 8.5, ticket 04: PARTITIONS, a list, in place of 8.4's PARTITION.
    report = repr(project.compare_batch("failed", query=SAME,
                                        partitions=[{"dt": "2026-09-23"}]))
    assert f"{DEV}: passed, on dt = '2026-09-24', the latest Partition both hold" in report
    assert f"{DEV}: passed, on dt = '2026-09-23', the Partition you gave" in report
    text = compared(started)
    assert "## dt = '2026-09-23'\n\nPassed: compared on dt = '2026-09-23', the Partition you " \
        "gave" in text
    assert "## dt = '2026-09-24'\n\nPassed: compared on dt = '2026-09-24', the latest" in text
    # The one other Partition both hold is listed, so none is named as left unchecked.
    assert "not compared" not in text


def test_no_partitions_listed_compares_the_latest_alone(started: Path) -> None:
    project.compare_batch("failed", query=SAME, partitions=[])
    text = compared(started)
    assert "## dt = '2026-09-24'" in text and "## dt = '2026-09-23'" not in text


def test_a_listed_partition_that_is_the_latest_is_compared_once(started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME,
                                        partitions=[{"dt": "2026-09-24"}]))
    assert report.count(f"{DEV}: passed") == 1
    assert compared(started).count("Compared at ") == 1


def test_partition_is_refused_naming_partitions(started: Path) -> None:
    # Toolbox 8.5, ticket 04: one way to give a Partition, a list of them.
    with pytest.raises(TypeError, match=r"was given partition=, which Toolbox 8\.5 replaced"
                       r"[\s\S]*partitions=\[\{'dt': '2026-09-23'\}\]"):
        project.compare_batch("failed", query=SAME, partition={"dt": "2026-09-23"})


def test_a_finished_batch_compares_again_saying_so(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    report = repr(project.compare_batch("failed", query=SAME,
                                        partitions=[{"dt": "2026-09-23"}]))
    assert ("The batch was finished already, in admin/workflows/convert/finished/failed/"
            in report)
    assert "## dt = '2026-09-23'" in compared(started)


@pytest.mark.parametrize("given, said", [
    ([{"dt": "'2026-09-23'"}], "partitions= gives dt in quotes of its own"),
    ([{"dt": '"2026-09-23"'}], "partitions= gives dt in quotes of its own"),
    (["2026-09-23"], "partitions= holds '2026-09-23', not a dict of each partition column's "
     "value"),
    # 8.4's PARTITION, one dict, given as PARTITIONS.
    ({"dt": "2026-09-23"}, r"partitions= is \{'dt': '2026-09-23'\}, not a list of Partitions"),
], ids=["quoted", "double quoted", "not a dict", "not a list"])
def test_a_partition_not_as_show_partitions_lists_it_is_refused(
        started: Path, given: object, said: str) -> None:
    # Toolbox 8.3: step 2 teaches a bare tag's own quotes; a Partition's value takes none.
    with pytest.raises((ValueError, TypeError), match=said):
        project.compare_batch("failed", query=SAME, partitions=given)


def test_the_compare_names_partitions_to_compare_another(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    assert ('to compare one, add it to PARTITIONS, such as PARTITIONS = [{"dt": "..."}], in '
            "the convert notebook's names cell, run it, and run step 6 again"
            ) in compared(started)


def test_a_compare_of_another_partition_keeps_the_first_result_beside_it(started: Path) -> None:
    project.compare_batch("failed", query=SAME)
    project.compare_batch("failed", query=SAME, partitions=[{"dt": "2026-09-23"}])
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
    project.compare_batch("failed", query=fewer, partitions=[{"dt": "2026-09-23"}])
    workflows = toolbox_module("workflows")
    # One Partition failing fails the table, though the other passed.
    assert not workflows.compare_passed(started, DEV)
    project.compare_batch("failed", query=SAME, partitions=[{"dt": "2026-09-23"}])
    text = compared(started)
    assert text.count("## dt = '2026-09-23'") == 1 and "Failed: " not in text
    assert workflows.compare_passed(started, DEV)


def test_a_partition_that_failed_fails_the_table_beside_one_that_passed(started: Path) -> None:
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-23'")["run_id"][0]
    fewer = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                      {DEV: f"{FAILED_ROWS} AND run_id <> {left_out}", ORIGINAL: FAILED_ROWS})
    project.compare_batch("failed", query=fewer, partitions=[{"dt": "2026-09-23"}])
    project.compare_batch("failed", query=SAME)
    text = compared(started)
    assert "## dt = '2026-09-23'\n\nFailed: " in text
    assert "## dt = '2026-09-24'\n\nPassed: " in text
    assert not toolbox_module("workflows").compare_passed(started, DEV)
    # A result that failed is listed before one that passed (Toolbox 8.10, ticket 03).
    late = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-24'")["run_id"][0]
    fewer_late = warehouse({DEV: BOTH_DAYS, ORIGINAL: BOTH_DAYS},
                           {DEV: f"{FAILED_ROWS} AND run_id <> {late}", ORIGINAL: FAILED_ROWS})
    project.compare_batch("failed", query=fewer_late, partitions=[{"dt": "2026-09-23"}])
    text = compared(started)
    assert text.index("## dt = '2026-09-24'\n\nFailed: ") < text.index(
        "## dt = '2026-09-23'\n\nPassed: ")


def test_a_compare_md_from_before_8_2_is_read_then_written_over(started: Path) -> None:
    path = started / "tables" / "mart_dev__failed_ops_reports" / "conversion" / "compare.md"
    path.write_text(f"# {DEV} against {ORIGINAL}\n\nPassed: compared on dt = '2026-09-24', the "
                    "latest Partition both hold.\nCompared at 2026-10-31 09:30:00.\n",
                    encoding="utf-8")
    workflows = toolbox_module("workflows")
    assert workflows.compare_passed(started, DEV)
    project.compare_batch("failed", query=SAME, partitions=[{"dt": "2026-09-23"}])
    text = compared(started)
    # The result 8.1 wrote names no Partition, so the new ones, which do, take its place.
    assert text.count("Compared at ") == 2 and "## dt = '2026-09-23'" in text


def test_a_result_from_before_the_table_was_written_again_is_dropped(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project.compare_batch("failed", query=SAME, partitions=[{"dt": "2026-09-23"}])
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
    assert step.call == "project.compare_batch(NAME, query=query, partitions=PARTITIONS)"


def test_the_compare_step_says_it_checks_the_latest_partition_and_how_to_check_another(
        ) -> None:
    # Toolbox 8.2, 23: H1 had to find partition= for itself.
    step = toolbox_module("workflows").CONVERT.steps[-1]
    assert "on the latest Partition both hold" in step.goal
    assert "If you want other Partitions compared too, each one your dev table holds" in (
        step.action)
    assert "each value with no quotes of its own, run the names cell" in step.action
    # Toolbox 8.3, 06: set in the names cell, with no cell of your own.
    assert '`[{"dt": "2026-09-23"}]`' in step.action
    assert "in a new cell" not in step.action


def test_the_write_steps_seed_says_why_a_table_has_none_and_sends_nothing(
        started: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Toolbox 8.2, 23: W1-1 saw the seed cell send its Session setting, and say nothing,
    # though no table of the batch reads itself. 8.10, ticket 05: the Seed is the write step's
    # first line, and says why a table that is no History table has none.
    notebook = started / "admin" / "workflows" / "convert" / "convert.ipynb"
    code = [text for kind, text in toolbox_module("notebooks").read_cells(notebook)
            if kind == "code"]
    write = toolbox_module("workflows").CONVERT.steps[4]
    assert write.call in code
    seed_line = write.call.split("\nproject.run_tables(")[0]
    said = run_admin_notebook(notebook, [code[0], 'NAME = "failed"', seed_line], capsys)
    assert said == ("mart_dev.failed_ops_reports: no Seed, as its Table reference says no "
                    "kind, Rebuilt or History.\n")
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
    with pytest.raises(ValueError, match="partitions= names day, which no table it compares"):
        project.compare_batch("failed", query=SAME, partitions=[{"day": "2026-09-23"}])


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


def test_a_partition_you_give_that_neither_holds_fails_and_still_finishes_the_batch(
        started: Path) -> None:
    report = repr(project.compare_batch("failed", query=SAME,
                                        partitions=[{"dt": "2030-01-01"}]))
    assert (f"{DEV}: failed, there is no Partition where dt = '2030-01-01' in {DEV} and "
            f"{ORIGINAL}: list one both hold") in report
    assert "The batch is finished, though not every table passed" in report


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


# --- A query alone, its params filled before it is sent (Toolbox 8.10, ticket 03) -----------

ALONE = "mart_dev.alone"
# A query alone, as someone else's program runs it: a bare tag and a quoted one, which the
# program fills, and a Hivevar its SET line gives.
ALONE_HIVE = """\
SET hivevar:min_mins=15;
SELECT r.run_id, r.status FROM ops.job_runs r
WHERE r.dt = <PARM="RUN_DAY"/> AND r.status <> '<PARM="SKIP"/>'
AND r.duration_mins >= ${hivevar:min_mins}
"""
# Its dev table's rows, once written with RUN_DAY '2026-09-24' and SKIP FAILED, read by an
# alias of their own.
ALONE_ROWS = ("SELECT c.run_id, c.status FROM ops.job_runs c WHERE c.dt = '2026-09-24' "
              "AND c.status <> 'FAILED' AND c.duration_mins >= 15")
RUN_VALUES = '''import datetime


def run_day() -> datetime.date:
    """The day each write reads."""
    return datetime.date(2026, 9, 24)


def skipped_status() -> str:
    """The status each write leaves out."""
    return "FAILED"
'''


def sending(rows: dict[str, str]) -> tuple[Callable[[str], pd.DataFrame], list[str]]:
    """A query reading the Example database, each table `rows` names read as its Hive, and
    the list it keeps of each Hive it is sent."""
    sent: list[str] = []
    read = warehouse({}, rows)

    def query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return read(hive)
    return query, sent


def alone_compared(root: Path) -> str:
    return (root / "tables" / "mart_dev__alone" / "conversion" / "compare.md").read_text(
        encoding="utf-8")


@pytest.fixture
def alone(started: Path) -> Path:
    """The Project, with ALONE_HIVE converted as a batch of its own, alone, and the Run values
    of building_blocks/run_values.py there to answer its tags."""
    (started / "alone.hql").write_text(ALONE_HIVE, encoding="utf-8")
    project.convert("alone", files=["alone.hql"], query=example_database.query,
                    database="ops")
    (started / "building_blocks" / "run_values.py").write_text(RUN_VALUES, encoding="utf-8")
    return started


def answered_and_written(answers: dict[str, object]) -> None:
    """Answer ALONE's tags and its location, then write it in dev, as the convert Workflow's
    steps 3 and 6 do."""
    project.write_decisions({ALONE: {"tags": answers, "location": "/data/dev/alone"}})
    project.run_tables(tables=[ALONE], execute=example_database.execute)


def test_a_query_alones_tags_and_hivevar_are_filled_and_its_run_value_is_as_written(
        alone: Path) -> None:
    from building_blocks.run_values import run_day

    answered_and_written({"RUN_DAY": run_day, "SKIP": "FAILED"})
    # The Run value gives another day now: the compare reads the one the write used.
    values = alone / "building_blocks" / "run_values.py"
    values.write_text(RUN_VALUES.replace("2026, 9, 24", "2026, 9, 23"), encoding="utf-8")
    query, sent = sending({ALONE: ALONE_ROWS})
    report = repr(project.compare_batch("alone", query=query))
    assert f"{ALONE}: passed, every row: it has no Partitions" in report
    assert "Every table the batch wrote passed, so it is finished" in report
    [compared_hive] = sent
    assert "<PARM" not in compared_hive and "${hivevar" not in compared_hive
    assert "r.dt = '2026-09-24'" in compared_hive
    assert "r.status <> 'FAILED'" in compared_hive
    assert "r.duration_mins >= 15" in compared_hive
    # A passing compare reads as it did before 8.10: no warning.
    assert "Warning" not in alone_compared(alone)


def test_a_bare_tags_hivevar_and_a_quoted_tags_run_value_are_filled(alone: Path) -> None:
    from building_blocks.run_values import skipped_status

    answered_and_written({"RUN_DAY": hivevar("RUN_DAY", default="'2026-09-24'"),
                          "SKIP": skipped_status})
    query, sent = sending({ALONE: ALONE_ROWS})
    assert f"{ALONE}: passed, every row" in repr(project.compare_batch("alone", query=query))
    assert "r.dt = '2026-09-24'" in sent[0] and "r.status <> 'FAILED'" in sent[0]


def test_a_tag_no_answer_fills_skips_the_compare_saying_why(alone: Path) -> None:
    query, sent = sending({ALONE: ALONE_ROWS})
    report = repr(project.compare_batch("alone", query=query))
    said = ('not compared: it holds <PARM="RUN_DAY"/> and <PARM="SKIP"/>, which only your '
            "program fills")
    assert f"{ALONE}: {said}" in report
    assert sent == [], "a query was sent that couldn't run"
    text = alone_compared(alone)
    assert (f"Warning: {ALONE} wasn't compared: it holds <PARM=\"RUN_DAY\"/> and "
            "<PARM=\"SKIP\"/>, which only your program fills. Nothing checked its rows: check "
            "them yourself before you promote it.") in text
    assert '## Every row\n\nNot compared: it holds <PARM="RUN_DAY"/>' in text
    assert "Checked at 2026-10-31 09:30:00." in text
    # A skip stops nothing either.
    assert (alone / "admin" / "workflows" / "convert" / "finished" / "alone").is_dir()
    assert f"{ALONE} wasn't compared" in report


def test_a_hivevar_no_set_line_gives_skips_the_compare(started: Path) -> None:
    project.convert("teams", "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24' "
                    "AND r.status <> '${hivevar:skip}'", query=example_database.query,
                    database="ops")
    query, sent = sending({})
    report = repr(project.compare_batch("teams", query=query))
    assert ("mart_dev.teams: not compared: it holds ${hivevar:skip}, which only your program "
            "fills: no SET line in its notebook's session_settings() gives it") in report
    assert sent == []


def test_a_run_value_with_no_value_recorded_skips_the_compare(alone: Path) -> None:
    from building_blocks.run_values import run_day

    # Answered, and never written since: no value of run_day() is recorded.
    project.write_decisions({ALONE: {"tags": {"RUN_DAY": run_day, "SKIP": "FAILED"}}})
    query, sent = sending({ALONE: ALONE_ROWS})
    report = repr(project.compare_batch("alone", query=query))
    assert (f'{ALONE}: not compared: its <PARM="RUN_DAY"/> is answered by run_day(), whose '
            f"value when {ALONE} was written isn't recorded: write {ALONE} again, then compare "
            "it") in report
    assert sent == []


def test_a_failed_compare_of_a_table_whose_tags_were_answered_says_why_it_may_differ(
        started: Path) -> None:
    tagged = FAILED.replace("r.dt = '2026-09-24'", 'r.dt = <PARM="RUN_DAY"/>').replace(
        "ops_reports.failed", "ops_reports.tagged")
    (started / "tagged.hql").write_text(tagged, encoding="utf-8")
    project.convert("tagged", files=["tagged.hql"], query=example_database.query,
                    database="ops")
    dev = "mart_dev.tagged_ops_reports"
    project.write_decisions({dev: {"tags": {"RUN_DAY": "'2026-09-24'"}}})
    left_out = example_database.query(f"{FAILED_ROWS} AND dt = '2026-09-24'")["run_id"][0]
    fewer = warehouse({dev: BOTH_DAYS, "ops_reports.tagged": BOTH_DAYS},
                      {dev: f"{FAILED_ROWS} AND run_id <> {left_out}",
                       "ops_reports.tagged": FAILED_ROWS})
    project.compare_batch("tagged", query=fewer)
    text = (started / "tables" / "mart_dev__tagged_ops_reports" / "conversion"
            / "compare.md").read_text(encoding="utf-8")
    assert ("Its Script tags were answered in the decisions cell (RUN_DAY): the original's "
            "last run may have used other values for them, which give other rows.") in text


def test_a_dry_run_of_the_compare_step_shows_the_query_alone_as_it_would_be_sent(
        alone: Path) -> None:
    from building_blocks.run_values import run_day

    answered_and_written({"RUN_DAY": run_day, "SKIP": "FAILED"})
    workflows = toolbox_module("workflows")
    said = "\n".join(workflows.compare_the_batch(
        {"NAME": "alone"}, workflows.Calls(query=None, execute=None, dry_run=True)))
    assert "would compare mart_dev.alone with its query, filled in as:" in said
    assert "r.dt = '2026-09-24' AND r.status <> 'FAILED'" in said
