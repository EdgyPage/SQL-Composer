"""project.new_run_value: a Run value's function written for you. Toolbox 8.5, ticket 06.

Every W7 run wrote building_blocks/run_values.py by hand and registered it from no cell. The
common case, the latest Partition of a table, is now one call, which writes the function and
its imports into that file, made if missing, registers it, and prints the import line for the
decisions cell. Run again as it was, as a decisions cell holding it is run again, it changes
nothing. Any other kind of function is the file to edit.
"""

from __future__ import annotations

import datetime
import importlib
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project

workflows = toolbox_module("workflows")

RUN_VALUES = Path("building_blocks") / "run_values.py"
IMPORT_LINE = "from building_blocks.run_values import period_end"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project holding the Table references of ops.job_runs, ops.jobs and
    ops.job_events, its conn the Example database."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references(["ops.job_runs", "ops.jobs", "ops.job_events"],
                           query=example_database.query)
    yield tmp_path
    forget_the_projects_modules()


def _registry_rows(root: Path) -> list[str]:
    text = (root / "admin" / "registry.csv").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if "run_values" in line]


def _period_end() -> object:
    forget_the_projects_modules()
    return importlib.import_module("building_blocks.run_values").period_end


def test_it_writes_the_latest_partition_of_a_table(started: Path) -> None:
    said = repr(project.new_run_value("period_end", latest_partition="ops.job_runs.dt"))
    text = (started / RUN_VALUES).read_text(encoding="utf-8")
    assert text.startswith('"""Run values: ')
    for line in ["import datetime",
                 "from sqlglot_composer import latest_partition",
                 "from references.ops__job_runs import job_runs",
                 "from warehouse import query",
                 "def period_end() -> datetime.date | int | str:",
                 "    return latest_partition(job_runs.dt, query)"]:
        assert f"\n{line}\n" in text, line
    assert _period_end()() == datetime.date(2026, 9, 24)
    assert said == (
        "Wrote period_end into building_blocks/run_values.py: the latest Partition of "
        "ops.job_runs, by dt.\n"
        "Registered building_blocks/run_values.py.\n"
        "Import it at the top of the decisions cell:\n"
        f"{IMPORT_LINE}")
    assert len(_registry_rows(started)) == 1
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert ('- Call: `project.new_run_value("period_end", '
            'latest_partition="ops.job_runs.dt")`') in log


def test_a_second_adds_only_the_imports_it_lacks(started: Path) -> None:
    project.new_run_value("period_end", latest_partition="ops.job_runs.dt")
    said = repr(project.new_run_value("latest_event_day",
                                      latest_partition="ops.job_events.dt"))
    text = (started / RUN_VALUES).read_text(encoding="utf-8")
    assert text.count("import datetime\n") == 1
    assert text.count("from warehouse import query\n") == 1
    assert "from references.ops__job_events import job_events\n" in text
    assert "    return latest_partition(job_events.dt, query)" in text
    assert "Registered" not in said
    assert "from building_blocks.run_values import latest_event_day" in said
    assert len(_registry_rows(started)) == 1


def test_an_integer_partition_column_gives_a_number(started: Path) -> None:
    (started / "references" / "ops__job_years.py").write_text(
        'from sqlglot_composer import Table\n\njob_years = Table("ops.job_years", columns={'
        '"job_id": "bigint", "year": "int"}, partitioned_by=["year"])\n', encoding="utf-8")
    project.new_run_value("latest_year", latest_partition="ops.job_years.year")
    text = (started / RUN_VALUES).read_text(encoding="utf-8")
    assert "\ndef latest_year() -> int:\n" in text
    assert "import datetime" not in text


def test_a_table_named_as_one_imported_already_is_imported_by_its_files_name(
        started: Path) -> None:
    (started / RUN_VALUES).write_text(
        '"""Mine."""\n\nfrom references.ops__jobs import jobs as job_runs\n', encoding="utf-8")
    project.new_run_value("period_end", latest_partition="ops.job_runs.dt")
    text = (started / RUN_VALUES).read_text(encoding="utf-8")
    assert "from references.ops__job_runs import job_runs as ops__job_runs\n" in text
    assert "    return latest_partition(ops__job_runs.dt, query)" in text
    assert _period_end()() == datetime.date(2026, 9, 24)


def test_run_again_as_it_was_it_changes_nothing(started: Path) -> None:
    project.new_run_value("period_end", latest_partition="ops.job_runs.dt")
    before = (started / RUN_VALUES).read_text(encoding="utf-8")
    said = repr(project.new_run_value("period_end", latest_partition="ops.job_runs.dt"))
    assert said == ("building_blocks/run_values.py holds period_end already, as this call "
                    "writes it: nothing changed.\n"
                    "Import it at the top of the decisions cell:\n"
                    f"{IMPORT_LINE}")
    assert (started / RUN_VALUES).read_text(encoding="utf-8") == before
    assert len(_registry_rows(started)) == 1


def test_it_adds_to_a_file_written_by_hand_and_registers_it(started: Path) -> None:
    (started / RUN_VALUES).write_text(
        '"""My Run values."""\n\nimport datetime\n\n\ndef month_end() -> datetime.date:\n'
        '    return datetime.date(2026, 9, 30)\n', encoding="utf-8")
    said = repr(project.new_run_value("period_end", latest_partition="ops.job_runs.dt"))
    text = (started / RUN_VALUES).read_text(encoding="utf-8")
    assert text.startswith('"""My Run values."""\n\nimport datetime\n'
                           "from sqlglot_composer import latest_partition\n")
    assert "def month_end() -> datetime.date:" in text
    assert "Registered building_blocks/run_values.py." in said
    assert _period_end()() == datetime.date(2026, 9, 24)


def test_a_name_already_in_the_file_is_refused(started: Path) -> None:
    (started / RUN_VALUES).write_text(
        "import datetime\n\n\ndef period_end() -> datetime.date:\n"
        "    return datetime.date(2026, 9, 30)\n", encoding="utf-8")
    before = (started / RUN_VALUES).read_text(encoding="utf-8")
    with pytest.raises(FileExistsError,
                       match="building_blocks/run_values.py has a period_end already"):
        project.new_run_value("period_end", latest_partition="ops.job_runs.dt")
    with pytest.raises(FileExistsError, match="has a datetime already"):
        project.new_run_value("datetime", latest_partition="ops.job_runs.dt")
    assert (started / RUN_VALUES).read_text(encoding="utf-8") == before


def test_a_table_with_no_table_reference_is_refused(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match=(
            r"ops.run_alerts has no Table reference, references/ops__run_alerts.py(.|\n)*"
            r"admin/workflows/references/references.ipynb")):
        project.new_run_value("period_end", latest_partition="ops.run_alerts.dt")
    assert not (started / RUN_VALUES).exists()


def test_a_column_that_isnt_a_partition_column_is_refused(started: Path) -> None:
    with pytest.raises(ValueError, match=(
            "status isn't a partition column of ops.job_runs: its partition column is dt")):
        project.new_run_value("period_end", latest_partition="ops.job_runs.status")
    with pytest.raises(ValueError, match="ops.jobs has no partition column"):
        project.new_run_value("period_end", latest_partition="ops.jobs.job_id")
    assert not (started / RUN_VALUES).exists()


@pytest.mark.parametrize("given", ["ops.job_runs", "job_runs.dt.x.y", "", 7])
def test_a_latest_partition_that_isnt_a_column_by_its_table_is_refused(
        started: Path, given: object) -> None:
    with pytest.raises(ValueError, match="isn't a partition column by its table's name"):
        project.new_run_value("period_end", latest_partition=given)  # type: ignore[arg-type]


@pytest.mark.parametrize(("name", "said"), [
    ("period-end", "isn't a name Python can import a Run value by"),
    ("1st", "isn't a name Python can import a Run value by"),
    ("class", "class is a name Python keeps for itself"),
])
def test_a_name_python_cant_import_is_refused(started: Path, name: str, said: str) -> None:
    with pytest.raises(ValueError, match=said):
        project.new_run_value(name, latest_partition="ops.job_runs.dt")


def test_the_decisions_cell_names_it() -> None:
    assert 'project.new_run_value("period_end", latest_partition=' in workflows.DECISIONS_CELL
