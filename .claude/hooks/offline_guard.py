"""PreToolUse hook: no Edit, Write or NotebookEdit that would leave network code in the repo.

The Toolbox reaches nothing but the user's `send`. This works out the file's text as the edit
would leave it and judges it with `tools/offline_policy.py`, the one reader of that policy:

- **Write:** the new content.
- **Edit:** the file on disk (empty if there is none) with `old_string` replaced by
  `new_string`, every one with `replace_all` and the first without, matched as Claude Code
  matches it (LF line ends, straight quotes matching curly ones). If Claude Code would find no
  `old_string`, it refuses the Edit itself; the guard still judges `new_string` on its own.
- **NotebookEdit:** the notebook on disk with the cell replaced, inserted or deleted; if the
  notebook or the cell can't be found, the new source alone, as a code cell.

It refuses with each finding as `file:line kind: code`, and the way through. It only reads
text: it never imports or runs the code it judges, and it reaches nothing.

**Which checkout and which policy.** The session's project is `$CLAUDE_PROJECT_DIR`, or this
hook's own checkout without it. A file in one of Claude Code's worktrees in it
(`.claude/worktrees/<name>/`) is judged at its own path there, by that worktree's own
`tools/offline_policy.py`, so an `ALLOWED` entry added in a worktree counts in that worktree;
any other file in the project is judged by the project's. A `.git` found anywhere else is not a
checkout, so one planted inside the Toolbox changes nothing. A file outside the project, or in a
checkout without the policy, isn't the repo's and passes; so does a file the policy doesn't read
(another kind, or in `.scratch/` and the other folders it skips outside the Toolbox).

**The policy is judged like any other file.** An edit to `tools/offline_policy.py` is read as
maintainer code, as `tools/` is, so its allowlist can be edited, and the names and strings it
holds to look for aren't refused.

**Code that doesn't parse** (the policy's "unreadable") could hide anything the policy can't
read, so in the Toolbox and user-copied code it is refused like any finding: an edit there must
leave the file whole. Elsewhere it passes, since tools and tests may pass through a broken state
mid-change.

**When the guard itself fails** (input that isn't a call, a file it can't read, a broken
policy), it fails closed for a file in the Toolbox or user-copied code (`STRICT_FOLDERS`) of a
kind the policy reads: those reach the user, so an edit there that can't be judged is refused,
and says why. Anywhere else it fails open, saying so on stderr with exit code 1, which Claude
Code shows the user without blocking: the policy itself lives in `tools/`, and a broken policy
must not refuse the edit that fixes it. Input that isn't a call names no file, so it fails open.
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from pathlib import Path, PurePosixPath
from typing import NoReturn

from hook_io import deny, plain_line, read_hook_input

# The policy's strict folders and the kinds of file it reads, known here without it, for when
# it can't be loaded. A test holds them to `offline_policy.TOOLBOX`, `USER_COPIED` and
# `READ_FILES`.
STRICT_FOLDERS = ("composer_core", "sqlglot_composer", "spark_composer", "templates",
                  "example_projects", "worked_examples")
USER_COPIED = ("templates", "example_projects", "worked_examples")
READ_FILES = (".py", ".pyw", ".html", ".htm", ".js", ".mjs", ".ipynb")
WORKTREES = (".claude", "worktrees")

# Claude Code matches an Edit's straight quotes to curly ones in the file.
STRAIGHT_QUOTES = str.maketrans("‘’“”", "''\"\"")

# Each finding goes into Claude's context as one plain line (see hook_io), and only so many.
LONGEST_LINE = 160
MOST_FINDINGS = 20

WAY_THROUGH = (
    "The Toolbox reaches nothing but the user's `send`, and the repo's other code reaches "
    "nothing outside this computer except at the sites `tools/offline_policy.py`'s ALLOWED "
    "lists. If this site is reviewed and needed, it goes in ALLOWED with a reason, and only "
    "with the user's OK: ask them first."
)
NOTHING_ALLOWED = (
    "Users copy this folder's files into their own work, so nothing in it may reach the "
    "network, start a process or run code it builds, and `tools/offline_policy.py`'s ALLOWED "
    "doesn't apply here. The Toolbox reaches nothing but the user's `send`."
)


class CantJudge(Exception):
    """The guard can't work out or judge the file as the edit would leave it."""


def checkout_of(file: Path) -> Path | None:
    """The checkout `file` is judged in: one of Claude Code's worktrees in the session's
    project, or the project itself; None for a file outside the project."""
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).parents[2]).resolve()
    if project not in file.parents:
        return None
    parts = file.relative_to(project).parts
    if parts[:2] == WORKTREES and len(parts) > 3:
        return project.joinpath(*parts[:3])
    return project


def text_on_disk(file: Path) -> str:
    """The file's text, or "" if there is none, read as the policy reads a file."""
    try:
        return file.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    except OSError as error:
        raise CantJudge(f"it can't read {file.name} ({error.strerror or error})") from error


def edited(text: str, old: str, new: str, every: bool) -> str | None:
    """`text` with `old` replaced by `new`, as Claude Code's Edit replaces it, or None if Claude
    Code would find no `old` to replace: it reads the file with LF line ends, and matches
    straight quotes to curly ones."""
    text = text.replace("\r\n", "\n")
    if old not in text:
        start = text.translate(STRAIGHT_QUOTES).find(old.translate(STRAIGHT_QUOTES))
        if start == -1:
            return None
        old = text[start:start + len(old)]
    return text.replace(old, new) if every else text.replace(old, new, 1)


def after_edit(tool_input: dict, file: Path) -> str:
    new = tool_input.get("new_string", "")
    after = edited(text_on_disk(file), tool_input.get("old_string", ""), new,
                   bool(tool_input.get("replace_all")))
    return textwrap.dedent(new) if after is None else after


def after_notebook_edit(tool_input: dict, file: Path) -> str:
    """The notebook as the edit would leave it, or the new cell alone when the notebook or the
    cell can't be found."""
    source, kind = tool_input.get("new_source", ""), tool_input.get("cell_type")
    new_cell = {"cell_type": kind or "code", "source": source}
    mode = tool_input.get("edit_mode") or "replace"
    try:
        notebook = json.loads(text_on_disk(file))
        cells = notebook["cells"]
        at = cell_index(cells, tool_input.get("cell_id"))
        if mode == "delete":
            del cells[at]
        elif mode == "insert":
            cells.insert(at + 1, new_cell)
        else:
            cells[at] = {**cells[at], "source": source,
                         "cell_type": kind or cells[at]["cell_type"]}
    except (ValueError, LookupError, TypeError):
        return json.dumps({"cells": [new_cell]})
    return json.dumps(notebook)


def cell_index(cells: list, cell_id: str | None) -> int:
    """Where the cell is: by its id, or as `cell-N`; -1 for none given, so that an insert goes
    before the first."""
    if cell_id is None:
        return -1
    for at, cell in enumerate(cells):
        if cell.get("id") == cell_id:
            return at
    numbered = re.fullmatch(r"cell-(\d+)", cell_id)
    if numbered and int(numbered.group(1)) < len(cells):
        return int(numbered.group(1))
    raise KeyError(cell_id)


def text_after(tool: str, tool_input: dict, file: Path) -> str:
    if tool == "NotebookEdit":
        return after_notebook_edit(tool_input, file)
    if tool == "Edit":
        return after_edit(tool_input, file)
    return tool_input.get("content", "")


def findings(tool: str, tool_input: dict, file: Path, root: Path) -> list[str]:
    """Each finding in the file as the edit would leave it, as `file:line kind: code`."""
    sys.path.insert(0, str(root / "tools"))
    try:
        import offline_policy
    except Exception as error:
        raise CantJudge(f"its policy, tools/offline_policy.py, doesn't load ({error!r})") \
            from error
    if not offline_policy.is_read(root, file):
        return []
    relative = file.relative_to(root).as_posix()
    strict = offline_policy.scope_of(relative) != "maintainer"
    found = offline_policy.findings_in(text_after(tool, tool_input, file), relative)
    return [str(finding) for finding in found if strict or finding.kind != "unreadable"]


def why_refused(relative: PurePosixPath, found: list[str]) -> str:
    shown = [plain_line(finding, LONGEST_LINE) for finding in found[:MOST_FINDINGS]]
    if len(found) > MOST_FINDINGS:
        shown.append(f"... and {len(found) - MOST_FINDINGS} more")
    way = NOTHING_ALLOWED if relative.parts[0] in USER_COPIED else WAY_THROUGH
    return (f"The offline guard refuses this edit: it would leave code in "
            f"{plain_line(str(relative), LONGEST_LINE)} that tools/offline_policy.py refuses.\n"
            + "\n".join(shown) + "\n" + way)


def is_strict(relative: PurePosixPath) -> bool:
    """A file in the Toolbox or user-copied code, of a kind the policy reads."""
    return relative.parts[0] in STRICT_FOLDERS and relative.name.lower().endswith(READ_FILES)


def let_through(why: str) -> NoReturn:
    print(f"The offline guard let this edit through unjudged: {plain_line(why, LONGEST_LINE)}",
          file=sys.stderr)
    sys.exit(1)


def main() -> None:
    try:
        hook = read_hook_input()
        tool, tool_input = hook["tool_name"], hook["tool_input"]
        named = tool_input.get("file_path") or tool_input["notebook_path"]
        file = (Path(hook.get("cwd") or ".") / named).resolve()
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        let_through(f"its input isn't a file tool's call ({error!r})")
    root = checkout_of(file)
    if root is None or not (root / "tools" / "offline_policy.py").is_file():
        return
    relative = PurePosixPath(file.relative_to(root).as_posix())
    try:
        found = findings(tool, tool_input, file, root)
    except Exception as error:
        why = f"it couldn't judge the edit to {relative}: {error}"
        if is_strict(relative):
            deny(f"The offline guard refuses this edit, since {plain_line(why, LONGEST_LINE)}. "
                 "This folder reaches the user, so an edit the guard can't judge waits until "
                 "what stops it is fixed: the file, or tools/offline_policy.py.")
            return
        let_through(why)
    if found:
        deny(why_refused(relative, found))


if __name__ == "__main__":
    main()
