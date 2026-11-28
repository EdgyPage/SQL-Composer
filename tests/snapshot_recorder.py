"""The snapshot of what the Toolbox shows its user, held while Toolbox 8.0's refactor runs.

Phase 2 changes nothing a user sees: no Hive, no refusal or warning message, no text it prints,
no report a Project action or a check gives, no rows the Example database gives. The suite pins
much of that, but not all, so every test also records what the Toolbox makes, where it makes
it:

- `_four_part_message`, every refusal and warning message;
- `writing.sql_text`, every Hive string a Statement is written as;
- `print`, as the `running` module calls it, every text `show_hive` prints, headings, Session
  settings, Unchecked statements and Python steps included (show_hive itself isn't wrapped:
  it reads its caller's variable names from the calling frame);
- `ProjectReport` and `Verdict`, every Project action's report and every check's verdict, as
  each prints;
- `example_database.query`, dev's Example database's, every set of rows, as CSV.

Each is kept as a short hash in the snapshot of the sqlglot the run is on. CI runs the whole
suite at two, engine.py's `_PIN` and `_NEWEST_TESTED`, and a few texts differ between them, so
each keeps its own (Toolbox 8.10; the user: "test for both"): `tests/snapshot/known.txt` for
the pin, and `tests/snapshot/known-<version>.txt`, such as `known-30.34.0.txt`, for the newest
tested. A run on any other sqlglot checks no snapshot, and says why in one line at its end.

Before a text is hashed, the run's temp folders are written as `<tmp>` everywhere; in a
message, printed text or report, its times and memory addresses are written as `<time>` and
`<address>` too, but never in Hive or rows, where a changed time would be a real change. A test
that makes a text the snapshot doesn't know fails, showing it. A run of the whole suite also
fails on a hash no test made: something a user saw is gone.

Writing a snapshot again is a deliberate act, which its commit message says, never part of a
refactor: run the whole suite, every test passing, with `SNAPSHOT_WRITE=1` set, on the sqlglot
whose snapshot it is; it writes that one file. A run of part of the suite, one with a failure,
or one on a sqlglot CI doesn't test is refused, since it would write only what it made.
"""

from __future__ import annotations

import builtins
import functools
import hashlib
import importlib
import importlib.metadata
import os
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pandas as pd

TESTS = Path(__file__).resolve().parent
# Where each sqlglot's snapshot is kept.
SNAPSHOT = TESTS / "snapshot"
WRITING = os.environ.get("SNAPSHOT_WRITE") == "1"
# A time as the Toolbox writes one: 2026-10-30 17:51, or 20261030-175142 in a folder's name.
TIME = re.compile(r"\d{4}-\d{2}-\d{2}[ T_]\d{2}[:\-.]\d{2}([:\-.]\d{2}(\.\d+)?)?"
                  r"|\b\d{8}-\d{6}\b")
ADDRESS = re.compile(r"\b0x[0-9a-fA-F]{6,}\b")
# A temp folder's placeholder and the path after it, whose separators are written as / so a
# path reads the same on Windows as on Linux, where CI runs.
TEMP_PATH = re.compile(r"<tmp>[^\s'\"<>,;:)]*")
# The kinds of text that are prose a user reads, where a time or an address can change run to
# run; Hive and rows are kept exactly.
PROSE = frozenset({"message", "printed", "report"})

# What this test made so far: each text, by the kind of place that made it.
texts_made_by_this_test: list[tuple[str, str]] = []
hashes_made_in_this_run: set[str] = set()
temp_folders: list[str] = []


def text_as_kept(kind: str, text: str) -> str:
    """`text` with what changes from run to run written as a placeholder."""
    for folder in temp_folders:
        for spelling in (folder, folder.replace("\\", "/"), folder.replace("\\", "\\\\")):
            text = text.replace(spelling, "<tmp>")
    text = TEMP_PATH.sub(lambda path: path.group().replace("\\\\", "/").replace("\\", "/"),
                         text)
    if kind in PROSE:
        text = ADDRESS.sub("<address>", TIME.sub("<time>", text))
    return text


def hash_of(kind: str, text: str) -> str:
    """The short hash a snapshot keeps for one text."""
    return hashlib.sha256(text_as_kept(kind, text).encode("utf-8")).hexdigest()[:20]


def recorded_function(kind: str, function: Callable[..., object],
                      text_of: Callable[[object], str]) -> Callable[..., object]:
    """`function`, recording the text of what it returns as a text of kind `kind`."""
    @functools.wraps(function)
    def recorded(*args: object, **kwargs: object) -> object:
        value = function(*args, **kwargs)
        texts_made_by_this_test.append((kind, text_of(value)))
        return value
    return recorded


def rows_as_text(rows: pd.DataFrame) -> str:
    """A DataFrame of rows as CSV, the text the snapshot keeps for it, each line ended with LF
    on every computer: to_csv's own ending is the computer's, CRLF on Windows."""
    return rows.to_csv(index=False, lineterminator="\n")


def recorded_print(*values: object, sep: str = " ", **kwargs: object) -> None:
    """`print`, recording what it prints."""
    texts_made_by_this_test.append(("printed", sep.join(str(value) for value in values)))
    builtins.print(*values, sep=sep, **kwargs)


def replace_everywhere(original: object, replacement: object) -> None:
    """Put `replacement` wherever a loaded module holds `original`, as a name of its own: the
    Toolbox's own modules, and every test and Worked example that imported it by name."""
    for module in list(sys.modules.values()):
        if not isinstance(module, ModuleType):
            continue
        for name, value in list(vars(module).items()):
            if value is original:
                setattr(module, name, replacement)


def record_each_printed(kind: type) -> None:
    """Record the text each instance of `kind` prints as, once it is made."""
    original_init = kind.__init__

    @functools.wraps(original_init)
    def recorded_init(self, *args: object, **kwargs: object) -> None:
        original_init(self, *args, **kwargs)
        texts_made_by_this_test.append(("report", repr(self)))

    kind.__init__ = recorded_init


def install(toolbox: Callable[[str], ModuleType], basetemp: str) -> None:
    """Record at each place the Toolbox makes what a user sees, once per run."""
    temp_folders.extend([basetemp, tempfile.gettempdir()])
    package = toolbox("")
    for module, name, kind, text_of in (
        (package, "_four_part_message", "message", str),
        (toolbox("writing"), "sql_text", "hive", str),
        (importlib.import_module("example_database"), "query", "rows", rows_as_text),
    ):
        original = getattr(module, name)
        replace_everywhere(original, recorded_function(kind, original, text_of))
    toolbox("running").print = recorded_print
    record_each_printed(toolbox("project").ProjectReport)
    record_each_printed(toolbox("tables").Verdict)


def versions_ci_tests() -> tuple[str, str]:
    """The sqlglots CI runs the whole suite at, as engine.py names them: its pin, then the
    newest it is tested on."""
    # Imported here, not at the top: conftest imports the Toolbox after the offline trap.
    from sqlglot_composer import engine

    pin, newest = (".".join(str(n) for n in version)
                   for version in (engine._PIN, engine._NEWEST_TESTED))
    return pin, newest


def snapshot_files() -> dict[str, Path]:
    """Each sqlglot CI tests, by its version, with its snapshot: known.txt for the pin, and a
    file named for its version for the newest tested."""
    pin, newest = versions_ci_tests()
    return {pin: SNAPSHOT / "known.txt", newest: SNAPSHOT / f"known-{newest}.txt"}


def sqlglot_version() -> str:
    """The version of the sqlglot this run is on, as its installed metadata says: a shared
    file of tests/ imports no sqlglot of its own (test_suite_layout.py)."""
    return importlib.metadata.version("sqlglot")


def snapshot_file() -> Path | None:
    """The snapshot of the sqlglot this run is on, or None where CI tests no such sqlglot."""
    return snapshot_files().get(sqlglot_version())


def snapshot_name(file: Path) -> str:
    """A snapshot's file as a message names it, from the repo's top."""
    return f"tests/snapshot/{file.name}"


def known_hashes() -> set[str] | None:
    """The hashes the snapshot of this run's sqlglot holds, or None where it has none."""
    file = snapshot_file()
    if file is None:
        return None
    if not file.exists():
        return set()
    return set(file.read_text(encoding="utf-8").split())


def why_no_snapshot_is_checked() -> str | None:
    """Why this run checks no snapshot, in one line, or None where it checks one."""
    if snapshot_file() is not None:
        return None
    pin, newest = versions_ci_tests()
    return (f"No snapshot was checked: tests/snapshot/ keeps one for each sqlglot CI tests, "
            f"{pin} and {newest}, and this is {sqlglot_version()}, which can write some texts "
            "differently.")


def take_unknown_texts(known: set[str] | None) -> list[str]:
    """Take what this test made, keep each hash for the run, and give back each text the
    snapshot doesn't know, with the kind of place that made it: none, when the snapshot is
    being written, or where this sqlglot has none (`known` is None)."""
    found = []
    for kind, text in texts_made_by_this_test:
        digest = hash_of(kind, text)
        hashes_made_in_this_run.add(digest)
        if known is not None and digest not in known and not WRITING:
            found.append(f"A {kind} text:\n{text_as_kept(kind, text)}")
    texts_made_by_this_test.clear()
    return found


def is_the_whole_suite(args: list[str], keyword: str, markers: str, failed: int) -> bool:
    """Whether a run read every test, and every one passed: the only run whose hashes are the
    whole snapshot."""
    every_test = all(Path(arg).resolve() == TESTS for arg in args)
    return every_test and not keyword and not markers and failed == 0


def finish_the_run(whole: bool) -> str | None:
    """At a run's end, with every test's hashes in hashes_made_in_this_run, every worker's
    included: with SNAPSHOT_WRITE=1, write this sqlglot's snapshot for a `whole` run, and
    otherwise give why the run fails; without it, for a `whole` run, give why the run fails
    when a hash the snapshot holds no test made, since something a user saw is gone. None where
    the run passes, as it does without SNAPSHOT_WRITE=1 where this sqlglot has no snapshot."""
    file = snapshot_file()
    if file is None:
        if not WRITING:
            return None
        pin, newest = versions_ci_tests()
        return (f"SNAPSHOT_WRITE=1 writes a snapshot only on a sqlglot CI tests, {pin} or "
                f"{newest}, and this is {sqlglot_version()}.")
    if WRITING:
        if not whole:
            return (f"{snapshot_name(file)}: SNAPSHOT_WRITE=1 writes it only from a run of "
                    "the whole suite in which every test passed.")
        write_snapshot(file)
        return None
    gone = known_hashes() - hashes_made_in_this_run
    if whole and gone:
        return (f"{snapshot_name(file)}: {len(gone)} of its texts no test made: something "
                "the Toolbox showed its user is gone.")
    return None


def write_snapshot(file: Path) -> None:
    """The snapshot `file`, as this run made it: one hash per line, sorted."""
    file.parent.mkdir(exist_ok=True)
    file.write_text("".join(f"{digest}\n" for digest in sorted(hashes_made_in_this_run)),
                    encoding="utf-8")
