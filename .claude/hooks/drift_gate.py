"""PreToolUse hook: no push of dev while a commit it pushes has had no drift review.

A drift review runs once, when a session's planned work is done, over every commit the push
would send that touches a watched path: one subagent on Sonnet for all of them, not one a
commit (the user, 2026-11-14). So this hook asks nothing after a commit; it refuses a
`git push` from dev while any such commit has no line under "Reviewed commits" in
`.scratch/drift.md`, or any item there is open, and says what to run.

The user may skip the review for a small push: `DRIFT_REVIEW=skip git push ...` goes through,
and the commits it sends stay unreviewed. The export to `main` refuses on its own while an
item is open.
"""

from __future__ import annotations

from pathlib import Path

from drift_list import (
    DRIFT_LIST,
    PUSHES,
    RECORD_RUN,
    REVIEWER_BRIEF,
    changed_paths,
    git,
    needs_review,
    new_commits,
    open_items,
    reviewed_commits,
    same_commit,
)
from hook_io import deny, read_hook_input

SKIP = "DRIFT_REVIEW=skip"
# The most commits a refusal names one by one; more are given as their range.
MOST_NAMED = 40


def unreviewed(repo: str | Path, drift_text: str) -> list[str]:
    """Each commit the push would send, oldest first, that touches a watched path and has no
    review line yet."""
    reviewed = reviewed_commits(drift_text)
    found = []
    for commit in new_commits(repo):
        if any(same_commit(commit, done) for done in reviewed):
            continue
        message = git(repo, "log", "-1", "--format=%B", commit)
        if needs_review(changed_paths(repo, commit), message):
            found.append(commit[:7])
    return found


def refusal(commits: list[str], items: list[str]) -> str | None:
    """Why the push waits, and what to run, or None to let it through."""
    reasons = []
    if commits:
        named = " ".join(commits)
        if len(commits) > MOST_NAMED:
            named = (f"{commits[0]}^..{commits[-1]} (each of the {len(commits)} that touches "
                     "a watched path)")
        reasons.append(
            f"Before this push, run one drift review over the {len(commits)} commit(s) it "
            f"sends that touch watched paths: one subagent on Sonnet (model \"sonnet\") with "
            f"the prompt \"Read {REVIEWER_BRIEF.as_posix()} and follow it for commits "
            f"{named}.\" "
            f"Fix any item it opens as your next commits, then push. When it finishes, record "
            f"its run from its reported tokens and seconds, with <commit> its last commit: "
            f"{RECORD_RUN}")
    if items:
        reasons.append(
            f"Drift items {', '.join(items)} are open in {DRIFT_LIST.as_posix()}: fix them, or "
            "close a false alarm with a `No-drift:` line.")
    if not reasons:
        return None
    reasons.append(f"Only if the user said to skip the review for this push: {SKIP} git "
                   "push ...")
    return " ".join(reasons)


def main() -> None:
    hook = read_hook_input()
    command = str(hook.get("tool_input", {}).get("command", ""))
    if not PUSHES.search(command) or SKIP in command:
        return
    repo = git(hook.get("cwd", "."), "rev-parse", "--show-toplevel")
    if not repo or git(repo, "rev-parse", "--abbrev-ref", "HEAD") != "dev":
        return
    drift_file = Path(repo) / DRIFT_LIST
    drift_text = drift_file.read_text(encoding="utf-8") if drift_file.exists() else ""
    why = refusal(unreviewed(repo, drift_text), [item for item, _ in open_items(drift_text)])
    if why:
        deny(why)


if __name__ == "__main__":
    main()
