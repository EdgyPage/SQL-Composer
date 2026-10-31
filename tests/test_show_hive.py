"""show_hive: the Hive that runs, printed with a ; on each Statement, ready to paste elsewhere.

What it prints is what it returns, and each Statement's text is exactly what to_hive gives and
run sends, plus the ;. Several Statements, or a list of them, are each headed by a comment
naming them.
"""

from __future__ import annotations

import pytest

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    Statement,
    equals,
    example_database,
    show_hive,
    statement,
    to_hive,
)
from sqlglot_composer import running

job_runs = example_database.job_runs


def _one_day(day: str = "2026-09-24") -> Statement:
    return statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(equals(job_runs.dt, day)))


def test_one_statement_is_its_hive_with_a_semicolon_printed_and_returned(
        capsys: pytest.CaptureFixture[str]) -> None:
    failed_runs = _one_day()
    text = show_hive(failed_runs)
    assert text == to_hive(failed_runs) + ";"
    assert capsys.readouterr().out == text + "\n"


def test_several_statements_are_each_headed_by_their_names(
        capsys: pytest.CaptureFixture[str]) -> None:
    first_day, second_day = _one_day("2026-09-23"), _one_day("2026-09-24")
    text = show_hive(first_day, second_day)
    assert text == (f"-- 1 of 2: first_day\n{to_hive(first_day)};\n\n"
                    f"-- 2 of 2: second_day\n{to_hive(second_day)};")
    assert capsys.readouterr().out == text + "\n"


def test_a_list_in_a_variable_is_shown_item_by_item(capsys: pytest.CaptureFixture[str]) -> None:
    days = [_one_day("2026-09-23"), _one_day("2026-09-24")]
    text = show_hive(days)
    assert text.splitlines()[0] == "-- 1 of 2: days[0]"
    assert f"-- 2 of 2: days[1]\n{to_hive(days[1])};" in text
    capsys.readouterr()


def test_a_statement_in_no_variable_is_headed_by_its_number_only(
        capsys: pytest.CaptureFixture[str]) -> None:
    text = show_hive(_one_day(), _one_day("2026-09-23"))
    assert text.splitlines()[0] == "-- 1 of 2"
    capsys.readouterr()


def test_statements_in_a_list_keep_their_own_names(capsys: pytest.CaptureFixture[str]) -> None:
    first_day, second_day = _one_day("2026-09-23"), _one_day("2026-09-24")
    text = show_hive([first_day, second_day])
    assert [line for line in text.splitlines() if line.startswith("--")] == [
        "-- 1 of 2: first_day", "-- 2 of 2: second_day"]
    capsys.readouterr()


def test_a_list_made_in_the_call_is_numbered(capsys: pytest.CaptureFixture[str]) -> None:
    text = show_hive([_one_day("2026-09-23"), _one_day("2026-09-24")])
    assert [line for line in text.splitlines() if line.startswith("--")] == ["-- 1 of 2",
                                                                             "-- 2 of 2"]
    capsys.readouterr()


def test_what_isnt_a_statement_is_refused() -> None:
    with pytest.raises(TypeError,
                       match="show_hive was given 'SELECT 1', which isn't a Statement"):
        show_hive("SELECT 1")
    with pytest.raises(TypeError, match=r"show_hive\(\) was given no Statement"):
        show_hive()
    with pytest.raises(TypeError, match="show_hive was given a list inside a list"):
        show_hive([[_one_day()]])


def test_what_to_hive_refuses_it_refuses_too(monkeypatch: pytest.MonkeyPatch) -> None:
    def reads_back_wrong(text: str) -> None:
        raise ValueError("the Hive read back differently")

    # to_hive reads its own Hive back; here that check fails, as it would on a bug.
    monkeypatch.setattr(running, "_self_check", reads_back_wrong)
    with pytest.raises(ValueError) as from_to_hive:
        to_hive(_one_day())
    with pytest.raises(ValueError) as from_show_hive:
        show_hive(_one_day())
    assert str(from_show_hive.value) == str(from_to_hive.value)


def test_a_notebook_shows_the_returned_text_only_once(
        capsys: pytest.CaptureFixture[str]) -> None:
    text = show_hive(_one_day())
    capsys.readouterr()
    text._ipython_display_()  # what a notebook calls to show the value of the last line
    assert capsys.readouterr().out == ""
    assert isinstance(text, str)
