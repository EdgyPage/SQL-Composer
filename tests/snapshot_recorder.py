"""The snapshot of what the Toolbox shows its user, held while Toolbox 8.0's refactor runs.

Phase 2 changes nothing a user sees: no Hive, no refusal or warning message, no report a
Project action prints, no rows the Example database gives. The suite pins much of that, but not
all, so every test also records what the Toolbox makes at the four places it makes it:

- `_four_part_message`, every refusal and warning message;
- `writing.sql_text`, every Hive string, which `show_hive` prints too (it reads its caller's
  variable names from the calling frame, so it isn't wrapped itself);
- `ProjectReport`, every Project action's report;
- `example_database.query`, every set of rows, as CSV.

Each is kept as a short hash in `tests/snapshot/known.txt`, after the run's own temp folders,
times and memory addresses are written as `<tmp>`, `<time>` and `<address>`. A test that makes
one the file doesn't know fails, naming it: the refactor changed something a user sees.

Writing the file again is a deliberate act, which its commit message says, never part of a
refactor: run the whole suite with `SNAPSHOT_WRITE=1` set, and the file becomes what that run
made.
"""

from __future__ import annotations

import functools
import hashlib
import os
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

KNOWN = Path(__file__).resolve().parent / "snapshot" / "known.txt"
WRITING = os.environ.get("SNAPSHOT_WRITE") == "1"
# A time as the Toolbox writes one: 2026-10-30 17:51, or 20261030-175142 in a folder's name.
TIME = re.compile(r"\d{4}-\d{2}-\d{2}[ T_]\d{2}[:\-.]\d{2}([:\-.]\d{2}(\.\d+)?)?"
                  r"|\b\d{8}-\d{6}\b")
ADDRESS = re.compile(r"0x[0-9a-fA-F]+")

made: list[tuple[str, str]] = []
made_in_the_whole_run: set[str] = set()
temp_folders: list[str] = []


def plain_text(text: str) -> str:
    """`text` with what changes from run to run written as a placeholder."""
    for folder in temp_folders:
        for spelling in (folder, folder.replace("\\", "/"), folder.replace("\\", "\\\\")):
            text = text.replace(spelling, "<tmp>")
    text = TIME.sub("<time>", text)
    return ADDRESS.sub("<address>", text)


def hash_of(text: str) -> str:
    """The short hash known.txt keeps for one text."""
    return hashlib.sha256(plain_text(text).encode("utf-8")).hexdigest()[:20]


def recording(where: str, function: Callable[..., object],
              text_of: Callable[[object], str]) -> Callable[..., object]:
    """`function`, recording the text of what it returns, by the place it was made."""
    @functools.wraps(function)
    def recorded(*args: object, **kwargs: object) -> object:
        value = function(*args, **kwargs)
        made.append((where, text_of(value)))
        return value
    return recorded


def rows_as_text(rows: object) -> str:
    """A DataFrame of rows as CSV, the text the snapshot keeps for it."""
    return rows.to_csv(index=False)


def replace_everywhere(original: object, replacement: object) -> None:
    """Put `replacement` wherever a loaded module holds `original`, as a name of its own: the
    Toolbox's own modules, and every test and Worked example that imported it by name."""
    for module in list(sys.modules.values()):
        if not isinstance(module, ModuleType):
            continue
        for name, value in list(vars(module).items()):
            if value is original:
                setattr(module, name, replacement)


def install(toolbox: Callable[[str], ModuleType], basetemp: str) -> None:
    """Record at each of the four places, once per run."""
    temp_folders.extend([basetemp, tempfile.gettempdir()])
    folder = toolbox("")
    places = (
        (folder, "_four_part_message", str),
        (toolbox("writing"), "sql_text", str),
        (toolbox("example_database"), "query", rows_as_text),
    )
    for module, name, text_of in places:
        original = getattr(module, name)
        replace_everywhere(original, recording(f"{module.__name__}.{name}", original, text_of))
    report = toolbox("project").ProjectReport
    original_init = report.__init__

    def recorded_init(self: object, lines: list[str]) -> None:
        original_init(self, lines)
        made.append(("ProjectReport", "\n".join(lines)))

    report.__init__ = recorded_init


def known_hashes() -> set[str]:
    """The hashes known.txt holds."""
    if not KNOWN.exists():
        return set()
    return set(KNOWN.read_text(encoding="utf-8").split())


def unknown_texts(known: set[str]) -> list[str]:
    """What this test made that known.txt doesn't know, each with the place it was made; and,
    when the file is being written, nothing, as each hash is kept for it instead."""
    found = []
    for where, text in made:
        digest = hash_of(text)
        made_in_the_whole_run.add(digest)
        if digest not in known and not WRITING:
            found.append(f"{where} made:\n{plain_text(text)}")
    made.clear()
    return found


def write_known() -> None:
    """known.txt, as this run made it: one hash per line, sorted."""
    KNOWN.parent.mkdir(exist_ok=True)
    KNOWN.write_text("".join(f"{digest}\n" for digest in sorted(made_in_the_whole_run)),
                     encoding="utf-8")
