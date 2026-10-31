"""The import self-check: the Toolbox's folder checks itself before any other file is trusted.

At work the Toolbox is one folder pasted beside your scripts. Its __init__.py runs these checks
before any other file is trusted. The folder's version.txt says which Toolbox and version it is,
and, in a copy from the download, lists every file with its hash. If a file is missing or
extra, if version.txt is missing or unreadable, or if this Python can't run the Toolbox, the
import stops and says what happened, why it matters and the usual fix. A file
whose hash isn't the one listed, edited by hand or pasted from another download, only warns.
Every message is headed by the folder you imported, `importing`, whichever folder it found the
problem in.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import warnings
from typing import NamedTuple

from . import _four_part_message, _stop
from .shared import singular_or_plural

_PYTHON_NEEDED = (3, 11)

VERSION_FILE = "version.txt"

# version.txt's first line, such as "sqlglot Composer 7.2": the Toolbox and its version.
_FIRST_LINE = re.compile(r"(?P<product>.+) (?P<version>\d+\.\d+)")
# Its export line, such as "exported 2026-10-26 14:05 from dev commit 768f7ce...", or, from a
# preview of a checkout, "... from dev commit 768f7ce... (a preview of the checkout)".
_EXPORTED = re.compile(r"exported (?P<when>\d{4}-\d\d-\d\d \d\d:\d\d) from dev commit .+")
# Each file's line: its git hash, two spaces, and its name.
_FILE_LINE = re.compile(r"(?P<hash>[0-9a-f]{40})  (?P<name>\S+)")

# What each file of a Toolbox folder that isn't Python holds, for a stop that finds it missing.
_PAGES = {"examples.html": "the Example gallery", "how_to.html": "the how-tos"}


class VersionFile(NamedTuple):
    """What a folder's version.txt says: the Toolbox, its version, when it was exported (None on
    dev) and each file's hash (None on dev)."""

    product: str
    version: str
    exported: str | None
    hashes: dict[str, str] | None


def git_hash(data: bytes) -> str:
    """The hash `git hash-object` gives a file holding `data`, with its line endings as LF, so a
    copy saved with Windows line endings hashes the same."""
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def check_python(product: str, importing: str) -> None:
    """Stop if this Python is too old for the Toolbox."""
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


def read_version_file(here: str, product: str, importing: str) -> VersionFile:
    """The folder's version.txt, or a stop if it is missing, or its first line doesn't name this
    Toolbox and a version."""
    on_disk = os.path.basename(here)
    path = os.path.join(here, VERSION_FILE)
    if not os.path.isfile(path):
        _stop(
            what=f"{VERSION_FILE} is missing from the {on_disk} folder.",
            why="It says which Toolbox version the folder is and lists its files, and the "
            "folder can't check itself without it.",
            fix=f"Delete the {on_disk} folder, then copy the whole folder in again from the "
            "download.",
            folder=importing,
        )
    # utf-8-sig, since an editor that saves a byte-order mark puts one at the start of line 1.
    with open(path, encoding="utf-8-sig", errors="replace") as file:
        lines = [line.strip() for line in file if line.strip() and not line.startswith("#")]
    first = _FIRST_LINE.fullmatch(lines[0]) if lines else None
    if first is None or first["product"] != product:
        _stop(
            what=f"{on_disk}/{VERSION_FILE} doesn't start with \"{product}\" and a version "
            "number, as the download's does.",
            why="The folder can't tell which Toolbox version it is, so it can't check its files.",
            fix=f"Delete the {on_disk} folder, then copy the whole folder in again from the "
            "download.",
            folder=importing,
        )
    exported = next((found["when"] for found in map(_EXPORTED.fullmatch, lines[1:]) if found),
                    None)
    listed = [found for found in map(_FILE_LINE.fullmatch, lines[1:]) if found]
    hashes = {found["name"]: found["hash"] for found in listed} if listed else None
    return VersionFile(first["product"], first["version"], exported, hashes)


def version_text(product: str, version_file: VersionFile) -> str:
    """The full version: the product and version, and when this copy was exported."""
    if version_file.exported is None:
        return f"{product} {version_file.version}, not exported (dev)"
    return f"{product} {version_file.version}, exported {version_file.exported}"


def check_folder(here: str, product: str, version_file: VersionFile, importing: str) -> None:
    """Stop if a pasted Toolbox folder is missing a file or has an extra one, and warn about a
    file whose hash isn't the one version.txt lists.

    `here` is the folder on disk, `product` what the messages call it, `version_file` its
    version.txt, read, and `importing` the folder you imported. On dev version.txt lists no
    files, and nothing is checked.
    """
    if version_file.hashes is None:
        return
    on_disk = os.path.basename(here)
    present = sorted(
        name for name in os.listdir(here)
        if name != "__pycache__" and not name.startswith(".")
    )
    files = sorted([*version_file.hashes, VERSION_FILE])
    extra = [name for name in present if name not in files]
    missing = [name for name in files if name not in present]
    number = version_file.version
    if extra:
        _stop(
            what=f"{', '.join(extra)} {singular_or_plural(len(extra), 'is', 'are')} in the "
            f"{on_disk} folder, but not part of {product} {number}.",
            why="A file left over from an earlier Toolbox version can still be imported, "
            "and would quietly run old code. A script of your own inside the folder would "
            "be deleted with it at the next update.",
            fix=f"Move any of your own scripts out first: they sit beside the {on_disk} "
            f"folder, never inside it. Then delete the {on_disk} folder, and copy the "
            f"whole folder in again from the {number} download.",
            folder=importing,
        )
    if missing:
        lost = ["a missing .py file would make a part of it fail later, far from the cause"]
        lost += [f"a missing {name} leaves you without {_PAGES[name]}"
                 for name in missing if name in _PAGES]
        _stop(
            what=f"{', '.join(missing)} "
            f"{singular_or_plural(len(missing), 'is', 'are')} missing "
            f"from the {on_disk} folder.",
            why=f"Every file of {product} {number} is needed: "
            + (", ".join(lost[:-1]) + ", and " if len(lost) > 1 else "") + f"{lost[-1]}.",
            fix=f"Delete the {on_disk} folder, then copy the whole folder in again from "
            f"the {number} download.",
            folder=importing,
        )
    changed = []
    for name, listed in version_file.hashes.items():
        with open(os.path.join(here, name), "rb") as file:
            if git_hash(file.read()) != listed:
                changed.append(name)
    if changed:
        warnings.warn(
            f"{importing} on import:" + _four_part_message(
                what=f"{', '.join(changed)} "
                f"{singular_or_plural(len(changed), 'differs', 'differ')} "
                f"from the {singular_or_plural(len(changed), 'file', 'files')} "
                f"the {product} {number} "
                f"download holds, which {VERSION_FILE} lists.",
                why="A file edited by hand, or pasted from another download, may not work with "
                "the rest of the folder, so a Statement could fail or come out wrong. It only "
                "warns, since a change you made on purpose may be one you need.",
                fix=f"Delete the {on_disk} folder and copy the whole folder in again from the "
                f"{number} download. If you changed a file on purpose, keep that change in a "
                f"script of your own beside the {on_disk} folder instead: this shows at every "
                "import until the folder matches its download.",
                opt_out=None),
            UserWarning, stacklevel=3)
