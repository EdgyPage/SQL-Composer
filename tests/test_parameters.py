"""A Scheduled run's parameters cell, read strongly: Toolbox 8.6, ticket 03.

"make sure passing in parameters is strong here in case I need to define days of interest or
whatever" (the map's Q13). A scheduler passes text, so the build reads each value of the
notebook's # parameters cell by its type hint before anything is built: "2026-11-01" given for
a datetime.date is that date, and a value that can't be read is refused, naming the parameter,
its hint and the value. The values read are given back to the notebook's names, and printed,
first, so the scheduler's log holds what the run used.

Each test writes the notebook's cells, as write_notebook writes them, and the names the
notebook holds once its cells have run, as a scheduler leaves them: the cell's defaults, and
the text a cell papermill injects after the tagged one assigns.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
from conftest import toolbox_module

from sqlglot_composer import notebooks

scheduled_runs = toolbox_module("scheduled_runs")
with_article = toolbox_module("shared").with_article
CALL = "project.build_run(statements)"
SHOWN = "scheduled_runs/weekly/weekly.ipynb"
PARAMETERS = "# parameters\nimport datetime\n\n"
# The cell papermill puts after the one tagged parameters: each value passed with -p, as text.
INJECTED = ('# Parameters\nRUN_DATE = "2026-11-01"\nDAYS = "2026-11-01,2026-11-08"\n'
            'START_FROM = "mart.team_days"\n')


def notebook(tmp_path: Path, parameters: str, *after: str) -> Path:
    """A Scheduled run's notebook: a text cell, the parameters cell `parameters`, then the
    code cells `after`, written as write_notebook writes one."""
    path = tmp_path / "weekly.ipynb"
    notebooks.write_notebook(path, [("markdown", "# Scheduled run: weekly"),
                                    ("code", parameters),
                                    *[("code", text) for text in after]])
    return path


def used(tmp_path: Path, parameters: str, names: dict[str, object]) -> dict[str, object]:
    """`names`, the notebook's names as its cells left them, once the build has read the
    parameters cell `parameters`: each parameter's value as read, given back."""
    scheduled_runs.use_parameters(notebook(tmp_path, parameters), SHOWN, names, CALL)
    return names


def refused(tmp_path: Path, parameters: str, names: dict[str, object]) -> str:
    """The refusal of a notebook's parameters, as one line, from what happened on."""
    with pytest.raises((ValueError, NameError)) as raised:
        used(tmp_path, parameters, names)
    return " ".join(str(raised.value).split()).removeprefix("What happened: ")


# --- Each hint, read from text ----------------------------------------------------------------


@pytest.mark.parametrize(("hint", "text", "value"), [
    ("datetime.date", "2026-11-01", datetime.date(2026, 11, 1)),
    ("int", "7", 7),
    ("int", " -3 ", -3),
    ("float", "1.5", 1.5),
    ("float", "2", 2.0),
    ("bool", "true", True),
    ("bool", "False", False),
    ("str", "mart.team_days", "mart.team_days"),
    ("datetime.date | None", "2026-11-01", datetime.date(2026, 11, 1)),
    ("datetime.date | None", "", None),
    ("list[datetime.date]", "2026-11-01,2026-11-08",
     [datetime.date(2026, 11, 1), datetime.date(2026, 11, 8)]),
    ("list[datetime.date]", '["2026-11-01", "2026-11-08"]',
     [datetime.date(2026, 11, 1), datetime.date(2026, 11, 8)]),
    ("list[int]", "1, 2,3", [1, 2, 3]),
    ("list[int]", "[1, 2]", [1, 2]),
    ("list[str] | None", "", None),
])
def test_each_hint_is_read_from_text(tmp_path: Path, hint: str, text: str,
                                     value: object) -> None:
    names = used(tmp_path, f"{PARAMETERS}DAYS: {hint} = None", {"DAYS": text})
    assert names["DAYS"] == value
    assert type(names["DAYS"]) is type(value)


@pytest.mark.parametrize(("hint", "given"), [
    ("datetime.date", datetime.date(2026, 11, 1)),
    ("int", 7),
    ("float", 7.5),
    ("bool", True),
    ("str", ""),
    ("datetime.date | None", None),
    ("list[int]", [1, 2]),
])
def test_a_value_of_its_type_is_kept_as_it_is(tmp_path: Path, hint: str,
                                              given: object) -> None:
    """A default in the cell, or a value papermill passes as a number, is read as it is."""
    assert used(tmp_path, f"{PARAMETERS}VALUE: {hint}", {"VALUE": given})["VALUE"] == given


def test_a_whole_number_given_for_a_float_is_a_float(tmp_path: Path) -> None:
    names = used(tmp_path, f"{PARAMETERS}RATE: float = 0.0", {"RATE": 2})
    assert names["RATE"] == 2.0 and isinstance(names["RATE"], float)


def test_a_number_given_for_a_str_is_its_text(tmp_path: Path) -> None:
    """papermill's -p passes 12345 as a number: a user ID hinted str is "12345"."""
    names = used(tmp_path, f'{PARAMETERS}USER_ID: str = ""', {"USER_ID": 12345})
    assert names["USER_ID"] == "12345"


# --- Each refusal -----------------------------------------------------------------------------


@pytest.mark.parametrize(("hint", "text"), [
    ("datetime.date", "2026-13-01"),
    ("datetime.date", "11/01/2026"),
    ("datetime.date", "20261101"),
    ("int", "1.5"),
    ("int", "seven"),
    ("float", "one"),
    ("bool", "yes"),
    ("list[datetime.date]", "2026-11-01,soon"),
    ("list[int]", "[1, 2"),
])
def test_a_value_that_cant_be_read_is_refused_naming_it(tmp_path: Path, hint: str,
                                                        text: str) -> None:
    said = refused(tmp_path, f"{PARAMETERS}DAYS: {hint} = None", {"DAYS": text})
    assert said.startswith(f"{CALL}: the parameter DAYS, {with_article(hint)}, was given "
                           f"\"{text}\", "
                           "which can't be read as one.")


def test_a_true_given_for_an_int_is_refused(tmp_path: Path) -> None:
    said = refused(tmp_path, f"{PARAMETERS}COUNT: int = 0", {"COUNT": True})
    assert "the parameter COUNT, an int, was given True, which can't be read as one" in said


def test_a_parameter_with_no_hint_is_refused(tmp_path: Path) -> None:
    said = refused(tmp_path, f"{PARAMETERS}RUN_DATE = None", {"RUN_DATE": None})
    assert said.startswith(f"{CALL}: the parameter RUN_DATE, in the # parameters cell of "
                           f"{SHOWN}, has no type hint.")
    assert "RUN_DATE: datetime.date | None = None" in said


@pytest.mark.parametrize("hint", ["dict[str, int]", "datetime.datetime", "list[list[int]]",
                                  "None | int", "pd.Timestamp"])
def test_a_hint_outside_those_read_is_refused_naming_those_read(tmp_path: Path,
                                                                hint: str) -> None:
    said = refused(tmp_path, f"{PARAMETERS}VALUE: {hint} = None", {"VALUE": None})
    assert f"has the hint {hint}, which the build doesn't read." in said
    assert ("Use datetime.date, int, float, bool or str, alone, in list[...] or with | None"
            in said)


@pytest.mark.parametrize(("hint", "given", "shown"), [
    ("datetime.date", None, "None"), ("datetime.date", "", '""'), ("int", "", '""'),
    ("list[int]", "", '""')])
def test_one_the_run_needs_left_empty_is_refused(tmp_path: Path, hint: str, given: object,
                                                  shown: str) -> None:
    said = refused(tmp_path, f"{PARAMETERS}VALUE: {hint} = None", {"VALUE": given})
    assert said.startswith(f"{CALL}: the parameter VALUE, {with_article(hint)}, was left "
                           f"empty: it was given {shown}.")
    assert f"write its hint {hint} | None" in said


def test_an_empty_str_is_a_value(tmp_path: Path) -> None:
    names = used(tmp_path, f'{PARAMETERS}START_FROM: str = ""', {"START_FROM": ""})
    assert names["START_FROM"] == ""


def test_a_parameter_the_notebook_doesnt_hold_is_refused(tmp_path: Path) -> None:
    said = refused(tmp_path, f"{PARAMETERS}RUN_DATE: datetime.date | None = None", {})
    assert said.startswith(f"{CALL}: the parameter RUN_DATE isn't set in this notebook.")


def test_a_notebook_with_no_parameters_cell_is_refused(tmp_path: Path) -> None:
    said = refused(tmp_path, "RUN_DATE = None", {"RUN_DATE": None})
    assert said.startswith(f"{CALL}: {SHOWN} has no cell whose first line is # parameters.")


def test_a_parameters_cell_not_tagged_is_refused(tmp_path: Path) -> None:
    path = notebook(tmp_path, f'{PARAMETERS}START_FROM: str = ""')
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"parameters"', '"injected-parameters"'), encoding="utf-8")
    with pytest.raises(ValueError, match="the # parameters cell of .* isn't tagged "
                                         "parameters"):
        scheduled_runs.use_parameters(path, SHOWN, {"START_FROM": ""}, CALL)


def test_nothing_is_given_back_when_one_is_refused(tmp_path: Path) -> None:
    names: dict[str, object] = {"FIRST": "1", "SECOND": "two"}
    refused(tmp_path, f"{PARAMETERS}FIRST: int = 0\nSECOND: int = 0", names)
    assert names == {"FIRST": "1", "SECOND": "two"}


# --- What papermill injects, and cells of the user's own --------------------------------------


def test_a_value_papermill_injects_after_the_tagged_cell_is_read(tmp_path: Path) -> None:
    """The injected cell's first line is # Parameters, tagged injected-parameters: it isn't
    read as the parameters cell, and the names it assigns are read by the cell's hints."""
    path = notebook(tmp_path, f"{PARAMETERS}RUN_DATE: datetime.date | None = None\n"
                    'DAYS: list[datetime.date] = []\nSTART_FROM: str = ""', INJECTED)
    names: dict[str, object] = {"RUN_DATE": "2026-11-01", "DAYS": "2026-11-01,2026-11-08",
                                "START_FROM": "mart.team_days"}
    scheduled_runs.use_parameters(path, SHOWN, names, CALL)
    assert names == {"RUN_DATE": datetime.date(2026, 11, 1),
                     "DAYS": [datetime.date(2026, 11, 1), datetime.date(2026, 11, 8)],
                     "START_FROM": "mart.team_days"}


def test_only_the_parameters_cell_is_read(tmp_path: Path) -> None:
    """A cell of the user's own beside it, with a user ID, is theirs: it isn't read, and its
    names aren't changed."""
    path = notebook(tmp_path, f'{PARAMETERS}START_FROM: str = ""',
                    "# my own parameters\nUSER_ID: int = 42", INJECTED)
    names: dict[str, object] = {"START_FROM": "", "USER_ID": "42"}
    parameters = scheduled_runs.use_parameters(path, SHOWN, names, CALL)
    assert [parameter.name for parameter in parameters] == ["START_FROM"]
    assert names["USER_ID"] == "42"


# --- Printed first ----------------------------------------------------------------------------


def test_each_parameter_is_printed_as_used(tmp_path: Path) -> None:
    path = notebook(tmp_path, f"{PARAMETERS}RUN_DATE: datetime.date | None = None\n"
                    'START_FROM: str = ""')
    names: dict[str, object] = {"RUN_DATE": "2026-11-01", "START_FROM": ""}
    parameters = scheduled_runs.use_parameters(path, SHOWN, names, CALL)
    assert scheduled_runs.parameter_lines(parameters) == [
        "Parameters, as this run uses them:",
        '  RUN_DATE = datetime.date(2026, 11, 1), read as datetime.date | None from '
        '"2026-11-01"',
        '  START_FROM = ""',
    ]


def test_a_cell_naming_none_says_so() -> None:
    assert scheduled_runs.parameter_lines([]) == [
        "Parameters: none, as the parameters cell names none."]
