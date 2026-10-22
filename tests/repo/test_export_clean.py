"""The Clean-branch export, checked on `dev` without git: the same build `main` gets.

`tools/export_clean.py` builds the Clean tree in a folder. These tests build it into a
temporary folder and check what `main` would hold: the allowlist, the stamp on line 1 of every
Toolbox file, the file list in `__init__.py`, the copy of the Example projects and
the Templates, and the README with its lists of how-tos and Templates and its cheat sheet; and
that a Clean tree failing one of the export's own checks is refused.
"""

from __future__ import annotations

import ast
import datetime
import doctest
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import export_clean  # noqa: E402
from test_pointers import named_paths  # noqa: E402

import sqlglot_composer  # noqa: E402

WHEN = datetime.datetime(2026, 10, 2, 14, 5)
VERSION = sqlglot_composer.TOOLBOX_VERSION
VERSION_TEXT = f"sqlglot Composer {VERSION}, exported 2026-10-02 14:05"
STAMP = f"{VERSION_TEXT} - generated from dev, do not edit"
# What main's commit and the README say the tree is: the Toolbox, at its version and time.
SHIPPED = f"sqlglot Composer {VERSION}, exported 2026-10-02 14:05"


def dev_toolbox_files() -> list[str]:
    return sorted(
        path.name for path in (ROOT / "sqlglot_composer").iterdir() if path.name != "__pycache__"
    )


@pytest.fixture(scope="module")
def clean(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("clean")
    export_clean.build(ROOT, folder, WHEN)
    return folder


@pytest.mark.parametrize("name", dev_toolbox_files())
def test_every_toolbox_file_is_stamped_on_line_1(clean: Path, name: str) -> None:
    first = (clean / "sqlglot_composer" / name).read_text(encoding="utf-8").splitlines()[0]
    if name.endswith(".py"):
        assert first == f"# {STAMP}"
    else:
        assert first == f"<!-- {STAMP} -->"


def files_list_in(init_text: str) -> list[str]:
    found = re.search(r"^_FILES = (\[.*?\])$", init_text, re.MULTILINE | re.DOTALL)
    assert found, "__init__.py has no _FILES list"
    return ast.literal_eval(found.group(1))


def test_the_file_list_in_init_names_every_toolbox_file(clean: Path) -> None:
    init = (clean / "sqlglot_composer" / "__init__.py").read_text(encoding="utf-8")
    assert files_list_in(init) == dev_toolbox_files()
    assert "_FILES = None" not in init


# The Toolbox's folder, which the export ships.
FOLDERS = ["sqlglot_composer"]


@pytest.mark.parametrize("name", [
    f"{folder}/{path.name}" for folder in FOLDERS
    for path in sorted((ROOT / folder).iterdir()) if path.name != "__pycache__"])
def test_below_the_stamp_each_file_is_devs_own(clean: Path, name: str) -> None:
    exported = (clean / name).read_text(encoding="utf-8").split("\n", 1)[1]
    dev = (ROOT / name).read_text(encoding="utf-8")
    if name.endswith("/__init__.py"):
        written = re.search(r"^_FILES = \[.*?\]$", exported, re.MULTILINE | re.DOTALL).group(0)
        exported = exported.replace(written, "_FILES = None")
    assert exported == dev


def readme(clean: Path) -> str:
    return (clean / ".github" / "README.md").read_text(encoding="utf-8")


def test_the_readme_says_which_copy_it_came_with(clean: Path) -> None:
    text = readme(clean)
    assert text.splitlines()[0] == f"<!-- {SHIPPED} - generated from dev, do not edit -->"
    assert f"This is version {VERSION}, exported 2026-10-02 14:05." in text
    assert "<!-- VERSION -->" not in text and "<!-- CHEAT SHEET -->" not in text


def test_the_cheat_sheet_has_one_line_per_public_name(clean: Path) -> None:
    lines = [line for line in readme(clean).splitlines() if re.match(r"- `\w+` [-=] ", line)]
    named = [re.match(r"- `(\w+)`", line).group(1) for line in lines]
    assert named == list(sqlglot_composer.__all__)


def test_the_cheat_sheet_groups_names_by_file_with_their_first_lines(clean: Path) -> None:
    text = readme(clean)
    running = text.split("### `running.py`\n", 1)[1].split("###", 1)[0]
    assert "Running: turn a Statement into Hive, send it, and set the load limit on rows" in running
    assert "- `to_hive` - The Hive string for a Statement, ready to send.\n" in running
    constants = text.split("### `__init__.py`\n", 1)[1]
    assert (f"- `TOOLBOX_VERSION` = `{VERSION!r}` - the feature number, raised only when a big "
            "feature lands.\n") in constants
    assert text.index("### `tables.py`") < text.index("### `clauses.py`")
    admin = text.split("### `admin.py`\n", 1)[1].split("###", 1)[0]
    assert ("- `admin.drop_table` - Drop one of your Saved tables: the DROP TABLE IF EXISTS "
            "Statement.\n") in admin
    assert [line.split("`")[1] for line in admin.splitlines() if line.startswith("- `")] == [
        f"admin.{name}" for name in sqlglot_composer.admin.__all__]


def test_the_exported_toolbox_docstring_shows_a_true_version(clean: Path) -> None:
    init = (clean / "sqlglot_composer" / "__init__.py").read_text(encoding="utf-8")
    examples = doctest.DocTestParser().get_examples(ast.get_docstring(ast.parse(init)))
    shown = next(example.want for example in examples if example.source.strip() == "VERSION")
    exported = repr(VERSION_TEXT) + "\n"
    assert doctest.OutputChecker().check_output(shown, exported, doctest.ELLIPSIS), shown


def test_a_file_line_that_repeats_its_only_name_line_is_left_out(clean: Path) -> None:
    section = readme(clean).split("### `example_database.py`\n", 1)[1]
    assert section.count("The Example database: nine made-up tables") == 1


# The folders main holds a copy of, to copy and edit, at the paths dev has them. Written out
# here, not taken from export_clean, so the tests say what main holds on their own.
COPIED = ["example_projects"]
# The copies with no comment syntax for a stamp, which main holds as dev does.
UNSTAMPED = (".ipynb", ".csv")


def copied_files(folder: str) -> list[str]:
    """Each file of one of dev's COPIED folders, as a path inside it, such as
    "starter/README.md"."""
    return sorted(path.relative_to(ROOT / folder).as_posix()
                  for path in (ROOT / folder).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def exported_files() -> list[str]:
    """Every file `main` holds, sorted: the README, the change notes, the license,
    requirements.txt, the Toolbox's files, and the Example projects."""
    toolbox = [f"{folder}/{path.name}" for folder in FOLDERS
               for path in (ROOT / folder).iterdir() if path.name != "__pycache__"]
    copies = [f"{folder}/{relative}" for folder in COPIED for relative in copied_files(folder)]
    return sorted([".github/README.md", "CHANGES.md", "LICENSE", "requirements.txt", *toolbox,
                   *copies])


def test_the_clean_tree_holds_only_the_allowlist(clean: Path) -> None:
    held = sorted(path.relative_to(clean).as_posix() for path in clean.rglob("*") if path.is_file())
    assert held == exported_files()


def test_anything_outside_the_allowlist_is_named() -> None:
    paths = ["sqlglot_composer/tables.py", ".github/README.md", "LICENSE", "requirements.txt",
             "README.md", "sqlglot_composer/notes/x.py", "tools/export_clean.py",
             ".github/workflows/dev.yml"]
    assert export_clean.outside_allowlist(paths) == [
        "README.md", "sqlglot_composer/notes/x.py", "tools/export_clean.py",
        ".github/workflows/dev.yml",
    ]


def test_the_example_projects_may_hold_anything_below_them() -> None:
    paths = ["example_projects/starter/run_pipeline.py", "example_projects/starter/a/b.py",
             "example_projects", "templates/starter/notebook_start.py",
             "worked_examples/how_to/01_start_a_project.py"]
    assert export_clean.outside_allowlist(paths) == [
        "example_projects", "templates/starter/notebook_start.py",
        "worked_examples/how_to/01_start_a_project.py"]


def test_a_toolbox_file_importing_what_work_lacks_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    writing = source / "sqlglot_composer" / "writing.py"
    writing.write_text(writing.read_text(encoding="utf-8") + "\nimport requests  # noqa\n",
                       encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused,
                       match="sqlglot_composer/writing.py imports requests"):
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
    return make_repo(tmp_path, monkeypatch, dev_copy, autocrlf="false")


def make_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, copy: Callable[..., Path],
              autocrlf: str) -> Path:
    """A v1 `main`, and `dev` checked out holding what `copy` puts in a folder."""
    for who in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{who}_NAME", "Test")
        monkeypatch.setenv(f"GIT_{who}_EMAIL", "test@example.com")
    folder = tmp_path / "repo"
    folder.mkdir()
    git(folder, "init", "-q", "-b", "main")
    git(folder, "config", "core.autocrlf", autocrlf)
    (folder / "README.md").write_text("v1\n")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "v1")
    git(folder, "checkout", "-q", "-b", "dev")
    git(folder, "rm", "-q", "README.md")
    copy(folder)
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
    assert held == exported_files()
    assert git(repo, "log", "-1", "--format=%s", "main") == SHIPPED
    assert dev in git(repo, "log", "-1", "--format=%b", "main")
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "dev"
    assert git(repo, "rev-parse", "dev") == dev
    assert git(repo, "status", "--porcelain") == ""


def test_the_export_refuses_off_dev(repo: Path) -> None:
    git(repo, "checkout", "-q", "main")
    with pytest.raises(export_clean.ExportRefused, match="Check out dev"):
        export_clean.export(repo, WHEN)


def test_the_export_refuses_with_uncommitted_changes(repo: Path) -> None:
    (repo / "sqlglot_composer" / "tables.py").write_text("# half done\n")
    with pytest.raises(export_clean.ExportRefused, match="uncommitted"):
        export_clean.export(repo, WHEN)


def test_the_export_refuses_while_a_drift_item_is_open(repo: Path) -> None:
    old_main = git(repo, "rev-parse", "main")
    (repo / ".scratch" / "drift.md").write_text(DRIFT_TEXT)
    git(repo, "commit", "-q", "-am", "drift")
    with pytest.raises(export_clean.ExportRefused, match="D5"):
        export_clean.export(repo, WHEN)
    assert git(repo, "rev-parse", "main") == old_main


def dev_copy(folder: Path) -> Path:
    """A copy of what the build reads from `dev`, the Toolbox's folder and every folder main
    holds a copy of, to spoil on purpose."""
    for name in [*FOLDERS, *COPIED]:
        shutil.copytree(ROOT / name, folder / name,
                        ignore=shutil.ignore_patterns("__pycache__"))
    (folder / "docs").mkdir()
    shutil.copy(ROOT / export_clean.README_TEMPLATE, folder / export_clean.README_TEMPLATE)
    for name in export_clean.ROOT_FILES:
        shutil.copy(ROOT / name, folder / name)
    shutil.copytree(ROOT / export_clean.HOW_TOS, folder / export_clean.HOW_TOS,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return folder


@pytest.mark.parametrize("name", ["CHANGES.md", "LICENSE", "requirements.txt"])
def test_main_holds_devs_root_files_word_for_word(clean: Path, name: str) -> None:
    # Unstamped: GitHub reads the license as is, and pip reads requirements.txt as is.
    assert (clean / name).read_text(encoding="utf-8") == (ROOT / name).read_text(encoding="utf-8")


def test_main_holds_the_mit_no_attribution_license(clean: Path) -> None:
    assert (clean / "LICENSE").read_text(encoding="utf-8").startswith("MIT No Attribution\n")


@pytest.mark.parametrize("name", ["CHANGES.md", "LICENSE", "requirements.txt"])
def test_a_dev_without_a_root_file_is_refused(tmp_path: Path, name: str) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / name).unlink()
    with pytest.raises(export_clean.ExportRefused, match=name):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_the_stamped_copy_is_imported_and_says_it_was_exported(tmp_path: Path) -> None:
    assert export_clean.build(ROOT, tmp_path / "clean", WHEN) == SHIPPED


def test_a_toolbox_that_stops_on_import_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sqlglot_composer" / "old_module.py").write_text("x = 1\n")
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    # The whole four-part stop, not only its last line.
    assert str(refused.value).startswith(
        "The stamped copy of sqlglot Composer doesn't import, so nothing was exported:\n"
        "ImportError: sqlglot_composer stopped on import:\n"
        "  What happened:  old_module.py is from another Toolbox version, and "
        "sqlglot_composer/__init__.py is from "
        f"{VERSION}.\n"
        "  Why it matters: ")
    assert "\n  Usual fix:      " in str(refused.value)


def test_a_file_the_export_cannot_stamp_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sqlglot_composer" / "notes.txt").write_text("scratch\n")
    with pytest.raises(export_clean.ExportRefused, match="sqlglot_composer/notes.txt"):
        export_clean.build(source, tmp_path / "clean", WHEN)


@pytest.mark.parametrize("marker", ["<!-- CHEAT SHEET -->", "<!-- HOW-TOS -->"])
def test_a_readme_template_without_its_markers_is_refused(tmp_path: Path, marker: str) -> None:
    source = dev_copy(tmp_path / "dev")
    template = source / export_clean.README_TEMPLATE
    template.write_text(template.read_text(encoding="utf-8").replace(marker, ""),
                        encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match=re.escape(marker)):
        export_clean.build(source, tmp_path / "clean", WHEN)


def section_of(text: str, heading: str) -> str:
    return text.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]


def test_every_path_the_readme_names_is_on_main(clean: Path) -> None:
    """Each path the README names in backticks or as a link: from main's top folder, or, for
    a name inside a folder it has just named, such as `run_pipeline.py`, somewhere on main."""
    held = export_clean.files_in(clean)
    folders = {f"{folder}/" for path in held for folder in
               ("/".join(path.split("/")[:end]) for end in range(1, path.count("/") + 1))}
    # The README is .github/README.md: a path going up one folder starts at main's top.
    missing = [path for path in (named.split("#")[0].removeprefix("../")
                                 for named in named_paths(readme(clean)))
               if not (clean / path).exists()
               and not any(f"/{one}".endswith(f"/{path}") for one in [*held, *folders])]
    assert not missing


def test_the_readme_lists_each_how_to_by_its_number_in_its_group(clean: Path) -> None:
    section = section_of(readme(clean), "The how-tos")
    numbered = re.findall(r"^(\d+)\. \[(.+)\]\(\.\./sqlglot_composer/how_to\.html#\w+\)$",
                          section, re.MULTILINE)
    assert [int(number) for number, _ in numbered] == list(range(1, 42))
    assert numbered[0] == ("1", "Start a Project")
    assert numbered[21] == ("22", "A day written another way, and a second partition")
    assert section.index("Getting started, how-tos 1 to 21:\n\n1. [Start a Project](") < (
        section.index("Intermediate, how-tos 22 to 41:\n\n22. [A day written another way"))
    assert "<!--" not in section


def test_the_export_ships_what_dev_committed_not_ignored_leftovers(repo: Path) -> None:
    (repo / ".gitignore").write_text("*.log\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore logs")
    (repo / "sqlglot_composer" / "run.log").write_text("left behind\n")
    export_clean.export(repo, WHEN)
    assert "sqlglot_composer/run.log" not in git(repo, "ls-tree", "-r", "--name-only", "main")


def test_the_export_refuses_while_main_is_checked_out_in_a_worktree(repo: Path) -> None:
    git(repo, "worktree", "add", "-q", str(repo.parent / "elsewhere"), "main")
    with pytest.raises(export_clean.ExportRefused, match="worktree"):
        export_clean.export(repo, WHEN)


def _main_commit(repo: Path) -> str:
    """The commit `main` points at, or "" where there is no local `main`, as in CI's checkout."""
    return git(repo, "for-each-ref", "--format=%(objectname)", "refs/heads/main")


def test_preview_builds_into_a_folder_and_commits_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main_before = _main_commit(ROOT)
    assert export_clean.main(["--preview", str(tmp_path / "preview")]) == 0
    assert (tmp_path / "preview" / ".github" / "README.md").is_file()
    assert sorted(path.name for path in (tmp_path / "preview").iterdir()) == [
        ".github", "CHANGES.md", "LICENSE", "example_projects", "requirements.txt",
        "sqlglot_composer"]
    assert "Nothing was committed" in capsys.readouterr().out
    assert _main_commit(ROOT) == main_before


# --- The Toolbox's folder and the copies --------------------------------------------------------


def _files_of(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.iterdir() if path.name != "__pycache__")


def test_the_folder_is_stamped_with_its_name_and_one_time(clean: Path) -> None:
    for name in _files_of(clean / "sqlglot_composer"):
        first = (clean / "sqlglot_composer" / name).read_text(encoding="utf-8").split("\n")[0]
        assert first in (f"# {STAMP}", f"<!-- {STAMP} -->"), name


def test_the_folders_file_list_names_its_own_files(clean: Path) -> None:
    init = (clean / "sqlglot_composer" / "__init__.py").read_text(encoding="utf-8")
    assert files_list_in(init) == _files_of(ROOT / "sqlglot_composer")


def test_the_example_projects_are_stamped_to_copy(clean: Path) -> None:
    stamp = f"{VERSION_TEXT} - copy it, then edit your copy"
    for folder in COPIED:
        for relative in copied_files(folder):
            if relative.endswith(UNSTAMPED):
                continue
            first = (clean / folder / relative).read_text(encoding="utf-8").split("\n")[0]
            assert first in (f"# {stamp}", f"<!-- {stamp} -->"), f"{folder}/{relative}"


def test_below_the_stamp_each_copy_is_devs_own(clean: Path) -> None:
    for folder in COPIED:
        for relative in copied_files(folder):
            exported = (clean / folder / relative).read_text(encoding="utf-8")
            if not relative.endswith(UNSTAMPED):
                exported = exported.split("\n", 1)[1]
            assert exported == (ROOT / folder / relative).read_text(encoding="utf-8"), relative


def test_each_example_projects_readme_says_to_copy_the_toolbox_in(clean: Path) -> None:
    for project in (clean / "example_projects").iterdir():
        readme_text = (project / "README.md").read_text(encoding="utf-8")
        assert "Copy the `sqlglot_composer` folder into this folder first" in readme_text


def _range_of(folder: str) -> dict[str, str]:
    """A folder's engine.py's version constants, such as {"_LOWEST": "25.24.2"}."""
    text = (ROOT / folder / "engine.py").read_text(encoding="utf-8")
    return {name: ".".join(numbers.replace(" ", "").split(","))
            for name, numbers in re.findall(r"^(_\w+) = \(([\d, ]+)\)$", text, re.MULTILINE)}


def _short(version: str) -> str:
    """A version without its trailing zeros, such as "31" for 31.0.0 and "4.1" for 4.1.0."""
    parts = version.split(".")
    while len(parts) > 1 and parts[-1] == "0":
        parts.pop()
    return ".".join(parts)


def test_the_readme_says_what_the_toolbox_needs_as_its_engine_checks_it() -> None:
    template = " ".join((ROOT / export_clean.README_TEMPLATE).read_text(encoding="utf-8").split())
    sql = _range_of("sqlglot_composer")
    python = re.search(r"^_PYTHON_NEEDED = \((\d+), (\d+)\)$",
                       (ROOT / "sqlglot_composer" / "checks.py").read_text(encoding="utf-8"),
                       re.MULTILINE).groups()
    assert f"The Toolbox needs Python {'.'.join(python)} or newer" in template
    assert (f"any sqlglot from {sql['_LOWEST']} up to (not including) {_short(sql['_BELOW'])}, "
            f"whose Example database and a struct column in create_table need "
            f"{sql['_EXECUTOR_NEEDS']} or newer") in template


def test_the_toolbox_is_exported_from_a_checkout_that_writes_crlf(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """git archive writes CRLF under core.autocrlf, which a fresh Windows install sets."""
    repo = make_repo(tmp_path, monkeypatch, dev_copy, autocrlf="true")
    export_clean.export(repo, WHEN)
    assert git(repo, "ls-tree", "-r", "--name-only", "main").splitlines() == exported_files()


def without_sqlglot_composer(folder: Path) -> Path:
    """What the build reads from a `dev` whose commit lacks sqlglot Composer's folder."""
    dev_copy(folder)
    shutil.rmtree(folder / "sqlglot_composer")
    return folder


def test_a_commit_without_the_toolbox_is_refused(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo(tmp_path, monkeypatch, without_sqlglot_composer, autocrlf="false")
    with pytest.raises(export_clean.ExportRefused, match="The export ships sqlglot_composer, "
                       "but this commit doesn't have it. Commit the folder on dev."):
        export_clean.export(repo, WHEN)


def test_a_commit_without_the_example_projects_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    shutil.rmtree(source / "example_projects")
    with pytest.raises(export_clean.ExportRefused, match=re.escape(
            "this commit doesn't have example_projects. Commit it on dev.")):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_files_of_different_versions_are_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    writing = source / "sqlglot_composer" / "writing.py"
    writing.write_text(writing.read_text(encoding="utf-8").replace(
        f'TOOLBOX_VERSION = "{VERSION}"', 'TOOLBOX_VERSION = "9.9"'), encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value) == (
        f"The Toolbox's files share one version, but __init__.py is {VERSION} and writing.py "
        "is 9.9. Set TOOLBOX_VERSION in every .py file of sqlglot_composer/, and commit.")


def spoil(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"{path.name} no longer holds {old!r}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_a_folder_that_imports_only_beside_something_else_is_refused(tmp_path: Path) -> None:
    folder = tmp_path / "clean" / "sqlglot_composer"
    folder.mkdir(parents=True)
    (folder / "__init__.py").write_text("import beside\n", encoding="utf-8")
    (tmp_path / "clean" / "beside.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.check_imports_alone(tmp_path / "clean")
    assert str(refused.value).startswith(
        "sqlglot_composer, copied on its own, doesn't import, so nothing was exported:\n"
        "ModuleNotFoundError: No module named 'beside'")


def test_an_example_projects_dry_run_that_fails_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    spoil(source / "example_projects" / "intermediate" / "references" / "mart__team_days.py",
          'key=["team", "dt"],', 'key=["team", "day"],')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value).startswith(
        "example_projects/intermediate's run_tables doesn't run its dry run "
        "on main, so nothing was exported:\nValueError: ")


def test_a_dry_run_that_leaves_a_file_behind_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    spoil(source / "example_projects" / "starter" / "building_blocks" / "runs_per_job.py",
          "\nfrom sqlglot_composer import", 'import pathlib\n'
          'pathlib.Path("left_behind.txt").write_text("x")\nfrom sqlglot_composer import')
    with pytest.raises(export_clean.ExportRefused, match=re.escape(
            "example_projects/starter's run_tables's dry run left files "
            "in the Clean tree: ['example_projects/starter/admin/left_behind.txt']")):
        export_clean.build(source, tmp_path / "clean", WHEN)


NETWORK_REFUSAL = ("The Clean tree holds something that could reach the network, but the "
                   "Toolbox, its Example projects and its Templates reach nothing but the "
                   "user's query and execute. tools/offline_policy.py found, as main would "
                   "hold it, line 1 being the export's stamp:\n")


def test_an_example_project_that_imports_a_network_client_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    spoil(source / "example_projects" / "starter" / "warehouse.py",
          '"""warehouse - ', 'import requests\n"""warehouse - ')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    # Line 2 on main: the export's stamp is line 1.
    assert str(refused.value).startswith(
        NETWORK_REFUSAL
        + "  example_projects/starter/warehouse.py:2 network: import requests\n")


def test_a_page_that_loads_a_script_from_the_internet_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    page = "tables/mart__team_day/lineage/20260925-060000-mart__team_day.html"
    spoil(source / "example_projects" / "starter" / page,
          "<!doctype html>", '<!doctype html><script src="https://example.com/x.js"></script>')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value).startswith(
        NETWORK_REFUSAL + f"  example_projects/starter/{page}:2 page reference: ")
    assert '<script src="https://example.com/x.js">' in str(refused.value)


def test_a_readme_that_embeds_a_picture_from_the_internet_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    spoil(source / export_clean.README_TEMPLATE, "# sqlglot Composer\n",
          '# sqlglot Composer\n<img src="https://example.com/x.png">\n')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value).startswith(
        NETWORK_REFUSAL
        + '  .github/README.md:3 page reference: <img src="https://example.com/x.png">\n')


def test_an_example_project_is_read_for_network_code_before_its_dry_run_runs_it(
        tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    # Run, it would leave a file behind, which the dry run's own check refuses: read first, the
    # socket stops it before anything runs.
    spoil(source / "example_projects" / "starter" / "building_blocks" / "runs_per_job.py",
          "\nfrom sqlglot_composer import", 'import pathlib\nimport socket\n'
          'pathlib.Path("left_behind.txt").write_text("x")\nfrom sqlglot_composer import')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value).startswith(NETWORK_REFUSAL)
    assert "example_projects/starter/building_blocks/runs_per_job.py:" in str(refused.value)
    assert not list((tmp_path / "clean").rglob("left_behind.txt"))


def test_the_allowlist_takes_only_the_exported_folders() -> None:
    paths = ["composer_core/tables.py", "sqlglot_composer/writing.py", "other_composer/writing.py",
             ".github/README.md"]
    assert export_clean.outside_allowlist(paths) == ["composer_core/tables.py",
                                                     "other_composer/writing.py"]
