"""How the test suite is laid out: shared tests, one folder per Edition, and the repo's own.

The tests directly in `tests/` run against every Edition, so they import neither Edition's
library. `tests/sqlglot_edition/` holds what only SQL Composer can pass, and
`tests/spark_edition/` what only Spark Composer can. `tests/repo/` holds the checks on the repo
itself, which run once, in SQL Composer's run. pytest imports every file under `tests/` by its
name alone, so no two may share one.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

import conftest

TESTS = Path(__file__).resolve().parents[1]
SHARED = sorted(TESTS.glob("*.py"))


def test_every_file_under_tests_has_a_name_of_its_own() -> None:
    names = [path.name for path in TESTS.rglob("*.py")]
    assert sorted({name for name in names if names.count(name) > 1}) == []


@pytest.mark.parametrize("path", SHARED, ids=lambda path: path.name)
def test_a_shared_test_imports_neither_editions_library(path: Path) -> None:
    imported = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported & {"sqlglot", "pyspark"} == set()


def given(edition: str) -> SimpleNamespace:
    """A stand-in for pytest's config, given `--edition`."""
    return SimpleNamespace(getoption=lambda name: {"--edition": edition}[name])


def test_each_run_leaves_out_the_other_editions_folder_and_spark_leaves_out_the_repos() -> None:
    assert conftest.folders_left_out(given("sqlglot")) == {"spark_edition"}
    assert conftest.folders_left_out(given("spark")) == {"sqlglot_edition", "repo"}


def test_a_run_given_a_folder_its_edition_leaves_out_stops() -> None:
    stray = SimpleNamespace(path=TESTS / "spark_edition" / "test_spark_anything.py")
    with pytest.raises(pytest.UsageError, match="tests/spark_edition/ doesn't run with "
                       "--edition sqlglot"):
        conftest.pytest_collection_modifyitems(given("sqlglot"), [stray])
    own = SimpleNamespace(path=TESTS / "sqlglot_edition" / "test_sqlglot_anything.py")
    conftest.pytest_collection_modifyitems(given("sqlglot"), [own])
