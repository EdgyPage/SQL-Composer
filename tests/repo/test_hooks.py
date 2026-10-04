"""The decisions the `dev` hooks make, checked without running Claude Code.

The hooks live in `.claude/hooks/` and import each other by name, so that folder goes on
`sys.path` here the way Claude Code's `python <script>` puts it there.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

from drift_list import MAKES_A_COMMIT, needs_review, open_items, reviewed_commits  # noqa: E402
from drift_review import review_request  # noqa: E402
from drift_stop import what_blocks  # noqa: E402
from protect_main import refusal  # noqa: E402

DRIFT_TEXT = """\
# Drift

    - [ ] D3 | 1a2b3c4 | glossary | an example line, indented, never counted

## Items

- [x] D1 | aaaaaaa | docstring | closed - closed by bbbbbbb
- [ ] D2 | ccccccc | glossary | `first_look` says "sample"

## Reviewed commits

- aaaaaaa: D1
- ccccccc: D2
- ddddddd: clean
"""


def test_a_commit_command_is_recognised() -> None:
    assert MAKES_A_COMMIT.search('git commit -m "x"')
    assert MAKES_A_COMMIT.search("git -C repo merge dev")
    assert MAKES_A_COMMIT.search("git -c user.name=x cherry-pick a..b")
    assert MAKES_A_COMMIT.search("cd repo && git pull")


def test_a_command_that_only_mentions_a_commit_word_is_not_one() -> None:
    for command in ("git log --grep=revert", "git show HEAD --stat -- commit.txt",
                    "git branch --merged"):
        assert not MAKES_A_COMMIT.search(command), command
    assert not MAKES_A_COMMIT.search("git status && git log --oneline")


def test_watched_paths_need_a_review_and_tracker_commits_do_not() -> None:
    changed = ["sql_composer/tables.py", ".scratch/drift.md", "CONTEXT.md", "tests/test_x.py"]
    assert needs_review(changed, "feat: x") == ["sql_composer/tables.py", "CONTEXT.md"]
    assert needs_review([".scratch/sql-composer-v2/map.md"], "docs(wayfinder): x") == []


def test_both_editions_and_the_worked_examples_are_watched() -> None:
    changed = ["spark_composer/tables.py", "worked_examples/statements/regrouping.py",
               "tools/hive_corpus.py"]
    assert needs_review(changed, "feat: x") == ["spark_composer/tables.py",
                                                "worked_examples/statements/regrouping.py"]


def test_a_no_drift_commit_needs_a_review_even_off_the_watched_paths() -> None:
    assert needs_review(["tests/test_x.py"], "fix: x\n\nNo-drift: D2 - it was fine") == ["No-drift"]


def test_the_drift_list_is_read_without_its_examples() -> None:
    assert open_items(DRIFT_TEXT) == [("D2", "ccccccc")]
    assert reviewed_commits(DRIFT_TEXT) == ["aaaaaaa", "ccccccc", "ddddddd"]


def test_the_review_request_names_the_brief_and_the_commit() -> None:
    request = review_request("ccccccc0123456789", ["CONTEXT.md"])
    assert ".claude/hooks/drift-reviewer.md" in request
    assert "ccccccc" in request and "0123456789" not in request


def test_a_session_with_its_reviews_done_and_items_closed_may_stop() -> None:
    assert what_blocks(["aaaaaaa0000", "ddddddd"], DRIFT_TEXT) is None


def test_an_open_item_from_the_sessions_own_commit_blocks_stopping() -> None:
    why = what_blocks(["ccccccc"], DRIFT_TEXT)
    assert why is not None and "D2" in why


def test_an_unreviewed_commit_blocks_stopping() -> None:
    why = what_blocks(["eeeeeee"], DRIFT_TEXT)
    assert why is not None and "eeeeeee" in why and "D2" not in why


def test_switching_to_main_to_commit_is_refused_but_reading_is_not() -> None:
    assert refusal("Bash", {"command": "git checkout main && git commit -m x"}, str(ROOT))
    assert refusal("Bash", {"command": "git checkout -q main && git commit -m x"}, str(ROOT))
    assert refusal("Bash", {"command": "git log main"}, str(ROOT)) is None


def test_the_export_script_run_alone_goes_through() -> None:
    for command in (
        "python tools/export_clean.py",
        "python tools\\export_clean.py",
        f'python "{ROOT.as_posix()}/tools/export_clean.py"',
        "python tools/export_clean.py --preview clean",
    ):
        assert refusal("Bash", {"command": command}, str(ROOT)) is None, command


def test_naming_the_export_script_does_not_excuse_a_commit_by_hand() -> None:
    command = "git checkout main && python tools/export_clean.py && git commit -m export"
    assert refusal("Bash", {"command": command}, str(ROOT))


def test_moving_main_by_hand_is_refused() -> None:
    for command in (
        "git update-ref refs/heads/main 1a2b3c4",
        "python tools/export_clean.py; git update-ref refs/heads/main HEAD",
        "git branch -f main dev",
        "git branch main -f",
        "git fetch . dev:main",
        "git push . HEAD:refs/heads/main",
        "git checkout -B main dev",
        "git switch -C main",
        "git switch --force-create main HEAD",
        "git branch -D main",
        "git branch --delete main",
        "git branch -m main old-main",
        "git branch -m dev main",
    ):
        assert refusal("Bash", {"command": command}, str(ROOT)), command
    for command in (
        "git update-ref refs/heads/dev 1a2b3c4",
        "git update-ref refs/heads/dev main",
        "git branch -f main-old dev",
    ):
        assert refusal("Bash", {"command": command}, str(ROOT)) is None, command


# --- The review hook, run as Claude Code runs it ---------------------------------------------


def run(folder: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True,
                          check=True)
    return done.stdout.strip()


def commit(folder: Path, path: str, text: str) -> str:
    (folder / path).parent.mkdir(parents=True, exist_ok=True)
    (folder / path).write_text(text, encoding="utf-8")
    run(folder, "add", path)
    run(folder, "commit", "-q", "-m", f"change {path}")
    return run(folder, "rev-parse", "HEAD")


def a_clone_on_dev(tmp_path: Path) -> Path:
    """A clone whose dev branch has an upstream, with one commit already pushed."""
    remote, clone = tmp_path / "remote.git", tmp_path / "clone"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(remote), str(clone)], check=True,
                   capture_output=True)
    run(clone, "config", "user.email", "test@example.com")
    run(clone, "config", "user.name", "Test")
    run(clone, "checkout", "-q", "-b", "dev")
    commit(clone, "README.md", "start")
    run(clone, "push", "-q", "-u", "origin", "dev")
    return clone


def review_hook(clone: Path, command: str) -> str:
    hook = ROOT / ".claude" / "hooks" / "drift_review.py"
    given = {"tool_input": {"command": command}, "cwd": str(clone), "session_id": "test"}
    done = subprocess.run([sys.executable, str(hook)], input=json.dumps(given),
                          capture_output=True, text=True, check=True)
    if not done.stdout.strip():
        return ""
    return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]


def test_every_new_commit_of_a_rebase_is_asked_about(tmp_path) -> None:
    clone = a_clone_on_dev(tmp_path)
    first = commit(clone, "sql_composer/a.py", "a")
    commit(clone, ".scratch/notes.md", "not watched")
    second = commit(clone, "docs/b.md", "b")
    asked = review_hook(clone, "git rebase origin/dev")
    assert f"for commit {first[:7]}" in asked
    assert f"for commit {second[:7]}" in asked
    assert review_hook(clone, "git commit --amend") == ""  # each is asked about only once


def test_a_merge_is_asked_about_for_what_it_brings_in(tmp_path) -> None:
    clone = a_clone_on_dev(tmp_path)
    run(clone, "checkout", "-q", "-b", "work")
    commit(clone, "sql_composer/c.py", "c")
    run(clone, "checkout", "-q", "dev")
    run(clone, "merge", "-q", "--no-ff", "-m", "merge work", "work")
    merge = run(clone, "rev-parse", "HEAD")
    asked = review_hook(clone, "git merge --no-ff work")
    assert f"Commit {merge[:7]} touches sql_composer/c.py" in asked


def test_a_command_that_makes_no_commit_asks_for_nothing(tmp_path) -> None:
    clone = a_clone_on_dev(tmp_path)
    commit(clone, "sql_composer/a.py", "a")
    assert review_hook(clone, "git log --grep=revert") == ""
