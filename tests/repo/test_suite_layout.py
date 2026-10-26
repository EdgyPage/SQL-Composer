"""How the test suite is laid out: shared tests, sqlglot Composer's own, and the repo's own.

The tests directly in `tests/` test the Toolbox through its public names, so they don't import
sqlglot themselves. `tests/sqlglot_checks/` holds what tests sqlglot itself, and `tests/repo/`
the checks on the repo. pytest imports every file under `tests/` by its name alone, so no two
may share one.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[1]
SHARED = sorted(TESTS.glob("*.py"))


def test_every_file_under_tests_has_a_name_of_its_own() -> None:
    # tests/upgrade_from/ holds Example projects as an earlier version left them, data for the
    # Upgrade's test that pytest never imports.
    names = [path.name for path in TESTS.rglob("*.py")
             if "upgrade_from" not in path.relative_to(TESTS).parts]
    assert sorted({name for name in names if names.count(name) > 1}) == []


@pytest.mark.parametrize("path", SHARED, ids=lambda path: path.name)
def test_a_shared_test_imports_no_library_of_its_own(path: Path) -> None:
    imported = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported & {"sqlglot"} == set()
