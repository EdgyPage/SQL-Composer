"""The usability loop's harness (Toolbox 8.2, ticket 02).

A run's folder holds what a user has, built from what main ships; its warehouse keeps each
table between processes; its notebook runner runs cells as Run All does; a question goes to
Copilot as one chat, file 00 first; and a run's end is scored against its scenario's answer
key, failing on the check meant to catch each wrong end.
"""

from __future__ import annotations

import ast
import json
import sys
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
                   {"role": "non_technical", "job": "Fill in the workbook."}],
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


def test_a_run_built_from_dev_holds_mains_tree(tmp_path: Path) -> None:
    main = tmp_path / "main"
    usability_loop.build_main(main)
    assert (main / "sqlglot_composer" / "version.txt").is_file()
    assert (main / ".github" / "README.md").is_file()
    assert (main / "copilot" / "formula_workbook.xlsx").is_file()
    assert not (main / "tools").exists() and not (main / ".scratch").exists()


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


@pytest.mark.parametrize("arguments", [[], ["a.ipynb", "b.ipynb"], ["--cells", "a.ipynb"],
                                       ["a.ipynb", "--list", "--cells", "1"]],
                         ids=["no path", "two paths", "no cells", "both"])
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
