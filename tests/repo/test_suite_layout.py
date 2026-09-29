"""How the test suite is laid out: shared tests, one folder per Edition, and the repo's own.

The tests directly in `tests/` run against every Edition, so they import neither Edition's
library. `tests/sqlglot_edition/` holds what only SQL Composer can pass, and
`tests/spark_edition/` what only Spark Composer can. `tests/repo/` holds the checks on the repo
itself, which run once, in SQL Composer's run. pytest imports every test file by its name alone,
so no two may share one.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[1]
SHARED = sorted(path for path in TESTS.glob("*.py") if path.name != "conftest.py")


def test_every_test_file_has_a_name_of_its_own() -> None:
    names = [path.name for path in TESTS.rglob("test_*.py")]
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
