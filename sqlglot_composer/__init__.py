"""Write Hive SQL as Python, one clause function per SQL clause.

Import everything from here, never from a file inside the folder:

    from sqlglot_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

The Toolbox is this one folder. To update, delete it, copy it in again from the download and
restart the kernel. It checks itself when imported. If a file is missing, extra, from another
version or export, or from another Toolbox folder, or if this Python can't run the Toolbox, it
stops and says what happened, why it matters and the usual fix.

TOOLBOX_VERSION is the feature number, raised only when a big feature lands. VERSION is the
full text, which also says when this copy was exported.

>>> TOOLBOX_VERSION
'6.0'
>>> VERSION
'sqlglot Composer 6.0, ...'
"""

from __future__ import annotations

import os

TOOLBOX_VERSION = "6.0"

# The folder this file belongs in, and the name its export stamps on each of the folder's
# files.
_FOLDER = "sqlglot_composer"
_PRODUCT = "sqlglot Composer"

# The export script writes this folder's file list here. On dev it is None, and the checks
# for missing and extra files are skipped.
_FILES = None

_HERE = os.path.dirname(os.path.abspath(__file__))
# The folder the import found, which a stop is headed by, even if you renamed it.
_IMPORTING = os.path.basename(_HERE)


def _four_part_message(what: str, why: str, fix: str, opt_out: str | None) -> str:
    """The one shape every refusal and Warning message has, and every import stop too.

    It lives here, not in refusals.py, because the import self-check needs it before any
    other file in the folder can be trusted, or even found.
    """
    if opt_out is None:
        opt_out = "none - this one can't be switched off."
    return (
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        f"\n  Opt-out:        {opt_out}"
    )


def _stop(what, why, fix, folder):
    """Stop the import of `folder`, the one you imported, with the four-part message. No import
    stop can be switched off."""
    raise ImportError(f"{folder} stopped on import:"
                      + _four_part_message(what=what, why=why, fix=fix, opt_out=None))


if not os.path.isfile(os.path.join(_HERE, "checks.py")):
    _stop(
        what=f"checks.py is missing from the {_IMPORTING} folder.",
        why="The folder checks itself when it is imported, and can't without that file.",
        fix=f"Delete the {_IMPORTING} folder, then copy the whole folder in again from the "
        "download.",
        folder=_IMPORTING,
    )

from . import checks  # noqa: E402

checks.check_python(_PRODUCT, _IMPORTING)
checks.check_folder(_HERE, _FOLDER, _PRODUCT, _FILES, TOOLBOX_VERSION, _IMPORTING)

# engine.py checks that sqlglot is installed. It is imported only once the folder is known to
# be whole, and before writing.py, which needs sqlglot.
from . import engine  # noqa: E402

engine.check_installed()

VERSION = checks.version_text(_HERE, _PRODUCT, TOOLBOX_VERSION)

from . import writing  # noqa: E402, F401
from .public import *  # noqa: E402, F403
from .public import __all__ as _PUBLIC_NAMES  # noqa: E402

__all__ = ["TOOLBOX_VERSION", "VERSION", *_PUBLIC_NAMES]

# The admin module, imported by name, as `from sqlglot_composer import admin`: the star import
# leaves it out, since its functions change your own Saved tables.
from . import admin  # noqa: E402, F401

# The project module, imported by name too, as `from sqlglot_composer import project`: its
# functions make and archive a Project's folders and files.
from . import project  # noqa: E402, F401
