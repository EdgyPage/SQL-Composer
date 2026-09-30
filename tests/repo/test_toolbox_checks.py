"""The checks `dev` holds the Toolbox to, as decided in "What does `dev` enforce?".

- each Toolbox file imports only the standard library, itself and what `tools/editions.py`
  allows it: pandas and numpy, and its Edition's library in the files that need it;
- every Toolbox file declares the same TOOLBOX_VERSION, and CHANGES.md has a section for it;
- the public names are exactly the list below, so a name is added or removed only here;
- ruff passes, with its complexity limit (C901, at most 10) on every function;
- the sqlglot pin in requirements-dev.txt falls inside the supported range, and CI runs both
  the bottom of that range and the pin.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

import editions
import sql_composer
from conftest import toolbox_folder

ROOT = Path(__file__).resolve().parents[2]
TOOLBOX = toolbox_folder()

# Every public name, as decided in the tracker. Add or remove a name only with the ticket
# that decided it.
PUBLIC_NAMES = [
    "TOOLBOX_VERSION", "VERSION",
    "Table", "write_table_reference", "first_look", "check_key", "check_table_reference",
    "create_table", "drop_table", "all_columns",
    "SELECT", "SELECT_DISTINCT", "AS", "FROM", "JOIN", "LEFT_JOIN", "CROSS_JOIN", "WHERE",
    "GROUP_BY", "HAVING", "ORDER_BY", "LIMIT", "INSERT_OVERWRITE", "INSERT_INTO", "statement",
    "derived",
    "equals", "not_equals", "is_null", "is_not_null", "at_least", "at_most", "more_than",
    "less_than", "between", "last_n_days", "is_in", "is_not_in", "contains", "starts_with",
    "any_of", "all_of",
    "count_rows", "count_distinct", "sum_of", "average_of", "min_of", "max_of", "if_else",
    "fill_null", "week_start", "month_start", "row_number", "descending", "hive_function",
    "to_hive", "run", "by_day", "set_load_limits",
    "GuardRefused", "LoadRefused",
    "export_lineage",
    "example_database",
]


def toolbox_files() -> list[Path]:
    """Every .py file of both Editions: they share one TOOLBOX_VERSION."""
    return [path for folder in editions.EDITIONS if (ROOT / folder).is_dir()
            for path in sorted((ROOT / folder).glob("*.py"))]


def test_the_public_names_are_the_decided_ones() -> None:
    assert len(PUBLIC_NAMES) == 63
    assert len(set(PUBLIC_NAMES)) == 63
    assert sorted(sql_composer.__all__) == sorted(PUBLIC_NAMES)
    for name in sql_composer.__all__:
        assert hasattr(sql_composer, name), name


def test_spark_composer_has_the_same_public_names() -> None:
    import spark_composer

    assert sorted(spark_composer.__all__) == sorted(PUBLIC_NAMES)
    for name in spark_composer.__all__:
        assert hasattr(spark_composer, name), name


@pytest.mark.parametrize("folder", [f for f in editions.EDITIONS if (ROOT / f).is_dir()])
def test_each_toolbox_file_imports_only_what_editions_allows(folder: str) -> None:
    assert editions.imports_outside(ROOT / folder) == []


@pytest.mark.parametrize("path", toolbox_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_file_of_both_editions_declares_the_same_toolbox_version(path: Path) -> None:
    found = re.findall(r'^TOOLBOX_VERSION = "([^"]+)"$', path.read_text(encoding="utf-8"),
                       re.MULTILINE)
    assert found == [sql_composer.TOOLBOX_VERSION]


def test_changes_has_a_section_for_the_version() -> None:
    changes = (TOOLBOX / "CHANGES.md").read_text(encoding="utf-8")
    assert f"\n## {sql_composer.TOOLBOX_VERSION}\n" in changes


def test_ruff_passes_with_its_complexity_limit() -> None:
    edition_folders = [folder for folder in editions.EDITIONS if (ROOT / folder).is_dir()]
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *edition_folders, "tests", "tools",
         "worked_examples"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    settings = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'extend-select = ["C901"]' in settings
    assert "max-complexity = 10" in settings


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(n) for n in text.split("."))


def test_the_sqlglot_pin_is_inside_the_supported_range() -> None:
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    pin = _version(re.search(r"^sqlglot==([\d.]+)$", requirements, re.MULTILINE).group(1))
    assert sql_composer.engine._LOWEST <= pin < sql_composer.engine._BELOW
    assert pin == sql_composer.engine._NEWEST_TESTED


def test_ci_runs_the_bottom_of_the_range_and_the_pin() -> None:
    workflow = (ROOT / ".github" / "workflows" / "dev.yml").read_text(encoding="utf-8")
    matrix = re.search(r"sqlglot: \[(.*)\]", workflow).group(1)
    versions = {_version(v.strip().strip('"')) for v in matrix.split(",")}
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    pin = _version(re.search(r"^sqlglot==([\d.]+)$", requirements, re.MULTILINE).group(1))
    assert versions == {sql_composer.engine._LOWEST, pin}
    assert 'python-version: "3.11"' in workflow
