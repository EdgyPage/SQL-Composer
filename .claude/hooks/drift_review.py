"""PostToolUse hook: after a commit that touches watched paths, ask the session for a drift review.

The hook only asks, for each new commit on dev that touches a watched path: a merge, a rebase
or a cherry-pick may make several. It records `<commit> <session id>` inside `.git`, and tells
the session to start a subagent on the reviewer's brief. The review itself happens in that
subagent, which writes to `.scratch/drift.md`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from drift_list import (
    DRIFT_LIST,
    MAKES_A_COMMIT,
    REVIEWER_BRIEF,
    add_request,
    changed_paths,
    git,
    needs_review,
    new_commits,
    read_hook_input,
    read_requests,
    reviewed_commits,
    same_commit,
)


# A path is printed into the session's context, so it goes as one plain line of bounded length,
# and only so many of them: a file name crafted with newlines, Unicode line breaks, direction
# marks or terminal codes can't read as an instruction, and many can't flood the context.
UNPRINTABLE = re.compile(r"[\x00-\x1f\x7f-\x9f‎‏  ‪-‮"
                         r"⁦-⁩]+")
LONGEST_PATH = 120
MOST_PATHS = 20


def plain_path(path: str) -> str:
    shown = UNPRINTABLE.sub(" ", path).strip()
    return shown if len(shown) <= LONGEST_PATH else shown[:LONGEST_PATH] + "..."


def plain_paths(paths: list[str]) -> str:
    """The first MOST_PATHS paths, each made plain, and how many more there are."""
    shown = ", ".join(plain_path(path) for path in paths[:MOST_PATHS])
    more = len(paths) - MOST_PATHS
    return f"{shown} and {more} more" if more > 0 else shown


def review_request(commit: str, watched: list[str]) -> str:
    touched = plain_paths(watched)
    return (
        f"Commit {commit[:7]} touches {touched}, so it needs a drift review. Start a subagent "
        f"now, before other work, with this prompt: \"Read {REVIEWER_BRIEF.as_posix()} and "
        f"follow it for commit {commit[:7]}.\" Then fix any item it opens as your next commits."
    )


def to_review(repo: str | Path) -> list[tuple[str, list[str]]]:
    """Each new commit that touches a watched path and wasn't asked for or reviewed yet, with
    the watched paths it touches. A rebase or a cherry-pick of several commits makes several."""
    drift_file = Path(repo) / DRIFT_LIST
    drift_text = drift_file.read_text(encoding="utf-8") if drift_file.exists() else ""
    done = [asked for asked, _ in read_requests(repo)] + reviewed_commits(drift_text)
    found = []
    for commit in new_commits(repo):
        if any(same_commit(commit, other) for other in done):
            continue
        message = git(repo, "log", "-1", "--format=%B", commit)
        watched = needs_review(changed_paths(repo, commit), message)
        if watched:
            found.append((commit, watched))
    return found


def main() -> None:
    hook = read_hook_input()
    if not MAKES_A_COMMIT.search(hook.get("tool_input", {}).get("command", "")):
        return
    repo = git(hook.get("cwd", "."), "rev-parse", "--show-toplevel")
    if not repo or git(repo, "rev-parse", "--abbrev-ref", "HEAD") != "dev":
        return
    found = to_review(repo)
    for commit, _ in found:
        add_request(repo, commit, hook.get("session_id", "unknown"))
    if found:
        asks = " ".join(review_request(commit, watched) for commit, watched in found)
        context = {"hookEventName": "PostToolUse", "additionalContext": asks}
        print(json.dumps({"hookSpecificOutput": context}))


if __name__ == "__main__":
    main()
