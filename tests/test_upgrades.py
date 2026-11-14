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
from conftest import (awaiting_its_rewrite, forget_the_projects_modules, toolbox_folder,
                      toolbox_module)
import notebook_runner

import sqlglot_composer
import example_database
from sqlglot_composer import project, set_admin_log

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
# The same in a notebook's file, a line of a cell's source as Jupyter's JSON holds it, as
# `    "# UPGRADE 8.7: ...\n",`: a mark sits above a line, so it is never a cell's last.
UPGRADE_MARK_SOURCE_LINE = re.compile(rb'^[ \t]*"[ \t]*# UPGRADE \d+\.\d+: [^\n]*\\n",\n',
                                      re.MULTILINE)
# The step that rewrites a Project's import of the Example database, and what it writes in a
# setup cell where 8.6 connected the notebook to it (Toolbox 8.7, ticket 14).
STEP_8_7 = "8.7"
EXAMPLE_CONNECTION_8_7 = "import example_database\nconnect(example_database)"


def without_marks(cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """A notebook's cells with each UPGRADE mark's line left out."""
    return [(kind, UPGRADE_MARK_LINE.sub(b"", f"{text}\n".encode("utf-8")).decode("utf-8")[:-1])
            for kind, text in cells]


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
    # 8.6's ticket 09: the intermediate's Scheduled run, made with new_scheduled_run, which
    # registers it, and filled in, its Hive exported by hand; and both READMEs, which name
    # admin/'s scheduled_runs notebook, the intermediate's its run too.
    "8.6": {"starter": ("README.md",),
            "intermediate": ("README.md", "admin/registry.csv",
                             "scheduled_runs/weekly_team/")},
    # 8.7's ticket 08: the intermediate's schedule notebook names weekly_team, as the user
    # named it to make the run, which 8.7's step makes empty; and its README, which says so.
    "8.7": {"intermediate": ("admin/workflows/schedule/schedule.ipynb", "README.md")},
}
# What a version's Upgrade leaves as the version before wrote it, on purpose, by the version,
# such as {"8.4": ("admin/check_project.ipynb",)}: left out the same way, and kept the same
# way.
LEFT_AS_IT_WAS: dict[str, tuple[str, ...]] = {
    # A batch finished before 8.5 is history: its batch.md, its record and its scripts' copy
    # stay as that version wrote them.
    "8.5": ("admin/workflows/convert/finished/",),
    # So is one finished before 8.6: its record keeps the hash its converted table's notebook
    # had when the batch wrote it, before 8.6 connected the notebook.
    "8.6": ("admin/workflows/convert/finished/",),
}
# What the coming version's tickets changed in the Example projects before its Upgrade step is
# written, left out of every comparison until it is, and emptied once its step makes them, as
# 8.6's ticket 12 and 8.7's ticket 14 emptied it.
AWAITING_ITS_STEP: tuple[str, ...] = ()
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
            awaiting_its_rewrite(UPGRADE_MARK_SOURCE_LINE.sub(b"", UPGRADE_MARK_LINE.sub(
                b"", path.read_bytes().replace(b"\r\n", b"\n"))))
            for path in sorted(folder.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
            and kept(path.relative_to(folder).as_posix())}


def left_out_since(start_from: str, name: str) -> tuple[str, ...]:
    """What the comparison leaves out of the Example project `name` upgraded from `start_from`:
    what it gained by hand in each later version, GAINED_BY_HAND, and what each later version's
    Upgrade left as it was, LEFT_AS_IT_WAS."""
    left_out: list[str] = list(AWAITING_ITS_STEP)
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
    assert said[7].startswith("8.5: ")
    assert said[8].startswith("8.6: ")
    assert said[9].startswith(f"{VERSION}: ")
    assert said[10] == ("Read each step's checklist, in order: admin/upgrade_7.2.md, "
                        "admin/upgrade_8.0.md, admin/upgrade_8.1.md, admin/upgrade_8.2.md, "
                        "admin/upgrade_8.3.md, admin/upgrade_8.4.md, admin/upgrade_8.5.md, "
                        f"admin/upgrade_8.6.md and admin/upgrade_{VERSION}.md.")
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
    # Its cell 3, since 8.6, imports execute and connects, before the run_tables cells.
    assert source[1].startswith("from warehouse import connect, execute")


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
    notebook.write_bytes(awaiting_its_rewrite(notebook.read_bytes()))
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
    # Since 8.6 it takes each notebook's connection with connect(...), and the comment on a
    # connection kept outside the Project is in each notebook's setup cell.
    assert "def connect(connection: object) -> None:" in project.WAREHOUSE_TEXT


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
    assert "rewrote warehouse.py" not in (copy / "admin" / f"upgrade_{STEP_8_2}.md").read_text(
        encoding="utf-8")
    # Since 8.6, whose step keeps your conn line, as you wrote it, marked to move.
    lines = warehouse.read_text(encoding="utf-8").split("\n")
    at = lines.index("conn = my_api.connect()")
    assert lines[at - 1].startswith("# UPGRADE 8.6: 8.6 takes your connection in each notebook")


def test_8_2_writes_check_references_again(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = tmp_path / "starter"
    shutil.copytree(UPGRADE_FROM / "8.1" / "starter", copy)
    notebook = copy / "admin" / "check_references.ipynb"
    assert "<a value>" in "".join(text for _, text in notebooks.read_cells(notebook))
    monkeypatch.chdir(copy)
    project.upgrade()
    # Since 8.6, connected to the Example database, as the 8.1 Project's conn was, and since
    # 8.7 importing it from beside the Project, under 8.7's mark.
    placeholder = toolbox_module("project_templates").CONNECT_PLACEHOLDER
    connected = [(kind, text.replace(placeholder, EXAMPLE_CONNECTION_8_7))
                 for kind, text in project.admin_notebook_cells("check_references")]
    assert without_marks(notebooks.read_cells(notebook)) == connected
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
    assert f"Upgraded the Project from 8.4 to {VERSION}." in said
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
    # As each later step writes the notebook again, the value given stays, written as Python.
    workflows = toolbox_module("workflows")
    convert = next(each for each in workflows.WORKFLOWS if each.name == "convert")
    assert workflows.given_inputs(copy, convert)["PARTITIONS"] == [{"dt": "2026-09-23"}]
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


# --- 8.6 (ticket 12) ------------------------------------------------------------------------

STEP_8_6 = "8.6"
# The line each notebook's setup cell is filled with, where warehouse.py's conn was the Example
# database, as the Example projects fill theirs.
EXAMPLE_CONNECTION = "from sqlglot_composer import example_database\nconnect(example_database)"
CONNECT_PLACEHOLDER = toolbox_module("project_templates").CONNECT_PLACEHOLDER
# A warehouse.py as 8.2 to 8.5 wrote it, its conn changed to the user's own connection.
YOUR_CONNECTION = ("import my_api  # the team's library\n"
                   'conn = my_api.connect(host="hive.example",\n'
                   '                      user="me")')


def _copy_of_8_5(tmp_path: Path, name: str = "starter") -> Path:
    """An Example project as 8.5 left it, to upgrade."""
    copy = tmp_path / name
    shutil.copytree(UPGRADE_FROM / "8.5" / name, copy)
    return copy


def _code(notebook: Path) -> str:
    """A notebook's code cells, as one text."""
    return "\n".join(text for kind, text in notebooks.read_cells(notebook) if kind == "code")


def _with_your_connection(copy: Path) -> Path:
    """The Project's warehouse.py with conn set to the user's own connection."""
    warehouse = copy / "warehouse.py"
    text = warehouse.read_text(encoding="utf-8")
    assert "\nconn = example_database\n" in text
    warehouse.write_text(text.replace("from sqlglot_composer import example_database\n", "")
                         .replace("conn = example_database", YOUR_CONNECTION), encoding="utf-8")
    return warehouse


def test_8_6_connects_each_notebook_to_the_example_database_as_conn_was(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_6}: nothing to change by hand." in said
    assert (copy / "warehouse.py").read_text(encoding="utf-8") == project.WAREHOUSE_TEXT
    assert list((copy / "admin" / "removed").rglob("warehouse.py"))
    for notebook in [copy / "tables" / "mart__team_day" / "mart__team_day.ipynb",
                     copy / "admin" / "workflows" / "new_table" / "new_table.ipynb",
                     copy / "admin" / "check_references.ipynb",
                     copy / "admin" / "run_tables.ipynb",
                     copy / "admin" / "scheduled_runs.ipynb"]:
        code = _code(notebook)
        assert "from warehouse import connect" in code, notebook
        # As 8.6 connected it, its import rewritten by 8.7's step.
        assert f"\n{EXAMPLE_CONNECTION_8_7}" in code, notebook
        assert CONNECT_PLACEHOLDER not in code.split("\n"), notebook
    assert (copy / "scheduled_runs").is_dir()
    # Each Template, written again or added, is left as start() writes it: its line to fill in.
    for template in ("saved_table", "quality_checks", "scheduled_run"):
        text = (copy / "admin" / "templates" / f"{template}.py").read_text(encoding="utf-8")
        assert CONNECT_PLACEHOLDER in text.split("\n"), template
        assert "connect(example_database)" not in text.split("\n"), template
    checklist = (copy / "admin" / "upgrade_8.6.md").read_text(encoding="utf-8")
    assert ("- connected each Toolbox notebook that reaches the warehouse to the Example "
            "database, as warehouse.py's conn was") in checklist


def test_8_6_keeps_your_connection_in_warehouse_py_and_marks_it_to_move(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = _with_your_connection(copy)
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_6}: 1 change for you to make" in said
    text = warehouse.read_text(encoding="utf-8")
    assert "def connect(connection: object) -> None:" in text
    # Kept as you wrote it, each line, under the mark; nothing of it rewritten.
    lines = text.split("\n")
    at = lines.index("import my_api  # the team's library")
    assert lines[at + 1].startswith(f"# UPGRADE {STEP_8_6}: 8.6 takes your connection in each "
                                    "notebook")
    assert "\n".join(lines[at + 2:at + 4]) == YOUR_CONNECTION.split("\n", 1)[1]
    # The file is the one start() writes, but for your lines and the mark.
    assert UPGRADE_MARK_LINE.sub(b"", text.encode("utf-8")).decode("utf-8") == (
        project.WAREHOUSE_TEXT.replace(
            "import pandas as pd\n",
            "import pandas as pd\n\n" + upgrades.KEPT_CONNECTION_HEADING + "\n"
            + YOUR_CONNECTION + "\n", 1))
    # Each notebook's line is left for you to fill in.
    code = _code(copy / "tables" / "mart__team_day" / "mart__team_day.ipynb")
    assert "from warehouse import connect, query" in code
    assert CONNECT_PLACEHOLDER in code.split("\n")
    assert "example_database" not in code
    checklist = (copy / "admin" / "upgrade_8.6.md").read_text(encoding="utf-8")
    assert "- [ ] warehouse.py, line" in checklist


def test_8_6_marks_a_warehouse_py_whose_calls_you_wrote_yourself(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = copy / "warehouse.py"
    mine = warehouse.read_text(encoding="utf-8").replace(
        "return conn.query(hive)", "return conn.cursor().fetch(hive)")
    warehouse.write_text(mine, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    text = warehouse.read_text(encoding="utf-8")
    # Kept as it is, but for 8.7's step importing the Example database from beside it.
    assert UPGRADE_MARK_LINE.sub(b"", text.encode("utf-8")).decode("utf-8") == mine.replace(
        "from sqlglot_composer import example_database", "import example_database")
    marks = [line for line in text.split("\n") if line.startswith("# UPGRADE")]
    assert [mark.split(":")[0] for mark in marks] == [f"# UPGRADE {STEP_8_7}",
                                                      f"# UPGRADE {STEP_8_6}"]
    assert marks[1].startswith(
        f"# UPGRADE {STEP_8_6}: 8.6's notebooks import connect from here")


def test_8_6_keeps_your_comments_with_the_lines_of_yours_they_sit_by(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = copy / "warehouse.py"
    yours = ("# The team's library, installed by IT\nimport my_api\n\n"
             "# The prod host: ask Sam before changing it\n"
             'conn = my_api.connect(host="hive.example")')
    text = warehouse.read_text(encoding="utf-8")
    shared = "\n# Both calls share one session\n\ndef query"
    warehouse.write_text(text.replace("from sqlglot_composer import example_database\n", "")
                         .replace("conn = example_database", yours)
                         .replace("\n\ndef query", shared), encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    lines = warehouse.read_text(encoding="utf-8").split("\n")
    at = lines.index(upgrades.KEPT_CONNECTION_HEADING.split("\n")[-1])
    # Each comment of yours kept where it sat, the mark right above the line setting conn.
    assert lines[at + 1:at + 7] == [
        "# The team's library, installed by IT", "import my_api", "",
        "# The prod host: ask Sam before changing it", lines[at + 5],
        'conn = my_api.connect(host="hive.example")']
    assert lines[at + 5].startswith(f"# UPGRADE {STEP_8_6}: 8.6 takes your connection")
    assert lines[at + 7:at + 9] == ["", "# Both calls share one session"]
    # The comment 8.2 wrote above conn is the Toolbox's, and goes with its conn.
    assert "#     from team_connection import conn" not in lines
    assert not [line for line in lines if line.startswith("# Your connection to the warehouse. "
                                                          "At work, replace example_database")]


def test_8_6_keeps_a_conn_set_in_a_try_and_marks_it_to_move(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = copy / "warehouse.py"
    yours = ("try:\n    from team_connection import conn\nexcept ImportError:\n"
             "    conn = example_database")
    text = warehouse.read_text(encoding="utf-8")
    warehouse.write_text(text.replace("conn = example_database", yours), encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    text = warehouse.read_text(encoding="utf-8")
    assert "def connect(connection: object) -> None:" in text
    lines = text.split("\n")
    at = lines.index("try:")
    assert lines[at - 1].startswith(f"# UPGRADE {STEP_8_6}: 8.6 takes your connection in each "
                                    "notebook")
    assert "\n".join(lines[at:at + 4]) == yours
    # Its import of the Example database, rewritten by 8.7's step under its mark.
    at = lines.index("import example_database")
    assert lines[at - 1].startswith(f"# UPGRADE {STEP_8_7}: ")


def test_8_6_marks_a_connect_of_your_own_in_warehouse_py(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = copy / "warehouse.py"
    mine = ("import my_api\n\nconn = None\n\n\ndef connect() -> None:\n    global conn\n"
            "    conn = my_api.connect()\n\n\ndef query(hive: str) -> object:\n"
            "    return conn.query(hive)\n\n\ndef execute(hive: str) -> None:\n"
            "    conn.execute(hive)\n")
    warehouse.write_text(mine, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    text = warehouse.read_text(encoding="utf-8")
    assert UPGRADE_MARK_LINE.sub(b"", text.encode("utf-8")).decode("utf-8") == mine
    lines = text.split("\n")
    at = lines.index("def connect() -> None:")
    assert lines[at - 1].startswith(f"# UPGRADE {STEP_8_6}: 8.6's notebooks each call "
                                    "connect(...)")


def test_8_6_leaves_8_6s_own_connect_in_warehouse_py(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    warehouse = copy / "warehouse.py"
    # 8.6's, its connect's docstring reworded: still 8.6's connect.
    text = project.WAREHOUSE_TEXT
    at = text.index('"""', text.index("def connect(")) + 3
    ours = f"{text[:at]}Yours, reworded: {text[at:]}"
    warehouse.write_text(ours, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    assert warehouse.read_text(encoding="utf-8") == ours


def test_8_6_marks_each_import_of_conn_once_warehouse_py_has_none(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    helpers = copy / "building_blocks" / "helpers.py"
    helpers.write_text("from warehouse import (\n    conn,\n)\n\n\ndef rows() -> object:\n"
                       "    return conn.query('SELECT 1')\n", encoding="utf-8")
    other = copy / "building_blocks" / "other.py"
    other.write_text("import warehouse\n\nTABLES = warehouse.conn.query('SHOW TABLES')\n",
                     encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    assert re.search(r"^conn\b", (copy / "warehouse.py").read_text(encoding="utf-8"),
                     re.MULTILINE) is None
    for path, line in ((helpers, "from warehouse import ("),
                       (other, "TABLES = warehouse.conn.query('SHOW TABLES')")):
        lines = path.read_text(encoding="utf-8").split("\n")
        at = lines.index(line)
        mark = f"# UPGRADE {STEP_8_6}: 8.6's warehouse.py has no conn"
        assert lines[at - 1].startswith(mark), path
    checklist = (copy / "admin" / "upgrade_8.6.md").read_text(encoding="utf-8")
    assert ("- [ ] building_blocks/helpers.py, line 1: 8.6's warehouse.py has no conn"
            in checklist)


def test_8_6_connects_a_table_notebook_whose_import_is_over_several_lines(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    notebook = copy / "tables" / "mart__team_day" / "mart__team_day.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if kind == "code" and "\nfrom warehouse import query" in text:
            notebooks.write_cell_text(notebook, number, text.replace(
                "from warehouse import query", "from warehouse import (\n    query,\n)"))
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_6}: nothing to change by hand." in said
    code = _code(notebook)
    assert "from warehouse import (\n    query,\n)\nfrom warehouse import connect\n" in code
    assert f"\n{EXAMPLE_CONNECTION_8_7}" in code


def test_8_6_marks_a_table_notebook_it_cant_connect(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    notebook = copy / "tables" / "mart__team_day" / "mart__team_day.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if kind == "code" and "\nfrom warehouse import query" in text:
            notebooks.write_cell_text(notebook, number, text.replace(
                "from warehouse import query",
                "try:\n    from warehouse import query\nexcept ImportError:\n    query = None"))
            cell = number
    monkeypatch.chdir(copy)
    project.upgrade()
    lines = notebooks.read_cells(notebook)[cell - 1][1].split("\n")
    at = lines.index("    from warehouse import query")
    assert lines[at - 1].startswith(f"    # UPGRADE {STEP_8_6}: 8.6's query and execute refuse "
                                    "until this notebook connects")


def test_8_6_rewrites_each_admin_notebooks_one_text_cell() -> None:
    # The step writes each admin notebook's first cell as 8.6's: in 8.5 and 8.6 it is the only
    # text cell each has.
    for name in project.ADMIN_NOTEBOOKS:
        kinds = [kind for kind, _ in project.admin_notebook_cells(name)]
        assert kinds.count("markdown") == 1 and kinds[0] == "markdown", name
        frozen = UPGRADE_FROM / "8.5" / "starter" / "admin" / f"{name}.ipynb"
        if frozen.is_file():
            kinds = [kind for kind, _ in notebooks.read_cells(frozen)]
            assert kinds.count("markdown") == 1 and kinds[0] == "markdown", name


def test_8_6_keeps_the_connection_a_workflow_notebook_gives(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A Project 8.6 wrote, recorded as 8.5: a Workflow notebook written again keeps the
    # connection you gave its setup cell.
    notebook = started / "admin" / "workflows" / "promote" / "promote.ipynb"
    mine = "from team_connection import conn\nconnect(conn)"
    for number, (kind, text) in enumerate(notebooks.read_cells(notebook), 1):
        if kind == "code" and CONNECT_PLACEHOLDER in text.split("\n"):
            notebooks.write_cell_text(notebook, number, text.replace(CONNECT_PLACEHOLDER, mine))
    upgrades.write_project_version(started, "8.5")
    project.upgrade()
    code = _code(notebook)
    assert f"#     connect(conn)\n{mine}\n" in f"{code}\n"
    assert CONNECT_PLACEHOLDER not in code.split("\n")


def test_8_6_keeps_what_you_named_in_remove_and_adds_scheduled_runs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    remove = copy / "admin" / "remove.ipynb"
    for number, (kind, text) in enumerate(notebooks.read_cells(remove), 1):
        if kind == "code" and text.startswith("TABLES = []"):
            notebooks.write_cell_text(remove, number,
                                      text.replace("TABLES = []", 'TABLES = ["mart.team_day"]'))
    monkeypatch.chdir(copy)
    project.upgrade()
    code = _code(remove)
    assert 'TABLES = ["mart.team_day"]  # Table folders to archive' in code
    assert "\nSCHEDULED_RUNS = []  # Scheduled runs to archive" in code
    assert code.endswith("if SCHEDULED_RUNS:\n    print(project.remove_scheduled_run("
                         "SCHEDULED_RUNS))")
    cells = notebooks.read_cells(remove)
    assert cells[0] == project.admin_notebook_cells("remove")[0]


def test_8_6_marks_a_notebook_of_yours_that_reaches_the_warehouse(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    notebooks.write_notebook(mine, [("markdown", "Mine"),
                                    ("code", "from warehouse import query\nquery('SELECT 1')")])
    module = copy / "building_blocks" / "run_values.py"
    module.write_text("from warehouse import query\n", encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    code = notebooks.read_cells(mine)[1][1].split("\n")
    assert code[0].startswith(f"# UPGRADE {STEP_8_6}: 8.6's query and execute refuse until "
                              "this notebook connects")
    # 8.7's Toolbox has no Example database to connect it to, so the mark doesn't offer one
    # (drift D514).
    assert "example_database" not in code[0]
    assert code[1] == "from warehouse import query"
    # A module of yours runs on the connection of the notebook that imports it: not marked.
    assert module.read_text(encoding="utf-8") == "from warehouse import query\n"


def test_8_6_keeps_the_promoted_record_of_a_prod_copy_it_connects(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    relative = "tables/mart__team_day/mart__team_day.ipynb"
    record = copy / "admin" / "workflows" / "promote" / "promoted.json"
    record.write_text(json.dumps({"mart.team_day": {
        "dev": "mart_dev.team_day", "seeded": False,
        "files": {relative: toolbox_module("project")._hash((copy / relative).read_bytes()),
                  "tables/mart__team_day/gone.md": "0" * 64}}}), encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    files = json.loads(record.read_text(encoding="utf-8"))["mart.team_day"]["files"]
    assert files[relative] == toolbox_module("project")._hash((copy / relative).read_bytes())
    assert files["tables/mart__team_day/gone.md"] == "0" * 64
    assert f"Edited by hand, which project.promote writes over: {relative}" not in repr(
        project.check())


# --- 8.7 (ticket 14) ------------------------------------------------------------------------

# The import forms a Project may hold of the Example database, as the Toolbox held it before
# 8.7 (ticket 12's Answer), each in a notebook of the user's own: each form, and what 8.7's
# step writes in its place.
FORMS_8_6 = {
    "alone": ("from sqlglot_composer import example_database\nquery = example_database.query",
              "import example_database\nquery = example_database.query"),
    "among others": ("from sqlglot_composer import example_database, project  # both\n"
                     "project.check()",
                     "import example_database\nfrom sqlglot_composer import project  # both\n"
                     "project.check()"),
    "in brackets": ("from sqlglot_composer import (\n    project,\n    example_database,\n)",
                    "import example_database\nfrom sqlglot_composer import (\n    project,\n)"),
    "as a name of yours": ("from sqlglot_composer import example_database as demo\n"
                           "demo.query('SELECT 1')",
                           "import example_database as demo\ndemo.query('SELECT 1')"),
    "names from it": ("from sqlglot_composer.example_database import jobs, job_runs",
                      "from example_database import jobs, job_runs"),
    "through the package": ("import sqlglot_composer.example_database\n"
                            "jobs = sqlglot_composer.example_database.jobs",
                            "import sqlglot_composer, example_database\n"
                            "jobs = example_database.jobs"),
    "reached by the package": ("import sqlglot_composer\n\n"
                               "rows = sqlglot_composer.example_database.query('SELECT 1')",
                               "import sqlglot_composer\nimport example_database\n\n"
                               "rows = example_database.query('SELECT 1')"),
    "by the star import": ("from sqlglot_composer import *\n"
                           "jobs, job_runs = example_database.jobs, example_database.job_runs",
                           "from sqlglot_composer import *\nimport example_database\n"
                           "jobs, job_runs = example_database.jobs, example_database.job_runs"),
}
# How many marks each form leaves: one at each line it rewrote.
MARKS_LEFT = {"through the package": 2, "reached by the package": 2}
# The first words of 8.7's mark on an import of the Example database it rewrote.
NO_EXAMPLE_DATABASE = f"# UPGRADE {STEP_8_7}: 8.7's Toolbox has no Example database"
MARK_LINE_TEXT = re.compile(r"# UPGRADE \d+\.\d+: ")


def _copy_of_8_6(tmp_path: Path, name: str = "starter") -> Path:
    """An Example project as 8.6 left it, to upgrade."""
    copy = tmp_path / name
    shutil.copytree(UPGRADE_FROM / "8.6" / name, copy)
    return copy


def _marks_of(text: str) -> list[str]:
    """Each UPGRADE mark's line in a text, its indent stripped."""
    return [line.strip() for line in text.split("\n") if MARK_LINE_TEXT.match(line.strip())]


@pytest.mark.parametrize("form", list(FORMS_8_6))
def test_8_7_rewrites_an_import_of_the_example_database_and_marks_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None, form: str) -> None:
    copy = _copy_of_8_6(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    before, after = FORMS_8_6[form]
    notebooks.write_notebook(mine, [("markdown", "Mine"), ("code", "x = 1"), ("code", before)])
    monkeypatch.chdir(copy)
    project.upgrade()
    cells = notebooks.read_cells(mine)
    # Each line of yours kept, but for what it rewrote, each under a mark.
    assert without_marks(cells) == [("markdown", "Mine"), ("code", "x = 1"), ("code", after)]
    marks = _marks_of(cells[2][1])
    assert len(marks) == MARKS_LEFT.get(form, 1)
    assert all(mark.startswith(NO_EXAMPLE_DATABASE) for mark in marks)
    assert "your team's connection" in marks[0]
    assert list((copy / "admin" / "removed").rglob("scratch.ipynb"))
    checklist = (copy / "admin" / f"upgrade_{STEP_8_7}.md").read_text(encoding="utf-8")
    assert "- [ ] tables/mart__team_day/scratch.ipynb, cell 3, line" in checklist


def test_8_7_rewrites_an_import_in_a_py_file_and_leaves_a_comment_naming_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    helpers = copy / "building_blocks" / "helpers.py"
    helpers.write_text("# from sqlglot_composer import example_database, once\n"
                       "def rows() -> object:\n"
                       "    from sqlglot_composer import example_database\n"
                       "    return example_database.query('SELECT 1')\n", encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    lines = helpers.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "# from sqlglot_composer import example_database, once"
    at = lines.index("    import example_database")
    assert lines[at - 1].startswith(f"    {NO_EXAMPLE_DATABASE}")
    assert lines[at + 1] == "    return example_database.query('SELECT 1')"


def test_8_7_marks_an_import_in_code_it_cant_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    code = "from sqlglot_composer import example_database\nif True\n    pass"
    notebooks.write_notebook(mine, [("code", code)])
    monkeypatch.chdir(copy)
    project.upgrade()
    ((_, text),) = notebooks.read_cells(mine)
    lines = text.split("\n")
    assert lines[0].startswith(f"{NO_EXAMPLE_DATABASE}, and 8.7 couldn't read this code")
    assert "\n".join(lines[1:]) == code


def test_8_7_leaves_a_name_example_database_of_your_own(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    code = "from sqlglot_composer import *\nexample_database = 'mine'\nprint(example_database)"
    notebooks.write_notebook(mine, [("code", code)])
    monkeypatch.chdir(copy)
    project.upgrade()
    assert notebooks.read_cells(mine) == [("code", code)]


def test_8_7_imports_the_example_database_from_beside_the_project(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    monkeypatch.chdir(copy)
    said = repr(project.upgrade())
    assert f"{STEP_8_7}: " in said and "for you to make" in said
    notebook = copy / "tables" / "mart__team_day" / "mart__team_day.ipynb"
    code = _code(notebook)
    assert f"\n{EXAMPLE_CONNECTION_8_7}" in code
    assert "sqlglot_composer import example_database" not in code
    # The new schedule notebook is connected as the Project's other Workflow notebooks are.
    schedule = copy / "admin" / "workflows" / "schedule" / "schedule.ipynb"
    assert f"\n{EXAMPLE_CONNECTION_8_7}" in _code(schedule)
    # warehouse.py says 8.7's words, naming no Example database.
    assert (copy / "warehouse.py").read_text(encoding="utf-8") == project.WAREHOUSE_TEXT


def test_8_7_rewords_a_warehouse_py_you_changed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    warehouse = copy / "warehouse.py"
    mine = warehouse.read_text(encoding="utf-8").replace(
        "return _connection.query(hive)", "return _connection.fetch(hive)")
    assert "_connection.fetch(hive)" in mine
    warehouse.write_text(mine, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    text = warehouse.read_text(encoding="utf-8")
    assert "_connection.fetch(hive)" in text
    assert "example_database" not in text
    assert _marks_of(text) == []


def test_8_7_marks_a_warehouse_py_line_still_naming_the_example_database(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    warehouse = copy / "warehouse.py"
    mine = warehouse.read_text(encoding="utf-8").replace(
        "connect(example_database) in the Example projects. If yours",
        "connect(example_database) at home. If yours")
    warehouse.write_text(mine, encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    lines = warehouse.read_text(encoding="utf-8").split("\n")
    (at,) = [number for number, line in enumerate(lines) if "connect(example_database)" in line
             and "# UPGRADE" not in line]
    assert lines[at - 1].strip().startswith(f"{NO_EXAMPLE_DATABASE}, and this line still "
                                            "shows connect(example_database)")


def test_8_7_takes_new_runs_out_of_scheduled_runs_keeping_your_cells(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    notebook = copy / "admin" / "scheduled_runs.ipynb"
    notebooks.write_notebook(notebook, [*notebooks.read_cells(notebook),
                                        ("code", "print('mine')")])
    monkeypatch.chdir(copy)
    project.upgrade()
    cells = notebooks.read_cells(notebook)
    assert "NEW_RUNS" not in "\n".join(text for _, text in cells)
    assert cells[-1] == ("code", "print('mine')")
    # The rest as 8.7 writes it, its text cell too, but for the connection.
    placeholder = toolbox_module("project_templates").CONNECT_PLACEHOLDER
    fresh = [(kind, text.replace(placeholder, EXAMPLE_CONNECTION_8_7))
             for kind, text in project.admin_notebook_cells("scheduled_runs")]
    assert without_marks(cells[:-1]) == fresh
    assert list((copy / "admin" / "removed").rglob("scheduled_runs.ipynb"))


def test_8_7_marks_the_schedule_notebook_for_a_run_new_runs_named_and_didnt_make(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    notebook = copy / "admin" / "scheduled_runs.ipynb"
    notebooks.write_notebook(notebook, [
        (kind, text.replace("NEW_RUNS = []", 'NEW_RUNS = ["daily"]'))
        for kind, text in notebooks.read_cells(notebook)])
    monkeypatch.chdir(copy)
    project.upgrade()
    schedule = copy / "admin" / "workflows" / "schedule" / "schedule.ipynb"
    code = _code(schedule).split("\n")
    at = next(number for number, line in enumerate(code) if line.startswith("NAME = "))
    assert code[at - 1].startswith(f"# UPGRADE {STEP_8_7}: 8.6's NEW_RUNS")
    assert "'daily'" in code[at - 1]
    assert "NEW_RUNS" not in _code(notebook)


def test_8_7_marks_a_cell_of_yours_using_new_runs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    notebook = copy / "admin" / "scheduled_runs.ipynb"
    notebooks.write_notebook(notebook, [
        (kind, text.replace("    print(project.new_scheduled_run(NEW_RUNS))",
                            "    print(project.new_scheduled_run(NEW_RUNS))\nprint('mine')"))
        for kind, text in notebooks.read_cells(notebook)])
    monkeypatch.chdir(copy)
    project.upgrade()
    (yours,) = [text for _, text in notebooks.read_cells(notebook) if "NEW_RUNS" in text]
    assert yours.startswith(f"# UPGRADE {STEP_8_7}: 8.7 makes a Scheduled run in the schedule "
                            "Workflow")
    assert yours.endswith("print('mine')")


# What the 8.6 Toolbox's step wrote, where conn was the Example database, that told the user to
# do what 8.7 can't (drift D514).
SAID_BY_8_6 = (
    "8.6's query and execute refuse until this notebook connects: import connect with them, "
    "and call connect(...) with your connection under this line, such as "
    "connect(example_database), as warehouse.py's conn was",
    "8.6's warehouse.py has no conn, which was the Example database: here, import it as `from "
    "sqlglot_composer import example_database` and use it in conn's place, or call "
    "warehouse's query and execute, which use the connection the notebook running this gave "
    "connect(...)",
)


def test_8_7_rewords_each_mark_8_6_left_that_offered_the_example_database(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_6(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    notebooks.write_notebook(mine, [("code", f"# UPGRADE 8.6: {SAID_BY_8_6[0]}\n"
                                             "from warehouse import query")])
    helpers = copy / "building_blocks" / "helpers.py"
    helpers.write_text(f"# UPGRADE 8.6: {SAID_BY_8_6[1]}\nfrom warehouse import conn\n",
                       encoding="utf-8")
    checklist = copy / "admin" / "upgrade_8.6.md"
    checklist.write_text(
        f"# Upgrade to 8.6\n\n- [ ] tables/mart__team_day/scratch.ipynb, cell 1, line 1: "
        f"{SAID_BY_8_6[0]}\n- [ ] building_blocks/helpers.py, line 1: {SAID_BY_8_6[1]}\n",
        encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    assert _marks_of(_code(mine)) == [f"# UPGRADE 8.6: {upgrades.CONNECT_HERE}"]
    assert _marks_of(helpers.read_text(encoding="utf-8")) == [
        f"# UPGRADE 8.6: {upgrades.CONN_GONE}"]
    assert checklist.read_text(encoding="utf-8") == (
        f"# Upgrade to 8.6\n\n- [ ] tables/mart__team_day/scratch.ipynb, cell 1, line 1: "
        f"{upgrades.CONNECT_HERE}\n- [ ] building_blocks/helpers.py, line 1: "
        f"{upgrades.CONN_GONE}\n")
    for said in (upgrades.CONNECT_HERE, upgrades.CONN_GONE):
        assert "example_database" not in said


def test_an_8_5_project_upgraded_to_8_7_is_told_nothing_8_7_cant_do(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    copy = _copy_of_8_5(tmp_path)
    mine = copy / "tables" / "mart__team_day" / "scratch.ipynb"
    notebooks.write_notebook(mine, [("code", "from warehouse import query")])
    (copy / "building_blocks" / "helpers.py").write_text("from warehouse import conn\n",
                                                         encoding="utf-8")
    monkeypatch.chdir(copy)
    project.upgrade()
    told = "\n".join([*upgrades.marks_in(copy, upgrades.MARK_LINE),
                      (copy / "admin" / "upgrade_8.6.md").read_text(encoding="utf-8")])
    assert f"{upgrades.CONNECT_HERE}\n" in f"{told}\n"
    assert upgrades.CONN_GONE in told
    for said in SAID_BY_8_6:
        assert said not in told
    assert "sqlglot_composer import example_database" not in told


def test_8_7_loses_no_line_of_the_example_projects_but_the_imports_it_rewrites(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned: None) -> None:
    # Each file but warehouse.py and scheduled_runs.ipynb, whose words and NEW_RUNS cell 8.7
    # changes, holds each line it held, but for each import of the Example database.
    copy = _copy_of_8_6(tmp_path, "intermediate")
    before = files_of(copy)
    monkeypatch.chdir(copy)
    project.upgrade()
    after = files_of(copy)
    for relative, text in before.items():
        if relative in ("warehouse.py", "admin/scheduled_runs.ipynb",
                        "admin/project_version.txt"):
            continue
        written = text.replace(b"from sqlglot_composer import example_database",
                               b"import example_database")
        assert after[relative] == written, relative
