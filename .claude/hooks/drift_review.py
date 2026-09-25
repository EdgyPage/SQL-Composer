"""PostToolUse hook: after a commit that touches watched paths, ask the session for a drift review.

The hook only asks. It records `<commit> <session id>` inside `.git`, and tells the session to
start a subagent on the reviewer's brief. The review itself happens in that subagent, which
writes to `.scratch/drift.md`.
"""

from __future__ import annotations

import json

from drift_list import (
    MAKES_A_COMMIT,
    REVIEWER_BRIEF,
    add_request,
    git,
    needs_review,
    read_hook_input,
    read_requests,
    same_commit,
)

def review_request(commit: str, watched: list[str]) -> str:
    touched = ", ".join(watched)
    return (
        f"Commit {commit[:7]} touches {touched}, so it needs a drift review. Start a subagent "
        f"now, before other work, with this prompt: \"Read {REVIEWER_BRIEF.as_posix()} and "
        f"follow it for commit {commit[:7]}.\" Then fix any item it opens as your next commits."
    )


def main() -> None:
    hook = read_hook_input()
    if not MAKES_A_COMMIT.search(hook.get("tool_input", {}).get("command", "")):
        return
    repo = hook.get("cwd", ".")
    commit = git(repo, "rev-parse", "HEAD")
    if not commit or git(repo, "rev-parse", "--abbrev-ref", "HEAD") != "dev":
        return
    if any(same_commit(commit, asked) for asked, _ in read_requests(repo)):
        return
    changed = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit)
    watched = needs_review(changed.splitlines(), git(repo, "log", "-1", "--format=%B", commit))
    if not watched:
        return
    add_request(repo, commit, hook.get("session_id", "unknown"))
    context = {"hookEventName": "PostToolUse", "additionalContext": review_request(commit, watched)}
    print(json.dumps({"hookSpecificOutput": context}))


if __name__ == "__main__":
    main()
