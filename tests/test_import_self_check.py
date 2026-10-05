"""The Toolbox checks itself on import, and stops with a plain message when it can't be trusted.

At work the Toolbox is two folders side by side: composer_core and the Edition's. Each case
copies both somewhere else, breaks one the way a paste at work could, and imports the Edition
in a fresh Python.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import editions
import sqlglot_composer
from composer_core import checks
from conftest import edition, import_stop, toolbox_folder

TOOLBOX = toolbox_folder()
ROOT = TOOLBOX.parent
CORE = ROOT / editions.CORE
FOLDER, PRODUCT = edition().folder, edition().product
CORE_FOLDER, CORE_PRODUCT = editions.CORE, editions.CORE_PRODUCT
OTHER = next(other for other in editions.EDITIONS.values() if other is not edition())
VERSION = sqlglot_composer.TOOLBOX_VERSION


def _files(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir() if p.name != "__pycache__")


def import_copy(tmp_path: Path, change=None, change_core=None) -> str:
    """Copy both folders, apply `change` to the Edition's copy and `change_core` to the core's,
    import the Edition, and return what it printed."""
    copy, core = tmp_path / FOLDER, tmp_path / CORE_FOLDER
    for source, target in ((TOOLBOX, copy), (CORE, core)):
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
    if change:
        change(copy)
    if change_core:
        change_core(core)
    result = subprocess.run([sys.executable, "-c", f"import {FOLDER}"], cwd=tmp_path,
                            capture_output=True, text=True)
    return result.stderr


def with_file_list(copy: Path) -> None:
    init = copy / "__init__.py"
    text = init.read_text(encoding="utf-8").replace("_FILES = None", f"_FILES = {_files(copy)!r}")
    init.write_text(text, encoding="utf-8")


def test_an_untouched_copy_imports(tmp_path) -> None:
    assert import_copy(tmp_path, with_file_list, with_file_list) == ""


def test_a_core_file_from_another_version_stops_the_import(tmp_path) -> None:
    def older(core: Path) -> None:
        path = core / "running.py"
        text = path.read_text(encoding="utf-8").replace(f'TOOLBOX_VERSION = "{VERSION}"',
                                                        'TOOLBOX_VERSION = "1.9"')
        path.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, change_core=older).endswith(import_stop(
        what=f"running.py is from Toolbox version 1.9, and {CORE_FOLDER}/__init__.py is from "
        f"{VERSION}.",
        why="Files from different Toolbox versions weren't written to work together, so a "
        "Statement could fail or come out wrong.",
        fix=f"Delete the {CORE_FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def test_an_edition_file_from_another_version_stops_the_import(tmp_path) -> None:
    def older(copy: Path) -> None:
        path = copy / "writing.py"
        text = path.read_text(encoding="utf-8").replace(f'TOOLBOX_VERSION = "{VERSION}"',
                                                        'TOOLBOX_VERSION = "1.9"')
        path.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, older).endswith(import_stop(
        what=f"writing.py is from Toolbox version 1.9, and {FOLDER}/__init__.py is from "
        f"{VERSION}.",
        why="Files from different Toolbox versions weren't written to work together, so a "
        "Statement could fail or come out wrong.",
        fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def test_the_two_folders_from_different_versions_stop_the_import(tmp_path) -> None:
    def older(core: Path) -> None:
        for path in core.glob("*.py"):
            path.write_text(path.read_text(encoding="utf-8").replace(
                f'TOOLBOX_VERSION = "{VERSION}"', 'TOOLBOX_VERSION = "1.9"'), encoding="utf-8")

    assert import_copy(tmp_path, change_core=older).endswith(import_stop(
        what=f"{FOLDER} is from Toolbox version {VERSION}, and composer_core is from 1.9.",
        why="The two folders are written to work only with each other's copy from the same "
        "download, so a Statement could fail or come out wrong.",
        fix=f"Delete the {FOLDER} and composer_core folders, then copy both in again from one "
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


def test_an_extra_file_in_the_core_stops_the_import(tmp_path) -> None:
    def extra(core: Path) -> None:
        with_file_list(core)
        (core / "tables_old.py").write_text("x = 1\n", encoding="utf-8")

    stopped = import_copy(tmp_path, change_core=extra)
    assert f"ImportError: {FOLDER} stopped on import:" in stopped
    assert (f"What happened:  tables_old.py is in the {CORE_FOLDER} folder, but not part of "
            f"{CORE_FOLDER} {VERSION}.") in stopped


def test_a_missing_file_stops_the_import(tmp_path) -> None:
    def missing(core: Path) -> None:
        with_file_list(core)
        (core / "CHANGES.md").unlink()

    assert import_copy(tmp_path, change_core=missing).endswith(import_stop(
        what=f"CHANGES.md is missing from the {CORE_FOLDER} folder.",
        why=f"Every file of {CORE_FOLDER} {VERSION} is needed: a missing .py file would make "
        "a part of it fail later, far from the cause, and a missing CHANGES.md leaves you "
        "without the change notes.",
        fix=f"Delete the {CORE_FOLDER} folder, then copy the whole folder in again from the "
        f"{VERSION} download.",
    ) + "\n")


def test_a_missing_refusals_file_still_says_what_is_missing(tmp_path) -> None:
    """The four-part message is built in composer_core's __init__.py, so it works without
    refusals.py."""
    def missing(core: Path) -> None:
        with_file_list(core)
        (core / "refusals.py").unlink()

    assert f"What happened:  refusals.py is missing from the {CORE_FOLDER} folder." in (
        import_copy(tmp_path, change_core=missing))


@pytest.mark.parametrize("page", editions.PAGES)
def test_a_missing_page_stops_the_import(tmp_path, page: str) -> None:
    def missing(copy: Path) -> None:
        with_file_list(copy)
        (copy / page).unlink()

    assert f"{page} is missing" in import_copy(tmp_path, missing)


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


def stamp_core(core: Path, odd: str | None = None) -> None:
    stamp_every_file(core, odd, product=CORE_PRODUCT)


def test_an_exported_copy_imports(tmp_path) -> None:
    def exported(copy: Path) -> None:
        with_file_list(copy)
        stamp_every_file(copy)

    def exported_core(core: Path) -> None:
        with_file_list(core)
        stamp_core(core)

    assert import_copy(tmp_path, exported, exported_core) == ""


TWO_EXPORTS_WHY = ("Two exports of the same Toolbox version can differ, so the files in this "
                   "folder may not match each other.")


@pytest.mark.parametrize("odd", ["writing.py", "examples.html"])
def test_edition_files_from_two_exports_stop_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: stamp_every_file(copy, odd=odd),
                       stamp_core).endswith(import_stop(
        what=f"{odd} came from a different export than {FOLDER}/__init__.py.",
        why=TWO_EXPORTS_WHY, fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


@pytest.mark.parametrize("odd", ["tables.py", "CHANGES.md"])
def test_core_files_from_two_exports_stop_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, stamp_every_file,
                       lambda core: stamp_core(core, odd=odd)).endswith(import_stop(
        what=f"{odd} came from a different export than {CORE_FOLDER}/__init__.py.",
        why=TWO_EXPORTS_WHY,
        fix=f"Delete the {CORE_FOLDER} folder, then copy the whole folder in again from one "
        "download.",
    ) + "\n")


def test_the_two_folders_from_different_exports_stop_the_import(tmp_path) -> None:
    def other_export(core: Path) -> None:
        stamp_every_file(core, product=CORE_PRODUCT, when="2026-09-30 09:00")

    assert import_copy(tmp_path, stamp_every_file, other_export).endswith(import_stop(
        what=f"{FOLDER} was exported 2026-10-02 14:05, and composer_core 2026-09-30 09:00.",
        why="The two folders are written to work only with each other's copy from the same "
        "download, so a Statement could fail or come out wrong.",
        fix=f"Delete the {FOLDER} and composer_core folders, then copy both in again from one "
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


@pytest.mark.parametrize("odd", ["writing.py", "engine.py", "examples.html"])
def test_a_file_from_the_other_folder_stops_the_import(tmp_path, odd: str) -> None:
    assert import_copy(tmp_path, lambda copy: from_the_other_folder(copy, odd),
                       stamp_core).endswith(
        import_stop(what=f"{odd} is from the {OTHER.folder} folder, and this is the {FOLDER} "
                    "folder.", why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


def test_every_file_from_the_other_folder_is_named(tmp_path) -> None:
    pasted = import_copy(tmp_path,
                         lambda copy: from_the_other_folder(copy, "writing.py", "engine.py"),
                         stamp_core)
    assert f"What happened:  engine.py, writing.py are from the {OTHER.folder} folder" in pasted


def test_an_edition_file_pasted_into_the_core_stops_the_import(tmp_path) -> None:
    def pasted_in(core: Path) -> None:
        stamp_core(core)
        tables = core / "tables.py"
        tables.write_text(tables.read_text(encoding="utf-8").replace(CORE_PRODUCT, PRODUCT, 1),
                          encoding="utf-8")

    assert (f"What happened:  tables.py is from the {FOLDER} folder, and this is the "
            f"{CORE_FOLDER} folder.") in import_copy(tmp_path, stamp_every_file, pasted_in)


def test_the_other_folders_init_stops_the_import_naming_itself(tmp_path) -> None:
    """Its own text names the other folder, so the stop goes by the folder the import found."""
    def pasted_in(copy: Path) -> None:
        shutil.copy(ROOT / OTHER.folder / "__init__.py", copy / "__init__.py")
        from_the_other_folder(copy, "__init__.py")

    assert import_copy(tmp_path, pasted_in, stamp_core).endswith(import_stop(
        what=f"__init__.py is from the {OTHER.folder} folder, and this is the {FOLDER} folder.",
        why=FROM_ELSEWHERE_WHY, fix=FROM_ELSEWHERE_FIX) + "\n")


def renamed_copy(tmp_path: Path, change) -> str:
    """Copy the Edition as the folder my_toolbox, beside composer_core, as their export would,
    apply `change`, and import it."""
    copy, core = tmp_path / "my_toolbox", tmp_path / CORE_FOLDER
    shutil.copytree(TOOLBOX, copy, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(CORE, core, ignore=shutil.ignore_patterns("__pycache__"))
    with_file_list(copy)
    stamp_every_file(copy)
    stamp_core(core)
    change(copy)
    return subprocess.run([sys.executable, "-c", "import my_toolbox"], cwd=tmp_path,
                          capture_output=True, text=True).stderr


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
        shutil.copy(ROOT / OTHER.folder / "__init__.py", copy / "__init__.py")
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

    assert "examples.html came from a different export" in import_copy(
        tmp_path, exported_but_one, stamp_core)


def test_a_markdown_heading_is_not_read_as_a_stamp(tmp_path) -> None:
    """In Markdown the export writes an HTML comment, so a `# ...` line 1 there is a heading."""
    def heading(core: Path) -> None:
        changes = core / "CHANGES.md"
        text = changes.read_text(encoding="utf-8").replace("# Changes", f"# {PRODUCT} changes", 1)
        changes.write_text(text, encoding="utf-8")

    assert import_copy(tmp_path, change_core=heading) == ""


def test_an_exported_copy_says_when_it_was_exported(tmp_path) -> None:
    def stamped(copy: Path) -> None:
        stamp_every_file(copy)
        (copy.parent / "show.py").write_text(f"import {FOLDER}\nprint({FOLDER}.VERSION)\n",
                                             encoding="utf-8")

    import_copy(tmp_path, stamped, stamp_core)
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


@pytest.mark.parametrize("name", ["checks.py", "__init__.py"])
def test_a_core_folder_missing_what_checks_it_stops_the_import(tmp_path, name: str) -> None:
    assert import_copy(tmp_path, change_core=lambda core: (core / name).unlink()).endswith(
        import_stop(
            what=f"{name} is missing from the composer_core folder.",
            why="composer_core checks the Toolbox's folders when it is imported, and can't "
            "without its own files.",
            fix="Delete the composer_core folder, then copy the whole folder in again from the "
            f"download your {FOLDER} folder came from.",
        ) + "\n")


def test_an_editions_init_pasted_into_the_core_stops_the_import(tmp_path) -> None:
    def pasted_in(core: Path) -> None:
        shutil.copy(TOOLBOX / "__init__.py", core / "__init__.py")

    assert import_copy(tmp_path, change_core=pasted_in).endswith(import_stop(
        what="composer_core's __init__.py is an Edition's, such as this folder's.",
        why="Each folder's __init__.py does a different job, and an Edition's in composer_core "
        "makes the two import each other.",
        fix="Delete the composer_core folder, then copy the whole folder in again from the "
        f"download your {FOLDER} folder came from.",
    ) + "\n")
