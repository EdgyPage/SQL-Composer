"""The Clean-branch export, checked on `dev` without git: the same build `main` gets.

`tools/export_clean.py` builds the Clean tree in a folder. These tests build it into a
temporary folder and check what `main` would hold: the allowlist, the stamp on line 1 of every
Toolbox file, the file list in `__init__.py`, and the README with its cheat sheet.
"""

from __future__ import annotations

import ast
import datetime
import doctest
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import export_clean  # noqa: E402

import sql_composer  # noqa: E402
from conftest import EXECUTOR_READY  # noqa: E402

WHEN = datetime.datetime(2026, 10, 2, 14, 5)
STAMP = "SQL Composer 2.0, exported 2026-10-02 14:05 - generated from dev, do not edit"


def dev_toolbox_files() -> list[str]:
    return sorted(
        path.name for path in (ROOT / "sql_composer").iterdir() if path.name != "__pycache__"
    )


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("clean")
    export_clean.build(ROOT, folder, WHEN)
    return folder


@pytest.mark.parametrize("name", dev_toolbox_files())
def test_every_toolbox_file_is_stamped_on_line_1(clean: Path, name: str) -> None:
    first = (clean / "sql_composer" / name).read_text(encoding="utf-8").splitlines()[0]
    if name.endswith(".py"):
        assert first == f"# {STAMP}"
    else:
        assert first == f"<!-- {STAMP} -->"


def files_list_in(init_text: str) -> list[str]:
    found = re.search(r"^_FILES = (\[.*?\])$", init_text, re.MULTILINE | re.DOTALL)
    assert found, "__init__.py has no _FILES list"
    return ast.literal_eval(found.group(1))


def test_the_file_list_in_init_names_every_toolbox_file(clean: Path) -> None:
    init = (clean / "sql_composer" / "__init__.py").read_text(encoding="utf-8")
    assert files_list_in(init) == dev_toolbox_files()
    assert "_FILES = None" not in init


@pytest.mark.parametrize("name", dev_toolbox_files())
def test_below_the_stamp_each_file_is_devs_own(clean: Path, name: str) -> None:
    exported = (clean / "sql_composer" / name).read_text(encoding="utf-8").split("\n", 1)[1]
    dev = (ROOT / "sql_composer" / name).read_text(encoding="utf-8")
    if name == "__init__.py":
        written = re.search(r"^_FILES = \[.*?\]$", exported, re.MULTILINE | re.DOTALL).group(0)
        exported = exported.replace(written, "_FILES = None")
    assert exported == dev


def readme(clean: Path) -> str:
    return (clean / ".github" / "README.md").read_text(encoding="utf-8")


def test_the_readme_says_which_copy_it_came_with(clean: Path) -> None:
    text = readme(clean)
    assert text.splitlines()[0] == f"<!-- {STAMP} -->"
    assert "This is SQL Composer 2.0, exported 2026-10-02 14:05." in text
    assert "<!-- VERSION -->" not in text and "<!-- CHEAT SHEET -->" not in text


def test_the_cheat_sheet_has_one_line_per_public_name(clean: Path) -> None:
    lines = [line for line in readme(clean).splitlines() if re.match(r"- `\w+` [-=] ", line)]
    named = [re.match(r"- `(\w+)`", line).group(1) for line in lines]
    assert named == list(sql_composer.__all__)


def test_the_cheat_sheet_groups_names_by_file_with_their_first_lines(clean: Path) -> None:
    text = readme(clean)
    running = text.split("### `running.py`\n", 1)[1].split("###", 1)[0]
    assert "Running: turn a Statement into Hive, send it, split it by day" in running
    assert "- `to_hive` - The Hive string for a Statement, ready to send.\n" in running
    constants = text.split("### `__init__.py`\n", 1)[1]
    assert ("- `TOOLBOX_VERSION` = `'2.0'` - the feature number, raised only when a big feature "
            "lands.\n") in constants
    assert text.index("### `tables.py`") < text.index("### `clauses.py`")


def test_a_file_line_that_repeats_its_only_name_line_is_left_out(clean: Path) -> None:
    section = readme(clean).split("### `example_database.py`\n", 1)[1]
    assert section.count("The Example database: three made-up tables") == 1


def test_the_clean_tree_holds_only_the_allowlist(clean: Path) -> None:
    held = sorted(path.relative_to(clean).as_posix() for path in clean.rglob("*") if path.is_file())
    assert held == [".github/README.md"] + [f"sql_composer/{name}" for name in dev_toolbox_files()]


def test_anything_outside_the_allowlist_is_named() -> None:
    paths = ["sql_composer/tables.py", ".github/README.md", "README.md",
             "sql_composer/notes/x.py", "tools/export_clean.py", ".github/workflows/dev.yml"]
    assert export_clean.outside_allowlist(paths) == [
        "README.md", "sql_composer/notes/x.py", "tools/export_clean.py",
        ".github/workflows/dev.yml",
    ]


def test_a_toolbox_file_importing_what_work_lacks_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    tables = source / "sql_composer" / "tables.py"
    tables.write_text(tables.read_text(encoding="utf-8") + "\nimport requests  # noqa\n",
                      encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match="tables.py imports requests"):
        export_clean.build(source, tmp_path / "clean", WHEN)


DRIFT_TEXT = """\
# Drift

    - [ ] D3 | 1a2b3c4 | glossary | what drifted, and the line to change
    - [x] D2 | 1a2b3c4 | version | what drifted - closed by 9f8e7d6

## Items

- [x] D4 | 7646714 | standing-docs | closed - closed by 25b4bb8
- [ ] D5 | 0089c86 | glossary | `_check_sqlglot` says "safety check"

## Reviewed commits

- 0089c86: D5
"""


def test_only_open_items_under_the_items_heading_count() -> None:
    assert export_clean.open_drift_items(DRIFT_TEXT) == ["D5"]
    assert export_clean.open_drift_items(DRIFT_TEXT.replace("- [ ] D5", "- [x] D5")) == []


def test_a_drift_list_without_its_items_heading_is_refused() -> None:
    with pytest.raises(export_clean.ExportRefused, match="## Items"):
        export_clean.open_drift_items(DRIFT_TEXT.replace("## Items", "## Open"))


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", check=True)
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway clone-alike: a v1 `main`, and `dev` checked out holding the Toolbox."""
    for who in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{who}_NAME", "Test")
        monkeypatch.setenv(f"GIT_{who}_EMAIL", "test@example.com")
    folder = tmp_path / "repo"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "core.autocrlf", "false")
    (folder / "README.md").write_text("v1\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "v1")
    git(folder, "checkout", "-q", "-b", "dev")
    git(folder, "rm", "-q", "README.md")
    dev_copy(folder)
    (folder / ".scratch").mkdir()
    (folder / ".scratch" / "drift.md").write_text(DRIFT_TEXT.replace("- [ ] D5", "- [x] D5"))
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "dev")
    return folder


def test_the_export_commits_the_clean_tree_on_top_of_main(repo: Path) -> None:
    old_main, dev = git(repo, "rev-parse", "main"), git(repo, "rev-parse", "dev")
    new_main = export_clean.export(repo, WHEN)
    assert git(repo, "rev-parse", "main") == new_main
    assert git(repo, "rev-parse", "main~1") == old_main
    held = git(repo, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert held == [".github/README.md"] + [f"sql_composer/{name}" for name in dev_toolbox_files()]
    assert git(repo, "log", "-1", "--format=%s", "main") == (
        "SQL Composer 2.0, exported 2026-10-02 14:05")
    assert dev in git(repo, "log", "-1", "--format=%b", "main")
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "dev"
    assert git(repo, "rev-parse", "dev") == dev
    assert git(repo, "status", "--porcelain") == ""


def test_the_export_refuses_off_dev(repo: Path) -> None:
    git(repo, "checkout", "-q", "main")
    with pytest.raises(export_clean.ExportRefused, match="Check out dev"):
        export_clean.export(repo, WHEN)


def test_the_export_refuses_with_uncommitted_changes(repo: Path) -> None:
    (repo / "sql_composer" / "tables.py").write_text("# half done\n")
    with pytest.raises(export_clean.ExportRefused, match="uncommitted"):
        export_clean.export(repo, WHEN)


def test_the_export_refuses_while_a_drift_item_is_open(repo: Path) -> None:
    old_main = git(repo, "rev-parse", "main")
    (repo / ".scratch" / "drift.md").write_text(DRIFT_TEXT)
    git(repo, "commit", "-q", "-am", "drift")
    with pytest.raises(export_clean.ExportRefused, match="D5"):
        export_clean.export(repo, WHEN)
    assert git(repo, "rev-parse", "main") == old_main


def python_blocks(markdown: str) -> list[str]:
    return re.findall(r"^```python\n(.*?)^```$", markdown, re.MULTILINE | re.DOTALL)


@pytest.mark.parametrize("number", range(len(python_blocks(
    (ROOT / export_clean.README_TEMPLATE).read_text(encoding="utf-8")))))
def test_the_readme_examples_run(number: int) -> None:
    template = (ROOT / export_clean.README_TEMPLATE).read_text(encoding="utf-8")
    shared: dict = {}
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE)
    report = []
    for block in python_blocks(template)[: number + 1]:
        if not EXECUTOR_READY and "send=example_database.send" in block:
            pytest.skip("the example runs a query, which needs sqlglot 30.19.0 or newer")
        test = doctest.DocTestParser().get_doctest(block, shared, "README", None, 0)
        runner.run(test, out=report.append, clear_globs=False)
        shared = test.globs
    assert runner.failures == 0, "".join(report)


def dev_copy(folder: Path) -> Path:
    """A copy of what the build reads from `dev`, to spoil on purpose."""
    shutil.copytree(ROOT / "sql_composer", folder / "sql_composer",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (folder / "docs").mkdir()
    shutil.copy(ROOT / export_clean.README_TEMPLATE, folder / export_clean.README_TEMPLATE)
    return folder


def test_the_stamped_copy_is_imported_and_says_it_was_exported(tmp_path: Path) -> None:
    version = export_clean.build(ROOT, tmp_path / "clean", WHEN)
    assert version == "SQL Composer 2.0, exported 2026-10-02 14:05"


def test_a_toolbox_that_stops_on_import_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sql_composer" / "old_module.py").write_text('TOOLBOX_VERSION = "1.9"\n')
    with pytest.raises(export_clean.ExportRefused, match="old_module.py is from 1.9"):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_a_file_the_export_cannot_stamp_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sql_composer" / "notes.txt").write_text("scratch\n")
    with pytest.raises(export_clean.ExportRefused, match="notes.txt"):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_a_readme_template_without_its_markers_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    template = source / export_clean.README_TEMPLATE
    template.write_text(template.read_text(encoding="utf-8").replace("<!-- CHEAT SHEET -->", ""),
                        encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match="CHEAT SHEET"):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_the_export_ships_what_dev_committed_not_ignored_leftovers(repo: Path) -> None:
    (repo / ".gitignore").write_text("*.log\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore logs")
    (repo / "sql_composer" / "run.log").write_text("left behind\n")
    export_clean.export(repo, WHEN)
    assert "sql_composer/run.log" not in git(repo, "ls-tree", "-r", "--name-only", "main")


def test_the_export_refuses_while_main_is_checked_out_in_a_worktree(repo: Path) -> None:
    git(repo, "worktree", "add", "-q", str(repo.parent / "elsewhere"), "main")
    with pytest.raises(export_clean.ExportRefused, match="worktree"):
        export_clean.export(repo, WHEN)


def test_preview_builds_into_a_folder_and_commits_nothing(tmp_path: Path, capsys) -> None:
    main_before = git(ROOT, "rev-parse", "main")
    assert export_clean.main(["--preview", str(tmp_path / "preview")]) == 0
    assert (tmp_path / "preview" / ".github" / "README.md").is_file()
    assert "Nothing was committed" in capsys.readouterr().out
    assert git(ROOT, "rev-parse", "main") == main_before
