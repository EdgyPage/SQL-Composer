"""Proposals accepted at once, and proposed for a Table reference. Toolbox 8.5, 07 and 08.

A Key the Toolbox proposed is a line of a Table reference marked # proposed: one a Conversion
worked out of a table's query, made already, or one the references Workflow worked out of a
table's rows and checked with check_key, open until you accept it. DECISIONS["all_tables"]
{"key": "proposed"} accepts each table's at once, written as if typed; a table's own "key"
wins, and a table with no proposal stays open, named in the report. A guessed type is never
accepted so: it stays each table's own.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project

decisions = toolbox_module("decisions")
workflows = toolbox_module("workflows")

DAILY = "mart_dev.daily_close_mart"
WEEKLY = "mart_dev.weekly_close_mart"
BATCH = [DAILY, WEEKLY]
PROPOSED_LINE = ('    key=["job_id", "dt"],  # proposed from its query; if it is wrong, answer '
                 '"key" in the decisions cell')


def _script(name: str) -> str:
    return (f"INSERT OVERWRITE TABLE mart.{name}_close PARTITION (dt)\n"
            "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
            "WHERE r.dt = '2026-09-24'\n"
            "GROUP BY r.job_id, r.dt;\n")


@pytest.fixture
def converted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project whose batch "closing" made two tables, each with its location open and its
    Key proposed from its query."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    for name in ("daily", "weekly"):
        (tmp_path / f"{name}.hql").write_text(_script(name), encoding="utf-8")
    project.convert("closing", files=["daily.hql", "weekly.hql"],
                    query=example_database.query, database="ops")
    yield tmp_path
    forget_the_projects_modules()


def _reference(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    return (root / "references" / f"{stem}.py").read_text(encoding="utf-8")


# --- 07: a batch's proposed Keys accepted at once ---------------------------------------------


def test_all_tables_accepts_each_proposed_key_as_if_typed(converted: Path) -> None:
    for table in BATCH:
        assert PROPOSED_LINE in _reference(converted, table)
    said = repr(project.write_decisions({"all_tables": {"key": "proposed"}}, tables=BATCH))
    for table in BATCH:
        assert '    key=["job_id", "dt"],\n' in _reference(converted, table)
    assert (f'all_tables: key "proposed": accepted the proposed Key of {DAILY} and {WEEKLY}, '
            "each written as if typed." in said)


def test_a_tables_own_key_wins_and_one_with_no_proposal_stays_open(converted: Path) -> None:
    daily = converted / "references" / "mart_dev__daily_close_mart.py"
    daily.write_text(daily.read_text(encoding="utf-8").replace(
        PROPOSED_LINE, '    key=None,  # TODO: the columns that pick out one row'),
        encoding="utf-8")
    said = repr(project.write_decisions({"all_tables": {"key": "proposed"},
                                         WEEKLY: {"key": ["job_id"]}}, tables=BATCH))
    assert '    key=["job_id"],\n' in _reference(converted, WEEKLY)
    assert "    key=None,  # TODO" in _reference(converted, DAILY)
    assert (f'all_tables: key "proposed": accepted the proposed Key of no table. {WEEKLY} '
            f"keeps its own Key. {DAILY} has no proposed Key, so its Key stays open: answer "
            '"key" under its name.' in said)
    assert f"Still open in {DAILY}: key:" in said


def test_a_tables_own_key_of_proposed_accepts_its_proposal(converted: Path) -> None:
    project.write_decisions({DAILY: {"key": "proposed"}})
    assert '    key=["job_id", "dt"],\n' in _reference(converted, DAILY)
    assert PROPOSED_LINE in _reference(converted, WEEKLY)


def test_check_offers_accepting_every_proposed_key_at_once(converted: Path) -> None:
    said = repr(project.check())
    assert ('        "key": "proposed",  # accepts each table\'s proposed Key, marked # '
            "proposed in its Table reference" in said)


def test_check_names_each_proposed_line_left_until_it_is_accepted(converted: Path) -> None:
    said = repr(project.check())
    assert ("Proposed by the Toolbox, which blocks nothing: each line marked # proposed is "
            "used as it is." in said)
    assert (f"  references/mart_dev__daily_close_mart.py, line 12: {PROPOSED_LINE.strip()}"
            in said)
    project.write_decisions({"all_tables": {"key": "proposed"}}, tables=BATCH)
    assert "Proposed by the Toolbox" not in repr(project.check())


def test_one_proposed_key_is_not_offered_for_every_table() -> None:
    lines = decisions.paste_lines([decisions.Decision(DAILY, decisions.LOCATION)],
                                  proposed=[DAILY])
    assert not any('"key"' in line for line in lines)


# --- 08: the references Workflow proposes and checks ------------------------------------------


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    forget_the_projects_modules()


def _source(root: Path, table: str) -> str:
    return (root / "references" / f"{table.replace('.', '__')}.py").read_text(encoding="utf-8")


def test_add_references_proposes_each_key_from_the_rows_and_checks_it(started: Path) -> None:
    said = repr(project.add_references(["ops.job_runs", "ops.job_owners"],
                                       query=example_database.query))
    runs = _source(started, "ops.job_runs")
    assert ('    key=None,  # TODO: proposed ["run_id"], checked: accept it in the decisions '
            "cell\n" in runs)
    # job_id names one row of a day of ops.job_owners, but not of two days: its Key adds dt.
    assert '# TODO: proposed ["job_id", "dt"]' in _source(started, "ops.job_owners")
    assert ("ops.job_runs: the key (run_id) holds where job_runs.dt IN ('2026-09-23', "
            "'2026-09-24')." in said)
    assert ("ops.job_owners: the key (job_id) repeats where job_owners.dt IN ('2026-09-23', "
            "'2026-09-24')." in said)
    assert ("ops.job_owners: the key (job_id, dt) holds where job_owners.dt IN "
            "('2026-09-23', '2026-09-24')." in said)
    assert ('To accept every proposed Key, write in the decisions cell: "all_tables": {"key": '
            '"proposed"}' in said)


def test_one_table_proposed_is_accepted_by_its_own_line(started: Path) -> None:
    said = repr(project.add_references("ops.jobs", query=example_database.query))
    assert "ops.jobs: the key (job_id) holds." in said
    assert ('To accept it, write in the decisions cell: "ops.jobs": {"key": ["job_id"]}'
            in said)


def test_a_table_with_no_id_column_keeps_its_key_and_first_line_todo(started: Path) -> None:
    said = repr(project.add_references("ops.team_notes", query=example_database.query))
    notes = _source(started, "ops.team_notes")
    assert '"""ops.team_notes - TODO: say in one line what one row is."""' in notes
    assert "    key=None,  # TODO: the columns that pick out one row" in notes
    assert ("ops.team_notes: no Key proposed: no column is named like an id, such as run_id: "
            "answer its Key in the decisions cell." in said)


def test_what_one_row_is_and_what_doesnt_add_up_are_proposed(started: Path) -> None:
    project.add_references(["ops.job_runs", "ops.job_owners", "ops.team_notes"],
                           query=example_database.query)
    runs = _source(started, "ops.job_runs")
    assert runs.startswith('"""ops.job_runs - One row per run_id."""  # proposed from its '
                           "Key\n")
    assert ('    does_not_add_up=["avg_retry_secs"],  # proposed from its columns\' names\n'
            in runs)
    assert _source(started, "ops.job_owners").startswith(
        '"""ops.job_owners - One row per job_id and dt."""  # proposed')
    assert ("    does_not_add_up=[],  # proposed: no name says average, ratio, percent or "
            "rate\n" in _source(started, "ops.team_notes"))


@pytest.mark.parametrize(("columns", "proposed"), [
    ({"avg_mins": "double", "fail_ratio": "double", "done_pct": "int", "error_rate": "float",
      "runs_per_day": "double", "jobs_per_team": "bigint", "team": "string"},
     ["avg_mins", "fail_ratio", "done_pct", "error_rate", "runs_per_day"]),
    ({"runs": "bigint", "average": "double"}, []),
], ids=["each kind", "none"])
def test_does_not_add_up_is_proposed_from_names_and_types(columns: dict[str, str],
                                                          proposed: list[str]) -> None:
    assert decisions.proposed_does_not_add_up(columns) == proposed


def test_another_key_answered_proposes_what_one_row_is_again(started: Path) -> None:
    project.add_references("ops.job_runs", query=example_database.query)
    project.write_decisions({"ops.job_runs": {"key": ["run_id", "dt"]}})
    assert _source(started, "ops.job_runs").startswith(
        '"""ops.job_runs - One row per run_id and dt."""  # proposed from its Key\n')


def test_accepting_a_proposed_key_from_the_rows_leaves_no_todo_line(started: Path) -> None:
    project.add_references("ops.job_runs", query=example_database.query)
    said = repr(project.write_decisions({"ops.job_runs": {"key": "proposed"}}))
    assert '    key=["run_id"],\n' in _source(started, "ops.job_runs")
    assert "TODO" not in _source(started, "ops.job_runs")
    assert "Each Decision of ops.job_runs is made." in said

