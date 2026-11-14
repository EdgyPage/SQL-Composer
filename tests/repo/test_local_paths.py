"""No tracked file holds a local path or a personal detail (evaluation system, ticket 02).

`tools/local_paths.py` is the one reader of that rule: this tests it with a made-up user, then
reads every file git tracks with it, as the user's own name on this computer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

import export_clean  # noqa: E402
import local_paths  # noqa: E402
from drift_list import git  # noqa: E402

NAMES = ("zorbax",)


def kinds(text: str, names: tuple[str, ...] = NAMES) -> list[str]:
    """The kind of each finding: `user path`, `work folder`, `email` or `user's folder name`."""
    return [finding.split(" ", 1)[1].split(":")[0]
            for finding in local_paths.findings_in(text, "x.md", names)]


@pytest.mark.parametrize("path", [
    "C:\\Users\\jo\\Code\\x.py", "C:/Users/jo/Code/x.py", "/c/Users/jo/Code/x.py",
    "/home/jo/code/x.py", "/Users/jo/code/x.py", "c:\\users\\jo\\x", "C:\\\\Users\\\\jo\\\\x",
])
def test_an_absolute_user_path_is_found(path: str) -> None:
    assert kinds(f"see `{path}` for it") == ["user path"]


@pytest.mark.parametrize("path", [
    "C:\\Users\\<name>\\x", "/home/<user folder>/x", "/home/$USER/x",
    "C:\\Users\\%USERNAME%\\x",
    "/home/user/x", "code/x", "src/Users/x", "xhome/a",
])
def test_a_placeholder_or_a_relative_path_is_not(path: str) -> None:
    assert kinds(path) == []


def test_a_work_folder_is_found_on_top_of_the_user_path() -> None:
    text = "C:\\Users\\jo\\AppData\\Local\\Temp\\claude\\abc\\scratchpad\\x"
    assert kinds(text) == ["user path", "work folder"]


@pytest.mark.parametrize("text", [
    "AppData/Roaming/x", "AppData\\Local\\x", "/tmp/Temp/claude/x", "in ...\\scratchpad\\t1\\",
    "<home>/scratchpad/venv",
])
def test_an_appdata_temp_or_scratchpad_path_is_found(text: str) -> None:
    assert kinds(text) == ["work folder"]


def test_an_email_is_found_but_an_example_one_is_not() -> None:
    assert kinds("write to jo.smith@corp.co.uk now") == ["email"]
    for text in ("a@example.com", "noreply@anthropic.com", "@decorator", "user@host",
                 "a @ b.com", "pandas@2.0"):
        assert kinds(text) == [], text


def test_the_users_folder_name_is_found_as_a_word_and_not_inside_another() -> None:
    assert kinds("by Zorbax here") == ["user's folder name"]
    assert kinds("the zorbaxian way") == []
    assert kinds("zorbax-things") == []


def test_every_finding_names_the_file_and_line() -> None:
    found = local_paths.findings_in("fine\nsee C:/Users/jo/x\n", "docs/a.md", NAMES)
    assert found == ["docs/a.md:2 user path: C:/Users/jo"]


@pytest.mark.parametrize("here", [
    "C:/Users/zorbax/Code and Repos/SQL-Composer/tools/local_paths.py",
    "/home/zorbax/code/repo/tools/local_paths.py",
    "/c/Users/zorbax/repo/.claude/worktrees/a/tools/local_paths.py",
])
def test_the_name_is_read_at_run_time_from_where_the_repo_lies(here: str) -> None:
    assert local_paths.own_names(Path(here)) == ("zorbax",)


def test_a_repo_outside_a_users_folder_or_under_a_short_name_gives_no_name() -> None:
    assert local_paths.own_names(Path("/srv/ci/repo/tools/local_paths.py")) == ()
    assert local_paths.own_names(Path("/home/jo/repo/tools/local_paths.py")) == ()
    assert local_paths.own_names(Path("/home")) == ()


def test_this_computers_user_is_looked_for_in_every_file_without_being_named_in_the_repo(
        ) -> None:
    names = local_paths.own_names()
    assert local_paths.findings_in(f"by {' '.join(names)}", "x.md") or not names
    source = (ROOT / "tools" / "local_paths.py").read_text(encoding="utf-8")
    assert all(name.lower() not in source.lower() for name in names)


def test_a_file_that_is_not_text_is_not_read() -> None:
    assert local_paths.scan_files([("a.xlsx", b"\xff\xfeC:/Users/jo/x")], NAMES) == []


def test_a_file_that_names_the_patterns_to_check_for_them_is_not_read() -> None:
    text = b"C:/Users/jo/x"
    assert local_paths.scan_files([("tests/repo/test_local_paths.py", text)], NAMES) == []
    assert local_paths.scan_files([("tests/repo/test_x.py", text)], NAMES)


def test_the_allowlist_names_files_that_exist() -> None:
    for path in local_paths.NAMES_THE_PATTERNS:
        assert (ROOT / path).is_file(), path


def test_a_tree_is_read_without_its_git_folder(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "x").write_text("C:/Users/jo/x", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("ok\nC:/Users/jo/x", encoding="utf-8")
    assert local_paths.scan_tree(tmp_path, NAMES) == ["docs/a.md:2 user path: C:/Users/jo"]


def test_the_command_line_refuses_a_tree_and_passes_a_clean_one(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "a.md").write_text("fine", encoding="utf-8")
    assert local_paths.main(["--tree", str(tmp_path)]) == 0
    (tmp_path / "b.md").write_text("see zorbax@corp.co", encoding="utf-8")
    assert local_paths.main(["--tree", str(tmp_path)]) == 1
    assert "b.md:1 email" in capsys.readouterr().err


def test_the_refusal_lists_some_findings_and_counts_the_rest() -> None:
    found = [f"a.md:{number} email: x" for number in range(30)]
    text = local_paths.refusal(found, shown=3)
    assert "30 place(s)" in text and "a.md:2 email" in text and "27 more" in text
    assert ".eval-local/" in text


def test_the_export_refuses_a_clean_tree_holding_a_local_path(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("fine", encoding="utf-8")
    export_clean.check_local_paths(tmp_path)
    (tmp_path / "docs" / "b.md").write_text("C:/Users/jo/x", encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match="docs/b.md:1 user path"):
        export_clean.check_local_paths(tmp_path)


def test_the_export_runs_the_check_on_the_tree_it_builds() -> None:
    source = (ROOT / "tools" / "export_clean.py").read_text(encoding="utf-8")
    build = source[source.index("def build("):source.index("def git(")]
    assert "check_local_paths(into)" in build


def test_no_tracked_file_holds_a_local_path_or_a_personal_detail() -> None:
    tracked = [name for name in git(ROOT, "ls-files", "-z").split("\0") if name]
    files = [(name, (ROOT / name).read_bytes()) for name in tracked if (ROOT / name).is_file()]
    found = local_paths.scan_files(files)
    assert not found, local_paths.refusal(found)


def test_the_local_folder_is_git_ignored() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".eval-local/" in ignored
