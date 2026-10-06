# Offline audit

On 2026-10-06 the user asked for every line of the repo, and of the libraries it uses, to be read
for malicious code and for anything that can open an internet connection; for a report with the
code; and for a redesign that closes each risk, with a hook that keeps network code out. This is
that report, as the code stood after the redesign (Toolbox 4.1, 2026-10-06): its line numbers
and counts are a snapshot of that day, and a later change may move them. The plan it was
built from, and its tickets, are in `.scratch/offline-guard/`.

Read: the Composer core, both Editions, `tools/`, `tests/`, `.claude/hooks/`, the CI workflow,
the Worked examples, Example projects and Templates, every page, and the installed libraries:
sqlglot 30.19.0, pandas 2.0.3, numpy 1.25.2, pyspark 4.0.4 and py4j 0.10.9.9, the pins in
`requirements-dev.txt`. The bottoms of the Editions' ranges, which CI also runs (sqlglot 25.24.2
and pyspark 3.5.0), weren't read; the tests run them under the same trap.

## The verdict

- **No malicious code**, no webhooks, no telemetry, and nothing obfuscated or encoded.
- **Nothing reaches the internet.** Nothing in the repo contacts another computer when it runs.
- **The one way out is the user's `send`**, by design: the Toolbox builds Hive text and hands it
  to the user's own function, which sends it to their warehouse.
- What was left before the redesign was a set of local or by-design seams (R1-R8 below), library
  code the Toolbox never reaches, and nothing to stop a future edit adding network code. Each is
  now closed or held, or left open on purpose and said so.

## How to check it yourself

- `python tools/offline_policy.py` reads the whole repo and exits 0 when it is clean. Given
  paths, it reads only those. Each finding prints as `file:line kind: code`, and it exits 1.
- `python -m pytest` and `python -m pytest --edition spark` run every test under the runtime
  trap, so a test that reached another computer would fail. `tests/repo/test_offline_policy.py`
  holds what the reader finds, `tests/repo/test_offline_hook.py` what the hook refuses, and
  `tests/test_offline_trap.py` what the trap refuses.
- `python tools/export_clean.py --preview <folder>` builds the Clean tree and reads every part
  of it before anything in it is imported or run.

## What keeps the repo offline

| Part | Where | What it does |
|---|---|---|
| The reader | `tools/offline_policy.py` | Reads Python by its syntax tree, and pages by their references, for network modules, process launchers, dynamic code, library fetchers and URLs. Holds `ALLOWED`, the reviewed sites. The hook, the tests and the export all call it. |
| The edit hook | `.claude/hooks/offline_hook.py` | Before an Edit, Write or NotebookEdit lands, judges the file as the edit would leave it, and refuses one that adds a finding. |
| The repo test | `tests/repo/test_offline_policy.py` | `test_the_repo_reads_clean` (line 26): the repo has no finding and no stale `ALLOWED` entry. |
| The runtime trap | `spark_composer/engine.py` `_refuse_the_network`, installed by `tests/offline_trap.py` | An audit hook (PEP 578) that raises RuntimeError on a lookup, connection, bind or message off this computer, or any client library. Runs in every test run and in the Example database's own Spark process. |
| The export check | `tools/export_clean.py` `check_offline` | Reads each part of the Clean tree before it is imported or run, and refuses to commit `main` on any finding. |
| CI | `.github/workflows/dev.yml` | Read-only token, and each action pinned to a commit SHA. |

### What the reader allows, by folder

`tools/offline_policy.py:43-53`, strictest first:

- **The Templates, Example projects and Worked examples** (`templates/`, `example_projects/`,
  `worked_examples/`): nothing at all, since users copy these files into their own work.
  `ALLOWED` doesn't apply there, and an entry naming one is reported as stale.
- **The Toolbox** (`composer_core/` and both Editions' folders): nothing, apart from the sites
  `ALLOWED` lists. Only Spark Composer's `engine.py` has any.
- **Everything else** (`tools/`, `tests/`, `.claude/hooks/`): the same, apart from URLs and
  Spark settings in strings, which tests hold as text to check pages against.

`ALLOWED` (`tools/offline_policy.py:211-404`) holds 89 entries, each with its file, function,
kind, name and reason: 17 for Spark Composer's engine, 3 for the drift hooks, 14 for tools and 55
for tests. Every entry is a local site: git on a local repository, this same Python, ruff,
node on the pages' own scripts, powershell listing this computer's processes, Java, taskkill
and kernel32 on the Example database's own processes and folder, a socket on 127.0.0.1, or
the gallery's and tests' own code. An entry that matches nothing fails the repo test, so the
list can't go stale. A new entry needs a reason and the user's OK (`docs/agents/standards.md`).

## The risks, one by one

### R1. The user's `send`: the one way out (by design)

`composer_core/running.py:406-407`, in `run(s, send)`:

```python
text = to_hive(s)
result = send(text)
```

- **What it is.** `send` is the user's own function from a Hive string to a DataFrame. At work
  it calls the query API, or `spark.sql(hive).toPandas()`; `example_database.send` runs the
  Example database instead, on this computer.
- **Risk.** By design. What `send` reaches is the user's choice, not the Toolbox's.
- **What holds it.** `running.py` is Toolbox code, so the reader refuses any network code in it
  and `ALLOWED` has no entry for it: the Toolbox can call `send`, and nothing else. No runtime
  trap goes into the user's own Python, since `send` needs the network there (ADR 0004).

### R2. Spark Composer's Example database (local only)

The Example database's Spark runs in a second Python, started from `spark_composer/engine.py`,
which connects back to the user's Python on loopback.

```python
key = os.urandom(32)                                                    # engine.py:493
_SPARK["listener"] = listener = socket.create_server(("127.0.0.1", 0))  # engine.py:494
_SPARK["process"] = process = subprocess.Popen(                          # engine.py:498-499
    [_python(), "-B", str(Path(__file__).resolve())], cwd=folder,
    env=_environment(folder), ...
```

- **The connection.** `_check_key` (`engine.py:559-572`) runs multiprocessing's
  `deliver_challenge` and `answer_challenge` with that 32-byte key, so only the process holding
  it is kept. The process connects back with `Client(tuple(config["address"]), authkey=...)`
  (`engine.py:1147`), to the address its parent sent on stdin.
- **The Spark.** `_settings` (`engine.py:852-874`) holds it to this computer:
  `"spark.master": "local[1]"`, `"spark.ui.enabled": "false"`,
  `"spark.driver.host": "127.0.0.1"`, `"spark.driver.bindAddress": "127.0.0.1"`,
  `"spark.sql.catalogImplementation": "in-memory"`, `"spark.hadoop.fs.defaultFS": "file:///"`.
  There is no `spark.jars.packages`, so no Maven or Ivy download.
- **The environment.** `_NOT_PASSED_ON` (`engine.py:300-305`) leaves out `SPARK_REMOTE`,
  `SPARK_CONNECT_MODE`, `SPARK_CONNECT_MODE_ENABLED`, `SPARK_API_MODE`, `PYSPARK_GATEWAY_PORT`,
  `PYSPARK_GATEWAY_SECRET`, `HADOOP_CONF_DIR` and the rest, so a kernel's settings can't make the
  process a Spark Connect or cluster client. `_environment` (`engine.py:836`) sets
  `SPARK_CONF_DIR` to an empty folder of its own and `SPARK_LOCAL_IP="127.0.0.1"`.
- **Process control.** `_ask_java` runs `java -XX:-UsePerfData -XshowSettings:properties
  -version` (`engine.py:160-161`); `_kill_everything_started_by` runs `taskkill /T /F /PID` where
  Windows gave no job (`engine.py:934`); `_kernel32`, `_job_limits` and `_job_holding`
  (`engine.py:964-1021`) hold the processes in a Windows job through ctypes, so they end with the
  user's Python.
- **Risk.** Local only.
- **What holds it.**
  - Each site is an `ALLOWED` entry (`tools/offline_policy.py:212-245`). The listener's entry
    holds its address to `"127.0.0.1"`, and the connect-back's and the key check's to a host
    passed in, so the same calls given any other host written out are refused.
  - The process's first step is `_refuse_the_network()` (`engine.py:1142`), before it reads
    stdin or imports pyspark or py4j. It adds an audit hook and wraps socket's `connect`,
    `connect_ex`, `bind`, `sendto` and `sendmsg` (`engine.py:1279-1297`), since Python looks up a
    name given to them before it raises their event. What it lets through is decided by
    `_off_the_machine` (`engine.py:1321-1346`): only localhost, a loopback address, a Unix
    socket's path, or a lookup of no name. A bind to every interface is refused, and so is
    every client library (urllib, webbrowser, http.client, ftplib, smtplib, poplib, imaplib,
    nntplib, telnetlib). What is refused raises `RuntimeError("... was refused: this Python
    reaches nothing off this computer, only 127.0.0.1, ::1 and localhost.")`
    (`engine.py:1317-1318`), in the process's log.

### R3. Network code in the libraries (not reached)

pandas, numpy and pyspark hold code that downloads or connects, reached only through calls the
Toolbox never makes. See [Third-party libraries](#third-party-libraries) for each one.

- **Risk.** Not reached.
- **What holds it.** The reader refuses those calls by name in any file it reads: any
  pandas `read_*`, numpy's `loadtxt`, `genfromtxt` and `DataSource`, `pyspark.install`,
  `pyspark.sql.connect` and a `.remote(...)` on a builder; and, in the Toolbox and the files
  users copy, the settings `spark.jars.packages`, `spark.jars.repositories` and `spark.remote`
  in a string. The runtime trap catches what is reached anyway, in the tests and the Example
  database's process.

### R4. sqlglot's executor evaluates the Python it generates (low)

```python
return compile(sql, sql, "eval", optimize=2)   # sqlglot/executor/python.py:95
return eval(code, self.env)                    # sqlglot/executor/context.py:46
```

- **What it is.** sqlglot Composer's Example database runs a Statement's Hive on sqlglot's
  executor (`sqlglot_composer/engine.py:395`), which turns each expression into Python and
  evaluates it over the made-up tables. String literals are escaped as they are written
  (`STRING_ESCAPES = ["\\"]`, `sqlglot/executor/python.py:555`).
- **Risk.** Low. It is code execution of text the Toolbox itself wrote, not network, and only
  on the Example database.
- **What holds it.** Nothing new: library code isn't read by the reader. The tests run it under
  the runtime trap.

### R5. `export_lineage(to=...)` writes where the user points it (low, local)

```python
path = Path(to)                                              # composer_core/lineage.py:819
html_path.parent.mkdir(parents=True, exist_ok=True)          # lineage.py:873
markdown_path.write_text(markdown, encoding="utf-8")         # lineage.py:874
html_path.write_text(page, encoding="utf-8")                 # lineage.py:875
```

- **What it is.** `to=` names the HTML file, `..` included; the folder is made if it is missing.
- **Risk.** Low, and local: a write the user chose, on their own disk.
- **Left as is.** The page it writes is self-contained (see Pages, below).

### R6. CI's supply chain (low-medium, now pinned)

- **What it was.** `.github/workflows/dev.yml` used `actions/checkout@v4`, `setup-python@v5` and
  `setup-java@v4` by tag, which the action's owner can move, and had no `permissions:` block.
- **What closes it.** The jobs may only read the repo, and each action is pinned to a full
  commit SHA, its tag in a comment:

  ```yaml
  # dev.yml:18-19
  permissions:
    contents: read
  # dev.yml:30 and 46, 31 and 47, 50
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
  - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
  - uses: actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3 # v4
  ```

- **Left open.** pip installs exact versions (`requirements-dev.txt`) but not by hash; see
  [Left open on purpose](#left-open-on-purpose).

### R7. The drift hook prints file paths into Claude's context (low)

- **What it was.** `.claude/hooks/drift_review.py` names the files a commit touched in the text
  it gives the session, so a crafted file name could carry an instruction.
- **What closes it.** Each path goes in as one plain line, at most 120 characters, and at most 20
  of them. `plain_line` turns control characters, Unicode line and paragraph separators and
  direction marks into a space. The edit hook prints its findings as plain lines too.

  ```python
  # .claude/hooks/drift_review.py:37
  shown = ", ".join(plain_line(path, LONGEST_PATH) for path in paths[:MOST_PATHS])
  # .claude/hooks/hook_io.py:23
  shown = UNPRINTABLE.sub(" ", text).strip()
  ```

### R8. The Example gallery runs its examples (low)

```python
exec(compile(source, "<example>", "exec"), scope)        # tools/example_gallery.py:262
return eval(compile(tree, "<example>", "eval"), scope)   # tools/example_gallery.py:267
```

- **What it is.** `run_step` runs each `>>>` example of the Toolbox's own docstrings, as a
  doctest would, to build the gallery.
- **Risk.** Low: it runs only the repo's own docstrings, and the reader reads those examples as
  code, so a docstring example can't hold network code either.
- **What holds it.** Its `compile`, `exec` and `eval` are `ALLOWED` entries; any other is refused.

### Pages (none)

Every `.html` page, the Example galleries, the how-to pages and each lineage page, is
self-contained: no `src=`, `<link>`, `url(`, `fetch`, XMLHttpRequest, WebSocket or external URL.
The one browser call that reaches outside the page is `navigator.clipboard.writeText`, for the
how-to page's Copy button (`tools/how_to_page.py:648`). The reader's `external_references`
(`tools/offline_policy.py:434`) is the one list of what a page may not hold; the page tests call it
(`tests/test_how_tos.py:224`, `tests/test_example_gallery.py:208`, `tests/test_lineage.py:827`),
and the export reads the Clean tree's Markdown with it too (`page_findings`, line 439).

## Third-party libraries

None of this network code is reached by the Toolbox. Each library also loads network modules on
its own when imported: `socket` comes in through `email.utils` and pyarrow, `subprocess` through
pandas' localization, `ctypes` through numpy and dateutil. So a check on which modules are loaded
can't tell the Toolbox from its libraries; the reader reads the source instead.

- **sqlglot.** No network code. Its executor evaluates the Python it generates (R4).
- **pandas.** `pandas/io/common.py:263-270` wraps `urllib.request.urlopen`, and lines 356-368
  open any http(s) or ftp string given to a `read_*` function:
  `req_info = urllib.request.Request(filepath_or_buffer, headers=storage_options)` then
  `with urlopen(req_info) as req:`. The Toolbox makes DataFrames, uses `pd.Timestamp`,
  `pd.NA` and `pd.NaT`, and reads the DataFrames `send` returns (their columns, rows and
  length). It calls no `read_*` and reads no file through pandas.
- **numpy.** `numpy/lib/_datasource.py:327-337` opens a URL path with
  `with urlopen(path) as openedurl:`, reached through `DataSource`, `loadtxt` and `genfromtxt`.
  The Toolbox uses numpy only to recognise its number and date types
  (`composer_core/tables.py:235`, `423-425`).
- **pyspark.** `pyspark/install.py:146` downloads a Spark distribution
  (`download_to_file(urllib.request.urlopen(url), package_local_path)`), reached only when Spark
  is installed by calling `install_spark` (`install.py:108`). The Spark Connect client,
  `pyspark/sql/connect/client/`, talks gRPC (`import grpc`, `core.py:60`) to a remote Spark,
  reached through `SparkSession.builder.remote(url)` (`pyspark/sql/session.py:365-385`),
  `spark.remote` or `SPARK_REMOTE`. Spark Composer uses neither: its Example database's builder
  takes only the settings in R2, and `SPARK_REMOTE` and the Connect switches are left out of its
  process's environment.
- **py4j.** The bridge from pyspark to its Java. It connects to the gateway pyspark starts, at
  `DEFAULT_ADDRESS = "127.0.0.1"` (`py4j/java_gateway.py:54`; connects at `java_gateway.py:1170`
  and `clientserver.py:438`). In the Example database's process the runtime trap holds it there.

## Left open on purpose

- **pip hashes.** CI installs exact versions, but `--require-hashes` needs a lock file with every
  package's hash. A follow-up, not done.
- **`export_lineage(to=...)`** writes wherever the user points it (R5): a local write the user
  chose.
- **What the reader can't follow** (`tools/offline_policy.py:29-31`): a module kept in a variable
  (`m = os`), a name imported as two modules (the last is read), and a method on an object it
  can't name, such as an asyncio loop's `create_connection`. The runtime trap still catches any of
  them run in the tests or the Example database's process.
- **A file written from a shell command** gets past the edit hook, which sees only Edit, Write
  and NotebookEdit (and not MultiEdit, as `protect_main.py`'s matcher doesn't either). The repo
  test and the export read it anyway.
- **When the edit hook can't judge an edit** (its policy won't load, or the file can't be read),
  it refuses in the Toolbox and the files users copy, and lets the edit through elsewhere,
  saying so, so a broken policy never refuses the edit that fixes it.
- **A notebook's code cells are read as one text**, so a cell that doesn't parse hides the
  others; in the Toolbox and the files users copy, that refuses the edit.
- **`.scratch/` isn't read**: it holds the tracker's notes and reports, which nothing runs. One
  report opened by hand loads its styles and charts from CDNs.
- **Claude's own shell commands** aren't read: the user chose to hold code only, so
  `git push` of dev and reading CI through GitHub's public API stay as they are.
- **Spark's Java** can't be watched from Python. Its settings and environment hold it to
  127.0.0.1 (R2); the trap holds the Python side.
- **A raw `_socket.socket`**, used directly instead of `socket.socket`, isn't wrapped by the
  trap; nothing here uses one, and its numeric addresses still meet the audit hook.
- **A Python a test starts** (with subprocess) doesn't carry the tests' trap, apart from the
  Example database's process, which installs its own. Nor do Python workers the Spark Java starts
  for Python UDFs, which the Example database doesn't use.
- **The user's own Python** carries no trap, since `send` needs the network (ADR 0004).
