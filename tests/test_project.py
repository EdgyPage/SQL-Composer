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
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import (
    Table,
    admin,
    example_database,
    export_lineage,
    project,
    run,
    set_admin_log,
    to_hive,
)

NOW = datetime.datetime(2026, 10, 21, 9, 30, 0)
ADMIN_NOTEBOOKS = ["add_references", "change_a_saved_table", "check_project", "new_table",
                   "refresh_reference_sheet", "remove_table", "run_tables"]


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project just started in a folder of its own, the time pinned, the Admin log unmoved."""
    for module in ("project", "unchecked"):
        monkeypatch.setattr(toolbox_module(module), "_now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


def registry(root: Path) -> list[dict[str, str]]:
    with open(root / "admin" / "registry.csv", encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def cells(path: Path) -> list[tuple[str, str]]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    return [(cell["cell_type"], "".join(cell["source"])) for cell in notebook["cells"]]


def log_text(root: Path) -> str:
    return (root / "admin" / "admin_log.md").read_text(encoding="utf-8")


# --- start ------------------------------------------------------------------------------------


def test_start_lays_out_a_project(started: Path) -> None:
    assert sorted(path.name for path in started.iterdir()) == [
        "admin", "building_blocks", "references", "send.py", "tables"]
    assert sorted(path.name for path in (started / "admin").iterdir()) == sorted(
        ["admin_log.md", "registry.csv", "templates"]
        + [f"{name}.ipynb" for name in ADMIN_NOTEBOOKS])
    assert sorted(path.name for path in (started / "admin" / "templates").iterdir()) == [
        "as_of_lookup.py", "building_block.py", "daily_table.py", "incremental_load.py",
        "quality_checks.py", "saved_table_reference.py", "weekly_rollup.py"]
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


def test_send_py_sends_to_the_example_database_until_you_change_it(started: Path) -> None:
    text = (started / "send.py").read_text(encoding="utf-8")
    ast.parse(text)
    assert "return example_database.send(hive)  # at work: your warehouse's call" in text


def test_start_logs_a_project_action(started: Path) -> None:
    assert ("## 2026-10-21 09:30:00, Project action\n\n- Call: `project.start()`\n"
            "- Files: created admin/, references/, building_blocks/, tables/, send.py\n"
            in log_text(started))


@pytest.mark.parametrize("there",
                         ["admin", "references", "building_blocks", "tables", "send.py"])
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
    with pytest.raises(FileExistsError, match="this folder is one"):
        monkeypatch.chdir(started)
        project.start()


# --- new_table --------------------------------------------------------------------------------


def test_new_table_makes_a_table_folder_and_a_reference(started: Path) -> None:
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
    ("daily_job_runs", "daily_table", ValueError, "isn't a table's name with its database"),
    ("mart.daily-runs", "daily_table", ValueError, "isn't a table's name with its database"),
    ("mart.class", "daily_table", ValueError, "a word Python keeps for itself"),
    ("mart.daily_job_runs", "dialy_table", FileNotFoundError,
     "(?s)there is no Table notebook Template 'dialy_table'.*Use one of: 'as_of_lookup', "
     "'daily_table', 'incremental_load', 'quality_checks', 'weekly_rollup',"),
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
    assert repr(project.check()) == ("Every Table folder and Table reference is registered, "
                                     "and each one registered is there.")


def test_check_reports_what_was_made_or_moved_by_hand(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    (started / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    (started / "tables" / "mart__by_hand").mkdir()
    (started / "references" / "mart__daily_job_runs.py").unlink()
    assert repr(project.check()) == (
        "Not registered, made by hand: references/ops__jobs.py, tables/mart__by_hand/. Adopt "
        "each with\nproject.register(...).\n"
        "Registered, but not there: references/mart__daily_job_runs.py. Put each back, or\n"
        "mark it removed with project.remove_table(...) or project.remove_reference(...).")


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


# --- add_references ---------------------------------------------------------------------------


def failing_on(missing: str) -> Callable[..., pd.DataFrame]:
    """The Example database's send, but a table it doesn't have fails, as a warehouse's does."""
    def send(hive: str) -> pd.DataFrame:
        if missing in hive:
            raise RuntimeError(f"Table not found: {missing}")
        return example_database.send(hive)

    return send


def test_add_references_writes_each_table_and_registers_it(started: Path) -> None:
    report = project.add_references(["ops.jobs", "ops.job_runs"], send=example_database.send)
    assert sorted(path.name for path in (started / "references").iterdir()) == [
        "ops__job_runs.py", "ops__jobs.py"]
    assert "from references.ops__jobs import jobs, <alias>" in (
        started / "references" / "ops__jobs.py").read_text(encoding="utf-8")
    assert [(row["kind"], row["table"]) for row in registry(started)] == [
        ("reference", "ops.jobs"), ("reference", "ops.job_runs")]
    assert repr(report) == ("Wrote references/ops__jobs.py and references/ops__job_runs.py: "
                            "fill in their TODO lines.")


def test_add_references_names_three_files_or_more_as_a_sentence_does(started: Path) -> None:
    report = project.add_references(["ops.jobs", "ops.job_runs", "ops.run_alerts"],
                                    send=example_database.send)
    assert repr(report) == ("Wrote references/ops__jobs.py, references/ops__job_runs.py and "
                            "references/ops__run_alerts.py: fill in their TODO lines.")


def test_add_references_skips_what_it_cant_write_and_finishes_the_list(started: Path) -> None:
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


def test_add_references_refuses_a_name_where_a_list_goes(started: Path) -> None:
    with pytest.raises(ValueError, match="names isn't a list of tables"):
        project.add_references("ops.jobs", send=example_database.send)


# --- The Reference sheet ----------------------------------------------------------------------


def sheet(root: Path) -> list[dict[str, str]]:
    path = root / "references" / "reference_sheet.csv"
    with open(path, encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def test_the_reference_sheet_has_a_row_per_column_with_its_aliases(started: Path) -> None:
    project.add_references(["ops.job_runs"], send=example_database.send)
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
        "table": "ops.job_runs", "column": "run_id", "type": "bigint", "date_partition": "",
        "in_key": "yes", "aliases": "", "description": "", "exported_at": ""}
    assert rows["dt"]["date_partition"] == "yes"
    assert rows["duration_mins"]["aliases"] == "minutes"
    assert rows["status"]["aliases"] == "failed (a condition)"
    assert rows["avg_retry_secs"]["aliases"] == ""  # slow reads two columns
    assert rows["status"]["description"] == "SUCCESS / FAILED / TEST, NULL while running"
    assert {row["exported_at"] for row in rows.values()} == {"2026-10-21 09:30:00"}
    assert repr(report) == "Wrote references/reference_sheet.csv: 6 rows, 1 table."


def test_refreshing_one_table_replaces_only_its_rows(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_a_reference_still_to_fill_in_is_left_out_of_the_sheet(started: Path) -> None:
    project.new_table("mart.daily_job_runs")
    project.add_references(["ops.jobs"], send=example_database.send)
    assert repr(project.refresh_reference_sheet()) == (
        "Wrote references/reference_sheet.csv: 4 rows, 1 table.\n"
        "Left out, since it can't be read yet: references/mart__daily_job_runs.py. Fill in "
        "every <...> in it, and check it holds a Table(...) call, then refresh again.")


def test_a_named_refresh_keeps_the_rows_of_a_file_that_cant_be_read(started: Path) -> None:
    project.add_references(["ops.jobs"], send=example_database.send)
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
        project.add_references(["ops.empty"], send=lambda hive: pd.DataFrame(
            columns=["col_name", "data_type", "comment"]))
    message = str(skipped.value)
    assert message.count("What happened:") == 1
    assert "ops.empty (DESCRIBE failed: ValueError: write_table_reference('ops.empty', ...): "
    assert "DESCRIBE ops.empty listed no columns.)" in " ".join(message.split())


def test_refreshing_a_table_with_no_reference_is_refused(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match="there is no references/ops__jobs.py to read"):
        project.refresh_reference_sheet("ops.jobs")


# --- load, run_tables and lineage ------------------------------------------------------------

DAILY_RUNS = """from sqlglot_composer import Table

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    date_partition="dt",
    key=["job_id", "dt"],
    location="/data/your_team/tables",
)
"""
TEAM_RUNS = """from sqlglot_composer import Table

team_runs = Table(
    "mart.team_runs",
    columns={"runs": "bigint", "dt": "string"},
    date_partition="dt",
    key=["dt"],
    location="/data/your_team/tables",
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


def write_day(day):
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, day, day)),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )

# %%
run(write_day("2026-09-24"), send=send)
"""
TEAM_LOGIC = """# %%
# logic
from sqlglot_composer import (
    AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE, between, statement, sum_of,
)
from references.mart__daily_runs import daily_runs
from references.<NAME> import <TABLE>


def write_day(day):
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(AS(sum_of(daily_runs.runs), "runs")),
        FROM(daily_runs),
        WHERE(between(daily_runs.dt, day, day)),
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
    project.add_references(["ops.job_runs"], send=example_database.send)
    project.new_table("mart.daily_runs", template="daily")
    project.new_table("mart.team_runs", template="team")
    (started / "references" / "mart__daily_runs.py").write_text(DAILY_RUNS, encoding="utf-8")
    (started / "references" / "mart__team_runs.py").write_text(TEAM_RUNS, encoding="utf-8")
    return started


def notebook_of(root: Path, stem: str) -> Path:
    return root / "tables" / stem / f"{stem}.ipynb"


def test_load_gives_the_logic_cells_functions(two_tables: Path) -> None:
    logic = project.load("mart.daily_runs")
    assert repr(logic) == "The logic of mart.daily_runs: write_day."
    assert to_hive(logic.write_day("2026-09-24")).startswith(
        "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-24')")


def test_load_reads_the_references_as_they_are_now(two_tables: Path) -> None:
    project.load("mart.daily_runs")
    reference = two_tables / "references" / "mart__daily_runs.py"
    reference.write_text(DAILY_RUNS.replace('"mart.daily_runs"', '"mart.daily_runs_v2"'),
                         encoding="utf-8")
    write = project.load("mart.daily_runs").write_day("2026-09-24")
    assert "mart.daily_runs_v2" in to_hive(write)


def test_load_refuses_a_notebook_it_cant_find(two_tables: Path) -> None:
    with pytest.raises(FileNotFoundError,
                       match="there is no tables/mart__nope/mart__nope.ipynb"):
        project.load("mart.nope")


@pytest.mark.parametrize(("logic", "said"), [
    ("x = 1\n", "has no cell whose first line is # logic"),
    ("# logic\nfrom references.<SOURCE> import x\n", "isn't Python yet, at its line 2"),
    ("# logic\nfrom sqlglot_composer import run\nrun(1, send=print)\n", "calls run"),
    ("# logic\nfrom sqlglot_composer import run as go\ngo(1, send=print)\n", "calls run"),
    ("# logical next steps\nx = 1\n", "has no cell whose first line is # logic"),
])
def test_load_refuses_a_logic_cell_it_cant_run_safely(
        two_tables: Path, logic: str, said: str) -> None:
    (two_tables / "admin" / "templates" / "odd.py").write_text(f"# %%\n{logic}",
                                                               encoding="utf-8")
    project.new_table("mart.odd", template="odd")
    with pytest.raises(ValueError, match=said):
        project.load("mart.odd")


def test_run_tables_with_no_send_prints_each_write_writers_first(
        two_tables: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = project.run_tables("2026-09-24", tables=["mart.team_runs", "mart.daily_runs"])
    printed = capsys.readouterr().out
    daily = printed.index("-- 1 of 2: mart.daily_runs\nINSERT OVERWRITE TABLE mart.daily_runs")
    team = printed.index("-- 2 of 2: mart.team_runs\nINSERT OVERWRITE TABLE mart.team_runs")
    assert daily < team
    assert repr(report) == ("Printed 2 writes in order, and sent nothing. Pass send= to run "
                            "them.")


def test_run_tables_sends_every_registered_table_in_order(two_tables: Path) -> None:
    sent = []
    report = project.run_tables("2026-09-24", send=sent.append)
    assert [hive.split("\n")[0] for hive in sent] == [
        "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-24')",
        "INSERT OVERWRITE TABLE mart.team_runs PARTITION(dt = '2026-09-24')"]
    assert repr(report) == "Wrote 2026-09-24 of 2 tables, in order."


def test_run_tables_stops_at_the_first_that_fails(
        two_tables: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def send(hive: str) -> None:
        if "mart.team_runs" in hive.split("\n")[0]:
            raise RuntimeError("the warehouse said no")

    with pytest.raises(RuntimeError, match="the warehouse said no"):
        project.run_tables("2026-09-24", send=send)
    assert capsys.readouterr().out == (
        "1 of 2: mart.daily_runs  worked\n"
        "2 of 2: mart.team_runs   failed: see below. The tables after it weren't written.\n")


LOOP_REFERENCE = """from sqlglot_composer import Table

<TABLE> = Table(
    "<DB>.<TABLE>",
    columns={"n": "bigint", "dt": "string"},
    date_partition="dt",
    key=["dt"],
    location="/data/your_team/tables",
)
"""
# A table that sums the other one's n: two of them, each reading the other, are a loop.
LOOP_LOGIC = """# %%
# logic
from sqlglot_composer import AS, FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, WHERE
from sqlglot_composer import between, statement, sum_of
from references.mart__<OTHER> import <OTHER>
from references.<NAME> import <TABLE>


def write_day(day):
    return statement(
        INSERT_OVERWRITE(<TABLE>),
        SELECT(AS(sum_of(<OTHER>.n), "n")),
        FROM(<OTHER>),
        WHERE(between(<OTHER>.dt, day, day)),
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
        project.run_tables("2026-09-24")


SETTINGS = "<Session settings map_joins - show_hive(...) shows their SET lines>"


@pytest.mark.parametrize(("gives", "said"), [
    ('hive_settings("map_joins")', SETTINGS + ", which isn't a Statement or an Unchecked statement"),
    ('"INSERT OVERWRITE TABLE mart.odd"', "'INSERT OVERWRITE TABLE mart.odd', which isn't a Statement or an Unchecked statement"),
    ("None", "None, which isn't a Statement or an Unchecked statement"),
    ('[hive_settings("map_joins")]', "a list, and " + SETTINGS + " in it isn't a Statement or an Unchecked statement"),
    ("(1, 2)", "a tuple, and 1 in it isn't a Statement or an Unchecked statement"),
    ("[]", "an empty list, with no write in it"),
])
def test_run_tables_refuses_what_write_day_gives_that_it_cant_send(
        started: Path, capsys: pytest.CaptureFixture[str], gives: str, said: str) -> None:
    (started / "admin" / "templates" / "odd.py").write_text(
        "# %%\n# logic\nfrom sqlglot_composer import hive_settings\n\n\n"
        f"def write_day(day):\n    return {gives}\n", encoding="utf-8")
    project.new_table("mart.odd", template="odd")
    with pytest.raises(TypeError) as refused:
        project.run_tables("2026-09-24")
    message = " ".join(str(refused.value).split())
    assert message.count("What happened:") == 1
    assert ('What happened: project.run_tables("2026-09-24"): write_day("2026-09-24"), in the '
            f"logic cell of mart.odd's Table notebook, gave {said}.") in message
    assert capsys.readouterr().out == ""


def test_run_tables_with_no_table_folder_says_so(started: Path) -> None:
    assert repr(project.run_tables("2026-09-24")) == (
        "No Table folder to run: make one with project.new_table(...).")


def test_lineage_crosses_table_folders_through_load(
        two_tables: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(two_tables / "tables" / "mart__team_runs")
    daily = project.load("mart.daily_runs").write_day("2026-09-24")
    team = project.load("mart.team_runs").write_day("2026-09-24")
    # to= names the files: from a test, rather than a notebook, they would go beside this file.
    _, markdown_file = export_lineage(daily, team, to=two_tables / "both.html")
    text = markdown_file.read_text(encoding="utf-8")
    # The drawing follows ops.job_runs, through mart.daily_runs, to mart.team_runs.
    assert "ops.job_runs" in text and "mart.daily_runs" in text and "mart.team_runs" in text
    assert text.index("mart.daily_runs") < text.index("mart.team_runs")


def test_one_write_s_lineage_goes_in_its_table_folder_named_by_the_time(
        two_tables: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("lineage"), "_now", lambda: NOW)
    monkeypatch.chdir(two_tables / "admin")
    html_file, markdown_file = export_lineage(project.load("mart.daily_runs").write_day(
        "2026-09-24"))
    folder = two_tables / "tables" / "mart__daily_runs" / "lineage"
    assert (html_file, markdown_file) == (folder / "20261021-093000-mart__daily_runs.html",
                                          folder / "20261021-093000-mart__daily_runs.md")
    assert "from your scripts at commit" in markdown_file.read_text(encoding="utf-8")


# --- The Admin log inside a Project -----------------------------------------------------------


def test_an_admin_statement_run_inside_a_project_logs_in_its_admin_folder(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(started / "tables")
    t = Table("mart.daily_runs", columns={"job_id": "bigint", "dt": "string"},
              date_partition="dt", location="/data/your_team/tables")
    run(admin.drop_table(t), send=lambda hive: None)
    assert "## 2026-10-21 09:30:00, Admin statement\n" in log_text(started)
    assert not (started / "tables" / "admin_log.md").exists()
