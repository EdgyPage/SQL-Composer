"""Decisions: what only you decide about one table, which its Table reference shows made or not.

Toolbox 8.1's tickets 02 and 03. A Decision is a line of a Table reference holding a TODO: or
a <...>: its location=, its key=, a column whose type a Conversion could only guess, or any
other <...>. You answer each in a Workflow's decisions cell, and project.write_decisions
writes each answer into its line; a line made already is kept.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import example_database, project, set_admin_log

decisions = toolbox_module("decisions")
REFERENCE = '''"""mart_dev.x - TODO: say in one line what one row is."""
from sqlglot_composer import Table

x = Table(
    "mart_dev.x",
    columns={
        "team": "string",  # TODO: guessed: nothing told its type
        "fails": "bigint",
    },
    key=None,  # TODO: the columns that pick out one row, such as key=["team"]
    location=None,  # TODO: its own folder, such as "/data/your_team/mart_dev.db/this_table"
    does_not_add_up=[],  # TODO: columns that are averages, ratios or distinct counts
)

# --- Aliases ------------------------------------------------------------------------------
#     <alias> = x.team
'''


def kinds(text: str) -> list[tuple[str, str]]:
    return [(each.kind, each.subject) for each in decisions.open_decisions(text, "mart_dev.x")]


def test_each_open_line_is_a_decision_of_its_kind() -> None:
    assert kinds(REFERENCE) == [(decisions.GUESSED_TYPE, "team"), (decisions.KEY, ""),
                                (decisions.LOCATION, "")]


def test_a_todo_that_is_no_decision_and_a_comment_wait_on_nothing() -> None:
    # does_not_add_up's TODO, the docstring's, and the Aliases' <alias> are none.
    assert all(kind != decisions.PLACEHOLDER for kind, _ in kinds(REFERENCE))


def test_a_docstring_todo_is_counted_once_as_waiting_on_nothing() -> None:
    text = ('"""mart_dev.z - TODO: say in one line what one row is."""\n'
            'z = Table(\n    "mart_dev.z",\n    key=["team"],\n)\n')
    assert decisions.todo_lines(text) == [
        (1, 'mart_dev.z - TODO: say in one line what one row is.')]


def test_each_todo_line_is_given_by_its_line_in_the_file() -> None:
    # Ticket 21: so write_decisions can name each, a docstring of many lines too.
    text = ('"""mart_dev.z - TODO: say in one line what one row is.\n\nMore.\n"""\n'
            'z = Table(\n    "mart_dev.z",\n    key=None,  # TODO: the columns\n'
            "    does_not_add_up=[],  # TODO: averages\n)\n")
    assert decisions.todo_lines(text) == [
        (1, 'mart_dev.z - TODO: say in one line what one row is.'),
        (8, "does_not_add_up=[],  # TODO: averages")]


def test_a_placeholder_names_itself_and_its_docstring_is_not_read() -> None:
    text = ('"""mart_dev.y - <COLUMN> and <COLUMN_TYPE>: a column."""\n'
            "y = Table(\n    columns={\n        <COLUMN>: <COLUMN_TYPE>,\n    },\n"
            "    location=<LOCATION>,\n)\n")
    assert kinds(text) == [(decisions.PLACEHOLDER, "<COLUMN>"), (decisions.LOCATION, "")]


def test_an_answer_is_written_into_each_open_line() -> None:
    answered = decisions.answered_text(REFERENCE, {
        "location": "/data/team/mart_dev.db/x", "key": ["team"], "types": {"team": "string"}},
        "references/mart_dev__x.py")
    assert answered.unwritten == []
    assert answered.written == ["types: team", "key", "location"]
    assert '    location="/data/team/mart_dev.db/x",' in answered.text
    assert '    key=["team"],' in answered.text
    assert '        "team": "string",\n' in answered.text
    assert kinds(answered.text) == []


def test_none_answers_a_key_that_none_names() -> None:
    answered = decisions.answered_text(REFERENCE, {"key": None}, "references/mart_dev__x.py")
    assert "    key=None,\n" in answered.text
    assert (decisions.KEY, "") not in kinds(answered.text)


def test_a_location_left_none_is_open_with_its_todo_taken_off() -> None:
    text = REFERENCE.replace(
        '    location=None,  # TODO: its own folder, such as "/data/your_team/mart_dev.db/'
        'this_table"', "    location=None,")
    assert (decisions.LOCATION, "") in kinds(text)


def test_a_line_made_already_is_kept_and_a_different_answer_named() -> None:
    todo = '    key=None,  # TODO: the columns that pick out one row, such as key=["team"]'
    made = REFERENCE.replace(todo, '    key=["fails"],')
    answered = decisions.answered_text(made, {"key": ["team"]}, "references/mart_dev__x.py")
    assert '    key=["fails"],' in answered.text
    assert answered.unwritten == [
        "key: kept as references/mart_dev__x.py holds it, made already; to change it, edit "
        'its key= line there (the decisions cell says ["team"])']


def test_a_type_for_a_column_not_guessed_is_named() -> None:
    answered = decisions.answered_text(REFERENCE, {"types": {"fails": "int"}},
                                       "references/mart_dev__x.py")
    assert answered.unwritten == [
        "types: fails's type wasn't a guess: references/mart_dev__x.py gives it already; to "
        "change it, edit its line there"]


# --- write_decisions, in a Project -----------------------------------------------------------


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.add_references("ops.job_runs", query=example_database.query)
    yield tmp_path
    forget_the_projects_modules()


def test_write_decisions_writes_each_answer_and_says_what_is_left(started: Path) -> None:
    report = repr(project.write_decisions({"ops.job_runs": {"key": ["run_id"]}}))
    # Ticket 21: each TODO line left is named, by its line, so no one has to look for it.
    assert report == ('Wrote 1 answer into references/ops__job_runs.py.\n'
                      'ops.job_runs: 2 TODO lines left in references/ops__job_runs.py, which '
                      'wait on nothing: fill each in when you like.\n'
                      '  line 1: ops.job_runs - TODO: say in one line what one row is.\n'
                      '  line 16: does_not_add_up=[],  # TODO: columns that are averages, '
                      'ratios or distinct counts\n'
                      'Each Decision of ops.job_runs is made.')
    reference = (started / "references" / "ops__job_runs.py").read_text(encoding="utf-8")
    assert '    key=["run_id"],' in reference


# --- An answer that matches nothing (Toolbox 8.3, ticket 04) ---------------------------------


@pytest.mark.parametrize("answers, said", [
    ({"ops.job_run": {"key": None}},
     "ops.job_run: no table of the Project has that name; did you mean ops.job_runs?"),
    # Hive sets a name's case aside, and so does the name it may have meant.
    ({"OPS.JOB_RUN": {"key": None}}, "; did you mean ops.job_runs?"),
    ({"ops.job_runs": {"keys": ["run_id"]}},
     "ops.job_runs: 'keys' is no kind of answer; the decisions cell answers location, key, "
     "types and tags; did you mean key?"),
    ({"ops.job_runs": {"tag": {"X": "1"}}}, "; did you mean tags?"),
    ({"ops.job_runs": {"types": {"run_idd": "bigint"}}},
     "ops.job_runs: types: run_idd is no column of ops.job_runs; did you mean run_id?"),
    ({"ops.job_runs": {"types": {"amount": "bigint"}}},
     "ops.job_runs: types: amount is no column of ops.job_runs; its columns are run_id, "),
    ({"ops.job_runs": {"types": "bigint"}},
     "ops.job_runs: types: give a dict of each answer by its name, such as "
     "{\"fails\": \"bigint\"}, not 'bigint'"),
    ({"ops.job_runs": {"tags": {"PERIOD_ED": "1"}}},
     "ops.job_runs: tags: PERIOD_ED, but ops.job_runs holds no Script tag"),
], ids=["table", "table in upper case", "kind", "tag for tags", "column", "column far off",
        "types not a dict", "tag of a table with none"])
def test_an_answer_that_matches_nothing_is_refused_writing_nothing(
        started: Path, answers: dict, said: str) -> None:
    reference = started / "references" / "ops__job_runs.py"
    before = reference.read_text(encoding="utf-8")
    # A right answer beside the wrong one, which isn't written either.
    with_key = {**answers,
                "ops.job_runs": {"key": ["run_id"], **answers.get("ops.job_runs", {})}}
    with pytest.raises(ValueError, match="wrote nothing: 1 mistake in the decisions cell, "
                       "each an answer that matches no Decision") as refused:
        project.write_decisions(with_key)
    assert said in str(refused.value)
    assert reference.read_text(encoding="utf-8") == before


def test_each_answer_that_matches_nothing_is_named_at_once(started: Path) -> None:
    with pytest.raises(ValueError, match="2 mistakes in the decisions cell"):
        project.write_decisions({"ops.nothing": {}, "ops.job_runs": {"owner": "me"}})


def test_a_tag_answered_already_is_a_match_for_its_new_answer(started: Path) -> None:
    reference = started / "references" / "ops__job_runs.py"
    reference.write_text(reference.read_text(encoding="utf-8").replace(
        "# --- Aliases", 'TAGS = {\n    "END": "\'2026-10-31\'",  # bare. Answer it ...\n}\n\n'
        "# --- Aliases"), encoding="utf-8")
    said = repr(project.write_decisions({"ops.job_runs": {"tags": {"END": "'2026-09-30'"}}}))
    assert "tags: END is '2026-09-30' now, in place of '2026-10-31'" in said


def test_a_decisions_cell_not_by_table_is_refused(started: Path) -> None:
    with pytest.raises(TypeError, match="which isn't an answer per table"):
        project.write_decisions({"ops.job_runs": ["run_id"]})


# --- Script tags (Toolbox 8.3, ticket 03) ----------------------------------------------------

TAGGED = REFERENCE.replace("# --- Aliases", '''# What each Script tag stands for, as Hive.
TAGS = {
    "PERIOD_END": "<PARM=\\"PERIOD_END\\"/>",  # bare, at daily.hql, line 4. Answer it ...
    "team_2": "<PARM=\\"team_2\\"/>",  # inside quotes. Answer it with no quotes.
}

# --- Aliases''')


def test_a_tag_holding_itself_is_an_open_decision_naming_where_it_stands() -> None:
    tags = [each for each in decisions.open_decisions(TAGGED, "mart_dev.x")
            if each.kind == decisions.TAG]
    assert [(each.subject, each.where, each.quoted) for each in tags] == [
        ("PERIOD_END", "daily.hql, line 4", False), ("team_2", "", True)]
    assert tags[0].question() == (
        "tags: PERIOD_END, bare at daily.hql, line 4: the value with its own quotes, such as "
        "\"'2026-10-31'\", or a number, such as \"5\"")
    assert tags[1].question() == ("tags: team_2, inside quotes: the value with no quotes, "
                                  'such as "failed"')


def test_a_tag_answered_is_written_into_its_line_its_comment_kept() -> None:
    answered = decisions.answered_text(TAGGED, {"tags": {"PERIOD_END": "'2026-10-31'"}},
                                       "references/mart_dev__x.py")
    assert ('    "PERIOD_END": "\'2026-10-31\'",  # bare, at daily.hql, line 4. Answer it'
            in answered.text)
    assert answered.written == ["tags: PERIOD_END"]
    assert answered.changed == []
    assert ("tag", "PERIOD_END") not in kinds(answered.text)
    assert ("tag", "team_2") in kinds(answered.text)


def test_a_tag_answered_again_is_written_over_the_old_value_and_said() -> None:
    first = decisions.answered_text(TAGGED, {"tags": {"PERIOD_END": "'2026-10-31'"}}, "r.py")
    again = decisions.answered_text(first.text, {"tags": {"PERIOD_END": "'2026-09-30'"}},
                                    "r.py")
    assert "'2026-09-30'" in again.text
    assert "'2026-10-31'" not in again.text
    assert again.written == ["tags: PERIOD_END"]
    assert again.changed == ["tags: PERIOD_END is '2026-09-30' now, in place of '2026-10-31'"]


@pytest.mark.parametrize("tags, said", [
    ({"PERIOD_END": 5}, "tags: PERIOD_END is given 5, a Python int: give the Hive as Python "
     "text"),
    ({"PERIOD_END": " "}, "tags: PERIOD_END is given empty text"),
    ({"PERIOD_END": "2026-10-31"}, "tags: PERIOD_END stands bare, so a date needs its own "
     "quotes, or Hive reads it as a subtraction: answer \"'2026-10-31'\""),
    ({"team_2": "'nobody'"}, "tags: team_2 stands inside quotes already, so its answer has "
     'none: answer "nobody"'),
], ids=["number", "blank", "bare date", "quoted twice"])
def test_a_tag_answer_in_a_form_that_cant_stand_there_is_named(tags: dict, said: str) -> None:
    answered = decisions.answered_text(TAGGED, {"tags": tags}, "r.py")
    assert answered.written == []
    (unwritten,) = answered.unwritten
    assert unwritten.startswith(said)
    assert [kind for kind, _ in kinds(answered.text)].count("tag") == 2


def test_tags_that_arent_a_dict_are_named() -> None:
    answered = decisions.answered_text(TAGGED, {"tags": "'2026-10-31'"}, "r.py")
    assert answered.unwritten == ["tags: give a dict of each tag's answer by its NAME, such as "
                                  "{\"PERIOD_END\": \"'2026-10-31'\"}, not \"'2026-10-31'\""]


def test_a_tag_is_answered_by_its_name_under_tags() -> None:
    (tag,) = [each for each in decisions.open_decisions(TAGGED, "mart_dev.x")
              if each.subject == "team_2"]
    assert decisions.is_answered(tag, {"tags": {"team_2": "nobody"}})
    assert not decisions.is_answered(tag, {"tags": {"PERIOD_END": "x"}})
    assert not decisions.is_answered(tag, {"types": {"team_2": "x"}})


# --- DECISIONS printed to paste (Toolbox 8.3, ticket 05) -------------------------------------


def test_the_open_decisions_print_as_decisions_to_paste() -> None:
    lines = decisions.paste_lines(decisions.open_decisions(TAGGED, "mart_dev.x"))
    assert lines == [
        "DECISIONS = {",
        '    "mart_dev.x": {',
        '        "location": "<FILL IN>",  # its folder, such as '
        '"/data/your_team/mart_dev.db/x"',
        '        "key": "<FILL IN>",  # a list, such as ["job_id", "dt"], or None when no '
        "columns name one row",
        '        "types": {',
        '            "team": "string",  # guessed: its type, if not string, such as "bigint"',
        "        },",
        '        "tags": {',
        '            "PERIOD_END": "<FILL IN>",  # bare at daily.hql, line 4: the value with '
        'its own quotes, such as "\'2026-10-31\'", or a number, such as "5"',
        '            "team_2": "<FILL IN>",  # inside quotes: the value with no quotes, such '
        'as "failed"',
        "        },",
        "    },",
        "}"]
    pasted = ast.literal_eval("\n".join(lines).removeprefix("DECISIONS = "))
    assert pasted["mart_dev.x"]["tags"] == {"PERIOD_END": "<FILL IN>", "team_2": "<FILL IN>"}


THEN = "in the decisions cell in its place, then run project.write_decisions(DECISIONS) again"


def test_a_fill_in_pasted_and_left_is_no_answer() -> None:
    answer = {"location": "<FILL IN>", "key": "<FILL IN>", "types": {"team": "<FILL IN>"},
              "tags": {"PERIOD_END": "<FILL IN>"}}
    for decision in decisions.open_decisions(TAGGED, "mart_dev.x"):
        assert not decisions.is_answered(decision, answer)
    answered = decisions.answered_text(TAGGED, answer, "r.py")
    assert answered.written == []
    assert answered.text == TAGGED
    assert answered.unwritten == [
        f"location is still <FILL IN>: write its answer {THEN}",
        f"key is still <FILL IN>: write its answer {THEN}",
        f"types: team is still <FILL IN>: write its type {THEN}",
        f"tags: PERIOD_END is still <FILL IN>: write its answer {THEN}"]


def test_what_is_left_of_a_fill_in_is_no_answer_either() -> None:
    answer = {"tags": {"PERIOD_END": "FILL IN", "team_2": "<fill in>"}}
    answered = decisions.answered_text(TAGGED, answer, "r.py")
    assert answered.written == []
    assert answered.text == TAGGED


def test_a_tag_of_a_table_with_tags_names_them_when_none_is_close(started: Path) -> None:
    reference = started / "references" / "ops__job_runs.py"
    reference.write_text(reference.read_text(encoding="utf-8").replace(
        "# --- Aliases", 'TAGS = {\n    "END": "\'2026-10-31\'",  # bare. Answer it ...\n}\n\n'
        "# --- Aliases"), encoding="utf-8")
    with pytest.raises(ValueError, match="tags: RUN_DAY is no Script tag of ops.job_runs; its "
                       "Script tags are END"):
        project.write_decisions({"ops.job_runs": {"tags": {"RUN_DAY": "'2026-10-31'"}}})
