# Plan: the Offline guard — audit report, and a guard that keeps network code out

## Context

The user asked for an audit of every line of this repo for anything malicious or anything that
can open an internet connection, together with the libraries it uses. The Toolbox is meant to
work offline: it builds Hive text and hands it to the user's own `send`, which is the one
outbound seam. The user asked for a report with the relevant code, a redesign that closes off
each risk, and a hook that reads all imported and written code to keep external communication
out.

**Audit done (read-only, 2026-10-06).** Three agents covered:
- the Toolbox, line by line;
- tools, tests, hooks, CI and the example code;
- the installed libraries: sqlglot 30.19.0, pandas 2.0.3, numpy 1.25.2, pyspark 4.0.4 and
  py4j 0.10.9.9.

I checked the key sites again myself.

**Verdict:** no malicious code, no webhooks, no telemetry, and no obfuscated or encoded content.
Nothing in the repo contacts the internet when it runs locally. What is left is a set of guarded
or by-design seams, plus library code that is present but never reached. Nothing yet stops a
future edit from adding network code.

**The user's choices (2026-10-06):**
- **The hook guards code only.** Claude's own shell commands are left alone (git push of dev,
  and curl to GitHub's public API to read CI).
- **The runtime trap** goes into every test run, and into Spark Composer's Example database
  child process. The user's own notebook Python is left alone, because `send` needs the
  network.

## The report (saved as `docs/offline-audit.md` in step 9)

| # | Where | Code | What it is | Risk |
|---|---|---|---|---|
| R1 | `composer_core/running.py:406-407` | `text = to_hive(s)` / `result = send(text)` | The only way out, by design: the user's `send` | By design |
| R2 | `spark_composer/engine.py:492-500` | `socket.create_server(("127.0.0.1", 0))`; `subprocess.Popen([_python(), "-B", engine.py], env=_environment(folder))` | The Example database's child process, which connects back on loopback and is checked with a 32-byte HMAC challenge (`_check_key`, 558-571) | Local only |
| R2 | `engine.py:851-873` | `spark.master local[1]`, `spark.ui.enabled false`, `driver.host/bindAddress 127.0.0.1`, `catalogImplementation in-memory`, `fs.defaultFS file:///`; no `spark.jars.packages` | Spark is held to loopback, and no Maven or Ivy download happens | Local only |
| R2 | `engine.py:299-304, 835-836` | `_NOT_PASSED_ON` strips `SPARK_REMOTE`, `SPARK_CONNECT_MODE*`, `PYSPARK_GATEWAY_*`, `HADOOP_CONF_DIR`; `SPARK_LOCAL_IP=127.0.0.1`; empty `SPARK_CONF_DIR` | Stops the child being turned into a Spark Connect or cluster client | Guarded |
| R2 | `engine.py:159, 933, 807-1029` | `java -XshowSettings:properties -version`; `taskkill /T /F /PID`; ctypes job objects | Process control | Local only |
| R3 | `pandas/io/common.py:263-270, 355-368` | `urllib.request.urlopen(req_info)` from any `read_*` given an http(s) or ftp string | Library network code. The Toolbox calls only `pd.DataFrame`, `itertuples`, `iloc` and `Timestamp` | Not reached |
| R3 | `numpy/lib/_datasource.py:327-337`; `pyspark/install.py:146`; `pyspark/sql/connect/client/` | `urlopen(path)`; Spark distribution download; Spark Connect gRPC client | Library network code | Not reached |
| R4 | `sqlglot/executor/python.py:95`, `context.py:46` | `compile(sql, sql, "eval")` / `eval(code, self.env)` | sqlglot's executor evaluates the Python it generates; string literals are escaped (`python.py:555`). This is code execution, not network | Low |
| R5 | `composer_core/lineage.py:817-873` | `Path(to)`, then `mkdir(parents=True)` and `write_text` | `export_lineage(to=...)` writes wherever the user points it, `..` included. A local write the user chose. Left as is | Low, local |
| R6 | `.github/workflows/dev.yml` | `actions/checkout@v4`, `setup-python@v5`, `setup-java@v4`; pip with exact versions and no hashes; no `permissions:` block | CI supply chain: an action tag can be moved | Low-medium |
| R7 | `.claude/hooks/drift_review.py` / `drift_list.py` | Prints changed file paths into Claude's context | A crafted file name could inject text into Claude's context | Low |
| R8 | `tools/example_gallery.py:262,267` | `exec`/`eval` of `>>>` examples | Only the repo's own docstrings | Low |
| — | Every `.html` page and lineage page | No `src=`, `<link>`, `url(`, `fetch`, XHR, WebSocket or external URL; `navigator.clipboard.writeText` for the Copy button only | Self-contained; three tests hold this already (`test_how_tos.py:223`, `test_example_gallery.py:207`, `test_lineage.py:827`) | None |

**Libraries load network modules themselves**, checked by running the import:
- `socket` comes from email.utils and pyarrow;
- `subprocess` comes from pandas' localization;
- `ctypes` comes from numpy and dateutil.

So a check on which modules are loaded can't tell the Toolbox from its libraries. The guard
reads the source instead, and adds a runtime trap where the process is the Toolbox's own.

## The redesign

### 1. One reader: `tools/offline_policy.py` (new)

A static scanner. It is the single source of the rules, and the hook, the tests and the export
all call it.
- **Python files: walk the AST**, collecting every `import` / `from ... import`, every call, and
  every string that isn't a docstring. Flag:
  - **network modules:** `socket`, `ssl`, `http.*`, `urllib.request`, `urllib3`, `requests`,
    `httpx`, `aiohttp`, `websocket(s)`, `ftplib`, `smtplib`, `poplib`, `imaplib`, `nntplib`,
    `telnetlib`, `xmlrpc`, `socketserver`, `webbrowser`, `grpc`, `paramiko`, `boto3`, `fsspec`,
    `multiprocessing.connection` / `.managers`, and `asyncio.open_connection` /
    `start_server`;
  - **process launchers:** `subprocess`, `os.system` / `popen` / `spawn*` / `exec*`, `pty`;
  - **dynamic code:** `eval`, `exec`, `compile`, `__import__`, and `importlib.import_module`
    with a name that isn't a literal;
  - **library fetchers:** `pd.read_*` / `pandas.read_*`, `np.loadtxt` / `genfromtxt` /
    `DataSource`, `pyspark.install`, `SparkSession.builder.remote`, and a
    `spark.jars.packages` / `spark.jars.repositories` / `spark.remote` config literal;
  - **URLs in code strings:** `http(s)://`, `ftp://` and `ws(s)://`.
- **`.html` / `.js` files: flag** `src=`, `<link`, `@import`, `url(`, `fetch(`,
  `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `EventSource`, `<iframe`, and `http(s)://`. This
  is the one shared form of the three existing page tests' lists, which then call it.
- **Scopes,** strictest first:
  - **The Toolbox** (`composer_core/`, both Editions): nothing from the network or launcher
    groups, apart from allowlisted sites.
  - **`templates/`, `example_projects/`, `worked_examples/`:** nothing at all, because users
    copy these files.
  - **`tools/`, `tests/`, `.claude/hooks/`:** process launchers and loopback sockets only at
    allowlisted sites; no network client modules.
- **The allowlist** is `ALLOWED` in the same file. Each entry gives the file, the enclosing
  function, the kind and a reason. Every R2 site is in it.
  - The socket entry also requires the literal address `"127.0.0.1"`.
  - The tools and tests entries cover their git, python, node and powershell subprocesses, the
    tests' loopback socket, and example_gallery's exec/eval.
  - An entry that matches nothing fails, so the list can't go stale.
- **The command line:** `python tools/offline_policy.py [paths...]` prints findings as
  `file:line kind: code` and exits 1. Run with no paths, it scans the repo.

### 2. The hook: `.claude/hooks/offline_guard.py` (new), PreToolUse

- It runs on `Edit|Write|NotebookEdit`, as a second entry in `.claude/settings.json`.
- It works out the file as the edit would leave it:
  - for Write, the `content`;
  - for Edit, the file on disk with `old_string` → `new_string` (or `replace_all`);
  - for NotebookEdit, the new cell's source.
- It runs `offline_policy` on that text under the file's repo path. It denies with
  `permissionDecisionReason` listing each finding and the way through: "a reviewed entry in
  `tools/offline_policy.py`'s `ALLOWED`, with the user's OK". The deny JSON follows
  `protect_main.py`'s.
- It only reads the text. It never runs the code, and it makes no network call.
- **Known gap:** writing a file from Bash gets past a PreToolUse file hook. The pytest test
  (step 3) and the export check (step 6) catch that.

### 3. The tests: `tests/repo/test_offline_policy.py` (new), written red first with the `tdd` skill

- The whole repo scans clean.
- Each forbidden form is caught in a fixture string, including the disguised forms:
  - `import requests`;
  - `from urllib.request import urlopen`;
  - `socket.create_connection(("example.com", 80))`;
  - `__import__("soc" + "ket")`;
  - `importlib.import_module(name)`;
  - `pd.read_csv(path)`;
  - `eval(x)`;
  - `"https://x"` in code;
  - `<script src="https://...">`;
  - `fetch(`.
- An allowlisted socket whose address isn't `127.0.0.1` is refused.
- A stale allowlist entry fails.
- **The hook, run as a hook** (as `test_protect_main_refuses_a_commit_on_main_when_run_as_a_hook`
  does): a Write adding `import requests` to `composer_core/x.py` is denied, a clean Write gets
  no output, and an Edit is judged on its result.
- The three page tests switch to `offline_policy`'s HTML check.

### 4. The runtime trap in every test run: `tests/offline_trap.py` (new)

- `tests/conftest.py` installs it at import, in both Editions' runs.
- It is a `sys.addaudithook` that raises on:
  - `socket.connect` / `sendto` / `bind` to anything but `127.0.0.1`, `::1` or `localhost`;
  - `socket.getaddrinfo` / `gethostbyname` for any other host;
  - `urllib.Request`, `http.client.connect`, `webbrowser.open`, `ftplib.connect` and
    `smtplib.connect`.
- Test: it refuses `socket.getaddrinfo("example.com", 80)` and allows `127.0.0.1`.

### 5. The runtime trap in Spark Composer's child: `spark_composer/engine.py`

- `_serve` (line 1128) installs the same audit hook before it imports pyspark, as a new
  `_refuse_the_network()`.
- It allows the 127.0.0.1 connect-back and py4j's loopback gateway. The JVM isn't Python and
  can't be audited from here; the existing `_settings` / `_environment` already pin it to
  loopback.
- The spark run gets a test: in a `python -c` child, `_refuse_the_network()` then
  `getaddrinfo("example.com", 80)` is refused, and the Example database still answers.
- **This changes the shipped engine**, so the drift reviewer will open a version item. Per
  CLAUDE.md, I ask the user then (4.0.1 or 4.1); I don't raise it myself.

### 6. The export refuses network code: `tools/export_clean.py`

- It runs `offline_policy` over the Clean tree it built: Toolbox, copied projects, templates,
  pages and README.
- It refuses to commit `main` on any finding, beside its other checks.
- Test in `tests/repo/test_export_clean.py`: a template spoiled with `import requests` is
  refused.

### 7. CI hardening: `.github/workflows/dev.yml`

- Add `permissions: contents: read`.
- Pin `actions/checkout`, `actions/setup-python` and `actions/setup-java` to full commit SHAs,
  with the tag in a comment. The SHAs are read from GitHub's public API.
- pip hashes (`--require-hashes`) need a hashed lock file. The report lists this as a follow-up;
  it isn't done here.

### 8. Drift hook context: `.claude/hooks/drift_list.py`

- Before file paths are printed into `additionalContext`, strip control characters and
  newlines and cap the length. Test in `tests/repo/test_hooks.py`.

### 9. Records

- **`docs/offline-audit.md`:** the report above, with its code quotes.
- **ADR 0004, "The Toolbox reaches nothing but send":**
  - the policy;
  - the allowlist as the review point;
  - the Example database on loopback only;
  - why no trap goes into the user's Python.
- **`docs/agents/standards.md`:** a new allowlist entry needs a reason and the user's OK.
- **CLAUDE.md:** a short "Offline" section naming the hook, `tools/offline_policy.py` and the
  test.
- **Tracker:** the work is tracked as `.scratch/offline-guard/` (map plus issues), per the repo's
  convention. Each ticket follows CLAUDE.md's Definition of done.

## Order (parallel where the files don't overlap)

1. **First:** `offline_policy.py` and its tests (steps 1 and 3, without the hook), because the
   other steps use it.
2. **Then in parallel:**
   - (a) the hook (step 2);
   - (b) the runtime traps (steps 4 and 5);
   - (c) the export check, CI and the drift-hook fix (steps 6, 7 and 8).
3. **Last:** the records (step 9).

## Verification

- `python tools/offline_policy.py` exits 0 on the repo, and exits 1 with `file:line` findings on
  a scratch file holding `import requests`.
- **The hook, by hand:** pipe a Write JSON with `import socket; socket.create_connection(...)`
  into `python .claude/hooks/offline_guard.py` and see the deny. A clean one prints nothing.
- **The hook live:** an Edit that adds `import requests` to `composer_core/running.py` is denied
  in-session.
- `python -m pytest`, `python -m pytest --edition spark` (Java 17) and the low-sqlglot venv all
  pass, with the audit trap active in each. Any non-loopback lookup during the suite would fail
  it.
- `python tools/export_clean.py --preview <tmp>` passes. Spoiled with `import requests`, it
  refuses.
- CI's four jobs pass with the SHA-pinned actions and `contents: read`.
- The drift reviews come back clean, or their items are fixed. The version item from step 5 goes
  to the user.
