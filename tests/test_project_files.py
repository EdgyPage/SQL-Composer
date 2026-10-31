"""The registry and each kind of thing a Project action makes, as data: Toolbox 7.1's ticket 12.

project_files.py holds, for a Table folder, a Table reference and a Building block, its path,
its label, the Project action that archives it, how it is found on disk, and how its name maps
to its file or folder's stem and back; and it is the one reader and writer of the registry,
admin/registry.csv. These tests read the kinds as data, in a folder of their own, and never
change the folder the test runs in.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sqlglot_composer import project_files
from sqlglot_composer.project_files import (
    BUILDING_BLOCK,
    KINDS,
    REFERENCE,
    TABLE_FOLDER,
    FileKind,
    Registry,
)

NOW = datetime.datetime(2026, 10, 21, 9, 30, 0)
LATER = datetime.datetime(2026, 10, 22, 8, 0, 5)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A folder with a Project's empty registry and its three folders, and nothing else."""
    for folder in ("admin", "references", "building_blocks", "tables"):
        (tmp_path / folder).mkdir()
    project_files.start_registry(tmp_path)
    return tmp_path


# --- The kinds, as data -----------------------------------------------------------------------


def test_each_kind_is_one_entry() -> None:
    assert KINDS == (TABLE_FOLDER, REFERENCE, BUILDING_BLOCK)
    assert [(kind.kind, kind.label, kind.remover) for kind in KINDS] == [
        ("table_folder", "Table folder", "remove_table"),
        ("reference", "Table reference", "remove_reference"),
        ("building_block", "Building block", "remove_block"),
    ]
    assert all(isinstance(kind, FileKind) for kind in KINDS)
    # Only a Table reference's change writes the Database modules again.
    assert [kind.writes_databases for kind in KINDS] == [False, True, False]


@pytest.mark.parametrize(("kind", "name", "stem", "shown"), [
    (TABLE_FOLDER, "mart.daily_job_runs", "mart__daily_job_runs",
     "tables/mart__daily_job_runs/"),
    (REFERENCE, "ops.jobs", "ops__jobs", "references/ops__jobs.py"),
    (BUILDING_BLOCK, "runs_per_job", "runs_per_job", "building_blocks/runs_per_job.py"),
])
def test_a_name_maps_to_its_stem_and_path_and_back(
        tmp_path: Path, kind: FileKind, name: str, stem: str, shown: str) -> None:
    assert kind.stem(name) == stem
    assert kind.name_of(stem) == name
    assert kind.shown(stem) == shown
    assert kind.path(tmp_path, stem) == tmp_path / shown.rstrip("/")


def test_a_table_name_holding_two_underscores_after_the_dot_maps_back_whole() -> None:
    assert REFERENCE.stem("ops.job__runs") == "ops__job__runs"
    assert REFERENCE.name_of("ops__job__runs") == "ops.job__runs"


@pytest.mark.parametrize(("name", "stem", "back"), [
    ("my__db.jobs", "my__db__jobs", "my.db__jobs"),
    ("ops_.jobs", "ops___jobs", "ops._jobs"),
    ("__main__.jobs", "__main____jobs", ".main____jobs"),
])
def test_a_database_name_holding_two_underscores_doesnt_map_back(
        name: str, stem: str, back: str) -> None:
    """Pins today's lossy mapping: a stem is read back at its first __, so a Database whose
    name holds __, or ends in _, comes back as another name. check() then suggests register
    with that name, which finds the same stem."""
    assert TABLE_FOLDER.stem(name) == stem
    assert TABLE_FOLDER.name_of(stem) == back
    assert TABLE_FOLDER.stem(back) == stem


def test_a_name_with_a_dot_is_a_tables_and_one_without_a_building_blocks() -> None:
    assert project_files.kinds_named_by("ops.jobs") == (TABLE_FOLDER, REFERENCE)
    assert project_files.kinds_named_by("runs_per_job") == (BUILDING_BLOCK,)


def test_a_table_notebook_is_named_as_its_table_folder() -> None:
    assert project_files.table_notebook("mart__daily_job_runs") == (
        "tables/mart__daily_job_runs/mart__daily_job_runs.ipynb")
    assert project_files.table_stem("mart.daily_job_runs") == "mart__daily_job_runs"


def test_each_kind_is_found_on_disk(root: Path) -> None:
    (root / "tables" / "mart__daily_job_runs").mkdir()
    (root / "tables" / "stray.txt").write_text("", encoding="utf-8")
    (root / "references" / "ops__jobs.py").write_text("# by hand", encoding="utf-8")
    (root / "references" / "__init__.py").write_text("", encoding="utf-8")
    (root / "references" / "ops.py").write_text(
        f'"""ops{project_files.DATABASE_TITLE}\n"""\n', encoding="utf-8")
    (root / "references" / "notes.txt").write_text("", encoding="utf-8")
    (root / "building_blocks" / "runs_per_job.py").write_text("", encoding="utf-8")
    (root / "building_blocks" / "__init__.py").write_text("", encoding="utf-8")
    assert TABLE_FOLDER.found(root) == ["mart__daily_job_runs"]
    assert REFERENCE.found(root) == ["ops__jobs"]
    assert BUILDING_BLOCK.found(root) == ["runs_per_job"]
    assert project_files.table_references(root) == [root / "references" / "ops__jobs.py"]
    assert project_files.is_database_module(root / "references" / "ops.py")
    assert not project_files.is_database_module(root / "references" / "ops__jobs.py")


def test_only_references_leave_a_database_module_out(root: Path) -> None:
    """A Database module is written only into references/: a file in building_blocks/ whose
    first line looks like one is still a Building block, as check() found it before."""
    (root / "building_blocks" / "ops.py").write_text(
        f'"""ops{project_files.DATABASE_TITLE}\n"""\n', encoding="utf-8")
    assert BUILDING_BLOCK.found(root) == ["ops"]


@pytest.mark.parametrize(("kind", "stem", "moved"), [
    (TABLE_FOLDER, "mart__daily_job_runs",
     "admin/removed/20261021-093000-mart__daily_job_runs/"),
    (REFERENCE, "ops__jobs", "admin/removed/20261021-093000-ops__jobs.py"),
    (BUILDING_BLOCK, "runs_per_job", "admin/removed/20261021-093000-runs_per_job.py"),
])
def test_each_kind_is_archived_named_by_the_time(
        root: Path, kind: FileKind, stem: str, moved: str) -> None:
    path = kind.path(root, stem)
    if kind.is_folder:
        (path / "lineage").mkdir(parents=True)
    else:
        path.write_text("# mine", encoding="utf-8")
    assert kind.archive(root, stem, NOW) == moved
    assert not path.exists()
    assert (root / moved.rstrip("/")).exists()


# --- The registry -----------------------------------------------------------------------------


def test_a_new_registry_has_only_its_header(root: Path) -> None:
    assert (root / "admin" / "registry.csv").read_text(encoding="utf-8") == (
        "kind,table,created_at,removed_at\n")
    assert Registry(root).rows == []


def test_the_registry_lists_marks_removed_and_gives_the_rows_in_force(root: Path) -> None:
    registry = Registry(root)
    registry.add([(TABLE_FOLDER, "mart.daily_job_runs"), (REFERENCE, "mart.daily_job_runs")],
                 NOW)
    registry.add([(BUILDING_BLOCK, "runs_per_job")], NOW)
    assert registry.listed(TABLE_FOLDER, "mart.daily_job_runs")
    assert not registry.listed(BUILDING_BLOCK, "mart.daily_job_runs")
    registry.mark_removed(TABLE_FOLDER, "mart.daily_job_runs", LATER)
    assert not registry.listed(TABLE_FOLDER, "mart.daily_job_runs")
    assert registry.in_force(REFERENCE) == ["mart.daily_job_runs"]
    assert registry.in_force(TABLE_FOLDER) == []
    # Each change is written as it is made, and read back the same.
    assert Registry(root).rows == registry.rows == [
        {"kind": "table_folder", "table": "mart.daily_job_runs",
         "created_at": "2026-10-21 09:30:00", "removed_at": "2026-10-22 08:00:05"},
        {"kind": "reference", "table": "mart.daily_job_runs",
         "created_at": "2026-10-21 09:30:00", "removed_at": ""},
        {"kind": "building_block", "table": "runs_per_job",
         "created_at": "2026-10-21 09:30:00", "removed_at": ""},
    ]
    assert (root / "admin" / "registry.csv").read_text(encoding="utf-8").splitlines()[1] == (
        "table_folder,mart.daily_job_runs,2026-10-21 09:30:00,2026-10-22 08:00:05")


def test_marking_removed_what_the_registry_doesnt_list_changes_nothing(root: Path) -> None:
    registry = Registry(root)
    registry.mark_removed(REFERENCE, "ops.jobs", NOW)
    assert Registry(root).rows == []


def test_a_name_listed_again_after_its_removal_is_in_force_once(root: Path) -> None:
    registry = Registry(root)
    registry.add([(REFERENCE, "ops.jobs")], NOW)
    registry.mark_removed(REFERENCE, "ops.jobs", NOW)
    registry.add([(REFERENCE, "ops.jobs")], LATER)
    assert registry.in_force(REFERENCE) == ["ops.jobs"]
    assert [row["removed_at"] for row in Registry(root).rows] == ["2026-10-21 09:30:00", ""]
