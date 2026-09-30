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

import editions
import sql_composer
from conftest import edition, import_stop, toolbox_folder

TOOLBOX = toolbox_folder()
ROOT = TOOLBOX.parent
FOLDER, PRODUCT = edition().folder, edition().product
OTHER = next(other for other in editions.EDITIONS.values() if other is not edition())
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

    assert import_copy(tmp_path, older).endswith(import_stop(
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

    assert import_copy(tmp_path, extra).endswith(import_stop(
        what=f"my_notes.py is in the {FOLDER} folder, but not part of {PRODUCT} {VERSION}.",
        why="A file left over from an earlier Toolbox version can still be imported, and would "
        "quietly run old code. A script of your own inside the folder would be deleted with it "
        "at the next update.",
        fix=f"Move any of your own scripts out first: they sit beside the {FOLDER} folder, "
        f"never inside it. Then delete the {FOLDER} folder, and copy the whole folder in "
        f"again from the {VERSION} download.",
    ) + "\n")



def test_a_missing_file_stops_the_import(tmp_path) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "CHANGES.md").unlink()

    assert import_copy(tmp_path, missing).endswith(import_stop(
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
    assert import_copy(tmp_path, lambda copy: stamp_every_file(copy, odd=odd)).endswith(import_stop(
        what=f"{odd} came from a different export than __init__.py.",
        why="Two exports of the same Toolbox version can differ, so the code, the Example "
        "gallery and the change notes in this folder may not match each other.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def from_the_other_folder(copy: Path, *names: str) -> None:
    """Stamp every file, then make `names` read as the same export's files of the other folder."""
    stamp_every_file(copy)
    for name in names:
        path = copy / name
        # The stamp, on line 1, names the folder the file came from.
        path.write_text(path.read_text(encoding="utf-8").replace(PRODUCT, OTHER.product, 1),
                        encoding="utf-8")


FROM_ELSEWHERE_WHY = (
    "A folder's files are made to work only with each other: a .py file from another folder "
    "could make a Statement fail or come out wrong, and an examples.html or CHANGES.md from one "
    "may not describe this folder's code.")
FROM_ELSEWHERE_FIX = (f"Delete the {FOLDER} folder, then copy it in again from the {FOLDER} "
                      f"folder of one download, not from {OTHER.folder}.")


@pytest.mark.parametrize("odd", ["tables.py", "examples.html", "CHANGES.md"])
def test_a_file_from_the_other_folder_stops_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: from_the_other_folder(copy, odd)).endswith(
        import_stop(what=f"{odd} is from the {OTHER.folder} folder, and this is the {FOLDER} "
                    "folder.", why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


def test_every_file_from_the_other_folder_is_named(tmp_path) -> None:
    pasted = import_copy(tmp_path,
                         lambda copy: from_the_other_folder(copy, "tables.py", "running.py"))
    assert f"What happened:  running.py, tables.py are from the {OTHER.folder} folder" in pasted


def test_the_other_folders_init_stops_the_import_naming_itself(tmp_path) -> None:
    """Its own text names the other folder, so the stop goes by the folder the import found."""
    def pasted_in(copy: Path) -> None:
        shutil.copy(ROOT / OTHER.folder / "__init__.py", copy / "__init__.py")

    assert import_copy(tmp_path, pasted_in).endswith(import_stop(
        what=f"__init__.py is from the {OTHER.folder} folder, and this is the {FOLDER} folder.",
        why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


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


def test_an_older_python_stops_the_import(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 9, 7, "final", 0))
    with pytest.raises(ImportError) as error:
        sql_composer._check_python()
    assert f"ImportError: {error.value}" == import_stop(
        what=f"{PRODUCT} needs Python 3.11 or newer, and this is Python 3.9.7.",
        why=f"{PRODUCT} is tested only on Python 3.11 and newer, and parts of it may not work "
        "on an older one.",
        fix="Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab), or ask "
        "whoever looks after your environment to add one.",
    )
