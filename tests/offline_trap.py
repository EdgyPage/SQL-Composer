"""The offline trap every test run carries: the test Python reaches nothing off this computer.

`tests/conftest.py` calls `install()` as it loads. A lookup of any name but this computer's own,
or a connection, bind or message to any address but its own (127.0.0.1, ::1, localhost, a Unix
socket's path), raises RuntimeError, and so does any client library, such as urllib or
webbrowser, before it sends anything.

Behind the trap stands a backstop: it stops any network event, or socket method given an
address, that names a host the trap's own tests try, should the trap ever let one through, so
no test reaches them. It stands in every run, where it stops nothing else.

A Python a test starts, such as with subprocess, doesn't carry the trap.
"""

from __future__ import annotations

import ipaddress
import os
import socket
import sys
from collections.abc import Callable

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
    _refuse_the_network()
    sys.addaudithook(backstop)


def backstop(event: str, args: tuple[object, ...]) -> None:
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


def _backstopped(event: str, method: Callable[..., int | None]) -> Callable[..., int | None]:
    def backstopped(self, *args: object) -> int | None:
        backstop(event, (self, *args))
        return method(self, *args)

    return backstopped


# --- The trap ------------------------------------------------------------------------------

# The audit events (PEP 578) through which a Python reaches another computer. A lookup gives the
# name it looks up first; a socket's event gives the socket, then the address, (host, port) or a
# Unix socket's path; a client library's gives its URL first, or itself and then its host.
_LOOKUPS = frozenset({"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
                      "socket.getnameinfo"})
_SOCKET_ADDRESSES = frozenset({"socket.connect", "socket.bind", "socket.sendto",
                               "socket.sendmsg"})
_CLIENT_URLS = frozenset({"urllib.Request", "webbrowser.open"})
_CLIENT_HOSTS = frozenset({"http.client.connect", "ftplib.connect", "smtplib.connect",
                           "poplib.connect", "imaplib.open", "nntplib.connect",
                           "telnetlib.Telnet.open"})
_REACHING = _LOOKUPS | _SOCKET_ADDRESSES | _CLIENT_URLS | _CLIENT_HOSTS


def _refuse_the_network() -> None:
    """Make this Python refuse, for as long as it runs, anything that would reach another
    computer.

    It still lets this Python connect to this computer, by 127.0.0.1, ::1 or localhost.
    """
    sys.addaudithook(_refuse_off_the_machine)
    # Python looks up a name given to a socket's method before it raises the method's event,
    # with no event for that lookup, so each method given an address judges it first.
    socket.socket.connect = _judged_first("socket.connect", socket.socket.connect)
    socket.socket.connect_ex = _judged_first("socket.connect", socket.socket.connect_ex)
    socket.socket.bind = _judged_first("socket.bind", socket.socket.bind)
    socket.socket.sendto = _judged_first("socket.sendto", socket.socket.sendto)
    if hasattr(socket.socket, "sendmsg"):  # Windows has none
        socket.socket.sendmsg = _judged_first("socket.sendmsg", socket.socket.sendmsg)


def _judged_first(event: str, method: Callable[..., int | None]) -> Callable[..., int | None]:
    """A socket method that refuses an address off this computer before Python looks it up."""

    def judged_first(self, *args: object) -> int | None:
        # The address is the last argument, and sendmsg is given one only with all four.
        if args and (event != "socket.sendmsg" or len(args) == 4):
            _refuse_off_the_machine(event, (self, args[-1]))
        return method(self, *args)

    return judged_first


def _refuse_off_the_machine(event: str, args: tuple[object, ...]) -> None:
    """Raise RuntimeError for an audit event that would reach off this computer."""
    if event in _REACHING:
        off = _off_the_machine(event, args)
        if off is not None:
            raise RuntimeError(f"{off} was refused: this Python reaches nothing off this "
                               "computer, only 127.0.0.1, ::1 and localhost.")


def _off_the_machine(event: str, args: tuple[object, ...]) -> str | None:
    """What an audit event would reach off this computer, as "socket.connect to '192.0.2.1'",
    or None when it stays on it.

    A lookup is allowed for this computer's own names, or for no name at all, which is answered
    with no lookup. A connection, a bind or a message is allowed to this computer's own
    addresses, or to a Unix socket's path, which is a file here: a bind to "" or "0.0.0.0"
    listens on every network the computer is on, so it is refused. A client library, such as
    urllib or webbrowser, is refused whatever it is given, since nothing here has any use for
    one.
    """
    if event in _CLIENT_URLS:
        return f"{event} of {args[0]!r}"
    if event in _CLIENT_HOSTS:
        return f"{event} to {args[1]!r}"
    if event in _LOOKUPS:
        name = _as_text(args[0][0] if isinstance(args[0], tuple) else args[0])
        return None if name in (None, "") or _on_this_machine(name) else f"{event} of {name!r}"
    if event in _SOCKET_ADDRESSES:
        address = args[1]
        # A connected socket's message, which goes where its connect went; or a Unix socket.
        if address is None or isinstance(address, (str, bytes, bytearray, os.PathLike)):
            return None
        host = _as_text(address[0] if isinstance(address, tuple) and address else address)
        return None if _on_this_machine(host) else f"{event} to {host!r}"
    return None


def _as_text(host: object) -> object:
    """A host given as bytes, as text; any other as it is."""
    return bytes(host).decode("ascii", "replace") if isinstance(host, (bytes, bytearray)) else host


def _on_this_machine(host: object) -> bool:
    """Whether a host is this computer: localhost, or a loopback address such as 127.0.0.1."""
    if not isinstance(host, str):
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.partition("%")[0]).is_loopback
    except ValueError:
        return False
