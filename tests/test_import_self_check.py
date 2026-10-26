"""The Toolbox checks itself on import, and stops with a plain message when it can't be trusted.

At work the Toolbox is one folder, `sqlglot_composer`. Each case copies it somewhere else,
breaks it the way a paste at work could, and imports it in a fresh Python. The folder's
version.txt says which Toolbox version it is, and in an exported copy lists each file's hash
(ADR 0013).
"""

from __future__ import annotations

import datetime
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import export_clean
import sqlglot_composer
import toolbox_registry
from sqlglot_composer import checks
from conftest import FOLDER, PRODUCT, import_stop, toolbox_folder

TOOLBOX = toolbox_folder()
VERSION = sqlglot_composer.TOOLBOX_VERSION
VERSION_FILE = toolbox_registry.VERSION_FILE
WHEN = datetime.datetime(2026, 10, 2, 14, 5)


def import_copy(tmp_path: Path, change: Callable[..., None] | None = None,
                name: str = FOLDER) -> str:
    """Copy the folder as `name`, apply `change` to the copy, import it, and return what it
    printed."""
    copy = tmp_path / name
    shutil.copytree(TOOLBOX, copy, ignore=shutil.ignore_patterns("__pycache__"))
    if change:
        change(copy)
    result = subprocess.run([sys.executable, "-c", f"import {name}"], cwd=tmp_path,
                            capture_output=True, text=True)
    return result.stderr


def exported(copy: Path) -> None:
    """Write the copy's version.txt as the export does, listing each of its files' hashes."""
    hashes = {path.name: checks.git_hash(path.read_bytes()) for path in copy.iterdir()
              if path.is_file() and path.name != VERSION_FILE}
    (copy / VERSION_FILE).write_text(
        export_clean.version_file_text(PRODUCT, VERSION, WHEN, "0" * 40, hashes),
        encoding="utf-8", newline="\n")


def test_an_untouched_dev_copy_imports(tmp_path: Path) -> None:
    assert import_copy(tmp_path) == ""


def test_an_exported_copy_imports(tmp_path: Path) -> None:
    assert import_copy(tmp_path, exported) == ""


def test_the_version_is_written_in_one_place() -> None:
    """No file of the folder but version.txt names the version (ADR 0013)."""
    assert (TOOLBOX / VERSION_FILE).read_text(encoding="utf-8") == f"{PRODUCT} {VERSION}\n"
    for path in sorted(TOOLBOX.glob("*.py")):
        assert not re.search(r'^TOOLBOX_VERSION = "', path.read_text(encoding="utf-8"),
                             re.MULTILINE), path.name


def test_an_extra_file_stops_the_import(tmp_path: Path) -> None:
    def extra(copy: Path) -> None:
        exported(copy)
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


def test_a_missing_refusals_file_still_says_what_is_missing(tmp_path: Path) -> None:
    """The four-part message is built in the folder's __init__.py, so it works without
    refusals.py."""
    def missing(copy: Path) -> None:
        exported(copy)
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
def test_a_missing_page_stops_the_import_and_says_what_it_holds(
        tmp_path: Path, pages: list[str], lost: str) -> None:
    assert sorted(pages) == [page for page in toolbox_registry.PAGES if page in pages]

    def missing(copy: Path) -> None:
        exported(copy)
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


def test_a_folder_missing_what_checks_it_stops_the_import(tmp_path: Path) -> None:
    assert import_copy(tmp_path, lambda copy: (copy / "checks.py").unlink()).endswith(
        import_stop(
            what=f"checks.py is missing from the {FOLDER} folder.",
            why="The folder checks itself when it is imported, and can't without that file.",
            fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
            "download.",
        ) + "\n")


def test_a_folder_missing_its_version_file_stops_the_import(tmp_path: Path) -> None:
    assert import_copy(tmp_path, lambda copy: (copy / VERSION_FILE).unlink()).endswith(
        import_stop(
            what=f"{VERSION_FILE} is missing from the {FOLDER} folder.",
            why="It says which Toolbox version the folder is and lists its files, and the folder "
            "can't check itself without it.",
            fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
            "download.",
        ) + "\n")


@pytest.mark.parametrize("first", ["hello", f"Other Composer {VERSION}", PRODUCT])
def test_an_unreadable_version_file_stops_the_import(tmp_path: Path, first: str) -> None:
    assert import_copy(tmp_path, lambda copy: (copy / VERSION_FILE).write_text(
        f"{first}\n", encoding="utf-8")).endswith(import_stop(
            what=f"{FOLDER}/{VERSION_FILE} doesn't start with \"{PRODUCT}\" and a version "
            "number, as the download's does.",
            why="The folder can't tell which Toolbox version it is, so it can't check its files.",
            fix=f"Delete the {FOLDER} folder, then copy the whole folder in again from the "
            "download.",
        ) + "\n")


def test_a_version_file_saved_with_a_byte_order_mark_reads(tmp_path: Path) -> None:
    """Old Notepad, and PowerShell 5's Set-Content -Encoding UTF8, save one on line 1."""
    def with_mark(copy: Path) -> None:
        exported(copy)
        path = copy / VERSION_FILE
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    assert import_copy(tmp_path, with_mark) == ""


def edited(*names: str) -> Callable[[Path], None]:
    """Export the copy, then change each of `names` after, as a hand edit or a paste would."""
    def change(copy: Path) -> None:
        exported(copy)
        for name in names:
            path = copy / name
            path.write_text(path.read_text(encoding="utf-8") + "\n# changed\n",
                            encoding="utf-8")
    return change


@pytest.mark.parametrize("odd", ["writing.py", "tables.py", "examples.html"])
def test_a_file_that_differs_from_the_download_only_warns(tmp_path: Path, odd: str) -> None:
    printed = import_copy(tmp_path, edited(odd))
    assert "Traceback" not in printed
    assert "UserWarning: sqlglot_composer on import:" in printed
    assert (f"What happened:  {odd} differs from the file the {PRODUCT} {VERSION} download "
            f"holds, which {VERSION_FILE} lists.") in printed
    assert (f"Usual fix:      Delete the {FOLDER} folder and copy the whole folder in again from "
            f"the {VERSION} download. If you changed a file on purpose, keep that change in a "
            f"script of your own beside the {FOLDER} folder instead: this shows at every import "
            "until the folder matches its download.") in printed


def test_every_file_that_differs_is_named_in_one_warning(tmp_path: Path) -> None:
    printed = import_copy(tmp_path, edited("writing.py", "engine.py"))
    assert printed.count("What happened:") == 1
    assert "What happened:  engine.py, writing.py differ from the" in printed


def test_a_copy_saved_with_windows_line_endings_matches(tmp_path: Path) -> None:
    def windows(copy: Path) -> None:
        exported(copy)
        path = copy / "writing.py"
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    assert import_copy(tmp_path, windows) == ""


def test_the_hash_is_gits_own() -> None:
    """`git hash-object` gives this file 2c18545..., worked out once with git."""
    git_says = "2c1854573a40224de599dd57077637eb5f882072"
    assert checks.git_hash(b"x = 1\ny = 2\n") == git_says
    assert export_clean.git_hash(b"x = 1\ny = 2\n") == git_says


def test_an_exported_copy_says_when_it_was_exported(tmp_path: Path) -> None:
    def shown(copy: Path) -> None:
        exported(copy)
        (copy.parent / "show.py").write_text(f"import {FOLDER}\nprint({FOLDER}.VERSION)\n",
                                             encoding="utf-8")

    import_copy(tmp_path, shown)
    done = subprocess.run([sys.executable, "show.py"], cwd=tmp_path, capture_output=True,
                          text=True)
    assert done.stdout.strip() == f"{PRODUCT} {VERSION}, exported 2026-10-02 14:05"


def test_a_previewed_copy_says_when_it_was_built(tmp_path: Path) -> None:
    """A preview names its commit with a note after it, which is still an export line."""
    (tmp_path / VERSION_FILE).write_text(export_clean.version_file_text(
        PRODUCT, VERSION, WHEN, "abc123 (a preview of the checkout)", {"x.py": "0" * 40}),
        encoding="utf-8")
    version_file = checks.read_version_file(str(tmp_path), PRODUCT, FOLDER)
    assert checks.version_text(PRODUCT, version_file) == (
        f"{PRODUCT} {VERSION}, exported 2026-10-02 14:05")


def test_a_dev_copy_says_it_was_not_exported() -> None:
    assert sqlglot_composer.VERSION == f"{PRODUCT} {VERSION}, not exported (dev)"


def test_an_older_python_stops_the_import(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_a_renamed_folder_imports(tmp_path: Path) -> None:
    assert import_copy(tmp_path, exported, name="my_toolbox") == ""


def test_a_stop_in_a_renamed_folder_is_headed_by_its_own_name(tmp_path: Path) -> None:
    def extra(copy: Path) -> None:
        exported(copy)
        (copy / "my_notes.py").write_text("x = 1\n", encoding="utf-8")

    stopped = import_copy(tmp_path, extra, name="my_toolbox")
    assert "ImportError: my_toolbox stopped on import:" in stopped
    assert "my_notes.py is in the my_toolbox folder" in stopped
