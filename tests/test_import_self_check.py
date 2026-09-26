"""The Toolbox checks itself on import, and stops with a plain message when it can't be trusted.

Each case copies the folder somewhere else, breaks it the way a paste at work could, and
imports it in a fresh Python.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import sqlglot

import sql_composer

TOOLBOX = Path(__file__).resolve().parent.parent / "sql_composer"
FILES = sorted(p.name for p in TOOLBOX.iterdir() if p.name != "__pycache__")


def import_copy(tmp_path: Path, change) -> str:
    """Copy the Toolbox, apply `change` to the copy, import it, and return what it printed."""
    copy = tmp_path / "sql_composer"
    shutil.copytree(TOOLBOX, copy, ignore=shutil.ignore_patterns("__pycache__"))
    change(copy)
    result = subprocess.run([sys.executable, "-c", "import sql_composer"], cwd=tmp_path,
                            capture_output=True, text=True)
    return result.stderr


def with_file_list(copy: Path) -> None:
    init = copy / "__init__.py"
    text = init.read_text(encoding="utf-8").replace("_FILES = None", f"_FILES = {FILES!r}")
    init.write_text(text, encoding="utf-8")


def test_an_untouched_copy_imports(tmp_path) -> None:
    assert import_copy(tmp_path, with_file_list) == ""


def test_a_file_from_another_version_stops_the_import(tmp_path) -> None:
    def older(copy: Path) -> None:
        path = copy / "running.py"
        text = path.read_text(encoding="utf-8").replace('TOOLBOX_VERSION = "2.0"',
                                                        'TOOLBOX_VERSION = "1.9"')
        path.write_text(text, encoding="utf-8")

    assert "running.py is from 1.9 - paste it again from the 2.0 download" in import_copy(
        tmp_path, older)


def test_an_extra_file_stops_the_import(tmp_path) -> None:
    def extra(copy: Path) -> None:
        with_file_list(copy)
        (copy / "my_notes.py").write_text("x = 1\n", encoding="utf-8")

    assert "my_notes.py isn't part of SQL Composer 2.0" in import_copy(tmp_path, extra)


def test_a_missing_file_stops_the_import(tmp_path) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "CHANGES.md").unlink()

    assert "CHANGES.md is missing" in import_copy(tmp_path, missing)


def test_a_missing_example_gallery_stops_the_import(tmp_path) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "examples.html").unlink()

    assert "examples.html is missing" in import_copy(tmp_path, missing)


def test_files_from_two_exports_stop_the_import(tmp_path) -> None:
    def stamped(copy: Path) -> None:
        for path in copy.glob("*.py"):
            when = "2026-10-02 14:05" if path.name != "tables.py" else "2026-09-30 09:00"
            stamp = f"# SQL Composer 2.0, exported {when} - generated from dev, do not edit\n"
            path.write_text(stamp + path.read_text(encoding="utf-8"), encoding="utf-8")

    assert "tables.py came from a different export" in import_copy(tmp_path, stamped)


def test_an_exported_copy_says_when_it_was_exported(tmp_path) -> None:
    def stamped(copy: Path) -> None:
        for path in copy.glob("*.py"):
            stamp = "# SQL Composer 2.0, exported 2026-10-02 14:05 - generated from dev, do not edit\n"
            path.write_text(stamp + path.read_text(encoding="utf-8"), encoding="utf-8")
        (copy.parent / "show.py").write_text("import sql_composer\nprint(sql_composer.VERSION)\n",
                                             encoding="utf-8")

    copy_root = tmp_path
    import_copy(copy_root, stamped)
    shown = subprocess.run([sys.executable, "show.py"], cwd=copy_root, capture_output=True,
                           text=True)
    assert shown.stdout.strip() == "SQL Composer 2.0, exported 2026-10-02 14:05"


@pytest.mark.parametrize("version", ["25.24.1", "31.0.0", "unknown"])
def test_a_sqlglot_outside_the_range_stops_the_import(monkeypatch, version) -> None:
    monkeypatch.setattr(sqlglot, "__version__", version)
    with pytest.raises(ImportError, match=f"this Python has sqlglot {version}"):
        sql_composer._check_sqlglot()


def test_an_older_python_stops_the_import(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 9, 7, "final", 0))
    with pytest.raises(ImportError, match="needs Python 3.11 or newer, and this is Python 3.9.7"):
        sql_composer._check_python()


def test_a_sqlglot_that_behaves_differently_stops_the_import(monkeypatch) -> None:
    from sqlglot import exp

    real = exp.convert
    monkeypatch.setattr(exp, "convert",
                        lambda value, *args, **kw: exp.Literal.string("changed")
                        if value == "O'Brien\\" else real(value, *args, **kw))
    with pytest.raises(ImportError, match="behaves differently: Hive string escaping has "
                                          "changed. Nothing has been built or sent."):
        sql_composer._check_sqlglot()


def test_a_newer_sqlglot_in_range_prints_a_note(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "30.20.1")
    sql_composer._check_sqlglot()
    assert capsys.readouterr().out == (
        "Note: sqlglot 30.20.1 is newer than any version SQL Composer was tested on "
        "(30.19.0). Its behaviour checks passed.\n")
