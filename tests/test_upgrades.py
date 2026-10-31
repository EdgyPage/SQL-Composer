"""Upgrades: a Project's files carried from the Toolbox version that last wrote them to this
one.

Toolbox 7.2's ticket 02. project.upgrade() runs each version's step in turn, from
admin/project_version.txt's version to the Toolbox's. A step makes the changes that need no
judgement, keeping each file as it was in admin/removed/, and marks each one that needs you
with `# UPGRADE <version>:` at its line and a box in admin/upgrade_<version>.md. Every version
ships its step, and the Example projects as the version before left them, in
tests/upgrade_from/, upgrade into the current ones.
"""

from __future__ import annotations

import datetime
import json
import shutil
import warnings
from pathlib import Path

import pytest
from conftest import toolbox_folder, toolbox_module

import sqlglot_composer
from sqlglot_composer import project, set_admin_log

NOW = datetime.datetime(2026, 10, 26, 9, 30, 0)
VERSION = sqlglot_composer.TOOLBOX_VERSION
ROOT = Path(__file__).resolve().parents[1]
UPGRADE_FROM = ROOT / "tests" / "upgrade_from"
# What each Example project gained by hand in this version, which no Upgrade makes: 7.2's
# Intermediate project finished a Conversion, mart.team_failures, so its files, and the files
# that list it, are left out of the comparison. Empty it when the next version's frozen copy
# holds them.
GAINED_BY_HAND = {
    "intermediate": ("README.md", "admin/registry.csv", "references/mart.py",
                     "references/reference_sheet.csv", "references/mart__team_failures.py",
                     "tables/mart__team_failures/",
                     # Toolbox 8.0's warehouse.py, which holds conn (ticket 21). Ticket 20's
                     # Upgrade step carries it, and takes this entry out.
                     "warehouse.py"),
    "starter": ("warehouse.py", "README.md"),  # the same, and the README that says to set conn
}
upgrades = toolbox_module("upgrades")


@pytest.fixture
def pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> Path:
    monkeypatch.chdir(tmp_path)
    project.start()
    return tmp_path


def made_by_7_1(root: Path) -> Path:
    """The Project as 7.1 left it: no admin/project_version.txt, and no admin/upgrade.ipynb."""
    (root / "admin" / "project_version.txt").unlink()
    (root / "admin" / "upgrade.ipynb").unlink()
    return root


def previous_version() -> str:
    """The version before this one that a step starts from: the step before this version's,
    or the first version an Upgrade starts from."""
    earlier = [version for version in upgrades.STEPS
               if upgrades.version_numbers(version) < upgrades.version_numbers(VERSION)]
    return max(earlier, key=upgrades.version_numbers, default=upgrades.FIRST_UPGRADABLE)


# --- The version a Project records ------------------------------------------------------------


def test_start_records_this_toolboxs_version(started: Path) -> None:
    text = (started / "admin" / "project_version.txt").read_text(encoding="utf-8")
    assert text.splitlines()[0] == VERSION
    assert upgrades.project_version(started) == VERSION


def test_a_project_at_this_version_has_nothing_to_upgrade(started: Path) -> None:
    assert repr(project.upgrade()) == (
        f"The Project is at {VERSION} already, as this Toolbox is: nothing to upgrade.")


# --- Every version ships its step -------------------------------------------------------------


def test_this_version_has_an_upgrade_step() -> None:
    assert VERSION in upgrades.STEPS
    assert all(upgrades.version_numbers(version)
               > upgrades.version_numbers(upgrades.FIRST_UPGRADABLE)
               for version in upgrades.STEPS)


def test_the_example_projects_of_the_version_before_are_kept_frozen() -> None:
    assert (sorted(path.name for path in (UPGRADE_FROM / previous_version()).iterdir())
            == sorted(path.name for path in (ROOT / "example_projects").iterdir()))


def files_of(folder: Path, name: str) -> dict[str, bytes]:
    """Each file of an Example project, by its path, leaving out the history an Upgrade keeps
    as it was or adds to: Lineage pages, the Admin log and the Upgrade's own checklists; and
    what the project gained by hand in this version, GAINED_BY_HAND."""
    def kept(relative: str) -> bool:
        return not ("/lineage/" in f"/{relative}" or relative == "admin/admin_log.md"
                    or relative.startswith(("admin/upgrade_", "admin/removed/",
                                            *GAINED_BY_HAND.get(name, ()))))

    return {path.relative_to(folder).as_posix(): path.read_bytes().replace(b"\r\n", b"\n")
            for path in sorted(folder.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
            and kept(path.relative_to(folder).as_posix())}


@pytest.mark.parametrize(
    "name", sorted(path.name for path in (ROOT / "example_projects").iterdir()))
def test_the_example_projects_of_the_version_before_upgrade_into_this_ones(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None, name: str) -> None:
    copy = tmp_path / name
    shutil.copytree(UPGRADE_FROM / previous_version() / name, copy)
    monkeypatch.chdir(copy)
    project.upgrade()
    upgraded, current = files_of(copy, name), files_of(ROOT / "example_projects" / name, name)
    assert sorted(upgraded) == sorted(current)
    assert [path for path in upgraded if upgraded[path] != current[path]] == []
    assert (copy / "admin" / f"upgrade_{VERSION}.md").is_file()


# --- An upgrade from 7.1 ----------------------------------------------------------------------


def test_a_7_1_project_is_upgraded_and_told_what_it_lacked(started: Path) -> None:
    made_by_7_1(started)
    assert repr(project.upgrade()) == (
        f"Upgraded the Project from 7.1 to {VERSION}.\n"
        f"{VERSION}: nothing to change by hand. admin/upgrade_{VERSION}.md lists what it did.")
    assert upgrades.project_version(started) == VERSION
    assert (started / "admin" / "upgrade.ipynb").is_file()
    checklist = (started / "admin" / f"upgrade_{VERSION}.md").read_text(encoding="utf-8")
    assert "- added admin/upgrade.ipynb\n" in checklist
    assert f"Nothing: {VERSION} needs nothing changed by hand." in checklist


def test_an_upgrade_is_logged_as_a_project_action(started: Path) -> None:
    made_by_7_1(started)
    project.upgrade()
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    entry = log.split("## 2026-10-26 09:30:00, Project action")[-1]
    assert "- Call: `project.upgrade()`" in entry
    assert (f"- Files: added admin/upgrade.ipynb; wrote admin/upgrade_{VERSION}.md; wrote "
            f"admin/project_version.txt: {VERSION}") in entry


def test_an_upgrade_run_again_does_nothing(started: Path) -> None:
    made_by_7_1(started)
    project.upgrade()
    before = files_of(started, "")
    assert "nothing to upgrade" in repr(project.upgrade())
    assert files_of(started, "") == before


# --- What an Upgrade refuses ------------------------------------------------------------------


def test_a_project_from_before_7_0_is_refused(started: Path) -> None:
    made_by_7_1(started)
    (started / "warehouse.py").rename(started / "send.py")
    with pytest.raises(ValueError, match="this Project records no Toolbox version, and holds "
                       "send.py, so it is from before 7.0"):
        project.upgrade()
    assert "last written by Toolbox" not in repr(project.check())


def test_a_project_with_no_version_and_no_warehouse_py_is_refused(started: Path) -> None:
    made_by_7_1(started)
    (started / "warehouse.py").unlink()
    with pytest.raises(ValueError, match="records no Toolbox version, and holds no "
                       "warehouse.py, which every Project from 7.0 on holds"):
        project.upgrade()


def test_each_step_is_logged_and_recorded_as_it_runs(started: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """Two steps, 7.3 then 7.4, as a Toolbox two versions on would run them."""
    monkeypatch.setattr(sqlglot_composer, "TOOLBOX_VERSION", "7.4")
    monkeypatch.setattr(upgrades, "STEPS", {"7.3": lambda step: None,
                                            "7.4": lambda step: None})
    upgrades.write_project_version(started, "7.2")
    assert repr(project.upgrade()).splitlines() == [
        "Upgraded the Project from 7.2 to 7.4.",
        "7.3: nothing to change by hand. admin/upgrade_7.3.md lists what it did.",
        "7.4: nothing to change by hand. admin/upgrade_7.4.md lists what it did."]
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert log.count("- Call: `project.upgrade()`") == 2
    assert "wrote admin/project_version.txt: 7.3" in log
    assert upgrades.project_version(started) == "7.4"
    assert "from 7.3 to 7.4" in (started / "admin" / "upgrade_7.4.md").read_text(
        encoding="utf-8")


def test_a_project_a_newer_toolbox_wrote_is_refused(started: Path) -> None:
    upgrades.write_project_version(started, "99.0")
    with pytest.raises(ValueError, match=f"last written by Toolbox 99.0, and this Toolbox is "
                       f"{VERSION}"):
        project.upgrade()


def test_a_project_version_that_isnt_one_is_refused(started: Path) -> None:
    (started / "admin" / "project_version.txt").write_text("seven\n", encoding="utf-8")
    with pytest.raises(ValueError, match="says 'seven', which isn't a version an Upgrade "
                       "starts from"):
        project.upgrade()


# --- Marks: what a step leaves for you --------------------------------------------------------


def marking_step(upgrade: upgrades.Upgrade) -> None:
    """A step that changes one file plainly and marks two lines it can't decide."""
    upgrade.rewrite("warehouse.py", "# rewritten\n")
    upgrade.mark("references/ops__jobs.py", 2, "say which call this is")
    upgrade.mark("admin/run_tables.ipynb", 1, "pick query or execute", cell=3)


@pytest.fixture
def marked(started: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (started / "references" / "ops__jobs.py").write_text("x = 1\n    y = run(s)\n",
                                                         encoding="utf-8")
    made_by_7_1(started)
    monkeypatch.setattr(upgrades, "STEPS", {VERSION: marking_step})
    project.upgrade()
    return started


def test_a_mark_sits_above_its_line_at_its_indent(marked: Path) -> None:
    assert (marked / "references" / "ops__jobs.py").read_text(encoding="utf-8") == (
        f"x = 1\n    # UPGRADE {VERSION}: say which call this is\n    y = run(s)\n")


def test_a_mark_in_a_notebook_sits_in_its_cell(marked: Path) -> None:
    notebook = json.loads((marked / "admin" / "run_tables.ipynb").read_text(encoding="utf-8"))
    source = notebook["cells"][2]["source"]
    assert source[0] == f"# UPGRADE {VERSION}: pick query or execute\n"
    assert source[1].startswith("project.run_tables()")


def test_each_file_a_step_changes_is_kept_as_it_was(marked: Path) -> None:
    kept = marked / "admin" / "removed" / f"20261026-093000-upgrade_{VERSION}"
    assert (kept / "warehouse.py").read_text(encoding="utf-8").startswith('"""warehouse')
    assert (kept / "references" / "ops__jobs.py").read_text(encoding="utf-8") == (
        "x = 1\n    y = run(s)\n")
    assert (kept / "admin" / "run_tables.ipynb").is_file()


def test_the_checklist_has_a_box_for_each_mark(marked: Path) -> None:
    checklist = (marked / "admin" / f"upgrade_{VERSION}.md").read_text(encoding="utf-8")
    assert "- rewrote warehouse.py\n" in checklist
    assert "- [ ] references/ops__jobs.py, line 2: say which call this is\n" in checklist
    assert "- [ ] admin/run_tables.ipynb, cell 3, line 1: pick query or execute\n" in checklist


def test_check_lists_each_mark_left(marked: Path) -> None:
    said = repr(project.check())
    assert "Marked by project.upgrade() for you to change" in said
    assert (f"  references/ops__jobs.py, line 2: # UPGRADE {VERSION}: say which call this is"
            in said)
    assert (f"  admin/run_tables.ipynb, cell 3, line 1: # UPGRADE {VERSION}: pick query or "
            "execute") in said
    assert "removed/" not in said


def test_the_report_counts_the_marks(started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (started / "references" / "ops__jobs.py").write_text("a\nb\n", encoding="utf-8")
    made_by_7_1(started)
    monkeypatch.setattr(upgrades, "STEPS", {VERSION: marking_step})
    assert repr(project.upgrade()).splitlines()[1] == (
        f"{VERSION}: 2 changes for you to make, each marked `# UPGRADE {VERSION}:`, and listed "
        f"in admin/upgrade_{VERSION}.md.")


# --- A Project behind its Toolbox only warns --------------------------------------------------


def test_check_says_a_project_behind_its_toolbox_needs_an_upgrade(started: Path) -> None:
    made_by_7_1(started)
    assert repr(project.check()) == (
        f"The Project was last written by Toolbox 7.1, and this Toolbox is {VERSION}: run "
        "project.upgrade() in a new cell of admin/check_project.ipynb, or of "
        "admin/upgrade.ipynb once the Project has one.")


def test_check_says_a_newer_toolbox_last_wrote_the_project(started: Path) -> None:
    upgrades.write_project_version(started, "99.0")
    assert repr(project.check()) == (
        f"The Project was last written by Toolbox 99.0, newer than this Toolbox, {VERSION}: "
        "copy in the 99.0 download of sqlglot_composer, or a newer one.")


def test_a_later_mark_above_an_earlier_one_moves_it_down_in_the_checklist(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def two_marks(upgrade: upgrades.Upgrade) -> None:
        upgrade.mark("references/ops__jobs.py", 3, "the later line")
        upgrade.mark("references/ops__jobs.py", 1, "the first line")

    (started / "references" / "ops__jobs.py").write_text("a\nb\nc\n", encoding="utf-8")
    made_by_7_1(started)
    monkeypatch.setattr(upgrades, "STEPS", {VERSION: two_marks})
    project.upgrade()
    checklist = (started / "admin" / f"upgrade_{VERSION}.md").read_text(encoding="utf-8")
    assert "- [ ] references/ops__jobs.py, line 4: the later line\n" in checklist
    assert "- [ ] references/ops__jobs.py, line 1: the first line\n" in checklist
    listed = repr(project.check())
    assert "references/ops__jobs.py, line 4: # UPGRADE" in listed
    assert "references/ops__jobs.py, line 1: # UPGRADE" in listed


def test_the_import_warns_in_a_project_behind_it(started: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """__init__.py calls warn_if_behind() once the project module is imported."""
    assert "\nproject.warn_if_behind()\n" in (toolbox_folder() / "__init__.py").read_text(
        encoding="utf-8")
    made_by_7_1(started)
    monkeypatch.chdir(started / "tables")
    with pytest.warns(UserWarning) as caught:
        project.warn_if_behind()
    said = str(caught[0].message)
    assert said.startswith("sqlglot_composer on import:")
    assert (f"What happened:  The Project was last written by Toolbox 7.1, and this Toolbox is "
            f"{VERSION}.") in said
    assert "Opt-out:        none" in said


@pytest.mark.parametrize("where", ["outside a Project", "in a Project at this version"])
def test_the_import_says_nothing_otherwise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                           pinned: None, where: str) -> None:
    monkeypatch.chdir(tmp_path)
    if where != "outside a Project":
        project.start()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        project.warn_if_behind()
