"""The checks `dev` holds the Toolbox to, as decided in "What does `dev` enforce?".

- each Toolbox file imports only the standard library, itself and what `tools/toolbox_registry.py`
  allows it: pandas and numpy, and sqlglot in the files that need it;
- the Toolbox's version is written in one place, its version.txt, and CHANGES.md, at the repo's
  top, has a section for it;
- the public names are exactly the list below, so a name is added or removed only here, and
  so are the admin module's and the project module's, which the star import leaves out;
- ruff passes, with its complexity limit (C901, at most 10) on every function;
- requirements.txt, what a user installs, names exactly the libraries the Toolbox may import,
  pinned to the version requirements-dev.txt pins;
- sqlglot's pin in requirements-dev.txt falls inside the range engine.py supports, and CI runs
  the tests at the pin.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

import toolbox_registry
import sqlglot_composer
from conftest import toolbox_folder

ROOT = Path(__file__).resolve().parents[2]
TOOLBOX = toolbox_folder()

# Every public name, as decided in the tracker. Add or remove a name only with the ticket
# that decided it.
PUBLIC_NAMES = [
    "TOOLBOX_VERSION", "VERSION",
    "Table", "write_table_reference", "first_look", "check_key", "check_table_reference",
    "create_table", "all_columns",
    "SELECT", "SELECT_DISTINCT", "AS", "FROM", "JOIN", "LEFT_JOIN", "CROSS_JOIN", "WHERE",
    "GROUP_BY", "HAVING", "ORDER_BY", "LIMIT", "INSERT_OVERWRITE", "INSERT_INTO", "statement",
    "derived",
    "equals", "not_equals", "is_null", "is_not_null", "at_least", "at_most", "more_than",
    "less_than", "between", "last_n_days", "is_in", "is_not_in", "contains", "starts_with",
    "any_of", "all_of",
    "count_rows", "count_distinct", "sum_of", "average_of", "min_of", "max_of", "if_else",
    "fill_null", "week_start", "month_start", "row_number", "descending", "hive_function",
    "to_hive", "show_hive", "set_load_limits",
    "GuardRefused", "LoadRefused",
    "export_lineage",
    # Toolbox 5.0, ticket 03: Session settings, the Unchecked statement and the Admin log.
    "hive_settings", "unchecked_hive", "set_admin_log",
    # Toolbox 5.0, ticket 05: Joins.
    "SEMI_JOIN", "ANTI_JOIN", "FULL_JOIN", "RIGHT_JOIN",
    # Toolbox 5.0, ticket 06: windows.
    "window", "rank", "dense_rank", "ntile", "lag", "lead", "first_value", "last_value",
    # Toolbox 5.0, ticket 07: Stacks and subtotals.
    "UNION_ALL", "UNION", "INTERSECT", "EXCEPT", "rollup", "cube", "grouping_sets", "is_total",
    # Toolbox 5.0, ticket 08: upkeep and speed.
    "repair_partitions", "compute_statistics", "explain",
    "example_database",
    # Toolbox 6.1, ticket 01: the types a hint names.
    "Statement", "Column", "Condition", "SessionSettings", "UncheckedStatement",
    # Toolbox 6.1, ticket 03: the types the public signatures name.
    "Clause", "Window",
    # Toolbox 6.1, ticket 08: the rest of the types the public signatures name.
    "Named", "Ordering", "Subtotals", "Verdict",
    # Toolbox 7.0, ticket 08: Python steps, declared for Lineage.
    "python_step", "PythonStep",
    # Toolbox 7.1 (7.0's map, ticket 09): you pick the call, so run_query and run_execute replace run.
    "run_query", "run_execute",
    # Toolbox 7.2, ticket 03: Unchecked expressions and the Unchecked derived table.
    "unchecked_column", "unchecked_condition", "unchecked_derived",
    # Toolbox 7.2, ticket 04: an if/else chain, or a lookup on one column, as one CASE.
    "first_match", "mapped",
    # Toolbox 7.2, ticket 08: checking a Conversion against the Hive it was converted from.
    "compare_hive", "compare_with_original",
]
# The admin module's names, `from sqlglot_composer import admin`, as decided in Toolbox 5.0's
# ticket 04: drop_table moved here from the names above. Toolbox 7.0, ticket 03: tables have no
# days, so drop_partitions replaced drop_days and by_day left the names above. Toolbox 7.0,
# ticket 09, 7.1: check_the_copy compares a move's copy through query, then gives its last steps.
ADMIN_NAMES = ["drop_table", "drop_partitions", "add_columns", "set_properties",
               "move_to_own_folder", "check_the_copy"]
# The project module's names, `from sqlglot_composer import project`, as decided in Toolbox
# 6.0's ticket 06. Toolbox 7.0, ticket 06: new_block and remove_block, for Building blocks.
PROJECT_NAMES = ["start", "new_table", "remove_table", "new_block", "remove_block",
                 "add_references", "remove_reference", "register", "check",
                 "refresh_reference_sheet", "load", "run_tables",
                 # Toolbox 7.2, ticket 02: upgrade carries a Project to a newer Toolbox.
                 "upgrade",
                 # Toolbox 7.2, ticket 07: a Conversion, from scan to Saved table.
                 "scan_hive", "convert", "finish_conversion", "remove_conversion"]


FOLDER = ROOT / toolbox_registry.FOLDER


def toolbox_files() -> list[Path]:
    """Every .py file of the Toolbox's folder."""
    return sorted(FOLDER.glob("*.py"))


def test_the_folder_holds_exactly_its_files() -> None:
    present = {path.name for path in FOLDER.iterdir() if path.name != "__pycache__"}
    assert present == set(toolbox_registry.FILES)


def test_the_public_names_are_the_decided_ones() -> None:
    assert len(PUBLIC_NAMES) == 109
    assert len(set(PUBLIC_NAMES)) == 109
    assert sorted(sqlglot_composer.__all__) == sorted(PUBLIC_NAMES)
    for name in sqlglot_composer.__all__:
        assert hasattr(sqlglot_composer, name), name


def test_the_admin_modules_names_are_the_decided_ones() -> None:
    assert sqlglot_composer.admin.__all__ == ADMIN_NAMES
    for name in ADMIN_NAMES:
        assert callable(getattr(sqlglot_composer.admin, name)), name


def test_the_project_modules_names_are_the_decided_ones() -> None:
    assert sqlglot_composer.project.__all__ == PROJECT_NAMES
    for name in PROJECT_NAMES:
        assert callable(getattr(sqlglot_composer.project, name)), name


def test_each_toolbox_file_imports_only_what_toolbox_folder_allows() -> None:
    assert toolbox_registry.imports_outside(FOLDER) == []


@pytest.mark.parametrize("path", toolbox_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_no_toolbox_file_but_version_txt_names_the_version(path: Path) -> None:
    """The version is written in one place, version.txt (ADR 0013)."""
    assert not re.search(r'^TOOLBOX_VERSION = "', path.read_text(encoding="utf-8"), re.MULTILINE)


def test_version_txt_holds_the_toolbox_and_its_version_alone() -> None:
    text = (FOLDER / toolbox_registry.VERSION_FILE).read_text(encoding="utf-8")
    assert text == f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}\n"


def test_changes_has_a_section_for_the_version() -> None:
    changes = (ROOT / "CHANGES.md").read_text(encoding="utf-8")
    assert f"\n## {sqlglot_composer.TOOLBOX_VERSION}\n" in changes


def test_ruff_passes_with_its_complexity_limit() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", toolbox_registry.FOLDER, "tests", "tools",
         "worked_examples"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    settings = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'extend-select = ["C901"]' in settings
    assert "max-complexity = 10" in settings


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(n) for n in text.split("."))


def _engine() -> ModuleType:
    """engine.py, which holds the range of sqlglot the Toolbox supports."""
    return sqlglot_composer.engine


def _pin() -> tuple[int, ...]:
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    return _version(re.search(rf"^{toolbox_registry.LIBRARY}==([\d.]+)$", requirements,
                              re.MULTILINE).group(1))


WORKFLOW = ROOT / ".github" / "workflows" / "dev.yml"


def _job() -> str:
    """The Toolbox's job in dev.yml, named for its folder, as sqlglot-composer: its lines."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    name = toolbox_registry.FOLDER.replace("_", "-")
    found = re.search(rf"^  {name}:\n(.*?)(?=^  \S|\Z)", workflow, re.MULTILINE | re.DOTALL)
    assert found, f"dev.yml has no job for {toolbox_registry.PRODUCT}"
    return found.group(1)


def _steps(job: str) -> list[str]:
    """What a job runs, each run: line as written, so nothing can be added to one unseen."""
    return re.findall(r"^\s+(?:- )?run: (.*)$", job, re.MULTILINE)


def test_the_sqlglot_pin_is_inside_the_range_the_toolbox_supports() -> None:
    engine, pin = _engine(), _pin()
    assert engine._LOWEST <= pin < engine._BELOW
    assert pin == engine._NEWEST_TESTED


def _requirements() -> dict[str, str]:
    """requirements.txt, what a user installs: each package with its exact pin, such as
    {"sqlglot": "30.23.0"}. A line that isn't an exact pin is refused here."""
    found = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            pinned = re.fullmatch(r"([A-Za-z0-9_.-]+)==([\w.]+)", line)
            assert pinned, f"requirements.txt gives {line!r}, not an exact pin such as name==1.2.3"
            found[pinned.group(1)] = pinned.group(2)
    return found


def _dev_pins() -> dict[str, str]:
    """requirements-dev.txt's exact pins, the versions dev and CI test on."""
    text = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    return dict(re.findall(r"^([A-Za-z0-9_.-]+)==([\w.]+)$", text, re.MULTILINE))


def _the_libraries() -> set[str]:
    """What tools/toolbox_registry.py lets the Toolbox import: pandas, numpy and sqlglot."""
    return set(toolbox_registry.SHARED_IMPORTS) | {toolbox_registry.LIBRARY}


def _normal(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _needs(package: str) -> set[str] | None:
    """The packages an installed `package` needs in turn, its extras left out, or None where
    this Python hasn't installed it."""
    import importlib.metadata
    try:
        requires = importlib.metadata.distribution(package).requires or []
    except importlib.metadata.PackageNotFoundError:
        return None
    return {_normal(re.match(r"[A-Za-z0-9_.-]+", line).group())
            for line in requires if "extra ==" not in line}


def test_requirements_names_every_library_the_toolbox_may_import() -> None:
    # A new library the Toolbox imports must be allowed in tools/toolbox_registry.py, and so here.
    assert _the_libraries() <= set(_requirements())


# Pinned though nothing needs it: pandas 3 dropped pytz, which the user keeps (2026-10-20).
KEPT_UNNEEDED = {"pytz"}


def test_requirements_lists_what_each_listed_package_needs_in_turn() -> None:
    # So pip installs nothing requirements.txt doesn't pin, and it lists nothing nobody needs,
    # apart from KEPT_UNNEEDED.
    listed = {_normal(name) for name in _requirements()}
    needed = set()
    for name in listed:
        needs = _needs(name)
        if needs is not None:
            assert needs <= listed, f"{name} needs {sorted(needs - listed)}, not in requirements.txt"
            needed |= needs
    if all(_needs(name) is not None for name in listed):
        assert listed == {_normal(name) for name in _the_libraries()} | needed | KEPT_UNNEEDED


def test_requirements_pins_the_versions_dev_tests_on() -> None:
    # So a user installs exactly what the tests and CI's pinned job passed on.
    dev = _dev_pins()
    assert _requirements() == {name: dev[name] for name in _requirements()}


def test_ci_runs_at_sqlglots_pin() -> None:
    job, library = _job(), toolbox_registry.LIBRARY
    matrix = re.search(rf"^\s+{library}: \[(.*)\]$", job, re.MULTILINE).group(1)
    versions = {_version(v.strip().strip('"')) for v in matrix.split(",")}
    assert versions == {_pin()}
    assert 'python-version: "3.12"' in job
    assert f'pip install "{library}==${{{{ matrix.{library} }}}}"' in _steps(job)
    assert "continue-on-error" not in job


def test_ci_runs_the_tests() -> None:
    assert _steps(_job())[-1] == "python -m pytest"
