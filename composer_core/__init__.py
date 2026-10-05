"""The code both Editions of the Toolbox share. Never import it yourself.

Import your Edition's folder instead, sqlglot_composer or spark_composer, which loads this
folder beside it and plugs in the two files of its own that write and run the Hive:

    from sqlglot_composer import statement, SELECT, AS, FROM, WHERE, GROUP_BY, to_hive, run

To update, delete this folder and your Edition's folder, copy both in again from one
download, and restart the kernel.
"""

from __future__ import annotations

import os

TOOLBOX_VERSION = "3.2"

# The export script writes this folder's file list here. On dev it is None, and the checks
# for missing and extra files are skipped.
_FILES = None

_HERE = os.path.dirname(os.path.abspath(__file__))


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
