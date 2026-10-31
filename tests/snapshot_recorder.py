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
- `example_database.query`, every set of rows, as CSV.

Each is kept as a short hash in `tests/snapshot/known.txt`. Before it is hashed, the run's temp
folders are written as `<tmp>` everywhere; in a message, printed text or report, its times and
memory addresses are written as `<time>` and `<address>` too, but never in Hive or rows, where a
changed time would be a real change. A test that makes a text the file doesn't know fails,
showing it. A run of the whole suite also fails on a hash no test made: something a user saw
is gone.

Writing the file again is a deliberate act, which its commit message says, never part of a
refactor: run the whole suite, every test passing, with `SNAPSHOT_WRITE=1` set. A run of part
of the suite, or one with a failure, is refused, since it would write only what it made.
"""

from __future__ import annotations

import builtins
import functools
import hashlib
import os
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pandas as pd

KNOWN = Path(__file__).resolve().parent / "snapshot" / "known.txt"
TESTS = Path(__file__).resolve().parent
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
    """The short hash known.txt keeps for one text."""
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
        (toolbox("example_database"), "query", "rows", rows_as_text),
    ):
        original = getattr(module, name)
        replace_everywhere(original, recorded_function(kind, original, text_of))
    toolbox("running").print = recorded_print
    record_each_printed(toolbox("project").ProjectReport)
    record_each_printed(toolbox("tables").Verdict)


def known_hashes() -> set[str]:
    """The hashes known.txt holds."""
    if not KNOWN.exists():
        return set()
    return set(KNOWN.read_text(encoding="utf-8").split())


def take_unknown_texts(known: set[str]) -> list[str]:
    """Take what this test made, keep each hash for the run, and give back each text known.txt
    doesn't know, with the kind of place that made it: none, when the file is being written."""
    found = []
    for kind, text in texts_made_by_this_test:
        digest = hash_of(kind, text)
        hashes_made_in_this_run.add(digest)
        if digest not in known and not WRITING:
            found.append(f"A {kind} text:\n{text_as_kept(kind, text)}")
    texts_made_by_this_test.clear()
    return found


def is_the_whole_suite(args: list[str], keyword: str, markers: str, failed: int) -> bool:
    """Whether a run read every test, and every one passed: the only run whose hashes are the
    whole snapshot."""
    every_test = all(Path(arg).resolve() == TESTS for arg in args)
    return every_test and not keyword and not markers and failed == 0


def write_known() -> None:
    """known.txt, as this run made it: one hash per line, sorted."""
    KNOWN.parent.mkdir(exist_ok=True)
    KNOWN.write_text("".join(f"{digest}\n" for digest in sorted(hashes_made_in_this_run)),
                     encoding="utf-8")
