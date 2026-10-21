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
import csv
import datetime
import json
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import Table, admin, example_database, project, run, set_admin_log

NOW = datetime.datetime(2026, 10, 21, 9, 30, 0)
ADMIN_NOTEBOOKS = ["add_references", "change_a_saved_table", "check_project", "new_table",
                   "refresh_reference_sheet", "remove_table"]


@pytest.fixture
def started(tmp_path, monkeypatch) -> Path:
    """A Project just started in a folder of its own, the time pinned, the Admin log unmoved."""
    for module in ("project", "unchecked"):
        monkeypatch.setattr(toolbox_module(module), "_now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


def registry(root: Path) -> list[dict]:
    with open(root / "admin" / "registry.csv", encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def cells(path: Path) -> list[tuple[str, str]]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    return [(cell["cell_type"], "".join(cell["source"])) for cell in notebook["cells"]]


def log_text(root: Path) -> str:
    return (root / "admin" / "admin_log.md").read_text(encoding="utf-8")


# --- start ------------------------------------------------------------------------------------


def test_start_lays_out_a_project(started) -> None:
    assert sorted(path.name for path in started.iterdir()) == [
        "admin", "building_blocks", "references", "send.py", "tables"]
    assert sorted(path.name for path in (started / "admin").iterdir()) == sorted(
        ["admin_log.md", "registry.csv", "templates"]
        + [f"{name}.ipynb" for name in ADMIN_NOTEBOOKS])
    assert sorted(path.name for path in (started / "admin" / "templates").iterdir()) == [
        "daily_table.py", "saved_table_reference.py"]
    assert registry(started) == []
    assert (started / "admin" / "registry.csv").read_text(encoding="utf-8") == (
        "kind,table,created_at,removed_at\n")


def test_each_admin_notebook_puts_the_project_on_the_path_and_parses(started) -> None:
    for name in ADMIN_NOTEBOOKS:
        found = cells(started / "admin" / f"{name}.ipynb")
        assert [kind for kind, _ in found[:2]] == ["markdown", "code"], name
        assert "sys.path.insert(0, str(pathlib.Path.cwd().parent))" in found[1][1]
        for kind, text in found:
            if kind == "code":
                ast.parse(text)


def test_send_py_sends_to_the_example_database_until_you_change_it(started) -> None:
    text = (started / "send.py").read_text(encoding="utf-8")
    ast.parse(text)
    assert "return example_database.send(hive)  # at work: your warehouse's call" in text


def test_start_logs_a_project_action(started) -> None:
    assert ("## 2026-10-21 09:30:00, Project action\n\n- Call: `project.start()`\n"
            "- Files: created admin/, references/, building_blocks/, tables/, send.py\n"
            in log_text(started))


@pytest.mark.parametrize("there",
                         ["admin", "references", "building_blocks", "tables", "send.py"])
def test_start_refuses_a_folder_that_has_any_of_its_parts(there, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / there).mkdir()
    with pytest.raises(FileExistsError, match=f"{there}/? is already in the folder"):
        project.start()
    assert [path.name for path in tmp_path.iterdir()] == [there]


def test_start_refuses_a_folder_inside_a_project(started, monkeypatch) -> None:
    monkeypatch.chdir(started / "building_blocks")
    with pytest.raises(FileExistsError, match="was run inside a Project"):
        project.start()
    with pytest.raises(FileExistsError, match="this folder is one"):
        monkeypatch.chdir(started)
        project.start()


# --- new_table --------------------------------------------------------------------------------


def test_new_table_makes_a_table_folder_and_a_reference(started) -> None:
    report = project.new_table("mart.daily_job_runs")
    folder = started / "tables" / "mart__daily_job_runs"
    assert sorted(path.name for path in folder.iterdir()) == [
        "lineage", "mart__daily_job_runs.ipynb"]
    assert list((folder / "lineage").iterdir()) == []
    found = cells(folder / "mart__daily_job_runs.ipynb")
    assert [kind for kind, _ in found] == ["markdown"] + ["code"] * 5
    assert found[0][1].startswith("# mart.daily_job_runs\n\nTODO: say in one line")
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
        "admin/templates/daily_table.py.\n"
        "Wrote references/mart__daily_job_runs.py: fill in its <...> and TODO lines.")
    assert ('- Call: `project.new_table("mart.daily_job_runs")`\n'
            "- Tables named: mart.daily_job_runs\n"
            "- Files: created tables/mart__daily_job_runs/ (mart__daily_job_runs.ipynb, "
            "lineage/); created references/mart__daily_job_runs.py\n") in log_text(started)


def test_new_table_keeps_a_reference_that_is_there(started) -> None:
    reference = started / "references" / "mart__daily_job_runs.py"
    reference.write_text("# mine", encoding="utf-8")
    assert "Kept references/mart__daily_job_runs.py" in repr(
        project.new_table("mart.daily_job_runs"))
    assert reference.read_text(encoding="utf-8") == "# mine"
    assert [row["kind"] for row in registry(started)] == ["table_folder"]


def test_new_table_uses_a_template_of_yours(started) -> None:
    (started / "admin" / "templates" / "mine.py").write_text(
        "# %% [markdown]\n# # <DB>.<TABLE>\n\n# %%\n# logic\nNAME = '<NAME>'\n",
        encoding="utf-8")
    project.new_table("mart.daily_job_runs", template="mine")
    notebook = started / "tables" / "mart__daily_job_runs" / "mart__daily_job_runs.ipynb"
    assert cells(notebook) == [("markdown", "# mart.daily_job_runs"),
                               ("code", "# logic\nNAME = 'mart__daily_job_runs'")]
    assert 'project.new_table("mart.daily_job_runs", template="mine")' in log_text(started)


def test_new_table_refuses_a_table_folder_that_is_there(started) -> None:
    project.new_table("mart.daily_job_runs")
    notebook = started / "tables" / "mart__daily_job_runs" / "mart__daily_job_runs.ipynb"
    notebook.write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="tables/mart__daily_job_runs/ is already there"):
        project.new_table("mart.daily_job_runs")
    assert notebook.read_text(encoding="utf-8") == "{}"


def test_new_table_refuses_a_table_the_registry_lists(started) -> None:
    project.new_table("mart.daily_job_runs")
    folder = started / "tables" / "mart__daily_job_runs"
    for path in sorted(folder.rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    folder.rmdir()
    with pytest.raises(FileExistsError, match="the registry lists a Table folder for"):
        project.new_table("mart.daily_job_runs")
    assert not folder.exists()


@pytest.mark.parametrize(("name", "template", "error", "said"), [
    ("daily_job_runs", "daily_table", ValueError, "isn't a table's name with its database"),
    ("mart.daily-runs", "daily_table", ValueError, "isn't a table's name with its database"),
    ("mart.class", "daily_table", ValueError, "a word Python keeps for itself"),
    ("mart.daily_job_runs", "dialy_table", FileNotFoundError,
     "(?s)there is no Template 'dialy_table'.*Use one of: 'daily_table'"),
])
def test_new_table_refuses(started, name, template, error, said) -> None:
    with pytest.raises(error, match=said):
        project.new_table(name, template=template)
    assert list((started / "tables").iterdir()) == []
    assert registry(started) == []


def test_a_project_action_outside_a_project_is_refused(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="was run outside a Project"):
        project.new_table("mart.daily_job_runs")
    assert list(tmp_path.iterdir()) == []


def test_a_project_action_runs_from_any_folder_inside_it(started, monkeypatch) -> None:
    monkeypatch.chdir(started / "admin")
    project.new_table("mart.daily_job_runs")
    assert (started / "tables" / "mart__daily_job_runs").is_dir()


# --- remove_table and remove_reference --------------------------------------------------------


def test_remove_table_archives_the_folder_and_keeps_the_reference(started) -> None:
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


def test_remove_table_refuses_a_table_folder_neither_there_nor_registered(started) -> None:
    with pytest.raises(FileNotFoundError, match="there is no tables/mart__daily_job_runs/ to "
                       "remove, and the registry lists none"):
        project.remove_table("mart.daily_job_runs")


def test_remove_table_marks_removed_a_registered_folder_deleted_by_hand(started) -> None:
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


def test_remove_reference_archives_the_file(started) -> None:
    project.new_table("mart.daily_job_runs")
    project.remove_table("mart.daily_job_runs")
    project.remove_reference("mart.daily_job_runs")
    archived = started / "admin" / "removed" / "20261021-093000-mart__daily_job_runs.py"
    assert "daily_job_runs = Table(" in archived.read_text(encoding="utf-8")
    assert not (started / "references" / "mart__daily_job_runs.py").exists()
    assert [row["removed_at"] for row in registry(started)] == ["2026-10-21 09:30:00"] * 2


def test_remove_reference_refuses_while_its_table_folder_is_there(started) -> None:
    project.new_table("mart.daily_job_runs")
    with pytest.raises(ValueError, match="tables/mart__daily_job_runs/ is still there"):
        project.remove_reference("mart.daily_job_runs")
    assert (started / "references" / "mart__daily_job_runs.py").is_file()


def test_remove_reference_refuses_a_file_that_isnt_there(started) -> None:
    with pytest.raises(FileNotFoundError, match="there is no references/ops__jobs.py"):
        project.remove_reference("ops.jobs")


def test_new_table_doesnt_register_a_reference_twice(started) -> None:
    project.new_table("mart.daily_job_runs")
    project.remove_table("mart.daily_job_runs")
    (started / "references" / "mart__daily_job_runs.py").unlink()
    project.new_table("mart.daily_job_runs")
    assert [(row["kind"], row["removed_at"]) for row in registry(started)] == [
        ("table_folder", "2026-10-21 09:30:00"), ("reference", ""), ("table_folder", "")]


# --- register and check -----------------------------------------------------------------------


def test_check_finds_nothing_in_a_new_project(started) -> None:
    assert repr(project.check()) == ("Every Table folder and Table reference is registered, "
                                     "and each one registered is there.")


def test_check_reports_what_was_made_or_moved_by_hand(started) -> None:
    project.new_table("mart.daily_job_runs")
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    (started / "tables" / "mart__by_hand").mkdir()
    (started / "references" / "mart__daily_job_runs.py").unlink()
    assert repr(project.check()) == (
        "Not registered, made by hand: references/ops__jobs.py, tables/mart__by_hand/. Adopt "
        "each with\nproject.register(...).\n"
        "Registered, but not there: references/mart__daily_job_runs.py. Put each back, or\n"
        "mark it removed with project.remove_table(...) or project.remove_reference(...).")


def test_check_changes_nothing(started) -> None:
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    before = log_text(started)
    project.check()
    assert log_text(started) == before
    assert registry(started) == []


def test_register_adopts_what_was_made_by_hand(started) -> None:
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    assert repr(project.register("ops.jobs")) == "Registered references/ops__jobs.py."
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "ops.jobs")]
    assert "- Files: registered references/ops__jobs.py\n" in log_text(started)
    assert "registered" in repr(project.check())


def test_register_refuses_when_there_is_nothing_to_adopt(started) -> None:
    project.new_table("mart.daily_job_runs")
    with pytest.raises(ValueError, match="nothing to register"):
        project.register("mart.daily_job_runs")
    with pytest.raises(ValueError, match="nothing to register"):
        project.register("ops.jobs")


# --- add_references ---------------------------------------------------------------------------


def failing_on(missing: str):
    """The Example database's send, but a table it doesn't have fails, as a warehouse's does."""
    def send(hive):
        if missing in hive:
            raise RuntimeError(f"Table not found: {missing}")
        return example_database.send(hive)

    return send


def test_add_references_writes_each_table_and_registers_it(started) -> None:
    report = project.add_references(["ops.jobs", "ops.job_runs"], send=example_database.send)
    assert sorted(path.name for path in (started / "references").iterdir()) == [
        "ops__job_runs.py", "ops__jobs.py"]
    assert "from references.ops__jobs import jobs, <alias>" in (
        started / "references" / "ops__jobs.py").read_text(encoding="utf-8")
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "ops.jobs"), ("reference", "ops.job_runs")]
    assert repr(report) == ("Wrote references/ops__jobs.py and references/ops__job_runs.py: "
                            "fill in their TODO lines.")


def test_add_references_skips_what_it_cant_write_and_finishes_the_list(started) -> None:
    (started / "references" / "ops__jobs.py").write_text("# mine", encoding="utf-8")
    with pytest.raises(project.SkippedTables) as skipped:
        project.add_references(["ops.jobs", "ops.job_ownres", "jobs", "ops.run_alerts"],
                               send=failing_on("ops.job_ownres"))
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
            '"ops.run_alerts"], send=...)`\n') in log
    assert "- Files: created references/ops__run_alerts.py\n" in log
    assert ("- Skipped: ops.jobs (references/ops__jobs.py is there already); "
            "ops.job_ownres") in log
    assert "- Result: 1 of 4 written; SkippedTables named the rest, above\n" in log


def test_add_references_refuses_a_name_where_a_list_goes(started) -> None:
    with pytest.raises(ValueError, match="names isn't a list of tables"):
        project.add_references("ops.jobs", send=example_database.send)


# --- The Reference sheet ----------------------------------------------------------------------


def sheet(root: Path) -> list[dict]:
    path = root / "references" / "reference_sheet.csv"
    with open(path, encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def test_the_reference_sheet_has_a_row_per_column_with_its_aliases(started) -> None:
    project.add_references(["ops.job_runs"], send=example_database.send)
    reference = started / "references" / "ops__job_runs.py"
    text = reference.read_text(encoding="utf-8").replace("key=None,", 'key=["run_id"],')
    reference.write_text(text + "minutes = job_runs.duration_mins\n"
                         "failed = job_runs.status == 'x'\n", encoding="utf-8")
    report = project.refresh_reference_sheet()
    rows = {row["column"]: row for row in sheet(started)}
    assert list(rows) == ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs", "dt"]
    assert rows["run_id"] | {"exported_at": ""} == {
        "table": "ops.job_runs", "column": "run_id", "type": "bigint", "date_partition": "",
        "in_key": "yes", "aliases": "", "description": "", "exported_at": ""}
    assert rows["dt"]["date_partition"] == "yes"
    assert rows["duration_mins"]["aliases"] == "minutes"
    assert rows["status"]["description"] == "SUCCESS / FAILED / TEST, NULL while running"
    assert {row["exported_at"] for row in rows.values()} == {"2026-10-21 09:30:00"}
    assert repr(report) == "Wrote references/reference_sheet.csv: 6 rows, 1 table."


def test_refreshing_one_table_replaces_only_its_rows(started, monkeypatch) -> None:
    project.add_references(["ops.jobs", "ops.run_alerts"], send=example_database.send)
    project.refresh_reference_sheet()
    later = datetime.datetime(2026, 10, 22, 8, 0, 0)
    monkeypatch.setattr(toolbox_module("project"), "_now", lambda: later)
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


def test_a_reference_still_to_fill_in_is_left_out_of_the_sheet(started) -> None:
    project.new_table("mart.daily_job_runs")
    project.add_references(["ops.jobs"], send=example_database.send)
    assert repr(project.refresh_reference_sheet()) == (
        "Wrote references/reference_sheet.csv: 4 rows, 1 table.\n"
        "Left out, since it can't be read yet: references/mart__daily_job_runs.py. Fill in "
        "every <...> in it, and check it holds a Table(...) call, then refresh again.")


def test_a_named_refresh_keeps_the_rows_of_a_file_that_cant_be_read(started) -> None:
    project.add_references(["ops.jobs"], send=example_database.send)
    project.refresh_reference_sheet()
    reference = started / "references" / "ops__jobs.py"
    reference.write_text(reference.read_text(encoding="utf-8") + "oops = <ALIAS>" + "\n",
                         encoding="utf-8")
    assert "its rows from before are kept until then" in repr(
        project.refresh_reference_sheet("ops.jobs"))
    assert len(sheet(started)) == 4


def test_a_describe_refused_by_the_toolbox_is_named_by_what_happened(started) -> None:
    """A Toolbox refusal from inside add_references is one line of the error, not a second
    four-part message inside the first."""
    with pytest.raises(project.SkippedTables) as skipped:
        project.add_references(["ops.empty"], send=lambda hive: pd.DataFrame(
            columns=["col_name", "data_type", "comment"]))
    message = str(skipped.value)
    assert message.count("What happened:") == 1
    assert "ops.empty (DESCRIBE failed: ValueError: write_table_reference('ops.empty', ...): "
    assert "DESCRIBE ops.empty listed no columns.)" in " ".join(message.split())


def test_refreshing_a_table_with_no_reference_is_refused(started) -> None:
    with pytest.raises(FileNotFoundError, match="there is no references/ops__jobs.py to read"):
        project.refresh_reference_sheet("ops.jobs")


# --- The Admin log inside a Project -----------------------------------------------------------


def test_an_admin_statement_run_inside_a_project_logs_in_its_admin_folder(started,
                                                                          monkeypatch) -> None:
    monkeypatch.chdir(started / "tables")
    t = Table("mart.daily_runs", columns={"job_id": "bigint", "dt": "string"},
              date_partition="dt", location="/data/your_team/tables")
    run(admin.drop_table(t), send=lambda hive: None)
    assert "## 2026-10-21 09:30:00, Admin statement\n" in log_text(started)
    assert not (started / "tables" / "admin_log.md").exists()
