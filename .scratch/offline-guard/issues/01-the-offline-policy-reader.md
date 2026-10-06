# The offline policy reader

Type: task
Status: resolved
Blocked by: nothing
Size: M

## Question

Plan steps 1 and 3 (without the hook test): `tools/offline_policy.py`, the AST and page scanner with its scopes and `ALLOWED` allowlist, its command line, and `tests/repo/test_offline_policy.py`; the three page tests call its HTML check.

## Done when

- The repo scans clean; every forbidden form in plan step 3 is caught; an allowlisted socket off 127.0.0.1 and a stale entry fail.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in 1fea21b, fixed up after its code review in the commit that resolves this ticket.

- **The reader.** `tools/offline_policy.py`, standard library only (it imports `editions` for
  the Toolbox's folder names). Python is read by its syntax tree, never imported or run:
  imports (aliases and `from` forms; relative imports name the file's own folder and are never
  flagged), every name and call, followed through aliases, getattr, `vars()`, `__dict__`,
  `sys.modules`, `__builtins__` and `importlib.import_module` with names written out, and
  strings added up (`"soc" + "ket"`). Kinds: **network**; **process** (subprocess,
  os.system/popen/spawn*/exec*, pty, ctypes, multiprocessing); **dynamic code** (eval, exec,
  compile, `__import__`, runpy, and import_module, getattr or a module's namespace looked up
  with a name not written out, or a star import from a module the repo doesn't write);
  **library fetcher** (pandas `read_*` at any module path, numpy loadtxt/genfromtxt/
  DataSource, pyspark.install, a `.remote(...)` on a builder or in a file importing pyspark,
  and the three Spark settings in a string); **URL**. A docstring, or any string standing as
  its own statement, is prose: only its `>>>` examples are read, as code, at their own lines.
  An annotation or an except clause's type is read for the calls in it, since Python runs
  them. A file that doesn't parse is a finding ("unreadable"); a template's `<TABLE>`
  placeholders are read as names, so the templates parse unfilled. A notebook's code cells
  are read too, a `!` or `%` line as a process.
- **Pages.** `external_references(text) -> list[str]` (as "line N: what") flags `src=`,
  `<link`, `@import`, `url(` (not `parse_url(`), `fetch(`, XMLHttpRequest, WebSocket,
  sendBeacon, EventSource, `<iframe`, `<object`, `<embed`, `import(` and any http(s)/ftp/ws(s)
  URL. The how-to, gallery and lineage page tests call it in place of their own lists.
- **Scopes.** By the path's top folder, the same on `dev` and `main`: user-copied code
  (`templates/`, `example_projects/`, `worked_examples/`) may hold nothing, and no ALLOWED
  entry applies there (one naming it is reported); the Toolbox and everything else (tools,
  tests, hooks, any root file) only the ALLOWED sites. Decided here: maintainer code isn't
  read for URLs or Spark settings in strings, since tests hold them as text to check pages
  against (`assert "https://" not in page`) and a string reaches nothing without a client,
  which is still refused there. `.scratch/` isn't read: it is the tracker's notes, and
  `.scratch/architecture-review/report.html` loads Tailwind and Mermaid from CDNs (a report
  opened by hand, not code anything runs). The walk skips `.git`, `.claude/worktrees`,
  `__pycache__`, tool caches and any folder holding `pyvenv.cfg`; it doesn't ask git what is
  ignored, which would itself be a process.
- **ALLOWED.** 81 entries, each (file, function or "<module>", kind, name, reason): 16 for
  Spark Composer's engine (R2) and 65 for tools, tests and the drift hook, each site reviewed
  (git on local repos, this same Python, node, ruff, powershell Get-CimInstance, the tests'
  exec of their own strings, the gallery's exec/eval of docstring examples, imports of the
  repo's own modules by name). A name ending ".*" covers all in a module (ctypes,
  multiprocessing.connection). A network entry with an address holds a call to that host:
  `_launch`'s `socket.create_server` and the stray-connection test's `create_connection` to
  "127.0.0.1", `_serve`'s and `_check_key`'s multiprocessing calls to a host passed in, so
  `Client(("example.com", 80))` there is refused, and so is a network function named without
  being called. The stray-connection test now writes `("127.0.0.1", port)` so its address can
  be read. Nothing was refused: every site was local.
- **For the hook and the export.** `findings_in(text, path, allowed=ALLOWED) ->
  list[Finding]` judges one file's text under its repo path; `scan(root=ROOT, paths=None,
  allowed=ALLOWED) -> list[Finding]` reads a tree, such as the Clean tree; `stale_entries(root,
  allowed)` reports entries that match nothing. A `Finding` prints as `file:line kind: code`.
  `python tools/offline_policy.py [paths...]` prints each and exits 1; with no paths it reads
  the repo and its stale entries.
- **The tests.** `tests/repo/test_offline_policy.py`: the repo reads clean with no stale
  entry; each plan form and 21 disguised ones are found under a Toolbox path; prose URLs and
  the Toolbox's own imports aren't; pages; scopes; the engine's socket off 127.0.0.1, and its
  child's Client to a written-out host, refused; a stale entry; the command line. Each rule
  was also checked red by breaking it.

**Code review (2026-10-06).** Two reviews found:

- **Bypasses** (both reviews): annotations and except types were skipped though Python runs
  them; getattr with a written-out name, `__builtins__`, `vars()`/`__dict__`/`sys.modules`
  lookups, `import_module("os").system`, `"soc" + "ket"`, star imports,
  `builder.appName(...).remote(...)`, `pd.io.parsers.read_csv`, `np.lib.npyio.loadtxt`, a
  `ctypes.CDLL` call taken for a constant, and multiprocessing/ProcessPoolExecutor. All fixed
  test first. `from http import HTTPStatus` is no longer a finding (http.client, http.server
  and http.cookiejar are).
- **`_serve`'s and `_check_key`'s entries allowed any host**: they now hold the host to one
  passed in (above).
- **Smells fixed:** the URL pattern is shared by strings and pages, the notebook's magic lines
  are worked out once, `stale_entries` reads each file once, and `_Reader` sets its fields
  one per line.
- **Not done:** a module kept in a variable, a name imported as two modules, and methods on
  objects it can't name (an asyncio loop) aren't followed; the module docstring says so. The
  maintainer scope's unread strings (above) were kept, as decided. One entry per test file
  instead of per function was not taken: the ticket asks for one per site, and a renamed test
  fails the scan with a stale entry. "user-copied code" and "maintainer code" are dev-only
  words, left for ticket 05 to add to CONTEXT.md if wanted.
