"""The usability loop's harness (Toolbox 8.2, ticket 02).

A run's folder holds what a user has, built from what main ships; its warehouse keeps each
table between processes; its notebook runner runs cells as Run All does; a question goes to
Copilot as one chat, file 00 first; and a run's end is scored against its scenario's answer
key, failing on the check meant to catch each wrong end.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import re
import shutil
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import notebook_runner
import openpyxl
import pytest
import usability_loop
from conftest import forget_the_projects_modules, toolbox_module
from openpyxl.worksheet.table import Table
from workflow_warehouse import SavedWarehouse

from sqlglot_composer import notebooks, project

HIVE_RAN = """CREATE TABLE IF NOT EXISTS mart.daily_fails (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt = '2026-09-24')
SELECT r.job_id, COUNT(*) AS fails FROM ops.job_runs r
WHERE r.dt = '2026-09-24' AND r.status = 'FAILED' GROUP BY r.job_id;
"""
END = ("CREATE TABLE IF NOT EXISTS mart_dev.fails (job_id BIGINT, fails BIGINT); "
       "INSERT OVERWRITE TABLE mart_dev.fails SELECT job_id, fails FROM mart.daily_fails")


@pytest.fixture
def chosen(tmp_path: Path) -> usability_loop.Scenario:
    """A scenario, T1, whose key asks for mart_dev.fails, and one file holding DEV's name."""
    folder = tmp_path / "scenarios"
    (folder / "T1").mkdir(parents=True)
    (folder / "T1" / "ran.hql").write_text(HIVE_RAN, encoding="utf-8")
    (folder / "T1" / "daily.hql").write_text("SELECT 1 AS x", encoding="utf-8")
    (folder / "T1" / "scenario.json").write_text(json.dumps({
        "id": "T1", "split": "dev", "title": "a test scenario",
        "phases": [{"role": "technical", "job": "Copy mart.daily_fails into mart_dev.fails."},
                   {"role": "non_technical",
                    "job": "Fill in the workbook, as main/copilot/07_convert_hive.txt says."}],
        "hive_ran": ["ran.hql"], "given": {"from_your_team/daily.hql": "daily.hql"}}),
        encoding="utf-8")
    warehouse = SavedWarehouse(tmp_path / "key_warehouse.json")
    warehouse.execute(HIVE_RAN)
    warehouse.execute(END)
    rows = warehouse.rows_of("mart_dev.fails").values.tolist()
    (folder / "T1" / "key.json").write_text(json.dumps({
        "tables": {"mart_dev.fails": {"columns": ["job_id", "fails"], "rows": rows}},
        "files": [{"path": "admin/databases.py", "holds": ['DEV = "mart_dev"']}]}),
        encoding="utf-8")
    return usability_loop.read_scenario("T1", folder)


@pytest.fixture
def main_tree(tmp_path: Path) -> Path:
    """Enough of main for a run that isn't built: the Copilot files' start and one file."""
    main = tmp_path / "main_tree"
    (main / "copilot").mkdir(parents=True)
    for name in ("00_start_here.txt", "07_convert_hive.txt"):
        (main / "copilot" / name).write_text(
            (usability_loop.ROOT / "copilot" / name).read_text(encoding="utf-8"),
            encoding="utf-8")
    return main


@pytest.fixture(scope="session")
def built_main(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Main's tree, built from dev's last commit once for the session, as it takes a while
    (Toolbox 8.6, ticket 11)."""
    main = tmp_path_factory.mktemp("built") / "main"
    usability_loop.build_main(main, usability_loop.dev_commit())
    return main


def _prepared(chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> Path:
    return usability_loop.prepare(chosen, tmp_path / "run", main=main_tree,
                                  python=Path(sys.executable))


def _finish(run: Path, end: str = END, dev: str = "mart_dev") -> None:
    """The end a run's agents reach: `end` sent, and a Project whose DEV is `dev`."""
    SavedWarehouse(run / "_loop" / "warehouse.json").execute(end)
    (run / "my_project" / "admin").mkdir(parents=True)
    (run / "my_project" / "admin" / "registry.csv").write_text("", encoding="utf-8")
    (run / "my_project" / "admin" / "databases.py").write_text(f'DEV = "{dev}"\n',
                                                                encoding="utf-8")


def test_the_saved_warehouse_keeps_each_table_between_processes(tmp_path: Path) -> None:
    path = tmp_path / "warehouse.json"
    SavedWarehouse(path).execute(HIVE_RAN)
    reopened = SavedWarehouse(path)
    assert len(reopened.rows_of("mart.daily_fails")) > 0
    assert "ops.job_runs" not in json.loads(path.read_text(encoding="utf-8"))
    assert len(reopened.rows_of("ops.job_runs")) > 0


def test_the_runner_runs_each_cell_in_turn_from_the_notebooks_folder(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cells = ["import pathlib\nhere = pathlib.Path.cwd().name", "print('printed')", "here",
             "raise ValueError('stops here')", "print('never')"]
    notebook = tmp_path / "work" / "book.ipynb"
    notebook.parent.mkdir()
    code = [{"cell_type": "code", "source": [text]} for text in cells]
    notebook.write_text(json.dumps({"cells": [
        {"cell_type": "markdown", "source": ["# a heading"]}, *code]}), encoding="utf-8")
    assert notebook_runner.run_notebook(notebook) == 1
    shown = capsys.readouterr().out
    assert "printed" in shown and "'work'" in shown and "ValueError: stops here" in shown
    assert "--- stopped at cell 4" in shown and "never" not in shown


def test_a_run_holds_what_the_user_has_and_nothing_of_the_key(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    made = sorted(path.name for path in tmp_path.iterdir())
    assert made == ["key_warehouse.json", "main_tree", "run", "scenarios"]
    assert not list(run.rglob("key.json"))
    assert (run / "from_your_team" / "daily.hql").is_file()
    assert (run / "my_work").is_dir() and (run / "run_notebook.py").is_file()
    connection = (run / "team_connection.py").read_text(encoding="utf-8")
    assert repr(str(run / "_loop" / "warehouse.json")) in connection
    assert len(SavedWarehouse(run / "_loop" / "warehouse.json").rows_of("mart.daily_fails"))


def test_a_project_brought_in_reaches_the_team_connection_through_its_conn_line_alone(
        tmp_path: Path) -> None:
    # 8.2's warehouse.py names the line in a comment too: only the line itself is replaced.
    warehouse = tmp_path / "warehouse.py"
    warehouse.write_text(f"# in place of the line {usability_loop.EXAMPLE_CONN}, as it was\n"
                         f"{usability_loop.EXAMPLE_CONN}\n", encoding="utf-8")
    usability_loop.connect_the_team(tmp_path)
    written = warehouse.read_text(encoding="utf-8")
    assert written.startswith(f"# in place of the line {usability_loop.EXAMPLE_CONN}, as it")
    assert written.count("from team_connection import conn") == 1
    ast.parse(written)


def test_a_project_brought_in_reaches_the_team_connection_through_each_connect_line(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Toolbox 8.6: each notebook connects at its top, so each notebook's line, and each
    # Template's, is the one filled in, and warehouse.py is left as start() wrote it.
    root = tmp_path / "my_project"
    root.mkdir()
    monkeypatch.chdir(root)
    project.start()
    warehouse = (root / "warehouse.py").read_text(encoding="utf-8")
    usability_loop.connect_the_team(root)
    assert (root / "warehouse.py").read_text(encoding="utf-8") == warehouse
    notebook = root / "admin" / "workflows" / "references" / "references.ipynb"
    setup = notebooks.read_cells(notebook)[1][1]
    assert f"sys.path.append({str(tmp_path)!r})" in setup
    assert "from team_connection import conn\nconnect(conn)" in setup
    assert "# connect(your_connection)" not in setup
    ast.parse(setup)
    template = (root / "admin" / "templates" / "saved_table.py").read_text(encoding="utf-8")
    assert "from team_connection import conn\nconnect(conn)" in template


def test_each_phases_message_gives_its_role_what_that_person_has(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    technical = (run / "_loop" / "phase_1.md").read_text(encoding="utf-8")
    assert "Copy mart.daily_fails into mart_dev.fails." in technical
    assert "QUESTION: " in technical and "DONE: " in technical and "_loop/" in technical
    assert "run_notebook.py" in technical and "team_connection" in technical
    excel = (run / "_loop" / "phase_2.md").read_text(encoding="utf-8")
    assert "openpyxl" in excel and "my_work/" in excel
    assert "run_notebook.py" not in excel and "team_connection" not in excel


def test_preparing_without_the_agents_python_is_refused(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="docs/usability-loop.md"):
        usability_loop.prepare(chosen, tmp_path / "run", main=main_tree,
                               python=tmp_path / "no_python.exe")


def test_a_run_whose_end_is_the_keys_passes(chosen: usability_loop.Scenario, main_tree: Path,
                                            tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    _finish(run)
    result = usability_loop.score(chosen, run)
    assert result.passed, usability_loop.report_text(result, run)
    assert result.project == run / "my_project"


def test_a_run_missing_a_table_or_a_file_fails(chosen: usability_loop.Scenario,
                                               main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    result = usability_loop.score(chosen, run)
    assert result.missing_tables == ["mart_dev.fails"] and not result.passed
    assert result.missing_files == ["admin/databases.py"]


@pytest.mark.parametrize(("end", "dev", "check"), [
    pytest.param(END.replace("SELECT job_id, fails", "SELECT job_id, fails + 1 AS fails"),
                 "mart_dev", "other_rows", id="other_rows"),
    pytest.param(END.replace("SELECT job_id, fails", "SELECT CAST(job_id AS STRING) AS job_id,"
                                                      " fails"), "mart_dev", "other_rows",
                 id="numbers_as_text"),
    pytest.param(END.replace("(job_id BIGINT, fails BIGINT)",
                             "(job_id BIGINT, fails BIGINT, note STRING)").replace(
        "SELECT job_id, fails", "SELECT job_id, fails, 'x' AS note"), "mart_dev",
                 "other_columns", id="an_extra_column"),
    pytest.param(END, "mart", "missing_files", id="a_file_without_its_text"),
])
def test_a_wrong_end_fails_on_the_check_meant_to_catch_it(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path, end: str, dev: str,
        check: str) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    _finish(run, end, dev)
    result = usability_loop.score(chosen, run)
    assert getattr(result, check) and not result.passed, usability_loop.report_text(result, run)


def test_more_questions_than_a_run_may_ask_fail_it(chosen: usability_loop.Scenario,
                                                   main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    _finish(run)
    for number in range(usability_loop.MOST_QUESTIONS + 1):
        usability_loop.route(run, f"question {number}")
    result = usability_loop.score(chosen, run)
    assert result.questions == usability_loop.MOST_QUESTIONS + 1 and not result.passed


def test_a_question_is_one_chat_file_00_first_then_the_file_it_names(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    message, reply = usability_loop.route(run, "How do I convert a script?")
    routed = message.read_text(encoding="utf-8")
    assert "Copilot files for sqlglot Composer" in routed and "## Q1" in routed
    assert "How do I convert a script?" in routed and "one Copilot file" in routed
    assert reply.name == "question_1_route_reply.md"
    answered = usability_loop.answer(run, 1, ["07_convert_hive.txt"])[0].read_text(
        encoding="utf-8")
    assert "Copilot files for sqlglot Composer" in answered
    assert "Copilot file 07" in answered and "How do I convert a script?" in answered
    assert "You replied: load 07_convert_hive.txt" in answered
    several = usability_loop.answer(run, 1, ["00_start_here.txt", "07_convert_hive.txt"])
    assert "load 00_start_here.txt and 07_convert_hive.txt" in several[0].read_text(
        encoding="utf-8")


def test_a_workbook_is_attached_as_copilot_reads_it(chosen: usability_loop.Scenario,
                                                    main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Runs"
    for row in (["job_id", "fails", "double"], [1, 2, "=[@fails]*2"]):
        sheet.append(row)
    sheet.add_table(Table(displayName="runs", ref="A1:C2"))
    workbook.save(run / "my_work" / "book.xlsx")
    usability_loop.route(run, "How do I turn my workbook into Hive?")
    attached = usability_loop.answer(run, 1, ["07_convert_hive.txt"],
                                     [Path("my_work/book.xlsx")])[0].read_text(encoding="utf-8")
    assert 'Sheet "Runs"' in attached and 'Excel Table "runs", A1:C2' in attached
    assert "=[@fails]*2" in attached


def test_an_attached_tables_total_row_is_named_as_the_excel_eval_names_it(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    run = _prepared(chosen, main_tree, tmp_path)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in (["job_id", "fails"], [1, 2], ["Total", "=SUBTOTAL(109,runs[fails])"]):
        sheet.append(row)
    table = Table(displayName="runs", ref="A1:B3")
    table.totalsRowCount = 1
    sheet.add_table(table)
    workbook.save(run / "my_work" / "book.xlsx")
    usability_loop.route(run, "How do I turn my workbook into Hive?")
    attached = usability_loop.answer(run, 1, ["07_convert_hive.txt"],
                                     [Path("my_work/book.xlsx")])[0].read_text(encoding="utf-8")
    assert "Headers: job_id | fails" in attached and "Row 2: 1 | 2" in attached
    assert "Total Row: Total | =SUBTOTAL(109,runs[fails])" in attached


def test_a_run_built_from_dev_holds_mains_tree(built_main: Path) -> None:
    assert (built_main / "sqlglot_composer" / "version.txt").is_file()
    assert (built_main / ".github" / "README.md").is_file()
    assert (built_main / "copilot" / "formula_workbook.xlsx").is_file()
    assert not (built_main / "tools").exists() and not (built_main / ".scratch").exists()


def test_mains_tree_hashes_the_same_whenever_it_was_built(built_main: Path,
                                                          tmp_path: Path) -> None:
    # Toolbox 8.6, ticket 11: the export stamps when it ran, and from which commit, in
    # version.txt and the README; the tree's hash leaves the stamp out, so a commit that
    # changes nothing main ships keeps it.
    hashed = usability_loop.main_tree_hash(built_main)
    again = tmp_path / "main"
    shutil.copytree(built_main, again)
    version = again / "sqlglot_composer" / "version.txt"
    text = version.read_text(encoding="utf-8")
    stamp = re.search(r"exported [^\n]*", text)[0]
    version.write_text(text.replace(stamp, f"exported 2027-01-01 00:00 from dev commit "
                                           f"{'0' * 40}"), encoding="utf-8", newline="\n")
    assert usability_loop.main_tree_hash(again) == hashed
    (again / "copilot" / "00_start_here.txt").write_text("changed\n", encoding="utf-8")
    assert usability_loop.main_tree_hash(again) != hashed


# --- Inputs recorded, and memoized (Toolbox 8.6, ticket 11) ----------------------------------


def _inputs(run: Path) -> dict[str, object]:
    return json.loads((run / "_loop" / "inputs.json").read_text(encoding="utf-8"))


def test_a_run_records_its_inputs_the_same_for_each_run_given_the_same(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path) -> None:
    first = usability_loop.prepare(chosen, tmp_path / "run_1", main=main_tree,
                                   python=Path(sys.executable))
    second = usability_loop.prepare(chosen, tmp_path / "run_2", main=main_tree,
                                    python=Path(sys.executable))
    inputs = _inputs(first)
    assert inputs["scenario"] == "T1" and inputs["commit"] == usability_loop.dev_commit()
    assert sorted(inputs["scenario_files"]) == ["daily.hql", "key.json", "ran.hql",
                                                "scenario.json"]
    assert len(inputs["phases"]) == 2 and inputs["project"] == {}
    # The files of main the phases name: the README every message names, absent from this
    # tree, and the Copilot file phase 2's job names.
    assert list(inputs["main"]["named"]) == ["copilot/07_convert_hive.txt"]
    assert len(inputs["inputs_hash"]) == 64
    assert _inputs(second)["inputs_hash"] == inputs["inputs_hash"]


@pytest.mark.parametrize("changed", ["a file of main", "a file of the scenario"])
def test_a_runs_inputs_hash_changes_with_any_of_its_inputs(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path, changed: str) -> None:
    before = usability_loop.prepare(chosen, tmp_path / "run_1", main=main_tree,
                                    python=Path(sys.executable))
    if changed == "a file of main":
        (main_tree / "copilot" / "07_convert_hive.txt").write_text("changed\n",
                                                                    encoding="utf-8")
    else:
        (chosen.folder / "T1" / "daily.hql").write_text("SELECT 2 AS x", encoding="utf-8")
    after = usability_loop.prepare(chosen, tmp_path / "run_2", main=main_tree,
                                   python=Path(sys.executable))
    assert _inputs(after)["inputs_hash"] != _inputs(before)["inputs_hash"]


def test_a_project_brought_in_is_recorded_file_by_file_without_the_toolbox(
        tmp_path: Path, main_tree: Path) -> None:
    folder = tmp_path / "scenarios"
    (folder / "T2").mkdir(parents=True)
    (folder / "T2" / "scenario.json").write_text(json.dumps({
        "id": "T2", "split": "dev", "title": "a Project brought in",
        "phases": [{"role": "technical", "job": "Change my_project."}],
        "project": "example_projects/starter"}), encoding="utf-8")
    (folder / "T2" / "key.json").write_text("{}", encoding="utf-8")
    chosen = usability_loop.read_scenario("T2", folder)
    run = usability_loop.prepare(chosen, tmp_path / "run", main=main_tree,
                                 python=Path(sys.executable))
    recorded = _inputs(run)["project"]
    assert "admin/registry.csv" in recorded and "warehouse.py" in recorded
    assert not [path for path in recorded if path.startswith("sqlglot_composer/")]
    assert (run / "my_project" / "sqlglot_composer").is_dir()


def _fake_build(builds: list[str]) -> Callable[[Path, str], None]:
    """A stand-in for build_main that notes each commit it builds and writes a README."""
    def build(into: Path, commit: str) -> None:
        builds.append(commit)
        (into / ".github").mkdir(parents=True)
        (into / ".github" / "README.md").write_text("# main\n", encoding="utf-8")
    return build


def test_a_cache_builds_mains_tree_once_per_commit_and_each_warehouse_once_per_scenario(
        chosen: usability_loop.Scenario, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    builds: list[str] = []
    monkeypatch.setattr(usability_loop, "build_main", _fake_build(builds))
    set_ups: list[str] = []
    set_up = usability_loop.set_up_the_scenario

    def counted_set_up(chosen: usability_loop.Scenario, set_up_folder: Path,
                       main_tree: Path) -> None:
        set_ups.append(chosen.id)
        set_up(chosen, set_up_folder, main_tree)

    monkeypatch.setattr(usability_loop, "set_up_the_scenario", counted_set_up)
    cache = tmp_path / "cache"
    (cache / "main" / ("0" * 40)).mkdir(parents=True)  # another commit's, dropped
    runs = [usability_loop.prepare(chosen, tmp_path / f"run_{number}", cache=cache,
                                   python=Path(sys.executable)) for number in (1, 2)]
    commit = usability_loop.dev_commit()
    assert builds == [commit] and len(set_ups) == 1
    assert sorted(path.name for path in (cache / "main").iterdir()) == [commit]
    for run in runs:
        assert (run / "main" / ".github" / "README.md").is_file()
        connection = (run / "team_connection.py").read_text(encoding="utf-8")
        assert repr(str(run / "_loop" / "warehouse.json")) in connection
    # Each run has a copy of its own: what one writes, no other run sees.
    SavedWarehouse(runs[0] / "_loop" / "warehouse.json").execute(END)
    third = usability_loop.prepare(chosen, tmp_path / "run_3", cache=cache,
                                   python=Path(sys.executable))
    assert "mart_dev.fails" not in json.loads(
        (third / "_loop" / "warehouse.json").read_text(encoding="utf-8"))
    assert _inputs(third)["inputs_hash"] == _inputs(runs[0])["inputs_hash"]


def test_two_builds_racing_on_one_place_leave_one_whole_folder(tmp_path: Path) -> None:
    # The code review (2026-11-09): two prepares at once each built into one .building folder,
    # the second deleting the first's. Each builds into a folder of its own now, and the one
    # that reaches the place second discards its own.
    place = tmp_path / "cache" / "main" / "a_commit"
    both_building = threading.Barrier(2)

    def build(into: Path) -> None:
        into.mkdir()
        both_building.wait(timeout=10)  # each is part way through when the other is
        for number in range(20):
            (into / f"file_{number}.txt").write_text(f"{number}\n", encoding="utf-8")

    returned: list[Path] = []

    def race() -> None:
        returned.append(usability_loop.build_in_place(place, build))

    threads = [threading.Thread(target=race) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert returned == [place, place]
    assert [path.name for path in place.parent.iterdir()] == ["a_commit"]
    assert sorted(path.name for path in place.iterdir()) == sorted(
        f"file_{number}.txt" for number in range(20))


def test_a_prepare_waits_for_the_caches_lock_and_refuses_once_it_has_waited_too_long(
        chosen: usability_loop.Scenario, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    # The code review (2026-11-09): a prepare building a new commit's tree dropped the other
    # commits' caches, though another prepare might be copying from one.
    builds: list[str] = []
    monkeypatch.setattr(usability_loop, "build_main", _fake_build(builds))
    monkeypatch.setattr(usability_loop, "LOCK_WAIT", 0.2)
    monkeypatch.setattr(usability_loop, "LOCK_POLL", 0.05)
    cache = tmp_path / "cache"
    other = cache / "main" / ("0" * 40)
    other.mkdir(parents=True)
    with usability_loop.hold_the_cache(cache):
        with pytest.raises(TimeoutError, match="prepare.lock"):
            usability_loop.prepare(chosen, tmp_path / "run_1", cache=cache,
                                   python=Path(sys.executable))
        assert other.is_dir() and builds == []
    monkeypatch.setattr(usability_loop, "LOCK_WAIT", 30)
    held = threading.Event()

    def hold_a_moment() -> None:
        with usability_loop.hold_the_cache(cache):
            held.set()
            time.sleep(0.3)

    holder = threading.Thread(target=hold_a_moment)
    holder.start()
    held.wait(timeout=10)
    run = usability_loop.prepare(chosen, tmp_path / "run_2", cache=cache,
                                 python=Path(sys.executable))
    holder.join(timeout=10)
    assert builds == [usability_loop.dev_commit()] and not other.exists()
    assert (run / "main" / ".github" / "README.md").is_file()
    assert not (cache / usability_loop.LOCK).exists()


RESULTS_HEAD = ("| date | scenario | split | run | result | questions | note |\n"
                "|---|---|---|---|---|---|---|\n"
                "| 2026-11-06 | T1 | dev | 2026-11-06-T1-1 | pass | 0 | 8.5 round; 5 actions "
                "|\n")


def _row(run: str, result: str, inputs: str, scenario: str = "T1") -> str:
    return (f"| 2026-11-10 | {scenario} | dev | {run} | {result} | 0 | a round; 3 actions; "
            f"inputs {inputs[:16]} |\n")


@pytest.mark.parametrize(("rows", "memoized", "said"), [
    pytest.param(["a pass", "b pass", "c pass"], True,
                 "T1: memoized: 3 runs passed with these inputs", id="three_passed"),
    pytest.param(["a pass", "b pass"], False, "T1: run it: 2 of 3 runs passed", id="two"),
    pytest.param(["a pass", "b pass", "c pass", "d fail"], False, "T1: run it: d failed",
                 id="one_failed"),
    pytest.param([], False, "T1: run it: no run recorded with these inputs", id="none"),
])
def test_plan_says_whether_a_scenario_is_memoized_naming_its_runs(
        chosen: usability_loop.Scenario, tmp_path: Path, rows: list[str], memoized: bool,
        said: str) -> None:
    inputs = "ab" * 32
    results = tmp_path / "results.md"
    text = RESULTS_HEAD + _row("e", "pass", "cd" * 32) + _row("f", "pass", inputs, "T9")
    for each in rows:
        run, result = each.split()
        text += _row(run, result, inputs)
    results.write_text(text, encoding="utf-8")
    recorded = usability_loop.read_recorded_runs(results)
    assert usability_loop.is_memoized(chosen, inputs, recorded) is memoized
    planned = usability_loop.plan_text(chosen, inputs, recorded)
    assert planned.startswith(said) and inputs[:16] in planned
    if memoized:
        assert planned.endswith("a, b and c")


def test_a_held_out_scenario_is_memoized_by_one_run_that_passed(
        chosen: usability_loop.Scenario, tmp_path: Path) -> None:
    held_out = dataclasses.replace(chosen, split="held_out")
    inputs = "ab" * 32
    results = tmp_path / "results.md"
    results.write_text(RESULTS_HEAD + _row("a", "pass", inputs), encoding="utf-8")
    recorded = usability_loop.read_recorded_runs(results)
    assert usability_loop.is_memoized(held_out, inputs, recorded)


def test_a_recorded_run_names_its_inputs_and_a_memoized_scenario_isnt_prepared_unless_fresh(
        chosen: usability_loop.Scenario, main_tree: Path, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usability_loop, "KEPT", tmp_path / "kept")
    monkeypatch.setattr(usability_loop, "RESULTS", tmp_path / "kept" / "results.md")
    for number in (1, 2, 3):
        run = usability_loop.prepare(chosen, tmp_path / f"T1-{number}", main=main_tree,
                                     python=Path(sys.executable))
        _finish(run)
        row = usability_loop.record(usability_loop.score(chosen, run), run, chosen)
        assert f"; inputs {_inputs(run)['inputs_hash'][:16]} |" in row
    with pytest.raises(ValueError, match="--fresh"):
        usability_loop.prepare(chosen, tmp_path / "T1-4", main=main_tree,
                               python=Path(sys.executable))
    assert not (tmp_path / "T1-4").exists()
    again = usability_loop.prepare(chosen, tmp_path / "T1-5", main=main_tree,
                                   python=Path(sys.executable), fresh=True)
    assert (again / "_loop" / "inputs.json").is_file()
    planned = usability_loop.plan(chosen, cache=None, main=main_tree)
    assert planned.startswith("T1: memoized: 3 runs passed")
    assert planned.endswith("T1-1, T1-2 and T1-3")


@pytest.mark.parametrize("path_first", [True, False], ids=["path first", "path last"])
def test_the_runner_runs_only_the_cells_it_is_given(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], path_first: bool) -> None:
    # A Workflow's cells run one at a time, to stop at a decision, as the README says. Ticket
    # 21: --cells works before the path too, as W4-2 and W3-1 wrote it.
    notebook = tmp_path / "book.ipynb"
    code = [{"cell_type": "code", "source": [f"print('cell {number}')"]}
            for number in (1, 2, 3, 4)]
    notebook.write_text(json.dumps({"cells": code}), encoding="utf-8")
    arguments = ["--cells", "1-2,4"]
    arguments = [str(notebook), *arguments] if path_first else [*arguments, str(notebook)]
    assert notebook_runner.main(arguments) == 0
    shown = capsys.readouterr().out
    assert "cell 1" in shown and "cell 2" in shown and "cell 4" in shown
    assert "cell 3" not in shown


@pytest.mark.parametrize("path_first", [True, False], ids=["path first", "path last"])
def test_the_runner_lists_each_code_cell_by_its_number_and_first_line(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], path_first: bool) -> None:
    # So a step's cell is found by its number, text cells left out as --cells leaves them.
    # Ticket 21: --list before the path printed only the usage line (W4-2, W3-1).
    notebook = tmp_path / "book.ipynb"
    cells = [{"cell_type": "markdown", "source": ["# Steps"]},
             {"cell_type": "code", "source": ["import pathlib\n", "x = 1"]},
             {"cell_type": "markdown", "source": ["## Step 1"]},
             {"cell_type": "code", "source": ["# names\n", "TABLES = []"]}]
    notebook.write_text(json.dumps({"cells": cells}), encoding="utf-8")
    arguments = [str(notebook), "--list"] if path_first else ["--list", str(notebook)]
    assert notebook_runner.main(arguments) == 0
    assert capsys.readouterr().out == "1: import pathlib\n2: # names\n"


def _tagged_notebook(path: Path, tagged: bool = True) -> Path:
    """A notebook whose first code cell is its parameters cell, tagged as papermill finds it
    when `tagged`, and whose second prints what WEEK is."""
    tags = {"tags": ["parameters"]} if tagged else {}
    cells = [{"cell_type": "code", "metadata": tags,
              "source": ["# parameters\n", "WEEK = None"]},
             {"cell_type": "code", "metadata": {}, "source": ["print(repr(WEEK))"]}]
    path.write_text(json.dumps({"cells": cells}), encoding="utf-8")
    return path


def test_the_runner_gives_each_parameter_as_text_after_the_parameters_cell(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Toolbox 8.6, ticket 11: as papermill's -p puts a cell after the cell tagged parameters,
    # so a Scheduled run is run as a scheduler runs it.
    notebook = _tagged_notebook(tmp_path / "run.ipynb")
    assert notebook_runner.main([str(notebook), "-p", "WEEK", "2026-09-16"]) == 0
    shown = capsys.readouterr().out
    assert "--- parameters given: WEEK" in shown and "'2026-09-16'" in shown
    assert notebook_runner.main(["-p", "WEEK", "2026-09-16", str(notebook)]) == 0


def test_the_runner_refuses_a_parameter_with_no_tagged_cell_to_follow(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    notebook = _tagged_notebook(tmp_path / "run.ipynb", tagged=False)
    assert notebook_runner.main([str(notebook), "-p", "WEEK", "2026-09-16"]) == 1
    assert "no code cell tagged parameters" in capsys.readouterr().out


def test_the_runner_refuses_parameters_when_cells_leaves_out_the_tagged_cell(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # The drift review (2026-11-09): -p with --cells 2 dropped WEEK without a word.
    notebook = _tagged_notebook(tmp_path / "run.ipynb")
    assert notebook_runner.main([str(notebook), "--cells", "2", "-p", "WEEK", "x"]) == 1
    shown = capsys.readouterr().out
    assert "code cell 1, tagged parameters" in shown and "--cells" in shown
    assert "--- cell" not in shown
    assert notebook_runner.main([str(notebook), "--cells", "1-2", "-p", "WEEK", "x"]) == 0


@pytest.mark.parametrize("arguments", [[], ["a.ipynb", "b.ipynb"], ["--cells", "a.ipynb"],
                                       ["a.ipynb", "--list", "--cells", "1"],
                                       ["a.ipynb", "-p", "WEEK"]],
                         ids=["no path", "two paths", "no cells", "both", "no value"])
def test_the_runner_says_how_to_run_it_when_its_arguments_dont_fit(
        arguments: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert notebook_runner.main(arguments) == 2
    assert capsys.readouterr().out.startswith("Run it as: python run_notebook.py")


def test_the_saved_warehouse_answers_a_select_of_values_and_keeps_a_location(
        tmp_path: Path) -> None:
    path = tmp_path / "warehouse.json"
    warehouse = SavedWarehouse(path)
    assert warehouse.query("SELECT 1 AS one").values.tolist() == [[1]]
    warehouse.execute("CREATE EXTERNAL TABLE mart_dev.kept (a BIGINT) LOCATION '/data/kept'")
    described = SavedWarehouse(path).query("DESCRIBE FORMATTED mart_dev.kept")
    assert ["Location:", "/data/kept"] in described.iloc[:, :2].values.tolist()


def test_a_run_that_adds_a_cell_to_a_workflow_notebook_is_scored_with_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Toolbox 8.4, ticket 14: on the intended path a user makes no cell of their own.
    monkeypatch.chdir(tmp_path)
    project = toolbox_module().project
    notebooks = toolbox_module("notebooks")
    project.start()
    result = usability_loop.RunScore("W7", project=tmp_path)
    usability_loop.check_cells(result)
    assert result.added_cells == []
    notebook = tmp_path / "admin" / "workflows" / "convert" / "convert.ipynb"
    notebooks.write_notebook(notebook, [*notebooks.read_cells(notebook),
                                        ("code", "print(project.check())")])
    usability_loop.check_cells(result)
    assert result.added_cells == ["convert (1)"]
    assert not result.passed
    forget_the_projects_modules()


def test_a_runs_actions_are_counted_cells_edited_and_files_of_its_own(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Toolbox 8.5, ticket 12: what a run did by hand, counted, failing nothing.
    run = tmp_path / "run"
    work = run / "my_work"
    work.mkdir(parents=True)
    monkeypatch.chdir(work)
    project = toolbox_module().project
    notebooks = toolbox_module("notebooks")
    project.start()
    result = usability_loop.RunScore("W7", project=work)
    usability_loop.count_actions(result, run)
    assert result.actions == 0
    notebook = work / "admin" / "workflows" / "convert" / "convert.ipynb"
    cells = notebooks.read_cells(notebook)
    names = next(number for number, (kind, text) in enumerate(cells)
                 if kind == "code" and text.startswith("NAME ="))
    cells[names] = ("code", cells[names][1].replace("NAME = ''", "NAME = 'weekly'", 1))
    notebooks.write_notebook(notebook, cells)
    (work / "admin" / "workflows" / "convert" / "weekly.hql").write_text("SELECT 1\n",
                                                                       encoding="utf-8")
    (run / "set_cell.py").write_text("print('mine')\n", encoding="utf-8")
    usability_loop.count_actions(result, run)
    assert result.edited_cells == {"convert": 1}
    assert result.own_files == ["my_work/admin/workflows/convert/weekly.hql", "set_cell.py"]
    assert result.actions == 3
    assert "actions: 3, cells edited (convert 1), 2 files of its own" in (
        usability_loop.report_text(result, run))
    forget_the_projects_modules()
