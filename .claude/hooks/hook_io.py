"""What every hook shares with Claude Code: reading its call, refusing one, and printing text
into the session safely."""

from __future__ import annotations

import json
import re
import sys

# Text a hook prints into the session goes as one plain line of bounded length: a file name or
# a line of code crafted with newlines or terminal codes can't read as an instruction.
UNPRINTABLE = re.compile(r"[\x00-\x1f\x7f-\x9f  ]+")


def read_hook_input() -> dict:
    """The hook's call, read as the bytes Claude Code sends: a piped stdin on Windows would
    otherwise be decoded in the local code page, not UTF-8."""
    return json.loads(sys.stdin.buffer.read() or b"{}")


def plain_line(text: str, longest: int) -> str:
    shown = UNPRINTABLE.sub(" ", text).strip()
    return shown if len(shown) <= longest else shown[:longest] + "..."


def deny(why: str) -> None:
    """Refuse the tool call a PreToolUse hook was given, saying why."""
    decision = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": why,
    }
    print(json.dumps({"hookSpecificOutput": decision}))
