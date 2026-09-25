"""PreToolUse hook: no commits and no file edits while `main` is checked out.

`main` is the Clean branch, written only by the export script. This refuses Claude's Edit,
Write and NotebookEdit on a file in a checkout of `main`, any git command that would make a
commit there, and moving `main` by hand with `git update-ref` or `git branch -f`, which is how
the export writes it. A command that only runs `tools/export_clean.py` goes through; naming the
script in a longer command excuses nothing. The user's own edits are theirs to make; this only
stops agents.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from drift_list import MAKES_A_COMMIT, git, read_hook_input

CLEAN_BRANCH = "main"
# The export script run alone, as `python tools/export_clean.py` with any path and arguments.
RUNS_THE_EXPORT = re.compile(
    r"""^\s*(python3?|py)(\.exe)?\s+["']?([^\s"';&|]*[/\\])?tools[/\\]export_clean\.py["']?"""
    r"""(\s+[^;&|<>`$\n]*)?$"""
)
# Moving `main` without checking it out, the way the export writes it.
MOVES_MAIN = re.compile(
    r"\bgit\b[^;&|\n]*\b(update-ref\b[^;&|\n]*\b(refs/heads/)?main"
    r"|branch\s+(-f|--force|-M|-C)\s+main)\b"
)
FILE_TOOLS = frozenset({"Edit", "Write", "NotebookEdit"})
SWITCHES_TO_MAIN = re.compile(r"\bgit\b[^;&|\n]*\b(checkout|switch)\s+main\b")


def branch_at(path: Path) -> str:
    folder = path if path.is_dir() else path.parent
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    return git(folder, "rev-parse", "--abbrev-ref", "HEAD")


def refusal(tool: str, tool_input: dict, cwd: str) -> str | None:
    """Why this call is refused, or None to let it through."""
    if tool in FILE_TOOLS:
        target = Path(tool_input.get("file_path") or tool_input.get("notebook_path") or cwd)
        if branch_at(target) == CLEAN_BRANCH:
            return f"{target} is in a checkout of `main`, which only the export script writes."
        return None
    command = tool_input.get("command", "")
    if RUNS_THE_EXPORT.match(command):
        return None
    if MOVES_MAIN.search(command):
        return "`main` is only moved by the export script: run `python tools/export_clean.py`."
    if not MAKES_A_COMMIT.search(command):
        return None
    if branch_at(Path(cwd)) == CLEAN_BRANCH or SWITCHES_TO_MAIN.search(command):
        return "`main` is only committed to by the export script. Commit on `dev` instead."
    return None


def main() -> None:
    hook = read_hook_input()
    why = refusal(hook.get("tool_name", ""), hook.get("tool_input", {}), hook.get("cwd", "."))
    if why:
        decision = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": why,
        }
        print(json.dumps({"hookSpecificOutput": decision}))


if __name__ == "__main__":
    main()
