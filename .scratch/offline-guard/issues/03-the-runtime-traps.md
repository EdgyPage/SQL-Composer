# The runtime traps

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

Plan steps 4 and 5: `tests/offline_trap.py`, an audit hook installed by tests/conftest.py in both Editions' runs, and `_refuse_the_network()` in spark_composer/engine.py's child before pyspark loads.

## Done when

- Both runs pass with the trap on; a non-loopback lookup is refused in the test Python and in the Spark child.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in 2fd1b0d, fixed up after its code review in the commit that resolves this ticket.

- **One rule, in the Toolbox.** `spark_composer/engine.py` holds it: `_off_the_machine(event,
  args) -> str | None`, a pure function naming what an audit event (PEP 578) would reach off
  this computer, and `_refuse_the_network()`, which adds the audit hook that raises
  RuntimeError ("socket.getaddrinfo of 'example.com' was refused: this Python reaches nothing
  off this computer, only 127.0.0.1, ::1 and localhost.") and wraps socket's methods given an
  address (below). `_serve` calls it as its first line, before stdin, the connect-back or any
  pyspark/py4j import. The rule lives in engine.py because the child runs engine.py as a script
  and can import nothing of the repo's; `tests/offline_trap.py` loads engine.py by its path
  (under the name `offline_trap_engine`; engine.py imports pyspark only inside functions), so
  the tests run the very same code, with no second copy to keep in step.
- **The rule, by event** (3.11 argument shapes checked against the stdlib and a live probe):
  - `socket.getaddrinfo` / `gethostbyname` / `gethostbyaddr` (name first), `socket.getnameinfo`
    (sockaddr first): allowed for localhost, a loopback IP (127.0.0.0/8, ::1) or no name
    (None, ""), which is answered with no lookup; refused otherwise.
  - `socket.connect` (connect_ex too) / `bind` / `sendto` / `sendmsg` (socket, address):
    allowed for a loopback host, a Unix socket's path (str, bytes, PathLike) and sendmsg with no
    address (a connected socket); refused otherwise, so a bind to "", "0.0.0.0" or "::" is
    refused, and so is any shape it can't read.
  - `urllib.Request`, `webbrowser.open` (URL first), `http.client.connect`, `ftplib.connect`,
    `smtplib.connect`, `poplib.connect`, `imaplib.open`, `nntplib.connect`,
    `telnetlib.Telnet.open` (self, host): refused whatever the host.
  - anything else: not judged.
- **The tests' trap.** `tests/offline_trap.py`'s `install()`, called by `tests/conftest.py` as it
  loads, in both Editions' runs and the low venv. Behind it a backstop (audit hook added after
  the trap's, socket wraps put on before the trap's) stops any network event or socket call
  naming a host the trap's tests try (example.com, 192.0.2.1), so no test reaches them even if
  the trap broke; checked by running the real calls with the backstop alone. A Python a test
  starts doesn't carry the trap (the Example database's process installs its own); the
  docstring says so. Nothing in the three runs tripped it, so the trap needed no loosening.
  Python workers the Spark JVM starts (for Python UDFs, which the Example database doesn't
  use) don't carry it either; its Java stays held to 127.0.0.1 by `_settings`/`_environment`.
- **The tests.** `tests/test_offline_trap.py` (both runs): each event raised by hand with
  sys.audit, 24 refused and 16 allowed; then, in a Python of its own under `install()`, the
  real calls: a 127.0.0.1 listener and connect allowed; `getaddrinfo("example.com", 80)`,
  `create_connection(("example.com", 80))` (refused at its lookup), a connect to 192.0.2.1, a
  connect, bind and sendto by name, `urlopen("http://example.com")` and `webbrowser.open`
  (through a do-nothing browser registered first, so it is the same call on a machine with no
  browser) refused. In the Spark run, `test_spark_example_database.py`: `_serve` calls the
  trap before anything else (a stand-in trap stops it before stdin is read), and a `python -c`
  that loads engine.py by path and calls `_refuse_the_network()` refuses
  `getaddrinfo("example.com", 80)`. That the Example database still answers under the trap is
  shown by every query test in that file, which all pass with it in `_serve`.
- **ALLOWED** (each with a reason; the user's OK for them is still to be asked): the engine's
  `_refuse_the_network` wrapping `socket.socket.*` (not called); `tests/offline_trap.py`'s
  socket import and its backstop's wraps (not called); `tests/test_offline_trap.py`'s subprocess
  import and its `subprocess.run` of this same Python; `test_spark_example_database.py`'s
  `subprocess.run` of the engine-only child. `sys.addaudithook` and `ipaddress` aren't flagged.
- **Version.** TOOLBOX_VERSION untouched; the map's Notes hold the CHANGES line.

**Code review (2026-10-06).** Two reviews found:

- **A name given to `socket.connect`, `bind` or `sendto` was looked up before the trap saw it**
  (standards review, confirmed): CPython reads the address, resolving a name with no audit
  event, before it raises the method's event. Fixed test first: `_refuse_the_network()` now
  also wraps socket's connect, connect_ex, bind, sendto and sendmsg so the same rule judges the
  address first, and the backstop wraps them too; the real-call test connects, binds and sends
  by name. A `_socket.socket` used directly, skipping `socket.socket`, isn't wrapped (nothing
  here does that); its numeric addresses still meet the audit hook.
- **Smells fixed:** `_refuse_off_the_machine` has a docstring, `_as_text`/`_on_this_machine`
  type their host, `TRIED`/`NETWORK` are `TRIED_HOSTS`/`NETWORK_EVENT_MODULES`, and
  test_offline_trap.py no longer imports conftest for a path. `offline_trap`'s docstring now
  says the backstop stands in every run, and that loading engine.py a second time registers a
  stop at exit that finds nothing to stop.
- **Answered, not changed:** the loopback rule takes all of 127.0.0.0/8 and any case of
  localhost (all stay on this computer; `::ffff:127.0.0.1` and `127.1` are refused, failing
  closed). RuntimeError rather than an OSError subclass, so a library's offline fallback can't
  swallow a refusal unseen; nothing in the runs relied on one. The client libraries the child
  never uses stay in the rule, as the ticket asks for all of them. The Spark run's engine-only
  child repeats part of `install()` on purpose: it checks engine.py's trap in a Python that has
  nothing of the tests' but the backstop. The new ALLOWED entries need the user's OK (map
  Notes): asked of the user through the hand-back.
