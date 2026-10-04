"""PostToolUse hook: after a commit that touches watched paths, ask the session for a drift review.

The hook only asks, for each new commit on dev that touches a watched path: a merge, a rebase
or a cherry-pick may make several. It records `<commit> <session id>` inside `.git`, and tells
the session to start a subagent on the reviewer's brief. The review itself happens in that
subagent, which writes to `.scratch/drift.md`.
"""

from __future__ import annotations

import json
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


def review_request(commit: str, watched: list[str]) -> str:
    touched = ", ".join(watched)
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
