"""What the drift hooks share: which commits need a drift review, and what `.scratch/drift.md` says.

`.scratch/drift.md` is tracked. Its item lines look like

    - [ ] D3 | 1a2b3c4 | glossary | `first_look` uses "sample", which the glossary avoids

and a closed one has `[x]`. Its "Reviewed commits" section has one line per review:

    - 1a2b3c4: D3, D4
    - 5d6e7f8: clean

A review runs before a push, over every commit the push sends (`drift_gate.py`).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

DRIFT_LIST = Path(".scratch") / "drift.md"
REVIEWER_BRIEF = Path(".claude") / "hooks" / "drift-reviewer.md"
# What the session runs when a drift review finishes, from the tokens and seconds the subagent
# reported (eval-system ticket 08). `eval_runs record` is the ledger's one writer.
RECORD_RUN = (
    '.venv/Scripts/python tools/eval_runs.py record --pipeline maintainer --role maintainer '
    '--task drift-reviewer --round <commit> --commit <commit> --arm - --model sonnet '
    '--tokens <tokens> --seconds <seconds> --result "<clean or opened D<n> ...>"'
)

WATCHED_FOLDERS = ("sqlglot_composer/", "worked_examples/", "example_projects/", "copilot/",
                   "docs/")
WATCHED_FILES = frozenset({"CHANGES.md", "CONTEXT.md", "CLAUDE.md", "requirements-dev.txt",
                           "requirements.txt"})

# git, its own options (such as -C <folder>, -c <name>=<value> or --git-dir <folder>, quoted
# or not), then a subcommand that makes a commit. `git log --grep=revert` names no such
# subcommand, and neither do merge-base or commit-tree.
_ARGUMENT = r"""("[^"]*"|'[^']*'|\S+)"""
MAKES_A_COMMIT = re.compile(
    rf"(?<![\w.])git(\s+(-[Cc]|--git-dir|--work-tree|--namespace)\s+{_ARGUMENT}"
    rf"|\s+--?[\w-]+(={_ARGUMENT})?)*\s+"
    r"(commit|merge|pull|cherry-pick|revert|am|rebase)(?![\w-])"
)
# git, its own options, then `push`: what the drift gate waits on.
PUSHES = re.compile(
    rf"(?<![\w.])git(\s+(-[Cc]|--git-dir|--work-tree|--namespace)\s+{_ARGUMENT}"
    rf"|\s+--?[\w-]+(={_ARGUMENT})?)*\s+push(?![\w-])"
)
OPEN_ITEM = re.compile(r"^- \[ \] (D\d+) \| ([0-9a-f]{7,40}) \|", re.MULTILINE)
REVIEWED = re.compile(r"^- ([0-9a-f]{7,40}):", re.MULTILINE)


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


def new_commits(repo: str | Path) -> list[str]:
    """The commits on this branch that its upstream hasn't got, oldest first, following each
    merge's first parent; HEAD alone when the branch has no upstream."""
    if git(repo, "rev-parse", "--abbrev-ref", "@{upstream}"):
        return git(repo, "rev-list", "--reverse", "--first-parent", "@{upstream}..HEAD").split()
    head = git(repo, "rev-parse", "HEAD")
    return [head] if head else []


def changed_paths(repo: str | Path, commit: str) -> list[str]:
    """The files a commit changes against its first parent, which for a merge is what was
    merged in; for the first commit, every file it adds."""
    changed = git(repo, "diff", "--name-only", f"{commit}^1", commit)
    if not changed and not git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^1"):
        changed = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit)
    return changed.splitlines()


def same_commit(a: str, b: str) -> bool:
    shorter = min(len(a), len(b))
    return shorter >= 7 and a[:shorter] == b[:shorter]


def open_items(drift_text: str) -> list[tuple[str, str]]:
    """Every open item as (item, commit)."""
    return OPEN_ITEM.findall(drift_text)


def reviewed_commits(drift_text: str) -> list[str]:
    return REVIEWED.findall(drift_text)
