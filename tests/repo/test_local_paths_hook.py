"""The commit hook that refuses a commit holding a local path or a personal detail, checked
without running Claude Code or git: `git` is replaced by what it would print.

The hooks live in `.claude/hooks/` and import each other by name, so that folder goes on
`sys.path` here the way Claude Code's `python <script>` puts it there.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

import local_paths_hook  # noqa: E402

NAMES = ("zorbax",)
COMMIT = 'git commit -m "x"'


def repo_with(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, files: dict[str, str],
              staged: list[str], on_disk: list[str] = ()) -> Path:
    """A folder holding `files`, and a `git` that says `staged` is in the index and `on_disk`
    is modified or untracked."""
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")

    def fake_git(folder: Path, *args: str) -> str:
        assert Path(folder) == tmp_path
        if args[0] == "diff":
            return "\0".join(staged)
        assert args[0] == "ls-files"
        return "\0".join(on_disk)

    monkeypatch.setattr(local_paths_hook, "git", fake_git)
    return tmp_path


def refusal(command: str, repo: Path) -> str | None:
    return local_paths_hook.refusal({"command": command}, str(repo), NAMES)


def test_a_commit_of_a_staged_file_with_a_local_path_is_refused(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "ok", "b.md": "x\nC:/Users/jo/x"},
                     staged=["a.md", "b.md"])
    why = refusal(COMMIT, repo)
    assert why and "b.md:2 user path" in why and ".eval-local/" in why
    assert "a.md" not in why


def test_a_clean_commit_goes_through(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "ok"}, staged=["a.md"])
    assert refusal(COMMIT, repo) is None


def test_the_users_folder_name_and_an_email_refuse_a_commit_too(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "by zorbax", "b.md": "jo@corp.co"},
                     staged=["a.md", "b.md"])
    why = refusal(COMMIT, repo)
    assert "a.md:1 user's folder name" in why and "b.md:1 email" in why


def test_a_file_outside_the_index_is_not_read_without_an_add_or_all(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "C:/Users/jo/x"}, staged=[],
                     on_disk=["a.md"])
    assert refusal(COMMIT, repo) is None


@pytest.mark.parametrize("command", [
    "git commit -am x", "git commit -a -m x", "git commit --all -m x",
    "git add . && git commit -m x", "git add -A; git commit -m x",
    "git -C . stage a.md && git commit -m x",
])
def test_a_command_that_adds_on_the_way_reads_the_files_on_disk(
        command: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "C:/Users/jo/x"}, staged=[],
                     on_disk=["a.md"])
    assert "a.md:1 user path" in refusal(command, repo)


@pytest.mark.parametrize("command", [
    "git status", "git log --grep=commit", "git add a.md", "git merge dev", "ls",
    "git commit-tree HEAD^{tree}",
])
def test_a_command_that_makes_no_commit_is_not_judged(
        command: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "C:/Users/jo/x"}, staged=["a.md"])
    assert refusal(command, repo) is None


def test_a_file_that_names_the_patterns_or_is_not_text_passes(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"tests/repo/test_local_paths.py": "C:/Users/jo/x"},
                     staged=["tests/repo/test_local_paths.py", "b.xlsx"])
    (tmp_path / "b.xlsx").write_bytes(b"\xff\xfe C:/Users/jo/x")
    assert refusal(COMMIT, repo) is None


def test_a_file_staged_and_modified_is_read_once(monkeypatch: pytest.MonkeyPatch,
                                                 tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "C:/Users/jo/x"}, staged=["a.md"],
                     on_disk=["a.md"])
    assert refusal("git add a.md && git commit -m x", repo).count("a.md:1") == 1


def test_a_deleted_file_is_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = repo_with(monkeypatch, tmp_path, {}, staged=["gone.md"])
    assert refusal(COMMIT, repo) is None


def test_a_long_list_names_the_first_and_counts_the_rest(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    names = [f"f{number}.md" for number in range(20)]
    repo = repo_with(monkeypatch, tmp_path, dict.fromkeys(names, "C:/Users/jo/x"), staged=names)
    assert "and 8 more" in refusal(COMMIT, repo)


def test_the_hook_denies_a_commit_when_run_as_a_hook(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        capsys: pytest.CaptureFixture[str]) -> None:
    repo = repo_with(monkeypatch, tmp_path, {"a.md": "C:/Users/jo/x"}, staged=["a.md"])
    monkeypatch.setattr(local_paths_hook, "read_hook_input",
                        lambda: {"tool_input": {"command": COMMIT}, "cwd": str(repo)})
    monkeypatch.setattr(local_paths_hook.local_paths, "own_names", lambda: NAMES)
    local_paths_hook.main()
    decision = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "a.md:1 user path" in decision["permissionDecisionReason"]


def test_the_hook_is_registered_for_bash_and_powershell() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    entries = [entry for entry in settings["hooks"]["PreToolUse"]
               if any("local_paths_hook.py" in hook["command"] for hook in entry["hooks"])]
    assert [entry["matcher"] for entry in entries] == ["Bash|PowerShell"]
