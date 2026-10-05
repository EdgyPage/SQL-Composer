"""The import self-check: each Toolbox folder checks itself, then the two check each other.

At work the Toolbox is two folders pasted side by side: composer_core and one Edition's. The
Edition's __init__.py runs these checks before any other file is trusted. If a file is
missing, extra, from another version or export, or from another Toolbox folder, or if this
Python can't run the Toolbox, the import stops and says what happened, why it matters and the
usual fix. Every stop is headed by the folder you imported, `importing`, whichever folder it
found the problem in.
"""

from __future__ import annotations

import os
import re
import sys

from . import _stop

TOOLBOX_VERSION = "3.2"

_PYTHON_NEEDED = (3, 11)

# Any Toolbox folder's stamp, such as "sqlglot Composer 3.2, exported 2026-10-02 14:05 - ...",
# whose first words name the folder its file belongs in.
_STAMP = re.compile(r"(\w+ Composer|Composer core) \S+, exported ")


def check_python(product: str, importing: str) -> None:
    """Stop if this Python is too old for the Edition being imported."""
    if sys.version_info[:2] < _PYTHON_NEEDED:
        _stop(
            what=f"{product} needs Python 3.11 or newer, and this is Python "
            + ".".join(str(n) for n in sys.version_info[:3]) + ".",
            why=f"{product} is tested only on Python 3.11 and newer, and parts of it may not "
            "work on an older one.",
            fix="Choose a Python 3.11 or newer kernel (Kernel > Change Kernel in JupyterLab), "
            "or ask whoever looks after your environment to add one.",
            folder=importing,
        )


def version_of(path: str) -> str | None:
    """The TOOLBOX_VERSION a .py file declares, or None if it declares none."""
    with open(path, encoding="utf-8") as file:
        found = re.search(r'^TOOLBOX_VERSION = "([^"]*)"', file.read(), re.MULTILINE)
    return found.group(1) if found else None


def stamp_of(path: str) -> str | None:
    """The export stamp on line 1, or None.

    The export writes it as a `# ...` comment in a .py file and as `<!-- ... -->` in any
    other, since a `#` line in Markdown is a heading.
    """
    with open(path, encoding="utf-8", errors="replace") as file:
        first = file.readline().strip()
    start, end = ("# ", "") if path.endswith(".py") else ("<!-- ", " -->")
    stamp = first[len(start):len(first) - len(end)]
    if first.startswith(start) and first.endswith(end) and _STAMP.match(stamp):
        return stamp
    return None


def _version_and_time(stamp: str) -> str:
    """A stamp's version and export time, such as "Composer core 3.2, exported 2026-10-02 14:05"."""
    return stamp.split(" - ")[0]


def version_text(here: str, product: str, version: str) -> str:
    """The full version: the product and version, and when this copy was exported."""
    stamp = stamp_of(os.path.join(here, "__init__.py"))
    if stamp is None:
        return f"{product} {version}, not exported (dev)"
    return _version_and_time(stamp)


def _home_of(name: str, stamp: str | None, folder: str) -> str | None:
    """The folder a file belongs in: __init__.py knows its own, and a stamp names any other's.

    None for an unstamped file other than __init__.py.
    """
    if name == "__init__.py":
        return folder
    if stamp is None:
        return None
    return _STAMP.match(stamp).group(1).lower().replace(" ", "_")


def _check_home(here: str, folder: str, stamps: dict, importing: str) -> None:
    """Stop if a file came from another Toolbox folder than the one it sits in."""
    on_disk = os.path.basename(here)
    homes = {name: _home_of(name, stamp, folder) for name, stamp in stamps.items()}
    # The folder is the Toolbox folder its name and its files' stamps agree on. A folder its
    # files don't name, such as one you renamed, is the one most of its other files' stamps
    # name, so a __init__.py pasted in can't decide it; unstamped, as on dev, __init__.py's.
    votes = {}
    for name, home in homes.items():
        if name != "__init__.py" and home:
            votes[home] = votes.get(home, 0) + 1
    if on_disk in homes.values():
        this = on_disk
    elif votes:
        this = max(votes, key=votes.get)
    else:
        this = folder
    elsewhere = sorted(name for name, home in homes.items() if home not in (None, this))
    if elsewhere:
        home = homes[elsewhere[0]]
        where = f"the {on_disk} folder" + ("" if on_disk == this else f", a copy of {this}")
        _stop(
            what=f"{', '.join(elsewhere)} {'is' if len(elsewhere) == 1 else 'are'} from the "
            f"{home} folder, and this is {where}.",
            why="A folder's files are made to work only with each other: a .py file from "
            "another folder could make a Statement fail or come out wrong, and an "
            "examples.html or CHANGES.md from one may not describe this folder's code.",
            fix=f"Delete the {on_disk} folder, then copy it in again from the {this} folder "
            f"of one download, not from {home}.",
            folder=importing,
        )


def check_folder(here: str, folder: str, product: str, files, version: str,
                 importing: str) -> None:
    """Stop if a pasted Toolbox folder is missing a file, has an extra one, or mixes versions,
    exports or Toolbox folders.

    `here` is the folder on disk, `folder` the name it was exported as, `product` what the
    messages call it, `files` the file list the export wrote into its __init__.py (None on
    dev), `version` its __init__.py's TOOLBOX_VERSION, and `importing` the folder you imported.
    """
    on_disk = os.path.basename(here)
    present = sorted(
        name for name in os.listdir(here)
        if name != "__pycache__" and not name.startswith(".")
    )
    stamps = {
        name: stamp_of(os.path.join(here, name))
        for name in present if os.path.isfile(os.path.join(here, name))
    }
    # First, since a __init__.py from another folder brings that folder's file list and names.
    _check_home(here, folder, stamps, importing)
    if files is not None:
        extra = [name for name in present if name not in files]
        missing = [name for name in files if name not in present]
        if extra:
            _stop(
                what=f"{', '.join(extra)} {'is' if len(extra) == 1 else 'are'} in the "
                f"{on_disk} folder, but not part of {product} {version}.",
                why="A file left over from an earlier Toolbox version can still be imported, "
                "and would quietly run old code. A script of your own inside the folder would "
                "be deleted with it at the next update.",
                fix=f"Move any of your own scripts out first: they sit beside the {on_disk} "
                f"folder, never inside it. Then delete the {on_disk} folder, and copy the "
                f"whole folder in again from the {version} download.",
                folder=importing,
            )
        if missing:
            page = ("a missing CHANGES.md leaves you without the change notes"
                    if "CHANGES.md" in files else
                    "a missing examples.html or how_to.html leaves you without the Example "
                    "gallery or the how-tos")
            _stop(
                what=f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} missing "
                f"from the {on_disk} folder.",
                why=f"Every file of {product} {version} is needed: a missing .py file would "
                f"make a part of it fail later, far from the cause, and {page}.",
                fix=f"Delete the {on_disk} folder, then copy the whole folder in again from "
                f"the {version} download.",
                folder=importing,
            )
    for name in present:
        if not name.endswith(".py"):
            continue
        found = version_of(os.path.join(here, name))
        if found != version:
            _stop(
                what=f"{name} is from "
                + (f"Toolbox version {found}" if found else "another Toolbox version")
                + f", and {on_disk}/__init__.py is from {version}.",
                why="Files from different Toolbox versions weren't written to work together, "
                "so a Statement could fail or come out wrong.",
                fix=f"Delete the {on_disk} folder, then copy the whole folder in again from "
                "one download.",
                folder=importing,
            )
    if len(set(stamps.values())) > 1:
        odd = sorted(name for name, stamp in stamps.items() if stamp != stamps["__init__.py"])
        _stop(
            what=f"{', '.join(odd)} came from a different export than {on_disk}/__init__.py.",
            why="Two exports of the same Toolbox version can differ, so the files in this "
            "folder may not match each other.",
            fix=f"Delete the {on_disk} folder, then copy the whole folder in again from one "
            "download.",
            folder=importing,
        )


def check_together(edition_here: str, edition_version: str, core_version: str) -> None:
    """Stop if the Edition's folder and composer_core come from different versions or exports."""
    core_here = os.path.dirname(os.path.abspath(__file__))
    edition = os.path.basename(edition_here)
    if edition_version != core_version:
        what = (f"{edition} is from Toolbox version {edition_version}, and composer_core is "
                f"from {core_version}.")
    else:
        edition_stamp = stamp_of(os.path.join(edition_here, "__init__.py"))
        core_stamp = stamp_of(os.path.join(core_here, "__init__.py"))
        if edition_stamp is None or core_stamp is None:
            return
        edition_export = _version_and_time(edition_stamp).split(", exported ")[1]
        core_export = _version_and_time(core_stamp).split(", exported ")[1]
        if edition_export == core_export:
            return
        what = f"{edition} was exported {edition_export}, and composer_core {core_export}."
    _stop(
        what=what,
        why="The two folders are written to work only with each other's copy from the same "
        "download, so a Statement could fail or come out wrong.",
        fix=f"Delete the {edition} and composer_core folders, then copy both in again from "
        "one download.",
        folder=edition,
    )
