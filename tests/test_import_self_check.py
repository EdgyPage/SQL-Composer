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
from conftest import edition, toolbox_folder

TOOLBOX = toolbox_folder()
FOLDER, PRODUCT = edition().folder, edition().product
VERSION = sql_composer.TOOLBOX_VERSION
FILES = sorted(p.name for p in TOOLBOX.iterdir() if p.name != "__pycache__")


def import_copy(tmp_path: Path, change) -> str:
    """Copy the Toolbox, apply `change` to the copy, import it, and return what it printed."""
    copy = tmp_path / FOLDER
    shutil.copytree(TOOLBOX, copy, ignore=shutil.ignore_patterns("__pycache__"))
    change(copy)
    result = subprocess.run([sys.executable, "-c", f"import {FOLDER}"], cwd=tmp_path,
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
        text = path.read_text(encoding="utf-8").replace(f'TOOLBOX_VERSION = "{VERSION}"',
                                                        'TOOLBOX_VERSION = "1.9"')
        path.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, older).endswith(stopped(
        what=f"running.py is from Toolbox version 1.9, and __init__.py is from {VERSION}.",
        why="Files from different Toolbox versions weren't written to work together, so a "
        "Statement could fail or come out wrong.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def test_an_extra_file_stops_the_import(tmp_path) -> None:
    def extra(copy: Path) -> None:
        with_file_list(copy)
        (copy / "my_notes.py").write_text("x = 1\n", encoding="utf-8")

    assert import_copy(tmp_path, extra).endswith(stopped(
        what=f"my_notes.py is in the {FOLDER} folder, but not part of {PRODUCT} {VERSION}.",
        why="A file left over from an earlier Toolbox version can still be imported, and would "
        "quietly run old code. A script of your own inside the folder would be deleted with it "
        "at the next update.",
        fix=f"Move any of your own scripts out first: they sit beside the {FOLDER} folder, "
        f"never inside it. Then delete the {FOLDER} folder, and copy the whole folder in "
        f"again from the {VERSION} download.",
    ) + "\n")


def stopped(what: str, why: str, fix: str) -> str:
    """The last line of an import stop: the four parts, with no opt-out."""
    return (
        f"ImportError: {FOLDER} stopped on import:"
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        "\n  Opt-out:        none - this one can't be switched off."
    )


def test_a_missing_file_stops_the_import(tmp_path) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "CHANGES.md").unlink()

    assert import_copy(tmp_path, missing).endswith(stopped(
        what=f"CHANGES.md is missing from the {FOLDER} folder.",
        why=f"Every file of {PRODUCT} {VERSION} is needed: a missing .py file would make a part "
        "of it fail later, far from the cause, and a missing examples.html or CHANGES.md "
        "leaves you without the Example gallery or the change notes.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the {VERSION} "
        "download.",
    ) + "\n")


def test_a_missing_refusals_file_still_says_what_is_missing(tmp_path) -> None:
    """The four-part message is built in __init__.py, so it works without refusals.py."""
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "refusals.py").unlink()

    assert f"What happened:  refusals.py is missing from the {FOLDER} folder." in (
        import_copy(tmp_path, missing))


def test_a_missing_example_gallery_stops_the_import(tmp_path) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "examples.html").unlink()

    assert "examples.html is missing" in import_copy(tmp_path, missing)


def stamp_every_file(copy: Path, odd: str | None = None) -> None:
    """Stamp line 1 of every file as the export does, and `odd` as from another export."""
    for path in copy.iterdir():
        when = "2026-09-30 09:00" if path.name == odd else "2026-10-02 14:05"
        stamp = f"{PRODUCT} {VERSION}, exported {when} - generated from dev, do not edit"
        line = f"# {stamp}" if path.suffix == ".py" else f"<!-- {stamp} -->"
        path.write_text(line + "\n" + path.read_text(encoding="utf-8"), encoding="utf-8")


def test_an_exported_copy_imports(tmp_path) -> None:
    def exported(copy: Path) -> None:
        with_file_list(copy)
        stamp_every_file(copy)

    assert import_copy(tmp_path, exported) == ""


@pytest.mark.parametrize("odd", ["tables.py", "examples.html", "CHANGES.md"])
def test_files_from_two_exports_stop_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: stamp_every_file(copy, odd=odd)).endswith(stopped(
        what=f"{odd} came from a different export than __init__.py.",
        why="Two exports of the same Toolbox version can differ, so the code, the Example "
        "gallery and the change notes in this folder may not match each other.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def test_a_file_unstamped_among_exported_ones_stops_the_import(tmp_path) -> None:
    """An examples.html regenerated on dev, pasted into an exported folder, is caught too."""
    def exported_but_one(copy: Path) -> None:
        dev_page = (copy / "examples.html").read_text(encoding="utf-8")
        stamp_every_file(copy)
        (copy / "examples.html").write_text(dev_page, encoding="utf-8")

    assert "examples.html came from a different export" in import_copy(tmp_path,
                                                                      exported_but_one)


def test_a_markdown_heading_is_not_read_as_a_stamp(tmp_path) -> None:
    """In Markdown the export writes an HTML comment, so a `# ...` line 1 there is a heading."""
    def heading(copy: Path) -> None:
        changes = copy / "CHANGES.md"
        text = changes.read_text(encoding="utf-8").replace("# Changes", f"# {PRODUCT} changes", 1)
        changes.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, heading) == ""


def test_an_exported_copy_says_when_it_was_exported(tmp_path) -> None:
    def stamped(copy: Path) -> None:
        stamp_every_file(copy)
        (copy.parent / "show.py").write_text(f"import {FOLDER}\nprint({FOLDER}.VERSION)\n",
                                             encoding="utf-8")

    copy_root = tmp_path
    import_copy(copy_root, stamped)
    shown = subprocess.run([sys.executable, "show.py"], cwd=copy_root, capture_output=True,
                           text=True)
    assert shown.stdout.strip() == f"{PRODUCT} {VERSION}, exported 2026-10-02 14:05"


def test_a_python_without_sqlglot_stops_the_import(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "sqlglot", None)  # makes `import sqlglot` fail
    with pytest.raises(ImportError) as error:
        sql_composer._check_sqlglot()
    assert f"ImportError: {error.value}" == stopped(
        what="SQL Composer needs sqlglot, and this Python can't import it.",
        why="SQL Composer writes every Statement as Hive through sqlglot, and reads the Hive "
        "back to check it, so it can't build anything without it.",
        fix='Install sqlglot from a notebook cell with %pip install "sqlglot>=25.24.2,<31.0.0", '
        "then restart the kernel. If you can't install packages, ask whoever looks after your "
        "environment.",
    )


@pytest.mark.parametrize("version", ["25.24.1", "31.0.0", "unknown"])
def test_a_sqlglot_outside_the_range_stops_the_import(monkeypatch, version) -> None:
    monkeypatch.setattr(sqlglot, "__version__", version)
    with pytest.raises(ImportError) as error:
        sql_composer._check_sqlglot()
    assert f"ImportError: {error.value}" == stopped(
        what="SQL Composer needs sqlglot 25.24.2 or newer, below 31.0.0, and this Python has "
        f"sqlglot {version}.",
        why="SQL Composer is checked only on that range of sqlglot. Another sqlglot can write "
        "Hive differently, so a Statement could come out wrong without anything saying so.",
        fix="Install a sqlglot in that range from a notebook cell with %pip install "
        '"sqlglot>=25.24.2,<31.0.0", then restart the kernel. '
        "If you can't install packages, "
        "ask whoever looks after your environment.",
    )


def test_an_older_python_stops_the_import(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 9, 7, "final", 0))
    with pytest.raises(ImportError) as error:
        sql_composer._check_python()
    assert f"ImportError: {error.value}" == stopped(
        what=f"{PRODUCT} needs Python 3.11 or newer, and this is Python 3.9.7.",
        why=f"{PRODUCT} is tested only on Python 3.11 and newer, and parts of it may not work "
        "on an older one.",
        fix="Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab), or ask "
        "whoever looks after your environment to add one.",
    )


def test_a_sqlglot_that_behaves_differently_stops_the_import(monkeypatch) -> None:
    from sqlglot import exp

    real = exp.convert
    monkeypatch.setattr(exp, "convert",
                        lambda value, *args, **kw: exp.Literal.string("changed")
                        if value == "O'Brien\\" else real(value, *args, **kw))
    with pytest.raises(ImportError) as error:
        sql_composer._check_sqlglot()
    assert f"ImportError: {error.value}" == stopped(
        what=f"sqlglot {sqlglot.__version__} is in the supported range, but behaves "
        "differently: Hive string escaping has changed. Nothing has been built or sent.",
        why="SQL Composer relies on this behaviour to write Hive safely, so a Statement could "
        "come out wrong.",
        fix="Install again the sqlglot SQL Composer is tested on, from a notebook cell with "
        '%pip install --force-reinstall "sqlglot==30.19.0", then restart the kernel. '
        "If you can't install packages, "
        "ask whoever looks after your environment.",
    )


def test_a_newer_sqlglot_in_range_prints_a_note(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "30.20.1")
    sql_composer._check_sqlglot()
    assert capsys.readouterr().out == (
        "Note: sqlglot 30.20.1 is newer than any version SQL Composer was tested on "
        "(30.19.0). Its behaviour checks passed.\n")
