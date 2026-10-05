"""Write Hive SQL as Python, one clause function per SQL clause.

Import everything from here, never from a file inside the folder:

    from sqlglot_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

The Toolbox is two folders side by side: this one, and composer_core, the code both Editions
share. To update, delete both folders, copy both in again from one download and restart the
kernel. The two check themselves when imported. If a file is missing, extra, from another
version or export, or from another Toolbox folder, or if this Python can't run the Toolbox, it
stops and says what happened, why it matters and the usual fix.

TOOLBOX_VERSION is the feature number, raised only when a big feature lands. VERSION is the
full text, which also says when this copy was exported.

>>> TOOLBOX_VERSION
'3.2'
>>> VERSION
'sqlglot Composer 3.2, ...'
"""

from __future__ import annotations

import importlib.util
import os

TOOLBOX_VERSION = "3.2"

# The folder this file belongs in, and the name its export stamps on each of that folder's
# files.
_FOLDER = "sqlglot_composer"
_PRODUCT = "sqlglot Composer"

# The export script writes this folder's file list here. On dev it is None, and the checks
# for missing and extra files are skipped.
_FILES = None

_HERE = os.path.dirname(os.path.abspath(__file__))
# The folder the import found, which a stop is headed by, even if you renamed it.
_IMPORTING = os.path.basename(_HERE)


def _stop_before_the_core(what, why, fix):
    """Stop the import while composer_core can't be trusted to say so itself."""
    raise ImportError(
        f"{_IMPORTING} stopped on import:"
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        "\n  Opt-out:        none - this one can't be switched off."
    )


# composer_core's own two files that check the rest: its __init__.py, and checks.py.
_CORE = importlib.util.find_spec("composer_core")
_CORE_HERE = (_CORE.submodule_search_locations or [""])[0] if _CORE else ""
if _CORE is None:
    _stop_before_the_core(
        what=f"The composer_core folder isn't beside the {_IMPORTING} folder.",
        why="composer_core holds the code both Editions share, so the Toolbox can't work "
        "without it.",
        fix="Copy the composer_core folder from the same download beside the "
        f"{_IMPORTING} folder, so the two sit side by side.",
    )
_CORE_MISSING = [name for name in ("__init__.py", "checks.py")
                 if not os.path.isfile(os.path.join(_CORE_HERE, name))]
if _CORE_MISSING:
    _stop_before_the_core(
        what=f"{', '.join(_CORE_MISSING)} {'is' if len(_CORE_MISSING) == 1 else 'are'} missing "
        "from the composer_core folder.",
        why="composer_core checks the Toolbox's folders when it is imported, and can't "
        "without its own files.",
        fix="Delete the composer_core folder, then copy the whole folder in again from the "
        f"download your {_IMPORTING} folder came from.",
    )
with open(os.path.join(_CORE_HERE, "__init__.py"), encoding="utf-8") as _file:
    if "\n_FOLDER = " in _file.read():
        _stop_before_the_core(
            what="composer_core's __init__.py is an Edition's, such as this folder's.",
            why="Each folder's __init__.py does a different job, and an Edition's in "
            "composer_core makes the two import each other.",
            fix="Delete the composer_core folder, then copy the whole folder in again from the "
            f"download your {_IMPORTING} folder came from.",
        )

import composer_core  # noqa: E402
from composer_core import checks  # noqa: E402

checks.check_python(_PRODUCT, _IMPORTING)
checks.check_folder(composer_core._HERE, "composer_core", "composer_core", composer_core._FILES,
                    composer_core.TOOLBOX_VERSION, _IMPORTING)
checks.check_folder(_HERE, _FOLDER, _PRODUCT, _FILES, TOOLBOX_VERSION, _IMPORTING)
checks.check_together(_HERE, TOOLBOX_VERSION, composer_core.TOOLBOX_VERSION)

# engine.py, one file per Edition, checks what the Edition needs installed. It is imported only
# once both folders are known to be whole, and before writing.py, which needs that library.
from . import engine  # noqa: E402

engine.check_installed()

VERSION = checks.version_text(_HERE, _PRODUCT, TOOLBOX_VERSION)

# The shared code reaches this Edition's writing.py and engine.py through composer_core's
# edition.py.
from composer_core import edition  # noqa: E402

from . import writing  # noqa: E402

edition.plug(_FOLDER, _PRODUCT, VERSION, writing, engine)

from composer_core.public import *  # noqa: E402, F403
from composer_core.public import __all__ as _SHARED_NAMES  # noqa: E402

__all__ = ["TOOLBOX_VERSION", "VERSION", *_SHARED_NAMES]
