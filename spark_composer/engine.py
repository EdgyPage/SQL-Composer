"""What Spark Composer runs on: the pyspark it needs, and the Spark of its Example database.

`__init__.py` calls `check_installed()` as soon as it knows the folder is whole, before it imports
any other file. It reads pyspark's version without starting Spark, so importing Spark Composer
needs no Java. The Example database hands `run_query` a query's Hive and its tables, and gets
back the query's column names and rows. This file imports pyspark only inside its functions, so
it can be imported to check pyspark before pyspark is trusted.
"""

from __future__ import annotations

import re

from . import _four_part_message as four_part_message
from . import _stop

TOOLBOX_VERSION = "2.1"

_LOWEST = (3, 5, 0)
_BELOW = (4, 1, 0)
_NEWEST_TESTED = (4, 0, 4)


# --- pyspark ------------------------------------------------------------------------------------


def _dotted(numbers):
    return ".".join(str(n) for n in numbers)


def _numbers(text):
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(n) for n in found.groups()) if found else None


_IN_RANGE = f'"pyspark>={_dotted(_LOWEST)},<{_dotted(_BELOW)}"'
_NO_INSTALLING = "If you can't install packages, ask whoever looks after your environment."


def check_installed():
    """Refuse a pyspark outside the supported range."""
    try:
        import pyspark
    except ImportError:
        _stop(
            what="Spark Composer needs pyspark, and this Python can't import it.",
            why="Spark Composer runs every Statement's Hive on Spark, and its Example database "
            "is a Spark of its own, so it can't run anything without it.",
            fix=f"Install pyspark from a notebook cell with %pip install {_IN_RANGE}, then "
            f"restart the kernel. {_NO_INSTALLING}",
        )
    found = getattr(pyspark, "__version__", "unknown")
    version = _numbers(found)
    if version is None or not _LOWEST <= version < _BELOW:
        _stop(
            what=f"Spark Composer needs pyspark {_dotted(_LOWEST)} or newer, below "
            f"{_dotted(_BELOW)}, and this Python has pyspark {found}.",
            why="Spark Composer is checked only on that range of pyspark. Another Spark can "
            "read the same Hive differently, so a Statement could come out wrong without "
            "anything saying so.",
            fix="Install a pyspark in that range from a notebook cell with %pip install "
            f"{_IN_RANGE}, then restart the kernel. {_NO_INSTALLING}",
        )
    if version > _NEWEST_TESTED:
        print(f"Note: pyspark {found} is newer than any version Spark Composer was tested on "
              f"({_dotted(_NEWEST_TESTED)}).")


# --- The Example database's Spark -----------------------------------------------------------


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can."""
    return "the Example database's Spark isn't built yet (ticket 19 of the PySpark work)"


def run_query(text: str, tables: dict) -> tuple[list, list]:
    """Run a query's Hive on the Example database's Spark: its column names, and its rows."""
    raise RuntimeError(four_part_message(
        what="Spark Composer's Example database can't run a query yet.",
        why="Its Spark isn't built yet.",
        fix="See the Hive with to_hive(...), and run it with your own send.",
        opt_out=None,
    ))
