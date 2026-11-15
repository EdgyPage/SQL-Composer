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

from drift_gate import SKIP, refusal as push_refusal  # noqa: E402
from drift_list import (  # noqa: E402
    MAKES_A_COMMIT,
    PUSHES,
    needs_review,
    open_items,
    reviewed_commits,
)
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
    assert MAKES_A_COMMIT.search('git -C "a b" commit -m x')
    assert MAKES_A_COMMIT.search("git -c 'a=b c' merge x")


def test_a_command_that_only_mentions_a_commit_word_is_not_one() -> None:
    for command in ("git log --grep=revert", "git show HEAD --stat -- commit.txt",
                    "git branch --merged", "git merge-base main dev",
                    "git commit-tree HEAD^{tree}", "cat .git/commit"):
        assert not MAKES_A_COMMIT.search(command), command
    assert not MAKES_A_COMMIT.search("git status && git log --oneline")


def test_watched_paths_need_a_review_and_tracker_commits_do_not() -> None:
    changed = ["sqlglot_composer/tables.py", ".scratch/drift.md", "CONTEXT.md",
               "tests/test_x.py"]
    assert needs_review(changed, "feat: x") == ["sqlglot_composer/tables.py", "CONTEXT.md"]
    assert needs_review([".scratch/sql-composer-v2/map.md"], "docs(wayfinder): x") == []


def test_the_toolbox_and_the_worked_examples_are_watched() -> None:
    changed = ["sqlglot_composer/tables.py", "worked_examples/statements/regrouping.py",
               "tools/hive_corpus.py"]
    assert needs_review(changed, "feat: x") == ["sqlglot_composer/tables.py",
                                                "worked_examples/statements/regrouping.py"]


def test_a_no_drift_commit_needs_a_review_even_off_the_watched_paths() -> None:
    assert needs_review(["tests/test_x.py"],
                        "fix: x\n\nNo-drift: D2 - it was fine") == ["No-drift"]


def test_the_drift_list_is_read_without_its_examples() -> None:
    assert open_items(DRIFT_TEXT) == [("D2", "ccccccc")]
    assert reviewed_commits(DRIFT_TEXT) == ["aaaaaaa", "ccccccc", "ddddddd"]


def test_a_push_command_is_recognised_and_other_commands_are_not() -> None:
    for command in ("git push", "git -C repo push origin dev", "cd x && git push -u origin dev",
                    'git -C "a b" push', "DRIFT_REVIEW=skip git push"):
        assert PUSHES.search(command), command
    for command in ("git log --grep=push", "git stash push -m x", "git commit -m push",
                    "git status"):
        assert not PUSHES.search(command), command


def test_a_push_waits_for_one_sonnet_review_over_every_commit_it_sends() -> None:
    why = push_refusal(["aaaaaaa", "bbbbbbb"], [])
    assert why is not None and 'model "sonnet"' in why
    assert ".claude/hooks/drift-reviewer.md" in why
    assert "for commits aaaaaaa bbbbbbb." in why
    assert "tools/eval_runs.py record --pipeline maintainer" in why and "--model sonnet" in why


def test_many_commits_are_named_by_their_range() -> None:
    commits = [f"{n:07x}" for n in range(100)]
    why = push_refusal(commits, [])
    assert why is not None and f"{commits[0]}^..{commits[-1]}" in why and len(why) < 1500


def test_an_open_item_holds_a_push_back_and_nothing_left_lets_it_through() -> None:
    why = push_refusal([], ["D2"])
    assert why is not None and "D2" in why and "model" not in why
    assert push_refusal([], []) is None


def test_the_refusal_names_the_users_skip() -> None:
    assert f"{SKIP} git push" in push_refusal(["aaaaaaa"], [])


def test_switching_to_main_to_commit_is_refused_but_reading_is_not() -> None:
    assert refusal("Bash", {"command": "git checkout main && git commit -m x"}, str(ROOT))
    assert refusal("Bash", {"command": "git checkout -q main && git commit -m x"}, str(ROOT))
    for command in ("git checkout -b main-fix && git commit -m x",
                    "git switch -q main-old && git commit -m x"):
        assert refusal("Bash", {"command": command}, str(ROOT)) is None, command
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


def gate_hook(clone: Path, command: str, folder: Path | None = None) -> str:
    """What the push gate says to `command` run in `clone`, "" when it lets it through."""
    hook = ROOT / ".claude" / "hooks" / "drift_gate.py"
    given = {"tool_input": {"command": command}, "cwd": str(folder or clone)}
    done = subprocess.run([sys.executable, str(hook)], input=json.dumps(given),
                          capture_output=True, text=True, check=True)
    if not done.stdout.strip():
        return ""
    return json.loads(done.stdout)["hookSpecificOutput"]["permissionDecisionReason"]


def test_a_push_names_each_unreviewed_watched_commit_it_sends(tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    first = commit(clone, "sqlglot_composer/a.py", "a")
    unwatched = commit(clone, ".scratch/notes.md", "not watched")
    second = commit(clone, "docs/b.md", "b")
    said = gate_hook(clone, "git push")
    assert f"for commits {first[:7]} {second[:7]}." in said
    assert unwatched[:7] not in said


def test_a_push_whose_commits_are_reviewed_goes_through(tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    reviewed = commit(clone, "sqlglot_composer/a.py", "a")
    commit(clone, ".scratch/drift.md", f"## Reviewed commits\n\n- {reviewed[:7]}: clean\n")
    (clone / "docs").mkdir()
    assert gate_hook(clone, "git push", folder=clone / "docs") == ""


def test_a_merge_is_reviewed_for_what_it_brings_in(tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    run(clone, "checkout", "-q", "-b", "work")
    commit(clone, "sqlglot_composer/c.py", "c")
    run(clone, "checkout", "-q", "dev")
    run(clone, "merge", "-q", "--no-ff", "-m", "merge work", "work")
    merge = run(clone, "rev-parse", "HEAD")
    assert f"for commits {merge[:7]}." in gate_hook(clone, "git push")


def test_the_users_skip_a_command_that_pushes_nothing_and_another_branch_go_through(
        tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    commit(clone, "sqlglot_composer/a.py", "a")
    assert gate_hook(clone, f"{SKIP} git push") == ""
    assert gate_hook(clone, "git commit -m x") == ""
    run(clone, "checkout", "-q", "-b", "work")
    assert gate_hook(clone, "git push -u origin work") == ""


def test_nothing_new_on_top_of_the_upstream_lets_a_push_through(tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    commit(clone, "sqlglot_composer/a.py", "a")
    run(clone, "push", "-q")
    assert gate_hook(clone, "git push") == ""


def test_protect_main_refuses_a_commit_on_main_when_run_as_a_hook(tmp_path: Path) -> None:
    clone = a_clone_on_dev(tmp_path)
    run(clone, "checkout", "-q", "-b", "main")
    hook = ROOT / ".claude" / "hooks" / "protect_main.py"
    given = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"},
             "cwd": str(clone)}
    done = subprocess.run([sys.executable, str(hook)], input=json.dumps(given),
                          capture_output=True, text=True, check=True)
    assert json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
