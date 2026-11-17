"""The Lineage difference: Toolbox 8.8, ticket 05.

"Highlight when and where changes occured" (the map). project.export_lineage_difference()
reads admin/lineage/lineage_state.csv and writes what changed between two points as an HTML
page and its Markdown twin: each Own change with its logic before and after, each Inherited
change with its chain down to the change it comes from, the Building blocks behind them, an
Upgrade's rewrites apart, and when admin/sent.csv says each changed Saved table was next
written. These tests drive lineage_difference.difference with recordings made by
lineage_state.record from columns written out by hand, as test_lineage_state does, and run the
export end to end on the Intermediate Example project.
"""

from __future__ import annotations

import datetime
import re
import shutil
import sys
from pathlib import Path

import pytest
from conftest import ROOT, toolbox_module
from offline_policy import external_references
from test_html_page import markdown_lines, text_shown
from test_lineage_state import FIRST_TIME, chain, column, logic_of, start_registry_folder

from sqlglot_composer import project
from sqlglot_composer.lineage_difference import (Difference, difference, effective_logic_text,
                                                 to_html, to_markdown)
from sqlglot_composer.lineage_state import columns_at, read_rows, record

# What admin/sent.csv holds after its header: one write of each table, a minute apart from
# the recordings, which are a minute apart from each other from FIRST_TIME.
SENT_HEADER = "time,kind,tables,script\n"
FOOTER = "Made by a test."


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project's folder, holding its registry, with its clock at FIRST_TIME, a minute on at
    each recording."""
    start_registry_folder(tmp_path)
    times = iter(FIRST_TIME + datetime.timedelta(minutes=n) for n in range(100))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: next(times))
    return tmp_path


def changed_up_the_chain(root: Path) -> list[dict[str, str]]:
    """Two recordings of the chain: the first, then mart.team_failures.fails changed at the
    table itself, which mart.team_report.fail_rate reads."""
    record(root, chain(), "first")
    record(root, chain(up_own="up-2", up_effective="up-e2", down_effective="down-e2"),
           "tables/mart__team_failures/mart__team_failures.ipynb export_hive()")
    return read_rows(root)


def by_table(found: Difference) -> dict[str, str]:
    return {table.table: table.change for table in found.tables}


# --- What changed -----------------------------------------------------------------------------


def test_an_own_change_and_the_inherited_change_it_makes_downstream(root: Path) -> None:
    found = difference(changed_up_the_chain(root))

    assert found.start == "2026-11-20 06:00:00"
    assert found.end == "2026-11-20 06:01:00"
    assert by_table(found) == {"mart.team_failures": "own", "mart.team_report": "inherited"}
    up, down = found.tables
    fails = up.columns[0]
    assert (fails.change, fails.before["own_logic"], fails.after["own_logic"]) == (
        "own", "<up-1>", "<up-2>")
    fail_rate = down.columns[0]
    assert fail_rate.change == "inherited"
    assert fail_rate.chains == (("mart.team_report.fail_rate", "mart.team_failures.fails"),)
    assert fail_rate.before["own_logic"] == fail_rate.after["own_logic"]


def test_the_effective_logic_is_written_out_down_to_the_tables_the_project_doesnt_write(
        root: Path) -> None:
    rows = changed_up_the_chain(root)

    text = effective_logic_text(columns_at(rows), "mart.team_report.fail_rate")

    assert text.splitlines() == ["mart.team_report.fail_rate = <down-1>",
                                 "└─ mart.team_failures.fails = <up-2>",
                                 "   └─ ops.job_events.event_type  (string)"]
    found = difference(rows)
    assert "<up-1>" in found.tables[1].columns[0].effective_before
    assert "<up-2>" in found.tables[1].columns[0].effective_after


def test_a_column_met_twice_is_written_once(root: Path) -> None:
    twice = logic_of(*chain().columns.values(),
                     column("mart.t", "both", reads=("mart.team_failures.fails",
                                                     "mart.team_report.fail_rate")))
    record(root, twice, "first")

    text = effective_logic_text(columns_at(read_rows(root)), "mart.t.both")

    assert text.count("ops.job_events.event_type") == 1
    assert "mart.team_failures.fails  (as above)" in text


def test_a_retyped_root_is_inherited_two_tables_down_with_its_chain(root: Path) -> None:
    record(root, chain(), "first")
    record(root, chain(root_type="int", up_effective="up-e2", down_effective="down-e2"),
           "project.add_references(...)")

    found = difference(read_rows(root))

    assert by_table(found) == {"ops.job_events": "own", "mart.team_failures": "inherited",
                               "mart.team_report": "inherited"}
    assert found.tables[0].columns[0].change == "retyped"
    report = next(table for table in found.tables if table.table == "mart.team_report")
    assert report.columns[0].chains == (("mart.team_report.fail_rate",
                                         "mart.team_failures.fails",
                                         "ops.job_events.event_type"),)


def test_a_building_block_is_named_by_the_own_change_it_came_with(root: Path) -> None:
    block = root / "building_blocks" / "owner_on_day.py"
    block.write_text("x = 1\n", encoding="utf-8")
    record(root, logic_of(column("mart.t", "a")), "first")
    block.write_text("x = 2\n", encoding="utf-8")
    record(root, logic_of(column("mart.t", "a", own="own-2")),
           "project.record_lineage_state()")
    # blocks_of says mart.t imports it: record names it only then.
    rows = read_rows(root)
    rows[-2]["because"] = "building_block:owner_on_day"

    found = difference(rows)

    assert found.tables[0].columns[0].blocks == ("owner_on_day",)
    assert found.blocks == (("owner_on_day", "own", "2026-11-20 06:01:00"),)


def test_added_removed_and_opaque_columns(root: Path) -> None:
    record(root, logic_of(column("mart.t", "a"), column("mart.t", "b"),
                          column("mart.u", "c", opaque=True)), "first")
    record(root, logic_of(column("mart.t", "a"), column("mart.t", "new"),
                          column("mart.u", "c", own="opaque-2", opaque=True)), "second")

    found = difference(read_rows(root))

    changes = {}
    for table in found.tables:
        changes.update({(table.table, c.column): c.change for c in table.columns})
    assert changes == {("mart.t", "new"): "added", ("mart.t", "b"): "removed",
                       ("mart.u", "c"): "opaque"}


def test_an_upgrades_rewrite_is_shown_apart_never_as_your_change(root: Path) -> None:
    record(root, chain(), "first")
    record(root, chain(up_own="up-2", up_effective="up-e2", down_effective="down-e2"),
           "project.upgrade()", by_upgrade=True)

    found = difference(read_rows(root))

    assert found.tables == ()
    assert [(rewrite.recorded_by, rewrite.columns) for rewrite in found.toolbox] == [
        ("project.upgrade()", ("mart.team_failures.fails", "mart.team_report.fail_rate"))]
    markdown = to_markdown(found, FOOTER)
    assert "Rewritten by the Toolbox's upgrade to" in markdown
    assert "No column of yours changed" in markdown


# --- since= and tables= -----------------------------------------------------------------------


def three_recordings(root: Path) -> list[dict[str, str]]:
    """The chain recorded three times: first, fails changed, then fail_rate changed."""
    rows = changed_up_the_chain(root)
    record(root, chain(up_own="up-2", up_effective="up-e2", down_effective="down-e3"), "third")
    rows = read_rows(root)
    for row in rows:
        row["commit"] = {"2026-11-20 06:00:00": "aaaa111", "2026-11-20 06:01:00": "bbbb222",
                         "2026-11-20 06:02:00": "cccc333"}[row["recorded_at"]]
    return rows


def test_since_left_out_compares_the_newest_with_the_one_before(root: Path) -> None:
    found = difference(three_recordings(root))

    assert (found.start, found.end) == ("2026-11-20 06:01:00", "2026-11-20 06:02:00")
    assert by_table(found) == {"mart.team_report": "inherited"}


def test_since_a_time_or_a_commit_shows_every_change_after_it(root: Path) -> None:
    rows = three_recordings(root)

    for since in ("2026-11-20 06:00", "2026-11-20 06:00:30", "aaaa111", "AAAA"):
        found = difference(rows, since=since)
        assert found.start == "2026-11-20 06:00:00", since
        assert by_table(found) == {"mart.team_failures": "own",
                                   "mart.team_report": "inherited"}, since
    # A day the first recording was made on starts from that recording, and says so.
    found = difference(rows, since="2026-11-20")
    assert found.start == "2026-11-20 06:00:00"
    assert found.since == "since 2026-11-20, from the first recording, of 2026-11-20 06:00:00"


@pytest.mark.parametrize(("since", "said"), [
    ("bbbb223", "The nearest a recording was made at is bbbb222"),
    ("dddd444", "Recordings were made at aaaa111, bbbb222 and cccc333"),
    ("last tuesday", "is neither a time nor a commit"),
])
def test_since_matching_no_recording_is_refused_naming_the_nearest(
        root: Path, since: str, said: str) -> None:
    with pytest.raises(ValueError, match=said):
        difference(three_recordings(root), since=since, call="project.x()")


def test_tables_keeps_those_named_and_the_chains_that_reach_them(root: Path) -> None:
    rows = changed_up_the_chain(root)
    record(root, logic_of(*chain(up_own="up-2", up_effective="up-e2",
                                 down_effective="down-e2").columns.values(),
                          column("mart.other", "x")), "other added")
    rows = read_rows(root)

    found = difference(rows, since="2026-11-20 06:00:00", tables="mart.team_report")

    assert by_table(found) == {"mart.team_failures": "own", "mart.team_report": "inherited"}
    assert set(found.kinds) == {"mart.team_report", "mart.team_failures"}
    assert found.reads["mart.team_report"] == ("mart.team_failures",)


def test_a_table_the_state_holds_nothing_of_is_refused_naming_the_nearest(root: Path) -> None:
    with pytest.raises(ValueError, match="Did you mean mart.team_report"):
        difference(changed_up_the_chain(root), tables=["mart.team_reprot"])


def test_no_lineage_state_yet_is_refused() -> None:
    with pytest.raises(ValueError, match="no Lineage state yet"):
        difference([])


def test_one_recording_has_nothing_to_compare_yet(root: Path) -> None:
    record(root, chain(), "first")

    found = difference(read_rows(root))

    assert (found.end, found.tables) == (None, ())
    assert "Nothing to compare yet" in to_markdown(found, FOOTER)


# --- When it reached the data -----------------------------------------------------------------


def test_each_changed_saved_table_says_when_it_was_next_written(root: Path) -> None:
    sent = [{"time": "2026-11-20 05:00:00", "kind": "write", "tables": "mart.team_failures",
             "script": "a"},
            {"time": "2026-11-20 06:05:00", "kind": "write",
             "tables": "mart.x;mart.team_failures", "script": "b"},
            {"time": "2026-11-20 06:09:00", "kind": "write", "tables": "mart.team_failures",
             "script": "c"}]

    found = difference(changed_up_the_chain(root), sent=sent)

    written = {table.table: table.first_written for table in found.tables}
    assert written == {"mart.team_failures": "2026-11-20 06:05:00", "mart.team_report": None}
    markdown = to_markdown(found, FOOTER)
    assert "First written with this logic: 2026-11-20 06:05:00 (admin/sent.csv)." in markdown
    assert "Not written since the change (admin/sent.csv)." in markdown


# --- The page and its twin --------------------------------------------------------------------


def test_every_line_of_the_markdown_is_on_the_page_which_comes_from_the_one_module(
        root: Path) -> None:
    rows = changed_up_the_chain(root)
    found = difference(rows, sent=[], not_built={"mart.broken": "its logic cell doesn't load"})

    page, markdown = to_html(found, FOOTER), to_markdown(found, FOOTER)

    shown = text_shown(page)
    assert [line for line in markdown_lines(markdown) if line not in shown] == []
    assert toolbox_module("html_page").tokens_css() in page
    assert " style=" not in page
    assert external_references(page) == []
    assert "`mart.broken`: its logic cell doesn't load" in markdown
    assert "`mart.team_report.fail_rate` ← `mart.team_failures.fails`" in markdown


# --- The drawing: ticket 06 ------------------------------------------------------------------


def drawn_boxes(page: str) -> dict[str, str]:
    """Each box the page draws, by its table, as the kind it is drawn as."""
    return {name: kind for kind, name in re.findall(
        r'<g class="n ([\w-]+)" id="box-[^"]*"[^>]*>.*?<text x="8" y="17" class="l">([^<]*)<',
        page)}


def test_each_table_is_drawn_by_what_changed_of_it_and_opens_its_section(root: Path) -> None:
    rows = changed_up_the_chain(root)
    record(root, logic_of(*chain(up_own="up-2", up_effective="up-e2",
                                 down_effective="down-e2").columns.values(),
                          column("mart.other", "x")), "other added")
    record(root, logic_of(*chain(up_own="up-2", up_effective="up-e2",
                                 down_effective="down-e2").columns.values(),
                          column("mart.other", "x")), "nothing changed")
    rows = read_rows(root)

    page = to_html(difference(rows, since="2026-11-20 06:00:00"), FOOTER)

    assert drawn_boxes(page) == {"mart.team_failures": "own-change",
                                 "mart.team_report": "inherited-change",
                                 "ops.job_events": "unchanged", "mart.other": "own-change"}
    for box in re.findall(r'<g class="n [^"]*"[^>]*>', page):
        assert 'tabindex="0"' in box and 'role="button"' in box, box
        part = re.search(r'data-parts="([^"]*)"', box)[1]
        assert f'<div class="part" id="{part}">' in page, box
    # An arrow from each table to each table that reads it.
    arrows = re.findall(r'<path class="e" data-a="([^"]*)" data-b="([^"]*)"', page)
    assert ("box-table-mart-team_failures", "box-table-mart-team_report") in arrows
    assert ("box-table-ops-job_events", "box-table-mart-team_failures") in arrows
    # The unchanged table's panel says so; the Markdown twin lists only what changed.
    assert "<h2><code>ops.job_events</code>: unchanged</h2>" in page
    assert "ops.job_events`: unchanged" not in to_markdown(difference(rows, since="2026-11-20 "
                                                                      "06:00:00"), FOOTER)
    legend = [kind for kind, _ in toolbox_module("lineage_difference").LEGEND if kind]
    assert legend == ["own-change", "inherited-change", "unchanged"]


def test_the_panel_holds_each_own_changes_logic_with_copy_and_each_chain(root: Path) -> None:
    page = to_html(difference(changed_up_the_chain(root)), FOOTER)

    panel = page.split('<aside id="panel"', 1)[1].split("</aside>", 1)[0]
    fails = panel.split('id="table-mart-team_failures"', 1)[1]
    fails = fails.split('<div class="part" id="table-mart-team_report"', 1)[0]
    button = '<button type="button" class="copy">Copy</button>'
    assert f'<div class="hive">{button}<pre>&lt;up-1&gt;</pre></div>' in fails
    assert f'<div class="hive">{button}<pre>&lt;up-2&gt;</pre></div>' in fails
    assert ("<li><code>mart.team_report.fail_rate</code> ← <code>mart.team_failures.fails"
            "</code></li>") in panel
    assert "Not written since the change (admin/sent.csv)." in panel


def test_given_tables_only_those_and_their_chains_are_drawn(root: Path) -> None:
    changed_up_the_chain(root)
    record(root, logic_of(*chain(up_own="up-2", up_effective="up-e2",
                                 down_effective="down-e2").columns.values(),
                          column("mart.other", "x")), "other added")

    page = to_html(difference(read_rows(root), since="2026-11-20 06:00:00",
                              tables="mart.team_report"), FOOTER)

    assert set(drawn_boxes(page)) == {"mart.team_report", "mart.team_failures"}


def test_nothing_to_compare_still_draws_a_page(root: Path) -> None:
    record(root, chain(), "first")

    page = to_html(difference(read_rows(root)), FOOTER)

    assert set(drawn_boxes(page).values()) == {"unchanged"}
    assert '<aside id="panel"' in page


# --- project.export_lineage_difference, end to end --------------------------------------------


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A copy of the Intermediate Example project, its clock a minute on at each reading."""
    shutil.copytree(ROOT / "example_projects" / "intermediate", tmp_path, dirs_exist_ok=True)
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "warehouse", "building_blocks")]:
        monkeypatch.delitem(sys.modules, name)
    times = iter(FIRST_TIME + datetime.timedelta(minutes=n) for n in range(1000))
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: next(times))
    monkeypatch.chdir(tmp_path / "admin")
    return tmp_path


def test_the_example_projects_building_block_change_is_written_as_a_page(
        intermediate: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project.record_lineage_state()
    block = intermediate / "building_blocks" / "events_per_job.py"
    block.write_text(block.read_text(encoding="utf-8").replace(
        'is_in(job_events.event_type, ["start", "retry"])',
        'is_in(job_events.event_type, ["start"])'),
        encoding="utf-8")
    for name in [name for name in sys.modules if name.split(".")[0] == "building_blocks"]:
        monkeypatch.delitem(sys.modules, name)
    project.record_lineage_state()
    (intermediate / "admin" / "sent.csv").write_text(
        f"{SENT_HEADER}2026-11-21 06:00:00,write,mart.job_day_facts,job_day_facts.ipynb\n",
        encoding="utf-8")

    report = project.export_lineage_difference(since="2026-11-20", tables="mart.team_days")

    assert report.lines[0].startswith("Wrote admin/lineage/")
    assert "-difference.html and its Markdown twin, " in report.lines[0]
    markdown = next((intermediate / "admin" / "lineage").glob("*-difference.md")).read_text(
        encoding="utf-8")
    assert "## `mart.job_day_facts`: own change" in markdown
    assert "## `mart.team_days`: inherited change only" in markdown
    assert "`mart.team_days.runs` ← `mart.job_day_facts.runs`" in markdown
    assert "It came with a change to the Building block `events_per_job`." in markdown
    assert "First written with this logic: 2026-11-21 06:00:00 (admin/sent.csv)." in markdown
    # The Example project holds the recordings its tool made, before 2026-11-20 (ticket 03).
    assert "since 2026-11-20" in markdown
    log = (intermediate / "admin" / "admin_log.md").read_text(encoding="utf-8")
    assert "- Call: `project.export_lineage_difference()`" in log
    assert "- Tables named: mart.team_days" in log
