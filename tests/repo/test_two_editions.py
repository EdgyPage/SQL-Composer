"""The two Editions' folders, and the Composer core both run.

`composer_core/` holds every file both Editions share, once. Each Edition's folder holds its
own `__init__.py`, `writing.py`, `engine.py` and Example gallery. These tests hold each folder
to the Edition registry, the two `__init__.py` files the same apart from their names, the
Edition files' interface the same in both, one Edition per Python, a missing composer_core
named, and `spark_composer` importable with neither Java nor sqlglot. One TOOLBOX_VERSION
across the folders is held in test_toolbox_checks.py.
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
SQL, SPARK = ROOT / editions.SQL_COMPOSER.folder, ROOT / editions.SPARK_COMPOSER.folder
CORE = ROOT / editions.CORE


def _files(folder: Path) -> set[str]:
    return {path.name for path in folder.iterdir() if path.name != "__pycache__"}


def test_each_folder_holds_exactly_its_files() -> None:
    assert _files(CORE) == set(editions.CORE_FILES)
    assert _files(SQL) == set(editions.EDITION_FILES + editions.PAGES)
    assert _files(SPARK) == set(editions.EDITION_FILES + editions.PAGES)


def test_the_two_editions_init_files_differ_only_by_their_names() -> None:
    sql_init = (SQL / "__init__.py").read_text(encoding="utf-8")
    spark_init = (SPARK / "__init__.py").read_text(encoding="utf-8")
    assert spark_init == editions.named_for(editions.SPARK_COMPOSER, sql_init)


def _functions(path: Path) -> dict[str, list[str]]:
    """Each public function a file defines, with its parameters' names."""
    return {node.name: [arg.arg for arg in node.args.args + node.args.kwonlyargs]
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")}


@pytest.mark.parametrize("name", sorted(editions.EDITION_INTERFACE))
@pytest.mark.parametrize("folder", [SQL, SPARK], ids=lambda folder: folder.name)
def test_each_edition_file_has_the_interface_both_share(folder: Path, name: str) -> None:
    found = _functions(folder / name)
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


def test_spark_composer_imports_with_neither_java_nor_sqlglot(tmp_path: Path) -> None:
    script = ("import sys\n"
              "sys.modules['sqlglot'] = None\n"
              "import spark_composer\n"
              "assert 'sql_composer' not in sys.modules\n"
              "print(len(spark_composer.__all__), spark_composer.VERSION)")
    result = _run(script, ROOT, JAVA_HOME=str(tmp_path / "no-java"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("63 Spark Composer ")


def test_importing_both_editions_in_one_python_stops() -> None:
    pytest.importorskip("sqlglot")
    result = _run("import spark_composer\nimport sql_composer", ROOT)
    assert "sql_composer stopped on import:" in result.stderr
    assert "sql_composer was imported after spark_composer, in the same Python" in result.stderr


def test_an_edition_without_composer_core_beside_it_says_so(tmp_path: Path) -> None:
    pytest.importorskip("sqlglot")
    shutil.copytree(SQL, tmp_path / SQL.name, ignore=shutil.ignore_patterns("__pycache__"))
    result = _run("import sql_composer", tmp_path)
    assert result.stderr.strip().endswith(
        "ImportError: sql_composer stopped on import:"
        "\n  What happened:  The composer_core folder isn't beside the sql_composer folder."
        "\n  Why it matters: composer_core holds the code both Editions share, so the Toolbox "
        "can't work without it."
        "\n  Usual fix:      Copy the composer_core folder from the same download beside the "
        "sql_composer folder, so the two sit side by side."
        "\n  Opt-out:        none - this one can't be switched off.")
