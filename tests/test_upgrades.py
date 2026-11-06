"""Upgrades: a Project's files carried from the Toolbox version that last wrote them to this
one.

Toolbox 7.2's ticket 02. project.upgrade() runs each version's step in turn, from
admin/project_version.txt's version to the Toolbox's. A step makes the changes that need no
judgement, keeping each file as it was in admin/removed/, and marks each one that needs you
with `# UPGRADE <version>:` at its line and a box in admin/upgrade_<version>.md. Every version
ships its step, and the Example projects as the version before left them, in
tests/upgrade_from/. From 8.3 on (Toolbox 8.4's ticket 11), the Example projects of every
version frozen there upgrade straight into the current ones, so a Project may skip versions.
"""

from __future__ import annotations

import datetime
import json
import re
import shutil
import sys
import warnings
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_folder, toolbox_module
import notebook_runner

import sqlglot_composer
from sqlglot_composer import example_database, project, set_admin_log

NOW = datetime.datetime(2026, 10, 26, 9, 30, 0)
VERSION = sqlglot_composer.TOOLBOX_VERSION
# The step the tests of a Conversion 7.2 left open read the marks and checklist of.
STEP_8_0 = "8.0"
# The step that adds a Table notebook's Hive cell.
STEP_8_2 = "8.2"
ROOT = Path(__file__).resolve().parents[1]
UPGRADE_FROM = ROOT / "tests" / "upgrade_from"
# A line an Upgrade step's mark holds in a file, as `# UPGRADE 8.5: ...`.
UPGRADE_MARK_LINE = re.compile(rb"^[ \t]*# UPGRADE \d+\.\d+: [^\n]*\n", re.MULTILINE)


# What each Example project gained or changed by hand in a version, which no Upgrade makes, by
# the version and the Example project, such as {"8.4": {"starter": ("admin/notes.md",)}}: left
# out of the comparison of a Project upgraded from any version before it. Add a version's entry
# when its Example projects gain a file by hand, and keep it once the version ships, since an
# upgrade from before it still lacks the file.
GAINED_BY_HAND: dict[str, dict[str, tuple[str, ...]]] = {
    # 8.5 reads a script where it is: the intermediate's is saved beside the convert notebook,
    # as a user saves one, where 8.4's batch kept a copy of it; its README lists it; and its
    # converted table's proposed Key is accepted, as a user accepts one (ticket 07).
    "8.5": {"intermediate": ("admin/workflows/convert/team_failures.hql", "README.md",
                             "references/mart__team_failures.py")},
}
# What a version's Upgrade leaves as the version before wrote it, on purpose, by the version,
# such as {"8.4": ("admin/check_project.ipynb",)}: left out the same way, and kept the same
# way.
LEFT_AS_IT_WAS: dict[str, tuple[str, ...]] = {
    # A batch finished before 8.5 is history: its batch.md, its record and its scripts' copy
    # stay as that version wrote them.
    "8.5": ("admin/workflows/convert/finished/",),
}
# The first version whose frozen Example projects are upgraded straight to this one.
CHAINS_START_AT = "8.3"
upgrades = toolbox_module("upgrades")
notebooks = toolbox_module("notebooks")
in_words = toolbox_module("shared").in_words


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
    """The Project as 7.1 left it, as far as an Upgrade reads: no admin/project_version.txt, and
    none of what 7.2 and 8.0 added, such as admin/workflows/upgrade/upgrade.ipynb."""
    (root / "admin" / "project_version.txt").unlink()
    shutil.rmtree(root / "admin" / "workflows")
    for name in ("databases.py", "sent.csv", "remove.ipynb"):
        (root / "admin" / name).unlink()
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


def files_of(folder: Path, left_out: tuple[str, ...] = ()) -> dict[str, bytes]:
    """Each file of a Project, by its path, leaving out the history an Upgrade keeps as it was
    or adds to: Lineage pages, the Admin log and the Upgrade's own checklists; and each path
    starting with one of `left_out`. Each UPGRADE mark's line is left out too: what a mark
    asks is the user's to do, and the rest of the file is what the Upgrade wrote."""
    def kept(relative: str) -> bool:
        return not ("/lineage/" in f"/{relative}" or relative == "admin/admin_log.md"
                    or relative.startswith(("admin/upgrade_", "admin/removed/", *left_out)))

    return {path.relative_to(folder).as_posix():
            UPGRADE_MARK_LINE.sub(b"", path.read_bytes().replace(b"\r\n", b"\n"))
            for path in sorted(folder.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
            and kept(path.relative_to(folder).as_posix())}


def left_out_since(start_from: str, name: str) -> tuple[str, ...]:
    """What the comparison leaves out of the Example project `name` upgraded from `start_from`:
    what it gained by hand in each later version, GAINED_BY_HAND, and what each later version's
    Upgrade left as it was, LEFT_AS_IT_WAS."""
    left_out: list[str] = []
    for version in upgrades.steps_between(start_from, VERSION):
        left_out += GAINED_BY_HAND.get(version, {}).get(name, ())
        left_out += LEFT_AS_IT_WAS.get(version, ())
    return tuple(left_out)


def upgraded_to_this_one() -> list[tuple[str, str]]:
    """Each frozen Example project upgraded straight to this version, as (its version, its
    name): those of every version from CHAINS_START_AT on that tests/upgrade_from/ holds, and
    those of the version before, which is 8.2 until 8.3's are frozen."""
    versions = {previous_version()}
    for folder in UPGRADE_FROM.iterdir():
        if (not upgrades.is_older(folder.name, than=CHAINS_START_AT)
                and upgrades.is_older(folder.name, than=VERSION)):
            versions.add(folder.name)
    names = sorted(path.name for path in (ROOT / "example_projects").iterdir())
    pairs = []
    for version in sorted(versions, key=upgrades.version_numbers):
        pairs += [(version, name) for name in names]
    return pairs


UPGRADED_TO_THIS_ONE = upgraded_to_this_one()


@pytest.mark.parametrize(("start_from", "name"), UPGRADED_TO_THIS_ONE,
                         ids=[f"{version}-{name}" for version, name in UPGRADED_TO_THIS_ONE])
def test_the_example_projects_of_each_version_since_8_3_upgrade_straight_into_this_ones(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None, start_from: str,
        name: str) -> None:
    """A Project may skip versions: one any version from 8.3 on wrote upgrades straight to this
    one, each step in turn. So an Upgrade step may not assume the Project was written by the
    version just before it, only that each earlier step ran: it reads the files as the steps
    before it left them, never as one version's start() wrote them."""
    copy = tmp_path / name
    shutil.copytree(UPGRADE_FROM / start_from / name, copy)
    monkeypatch.chdir(copy)
    said = repr(project.upgrade()).splitlines()
    left_out = left_out_since(start_from, name)
    upgraded = files_of(copy, left_out)
    current = files_of(ROOT / "example_projects" / name, left_out)
    assert sorted(upgraded) == sorted(current)
    assert [path for path in upgraded if upgraded[path] != current[path]] == []
    steps = upgrades.steps_between(start_from, VERSION)
    assert [line.split(":")[0] for line in said[1:-1]] == steps
    reports = [f"admin/upgrade_{version}.md" for version in steps]
    assert [report for report in reports if not (copy / report).is_file()] == []
    assert said[-1].endswith(f"{in_words(reports)}.")


# --- An upgrade from 7.1 ----------------------------------------------------------------------


def test_a_7_1_project_is_upgraded_and_told_what_it_lacked(started: Path) -> None:
    made_by_7_1(started)
    said = repr(project.upgrade()).split("\n")
    assert said[:2] == [
        f"Upgraded the Project from 7.1 to {VERSION}.",
        "7.2: nothing to change by hand. admin/upgrade_7.2.md lists what it did."]
    assert said[2].startswith("8.0: ")
    assert said[3].startswith("8.1: ")
    assert said[4].startswith("8.2: ")
    assert said[5].startswith("8.3: ")
    assert said[6].startswith("8.4: ")
    assert said[7].startswith(f"{VERSION}: ")
    assert said[8] == ("Read each step's checklist, in order: admin/upgrade_7.2.md, "
                       "admin/upgrade_8.0.md, admin/upgrade_8.1.md, admin/upgrade_8.2.md, "
                       "admin/upgrade_8.3.md, admin/upgrade_8.4.md and "
                       f"admin/upgrade_{VERSION}.md.")
    assert upgrades.project_version(started) == VERSION
    assert (started / "admin" / "workflows" / "upgrade" / "upgrade.ipynb").is_file()
    checklist = (started / "admin" / "upgrade_7.2.md").read_text(encoding="utf-8")
    assert "- added admin/workflows/upgrade/upgrade.ipynb\n" in checklist


def test_an_upgrade_is_logged_as_a_project_action(started: Path) -> None:
    made_by_7_1(started)
    project.upgrade()
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    entry = log.split("## 2026-10-26 09:30:00, Project action")[-1]
    assert "- Call: `project.upgrade()`" in entry
    assert "added admin/workflows/upgrade/upgrade.ipynb" in log
    assert (f"wrote admin/upgrade_{VERSION}.md; wrote admin/project_version.txt: {VERSION}"
            in entry)


def test_an_upgrade_run_again_does_nothing(started: Path) -> None:
    made_by_7_1(started)
    project.upgrade()
    before = files_of(started)
    assert "nothing to upgrade" in repr(project.upgrade())
    assert files_of(started) == before


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
        "7.4: nothing to change by hand. admin/upgrade_7.4.md lists what it did.",
        "Read each step's checklist, in order: admin/upgrade_7.3.md and admin/upgrade_7.4.md."]
    log = (started / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert log.count("- Call: `project.upgrade()`") == 2
    assert "wrote admin/project_version.txt: 7.3" in log
    assert upgrades.project_version(started) == "7.4"
    assert "from 7.3 to 7.4" in (started / "admin" / "upgrade_7.4.md").read_text(
        encoding="utf-8")


def test_each_step_keeps_its_own_report_and_archive(started: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """Two steps, 7.3 then 7.4, each rewriting warehouse.py: each keeps it as it found it."""
    monkeypatch.setattr(sqlglot_composer, "TOOLBOX_VERSION", "7.4")
    monkeypatch.setattr(upgrades, "STEPS", {
        "7.3": lambda step: step.rewrite("warehouse.py", "# 7.3\n"),
        "7.4": lambda step: step.rewrite("warehouse.py", "# 7.4\n")})
    upgrades.write_project_version(started, "7.2")
    project.upgrade()
    removed = started / "admin" / "removed"
    assert (removed / "20261026-093000-upgrade_7.3" / "warehouse.py").read_text(
        encoding="utf-8").startswith('"""warehouse')
    assert (removed / "20261026-093000-upgrade_7.4" / "warehouse.py").read_text(
        encoding="utf-8") == "# 7.3\n"
    admin = started / "admin"
    assert "from 7.2 to 7.3" in (admin / "upgrade_7.3.md").read_text(encoding="utf-8")
    assert "from 7.3 to 7.4" in (admin / "upgrade_7.4.md").read_text(encoding="utf-8")


def test_an_upgrade_of_one_step_names_its_report_last(started: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sqlglot_composer, "TOOLBOX_VERSION", "7.3")
    monkeypatch.setattr(upgrades, "STEPS", {"7.3": lambda step: None})
    upgrades.write_project_version(started, "7.2")
    assert repr(project.upgrade()).splitlines()[-1] == (
        "Read the step's checklist: admin/upgrade_7.3.md.")


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
        "step 1's cell of admin/workflows/upgrade/upgrade.ipynb, project.upgrade(); a Project "
        "made before 8.0 has no such notebook until its first Upgrade, so there "
        "project.upgrade() goes in admin/check_project.ipynb.")


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


# --- The step from 7.2 to 8.0: a Conversion 7.2 left open ---------------------------------

ORIGINAL = "SELECT r.run_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'\n"
FINISHING = 'project.finish_conversion("team_runs", table="mart.team_runs")'


@pytest.fixture
def open_in_7_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> Path:
    """The Starter project as 7.2 left it, with a Conversion, team_runs, not finished, and a
    script of yours that finishes it, beside a line that only says so."""
    root = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "7.2" / "starter", root)
    folder = root / "admin" / "conversions" / "team_runs"
    folder.mkdir(parents=True)
    (folder / "original.hql").write_text(ORIGINAL, encoding="utf-8")
    (folder / "scan.md").write_text("# team_runs\n", encoding="utf-8")
    toolbox_module("notebooks").write_notebook(
        folder / "team_runs.ipynb", [("code", "statement = 'yours, changed'")])
    (root / "finish.py").write_text(
        f"from sqlglot_composer import project\n\n# {FINISHING}\n{FINISHING}\n",
        encoding="utf-8")
    monkeypatch.chdir(root)
    return root


def names_cell(root: Path) -> str:
    """The convert Workflow notebook's third cell, its names cell."""
    notebook = root / "admin" / "workflows" / "convert" / "convert.ipynb"
    return "".join(json.loads(notebook.read_text(encoding="utf-8"))["cells"][2]["source"])


def test_an_open_conversions_hive_is_put_beside_the_convert_workflow(open_in_7_2: Path) -> None:
    project.upgrade()
    hive = open_in_7_2 / "admin" / "workflows" / "convert" / "team_runs.hql"
    assert hive.read_text(encoding="utf-8") == ORIGINAL
    assert not (open_in_7_2 / "admin" / "conversions").exists()


def test_an_open_conversions_folder_is_kept_as_it_was(open_in_7_2: Path) -> None:
    project.upgrade()
    kept = (open_in_7_2 / "admin" / "removed" / f"20261026-093000-upgrade_{STEP_8_0}" / "admin"
            / "conversions" / "team_runs")
    assert sorted(path.name for path in kept.iterdir()) == [
        "original.hql", "scan.md", "team_runs.ipynb"]
    assert "yours, changed" in (kept / "team_runs.ipynb").read_text(encoding="utf-8")


def test_the_convert_workflow_is_marked_to_convert_it_again(open_in_7_2: Path) -> None:
    project.upgrade()
    mark, name = names_cell(open_in_7_2).split("\n")[:2]
    assert mark.startswith(f'# UPGRADE {STEP_8_0}: convert team_runs again, as a batch: NAME = '
                           '"team_runs", FILES = ["team_runs.hql"], and DATABASE as 7.2\'s '
                           "admin/convert.ipynb set it")
    assert name.startswith("NAME =")
    checklist = (open_in_7_2 / "admin" / f"upgrade_{STEP_8_0}.md").read_text(encoding="utf-8")
    assert ("- [ ] admin/workflows/convert/convert.ipynb, cell 3, line 1: convert team_runs "
            "again") in checklist


def test_each_call_to_finish_conversion_is_marked(open_in_7_2: Path) -> None:
    project.upgrade()
    lines = (open_in_7_2 / "finish.py").read_text(encoding="utf-8").split("\n")
    assert lines[2:5] == [f"# {FINISHING}",
                          f"# UPGRADE {STEP_8_0}: finish_conversion is gone: delete this line, "
                          "convert the Hive again in admin/workflows/convert/convert.ipynb, "
                          "and promote its table for the name you gave here",
                          FINISHING]


def test_a_call_in_a_cell_with_a_magic_is_marked(open_in_7_2: Path) -> None:
    notebook = open_in_7_2 / "finish.ipynb"
    toolbox_module("notebooks").write_notebook(
        notebook, [("markdown", f"Run {FINISHING} last."), ("code", f"%time\n{FINISHING}")])
    project.upgrade()
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    assert cells[1]["source"][0] == "%time\n"
    assert cells[1]["source"][1].startswith(f"# UPGRADE {STEP_8_0}: finish_conversion is gone")
    assert "UPGRADE" not in "".join(cells[0]["source"])


def test_a_conversion_with_no_hive_says_where_its_files_are_kept(open_in_7_2: Path) -> None:
    (open_in_7_2 / "admin" / "conversions" / "team_runs" / "original.hql").unlink()
    project.upgrade()
    assert not (open_in_7_2 / "admin" / "workflows" / "convert" / "team_runs.hql").exists()
    mark = names_cell(open_in_7_2).split("\n")[0]
    assert "FILES =" not in mark
    assert "its Hive, which its 7.2 folder didn't hold, kept in admin/removed/" in mark


def test_each_name_databases_py_still_holds_unfilled_is_marked(open_in_7_2: Path) -> None:
    assert repr(project.upgrade()).split("\n")[1].startswith(
        f"{STEP_8_0}: 4 changes for you to make")
    lines = (open_in_7_2 / "admin" / "databases.py").read_text(encoding="utf-8").split("\n")
    marked = [number for number, line in enumerate(lines) if line.startswith("# UPGRADE")]
    assert [lines[number + 1].split(" =")[0] for number in marked] == ["DEV", "PROD"]


def test_a_filled_in_name_is_not_marked(open_in_7_2: Path) -> None:
    databases = open_in_7_2 / "admin" / "databases.py"
    # Toolbox 8.5: DEV's settings, its name and its root, both filled in.
    databases.write_text(toolbox_module("project").DATABASES_TEXT.replace(
        '"<DEV_DATABASE>"', '"mart_dev"').replace('"<DEV_LOCATION_ROOT>"', '"/data/team/dev"'),
        encoding="utf-8")
    project.upgrade()
    lines = databases.read_text(encoding="utf-8").split("\n")
    assert [line for line in lines if line.startswith("# UPGRADE")] == [
        f"# UPGRADE {STEP_8_0}: fill in your Prod Database's name"]


def test_a_template_you_changed_is_marked_and_one_as_written_is_written_again(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "7.2" / "starter", copy)
    changed = copy / "admin" / "templates" / "quality_checks.py"
    changed.write_text(changed.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    assert "# UPGRADE 8.1: new_table now writes" in changed.read_text(encoding="utf-8")
    written = (copy / "admin" / "templates" / "saved_table.py").read_text(encoding="utf-8")
    assert "PARTITIONED_BY = [" in written


def test_a_name_given_under_an_upgrade_mark_stays_given(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.0" / "starter", copy)
    notebook = copy / "admin" / "workflows" / "convert" / "convert.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if text.startswith("NAME = "):
            notebooks.write_cell_text(notebook, number, "# UPGRADE 8.0: convert it again\n"
                                      + text.replace("NAME = ''", "NAME = 'weekly'"))
    monkeypatch.chdir(copy)
    project.upgrade()
    names = next(text for kind, text in notebooks.read_cells(notebook) if "NAME = " in text)
    assert names.startswith("# UPGRADE 8.0: convert it again\nNAME = 'weekly'")


# --- An upgrade from 8.1 ----------------------------------------------------------------------


def hive_files(name: str) -> list[str]:
    """Each Table folder of an Example project whose Hive file its notebook's cell writes."""
    folder = ROOT / "example_projects" / name / "tables"
    return [f"{name}/{path.parent.name}" for path in sorted(folder.glob("*/*.hql"))
            if path.stem == path.parent.name]


@pytest.mark.parametrize("table", hive_files("starter") + hive_files("intermediate"))
def test_an_upgraded_notebooks_hive_cell_writes_the_example_projects_hive(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None, table: str) -> None:
    # Toolbox 8.2, 07: the cell 8.2 adds after the lineage cell writes the Hive a notebook
    # made by 8.2 writes.
    name, stem = table.split("/")
    copy = tmp_path / name
    shutil.copytree(UPGRADE_FROM / "8.1" / name, copy)
    monkeypatch.chdir(copy)
    project.upgrade()
    monkeypatch.setattr(sys, "path", list(sys.path))
    folder = copy / "tables" / stem
    notebook = folder / f"{stem}.ipynb"
    code = notebook_runner.code_cells(notebook)
    # Numbered from 1, as the runner counts code cells: the Project's, the logic and the Hive's.
    lineage = next(number for number, text in enumerate(code, 1) if "export_lineage(" in text)
    logic = next(number for number, text in enumerate(code, 1) if text.startswith("# logic"))
    assert code[lineage].endswith("\nexport_hive()")
    try:
        assert notebook_runner.run_notebook(notebook, {1, logic, lineage + 1}) == 0
    finally:
        forget_the_projects_modules()
    written = (folder / f"{stem}.hql").read_bytes()
    example = (ROOT / "example_projects" / name / "tables" / stem / f"{stem}.hql").read_bytes()
    assert written == example.replace(b"\r\n", b"\n")


def test_a_table_notebook_with_no_lineage_cell_is_marked(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    notebook = copy / "tables" / "mart__team_day" / "mart__team_day.ipynb"
    notebooks.write_notebook(notebook, [cell for cell in notebooks.read_cells(notebook)
                                        if "export_lineage(" not in cell[1]])
    monkeypatch.chdir(copy)
    project.upgrade()
    assert not any(text.endswith("export_hive()") for _, text in notebooks.read_cells(notebook))
    first = next(text for kind, text in notebooks.read_cells(notebook) if kind == "code")
    assert first.startswith(f"# UPGRADE {STEP_8_2}: this notebook has no lineage cell")
    assert "then run it to write mart__team_day.hql beside this notebook" in first
    checklist = (copy / "admin" / f"upgrade_{STEP_8_2}.md").read_text(encoding="utf-8")
    assert "- [ ] tables/mart__team_day/mart__team_day.ipynb, cell 2, line 1:" in checklist


# A Table notebook's text cell, and its compare cell's first lines, as 8.1 wrote them for a
# table new_table made from its query, mart_dev.failed_jobs.
TEXT_CELL_8_1 = (
    "# mart_dev.failed_jobs\n\nA Saved table the batch failed_jobs made, with "
    "project.convert(...), from the statements in `conversion/statement.hql`, as its script "
    "wrote them. Its logic cell builds the same query from the Toolbox's own functions, with "
    "create(), preview() and write(). Answer its open Decisions, which "
    "`conversion/checklist.md` lists, in the decisions cell of the convert Workflow's "
    "notebook, `admin/workflows/convert/convert.ipynb`, then run the cells top to bottom. The "
    "cells comparing it with the original stay until you delete them.")
COMPARE_AHEAD_8_1 = ("# The convert Workflow's step 6, project.compare_batch, compares this "
                     "table once written.\n# This compares its query with the original's "
                     "first:\n")


def test_a_name_given_in_8_1s_convert_notebook_stays_given_beside_rename(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    notebook = copy / "admin" / "workflows" / "convert" / "convert.ipynb"
    for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
        if text.startswith("NAME = "):
            assert "RENAME = " not in text
            notebooks.write_cell_text(notebook, number,
                                      text.replace("NAME = ''", "NAME = 'weekly'"))
    monkeypatch.chdir(copy)
    project.upgrade()
    names = next(text for _, text in notebooks.read_cells(notebook) if "NAME = " in text)
    assert names.startswith("NAME = 'weekly'")
    assert "\nRENAME = {}" in names


def test_a_table_new_table_made_names_new_tables_notebook_again(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Toolbox 8.2, 11 and 07: 8.1 sent the Decisions of a table new_table made from its query
    # to convert's notebook; 8.2's step names new_table's, as 8.2 writes them.
    monkeypatch.setattr(sys, "path", list(sys.path))
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    project.add_references(["ops.job_runs"], query=example_database.query)
    query = "SELECT r.run_id, r.job_id FROM ops.job_runs r WHERE r.dt = '2026-09-24'"
    project.new_table("mart_dev.failed_jobs", queries={"failed_jobs": query})
    folder = started / "tables" / "mart_dev__failed_jobs"
    notebook = folder / "mart_dev__failed_jobs.ipynb"
    checklist = folder / "conversion" / "checklist.md"
    as_8_2 = {path: path.read_text(encoding="utf-8") for path in (notebook, checklist)}
    # Its text cell, the opening of its compare cell and its checklist as 8.1 wrote them.
    notebooks.write_cell_text(notebook, 1, TEXT_CELL_8_1)
    for number, (_, text) in enumerate(notebooks.read_cells(notebook), 1):
        if text.startswith("# The new_table Workflow's compare step"):
            notebooks.write_cell_text(notebook, number,
                                      COMPARE_AHEAD_8_1 + text.split("\n", 2)[2])
    checklist.write_text(as_8_2[checklist].replace(
        "admin/workflows/new_table/new_table.ipynb", "admin/workflows/convert/convert.ipynb"),
        encoding="utf-8")
    assert all(path.read_text(encoding="utf-8") != as_8_2[path] for path in as_8_2)
    upgrades.write_project_version(started, "8.1")
    try:
        project.upgrade()
    finally:
        forget_the_projects_modules()
    assert {path: path.read_text(encoding="utf-8") for path in as_8_2} == as_8_2


def test_8_2_writes_warehouse_py_again_where_8_1_left_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    warehouse = copy / "warehouse.py"
    assert warehouse.read_text(encoding="utf-8") == upgrades.WAREHOUSE_TEXT_8_0
    monkeypatch.chdir(copy)
    project.upgrade()
    assert warehouse.read_text(encoding="utf-8") == project.WAREHOUSE_TEXT
    assert "from team_connection import conn" in project.WAREHOUSE_TEXT


def test_8_2_keeps_a_warehouse_py_you_changed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    warehouse = copy / "warehouse.py"
    mine = upgrades.WAREHOUSE_TEXT_8_0.replace("conn = example_database",
                                               "conn = my_api.connect()")
    warehouse.write_text(mine, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    assert warehouse.read_text(encoding="utf-8") == mine


def test_8_2_writes_check_references_again(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    notebook = copy / "admin" / "check_references.ipynb"
    assert "<a value>" in "".join(text for _, text in notebooks.read_cells(notebook))
    monkeypatch.chdir(copy)
    project.upgrade()
    assert notebooks.read_cells(notebook) == project.admin_notebook_cells("check_references")
    assert (copy / "admin" / "removed").is_dir()


# --- An upgrade from 8.2 ----------------------------------------------------------------------

# The step that marks a batch whose scripts hold Script tags.
STEP_8_3 = "8.3"


def test_a_batch_whose_scripts_hold_script_tags_is_marked_to_convert_again(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.2" / "starter", copy)
    scripts = copy / "admin" / "workflows" / "convert" / "closing" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "close.hql").write_text(
        "INSERT OVERWRITE TABLE mart.daily_close SELECT * FROM ops.job_runs r "
        'WHERE r.dt = <PARM="RUN_DAY"/>;\n', encoding="utf-8")
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_3}: 1 change for you to make" in said
    notebook = copy / "admin" / "workflows" / "convert" / "convert.ipynb"
    first = notebooks.read_cells(notebook)[0][1]
    assert first.startswith(f"# UPGRADE {STEP_8_3}: batch closing's scripts, in "
                            "admin/workflows/convert/closing/scripts/, hold Script tags")
    assert "giving each table a new name in RENAME" in first
    checklist = (copy / "admin" / f"upgrade_{STEP_8_3}.md").read_text(encoding="utf-8")
    assert "- [ ] admin/workflows/convert/convert.ipynb, cell 1, line 1: batch closing's" in (
        checklist)


def test_an_upgrade_from_8_2_with_no_script_tags_has_nothing_for_you_to_do(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "intermediate"
    shutil.copytree(UPGRADE_FROM / "8.2" / "intermediate", copy)
    monkeypatch.chdir(copy)
    assert f"{STEP_8_3}: nothing to change by hand." in repr(project.upgrade())


# --- 8.4 (ticket 13) ------------------------------------------------------------------------

STEP_8_4 = "8.4"
# A table 8.3 converted: a tag inside quotes, and a bare one in Hive kept whole, each read in
# its string as TAGS["NAME"] itself.
LOGIC_8_3 = '''# logic
from sqlglot_composer import FROM, SELECT, WHERE, Statement, equals, statement
from references.mart_dev__closing import TAGS, closing


def converted() -> Statement:
    return statement(SELECT(closing.team), FROM(closing),
                     WHERE(equals(closing.team, TAGS["SKIP_TEAM"])))


def kept() -> str:
    return "SELECT 1 FROM ops.job_runs r WHERE r.dt = " + TAGS["RUN_DAY"]
'''
REFERENCE_8_3 = '''TAGS = {
    "SKIP_TEAM": "nobody",  # inside quotes, at close.hql, line 3. Answer it with no quotes.
    "RUN_DAY": "'2026-09-24'",  # bare, at close.hql, line 4. Answer it with its quotes.
}
'''


def test_8_4_reads_a_tag_8_3_wrote_in_a_string_through_tag_text(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.3" / "starter", copy)
    folder = copy / "tables" / "mart_dev__closing"
    folder.mkdir(parents=True)
    notebooks.write_notebook(folder / "mart_dev__closing.ipynb", [("code", LOGIC_8_3)])
    (copy / "references" / "mart_dev__closing.py").write_text(REFERENCE_8_3, encoding="utf-8")
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_4}: nothing to change by hand." in said
    (logic,) = [text for _, text in notebooks.read_cells(folder / "mart_dev__closing.ipynb")]
    assert 'equals(closing.team, tag_text(TAGS["SKIP_TEAM"]))' in logic
    assert '" + tag_text(TAGS["RUN_DAY"], quoted=False)' in logic
    assert "from sqlglot_composer import tag_text  # for each Script tag in a string" in logic
    # The notebook as it was is kept.
    assert list((copy / "admin" / "removed").rglob("mart_dev__closing.ipynb"))


# --- 8.5 (ticket 13) ------------------------------------------------------------------------

STEP_8_5 = "8.5"


def _copy_of_8_4(tmp_path: Path) -> Path:
    """The starter Example project as 8.4 left it, to upgrade."""
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.4" / "starter", copy)
    return copy


def test_8_5_writes_dev_and_prod_as_database_settings_marking_each_root(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_4(tmp_path)
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"Upgraded the Project from 8.4 to {STEP_8_5}." in said
    text = (copy / "admin" / "databases.py").read_text(encoding="utf-8")
    assert 'DEV = {"database": "mart", "location_root": "<DEV_LOCATION_ROOT>"}' in text
    assert ('PROD = {"database": "<PROD_DATABASE>", "location_root": "<PROD_LOCATION_ROOT>"}'
            in text)
    marks = [line for line in text.split("\n") if line.startswith("# UPGRADE 8.5:")]
    assert len(marks) == 2 and 'fill in "location_root", the folder DEV' in marks[0]
    # The root an 8.4 location used, a Table reference's, is named.
    assert '"/data/your_team"' in marks[0] or "shows" not in marks[0]
    assert list((copy / "admin" / "removed").rglob("databases.py"))


def test_8_5_carries_partition_into_partitions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_4(tmp_path)
    notebook = copy / "admin" / "workflows" / "convert" / "convert.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if kind == "code" and "\nPARTITION = None" in f"\n{text}":
            notebooks.write_cell_text(notebook, number, text.replace(
                "PARTITION = None", 'PARTITION = {"dt": "2026-09-23"}'))
    monkeypatch.chdir(copy)
    project.upgrade()
    code = "\n".join(text for kind, text in notebooks.read_cells(notebook) if kind == "code")
    assert 'PARTITIONS = [{"dt": "2026-09-23"}]' in code
    assert "PARTITION =" not in code and "partition=PARTITION" not in code
    assert "partitions=PARTITIONS" in code


def test_8_5_marks_an_all_tables_location_root_a_decisions_cell_kept(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_4(tmp_path)
    notebook = copy / "admin" / "workflows" / "convert" / "convert.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if kind == "code" and text.startswith("DECISIONS ="):
            notebooks.write_cell_text(
                notebook, number, 'DECISIONS = {"all_tables": {"location_root": "/data/team"}}')
    monkeypatch.chdir(copy)
    project.upgrade()
    checklist = (copy / "admin" / "upgrade_8.5.md").read_text(encoding="utf-8")
    assert "location_root is a Database setting now" in checklist
    (cell,) = [text for kind, text in notebooks.read_cells(notebook)
               if kind == "code" and "DECISIONS = {" in text]
    assert cell.startswith("# UPGRADE 8.5: location_root is a Database setting now")


def test_8_5_marks_a_prod_copy_importing_devs_building_block(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_4(tmp_path)
    record = copy / "admin" / "workflows" / "promote" / "promoted.json"
    record.write_text(json.dumps({"team_prod.daily_job_runs": {
        "dev": "mart.daily_job_runs", "seeded": False}}), encoding="utf-8")
    folder = copy / "tables" / "team_prod__daily_job_runs"
    folder.mkdir(parents=True)
    notebooks.write_notebook(folder / "team_prod__daily_job_runs.ipynb", [
        ("code", "# logic\nfrom building_blocks.runs_per_job import runs_per_job\n")])
    monkeypatch.chdir(copy)
    project.upgrade()
    checklist = (copy / "admin" / "upgrade_8.5.md").read_text(encoding="utf-8")
    assert "this prod copy imports dev's Building block" in checklist
    (logic,) = [text for _, text in notebooks.read_cells(
        folder / "team_prod__daily_job_runs.ipynb")]
    assert logic.split("\n")[1].startswith("# UPGRADE 8.5: this prod copy imports dev's")


def test_8_5_marks_a_call_of_yours_giving_compare_batch_partition(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_4(tmp_path)
    script = copy / "compare_more.py"
    script.write_text('from sqlglot_composer import project\nfrom warehouse import query\n\n'
                      'project.compare_batch("weekly", query=query, '
                      'partition={"dt": "2026-09-23"})\n', encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    lines = script.read_text(encoding="utf-8").split("\n")
    assert lines[3].startswith("# UPGRADE 8.5: compare_batch takes partitions=, a list")
    assert lines[4].startswith("project.compare_batch(")
