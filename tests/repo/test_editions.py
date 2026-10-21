"""The Toolbox's folders, as `tools/editions.py` defines them for every tool and test on `dev`.

The registry is the one place that says which files the Composer core and sqlglot Composer's
folder hold, and what each file may import.
"""

from __future__ import annotations

from pathlib import Path

import editions
from editions import SQLGLOT_COMPOSER, may_import

ROOT = Path(__file__).resolve().parents[2]


def test_the_one_edition_has_its_folder_product_and_library() -> None:
    assert list(editions.EDITIONS) == ["sqlglot_composer"]
    assert (SQLGLOT_COMPOSER.product, SQLGLOT_COMPOSER.library) == ("sqlglot Composer", "sqlglot")
    assert editions.EXPORTED == (SQLGLOT_COMPOSER,)


def test_every_file_in_each_toolbox_folder_is_classified() -> None:
    def present(folder: str) -> set[str]:
        return {path.name for path in (ROOT / folder).iterdir() if path.name != "__pycache__"}

    assert present(editions.CORE) - set(editions.CORE_FILES) == set()
    assert present(SQLGLOT_COMPOSER.folder) - set(editions.EDITION_FILES + editions.PAGES) == set()


def test_what_each_file_may_import() -> None:
    assert may_import(SQLGLOT_COMPOSER, "writing.py") == {"pandas", "numpy", "sqlglot",
                                                          "composer_core"}
    assert may_import(SQLGLOT_COMPOSER, "engine.py") == {"pandas", "numpy", "sqlglot",
                                                         "composer_core"}
    assert may_import(SQLGLOT_COMPOSER, "__init__.py") == {"pandas", "numpy", "composer_core"}


def test_no_core_file_may_import_the_library_or_the_edition() -> None:
    for name in editions.CORE_FILES:
        assert may_import(None, name) == {"pandas", "numpy"}


def test_an_import_a_file_may_not_make_is_listed(tmp_path: Path) -> None:
    folder = tmp_path / "sqlglot_composer"
    folder.mkdir()
    (folder / "__init__.py").write_text("import re\nimport sqlglot\nfrom composer_core import trees\n")
    (folder / "engine.py").write_text("import numpy\nimport sqlglot.exp\nimport pyspark\n")
    assert editions.imports_outside(folder) == ["__init__.py imports sqlglot",
                                                "engine.py imports pyspark"]
    core = tmp_path / "composer_core"
    core.mkdir()
    (core / "tables.py").write_text("import pandas\nimport sqlglot_composer\nfrom . import trees\n")
    assert editions.imports_outside(core) == ["tables.py imports sqlglot_composer"]


def test_no_core_file_names_the_library() -> None:
    found = {path.name: editions.libraries_named(path.read_text("utf-8"))
             for path in (ROOT / editions.CORE).glob("*.py")}
    assert {name: words for name, words in found.items() if words} == {}


def test_the_core_may_name_sqlglot_composer_but_not_sqlglot() -> None:
    assert editions.libraries_named("Write it with sqlglot_composer, as sqlglot Composer does.") == []
    assert editions.libraries_named("import sqlglot") == ["sqlglot"]
