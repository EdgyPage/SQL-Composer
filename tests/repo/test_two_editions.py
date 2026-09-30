"""The two Editions' folders: Spark Composer's shared files are SQL Composer's, swapped.

`spark_composer/` holds a generated copy of every shared file and of `CHANGES.md`, and its own
`writing.py` and `engine.py`. These tests hold the copies current, both folders to the Edition
registry, CHANGES.md the same in both, the Edition files' interface the same in both, and
`spark_composer` importable with neither Java nor sqlglot. One TOOLBOX_VERSION across both
folders is held in test_toolbox_checks.py.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import editions
import make_spark_edition

ROOT = Path(__file__).resolve().parents[2]
SQL, SPARK = ROOT / editions.SQL_COMPOSER.folder, ROOT / editions.SPARK_COMPOSER.folder


def test_every_generated_file_is_current() -> None:
    stale = sorted(name for name, text in make_spark_edition.generated().items()
                   if (SPARK / name).read_text(encoding="utf-8") != text)
    assert stale == [], (f"{', '.join(stale)} in {SPARK.name}/ is stale: run "
                         f"{make_spark_edition.COMMAND}")


def _files(folder: Path) -> set[str]:
    return {path.name for path in folder.iterdir() if path.name != "__pycache__"}


def test_each_folder_holds_exactly_its_files() -> None:
    written = set(editions.SHARED_FILES + editions.EDITION_FILES + editions.VERBATIM_FILES)
    assert _files(SQL) == written | set(editions.PAGES)
    assert _files(SPARK) == written | set(editions.PAGES)


def test_changes_is_the_same_in_both_folders() -> None:
    assert (SPARK / "CHANGES.md").read_bytes() == (SQL / "CHANGES.md").read_bytes()


def _functions(path: Path) -> dict[str, list[str]]:
    """Each public function a file defines, with its parameters' names."""
    return {node.name: [arg.arg for arg in node.args.args + node.args.kwonlyargs]
            for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")}


@pytest.mark.parametrize("name", editions.EDITION_FILES)
@pytest.mark.parametrize("folder", [SQL, SPARK], ids=lambda folder: folder.name)
def test_each_edition_file_has_the_interface_both_share(folder: Path, name: str) -> None:
    found = _functions(folder / name)
    wanted = editions.EDITION_INTERFACE[name]
    assert {function: found.get(function) for function in wanted} == wanted


def test_spark_composer_imports_with_neither_java_nor_sqlglot(tmp_path: Path) -> None:
    script = ("import sys\n"
              "sys.modules['sqlglot'] = None\n"
              "import spark_composer\n"
              "assert 'sql_composer' not in sys.modules\n"
              "print(len(spark_composer.__all__), spark_composer.VERSION)")
    environment = {**os.environ, "JAVA_HOME": str(tmp_path / "no-java")}
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=environment,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("63 Spark Composer ")
