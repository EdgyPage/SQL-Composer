"""The project module: a Project's folders and files, made, archived and checked, and logged.

Toolbox 6.0's ticket 06. start() lays a Project out once; new_table makes a Table folder from a
Template; remove_table and remove_reference archive into admin/removed/, deleting nothing;
register adopts what was made by hand, and check() reports what the registry and the disk
disagree on. Each but check() logs a Project action in admin/admin_log.md, where the Admin
statements run inside the Project go too. A notebook is written as the plain JSON Jupyter
reads, so each one's code cells are parsed here as Python.
"""

from __future__ import annotations

import ast
import contextlib
import csv
import datetime
import importlib
import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import run_admin_notebook, toolbox_module

from sqlglot_composer import (
    Table,
    admin,
    example_database,
    export_lineage,
    notebooks,
    project,
    project_files,
    run_execute,
    set_admin_log,
    to_hive,
)

NOW = datetime.datetime(2026, 10, 21, 9, 30, 0)
ADMIN_NOTEBOOKS = ["add_references", "change_a_saved_table", "check_project",
                   "check_references", "convert", "new_block", "new_table",
                   "refresh_reference_sheet", "remove_table", "run_tables", "upgrade"]


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project just started in a folder of its own, the time pinned, the Admin log unmoved."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


def registry(root: Path) -> list[dict[str, str]]:
    return project_files.Registry(root).rows


def cells(path: Path) -> list[tuple[str, str]]:
    assert json.loads(path.read_text(encoding="utf-8"))["nbformat"] == 4
    return notebooks.read_cells(path)


def log_text(root: Path) -> str:
    return (root / "admin" / "admin_log.md").read_text(encoding="utf-8")


# --- start ------------------------------------------------------------------------------------


def test_start_lays_out_a_project(started: Path) -> None:
    assert sorted(path.name for path in started.iterdir()) == [
        "admin", "building_blocks", "references", "tables", "warehouse.py"]
    assert sorted(path.name for path in (started / "admin").iterdir()) == sorted(
        ["admin_log.md", "conversions", "project_version.txt", "registry.csv", "templates"]
        + [f"{name}.ipynb" for name in ADMIN_NOTEBOOKS])
    assert sorted(path.name for path in (started / "admin" / "templates").iterdir()) == [
        "building_block.py", "quality_checks.py", "saved_table.py",
        "saved_table_reference.py"]
    assert registry(started) == []
    assert (started / "admin" / "registry.csv").read_text(encoding="utf-8") == (
        "kind,table,created_at,removed_at\n")


def test_each_admin_notebook_puts_the_project_on_the_path_and_parses(started: Path) -> None:
    for name in ADMIN_NOTEBOOKS:
        found = cells(started / "admin" / f"{name}.ipynb")
        assert [kind for kind, _ in found[:2]] == ["markdown", "code"], name
        assert "sys.path.insert(0, str(pathlib.Path.cwd().parent))" in found[1][1]
        for kind, text in found:
            if kind == "code":
                ast.parse(text)


def test_the_admin_notebooks_speak_of_no_day(started: Path) -> None:
    run_tables = "\n".join(text for _, text in cells(started / "admin" / "run_tables.ipynb"))
    assert "DAY" not in run_tables and "write_day" not in run_tables
    assert "project.run_tables()" in run_tables
    change = "\n".join(text for _, text in
                       cells(started / "admin" / "change_a_saved_table.ipynb"))
    assert "drop_days" not in change
    assert "admin.drop_partitions(your_table, where=" in change


def test_warehouse_py_reaches_the_example_database_until_you_change_it(started: Path) -> None:
    text = (started / "warehouse.py").read_text(encoding="utf-8")
    assert text == project.WAREHOUSE_TEXT
    defined = {node.name: node for node in ast.parse(text).body
               if isinstance(node, ast.FunctionDef)}
    assert sorted(defined) == ["execute", "query"]
    assert ast.unparse(defined["query"].returns) == "pd.DataFrame"
    assert ast.unparse(defined["execute"].returns) == "None"
    assert "return example_database.query(hive)  # at work: your warehouse's query call" in text
    assert "    example_database.execute(hive)  # at work: your warehouse's execute call" in text


def test_start_says_to_write_the_query_and_execute(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    set_admin_log()
    assert " ".join(repr(project.start()).split()) == (
        "Started a Project in the folder you're working in: admin/, references/, "
        "building_blocks/, tables/ and warehouse.py. Next: write your two functions, query and "
        "execute, in warehouse.py.")


def test_start_logs_a_project_action(started: Path) -> None:
    assert ("## 2026-10-21 09:30:00, Project action\n\n- Call: `project.start()`\n"
            "- Files: created admin/, references/, building_blocks/, tables/, warehouse.py\n"
            in log_text(started))


# send.py, a Project's file before 7.0, is refused too: the folder holds a Project already.
@pytest.mark.parametrize("there",
                         ["admin", "references", "building_blocks", "tables", "warehouse.py",
                          "send.py"])
def test_start_refuses_a_folder_that_has_any_of_its_parts(
        there: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / there).mkdir()
    with pytest.raises(FileExistsError, match=f"{there}/? is already in the folder"):
        project.start()
    assert [path.name for path in tmp_path.iterdir()] == [there]


def test_start_refuses_a_folder_inside_a_project(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(started / "building_blocks")
    with pytest.raises(FileExistsError, match="was run inside a Project"):
        project.start()


def test_start_run_again_in_a_project_adds_only_what_it_lacks(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(started)
    assert str(project.start()) == ("This folder is a Project already, and lacks nothing "
                                    "start() makes.")
    (started / "admin" / "new_block.ipynb").unlink()
    (started / "admin" / "templates" / "saved_table.py").unlink()
    warehouse = started / "warehouse.py"
    warehouse.write_text("# mine\n", encoding="utf-8")
    report = str(project.start())
    assert report == ("This folder is a Project already. Added what it lacked: "
                      "admin/templates/saved_table.py, admin/new_block.ipynb.")
    assert (started / "admin" / "new_block.ipynb").exists()
    assert warehouse.read_text(encoding="utf-8") == "# mine\n"  # never written over
    assert "added admin/templates/saved_table.py" in (
        started / "admin" / "admin_log.md").read_text(encoding="utf-8")


def test_start_run_again_in_a_project_from_before_7_writes_no_warehouse_py(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """send.py's call goes into warehouse.py by hand, so check() goes on reporting it."""
    monkeypatch.chdir(started)
    (started / "warehouse.py").rename(started / "send.py")
    (started / "admin" / "new_block.ipynb").unlink()
    says = ("send.py is from before 7.0, so no warehouse.py was written: write your two "
            "functions, query and execute, in a new warehouse.py, as CHANGES.md's 7.0 says, "
            "then delete send.py.")
    assert str(project.start()) == ("This folder is a Project already. Added what it lacked: "
                                    "admin/new_block.ipynb.\n" + says)
    assert str(project.start()) == "This folder is a Project already.\n" + says
    assert not (started / "warehouse.py").exists()
    assert "send.py is from before 7.0" in repr(project.check())


# --- new_table --------------------------------------------------------------------------------


def test_new_table_makes_a_table_folder_and_a_reference(started: Path) -> None:
    report = project.new_table("mart.daily_job_runs")
    folder = started / "tables" / "mart__daily_job_runs"
    assert sorted(path.name for path in folder.iterdir()) == [
        "lineage", "mart__daily_job_runs.ipynb"]
    assert list((folder / "lineage").iterdir()) == []
    found = cells(folder / "mart__daily_job_runs.ipynb")
    assert [kind for kind, _ in found] == ["markdown"] + ["code"] * 5
    # The placeholders to fill in come first.
    assert found[0][1].startswith("# mart.daily_job_runs\n\nFill in every `<...>`")
    assert "TODO: say in one line what one row of mart.daily_job_runs is." in found[0][1]
    logic = found[2][1]
    assert logic.startswith("# logic\n")
    assert "from references.mart__daily_job_runs import daily_job_runs" in logic
    assert "<DB>" not in logic and "<TABLE>" not in logic and "<NAME>" not in logic
    # The placeholders that are yours stay, so the notebook can't run half filled in.
    assert "<SOURCE_TABLE>" in logic
    reference = (started / "references" / "mart__daily_job_runs.py").read_text(encoding="utf-8")
    assert 'daily_job_runs = Table(\n    "mart.daily_job_runs",' in reference
    assert "<LOCATION>" in reference
    assert [(row["kind"], row["table"], row["created_at"], row["removed_at"])
            for row in registry(started)] == [
        ("table_folder", "mart.daily_job_runs", "2026-10-21 09:30:00", ""),
        ("reference", "mart.daily_job_runs", "2026-10-21 09:30:00", "")]
    assert repr(report) == (
        "Made tables/mart__daily_job_runs/: mart__daily_job_runs.ipynb and lineage/, from\n"
        "admin/templates/saved_table.py.\n"
        "Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.")
    assert ('- Call: `project.new_table("mart.daily_job_runs")`\n'
            "- Tables named: mart.daily_job_runs\n"
            "- Files: created tables/mart__daily_job_runs/ (mart__daily_job_runs.ipynb, "
            "lineage/); created references/mart__daily_job_runs.py\n") in log_text(started)


def test_new_table_keeps_a_reference_that_is_there(started: Path) -> None:
    reference = started / "references" / "mart__daily_job_runs.py"
    reference.write_text("# mine", encoding="utf-8")
    assert "Kept references/mart__daily_job_runs.py" in repr(
        project.new_table("mart.daily_job_runs"))
    assert reference.read_text(encoding="utf-8") == "# mine"
    assert [row["kind"] for row in registry(started)] == ["table_folder"]


def test_new_table_uses_a_template_of_yours(started: Path) -> None:
    (started / "admin" / "templates" / "mine.py").write_text(
        "# %% [markdown]\n# # <DB>.<TABLE>\n\n# %%\n# logic\nNAME = '<NAME>'\n",
        encoding="utf-8")
    project.new_table("mart.daily_job_runs", template="mine")
    notebook = started / "tables" / "mart__daily_job_runs" / "mart__daily_job_runs.ipynb"
    assert cells(notebook) == [("markdown", "# mart.daily_job_runs"),
                               ("code", "# logic\nNAME = 'mart__daily_job_runs'")]
    assert 'project.new_table("mart.daily_job_runs", template="mine")' in log_text(started)


def test_new_table_refuses_a_table_folder_that_is_there(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    notebook = started / "tables" / "mart__daily_job_runs" / "mart__daily_job_runs.ipynb"
    notebook.write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="tables/mart__daily_job_runs/ is already there"):
        project.new_table("mart.daily_job_runs")
    assert notebook.read_text(encoding="utf-8") == "{}"


def test_new_table_refuses_a_table_the_registry_lists(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    folder = started / "tables" / "mart__daily_job_runs"
    for path in sorted(folder.rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    folder.rmdir()
    with pytest.raises(FileExistsError, match="the registry lists a Table folder for"):
        project.new_table("mart.daily_job_runs")
    assert not folder.exists()


@pytest.mark.parametrize(("name", "template", "error", "said"), [
    ("daily_job_runs", "saved_table", ValueError, "isn't a table's name with its database"),
    ("mart.daily-runs", "saved_table", ValueError, "isn't a table's name with its database"),
    ("mart.class", "saved_table", ValueError, "a word Python keeps for itself"),
    ("mart.daily_job_runs", "dialy_table", FileNotFoundError,
     "(?s)there is no Table notebook Template 'dialy_table'.*Use one of: 'quality_checks', "
     "'saved_table',"),
    ("mart.daily_job_runs", "building_block", FileNotFoundError,
     "there is no Table notebook Template 'building_block'"),
])
def test_new_table_refuses(
        started: Path, name: str, template: str, error: type[Exception], said: str) -> None:
    with pytest.raises(error, match=said):
        project.new_table(name, template=template)
    assert list((started / "tables").iterdir()) == []
    assert registry(started) == []


def test_a_project_action_outside_a_project_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="was run outside a Project"):
        project.new_table("mart.daily_job_runs")
    assert list(tmp_path.iterdir()) == []


def test_a_project_action_runs_from_any_folder_inside_it(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(started / "admin")
    project.new_table("mart.daily_job_runs")
    assert (started / "tables" / "mart__daily_job_runs").is_dir()


# --- remove_table and remove_reference --------------------------------------------------------


def test_remove_table_archives_the_folder_and_keeps_the_reference(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    report = project.remove_table("mart.daily_job_runs")
    archived = started / "admin" / "removed" / "20261021-093000-mart__daily_job_runs"
    assert (archived / "mart__daily_job_runs.ipynb").is_file()
    assert (archived / "lineage").is_dir()
    assert not (started / "tables" / "mart__daily_job_runs").exists()
    assert (started / "references" / "mart__daily_job_runs.py").is_file()
    assert [(row["kind"], row["removed_at"]) for row in registry(started)] == [
        ("table_folder", "2026-10-21 09:30:00"), ("reference", "")]
    assert repr(report) == ("Moved tables/mart__daily_job_runs/ to "
                            "admin/removed/20261021-093000-mart__daily_job_runs/.")
    assert "- Files: moved tables/mart__daily_job_runs/ to admin/removed/" in log_text(started)
    # Removed, the table can have a new Table folder.
    project.new_table("mart.daily_job_runs")
    assert (started / "tables" / "mart__daily_job_runs").is_dir()


def test_remove_table_refuses_a_table_folder_neither_there_nor_registered(
        started: Path) -> None:
    with pytest.raises(FileNotFoundError, match="there is no tables/mart__daily_job_runs/ to "
                       "remove, and the registry lists none"):
        project.remove_table("mart.daily_job_runs")


def test_remove_table_marks_removed_a_registered_folder_deleted_by_hand(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    folder = started / "tables" / "mart__daily_job_runs"
    for path in sorted(folder.rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    folder.rmdir()
    assert repr(project.remove_table("mart.daily_job_runs")) == (
        "tables/mart__daily_job_runs/ wasn't there, so only its registry row is marked "
        "removed.")
    assert [(row["kind"], row["removed_at"]) for row in registry(started)] == [
        ("table_folder", "2026-10-21 09:30:00"), ("reference", "")]
    assert "Registered, but not there" not in repr(project.check())
    assert not (started / "admin" / "removed").exists()


def test_remove_reference_archives_the_file(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    project.remove_table("mart.daily_job_runs")
    project.remove_reference("mart.daily_job_runs")
    archived = started / "admin" / "removed" / "20261021-093000-mart__daily_job_runs.py"
    assert "daily_job_runs = Table(" in archived.read_text(encoding="utf-8")
    assert not (started / "references" / "mart__daily_job_runs.py").exists()
    assert [row["removed_at"] for row in registry(started)] == ["2026-10-21 09:30:00"] * 2


def test_remove_reference_refuses_while_its_table_folder_is_there(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    with pytest.raises(ValueError, match="tables/mart__daily_job_runs/ is still there"):
        project.remove_reference("mart.daily_job_runs")
    assert (started / "references" / "mart__daily_job_runs.py").is_file()


def test_remove_reference_refuses_a_file_that_isnt_there(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match="there is no references/ops__jobs.py"):
        project.remove_reference("ops.jobs")


def test_new_table_doesnt_register_a_reference_twice(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    project.remove_table("mart.daily_job_runs")
    (started / "references" / "mart__daily_job_runs.py").unlink()
    project.new_table("mart.daily_job_runs")
    assert [(row["kind"], row["removed_at"]) for row in registry(started)] == [
        ("table_folder", "2026-10-21 09:30:00"), ("reference", ""), ("table_folder", "")]


# --- register and check -----------------------------------------------------------------------


def test_check_finds_nothing_in_a_new_project(started: Path) -> None:
    assert repr(project.check()) == ("Every Table folder, Table reference and Building block is "
                                     "registered, and each one registered is there.")


def test_check_reports_what_was_made_or_moved_by_hand(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    (started / "tables" / "mart__by_hand").mkdir()
    (started / "references" / "mart__daily_job_runs.py").unlink()
    assert repr(project.check()) == (
        "Not registered, made by hand. Adopt each with the call beside it:\n"
        '  references/ops__jobs.py: project.register("ops.jobs")\n'
        '  tables/mart__by_hand/: project.register("mart.by_hand")\n'
        "Registered, but not there. Put each back, or mark it removed with the call beside it:\n"
        '  references/mart__daily_job_runs.py: project.remove_reference("mart.daily_job_runs")')


def test_check_reads_a_database_holding_two_underscores_back_at_its_first(
        started: Path) -> None:
    """Pins today's behaviour: a file's stem is read back as a table's name at its first __,
    so my__db.jobs's file is offered to register as my.db__jobs, which names the same file."""
    (started / "references" / "my__db__jobs.py").write_text("# by hand", encoding="utf-8")
    assert repr(project.check()).splitlines()[1] == (
        '  references/my__db__jobs.py: project.register("my.db__jobs")')
    project.register("my.db__jobs")
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "my.db__jobs")]
    assert repr(project.check()).startswith("Every Table folder")


@contextlib.contextmanager
def registry_reads() -> Iterator[list[str]]:
    """Each time registry.csv is opened to be read, while inside."""
    reads: list[str] = []
    real_open = open

    def counting(file: object, mode: str = "r", *args: object, **kwargs: object) -> object:
        if str(file).endswith("registry.csv") and "w" not in mode:
            reads.append(str(file))
        return real_open(file, mode, *args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("builtins.open", counting)
        yield reads


def test_an_action_on_several_names_reads_the_registry_once(started: Path) -> None:
    with registry_reads() as reads:
        project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
                               query=example_database.query)
    assert len(reads) == 1
    (started / "references" / "ops__jobs.py").unlink()
    (started / "tables" / "mart__by_hand").mkdir()
    with registry_reads() as reads:
        project.check()
    assert len(reads) == 1
    project.new_table("mart.daily_job_runs")
    project.remove_table("mart.daily_job_runs")
    with registry_reads() as reads:
        project.new_table("mart.daily_job_runs")
        project.register("mart.by_hand")
        project.new_block("runs_per_job")
        project.remove_block("runs_per_job")
        project.remove_table("mart.daily_job_runs")
        project.remove_reference("mart.daily_job_runs")
    assert len(reads) == 6
    project.remove_table("mart.by_hand")
    with registry_reads() as reads:
        project.run_tables()
    assert len(reads) == 1


def test_check_reports_a_send_py_with_no_warehouse_py(started: Path) -> None:
    """A Project from before 7.0 holds send.py, whose one send Toolbox 7.0 split in two."""
    (started / "warehouse.py").rename(started / "send.py")
    assert repr(project.check()) == (
        "send.py is from before 7.0, and there is no warehouse.py: write your query and "
        "execute in\na new warehouse.py, as CHANGES.md's 7.0 says, then delete send.py.")
    (started / "warehouse.py").write_text(project.WAREHOUSE_TEXT, encoding="utf-8")
    assert "send.py" not in repr(project.check())


def test_check_changes_nothing(started: Path) -> None:
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    before = log_text(started)
    project.check()
    assert log_text(started) == before
    assert registry(started) == []


def test_register_adopts_what_was_made_by_hand(started: Path) -> None:
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    assert repr(project.register("ops.jobs")) == "Registered references/ops__jobs.py."
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "ops.jobs")]
    assert "- Files: registered references/ops__jobs.py\n" in log_text(started)
    assert "registered" in repr(project.check())


def test_register_refuses_when_there_is_nothing_to_adopt(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    with pytest.raises(ValueError, match="nothing to register"):
        project.register("mart.daily_job_runs")
    with pytest.raises(ValueError, match="nothing to register"):
        project.register("ops.jobs")


# --- new_block and remove_block ---------------------------------------------------------------


def test_new_block_writes_a_building_block_from_the_template(started: Path) -> None:
    report = project.new_block("runs_per_job")
    text = (started / "building_blocks" / "runs_per_job.py").read_text(encoding="utf-8")
    # <BLOCK> is filled in; the placeholders that are yours stay, so it can't run half done.
    assert "<BLOCK>" not in text
    assert "def runs_per_job(reads: Condition) -> Table:" in text
    assert '        "runs_per_job",  # the name the Hive gives it' in text
    assert "from building_blocks.runs_per_job import runs_per_job" in text
    assert 'project.new_block("runs_per_job") wrote this file' in text
    assert "<SOURCE_TABLE>" in text
    assert [(row["kind"], row["table"], row["removed_at"]) for row in registry(started)] == [
        ("building_block", "runs_per_job", "")]
    assert repr(report) == (
        "Wrote building_blocks/runs_per_job.py, from admin/templates/building_block.py:\n"
        "fill in its <...> and TODO lines.")
    assert ('- Call: `project.new_block("runs_per_job")`\n'
            "- Files: created building_blocks/runs_per_job.py\n") in log_text(started)
    assert repr(project.check()).startswith("Every Table folder, Table reference and Building")


def test_new_block_uses_the_projects_own_template(started: Path) -> None:
    """A Project's own copy, 6.x's among them, which named the Building block in quotes as
    <BLOCK_NAME>."""
    (started / "admin" / "templates" / "building_block.py").write_text(
        '"""<BLOCK> - mine."""\nNAME = <BLOCK_NAME>\n', encoding="utf-8")
    project.new_block("mine")
    assert (started / "building_blocks" / "mine.py").read_text(encoding="utf-8") == (
        '"""mine - mine."""\nNAME = "mine"\n')


def test_new_block_refuses_a_name_already_taken(started: Path) -> None:
    block = started / "building_blocks" / "runs_per_job.py"
    block.write_text("# mine", encoding="utf-8")
    with pytest.raises(FileExistsError, match="building_blocks/runs_per_job.py is already there"):
        project.new_block("runs_per_job")
    assert block.read_text(encoding="utf-8") == "# mine"
    block.unlink()
    project.new_block("runs_per_job")
    block.unlink()
    with pytest.raises(FileExistsError, match="the registry lists a Building block runs_per_job"):
        project.new_block("runs_per_job")
    assert len(registry(started)) == 1


@pytest.mark.parametrize(("name", "said"), [
    ("runs-per-job", "isn't a name Python can import a Building block by"),
    ("ops.runs", "isn't a name Python can import a Building block by"),
    ("1st_block", "isn't a name Python can import a Building block by"),
    (7, "isn't a name Python can import a Building block by"),
    ("class", "class is a name Python keeps for itself"),
    ("__init__", "__init__ is a name Python keeps for itself"),
])
def test_new_block_refuses_a_name_python_cant_import(
        started: Path, name: object, said: str) -> None:
    with pytest.raises(ValueError, match=said):
        project.new_block(name)  # type: ignore[arg-type]
    assert list((started / "building_blocks").iterdir()) == []
    assert registry(started) == []


def test_new_block_refuses_a_project_with_no_template(started: Path) -> None:
    (started / "admin" / "templates" / "building_block.py").unlink()
    with pytest.raises(FileNotFoundError, match="there is no admin/templates/building_block.py"):
        project.new_block("runs_per_job")
    assert registry(started) == []


def test_remove_block_archives_the_file(started: Path) -> None:
    project.new_block("runs_per_job")
    report = project.remove_block("runs_per_job")
    archived = started / "admin" / "removed" / "20261021-093000-runs_per_job.py"
    assert "def runs_per_job(" in archived.read_text(encoding="utf-8")
    assert not (started / "building_blocks" / "runs_per_job.py").exists()
    assert [row["removed_at"] for row in registry(started)] == ["2026-10-21 09:30:00"]
    assert repr(report) == ("Moved building_blocks/runs_per_job.py to "
                            "admin/removed/20261021-093000-runs_per_job.py.")
    assert "- Files: moved building_blocks/runs_per_job.py to admin/removed/" in log_text(
        started)
    # Removed, the name can be used again.
    project.new_block("runs_per_job")


def test_remove_block_refuses_while_something_imports_it(started: Path) -> None:
    project.new_block("runs_per_job")
    project.new_block("team_runs")
    (started / "building_blocks" / "team_runs.py").write_text(
        "from building_blocks.runs_per_job import runs_per_job\n", encoding="utf-8")
    project.new_table("mart.daily_job_runs")
    notebook = started / "tables" / "mart__daily_job_runs" / "mart__daily_job_runs.ipynb"
    found = notebooks.read_cells(notebook)
    found[2] = ("code", "# logic\nfrom building_blocks import runs_per_job\n")
    notebooks.write_notebook(notebook, found)
    with pytest.raises(ValueError, match=(
            "tables/mart__daily_job_runs/mart__daily_job_runs.ipynb and "
            "building_blocks/team_runs.py still import building_blocks/runs_per_job.py")):
        project.remove_block("runs_per_job")
    assert (started / "building_blocks" / "runs_per_job.py").is_file()
    # A name that only starts the same isn't an import of it.
    (started / "building_blocks" / "team_runs.py").write_text(
        "from building_blocks.runs_per_job_v2 import x\n", encoding="utf-8")
    notebooks.write_notebook(notebook, [])
    project.remove_block("runs_per_job")
    assert not (started / "building_blocks" / "runs_per_job.py").exists()


def test_remove_block_passes_over_a_notebook_jupyter_cant_read(started: Path) -> None:
    # remove_block only archives, so a broken notebook, which imports nothing, doesn't stop it.
    project.new_block("runs_per_job")
    project.new_table("mart.daily_job_runs")
    notebook_of(started, "mart__daily_job_runs").write_text('{"cells": [', encoding="utf-8")
    project.remove_block("runs_per_job")
    assert not (started / "building_blocks" / "runs_per_job.py").exists()


def test_a_cell_jupyter_keeps_as_one_string_is_read_as_its_text(tmp_path: Path) -> None:
    path = tmp_path / "one_string.ipynb"
    path.write_text(json.dumps({"cells": [{"cell_type": "code", "source": "# logic\nx = 1"}]}),
                    encoding="utf-8")
    assert notebooks.read_cells(path) == [("code", "# logic\nx = 1")]
    assert notebooks.logic_cell(path) == "# logic\nx = 1"


def test_remove_block_marks_removed_a_block_deleted_by_hand(started: Path) -> None:
    project.new_block("runs_per_job")
    (started / "building_blocks" / "runs_per_job.py").unlink()
    assert repr(project.check()) == (
        "Registered, but not there. Put each back, or mark it removed with the call beside it:\n"
        '  building_blocks/runs_per_job.py: project.remove_block("runs_per_job")')
    assert repr(project.remove_block("runs_per_job")) == (
        "building_blocks/runs_per_job.py wasn't there, so only its registry row is marked "
        "removed.")
    assert repr(project.check()).startswith("Every Table folder")


def test_remove_block_refuses_a_block_neither_there_nor_registered(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match=(
            "(?s)there is no building_blocks/runs_per_job.py to remove.*the files in "
            "building_blocks/ are named as the Building block is")):
        project.remove_block("runs_per_job")


def test_a_building_block_made_by_hand_is_adopted_with_register(started: Path) -> None:
    """A Project from before 7.0 holds Building blocks written by hand: register adopts each,
    and new_block, which never writes over a file, refuses them."""
    block = started / "building_blocks" / "runs_per_job.py"
    block.write_text("# by hand", encoding="utf-8")
    (started / "building_blocks" / "__init__.py").write_text("", encoding="utf-8")
    assert repr(project.check()) == (
        "Not registered, made by hand. Adopt each with the call beside it:\n"
        '  building_blocks/runs_per_job.py: project.register("runs_per_job")')
    with pytest.raises(FileExistsError, match="is already there"):
        project.new_block("runs_per_job")
    assert repr(project.register("runs_per_job")) == (
        "Registered building_blocks/runs_per_job.py.")
    assert block.read_text(encoding="utf-8") == "# by hand"
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("building_block", "runs_per_job")]
    assert ('- Call: `project.register("runs_per_job")`\n'
            "- Files: registered building_blocks/runs_per_job.py\n") in log_text(started)
    assert repr(project.check()).startswith("Every Table folder")
    with pytest.raises(ValueError, match="nothing to register: building_blocks/runs_per_job.py"):
        project.register("runs_per_job")


def test_the_new_block_notebook_makes_and_removes_a_building_block(started: Path) -> None:
    notebook = started / "admin" / "new_block.ipynb"
    code = [text for kind, text in cells(notebook) if kind == "code"]
    # Both lines wait, commented, for a name: run as it is, the notebook makes nothing.
    assert code[1:] == ['# project.new_block("your_block")',
                        '# project.remove_block("your_block")']
    run_admin_notebook(notebook)
    assert not (started / "building_blocks" / "your_block.py").exists()
    project.new_block("your_block")
    assert (started / "building_blocks" / "your_block.py").is_file()
    run_admin_notebook(notebook, [code[0], code[2].removeprefix("# ")])
    assert not (started / "building_blocks" / "your_block.py").exists()
    assert [row["removed_at"] for row in registry(started)] == ["2026-10-21 09:30:00"]


@pytest.mark.needs_example_database
def test_the_check_references_notebook_checks_each_table_and_its_key(
        started: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """ops.jobs' Key is checked; ops.team_notes has none; ops.job_runs is partitioned, so the
    call that checks it on some Partitions is printed; a reference still to fill in is left
    out, as the Reference sheet leaves it out."""
    project.add_references(["ops.jobs", "ops.job_runs", "ops.team_notes"],
                           query=example_database.query)
    for name, key in (("ops__jobs", '["job_id"]'), ("ops__job_runs", '["run_id"]')):
        reference = started / "references" / f"{name}.py"
        text = reference.read_text(encoding="utf-8")
        reference.write_text(text.replace("    key=None,", f"    key={key},", 1),
                             encoding="utf-8")
    project.new_table("mart.daily_job_runs")
    capsys.readouterr()
    said = run_admin_notebook(started / "admin" / "check_references.ipynb", capsys=capsys)
    assert said.startswith("Wrote references/reference_sheet.csv: 13 rows, 3 tables.\n"
                           "Left out, since it can't be read yet: "
                           "references/mart__daily_job_runs.py.")
    assert ("ops.job_runs matches its Table reference.\n"
            "ops.job_runs is partitioned by dt, so its Key isn't checked here: that would read "
            "every Partition. Check it on some, in the last cell:\n"
            "    from references.ops__job_runs import job_runs\n"
            "    print(check_key(job_runs, query=query, where=equals(job_runs.dt, "
            "<a value>)))\n\n") in said
    assert ("ops.jobs matches its Table reference.\n"
            "ops.jobs: the key (job_id) holds.\n\n") in said
    assert ("ops.team_notes matches its Table reference.\n"
            "ops.team_notes has no Key, so there is no Key to check.\n") in said
    assert "mart.daily_job_runs" not in said.split("\n", 2)[2]


# --- add_references ---------------------------------------------------------------------------


def failing_on(missing: str) -> Callable[..., pd.DataFrame]:
    """The Example database's query, but a table it doesn't have fails, as a warehouse's
    does."""
    def query(hive: str) -> pd.DataFrame:
        if missing in hive:
            raise RuntimeError(f"Table not found: {missing}")
        return example_database.query(hive)

    return query


def test_add_references_writes_each_table_and_registers_it(started: Path) -> None:
    report = project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    assert sorted(path.name for path in (started / "references").iterdir()) == [
        "ops.py", "ops__job_runs.py", "ops__jobs.py"]
    assert "from references.ops__jobs import jobs, <alias>" in (
        started / "references" / "ops__jobs.py").read_text(encoding="utf-8")
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "ops.jobs"), ("reference", "ops.job_runs")]
    assert repr(report) == ("Wrote references/ops__jobs.py and references/ops__job_runs.py: "
                            "fill in their TODO lines.\n"
                            "Wrote references/ops.py: from references import ops gives "
                            "ops.job_runs and ops.jobs.\n"
                            "Restart the kernel of a notebook that imported references, to "
                            "see a table added since.")


def test_add_references_names_three_files_or_more_as_a_sentence_does(started: Path) -> None:
    report = project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
                                    query=example_database.query)
    assert repr(report).splitlines()[0] == (
        "Wrote references/ops__jobs.py, references/ops__job_runs.py and "
        "references/ops__run_alerts.py: fill in their TODO lines.")


def test_add_references_skips_what_it_cant_write_and_finishes_the_list(started: Path) -> None:
    (started / "references" / "ops__jobs.py").write_text("# mine", encoding="utf-8")
    with pytest.raises(project.SkippedTables) as skipped:
        project.add_references(["ops.jobs", "ops.job_ownres", "jobs", "ops.run_alerts"],
                               query=failing_on("ops.job_ownres"))
    message = " ".join(str(skipped.value).split())
    assert ("add_references skipped 3 of 4 tables: ops.jobs (references/ops__jobs.py is there "
            "already); ops.job_ownres (DESCRIBE failed: RuntimeError: Table not found: "
            "ops.job_ownres); 'jobs' (not written as database.table, such as ops.jobs)."
            ) in message
    assert "references/ops__run_alerts.py was written." in message
    # The table after the skipped ones is still written, and the file there is left alone.
    assert (started / "references" / "ops__run_alerts.py").is_file()
    assert (started / "references" / "ops__jobs.py").read_text(encoding="utf-8") == "# mine"
    assert [row["table"] for row in registry(started)] == ["ops.run_alerts"]
    log = log_text(started)
    assert ('- Call: `project.add_references(["ops.jobs", "ops.job_ownres", "jobs", '
            '"ops.run_alerts"], query=...)`\n') in log
    assert "- Files: created references/ops__run_alerts.py; wrote references/ops.py\n" in log
    assert ("- Skipped: ops.jobs (references/ops__jobs.py is there already); "
            "ops.job_ownres") in log
    assert "- Result: 1 of 4 written; SkippedTables named the rest, above\n" in log


def test_add_references_refuses_send_naming_query(started: Path) -> None:
    with pytest.raises(TypeError) as refused:
        project.add_references(["ops.jobs"], send=example_database.query)
    message = str(refused.value)
    assert "add_references was given send=, which Toolbox 7.0 replaced." in message
    assert "Pass query= instead" in message
    assert list((started / "references").iterdir()) == []


def test_add_references_refuses_a_name_where_a_list_goes(started: Path) -> None:
    with pytest.raises(ValueError, match="names isn't a list of tables"):
        project.add_references("ops.jobs", query=example_database.query)


# --- The Reference sheet ----------------------------------------------------------------------


def sheet(root: Path) -> list[dict[str, str]]:
    path = root / "references" / "reference_sheet.csv"
    with open(path, encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def test_the_reference_sheet_has_a_row_per_column_with_its_aliases(started: Path) -> None:
    project.add_references(["ops.job_runs"], query=example_database.query)
    reference = started / "references" / "ops__job_runs.py"
    text = reference.read_text(encoding="utf-8").replace("key=None,", 'key=["run_id"],')
    reference.write_text(text + "minutes = job_runs.duration_mins\n"
                         'failed = equals(job_runs.status, "FAILED")\n'
                         "slow = job_runs.duration_mins > job_runs.avg_retry_secs\n",
                         encoding="utf-8")
    report = project.refresh_reference_sheet()
    rows = {row["column"]: row for row in sheet(started)}
    assert list(rows) == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"]
    assert rows["run_id"] | {"exported_at": ""} == {
        "table": "ops.job_runs", "column": "run_id", "type": "bigint", "partition": "",
        "in_key": "yes", "aliases": "", "description": "", "exported_at": ""}
    assert rows["dt"]["partition"] == "yes"
    assert rows["job_id"]["partition"] == ""
    assert rows["duration_mins"]["aliases"] == "minutes"
    assert rows["status"]["aliases"] == "failed (a condition)"
    assert rows["avg_retry_secs"]["aliases"] == ""  # slow reads two columns
    assert rows["status"]["description"] == "SUCCESS / FAILED / TEST, NULL while running"
    assert {row["exported_at"] for row in rows.values()} == {"2026-10-21 09:30:00"}
    assert repr(report) == "Wrote references/reference_sheet.csv: 6 rows, 1 table."


def test_refreshing_one_table_replaces_only_its_rows(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project.add_references(["ops.jobs", "ops.run_alerts"], query=example_database.query)
    project.refresh_reference_sheet()
    later = datetime.datetime(2026, 10, 22, 8, 0, 0)
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: later)
    reference = started / "references" / "ops__run_alerts.py"
    reference.write_text(reference.read_text(encoding="utf-8").replace(
        '"severity": "low / high"', '"severity": "low, high or critical"'), encoding="utf-8")
    project.refresh_reference_sheet("ops.run_alerts")
    rows = sheet(started)
    assert {(row["table"], row["exported_at"]) for row in rows} == {
        ("ops.jobs", "2026-10-21 09:30:00"), ("ops.run_alerts", "2026-10-22 08:00:00")}
    assert [row["description"] for row in rows if row["column"] == "severity"] == [
        "low, high or critical"]
    assert len(rows) == 8


def test_a_reference_still_to_fill_in_is_left_out_of_the_sheet(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    project.add_references(["ops.jobs"], query=example_database.query)
    assert repr(project.refresh_reference_sheet()) == (
        "Wrote references/reference_sheet.csv: 4 rows, 1 table.\n"
        "Left out, since it can't be read yet: references/mart__daily_job_runs.py. Fill in "
        "every <...> in it, and check it holds a Table(...) call, then refresh again.")


def test_a_named_refresh_keeps_the_rows_of_a_file_that_cant_be_read(started: Path) -> None:
    project.add_references(["ops.jobs"], query=example_database.query)
    project.refresh_reference_sheet()
    reference = started / "references" / "ops__jobs.py"
    reference.write_text(reference.read_text(encoding="utf-8") + "oops = <ALIAS>" + "\n",
                         encoding="utf-8")
    assert "its rows from before are kept until then" in repr(
        project.refresh_reference_sheet("ops.jobs"))
    assert len(sheet(started)) == 4


def test_a_describe_refused_by_the_toolbox_is_named_by_what_happened(started: Path) -> None:
    """A Toolbox refusal from inside add_references is one line of the error, not a second
    four-part message inside the first."""
    with pytest.raises(project.SkippedTables) as skipped:
        project.add_references(["ops.empty"], query=lambda hive: pd.DataFrame(
            columns=["col_name", "data_type", "comment"]))
    message = str(skipped.value)
    assert message.count("What happened:") == 1
    assert "ops.empty (DESCRIBE failed: ValueError: write_table_reference('ops.empty', ...): "
    assert "DESCRIBE ops.empty listed no columns.)" in " ".join(message.split())


def test_refreshing_a_table_with_no_reference_is_refused(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match="there is no references/ops__jobs.py to read"):
        project.refresh_reference_sheet("ops.jobs")


# --- Databases --------------------------------------------------------------------------------

JOB_DAYS = """from sqlglot_composer import Table

job_days = Table(
    "mart.job_days",
    columns={"job_id": "bigint", "tags": "array<string>", "dt": "string"},
    partitioned_by=["dt"],
    location="/data/your_team/mart.db/job_days",
)
"""


@contextlib.contextmanager
def on_the_path(root: Path) -> Iterator[None]:
    """The Project on Python's path, as a notebook of it has it, and its references/ forgotten
    after, so another test can write its own."""
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        yield
    finally:
        sys.path.remove(str(root))
        for module in [module for module in sys.modules
                       if module.split(".")[0] == "references"]:
            del sys.modules[module]


@pytest.mark.needs_example_database
def test_a_database_gives_its_tables_and_their_columns(started: Path) -> None:
    project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    with on_the_path(started):
        from references import ops
    assert repr(ops.jobs) == repr(example_database.jobs)
    assert repr(ops.jobs.job_id) == "jobs.job_id"
    # Tab completion lists its tables, and nothing else.
    assert dir(ops) == ["job_runs", "jobs"]
    assert f"SELECT {ops.jobs.job_id} FROM {ops.jobs}" == (
        "SELECT jobs.job_id FROM ops.jobs AS jobs")


@pytest.mark.needs_example_database
def test_a_name_a_database_doesnt_have_names_the_tables_it_has(started: Path) -> None:
    project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    with on_the_path(started):
        from references import ops
    with pytest.raises(AttributeError) as wrong:
        ops.jbos
    assert str(wrong.value) == (
        "ops has no table 'jbos'. Did you mean 'jobs'? Its tables are: job_runs, jobs.")
    with pytest.raises(AttributeError, match="jobs has no column 'jbo_id'. Did you mean"):
        ops.jobs.jbo_id


def test_a_database_module_says_what_it_is_and_lists_its_tables(started: Path) -> None:
    project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    text = (started / "references" / "ops.py").read_text(encoding="utf-8")
    assert text.splitlines()[0] == (
        '"""ops - a Database: written by the Project actions, never by hand.')
    assert ("Its tables: job_runs (references/ops__job_runs.py), jobs (references/ops__jobs.py)."
            in " ".join(text.split()))
    assert ("from references.ops__job_runs import job_runs\n"
            "from references.ops__jobs import jobs\n") in text


def test_check_and_the_reference_sheet_leave_a_database_module_out(started: Path) -> None:
    project.add_references(["ops.jobs"], query=example_database.query)
    assert repr(project.check()) == ("Every Table folder, Table reference and Building block is "
                                     "registered, and each one registered is there.")
    assert repr(project.refresh_reference_sheet()) == (
        "Wrote references/reference_sheet.csv: 4 rows, 1 table.")
    assert [row["table"] for row in registry(started)] == ["ops.jobs"]


def test_a_reference_still_to_fill_in_joins_its_database_once_filled_in(started: Path) -> None:
    report = project.new_table("mart.job_days")
    assert "references/mart.py" not in repr(report)
    assert not (started / "references" / "mart.py").exists()
    (started / "references" / "mart__job_days.py").write_text(JOB_DAYS, encoding="utf-8")
    # A column's type may hold < and >, as array<string> does: it is no <...> to fill in.
    assert repr(project.refresh_reference_sheet("mart.job_days")).splitlines()[1] == (
        "Wrote references/mart.py: from references import mart gives mart.job_days.")
    with on_the_path(started):
        from references import mart
    assert dir(mart) == ["job_days"]


def test_a_reference_with_a_placeholder_left_in_text_is_left_out(started: Path) -> None:
    (started / "references" / "mart__job_days.py").write_text(
        JOB_DAYS.replace('"/data/your_team/mart.db/job_days"', '"<LOCATION>"'),
        encoding="utf-8")
    project.register("mart.job_days")
    assert not (started / "references" / "mart.py").exists()


def test_register_writes_the_database_module(started: Path) -> None:
    (started / "references" / "mart__job_days.py").write_text(JOB_DAYS, encoding="utf-8")
    assert repr(project.register("mart.job_days")) == (
        "Registered references/mart__job_days.py.\n"
        "Wrote references/mart.py: from references import mart gives mart.job_days.\n"
        "Restart the kernel of a notebook that imported references, to see a table added "
        "since.")
    assert "- Files: registered references/mart__job_days.py; wrote references/mart.py\n" in (
        log_text(started))


def test_remove_reference_writes_the_database_again_and_removes_it_once_empty(
        started: Path) -> None:
    project.add_references(["ops.jobs", "ops.job_runs"], query=example_database.query)
    assert repr(project.remove_reference("ops.jobs")).splitlines()[1] == (
        "Wrote references/ops.py: from references import ops gives ops.job_runs.")
    with on_the_path(started):
        from references import ops
    assert dir(ops) == ["job_runs"]
    assert repr(project.remove_reference("ops.job_runs")).splitlines()[1] == (
        "Removed references/ops.py, since no Table reference left names the Database ops.")
    assert not (started / "references" / "ops.py").exists()
    assert "; removed references/ops.py\n" in log_text(started)


def test_an_unchanged_database_module_isnt_written_again(started: Path) -> None:
    project.add_references(["ops.jobs"], query=example_database.query)
    assert repr(project.refresh_reference_sheet()) == (
        "Wrote references/reference_sheet.csv: 4 rows, 1 table.")
    project.new_table("mart.daily_job_runs")  # its reference has a <...> still to fill in
    assert log_text(started).count("wrote references/ops.py") == 1


def test_a_file_of_yours_named_like_a_database_module_is_never_written_over(
        started: Path) -> None:
    (started / "references" / "ops.py").write_text("# mine\n", encoding="utf-8")
    report = repr(project.add_references(["ops.jobs"], query=example_database.query))
    assert " ".join(report.split()).endswith(
        "Didn't write references/ops.py, for the Database ops: references/ops.py is a file of "
        "yours, which the Project actions never write over. Import each of its tables from its "
        "own file instead, such as from references.ops__jobs import jobs.")
    project.remove_reference("ops.jobs")
    assert (started / "references" / "ops.py").read_text(encoding="utf-8") == "# mine\n"


@pytest.mark.parametrize(("name", "said", "instead"), [
    ("class.jobs", "class is a word Python keeps for itself",
     "from references.class__jobs import jobs"),
    ("2024.jobs", "2024 starts with a digit",
     'importlib.import_module("references.2024__jobs").jobs'),
    ("__main__.jobs", "__main__ starts and ends with two underscores, as the names Python "
     "keeps for itself do", "from references.__main____jobs import jobs"),
])
def test_a_database_python_cant_import_by_name_isnt_written(
        started: Path, name: str, said: str, instead: str) -> None:
    stem = project.table_stem(name)
    (started / "references" / f"{stem}.py").write_text(
        f'from sqlglot_composer import Table\n\njobs = Table("{name}", columns={{"id": "int"}})\n',
        encoding="utf-8")
    report = " ".join(repr(project.register(name)).split())
    assert f"Didn't write references/{name.split('.')[0]}.py" in report
    assert said in report and f"such as {instead}." in report
    assert sorted(path.name for path in (started / "references").iterdir()) == [f"{stem}.py"]


def test_two_tables_of_one_database_by_one_name_leave_the_second_out(started: Path) -> None:
    project.add_references(["ops.jobs"], query=example_database.query)
    (started / "references" / "ops__jobs_copy.py").write_text(
        'from sqlglot_composer import Table\n\njobs = Table("ops.jobs_copy", '
        'columns={"id": "int"})\n', encoding="utf-8")
    report = " ".join(repr(project.register("ops.jobs_copy")).split())
    assert ("Left out of its Database's file: references/ops__jobs_copy.py, which calls its "
            "table jobs, as references/ops__jobs.py does too.") in report
    with on_the_path(started):
        from references import ops
    assert dir(ops) == ["jobs"]


# --- load, run_tables and lineage ------------------------------------------------------------

DAILY_RUNS = """from sqlglot_composer import Table

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/daily_runs",
)
"""
TEAM_RUNS = """from sqlglot_composer import Table

team_runs = Table(
    "mart.team_runs",
    columns={"runs": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["dt"],
    location="/data/your_team/mart.db/team_runs",
)
"""
# Each table's notebook Template: a text cell and its logic cell. team_runs reads daily_runs.
DAILY_LOGIC = """# %% [markdown]
# # <DB>.<TABLE>

# %%
# logic
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, between, count_rows, statement,
)
from references.ops__job_runs import job_runs
from references.<NAME> import <TABLE>

DAY = "2026-09-24"


def write():
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(job_runs.job_id, AS(count_rows(), "runs"), AS(job_runs.dt, "dt")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, DAY, DAY)),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )

# %%
run_execute(write(), execute)
"""
TEAM_LOGIC = """# %%
# logic
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, between, statement, sum_of,
)
from references.mart__daily_runs import daily_runs
from references.<NAME> import <TABLE>

DAY = "2026-09-24"


def write():
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(AS(sum_of(daily_runs.runs), "runs"), AS(daily_runs.dt, "dt")),
        FROM(daily_runs),
        WHERE(between(daily_runs.dt, DAY, DAY)),
        GROUP_BY(daily_runs.dt),
    )
"""


@pytest.fixture
def two_tables(started: Path) -> Path:
    """A Project with two Table folders, mart.team_runs reading what mart.daily_runs writes,
    their Table references filled in, and ops.job_runs's written from the Example database."""
    templates = started / "admin" / "templates"
    (templates / "daily.py").write_text(DAILY_LOGIC, encoding="utf-8")
    (templates / "team.py").write_text(TEAM_LOGIC, encoding="utf-8")
    project.add_references(["ops.job_runs"], query=example_database.query)
    project.new_table("mart.daily_runs", template="daily")
    project.new_table("mart.team_runs", template="team")
    (started / "references" / "mart__daily_runs.py").write_text(DAILY_RUNS, encoding="utf-8")
    (started / "references" / "mart__team_runs.py").write_text(TEAM_RUNS, encoding="utf-8")
    return started


def notebook_of(root: Path, stem: str) -> Path:
    return root / "tables" / stem / f"{stem}.ipynb"


def test_load_gives_the_logic_cells_functions(two_tables: Path) -> None:
    logic = project.load("mart.daily_runs")
    assert repr(logic) == "The logic of mart.daily_runs: write."
    assert to_hive(logic.write()).startswith(
        "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)")


def test_load_reads_the_references_as_they_are_now(two_tables: Path) -> None:
    project.load("mart.daily_runs")
    reference = two_tables / "references" / "mart__daily_runs.py"
    reference.write_text(DAILY_RUNS.replace("daily_runs\"", "daily_runs_v2\""),
                         encoding="utf-8")
    write = project.load("mart.daily_runs").write()
    assert "mart.daily_runs_v2" in to_hive(write)


def test_load_refuses_a_notebook_it_cant_find(two_tables: Path) -> None:
    with pytest.raises(FileNotFoundError,
                       match="there is no tables/mart__nope/mart__nope.ipynb"):
        project.load("mart.nope")


@pytest.mark.parametrize(("text", "said"), [
    ('{"cells": [{"cell_type": "code", "sou', "isn't JSON"),
    ('{"metadata": {}, "nbformat": 4}', "has no list of cells Jupyter can read"),
    ('{"cells": [1]}', "has no list of cells Jupyter can read"),
])
def test_load_refuses_a_notebook_jupyter_cant_read(
        two_tables: Path, text: str, said: str) -> None:
    notebook_of(two_tables, "mart__daily_runs").write_text(text, encoding="utf-8")
    with pytest.raises(ValueError) as refused:
        project.load("mart.daily_runs")
    message = " ".join(str(refused.value).split())
    assert ('What happened: project.load("mart.daily_runs"): '
            f"tables/mart__daily_runs/mart__daily_runs.ipynb {said}") in message
    assert "Why it matters:" in message and "Usual fix:" in message
    assert "Opt-out: none" in message


@pytest.mark.parametrize(("logic", "said"), [
    ("x = 1\n", "has no cell whose first line is # logic"),
    ("# logic\nfrom references.<SOURCE> import x\n", "isn't Python yet, at its line 2"),
    ("# logic\nfrom sqlglot_composer import run_execute\nrun_execute(1, print)\n",
     "calls run_execute"),
    ("# logic\nfrom sqlglot_composer import run_query as go\ngo(1, print)\n", "calls go"),
    ("# logical next steps\nx = 1\n", "has no cell whose first line is # logic"),
])
def test_load_refuses_a_logic_cell_it_cant_run_safely(
        two_tables: Path, logic: str, said: str) -> None:
    (two_tables / "admin" / "templates" / "odd.py").write_text(f"# %%\n{logic}",
                                                               encoding="utf-8")
    project.new_table("mart.odd", template="odd")
    with pytest.raises(ValueError, match=said):
        project.load("mart.odd")


def odd_logic(root: Path, logic: str) -> None:
    """A Table folder mart.odd whose notebook's logic cell is `logic`."""
    (root / "admin" / "templates" / "odd.py").write_text(f"# %%\n# logic\n{logic}",
                                                         encoding="utf-8")
    project.new_table("mart.odd", template="odd")


def test_load_refuses_a_logic_cell_with_write_day_and_no_write(two_tables: Path) -> None:
    odd_logic(two_tables, "def write_day(day: str) -> str:\n    return day\n")
    with pytest.raises(ValueError) as refused:
        project.load("mart.odd")
    message = " ".join(str(refused.value).split())
    assert ('What happened: project.load("mart.odd"): the logic cell of '
            "tables/mart__odd/mart__odd.ipynb defines no write(). It defines write_day(day), "
            "from before 7.0, when run_tables gave each notebook a day: since 7.0 its write() "
            "takes nothing, and a value it needs, such as a day, is a constant in its logic "
            "cell.") in message
    assert "CHANGES.md, under 7.0, says how to turn a write_day(day) into it." in message


def test_load_refuses_a_logic_cell_with_no_write(two_tables: Path) -> None:
    odd_logic(two_tables, "def preview() -> int:\n    return 1\n")
    with pytest.raises(ValueError) as refused:
        project.load("mart.odd")
    message = " ".join(str(refused.value).split())
    assert "ipynb defines no write()." in message
    assert "write_day" not in message.split("Why it matters:")[0]


def test_load_refuses_a_write_that_needs_a_value_given(two_tables: Path) -> None:
    odd_logic(two_tables, "def write(day: str) -> str:\n    return day\n")
    with pytest.raises(ValueError) as refused:
        project.load("mart.odd")
    message = " ".join(str(refused.value).split())
    assert ('What happened: project.load("mart.odd"): the write() in the logic cell of '
            "tables/mart__odd/mart__odd.ipynb needs day given to it.") in message
    assert 'such as DAY = "2026-09-24"' in message


def test_load_takes_a_write_whose_arguments_all_have_defaults(two_tables: Path) -> None:
    odd_logic(two_tables, 'DAY = "2026-09-24"\n\n\ndef write(day: str = DAY) -> str:\n'
              "    return day\n")
    assert project.load("mart.odd").write() == "2026-09-24"


def test_run_tables_takes_no_day(two_tables: Path) -> None:
    with pytest.raises(TypeError, match="positional"):
        project.run_tables("2026-09-24")


def test_run_tables_with_no_execute_prints_each_write_writers_first(
        two_tables: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = project.run_tables(tables=["mart.team_runs", "mart.daily_runs"])
    printed = capsys.readouterr().out
    in_order = [printed.index(text) for text in (
        "-- 1 of 2: mart.daily_runs\n", "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)",
        "-- 2 of 2: mart.team_runs\n", "INSERT OVERWRITE TABLE mart.team_runs PARTITION(dt)")]
    assert in_order == sorted(in_order)
    # Each write fills dt from its rows, so each is printed after the setting it needs.
    assert printed.count('-- The Session setting "dynamic_partitions": this write fills dt '
                         "from its rows.") == 2
    assert repr(report) == ("Printed 2 writes in order, and sent nothing. Pass execute= to "
                            "run them.")


def test_run_tables_sends_every_registered_table_to_execute_in_order(two_tables: Path) -> None:
    sent = []
    report = project.run_tables(execute=sent.append)
    # Both fill dt from their rows, so dynamic partitioning is sent once, before either.
    assert [hive.split("\n")[0] for hive in sent] == [
        "SET hive.exec.dynamic.partition=true",
        "SET hive.exec.dynamic.partition.mode=nonstrict",
        "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt)",
        "INSERT OVERWRITE TABLE mart.team_runs PARTITION(dt)"]
    assert repr(report) == "Wrote 2 tables, in order."


def test_run_tables_refuses_send_naming_query_and_execute(
        two_tables: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sent = []
    with pytest.raises(TypeError) as refused:
        project.run_tables(send=sent.append)
    message = str(refused.value)
    assert "run_tables was given send=, which Toolbox 7.0 replaced." in message
    assert "Pass execute= instead" in message
    assert sent == []
    assert capsys.readouterr().out == ""


def test_run_tables_refuses_a_keyword_it_doesnt_take(two_tables: Path) -> None:
    with pytest.raises(TypeError, match="run_tables was given excute=, which it doesn't take"):
        project.run_tables(excute=print)


def test_run_tables_stops_at_the_first_that_fails(
        two_tables: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def execute(hive: str) -> None:
        if "mart.team_runs" in hive.split("\n")[0]:
            raise RuntimeError("the warehouse said no")

    with pytest.raises(RuntimeError, match="the warehouse said no"):
        project.run_tables(execute=execute)
    assert capsys.readouterr().out == (
        "1 of 2: mart.daily_runs  worked\n"
        "2 of 2: mart.team_runs   failed: see below. The tables after it weren't written.\n")


LOOP_REFERENCE = """from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={"n": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["dt"],
    location="/data/your_team/<DB>.db/<TABLE>",
)
"""
# A table that sums the other one's n: two of them, each reading the other, are a loop.
LOOP_LOGIC = """# %%
# logic
from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE
from sqlglot_composer import between, statement, sum_of
from references.mart__<OTHER> import <OTHER>
from references.<NAME> import <TABLE>


def write():
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(AS(sum_of(<OTHER>.n), "n"), AS(<OTHER>.dt, "dt")),
        FROM(<OTHER>),
        WHERE(between(<OTHER>.dt, "2026-09-24", "2026-09-24")),
        GROUP_BY(<OTHER>.dt),
    )
"""


def test_run_tables_refuses_a_loop(started: Path) -> None:
    templates = started / "admin" / "templates"
    for table, other in (("ping", "pong"), ("pong", "ping")):
        (templates / f"{table}.py").write_text(LOOP_LOGIC.replace("<OTHER>", other),
                                               encoding="utf-8")
        project.new_table(f"mart.{table}", template=table)
        (started / "references" / f"mart__{table}.py").write_text(
            LOOP_REFERENCE.replace("<DB>", "mart").replace("<TABLE>", table), encoding="utf-8")
    with pytest.raises(ValueError, match="project.run_tables.*can't order these tables, "
                       "because they go round in a loop"):
        project.run_tables()


SETTINGS = "<Session settings map_joins - show_hive(...) shows their SET lines>"


@pytest.mark.parametrize(("gives", "said"), [
    ('hive_settings("map_joins")', SETTINGS + ", which isn't a Statement that writes, an Unchecked statement or a Python step"),
    ('"INSERT OVERWRITE TABLE mart.odd"', "'INSERT OVERWRITE TABLE mart.odd', which isn't a Statement that writes, an Unchecked statement or a Python step"),
    ("None", "None, which isn't a Statement that writes, an Unchecked statement or a Python step"),
    ('[hive_settings("map_joins")]', "a list, and " + SETTINGS + " in it isn't a Statement that writes, an Unchecked statement or a Python step"),
    ("(1, 2)", "a tuple, and 1 in it isn't a Statement that writes, an Unchecked statement or a Python step"),
    ("[]", "an empty list, with no write in it"),
])
def test_run_tables_refuses_what_write_gives_that_it_cant_send(
        started: Path, capsys: pytest.CaptureFixture[str], gives: str, said: str) -> None:
    (started / "admin" / "templates" / "odd.py").write_text(
        "# %%\n# logic\nfrom sqlglot_composer import hive_settings\n\n\n"
        f"def write():\n    return {gives}\n", encoding="utf-8")
    project.new_table("mart.odd", template="odd")
    with pytest.raises(TypeError) as refused:
        project.run_tables()
    message = " ".join(str(refused.value).split())
    assert message.count("What happened:") == 1
    assert ("What happened: project.run_tables(): write(), in the "
            f"logic cell of mart.odd's Table notebook, gave {said}.") in message
    assert capsys.readouterr().out == ""


def test_run_tables_refuses_a_read_that_write_gives_before_sending_anything(
        started: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Everything run_tables sends goes through execute, which gives back no rows."""
    (started / "admin" / "templates" / "reads.py").write_text(
        "# %%\n# logic\nfrom sqlglot_composer import FROM, SELECT, statement\n"
        "from sqlglot_composer.example_database import jobs\n\n\n"
        "def write():\n    return statement(SELECT(jobs.job_id), FROM(jobs))\n",
        encoding="utf-8")
    project.new_table("mart.odd", template="reads")
    sent = []
    with pytest.raises(TypeError) as refused:
        project.run_tables(execute=sent.append)
    message = " ".join(str(refused.value).split())
    assert "which isn't a Statement that writes" in message
    assert "a read gives back rows, which only run_query brings back" in message
    assert sent == []
    assert capsys.readouterr().out == ""


def test_run_tables_with_no_table_folder_says_so(started: Path) -> None:
    assert repr(project.run_tables()) == (
        "No Table folder to run: make one with project.new_table(...).")


def test_lineage_crosses_table_folders_through_load(
        two_tables: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_tables / "tables" / "mart__team_runs")
    daily = project.load("mart.daily_runs").write()
    team = project.load("mart.team_runs").write()
    # to= names the files: from a test, rather than a notebook, they would go beside this file.
    _, markdown_file = export_lineage(daily, team, to=two_tables / "both.html")
    text = markdown_file.read_text(encoding="utf-8")
    # The drawing follows ops.job_runs, through mart.daily_runs, to mart.team_runs.
    assert "ops.job_runs" in text and "mart.daily_runs" in text and "mart.team_runs" in text
    assert text.index("mart.daily_runs") < text.index("mart.team_runs")


def test_one_write_s_lineage_goes_in_its_table_folder_named_by_the_time(
        two_tables: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.chdir(two_tables / "admin")
    html_file, markdown_file = export_lineage(project.load("mart.daily_runs").write())
    folder = two_tables / "tables" / "mart__daily_runs" / "lineage"
    assert (html_file, markdown_file) == (folder / "20261021-093000-mart__daily_runs.html",
                                          folder / "20261021-093000-mart__daily_runs.md")
    assert "from your scripts at commit" in markdown_file.read_text(encoding="utf-8")


# --- The Admin log inside a Project -----------------------------------------------------------


def test_an_admin_statement_run_inside_a_project_logs_in_its_admin_folder(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(started / "tables")
    t = Table("mart.daily_runs", columns={"job_id": "bigint", "dt": "string"},
              partitioned_by=["dt"], location="/data/your_team/mart.db/daily_runs")
    run_execute(admin.drop_table(t), lambda hive: None)
    assert "## 2026-10-21 09:30:00, Admin statement\n" in log_text(started)
    assert not (started / "tables" / "admin_log.md").exists()
