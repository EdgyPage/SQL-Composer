"""PreToolUse hook: no commits and no file edits while `main` is checked out.

`main` is the Clean branch, written only by the export script. This refuses Claude's Edit,
Write and NotebookEdit on a file in a checkout of `main`, and any git command that would
make a commit there. A command that runs `tools/export_clean.py` always goes through. The
user's own edits are theirs to make; this only stops agents.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from drift_list import MAKES_A_COMMIT, git, read_hook_input

CLEAN_BRANCH = "main"
EXPORT_SCRIPT = "tools/export_clean.py"
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
    if EXPORT_SCRIPT in command or not MAKES_A_COMMIT.search(command):
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
