"""The offline trap every test run carries: the test Python reaches nothing off this computer.

`tests/conftest.py` calls `install()` as it loads, in both Editions' runs. It installs the
trap Spark Composer's Example database runs its Spark under, `_refuse_the_network` in
spark_composer/engine.py, so the one rule holds for both: a lookup of any name but this
computer's own, or a connection, bind or message to any address but its own (127.0.0.1, ::1,
localhost, a Unix socket's path), raises RuntimeError, and so does any client library, such as
urllib or webbrowser, before it sends anything. engine.py is loaded by its path, under a name of
its own, which imports nothing of Spark's, so sqlglot Composer's run carries the same trap.
Loading it runs its module's own lines a second time, which start nothing: the stop it
registers for this Python's exit finds no Spark to stop.

Behind the trap stands a backstop: it stops any network event, or socket method given an
address, that names a host the trap's own tests try, should the trap ever let one through, so
no test reaches them. It stands in every run, where it stops nothing else.

A Python a test starts, such as with subprocess, doesn't carry the trap, apart from the Example
database's own process, which installs it itself.
"""

from __future__ import annotations

import importlib.util
import socket
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "spark_composer" / "engine.py"
# The hosts the trap's own tests try, which no test may reach.
TRIED_HOSTS = ("example.com", "192.0.2.1")
# The modules whose audit events reach the network, by the first part of an event's name.
NETWORK_EVENT_MODULES = ("socket", "urllib", "http", "webbrowser", "ftplib", "smtplib",
                         "poplib", "imaplib", "nntplib", "telnetlib")


def install() -> None:
    """Make this Python refuse anything that would reach another computer, with the backstop
    behind it.

    The backstop is called after the trap: its audit hook is added after the trap's, and its
    socket methods are wrapped before the trap's, so the trap's wrap their calls.
    """
    _backstop_the_socket_methods()
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
    if (event.split(".")[0] in NETWORK_EVENT_MODULES
            and any(host in repr(args) for host in TRIED_HOSTS)):
        raise AssertionError(f"the offline trap let {event} through: {args!r}")


def _backstop_the_socket_methods() -> None:
    """Put the backstop in front of each socket method given an address, which Python looks up
    before it raises the method's event."""
    socket.socket.connect = _backstopped("socket.connect", socket.socket.connect)
    socket.socket.connect_ex = _backstopped("socket.connect_ex", socket.socket.connect_ex)
    socket.socket.bind = _backstopped("socket.bind", socket.socket.bind)
    socket.socket.sendto = _backstopped("socket.sendto", socket.socket.sendto)
    if hasattr(socket.socket, "sendmsg"):  # Windows has none
        socket.socket.sendmsg = _backstopped("socket.sendmsg", socket.socket.sendmsg)


def _backstopped(event: str, method):
    def backstopped(self, *args):
        backstop(event, (self, *args))
        return method(self, *args)

    return backstopped
