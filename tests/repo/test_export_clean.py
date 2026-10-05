"""The Clean-branch export, checked on `dev` without git: the same build `main` gets.

`tools/export_clean.py` builds the Clean tree in a folder. These tests build it into a
temporary folder and check what `main` would hold: the allowlist, the stamp on line 1 of every
Toolbox file, the file list in `__init__.py`, and the README with its cheat sheet.
"""

from __future__ import annotations

import ast
import datetime
import doctest
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import editions  # noqa: E402
import export_clean  # noqa: E402

import sqlglot_composer  # noqa: E402

WHEN = datetime.datetime(2026, 10, 2, 14, 5)
VERSION = sqlglot_composer.TOOLBOX_VERSION
VERSION_TEXT = f"sqlglot Composer {VERSION}, exported 2026-10-02 14:05"
STAMP = f"{VERSION_TEXT} - generated from dev, do not edit"
# What main's commit and the README say the tree is: both Editions, at one version and time.
SHIPPED = f"sqlglot Composer and Spark Composer {VERSION}, exported 2026-10-02 14:05"


def dev_toolbox_files() -> list[str]:
    return sorted(
        path.name for path in (ROOT / "sqlglot_composer").iterdir() if path.name != "__pycache__"
    )


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
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


# Every Toolbox folder the export ships: the Composer core, then each Edition's.
FOLDERS = [editions.CORE] + [edition.folder for edition in editions.EDITIONS.values()]


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
    assert "Running: turn a Statement into Hive, send it, split it by day" in running
    assert "- `to_hive` - The Hive string for a Statement, ready to send.\n" in running
    constants = text.split("### `__init__.py`\n", 1)[1]
    assert (f"- `TOOLBOX_VERSION` = `{VERSION!r}` - the feature number, raised only when a big "
            "feature lands.\n") in constants
    assert text.index("### `tables.py`") < text.index("### `clauses.py`")


def test_the_exported_toolbox_docstring_shows_a_true_version(clean: Path) -> None:
    init = (clean / "sqlglot_composer" / "__init__.py").read_text(encoding="utf-8")
    examples = doctest.DocTestParser().get_examples(ast.get_docstring(ast.parse(init)))
    shown = next(example.want for example in examples if example.source.strip() == "VERSION")
    exported = repr(VERSION_TEXT) + "\n"
    assert doctest.OutputChecker().check_output(shown, exported, doctest.ELLIPSIS), shown


def test_a_file_line_that_repeats_its_only_name_line_is_left_out(clean: Path) -> None:
    section = readme(clean).split("### `example_database.py`\n", 1)[1]
    assert section.count("The Example database: six made-up tables") == 1


def exported_files() -> list[str]:
    """Every file `main` holds: the README, then each Edition's files, sorted."""
    return [".github/README.md"] + sorted(
        f"{folder}/{path.name}" for folder in FOLDERS
        for path in (ROOT / folder).iterdir() if path.name != "__pycache__")


def test_the_clean_tree_holds_only_the_allowlist(clean: Path) -> None:
    held = sorted(path.relative_to(clean).as_posix() for path in clean.rglob("*") if path.is_file())
    assert held == exported_files()


def test_anything_outside_the_allowlist_is_named() -> None:
    paths = ["sqlglot_composer/tables.py", ".github/README.md", "README.md",
             "sqlglot_composer/notes/x.py", "tools/export_clean.py", ".github/workflows/dev.yml"]
    assert export_clean.outside_allowlist(paths) == [
        "README.md", "sqlglot_composer/notes/x.py", "tools/export_clean.py",
        ".github/workflows/dev.yml",
    ]


def test_a_toolbox_file_importing_what_work_lacks_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    # One of Spark Composer's own files, so no copy of sqlglot Composer's goes stale first.
    writing = source / "spark_composer" / "writing.py"
    writing.write_text(writing.read_text(encoding="utf-8") + "\nimport requests  # noqa\n",
                       encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused,
                       match="spark_composer/writing.py imports requests"):
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


def make_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, copy, autocrlf: str) -> Path:
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
    """A copy of what the build reads from `dev`, every Toolbox folder, to spoil on purpose."""
    for name in FOLDERS:
        shutil.copytree(ROOT / name, folder / name,
                        ignore=shutil.ignore_patterns("__pycache__"))
    (folder / "docs").mkdir()
    shutil.copy(ROOT / export_clean.README_TEMPLATE, folder / export_clean.README_TEMPLATE)
    return folder


def test_the_stamped_copy_is_imported_and_says_it_was_exported(tmp_path: Path) -> None:
    assert export_clean.build(ROOT, tmp_path / "clean", WHEN) == SHIPPED


def test_a_toolbox_that_stops_on_import_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sqlglot_composer" / "old_module.py").write_text('TOOLBOX_VERSION = "1.9"\n')
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    # The whole four-part stop, not only its last line.
    assert str(refused.value).startswith(
        "The stamped copy of sqlglot Composer doesn't import, so nothing was exported:\n"
        "ImportError: sqlglot_composer stopped on import:\n"
        "  What happened:  old_module.py is from Toolbox version 1.9, and "
        "sqlglot_composer/__init__.py is from "
        f"{VERSION}.\n"
        "  Why it matters: ")
    assert "\n  Usual fix:      " in str(refused.value)


def test_a_file_the_export_cannot_stamp_is_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    (source / "sqlglot_composer" / "notes.txt").write_text("scratch\n")
    with pytest.raises(export_clean.ExportRefused, match="sqlglot_composer/notes.txt"):
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


def test_preview_builds_into_a_folder_and_commits_nothing(tmp_path: Path, capsys) -> None:
    main_before = _main_commit(ROOT)
    assert export_clean.main(["--preview", str(tmp_path / "preview")]) == 0
    assert (tmp_path / "preview" / ".github" / "README.md").is_file()
    assert sorted(path.name for path in (tmp_path / "preview").iterdir()) == [
        ".github", "composer_core", "spark_composer", "sqlglot_composer"]
    assert "Nothing was committed" in capsys.readouterr().out
    assert _main_commit(ROOT) == main_before


# --- Both Editions --------------------------------------------------------------------------

BOTH = tuple(editions.EDITIONS.values())


def _files_of(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.iterdir() if path.name != "__pycache__")


@pytest.mark.parametrize("edition", BOTH, ids=lambda edition: edition.folder)
def test_each_edition_is_stamped_with_its_own_name_and_one_time(clean: Path, edition) -> None:
    stamp = (f"{edition.product} {VERSION}, exported 2026-10-02 14:05 - generated from dev, do "
             "not edit")
    for name in _files_of(clean / edition.folder):
        first = (clean / edition.folder / name).read_text(encoding="utf-8").split("\n")[0]
        assert first in (f"# {stamp}", f"<!-- {stamp} -->"), name


@pytest.mark.parametrize("folder", FOLDERS)
def test_each_folders_file_list_names_its_own_files(clean: Path, folder: str) -> None:
    init = (clean / folder / "__init__.py").read_text(encoding="utf-8")
    assert files_list_in(init) == _files_of(ROOT / folder)


def test_the_composer_core_is_stamped_with_its_own_name_and_the_same_time(clean: Path) -> None:
    stamp = (f"Composer core {VERSION}, exported 2026-10-02 14:05 - generated from dev, do not "
             "edit")
    for name in _files_of(clean / editions.CORE):
        first = (clean / editions.CORE / name).read_text(encoding="utf-8").split("\n")[0]
        assert first in (f"# {stamp}", f"<!-- {stamp} -->"), name


def test_the_readme_lists_where_the_editions_hive_differs(clean: Path) -> None:
    section = readme(clean).split("## Where the two Editions' Hive differs\n", 1)[1]
    section = section.split("\n## ", 1)[0]
    items = [line for line in section.splitlines() if line.startswith("- **")]
    assert [item.split("**")[1] for item in items] == [
        row.title for row in editions.DECLARED_DIFFERENCES.values()]
    assert items[0].endswith(" sqlglot Composer writes `SUM(job_runs.duration_mins) / COUNT(*)` "
                             "where Spark Composer writes "
                             "`SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)`.")


def _range_of(folder: str) -> dict[str, str]:
    """An Edition's engine.py's version constants, such as {"_LOWEST": "25.24.2"}."""
    text = (ROOT / folder / "engine.py").read_text(encoding="utf-8")
    return {name: ".".join(numbers.replace(" ", "").split(","))
            for name, numbers in re.findall(r"^(_\w+) = \(([\d, ]+)\)$", text, re.MULTILINE)}


def _short(version: str) -> str:
    """A version without its trailing zeros, such as "31" for 31.0.0 and "4.1" for 4.1.0."""
    parts = version.split(".")
    while len(parts) > 1 and parts[-1] == "0":
        parts.pop()
    return ".".join(parts)


def test_the_readme_says_what_each_edition_needs_as_its_engine_checks_it() -> None:
    template = " ".join((ROOT / export_clean.README_TEMPLATE).read_text(encoding="utf-8").split())
    sql, spark = _range_of("sqlglot_composer"), _range_of("spark_composer")
    java = dict(re.findall(r"^(_JAVA_\w+) = (\d+)$",
                           (ROOT / "spark_composer" / "engine.py").read_text(encoding="utf-8"),
                           re.MULTILINE))
    python = re.search(r"^_PYTHON_NEEDED = \((\d+), (\d+)\)$",
                       (ROOT / "composer_core" / "checks.py").read_text(encoding="utf-8"),
                       re.MULTILINE).groups()
    assert f"Each Edition needs Python {'.'.join(python)} or newer" in template
    assert (f"sqlglot Composer: the sqlglot library, {sql['_LOWEST']} or newer, below "
            f"{_short(sql['_BELOW'])}. sqlglot Composer's Example database runs queries on "
            f"sqlglot {sql['_EXECUTOR_NEEDS']} or newer") in template
    assert (f'`%pip install "sqlglot>={sql["_EXECUTOR_NEEDS"]},<{_short(sql["_BELOW"])}"`'
            in template)
    assert (f"Spark Composer: pyspark {spark['_LOWEST']} or newer, below "
            f"{_short(spark['_BELOW'])}: `%pip install "
            f'"pyspark>={spark["_LOWEST"]},<{_short(spark["_BELOW"])}"`') in template
    assert f"needs Java {java['_JAVA_NEEDED']} to {java['_JAVA_NEWEST']}" in template


def test_the_clean_tree_holds_only_the_toolbox_folders_and_the_readme(clean: Path) -> None:
    assert [path for path in export_clean.files_in(clean)
            if not path.startswith(tuple(f"{folder}/" for folder in FOLDERS))] == [
        ".github/README.md"]


def test_both_editions_are_exported_from_a_checkout_that_writes_crlf(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """git archive writes CRLF under core.autocrlf, which a fresh Windows install sets."""
    repo = make_repo(tmp_path, monkeypatch, dev_copy, autocrlf="true")
    export_clean.export(repo, WHEN)
    assert git(repo, "ls-tree", "-r", "--name-only", "main").splitlines() == exported_files()


def sqlglot_composer_only(folder: Path) -> Path:
    """What the build reads from a `dev` that holds sqlglot Composer alone."""
    dev_copy(folder)
    shutil.rmtree(folder / "spark_composer")
    return folder


def test_an_edition_the_commit_lacks_is_refused(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo(tmp_path, monkeypatch, sqlglot_composer_only, autocrlf="false")
    with pytest.raises(export_clean.ExportRefused, match="but this commit doesn't have "
                       "spark_composer. Commit the folder on dev, or take its Edition out"):
        export_clean.export(repo, WHEN)


def test_editions_of_different_versions_are_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    init = source / "spark_composer" / "__init__.py"
    init.write_text(init.read_text(encoding="utf-8").replace(
        f'TOOLBOX_VERSION = "{VERSION}"', 'TOOLBOX_VERSION = "9.9"'), encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused) as refused:
        export_clean.build(source, tmp_path / "clean", WHEN)
    assert str(refused.value) == (
        f"The Toolbox's folders share one version, but composer_core is {VERSION} and "
        f"sqlglot_composer is {VERSION} and spark_composer is 9.9. Set TOOLBOX_VERSION in every .py "
        "file of composer_core/, sqlglot_composer/, spark_composer/, and commit.")


def test_editions_describing_their_names_differently_are_refused(tmp_path: Path) -> None:
    source = dev_copy(tmp_path / "dev")
    # Each Edition's own __init__.py says what TOOLBOX_VERSION is, for the cheat sheet.
    init = source / "spark_composer" / "__init__.py"
    init.write_text(init.read_text(encoding="utf-8").replace(
        "TOOLBOX_VERSION is the feature number", "TOOLBOX_VERSION is a feature number"),
        encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match=re.escape(
            "Spark Composer's cheat sheet differs from sqlglot Composer's: it has \"__init__.py: "
            "`TOOLBOX_VERSION` = `'")):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_the_stamped_copy_cannot_import_the_other_editions_library(tmp_path: Path) -> None:
    if importlib.util.find_spec("pyspark") is None:
        pytest.skip("pyspark isn't installed, so there is nothing for the check to block")
    source = dev_copy(tmp_path / "dev")
    engine = source / "sqlglot_composer" / "engine.py"
    # Written so the check of each file's imports doesn't see it: only the import can.
    engine.write_text(engine.read_text(encoding="utf-8") + '\n__import__("pyspark")\n',
                      encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match="import of pyspark halted"):
        export_clean.build(source, tmp_path / "clean", WHEN)


@pytest.mark.parametrize("spelling", ["Spark Composer", "spark_composer", "spark-composer",
                                      "SparkComposer"])
def test_a_readme_naming_an_edition_that_isnt_shipped_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, spelling: str) -> None:
    monkeypatch.setattr(editions, "EXPORTED", (editions.SQLGLOT_COMPOSER,))
    source = dev_copy(tmp_path / "dev")
    (source / export_clean.README_TEMPLATE).write_text(
        f"# Toolbox\n\n{export_clean.VERSION_MARKER}\n\n{export_clean.DIFFERENCES_MARKER}\n\n"
        f"{export_clean.CHEAT_SHEET_MARKER}\n\nSee {spelling} too.\n", encoding="utf-8")
    with pytest.raises(export_clean.ExportRefused, match="names Spark Composer, which this "
                       "export doesn't ship"):
        export_clean.build(source, tmp_path / "clean", WHEN)


def test_the_allowlist_takes_each_exported_editions_folder(monkeypatch) -> None:
    paths = ["composer_core/tables.py", "sqlglot_composer/writing.py", "spark_composer/writing.py",
             ".github/README.md"]
    assert export_clean.outside_allowlist(paths) == []
    monkeypatch.setattr(editions, "EXPORTED", (editions.SQLGLOT_COMPOSER,))
    assert export_clean.outside_allowlist(paths) == ["spark_composer/writing.py"]
