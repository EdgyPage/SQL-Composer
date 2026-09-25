"""Stop hook: a session can't end while its drift reviews are unrun or its items are open.

It blocks once. A second stop in a row (`stop_hook_active`) goes through, so the session can
end its turn to ask the user something, such as whether to raise the Toolbox version.
"""

from __future__ import annotations

import json
from pathlib import Path

from drift_list import (
    DRIFT_LIST,
    REVIEWER_BRIEF,
    git,
    open_items,
    read_hook_input,
    read_requests,
    reviewed_commits,
    same_commit,
)


def what_blocks(my_commits: list[str], drift_text: str) -> str | None:
    """Why this session can't stop yet, or None if it can."""
    reviewed = reviewed_commits(drift_text)
    unreviewed = [
        commit[:7]
        for commit in my_commits
        if not any(same_commit(commit, done) for done in reviewed)
    ]
    still_open = [
        item
        for item, commit in open_items(drift_text)
        if any(same_commit(commit, mine) for mine in my_commits)
    ]
    reasons = []
    if unreviewed:
        reasons.append(
            f"Commits {', '.join(unreviewed)} still need a drift review: start a subagent on "
            f"{REVIEWER_BRIEF.as_posix()} for each."
        )
    if still_open:
        reasons.append(
            f"Drift items {', '.join(still_open)} from your commits are still open in "
            f"{DRIFT_LIST.as_posix()}: fix them, or close a false alarm with a `No-drift:` line."
        )
    return " ".join(reasons) or None


def main() -> None:
    hook = read_hook_input()
    if hook.get("stop_hook_active"):
        return
    repo = git(hook.get("cwd", "."), "rev-parse", "--show-toplevel")
    if not repo:
        return
    session = hook.get("session_id", "")
    my_commits = [commit for commit, asker in read_requests(repo) if asker == session]
    if not my_commits:
        return
    drift_file = Path(repo) / DRIFT_LIST
    drift_text = drift_file.read_text(encoding="utf-8") if drift_file.exists() else ""
    why = what_blocks(my_commits, drift_text)
    if why:
        print(json.dumps({"decision": "block", "reason": why}))


if __name__ == "__main__":
    main()
