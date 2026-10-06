"""The offline trap every test run carries: the test Python reaches nothing off this computer.

`tests/conftest.py` calls `install()` as it loads, in both Editions' runs. It installs the
audit hook (PEP 578) that Spark Composer's Example database runs its Spark under,
`_refuse_the_network` in spark_composer/engine.py, so the one rule holds for both: a lookup of
any name but this computer's own, or a connection, bind or message to any address but its own
(127.0.0.1, ::1, localhost, a Unix socket's path), raises RuntimeError, and so does any client
library, such as urllib or webbrowser, before it sends anything. engine.py is loaded by its path,
which imports nothing of Spark's, so sqlglot Composer's run carries the same trap.

Behind the trap stands a backstop, for the trap's own tests: it stops any network event that
names a host those tests try, should the trap ever let one through, so no test reaches them.

A Python a test starts, such as with subprocess, doesn't carry the trap, apart from the Example
database's own process, which installs it itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "spark_composer" / "engine.py"
# The hosts the trap's own tests try, which no test may reach.
TRIED = ("example.com", "192.0.2.1")
# The modules whose audit events reach the network, as the backstop reads them by name.
NETWORK = ("socket", "urllib", "http", "webbrowser", "ftplib", "smtplib", "poplib", "imaplib",
           "nntplib", "telnetlib")


def install() -> None:
    """Make this Python refuse anything that would reach another computer, then add the
    backstop."""
    _engine()._refuse_the_network()
    sys.addaudithook(backstop)


def _engine():
    """Spark Composer's engine.py, loaded by its path, under a name of its own."""
    spec = importlib.util.spec_from_file_location("offline_trap_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backstop(event: str, args: tuple) -> None:
    """Stop a network event that names a host the trap's tests try: the trap let it through."""
    if event.split(".")[0] in NETWORK and any(host in repr(args) for host in TRIED):
        raise AssertionError(f"the offline trap let {event} through: {args!r}")
