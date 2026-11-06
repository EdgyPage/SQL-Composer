"""Decisions for every table: DECISIONS["all_tables"] answers for every table a Workflow's
notebook names, and a table's own answer overwrites it. Toolbox 8.4, ticket 08.

It takes "seed", for the seed's limits, and "tags"; a Key, a type and a location are each
table's own. 8.4's "location_root" is a Database setting since 8.5 (ticket 09), in
admin/databases.py, and refused here. project.write_decisions is given the notebook's tables
with tables=, as each Workflow's step cell does, and says which tables each answer of
all_tables was written into.
"""

from __future__ import annotations

import ast
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
RUN_VALUES = '''import datetime


def period_end() -> datetime.date:
    """The Example database's last day."""
    return datetime.date(2026, 9, 24)
'''


def _script(name: str) -> str:
    return (f"INSERT OVERWRITE TABLE mart.{name}_close PARTITION (dt)\n"
            "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
            'WHERE r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 1) AND <PARM="PERIOD_END"/>\n'
            "GROUP BY r.job_id, r.dt;\n")


@pytest.fixture
def converted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A Project whose batch "closing" made two tables, each placed under DEV's location_root,
    with a PERIOD_END tag."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"')
                         .replace('"<DEV_LOCATION_ROOT>"', '"/data/team"'), encoding="utf-8")
    (tmp_path / "building_blocks" / "run_values.py").write_text(RUN_VALUES, encoding="utf-8")
    for name in ("daily", "weekly"):
        (tmp_path / f"{name}.hql").write_text(_script(name), encoding="utf-8")
    project.convert("closing", files=["daily.hql", "weekly.hql"],
                    query=example_database.query, database="ops")
    yield tmp_path
    forget_the_projects_modules()
    sys.modules.pop("building_blocks.run_values", None)


def _reference(root: Path, table: str) -> str:
    stem = table.replace(".", "__")
    return (root / "references" / f"{stem}.py").read_text(encoding="utf-8")


# --- One answer for every table ---------------------------------------------------------------


def test_all_tables_answers_every_table_the_notebook_names(converted: Path) -> None:
    every = {"tags": {"PERIOD_END": "'2026-09-24'"}}
    said = repr(project.write_decisions({"all_tables": every},
                                        tables=project.batch_tables("closing")))
    for table in BATCH:
        reference = _reference(converted, table)
        assert f'    location="/data/team/mart_dev.db/{table.split(".")[1]}",' in reference
        assert '    "PERIOD_END": "\'2026-09-24\'",  # bare' in reference
        assert f"Each Decision of {table} is made." in said
    assert f"all_tables: tags: PERIOD_END: written into {DAILY} and {WEEKLY}." in said


def test_a_tables_own_answer_overwrites_all_tables_kind_by_kind(converted: Path) -> None:
    said = repr(project.write_decisions({
        "all_tables": {"tags": {"PERIOD_END": "'2026-09-24'"}},
        WEEKLY: {"tags": {"PERIOD_END": "'2026-09-20'"}},
    }, tables=BATCH))
    assert '"PERIOD_END": "\'2026-09-20\'",' in _reference(converted, WEEKLY)
    assert '"PERIOD_END": "\'2026-09-24\'",' in _reference(converted, DAILY)
    assert (f"all_tables: tags: PERIOD_END: written into {DAILY}. {WEEKLY} keeps its own "
            "answer." in said)


def test_a_tag_answered_with_a_run_value_is_written_into_every_table(converted: Path) -> None:
    from building_blocks.run_values import period_end
    project.write_decisions({"all_tables": {"tags": {"PERIOD_END": period_end}}},
                            tables=BATCH)
    for table in BATCH:
        reference = _reference(converted, table)
        assert "from building_blocks.run_values import period_end  # a Run value" in reference
        assert '    "PERIOD_END": period_end,  #' in reference


def test_a_tag_no_table_of_the_tables_holds_is_passed_over_for_that_table() -> None:
    held = ('TAGS = {\n    "END": "<PARM=\\"END\\"/>",  # bare. Answer it ...\n}\n'
            "    location=None,\n")
    answer = decisions.table_answer({"all_tables": {"tags": {"END": "1", "OTHER": "2"}}},
                                    "mart_dev.x", held)
    assert answer == {"tags": {"END": "1"}}


def test_the_location_under_a_root_is_its_database_folder_then_its_table() -> None:
    assert (decisions.location_under("/data/team", "mart_dev.weekly_ops")
            == "/data/team/mart_dev.db/weekly_ops")


def test_a_seed_under_all_tables_is_passed_through_for_each_table() -> None:
    seed = {"dt": {"from": "2026-01-01"}}
    answer = decisions.table_answer({"all_tables": {"seed": seed}}, "mart_dev.x", "")
    assert answer == {"seed": seed}


# --- What all_tables refuses ------------------------------------------------------------------


@pytest.mark.parametrize(("every", "said"), [
    ({"tags": {"PERIOD_ED": "1"}},
     "all_tables: tags: PERIOD_ED is no Script tag of any table it answers for; did you mean "
     "PERIOD_END?"),
    ({"key": ["job_id"]},
     f"all_tables: key is each table's own: answer it under the name of each table it is "
     f"for, {DAILY} and {WEEKLY}"),
    ({"types": {"runs": "bigint"}},
     f"all_tables: types is each table's own: answer it under the name of each table it is "
     f"for, {DAILY} and {WEEKLY}"),
    ({"location": "/data/team"},
     "all_tables: 'location' is no kind of answer for every table; all_tables answers seed "
     "and tags"),
    # Toolbox 8.5, ticket 09: the root is a Database setting.
    ({"location_root": "/data/team"},
     'all_tables: location_root is a Database setting now: give it as "location_root" in DEV '
     "and PROD, in admin/databases.py"),
    ({"tags": "'2026-09-24'"},
     "all_tables: tags: give a dict of each answer by its name"),
], ids=["tag held by no table", "key", "types", "location", "root", "tags not a dict"])
def test_an_answer_all_tables_cant_give_is_refused_writing_nothing(
        converted: Path, every: dict, said: str) -> None:
    before = _reference(converted, DAILY)
    with pytest.raises(ValueError, match="wrote nothing") as refused:
        project.write_decisions({"all_tables": every}, tables=BATCH)
    assert said in str(refused.value)
    assert _reference(converted, DAILY) == before


def test_all_tables_with_no_tables_given_is_refused(converted: Path) -> None:
    with pytest.raises(ValueError, match="all_tables answers for every table the notebook "
                       "names, but tables= names none") as refused:
        project.write_decisions({"all_tables": {"tags": {"PERIOD_END": "'2026-09-24'"}}})
    assert "tables=project.batch_tables(NAME)" in str(refused.value)


def test_a_table_given_with_no_table_reference_is_refused(converted: Path) -> None:
    with pytest.raises(ValueError, match="tables: mart_dev.nothing: no table of the Project "
                       "has that name"):
        project.write_decisions({"all_tables": {"tags": {"PERIOD_END": "'2026-09-24'"}}},
                                tables=[*BATCH, "mart_dev.nothing"])


# --- Offered in what check() prints to paste --------------------------------------------------


def test_a_tag_more_than_one_table_holds_is_offered_under_all_tables() -> None:
    # A location is each table's own since 8.5, its root a Database setting.
    still_open = [
        decisions.Decision("mart_dev.a", decisions.LOCATION),
        decisions.Decision("mart_dev.a", decisions.TAG, "PERIOD_END", "a.hql, line 3"),
        decisions.Decision("mart_dev.a", decisions.TAG, "TEAM", quoted=True),
        decisions.Decision("mart_dev.b", decisions.LOCATION),
        decisions.Decision("mart_dev.b", decisions.KEY),
        decisions.Decision("mart_dev.b", decisions.TAG, "PERIOD_END", "b.hql, line 3"),
    ]
    lines = decisions.paste_lines(still_open)
    assert lines == [
        "DECISIONS = {",
        '    "all_tables": {  # answers for every table of this notebook; a table\'s own '
        "answer, under its name, overrides it",
        '        "tags": {',
        '            "PERIOD_END": "<FILL IN>",  # bare: the value with its own quotes, '
        'such as "\'2026-10-31\'", or a number, such as "5"',
        "        },",
        "    },",
        '    "mart_dev.a": {',
        '        "location": "<FILL IN>",  # its folder, such as '
        '"/data/your_team/mart_dev.db/a"',
        '        "tags": {',
        '            "TEAM": "<FILL IN>",  # inside quotes: the value with no quotes, such as '
        '"failed"',
        "        },",
        "    },",
        '    "mart_dev.b": {',
        '        "location": "<FILL IN>",  # its folder, such as '
        '"/data/your_team/mart_dev.db/b"',
        '        "key": "<FILL IN>",  # a list, such as ["job_id", "dt"], or None when no '
        "columns name one row",
        "    },",
        "}"]
    pasted = ast.literal_eval("\n".join(lines).removeprefix("DECISIONS = "))
    assert pasted["all_tables"] == {"tags": {"PERIOD_END": "<FILL IN>"}}


def test_a_tag_bare_in_one_table_and_quoted_in_another_stays_with_each() -> None:
    lines = decisions.paste_lines([
        decisions.Decision("mart_dev.a", decisions.TAG, "END"),
        decisions.Decision("mart_dev.b", decisions.TAG, "END", quoted=True)])
    assert not any("all_tables" in line for line in lines)


def test_check_offers_all_tables_for_the_batch(converted: Path) -> None:
    said = repr(project.check())
    assert '    "all_tables": {' in said
    assert f'    "{DAILY}": {{' not in said


# --- In the Workflow --------------------------------------------------------------------------


def test_the_decision_step_is_done_once_all_tables_answers_each(converted: Path) -> None:
    inputs = {"NAME": "closing", "TABLES": BATCH, "DECISIONS": {"all_tables": {}}}
    assert not workflows.every_dev_decision_answered(converted, inputs)
    inputs["DECISIONS"]["all_tables"]["tags"] = {"PERIOD_END": "'2026-09-24'"}
    assert workflows.every_dev_decision_answered(converted, inputs)


def test_each_write_step_gives_write_decisions_the_notebooks_tables() -> None:
    calls = {workflow.name: step.call for workflow in workflows.WORKFLOWS
             for step in workflow.steps if step.call.startswith("project.write_decisions(")}
    assert calls == {
        "convert": "project.write_decisions(DECISIONS, tables=project.batch_tables(NAME))",
        "promote": "project.write_decisions(DECISIONS, tables=project.promoted_tables(TABLES))",
        "new_table": "project.write_decisions(DECISIONS, tables=TABLES)",
        "references": "project.write_decisions(DECISIONS, tables=TABLES)",
    }


def test_do_next_writes_all_tables_into_every_table_of_the_batch(converted: Path) -> None:
    (step,) = [each for each in workflows.CONVERT.steps if each.run is not None
               and each.call.startswith("project.write_decisions(")]
    step.run({"NAME": "closing", "TABLES": BATCH, "DECISIONS": {"all_tables": {
        "tags": {"PERIOD_END": "'2026-09-24'"}}}})
    assert workflows.every_dev_decision_made(converted, {"NAME": "closing", "TABLES": BATCH})


def test_the_decisions_cell_says_all_tables() -> None:
    assert '"all_tables"' in workflows.DECISIONS_CELL
