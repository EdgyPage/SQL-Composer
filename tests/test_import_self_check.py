"""The Toolbox checks itself on import, and stops with a plain message when it can't be trusted.

At work the Toolbox is one folder, `sqlglot_composer`. Each case copies it somewhere else,
breaks it the way a paste at work could, and imports it in a fresh Python.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import sqlglot_composer
import toolbox_registry
from sqlglot_composer import checks
from conftest import FOLDER, PRODUCT, import_stop, toolbox_folder

TOOLBOX = toolbox_folder()
VERSION = sqlglot_composer.TOOLBOX_VERSION
# Another Toolbox folder, whose files a paste at work could mix in, such as a copy of an
# Edition dropped before this version.
OTHER = SimpleNamespace(folder="other_composer", product="Other Composer")


def other_folders_init() -> str:
    """The other folder's __init__.py, as it names itself."""
    text = (TOOLBOX / "__init__.py").read_text(encoding="utf-8")
    return text.replace(FOLDER, OTHER.folder).replace(PRODUCT, OTHER.product)


def _files(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir() if p.name != "__pycache__")


def import_copy(tmp_path: Path, change=None, name: str = FOLDER) -> str:
    """Copy the folder as `name`, apply `change` to the copy, import it, and return what it
    printed."""
    copy = tmp_path / name
    shutil.copytree(TOOLBOX, copy, ignore=shutil.ignore_patterns("__pycache__"))
    if change:
        change(copy)
    result = subprocess.run([sys.executable, "-c", f"import {name}"], cwd=tmp_path,
                            capture_output=True, text=True)
    return result.stderr


def with_file_list(copy: Path) -> None:
    init = copy / "__init__.py"
    text = init.read_text(encoding="utf-8").replace("_FILES = None", f"_FILES = {_files(copy)!r}")
    init.write_text(text, encoding="utf-8")


def test_an_untouched_copy_imports(tmp_path) -> None:
    assert import_copy(tmp_path, with_file_list) == ""


@pytest.mark.parametrize("name", ["writing.py", "running.py"])
def test_a_file_from_another_version_stops_the_import(tmp_path, name: str) -> None:
    def older(copy: Path) -> None:
        path = copy / name
        text = path.read_text(encoding="utf-8").replace(f'TOOLBOX_VERSION = "{VERSION}"',
                                                        'TOOLBOX_VERSION = "1.9"')
        path.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, older).endswith(import_stop(
        what=f"{name} is from Toolbox version 1.9, and {FOLDER}/__init__.py is from "
        f"{VERSION}.",
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


def test_a_missing_refusals_file_still_says_what_is_missing(tmp_path) -> None:
    """The four-part message is built in the folder's __init__.py, so it works without
    refusals.py."""
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / "refusals.py").unlink()

    assert import_copy(tmp_path, missing).endswith(import_stop(
        what=f"refusals.py is missing from the {FOLDER} folder.",
        why=f"Every file of {PRODUCT} {VERSION} is needed: a missing .py file would make a part "
        "of it fail later, far from the cause.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
        f"{VERSION} download.",
    ) + "\n")


@pytest.mark.parametrize(("pages", "lost"), [
    (["examples.html"], "and a missing examples.html leaves you without the Example gallery"),
    (["how_to.html"], "and a missing how_to.html leaves you without the how-tos"),
    (["examples.html", "how_to.html"], "a missing examples.html leaves you without the Example "
     "gallery, and a missing how_to.html leaves you without the how-tos"),
])
def test_a_missing_page_stops_the_import_and_says_what_it_holds(tmp_path, pages: list[str],
                                                                lost: str) -> None:
    assert sorted(pages) == [page for page in toolbox_registry.PAGES if page in pages]

    def missing(copy: Path) -> None:
        with_file_list(copy)
        for page in pages:
            (copy / page).unlink()

    assert import_copy(tmp_path, missing).endswith(import_stop(
        what=f"{', '.join(pages)} {'is' if len(pages) == 1 else 'are'} missing from the "
        f"{FOLDER} folder.",
        why=f"Every file of {PRODUCT} {VERSION} is needed: a missing .py file would make a part "
        f"of it fail later, far from the cause, {lost}.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
        f"{VERSION} download.",
    ) + "\n")


def test_every_page_is_one_the_missing_file_stop_says_what_it_holds() -> None:
    assert set(toolbox_registry.PAGES) == set(checks._PAGES)


def test_a_folder_missing_what_checks_it_stops_the_import(tmp_path) -> None:
    assert import_copy(tmp_path, lambda copy: (copy / "checks.py").unlink()).endswith(
        import_stop(
            what=f"checks.py is missing from the {FOLDER} folder.",
            why="The folder checks itself when it is imported, and can't without that file.",
            fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
            "download.",
        ) + "\n")


def stamp_every_file(copy: Path, odd: str | None = None, product: str = PRODUCT,
                     when: str = "2026-10-02 14:05") -> None:
    """Stamp line 1 of every file as the export does, at `when`, and `odd` as from another
    export."""
    for path in copy.iterdir():
        if path.name == "__pycache__":
            continue
        at = "2026-09-30 09:00" if path.name == odd else when
        stamp = f"{product} {VERSION}, exported {at} - generated from dev, do not edit"
        line = f"# {stamp}" if path.suffix == ".py" else f"<!-- {stamp} -->"
        path.write_text(line + "\n" + path.read_text(encoding="utf-8"), encoding="utf-8")


def test_an_exported_copy_imports(tmp_path) -> None:
    def exported(copy: Path) -> None:
        with_file_list(copy)
        stamp_every_file(copy)

    assert import_copy(tmp_path, exported) == ""


@pytest.mark.parametrize("odd", ["writing.py", "tables.py", "examples.html"])
def test_files_from_two_exports_stop_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: stamp_every_file(copy, odd=odd)).endswith(
        import_stop(
            what=f"{odd} came from a different export than {FOLDER}/__init__.py.",
            why="Two exports of the same Toolbox version can differ, so the files in this "
            "folder may not match each other.",
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
    "could make a Statement fail or come out wrong, and an examples.html or how_to.html from one "
    "may not describe this folder's code.")
FROM_ELSEWHERE_FIX = (f"Delete the {FOLDER} folder, then copy it in again from the {FOLDER} "
                      f"folder of one download, not from {OTHER.folder}.")


@pytest.mark.parametrize("odd", ["writing.py", "engine.py", "tables.py", "examples.html"])
def test_a_file_from_the_other_folder_stops_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: from_the_other_folder(copy, odd)).endswith(
        import_stop(what=f"{odd} is from the {OTHER.folder} folder, and this is the {FOLDER} "
                    "folder.", why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


def test_every_file_from_the_other_folder_is_named(tmp_path) -> None:
    pasted = import_copy(tmp_path,
                         lambda copy: from_the_other_folder(copy, "writing.py", "engine.py"))
    assert f"What happened:  engine.py, writing.py are from the {OTHER.folder} folder" in pasted


def test_the_other_folders_init_stops_the_import_naming_itself(tmp_path) -> None:
    """Its own text names the other folder, so the stop goes by the folder the import found."""
    def pasted_in(copy: Path) -> None:
        (copy / "__init__.py").write_text(other_folders_init(), encoding="utf-8")
        from_the_other_folder(copy, "__init__.py")

    assert import_copy(tmp_path, pasted_in).endswith(import_stop(
        what=f"__init__.py is from the {OTHER.folder} folder, and this is the {FOLDER} folder.",
        why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


def renamed_copy(tmp_path: Path, change) -> str:
    """Copy the folder as my_toolbox, as its export would, apply `change`, and import it."""
    def exported_then_changed(copy: Path) -> None:
        with_file_list(copy)
        stamp_every_file(copy)
        change(copy)

    return import_copy(tmp_path, exported_then_changed, name="my_toolbox")


def test_a_renamed_folder_imports(tmp_path) -> None:
    assert renamed_copy(tmp_path, lambda copy: None) == ""


def test_a_file_from_the_other_folder_in_a_renamed_folder_stops_the_import(tmp_path) -> None:
    def pasted_in(copy: Path) -> None:
        writing = copy / "writing.py"
        writing.write_text(writing.read_text(encoding="utf-8").replace(PRODUCT, OTHER.product, 1),
                           encoding="utf-8")

    assert renamed_copy(tmp_path, pasted_in).endswith(renamed_stop("writing.py"))


def test_the_other_folders_init_in_a_renamed_folder_stops_the_import_naming_itself(
        tmp_path) -> None:
    """The folder is what most of its files' stamps say, whatever the pasted __init__.py says."""
    def pasted_in(copy: Path) -> None:
        (copy / "__init__.py").write_text(other_folders_init(), encoding="utf-8")
        with_file_list(copy)
        stamp_line = f"# {OTHER.product} {VERSION}, exported 2026-10-02 14:05 - generated from dev"
        init = copy / "__init__.py"
        init.write_text(f"{stamp_line}, do not edit\n" + init.read_text(encoding="utf-8"),
                        encoding="utf-8")

    assert renamed_copy(tmp_path, pasted_in).endswith(renamed_stop("__init__.py"))


def renamed_stop(odd: str) -> str:
    """The stop for `odd`, from the other folder, in the folder my_toolbox, a copy of this one."""
    return ("ImportError: my_toolbox stopped on import:"
            f"\n  What happened:  {odd} is from the {OTHER.folder} folder, and this is the "
            f"my_toolbox folder, a copy of {FOLDER}."
            f"\n  Why it matters: {FROM_ELSEWHERE_WHY}"
            f"\n  Usual fix:      Delete the my_toolbox folder, then copy it in again from the "
            f"{FOLDER} folder of one download, not from {OTHER.folder}."
            "\n  Opt-out:        none - this one can't be switched off.\n")


def test_a_file_unstamped_among_exported_ones_stops_the_import(tmp_path) -> None:
    """An examples.html regenerated on dev, pasted into an exported folder, is caught too."""
    def exported_but_one(copy: Path) -> None:
        dev_page = (copy / "examples.html").read_text(encoding="utf-8")
        stamp_every_file(copy)
        (copy / "examples.html").write_text(dev_page, encoding="utf-8")

    assert "examples.html came from a different export" in import_copy(tmp_path,
                                                                          exported_but_one)


def test_an_exported_copy_says_when_it_was_exported(tmp_path) -> None:
    def stamped(copy: Path) -> None:
        stamp_every_file(copy)
        (copy.parent / "show.py").write_text(f"import {FOLDER}\nprint({FOLDER}.VERSION)\n",
                                             encoding="utf-8")

    import_copy(tmp_path, stamped)
    shown = subprocess.run([sys.executable, "show.py"], cwd=tmp_path, capture_output=True,
                           text=True)
    assert shown.stdout.strip() == f"{PRODUCT} {VERSION}, exported 2026-10-02 14:05"


def test_an_older_python_stops_the_import(monkeypatch) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 9, 7, "final", 0))
    with pytest.raises(ImportError) as error:
        checks.check_python(PRODUCT, FOLDER)
    assert f"ImportError: {error.value}" == import_stop(
        what=f"{PRODUCT} needs Python 3.11 or newer, and this is Python 3.9.7.",
        why=f"{PRODUCT} is tested only on Python 3.11 and newer, and parts of it may not work "
        "on an older one.",
        fix="Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab), or ask "
        "whoever looks after your environment to add one.",
    )


def test_a_stop_in_a_renamed_folder_is_headed_by_its_own_name(tmp_path) -> None:
    def extra(copy: Path) -> None:
        (copy / "my_notes.py").write_text("x = 1\n", encoding="utf-8")

    stopped = renamed_copy(tmp_path, extra)
    assert "ImportError: my_toolbox stopped on import:" in stopped
    assert "my_notes.py is in the my_toolbox folder" in stopped
