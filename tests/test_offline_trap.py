"""Every test runs under the offline trap: its Python reaches nothing off this computer.

`tests/conftest.py` installs `offline_trap` as it loads, in both Editions' runs, so a test, or
a library a test calls, that looks up a name or connects anywhere but this computer fails. The
trap is the one Spark Composer's Example database runs under (`_refuse_the_network` in
spark_composer/engine.py).

These tests raise each audit event by hand, with sys.audit, so nothing could be sent even if the
trap let one through. Then, in a Python of their own, they make the real calls, behind the
trap's backstop, which stops them should the trap ever let one through: so no test here reaches
the network, whatever the trap does.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import offline_trap

# A socket's own argument, which the trap doesn't read: these events are raised by hand.
SOCKET = None
REFUSED = [
    ("socket.getaddrinfo", ("example.com", 80, 0, 0, 0)),
    ("socket.getaddrinfo", (b"example.com", 80, 0, 0, 0)),
    ("socket.getaddrinfo", ("192.0.2.1", 80, 0, 0, 0)),
    ("socket.gethostbyname", ("example.com",)),
    ("socket.gethostbyaddr", ("192.0.2.1",)),
    ("socket.getnameinfo", (("192.0.2.1", 80),)),
    ("socket.connect", (SOCKET, ("example.com", 80))),
    ("socket.connect", (SOCKET, ("192.0.2.1", 80))),
    ("socket.connect", (SOCKET, ("2001:db8::1", 80, 0, 0))),
    ("socket.connect", (SOCKET, ("", 80))),
    ("socket.sendto", (SOCKET, ("192.0.2.1", 53))),
    ("socket.sendmsg", (SOCKET, ("192.0.2.1", 53))),
    # Every network the computer is on, not this computer alone.
    ("socket.bind", (SOCKET, ("0.0.0.0", 0))),
    ("socket.bind", (SOCKET, ("", 0))),
    ("socket.bind", (SOCKET, ("::", 0, 0, 0))),
    # A client library is refused whatever its host.
    ("urllib.Request", ("http://example.com", None, {}, "GET")),
    ("http.client.connect", (SOCKET, "127.0.0.1", 80)),
    ("webbrowser.open", ("http://example.com",)),
    ("ftplib.connect", (SOCKET, "example.com", 21)),
    ("smtplib.connect", (SOCKET, "example.com", 25)),
    ("poplib.connect", (SOCKET, "example.com", 110)),
    ("imaplib.open", (SOCKET, "example.com", 143)),
    ("nntplib.connect", (SOCKET, "example.com", 119)),
    ("telnetlib.Telnet.open", (SOCKET, "example.com", 23)),
]
ALLOWED = [
    ("socket.getaddrinfo", ("127.0.0.1", 80, 0, 0, 0)),
    ("socket.getaddrinfo", ("localhost", 80, 0, 0, 0)),
    ("socket.getaddrinfo", ("::1", 80, 0, 0, 0)),
    # No name: answered on this computer, with no lookup.
    ("socket.getaddrinfo", (None, 80, 0, 0, 0)),
    ("socket.gethostbyname", ("localhost",)),
    ("socket.getnameinfo", (("127.0.0.1", 80),)),
    ("socket.connect", (SOCKET, ("127.0.0.1", 5000))),
    ("socket.connect", (SOCKET, ("::1", 5000, 0, 0))),
    ("socket.connect", (SOCKET, ("localhost", 5000))),
    # A Unix socket's path is a file on this computer.
    ("socket.connect", (SOCKET, "/tmp/a.sock")),
    ("socket.bind", (SOCKET, ("127.0.0.1", 0))),
    ("socket.bind", (SOCKET, ("localhost", 0))),
    # A connected socket's message goes where its connect, already allowed, went.
    ("socket.sendmsg", (SOCKET, None)),
    ("socket.sendto", (SOCKET, ("127.0.0.1", 53))),
    # Events that reach no other computer.
    ("open", ("example.com", "r", 0)),
    ("socket.gethostname", ()),
]


@pytest.mark.parametrize(("event", "args"), REFUSED, ids=lambda value: str(value))
def test_this_python_refuses_what_would_reach_another_computer(event: str, args: tuple) -> None:
    with pytest.raises(RuntimeError, match=f"^{event} .* was refused: this Python reaches "
                       "nothing off this computer"):
        sys.audit(event, *args)


@pytest.mark.parametrize(("event", "args"), ALLOWED, ids=lambda value: str(value))
def test_this_python_allows_what_stays_on_this_computer(event: str, args: tuple) -> None:
    sys.audit(event, *args)


# A Python of its own, under the trap and its backstop, making the real calls: each line it
# prints says what it tried and what became of it.
TRIES = f"""
import socket, sys, urllib.request, webbrowser
sys.path.insert(0, {str(Path(offline_trap.__file__).parent)!r})
import offline_trap
offline_trap.install()

def tried(what, call):
    try:
        call()
    except RuntimeError as error:
        print(what, "refused:", str(error).split(" was refused")[0])
    else:
        print(what, "allowed")

with socket.create_server(("127.0.0.1", 0)) as listener:
    tried("a connection to 127.0.0.1",
          lambda: socket.create_connection(listener.getsockname(), timeout=5).close())
tried("getaddrinfo", lambda: socket.getaddrinfo("example.com", 80))
tried("create_connection",
      lambda: socket.create_connection(("example.com", 80), timeout=1).close())
with socket.socket() as stray:
    stray.settimeout(1)
    tried("connect", lambda: stray.connect(("192.0.2.1", 80)))
    # Python looks a name given to connect up before it raises connect's event.
    tried("connect by name", lambda: stray.connect(("example.com", 80)))
    tried("bind by name", lambda: stray.bind(("example.com", 0)))
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as datagrams:
    tried("sendto by name", lambda: datagrams.sendto(b"x", ("example.com", 53)))
tried("urlopen", lambda: urllib.request.urlopen("http://example.com", timeout=1))
# A browser of its own, so the call is the same wherever the test runs: one that does nothing.
webbrowser.register("offline-trap", None,
                    webbrowser.GenericBrowser([sys.executable, "-c", "pass"]), preferred=True)
tried("webbrowser.open", lambda: webbrowser.open("http://example.com"))
"""


def test_the_real_calls_are_refused_before_anything_is_sent() -> None:
    done = subprocess.run([sys.executable, "-c", TRIES], capture_output=True, text=True,
                          timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == [
        "a connection to 127.0.0.1 allowed",
        # create_connection is refused at its lookup, before any connection.
        "getaddrinfo refused: socket.getaddrinfo of 'example.com'",
        "create_connection refused: socket.getaddrinfo of 'example.com'",
        "connect refused: socket.connect to '192.0.2.1'",
        # Refused before Python looks the name up.
        "connect by name refused: socket.connect to 'example.com'",
        "bind by name refused: socket.bind to 'example.com'",
        "sendto by name refused: socket.sendto to 'example.com'",
        "urlopen refused: urllib.Request of 'http://example.com'",
        "webbrowser.open refused: webbrowser.open of 'http://example.com'",
    ]


def test_the_backstop_stops_what_the_trap_would_let_through() -> None:
    # An event the trap allows, naming a host the tests try: only the backstop can stop it.
    with pytest.raises(AssertionError, match="the offline trap let socket.connect through"):
        offline_trap.backstop("socket.connect", (SOCKET, "/tmp/example.com.sock"))
    offline_trap.backstop("socket.connect", (SOCKET, ("127.0.0.1", 80)))
    # A file's source, as compile is given it, can name a host without reaching it.
    offline_trap.backstop("compile", ("socket.getaddrinfo('example.com', 80)", "<string>"))
