"""The offline policy: read the repo's code for anything that could reach the network.

The Toolbox works offline. It builds Hive text and hands it to the user's own `send`, the one way
out, and nothing else in the repo opens a connection. This is the one reader of that rule: the
hook, the tests and the export all call it, and it holds the allowlist, `ALLOWED`. It only reads
text. It never imports or runs the code it reads.

What it looks for, in a Python file, by walking its syntax tree:

- **network:** importing or using a network module (`socket`, `urllib.request`, `requests` and
  the rest of `NETWORK_MODULES`), or `asyncio.open_connection` / `start_server`;
- **process:** starting a process or calling native code: `subprocess`, `os.system`,
  `os.popen`, `os.spawn*`, `os.exec*`, `pty`, `ctypes`, `multiprocessing`;
- **dynamic code:** `eval`, `exec`, `compile`, `__import__`, and `importlib.import_module`,
  `getattr`, `vars(module)[...]` or `module.__dict__[...]` on a module with a name that isn't
  written out, or `from module import *`, which could reach any of the above unseen;
- **library fetcher:** a library function that downloads when given a URL or told to:
  `pd.read_*`, `np.loadtxt` / `genfromtxt` / `DataSource`, `pyspark.install`,
  `SparkSession.builder.remote`, and the Spark settings `spark.jars.packages`,
  `spark.jars.repositories` and `spark.remote` written in a string;
- **URL:** `http(s)://`, `ftp://` or `ws(s)://` in a string the code uses. A docstring, or any
  string that stands as a statement of its own, is prose, so only the `>>>` examples in it are
  read, as code.

A name is followed however it is reached: through an alias (`import socket as s`), from an
import (`from socket import create_connection`), through getattr, `vars()`, `__dict__`,
`sys.modules` or `__builtins__` with a name written out, through `importlib.import_module` with
a module written out, and through strings added up (`"soc" + "ket"`). The calls in an
annotation or an except clause's type are read, since Python runs them. What it can't follow:
a module kept in a variable (`m = os`), a name imported as two modules (the last is read), and
a method on an object it can't name, such as an asyncio loop's `create_connection`.

A notebook's code cells are read as one Python file, and a `!` or `%` line in one, which runs
a shell command or an IPython magic, is a process. A Python file that doesn't parse can't be
read, and says so ("unreadable"); a template's placeholders, such as `<TABLE>`, are read as
names, so it parses before it is filled in.

In a page (`.html`, `.js`), it looks for anything that loads or sends something outside the
page: `external_references`.

What is allowed depends on the folder, strictest first:

- **user-copied code** (`templates/`, `example_projects/`, `worked_examples/`): nothing at all,
  since users copy these files into their own work;
- **the Toolbox** (`composer_core/` and both Editions' folders): nothing, apart from the sites
  `ALLOWED` lists;
- **everything else** (`tools/`, `tests/`, `.claude/hooks/`): the same, apart from URLs and
  Spark settings in strings, which tests and tools hold as text to check pages against.

The tracker, `.scratch/`, holds notes and reports, not code, and isn't read.

Run it to read the repo, or the files and folders named:

    python tools/offline_policy.py [paths...]

It prints each finding as `file:line kind: code` and exits 1 if there is any. Read whole, the
repo also reports any `ALLOWED` entry that no longer matches anything, so the list can't go
stale.
"""

from __future__ import annotations

import ast
import builtins
import doctest
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import editions

ROOT = Path(__file__).resolve().parent.parent

# --- The rules ----------------------------------------------------------------------------------

NETWORK_MODULES = (
    "socket", "_socket", "ssl", "_ssl", "http.client", "http.server", "http.cookiejar",
    "urllib.request", "urllib3", "requests",
    "httpx", "aiohttp", "websocket", "websockets", "ftplib", "smtplib", "poplib", "imaplib",
    "nntplib", "telnetlib", "xmlrpc", "socketserver", "webbrowser", "grpc", "paramiko",
    "boto3", "botocore", "fsspec", "multiprocessing.connection", "multiprocessing.managers",
    "pyspark.sql.connect",
)
NETWORK_FUNCTIONS = ("asyncio.open_connection", "asyncio.start_server")
# multiprocessing's connection and managers are network modules (above); the rest of it
# starts processes.
PROCESS_MODULES = ("subprocess", "_posixsubprocess", "_winapi", "pty", "ctypes", "_ctypes",
                   "multiprocessing", "concurrent.futures.process",
                   "concurrent.futures.ProcessPoolExecutor")
# The functions of os (and of posix and nt, which os takes them from) that start a process or
# hand a path to the system to open, which may be a URL.
PROCESS_FUNCTIONS = ("system", "popen", "startfile", "fork", "forkpty")
PROCESS_PREFIXES = ("spawn", "exec", "posix_spawn")
PROCESS_FUNCTION_MODULES = ("os", "posix", "nt")
PROCESS_ASYNCIO = ("asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell")
DYNAMIC_FUNCTIONS = ("eval", "exec", "compile", "__import__", "importlib.__import__")
# The calls that import a module by its name, given as a string.
IMPORTERS = ("importlib.import_module", "__import__", "importlib.__import__")
# runpy runs a module or a file by its name.
DYNAMIC_MODULES = ("runpy",)
FETCHER_MODULES = ("pyspark.install", "numpy.lib._datasource")
# numpy's functions that read a URL, wherever in numpy they are reached from.
NUMPY_FETCHERS = ("loadtxt", "genfromtxt", "DataSource")
# What a network finding gives as its address when no host is written out: a call given its
# host in a variable, or a network function named but not called, which could be called with
# any host.
PASSED_IN = "<passed in>"
NOT_CALLED = "<not called>"
# A string that names a URL, or a Spark setting that downloads or connects elsewhere.
URL_START = r"\b(?:https?|ftp|wss?)://"
URL = re.compile(URL_START, re.IGNORECASE)
SPARK_SETTING = re.compile(r"\bspark\.(?:jars\.packages|jars\.repositories|remote)\b")
# What a page may not hold: anything that loads or sends something outside the page.
PAGE_REFERENCE = re.compile(
    r"\bsrc\s*=|<link\b|@import\b|\burl\s*\(|\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon"
    r"|EventSource|<iframe\b|<object\b|<embed\b|\bimport\(|" + URL_START,
    re.IGNORECASE,
)
# The names Python has without an import, such as eval; any other name not imported is the
# file's own.
BUILTIN_NAMES = frozenset(dir(builtins))
# The libraries a module may come from that the repo doesn't write, besides the standard
# library: getattr on one of them with a name that isn't written out could reach anything.
LIBRARIES = ("pandas", "numpy", "pyspark", "py4j", "sqlglot")
# A template's placeholder, such as <TABLE>, which stops it parsing until it is filled in.
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")

TOOLBOX = (editions.CORE, *editions.EDITIONS)
USER_COPIED = ("templates", "example_projects", "worked_examples")
# Folders never read: the tracker's notes, and what tools and Pythons leave behind.
NOT_READ = frozenset({".git", ".scratch", "__pycache__", ".pytest_cache", ".ruff_cache",
                      ".mypy_cache", "node_modules", "spark-warehouse", "metastore_db"})
PYTHON_FILES = (".py",)
PAGE_FILES = (".html", ".htm", ".js", ".mjs")


@dataclass(frozen=True)
class Finding:
    """One place the code could reach the network, or a page reaches outside itself.

    `function` is the function it is in, as `outer.inner`, or "<module>"; `name` is what it
    uses, as the module imported or the function called, such as "socket.create_server", or the
    string; `address`, for a network finding other than an import, is the host a call is
    given when it is written out, PASSED_IN when it isn't, and NOT_CALLED for a network
    function named but not called.
    """

    path: str
    line: int
    kind: str
    code: str
    function: str = "<module>"
    name: str = ""
    address: str | None = None

    def __str__(self) -> str:
        return f"{self.path}:{self.line} {self.kind}: {self.code}"


@dataclass(frozen=True)
class Allowed:
    """One reviewed site where code may do what the policy otherwise refuses.

    It matches a finding in `file` (from the repo's root), in `function`, of `kind`, using
    `name`, or anything in it for a name ending ".*"; with `address`, only an import or a call
    given exactly that host, or PASSED_IN for a host that comes from a variable.
    """

    file: str
    function: str
    kind: str
    name: str
    reason: str
    address: str | None = None

    def matches(self, finding: Finding) -> bool:
        return ((self.file, self.function, self.kind) == (finding.path, finding.function,
                                                         finding.kind)
                and self.covers(finding.name)
                and (self.address is None or finding.address in (None, self.address)))

    def covers(self, name: str) -> bool:
        """`name` is the entry's; an entry's "ctypes.*" covers ctypes and all in it."""
        if self.name.endswith(".*"):
            return _under(name, (self.name.removesuffix(".*"),))
        return name == self.name


# Every reviewed site, by file. A new entry needs a reason and the user's OK. Each says what
# the site runs or reaches, and why that is local.
ENGINE = "spark_composer/engine.py"
WINDOWS_JOB = ("holds the Example database's processes in a Windows job, through kernel32, so "
               "they all end with your Python")
GIT = "runs git on a local repository, the repo's own or one in a test's temporary folder"
PYTHON = "runs this same Python on the repo's own code, in a process of its own"
IMPORTS_GIT = "imports subprocess, to run git on a local repository"
IMPORTS_PYTHON = "imports subprocess, to run this same Python in a process of its own"
LOCAL_MODULES = "imports the repo's own modules by name, from its own folders"
ALLOWED: tuple[Allowed, ...] = (
    # Spark Composer's Example database: a Spark in a process of its own, on loopback only.
    Allowed(ENGINE, "<module>", "network", "socket",
            "imports socket, for _launch's listener on 127.0.0.1"),
    Allowed(ENGINE, "<module>", "process", "subprocess",
            "imports subprocess, to start the Example database's process and ask Java"),
    Allowed(ENGINE, "<module>", "process", "subprocess.Popen",
            "_Launcher subclasses Popen, so a Spark launcher that quits is seen to"),
    Allowed(ENGINE, "_launch", "network", "socket.create_server",
            "the listener the process connects back to, on 127.0.0.1 only",
            address="127.0.0.1"),
    Allowed(ENGINE, "_launch", "process", "subprocess.Popen",
            "starts this Python on engine.py itself, as the Example database's process"),
    Allowed(ENGINE, "_check_key", "network", "multiprocessing.connection.*",
            "checks the 32-byte key on a connection to the 127.0.0.1 listener",
            address=PASSED_IN),
    Allowed(ENGINE, "_serve", "network", "multiprocessing.connection.*",
            "the process connects back to the address its parent sent on stdin: the "
            "listener on 127.0.0.1", address=PASSED_IN),
    Allowed(ENGINE, "_ask_java", "process", "subprocess.run",
            "runs java -version to ask its version and folder"),
    Allowed(ENGINE, "_end", "process", "subprocess.TimeoutExpired",
            "catches a wait for the process that timed out"),
    Allowed(ENGINE, "_kill_everything_started_by", "process", "subprocess.run",
            "taskkill /T /F on the process's own tree, where Windows gave no job"),
    Allowed(ENGINE, "_temporary_folder", "process", "ctypes.*",
            "asks kernel32 for the temporary folder's short name, without a space"),
    Allowed(ENGINE, "_kernel32", "process", "ctypes.*", WINDOWS_JOB),
    Allowed(ENGINE, "_job_limits", "process", "ctypes.*", WINDOWS_JOB),
    Allowed(ENGINE, "_job_limits.Basic", "process", "ctypes.*", WINDOWS_JOB),
    Allowed(ENGINE, "_job_limits.Extended", "process", "ctypes.*", WINDOWS_JOB),
    Allowed(ENGINE, "_job_holding", "process", "ctypes.*", WINDOWS_JOB),
    # The dev hooks.
    Allowed(".claude/hooks/drift_list.py", "<module>", "process", "subprocess", IMPORTS_GIT),
    Allowed(".claude/hooks/drift_list.py", "git", "process", "subprocess.run", GIT),
    Allowed(".claude/hooks/drift_list.py", "on_this_branch", "process", "subprocess.run", GIT),
    # The dev tools.
    Allowed("tools/editions.py", "use", "dynamic code", "importlib.import_module",
            "imports Spark Composer's own modules under sqlglot Composer's names"),
    Allowed("tools/example_gallery.py", "statement_scripts", "dynamic code",
            "importlib.import_module", LOCAL_MODULES),
    Allowed("tools/example_gallery.py", "toolbox_modules", "dynamic code",
            "importlib.import_module", LOCAL_MODULES),
    Allowed("tools/example_gallery.py", "run_step", "dynamic code", "compile",
            "runs a >>> example from the repo's own docstrings, as a doctest does"),
    Allowed("tools/example_gallery.py", "run_step", "dynamic code", "exec",
            "runs a >>> example from the repo's own docstrings, as a doctest does"),
    Allowed("tools/example_gallery.py", "run_step", "dynamic code", "eval",
            "runs a >>> example from the repo's own docstrings, as a doctest does"),
    Allowed("tools/example_project.py", "<module>", "process", "subprocess", IMPORTS_PYTHON),
    Allowed("tools/example_project.py", "make", "process", "subprocess.run",
            "runs this same Python on example_project.py itself, in the project's folder"),
    Allowed("tools/export_clean.py", "<module>", "process", "subprocess",
            "imports subprocess, to run git and this same Python"),
    Allowed("tools/export_clean.py", "describe_toolbox", "dynamic code", "__import__",
            "imports an Edition's folder by name, in the Clean tree it built"),
    Allowed("tools/export_clean.py", "fresh_python", "process", "subprocess.run", PYTHON),
    Allowed("tools/export_clean.py", "git", "process", "subprocess.run", GIT),
    Allowed("tools/export_clean.py", "committed_files", "process", "subprocess.run",
            "git archive of the repo's own commit"),
    Allowed("tools/export_clean.py", "export", "process", "subprocess.run",
            "git rev-parse of the repo's own main"),
    # The tests.
    Allowed("tests/conftest.py", "toolbox_module", "dynamic code", "importlib.import_module",
            LOCAL_MODULES),
    Allowed("tests/test_example_projects.py", "<module>", "process", "subprocess",
            IMPORTS_PYTHON),
    Allowed("tests/test_example_projects.py", "_imported", "dynamic code",
            "importlib.import_module", "imports an Example project's own modules by name"),
    Allowed("tests/test_example_projects.py", "write_project", "process", "subprocess.run",
            "runs this same Python on tools/example_project.py"),
    Allowed("tests/test_how_tos.py", "<module>", "process", "subprocess",
            "imports subprocess, to run node"),
    Allowed("tests/test_how_tos.py",
            "test_the_script_filters_the_how_tos_and_puts_a_copy_button_on_each_block",
            "process", "subprocess.run",
            "runs node on the how-to page's own script, in a stand-in for a browser"),
    Allowed("tests/test_import_self_check.py", "<module>", "process", "subprocess",
            IMPORTS_PYTHON),
    Allowed("tests/test_import_self_check.py", "import_copy", "process", "subprocess.run",
            PYTHON),
    Allowed("tests/test_import_self_check.py", "renamed_copy", "process", "subprocess.run",
            PYTHON),
    Allowed("tests/test_import_self_check.py",
            "test_an_exported_copy_says_when_it_was_exported", "process", "subprocess.run",
            PYTHON),
    Allowed("tests/test_lineage.py", "<module>", "dynamic code", "runpy",
            "imports runpy, to run a script the test writes"),
    Allowed("tests/test_lineage.py", "<module>", "process", "subprocess",
            "imports subprocess, to run git and node"),
    Allowed("tests/test_lineage.py", "run_script", "dynamic code", "runpy.run_path",
            "runs a script the test wrote, as a user runs one"),
    Allowed("tests/test_lineage.py", "git", "process", "subprocess.run", GIT),
    Allowed("tests/test_lineage.py",
            "test_in_a_notebook_the_name_and_folder_come_from_the_notebook", "dynamic code",
            "compile", "runs the test's own script as a notebook cell"),
    Allowed("tests/test_lineage.py",
            "test_in_a_notebook_the_name_and_folder_come_from_the_notebook", "dynamic code",
            "exec", "runs the test's own script as a notebook cell"),
    Allowed("tests/test_lineage.py",
            "test_several_statements_are_named_by_their_variables_in_the_order_passed",
            "dynamic code", "compile", "runs the test's own line of code as typed at a prompt"),
    Allowed("tests/test_lineage.py",
            "test_several_statements_are_named_by_their_variables_in_the_order_passed",
            "dynamic code", "exec", "runs the test's own line of code as typed at a prompt"),
    Allowed("tests/test_lineage.py", "test_the_pages_script_is_javascript_a_browser_can_read",
            "process", "subprocess.run", "runs node --check on the lineage page's own script"),
    Allowed("tests/test_refusals.py", "<module>", "process", "subprocess", IMPORTS_PYTHON),
    Allowed("tests/test_refusals.py",
            "test_a_repeated_rows_warning_shows_from_a_scope_with_no_name", "dynamic code",
            "exec", "runs the test's own line of code in a scope with no name"),
    Allowed("tests/test_refusals.py", "test_a_repeated_rows_warning_shows_under_python_dash_c",
            "process", "subprocess.run", PYTHON),
    Allowed("tests/test_tables.py", "test_write_table_reference_writes_a_file_that_imports",
            "dynamic code", "exec", "runs the Table reference file the Toolbox just wrote"),
    Allowed("tests/test_templates.py", "filled_project", "dynamic code",
            "importlib.import_module", "imports a filled-in template's modules by name"),
    Allowed("tests/test_templates.py", "test_notebook_start_runs_in_an_empty_folder",
            "dynamic code", "importlib.import_module",
            "imports a filled-in template's module by name"),
    Allowed("tests/repo/test_edition_parity.py", "<module>", "process", "subprocess",
            IMPORTS_PYTHON),
    Allowed("tests/repo/test_edition_parity.py",
            "test_without_what_spark_composer_adds_it_shows_what_sqlglot_composer_shows",
            "process", "subprocess.run", "runs this same Python on tools/hive_corpus.py"),
    Allowed("tests/repo/test_export_clean.py", "<module>", "process", "subprocess",
            IMPORTS_GIT),
    Allowed("tests/repo/test_export_clean.py", "git", "process", "subprocess.run", GIT),
    Allowed("tests/repo/test_hooks.py", "<module>", "process", "subprocess",
            "imports subprocess, to run git and the hooks"),
    Allowed("tests/repo/test_hooks.py", "run", "process", "subprocess.run", GIT),
    Allowed("tests/repo/test_hooks.py", "a_clone_on_dev", "process", "subprocess.run",
            "git init and clone of a bare repository in the test's temporary folder"),
    Allowed("tests/repo/test_hooks.py", "review_hook", "process", "subprocess.run",
            "runs this same Python on a hook in .claude/hooks/"),
    Allowed("tests/repo/test_hooks.py",
            "test_the_hook_finds_the_drift_list_from_a_folder_inside_the_repo", "process",
            "subprocess.run", "runs this same Python on a hook in .claude/hooks/"),
    Allowed("tests/repo/test_hooks.py",
            "test_the_stop_hook_waits_for_a_review_and_not_for_a_dropped_commit", "process",
            "subprocess.run", "runs this same Python on a hook in .claude/hooks/"),
    Allowed("tests/repo/test_hooks.py",
            "test_protect_main_refuses_a_commit_on_main_when_run_as_a_hook", "process",
            "subprocess.run", "runs this same Python on a hook in .claude/hooks/"),
    Allowed("tests/repo/test_toolbox_checks.py", "<module>", "process", "subprocess",
            IMPORTS_PYTHON),
    Allowed("tests/repo/test_toolbox_checks.py",
            "test_spark_composer_has_the_same_public_names", "process", "subprocess.run",
            PYTHON),
    Allowed("tests/repo/test_toolbox_checks.py", "test_ruff_passes_with_its_complexity_limit",
            "process", "subprocess.run", "runs ruff, in this same Python, on the repo"),
    Allowed("tests/repo/test_two_editions.py", "<module>", "process", "subprocess",
            IMPORTS_PYTHON),
    Allowed("tests/repo/test_two_editions.py", "_run", "process", "subprocess.run", PYTHON),
    Allowed("tests/spark_edition/test_spark_example_database.py", "<module>", "network",
            "socket", "imports socket, for a stray connection to the Example database's "
            "listener on 127.0.0.1"),
    Allowed("tests/spark_edition/test_spark_example_database.py", "<module>", "process",
            "subprocess", "imports subprocess, to run Python and powershell"),
    Allowed("tests/spark_edition/test_spark_example_database.py",
            "test_a_stray_connection_doesnt_hold_up_a_start.knock", "network",
            "socket.create_connection",
            "a stray connection to the Example database's listener, on 127.0.0.1 only",
            address="127.0.0.1"),
    Allowed("tests/spark_edition/test_spark_example_database.py", "_processes_naming",
            "process", "subprocess.run",
            "powershell Get-CimInstance, listing this computer's processes"),
    Allowed("tests/spark_edition/test_spark_example_database.py", "_other_python", "process",
            "subprocess.Popen", PYTHON),
    Allowed("tests/spark_edition/test_spark_example_database.py",
            "test_a_python_that_stops_mid_query_stops_at_once_and_leaves_nothing", "process",
            "subprocess.run", PYTHON),
    Allowed("tests/spark_edition/test_spark_independence.py", "_loaded", "dynamic code",
            "importlib.import_module", LOCAL_MODULES),
)


# --- Reading one file ---------------------------------------------------------------------------


def findings_in(text: str, path: str, allowed: tuple[Allowed, ...] = ALLOWED) -> list[Finding]:
    """Each finding in a file's text, read as the file at `path` in the repo, that `allowed`
    doesn't cover.

    `path` is from the repo's root, such as "composer_core/running.py"; its folder decides what
    is allowed, and its suffix how the text is read. A file of any other kind has no findings.
    """
    path = _repo_path(path)
    found = _found(text, path)
    if scope_of(path) == "user-copied":
        return found
    return [finding for finding in found if not any(entry.matches(finding) for entry in allowed)]


def scope_of(path: str) -> str:
    """Which rules a file is read by: "toolbox", "user-copied" or "maintainer"."""
    top = PurePosixPath(_repo_path(path)).parts[:1]
    if top and top[0] in TOOLBOX:
        return "toolbox"
    if top and top[0] in USER_COPIED:
        return "user-copied"
    return "maintainer"


def external_references(text: str) -> list[str]:
    """Each thing a page holds that loads or sends something outside it, as "line N: what"."""
    return [f"line {line}: {what}" for line, what, _ in _page_references(text)]


def page_findings(text: str, path: str) -> list[Finding]:
    """Each reference in `text` that loads or sends something outside it, as a finding in the
    file at `path`, whatever its suffix: the export reads the Clean tree's Markdown so, since a
    preview of it loads what it embeds. `findings_in` and `scan` leave Markdown alone, so the
    repo's notes may cite their sources."""
    return [Finding(_repo_path(path), line, "page reference", around, name=what)
            for line, what, around in _page_references(text)]


def _repo_path(path: str) -> str:
    return PurePosixPath(str(path).replace("\\", "/")).as_posix()


def _found(text: str, path: str) -> list[Finding]:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in PAGE_FILES:
        return page_findings(text, path)
    if suffix in PYTHON_FILES:
        return _python_findings(text, path)
    if suffix == ".ipynb":
        return _notebook_findings(text, path)
    return []


def _page_references(text: str) -> list[tuple[int, str, str]]:
    """Each reference's line, what it is, and up to 40 characters either side of it on its
    line, since a page's line can be long."""
    found = []
    for match in PAGE_REFERENCE.finditer(text):
        start = max(text.rfind("\n", 0, match.start()) + 1, match.start() - 40)
        end = text.find("\n", match.end())
        end = min(len(text) if end == -1 else end, match.end() + 40)
        found.append((text.count("\n", 0, match.start()) + 1, match.group(),
                      text[start:end].strip()))
    return found


def _python_findings(text: str, path: str) -> list[Finding]:
    tree = _parsed(text)
    if isinstance(tree, SyntaxError):
        return [Finding(path, tree.lineno or 0, "unreadable",
                        f"it doesn't parse as Python ({tree.msg}), so it can't be read")]
    reader = _Reader(path, text.splitlines(), _aliases(tree),
                     read_strings=scope_of(path) != "maintainer")
    reader.visit(tree)
    return reader.found


def _parsed(text: str) -> ast.Module | SyntaxError:
    """The file's tree; a template's placeholders are read as names, so it parses unfilled."""
    try:
        return ast.parse(text)
    except SyntaxError as error:
        try:
            return ast.parse(PLACEHOLDER.sub(r"\1", text))
        except SyntaxError:
            return error


def _notebook_findings(text: str, path: str) -> list[Finding]:
    """A notebook's code cells, read as one Python file, line by line as joined; a `!` or `%`
    line, which runs a shell command or an IPython magic, is a process."""
    try:
        cells = json.loads(text).get("cells", [])
    except (ValueError, AttributeError):
        return [Finding(path, 0, "unreadable", "it isn't a notebook's JSON, so it can't be read")]
    lines = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            source = cell.get("source", "")
            lines += ("".join(source) if isinstance(source, list) else source).splitlines()
    magic = [line.lstrip().startswith(("!", "%")) for line in lines]
    shell = [Finding(path, number, "process", line.strip(), name=line.strip().split()[0])
             for number, (line, is_magic) in enumerate(zip(lines, magic), 1) if is_magic]
    code = "\n".join("" if is_magic else line for line, is_magic in zip(lines, magic))
    return shell + _python_findings(code, path)


# --- What a name is -----------------------------------------------------------------------------


def _under(name: str, modules: tuple[str, ...]) -> bool:
    return any(name == module or name.startswith(module + ".") for module in modules)


def kind_of(name: str) -> str | None:
    """The kind of finding that using `name`, a module or a function by its full name, is."""
    name = name.removeprefix("builtins.")
    if _under(name, NETWORK_MODULES) or name in NETWORK_FUNCTIONS:
        return "network"
    if _under(name, PROCESS_MODULES) or name in PROCESS_ASYNCIO or _starts_a_process(name):
        return "process"
    if name in DYNAMIC_FUNCTIONS or _under(name, DYNAMIC_MODULES):
        return "dynamic code"
    if (_under(name, FETCHER_MODULES) or re.fullmatch(r"pandas(\.\w+)*\.read_\w+", name)
            or (_under(name, ("numpy",)) and name.rpartition(".")[2] in NUMPY_FETCHERS)
            or name.endswith("builder.remote")):
        return "library fetcher"
    return None


def _starts_a_process(name: str) -> bool:
    module, _, function = name.rpartition(".")
    return module in PROCESS_FUNCTION_MODULES and (function in PROCESS_FUNCTIONS
                                                   or function.startswith(PROCESS_PREFIXES))


def _aliases(tree: ast.AST) -> dict[str, str]:
    """What each name a file imports stands for, by full name, wherever it is imported.

    A relative import names the file's own folder, so it stands for something starting ".".
    """
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    names[alias.asname] = alias.name
                else:
                    names[alias.name.split(".")[0]] = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            for alias in node.names:
                names[alias.asname or alias.name] = f"{base}.{alias.name}".replace("..", ".")
    return names


def _imported(node: ast.Import | ast.ImportFrom) -> list[str]:
    """The full name of each module or name an import brings in; a relative import's none."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.level:
        return []
    return [node.module or ""] + [f"{node.module}.{alias.name}" for alias in node.names]


def _literal(node: ast.AST | None) -> str | None:
    """A string written out, or added up from strings written out, as "soc" + "ket"."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left), _literal(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _plain(name: str) -> str:
    """A full name without the ways round to it: builtins.eval is eval, os.__dict__.system and
    sys.modules.os.system are os.system."""
    name = name.replace(".__dict__", "").removeprefix("sys.modules.")
    return name if name == "builtins" else name.removeprefix("builtins.")


def _address(call: ast.Call) -> str:
    """The host a network call is given first, as in socket.create_server(("127.0.0.1", 0)), or
    PASSED_IN when it isn't written out."""
    first = call.args[0] if call.args else None
    if isinstance(first, ast.Tuple) and first.elts:
        first = first.elts[0]
    host = _literal(first)
    return PASSED_IN if host is None else host


def _from_outside(module: str) -> bool:
    """A module the repo doesn't write: the standard library's, or a library's."""
    top = module.split(".")[0]
    return not module.startswith(".") and (top in sys.stdlib_module_names or top in LIBRARIES)


class _Reader(ast.NodeVisitor):
    """Collects the findings of one Python file's tree."""

    def __init__(self, path: str, lines: list[str], aliases: dict[str, str],
                 read_strings: bool, offset: int = 0, functions: tuple[str, ...] = ()) -> None:
        self.path = path
        self.lines = lines
        self.aliases = aliases
        self.read_strings = read_strings
        self.offset = offset
        self.functions = functions
        self.uses_pyspark = any(_under(name, ("pyspark",)) for name in aliases.values())
        self.found: list[Finding] = []

    def add(self, node: ast.AST, kind: str, name: str, address: str | None = None) -> None:
        line = self.offset + node.lineno
        code = self.lines[line - 1].strip() if 0 < line <= len(self.lines) else name
        self.found.append(Finding(self.path, line, kind, code,
                                  ".".join(self.functions) or "<module>", name, address))

    def full_name(self, node: ast.AST) -> str | None:
        """What an expression stands for, by full name, when it names a module or what is in
        one: "socket.create_server" for s.create_server after `import socket as s`, and the
        same through getattr(s, "create_server"), s.__dict__["create_server"] or
        importlib.import_module("socket").create_server; None for anything else."""
        if isinstance(node, ast.Name):
            if node.id == "__builtins__":
                return "builtins"
            root = self.aliases.get(node.id) or (node.id if node.id in BUILTIN_NAMES else None)
            return _plain(root) if root else None
        if isinstance(node, ast.Attribute | ast.Subscript):
            base = self.full_name(node.value)
            last = node.attr if isinstance(node, ast.Attribute) else _literal(node.slice)
            return _plain(f"{base}.{last}") if base and last else None
        if isinstance(node, ast.Call):
            return self.called_name(node)
        return None

    def called_name(self, node: ast.Call) -> str | None:
        """The module or name a call gives: an import, getattr or vars given names written
        out."""
        function = self.full_name(node.func)
        written = [_literal(argument) for argument in node.args]
        if function in IMPORTERS:
            return written[0] if written else None
        if function == "getattr" and len(written) >= 2 and written[1] is not None:
            base = self.full_name(node.args[0])
            return _plain(f"{base}.{written[1]}") if base else None
        if function == "vars" and len(node.args) == 1:
            return self.full_name(node.args[0])
        return None

    # Imports.

    def visit_Import(self, node: ast.Import | ast.ImportFrom) -> None:
        for name in _imported(node):
            kind = kind_of(name)
            if kind:
                self.add(node, kind, name)
        star = isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)
        if star and node.level == 0 and _from_outside(node.module or ""):
            # Everything it brings in is named nowhere, so nothing it brings in can be read.
            self.add(node, "dynamic code", f"{node.module}.*")

    visit_ImportFrom = visit_Import

    # Functions and classes: what is in their body is in them.

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for outside in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults]:
            if outside is not None:
                self.visit(outside)
        arguments = node.args
        for argument in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
                         arguments.vararg, arguments.kwarg]:
            if argument is not None:
                self.visit_calls_in(argument.annotation)
        self.visit_calls_in(node.returns)
        self.inside(node.name, node.body)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for outside in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(outside)
        self.inside(node.name, node.body)

    def inside(self, name: str, body: list[ast.stmt]) -> None:
        self.functions += (name,)
        for statement in body:
            self.visit(statement)
        self.functions = self.functions[:-1]

    # Annotations and the types an except clause names: a name there is only looked up, so
    # only a call in one is read.

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit_calls_in(node.annotation)
        if node.value is not None:
            self.visit(node.value)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.visit_calls_in(node.type)
        for statement in node.body:
            self.visit(statement)

    def visit_calls_in(self, node: ast.AST | None) -> None:
        if isinstance(node, ast.Call):
            self.visit(node)
        elif node is not None:
            for part in ast.iter_child_nodes(node):
                self.visit_calls_in(part)

    # Names, and calls.

    def visit_Name(self, node: ast.Name | ast.Attribute | ast.Subscript) -> None:
        name = self.full_name(node) if isinstance(node.ctx, ast.Load) else None
        if name is None:
            self.dynamic_subscript(node)
            self.generic_visit(node)
            return
        kind = kind_of(name)
        # A constant, such as subprocess.PIPE, only names a value.
        if kind and not (name.rpartition(".")[2].isupper() and "." in name):
            self.add(node, kind, name, NOT_CALLED if kind == "network" else None)

    visit_Attribute = visit_Name
    visit_Subscript = visit_Name

    def dynamic_subscript(self, node: ast.AST) -> None:
        """A module's names looked up by a name that isn't written out, as vars(os)[name],
        os.__dict__[name] or __builtins__[name], on a module the repo doesn't write."""
        if not (isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load)
                and _literal(node.slice) is None):
            return
        names = node.value
        a_namespace = ((isinstance(names, ast.Attribute) and names.attr == "__dict__")
                       or (isinstance(names, ast.Call) and self.full_name(names.func) == "vars")
                       or (isinstance(names, ast.Name) and names.id == "__builtins__"))
        module = self.full_name(names)
        if a_namespace and module and _from_outside(module):
            self.add(node, "dynamic code", f"{module}[...]")

    def visit_Call(self, node: ast.Call) -> None:
        name = self.full_name(node.func)
        taken = self.called_name(node)
        if name in IMPORTERS:
            self.read_import(node, name, taken)
        elif taken and kind_of(taken):
            self.add(node, kind_of(taken), taken, NOT_CALLED if kind_of(taken) == "network"
                     else None)
        elif name == "getattr" and self.dynamic_getattr(node):
            self.add(node, "dynamic code", name)
        elif name and kind_of(name):
            self.add(node, kind_of(name), name,
                     _address(node) if kind_of(name) == "network" else None)
        elif self.connects_spark_elsewhere(node):
            self.add(node, "library fetcher", "SparkSession.builder.remote")
        else:
            self.visit(node.func)
        for argument in [*node.args, *node.keywords]:
            self.visit(argument)

    def read_import(self, node: ast.Call, name: str, module: str | None) -> None:
        """An import by a call: of a name not written out, or by __import__, dynamic code; of a
        module the rules name, what that module is."""
        if module is None or name != "importlib.import_module":
            self.add(node, "dynamic code", name)
        if module and kind_of(module):
            self.add(node, kind_of(module), module)

    def dynamic_getattr(self, node: ast.Call) -> bool:
        """getattr with a name that isn't written out, on a module the repo doesn't write."""
        if len(node.args) < 2 or _literal(node.args[1]) is not None:
            return False
        module = self.full_name(node.args[0])
        return module is not None and (_from_outside(module) or kind_of(module) is not None)

    def connects_spark_elsewhere(self, node: ast.Call) -> bool:
        """A .remote(...) call on a Spark session's builder, however it was reached."""
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "remote"):
            return False
        return self.uses_pyspark or any(isinstance(part, ast.Attribute) and part.attr == "builder"
                                        for part in ast.walk(node.func.value))

    # Strings: prose is not read, apart from its >>> examples; a used string is.

    def visit_Expr(self, node: ast.Expr) -> None:
        prose = _literal(node.value)
        if prose is None:
            self.visit(node.value)
            return
        self.read_examples(node.value, prose)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str | bytes):
            text = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
            self.read_string(node, text)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        added = _literal(node)
        if added is None:
            self.generic_visit(node)
        else:
            self.read_string(node, added)

    def read_string(self, node: ast.AST, text: str) -> None:
        if not self.read_strings:
            return
        for pattern, kind in ((URL, "URL"), (SPARK_SETTING, "library fetcher")):
            match = pattern.search(text)
            if match:
                self.add(node, kind, match.group())

    def read_examples(self, node: ast.Constant, prose: str) -> None:
        """Read a docstring's >>> examples as code, each at its own line of the file."""
        try:
            examples = doctest.DocTestParser().get_examples(prose)
        except ValueError:
            return
        for example in examples:
            tree = _parsed(example.source)
            # An example that doesn't parse can't run, as prose showing a doctest's layout.
            if isinstance(tree, SyntaxError):
                continue
            offset = self.offset + node.lineno + example.lineno - 1
            reader = _Reader(self.path, self.lines, {**self.aliases, **_aliases(tree)},
                             self.read_strings, offset, self.functions)
            reader.visit(tree)
            self.found += reader.found


# --- Reading the repo ---------------------------------------------------------------------------


def scan(root: Path = ROOT, paths: list[str | Path] | None = None,
         allowed: tuple[Allowed, ...] = ALLOWED) -> list[Finding]:
    """Each finding in the files under `root`, or in the files and folders `paths` names (from
    `root`, or absolute), that `allowed` doesn't cover."""
    found = []
    for file in _files(root, paths):
        if file.is_file():
            found += findings_in(_text(file), _path_from(root, file), allowed)
        else:
            found.append(Finding(_path_from(root, file), 0, "unreadable",
                                 "there is no such file or folder"))
    return found


def stale_entries(root: Path = ROOT, allowed: tuple[Allowed, ...] = ALLOWED) -> list[Finding]:
    """Each entry of `allowed` that matches nothing in the files under `root`, and any that
    names user-copied code, where nothing is allowed."""
    stale = []
    read: dict[str, list[Finding]] = {}
    for entry in allowed:
        file = root / entry.file
        if entry.file not in read:
            read[entry.file] = _found(_text(file), entry.file) if file.is_file() else []
        found = read[entry.file]
        if scope_of(entry.file) == "user-copied":
            why = "names user-copied code, where nothing is allowed"
        elif not any(entry.matches(finding) for finding in found):
            why = "matches nothing: remove it, or correct it"
        else:
            continue
        stale.append(Finding(entry.file, 0, "stale entry",
                             f"ALLOWED's {entry.kind} entry for {entry.name} in "
                             f"{entry.function} {why}", entry.function, entry.name))
    return stale


def _files(root: Path, paths: list[str | Path] | None) -> list[Path]:
    starts = [root] if paths is None else [Path(root, path) for path in paths]
    files = []
    for start in starts:
        if not start.is_dir():
            files.append(start)
            continue
        for folder, subfolders, names in os.walk(start):
            subfolders[:] = sorted(name for name in subfolders
                                   if not _not_read(Path(folder, name), root))
            files += [Path(folder, name) for name in sorted(names)
                      if name.lower().endswith(PYTHON_FILES + PAGE_FILES + (".ipynb",))]
    return files


def _not_read(folder: Path, root: Path) -> bool:
    """A folder that holds no code of the repo's: see NOT_READ; Claude Code's worktrees, which
    are other checkouts; and a Python's own folder, which holds pyvenv.cfg."""
    if folder.name in NOT_READ or (folder / "pyvenv.cfg").exists():
        return True
    return _path_from(root, folder) == ".claude/worktrees"


def _path_from(root: Path, file: Path) -> str:
    try:
        return file.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return file.as_posix()


def _text(file: Path) -> str:
    return file.read_text(encoding="utf-8", errors="replace")


def main(arguments: list[str]) -> int:
    paths = [Path(path).resolve() for path in arguments[1:]] or None
    found = scan(ROOT, paths) + (stale_entries(ROOT) if paths is None else [])
    sys.stdout.reconfigure(errors="replace")
    for finding in found:
        print(finding)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
