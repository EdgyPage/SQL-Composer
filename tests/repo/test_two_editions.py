"""sqlglot Composer's folder, and the Composer core it runs.

`composer_core/` holds the code every function a user calls runs; `sqlglot_composer/` holds its
own `__init__.py`, `writing.py`, `engine.py`, Example gallery and how-to page. These tests hold
each folder to the registry in `tools/editions.py`, the Edition files to the interface the core
calls, and a missing composer_core named. One TOOLBOX_VERSION across the folders is held in
test_toolbox_checks.py.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import editions

ROOT = Path(__file__).resolve().parents[2]
SQLGLOT = ROOT / editions.SQLGLOT_COMPOSER.folder
CORE = ROOT / editions.CORE


def _files(folder: Path) -> set[str]:
    return {path.name for path in folder.iterdir() if path.name != "__pycache__"}


def test_each_folder_holds_exactly_its_files() -> None:
    assert _files(CORE) == set(editions.CORE_FILES)
    assert _files(SQLGLOT) == set(editions.EDITION_FILES + editions.PAGES)


def _functions(path: Path) -> dict[str, list[str]]:
    """Each public function a file defines, with its parameters' names."""
    return {node.name: [arg.arg for arg in node.args.args + node.args.kwonlyargs]
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")}


@pytest.mark.parametrize("name", sorted(editions.EDITION_INTERFACE))
def test_each_edition_file_has_the_interface_the_core_calls(name: str) -> None:
    found = _functions(SQLGLOT / name)
    wanted = editions.EDITION_INTERFACE[name]
    assert {function: found.get(function) for function in wanted} == wanted


def test_the_core_reaches_the_edition_only_through_the_interface() -> None:
    """Each function edition.py hands on is one the Edition files offer, with their parameters."""
    offered = {name: parameters for functions in editions.EDITION_INTERFACE.values()
               for name, parameters in functions.items()}
    forwarded = {name: parameters for name, parameters in _functions(CORE / "edition.py").items()
                 if name not in ("plug", "toolbox_folders")}
    assert forwarded
    assert {name: offered.get(name) for name in forwarded} == forwarded


def _run(script: str, cwd: Path, **environment) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", script], cwd=cwd,
                          env={**os.environ, **environment}, capture_output=True, text=True,
                          timeout=120)


def test_an_edition_without_composer_core_beside_it_says_so(tmp_path: Path) -> None:
    pytest.importorskip("sqlglot")
    shutil.copytree(SQLGLOT, tmp_path / SQLGLOT.name, ignore=shutil.ignore_patterns("__pycache__"))
    result = _run("import sqlglot_composer", tmp_path)
    assert result.stderr.strip().endswith(
        "ImportError: sqlglot_composer stopped on import:"
        "\n  What happened:  The composer_core folder isn't beside the sqlglot_composer folder."
        "\n  Why it matters: composer_core holds the code every Toolbox function runs, so the "
        "Toolbox can't work without it."
        "\n  Usual fix:      Copy the composer_core folder from the same download beside the "
        "sqlglot_composer folder, so the two sit side by side."
        "\n  Opt-out:        none - this one can't be switched off.")
