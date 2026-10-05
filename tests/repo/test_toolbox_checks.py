"""The checks `dev` holds the Toolbox to, as decided in "What does `dev` enforce?".

- each Toolbox file imports only the standard library, itself and what `tools/editions.py`
  allows it: pandas and numpy, and its Edition's library in the files that need it;
- every Toolbox file declares the same TOOLBOX_VERSION, and CHANGES.md has a section for it;
- the public names are exactly the list below, so a name is added or removed only here;
- ruff passes, with its complexity limit (C901, at most 10) on every function;
- each Edition's library pin in requirements-dev.txt (sqlglot for sqlglot Composer, pyspark for
  Spark Composer) falls inside the range its engine.py supports, and CI runs each Edition at the
  bottom of that range and at the pin; Spark Composer's jobs run on Java 17, without sqlglot,
  with its Example database required.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import editions
import sqlglot_composer
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
    "to_hive", "show_hive", "run", "by_day", "set_load_limits",
    "GuardRefused", "LoadRefused",
    "export_lineage",
    "example_database",
]


# Every Toolbox folder: the Composer core, and each Edition's.
FOLDERS = [editions.CORE, *editions.EDITIONS]


def toolbox_files() -> list[Path]:
    """Every .py file of the Toolbox's folders: they share one TOOLBOX_VERSION."""
    return [path for folder in FOLDERS if (ROOT / folder).is_dir()
            for path in sorted((ROOT / folder).glob("*.py"))]


def test_the_public_names_are_the_decided_ones() -> None:
    assert len(PUBLIC_NAMES) == 64
    assert len(set(PUBLIC_NAMES)) == 64
    assert sorted(sqlglot_composer.__all__) == sorted(PUBLIC_NAMES)
    for name in sqlglot_composer.__all__:
        assert hasattr(sqlglot_composer, name), name


def test_spark_composer_has_the_same_public_names() -> None:
    # In a Python of its own, since a Python runs one Edition and this one runs sqlglot Composer.
    script = ("import json, spark_composer\n"
              "print(json.dumps([spark_composer.__all__,\n"
              "                  [n for n in spark_composer.__all__ if not hasattr(spark_composer, n)]]))")
    done = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True,
                          text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    names, missing = json.loads(done.stdout)
    assert sorted(names) == sorted(PUBLIC_NAMES)
    assert missing == []


@pytest.mark.parametrize("folder", [f for f in FOLDERS if (ROOT / f).is_dir()])
def test_each_toolbox_file_imports_only_what_editions_allows(folder: str) -> None:
    assert editions.imports_outside(ROOT / folder) == []


@pytest.mark.parametrize("path", toolbox_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_file_of_both_editions_declares_the_same_toolbox_version(path: Path) -> None:
    found = re.findall(r'^TOOLBOX_VERSION = "([^"]+)"$', path.read_text(encoding="utf-8"),
                       re.MULTILINE)
    assert found == [sqlglot_composer.TOOLBOX_VERSION]


def test_changes_has_a_section_for_the_version() -> None:
    changes = (ROOT / editions.CORE / "CHANGES.md").read_text(encoding="utf-8")
    assert f"\n## {sqlglot_composer.TOOLBOX_VERSION}\n" in changes


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


def _engine(edition: editions.Edition):
    """An Edition's engine.py, which holds the range of its library it supports.

    It is loaded by its path, not imported with its Edition, since a Python runs one Edition.
    """
    path = ROOT / edition.folder / "engine.py"
    spec = importlib.util.spec_from_file_location(f"{edition.folder}_engine", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pin(edition: editions.Edition) -> tuple[int, ...]:
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    return _version(re.search(rf"^{edition.library}==([\d.]+)$", requirements,
                              re.MULTILINE).group(1))


EACH_EDITION = pytest.mark.parametrize("edition", list(editions.EDITIONS.values()),
                                       ids=lambda edition: edition.library)
WORKFLOW = ROOT / ".github" / "workflows" / "dev.yml"


def _job(edition: editions.Edition) -> str:
    """The Edition's own job in dev.yml, named for its folder, as sqlglot-composer: its lines."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    found = re.search(rf"^  {edition.folder.replace('_', '-')}:\n(.*?)(?=^  \S|\Z)", workflow,
                      re.MULTILINE | re.DOTALL)
    assert found, f"dev.yml has no job for {edition.product}"
    return found.group(1)


def _steps(job: str) -> list[str]:
    """What a job runs, each run: line as written, so nothing can be added to one unseen."""
    return re.findall(r"^\s+(?:- )?run: (.*)$", job, re.MULTILINE)


@EACH_EDITION
def test_each_library_pin_is_inside_the_range_its_edition_supports(edition) -> None:
    engine, pin = _engine(edition), _pin(edition)
    assert engine._LOWEST <= pin < engine._BELOW
    assert pin == engine._NEWEST_TESTED


@EACH_EDITION
def test_ci_runs_each_edition_at_the_bottom_of_its_range_and_at_its_pin(edition) -> None:
    job = _job(edition)
    matrix = re.search(rf"^\s+{edition.library}: \[(.*)\]$", job, re.MULTILINE).group(1)
    versions = {_version(v.strip().strip('"')) for v in matrix.split(",")}
    assert versions == {_engine(edition)._LOWEST, _pin(edition)}
    assert 'python-version: "3.11"' in job
    assert f'pip install "{edition.library}==${{{{ matrix.{edition.library} }}}}"' in _steps(job)
    assert "continue-on-error" not in job


def test_sqlglot_composers_ci_runs_its_tests() -> None:
    assert _steps(_job(editions.SQLGLOT_COMPOSER))[-1] == "python -m pytest"


def test_spark_composers_ci_runs_on_java_17_without_sqlglot_and_needs_its_example_database(
) -> None:
    job = _job(editions.SPARK_COMPOSER)
    assert "distribution: temurin" in job and 'java-version: "17"' in job
    steps = _steps(job)
    assert "pip uninstall --yes sqlglot" in steps
    # It exits 1 while sqlglot can be found, on its own.
    assert ("""python -c "import importlib.util, sys; """
            """sys.exit(importlib.util.find_spec('sqlglot') is not None)\"""" in steps)
    assert steps[-1] == "python -m pytest --edition spark --example-database required"
