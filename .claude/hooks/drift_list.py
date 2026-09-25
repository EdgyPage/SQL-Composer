"""What the drift hooks share: which commits need a drift review, and what `.scratch/drift.md` says.

`.scratch/drift.md` is tracked. Its item lines look like

    - [ ] D3 | 1a2b3c4 | glossary | `first_look` uses "sample", which the glossary avoids

and a closed one has `[x]`. Its "Reviewed commits" section has one line per review:

    - 1a2b3c4: D3, D4
    - 5d6e7f8: clean

Which session asked for which review is not tracked: it lives in a file inside the clone's
`.git` folder, one `<commit> <session id>` line per request.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

DRIFT_LIST = Path(".scratch") / "drift.md"
REVIEWER_BRIEF = Path(".claude") / "hooks" / "drift-reviewer.md"
REQUESTS_FILE = "sql-composer-drift-requests"

WATCHED_FOLDERS = ("sql_composer/", "docs/")
WATCHED_FILES = frozenset({"CONTEXT.md", "CLAUDE.md", "requirements-dev.txt"})

MAKES_A_COMMIT = re.compile(r"\bgit\b[^;&|\n]*\b(commit|merge|cherry-pick|revert|am|rebase)\b")
OPEN_ITEM = re.compile(r"^- \[ \] (D\d+) \| ([0-9a-f]{7,40}) \|", re.MULTILINE)
REVIEWED = re.compile(r"^- ([0-9a-f]{7,40}):", re.MULTILINE)


def read_hook_input() -> dict:
    return json.loads(sys.stdin.read() or "{}")


def git(folder: str | Path, *args: str) -> str:
    """Run git in `folder` and return its output, or "" if git fails there."""
    done = subprocess.run(
        ["git", "-C", str(folder), *args], capture_output=True, text=True, encoding="utf-8"
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def needs_review(changed_paths: list[str], message: str) -> list[str]:
    """The watched paths a commit touches, or ["No-drift"] for a commit closing a false alarm."""
    watched = [
        path
        for path in changed_paths
        if path in WATCHED_FILES or path.startswith(WATCHED_FOLDERS)
    ]
    if not watched and "No-drift:" in message:
        return ["No-drift"]
    return watched


def same_commit(a: str, b: str) -> bool:
    shorter = min(len(a), len(b))
    return shorter >= 7 and a[:shorter] == b[:shorter]


def open_items(drift_text: str) -> list[tuple[str, str]]:
    """Every open item as (item, commit)."""
    return OPEN_ITEM.findall(drift_text)


def reviewed_commits(drift_text: str) -> list[str]:
    return REVIEWED.findall(drift_text)


def requests_path(repo: str | Path) -> Path | None:
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / REQUESTS_FILE if common else None


def read_requests(repo: str | Path) -> list[tuple[str, str]]:
    """Every review requested in this clone, as (commit, session id)."""
    path = requests_path(repo)
    if path is None or not path.exists():
        return []
    pairs = (line.split() for line in path.read_text(encoding="utf-8").splitlines())
    return [(pair[0], pair[1]) for pair in pairs if len(pair) == 2]


def add_request(repo: str | Path, commit: str, session_id: str) -> None:
    path = requests_path(repo)
    if path is not None:
        with path.open("a", encoding="utf-8") as requests:
            requests.write(f"{commit} {session_id}\n")
