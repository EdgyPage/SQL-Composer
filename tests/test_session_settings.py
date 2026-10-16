"""Session settings: hive_settings(...) gives the SET lines of a named set, run sends them.

Map family 3 and ADR 0006. A set is one the Toolbox ships, each documented with why, or one of
the user's own, kept in their settings.py as HIVE_SETTINGS and passed as sets=. The SET lines
aren't a Statement, but run, show_hive and export_lineage take them as they take one: run sends
each line as a call of its own, show_hive prints them, and export_lineage names them in its
footers.
"""

from __future__ import annotations

import pytest

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    equals,
    example_database,
    export_lineage,
    hive_settings,
    run,
    show_hive,
    statement,
    to_hive,
)

job_runs = example_database.job_runs

HIVE_SETTINGS = {
    "nightly": {"hive.exec.parallel": True, "mapreduce.job.reduces": 8,
                "hive.exec.orc.split.strategy": "ETL"},
}


def one_day():
    return statement(SELECT(job_runs.run_id), FROM(job_runs),
                     WHERE(equals(job_runs.dt, "2026-09-24")))


# --- The sets the Toolbox ships -------------------------------------------------------------


def test_the_dynamic_partitions_set_is_its_set_lines() -> None:
    assert to_hive(hive_settings("dynamic_partitions")) == (
        "SET hive.exec.dynamic.partition=true\n"
        "SET hive.exec.dynamic.partition.mode=nonstrict")


@pytest.mark.parametrize("name", ["dynamic_partitions", "map_joins", "statistics_on_write",
                                  "merge_small_files"])
def test_each_shipped_set_is_documented_with_why(name: str) -> None:
    doc = hive_settings.__doc__
    assert f'"{name}"' in doc
    for line in to_hive(hive_settings(name)).splitlines():
        assert line.removeprefix("SET ").split("=")[0] in doc


def test_map_joins_lets_hive_heed_broadcast_trues_hint() -> None:
    # JOIN(..., broadcast=True) writes a MAPJOIN hint, which Hive ignores while
    # hive.ignore.mapjoin.hint is true, its default: "map_joins" switches it off.
    assert to_hive(hive_settings("map_joins")) == (
        "SET hive.auto.convert.join=true\n"
        "SET hive.auto.convert.join.noconditionaltask=true\n"
        "SET hive.ignore.mapjoin.hint=false")


def test_several_sets_give_their_lines_in_the_order_named() -> None:
    lines = to_hive(hive_settings("map_joins", "dynamic_partitions")).splitlines()
    assert lines[0].startswith("SET hive.auto.convert.join")
    assert lines[-1] == "SET hive.exec.dynamic.partition.mode=nonstrict"


# --- The user's own sets ---------------------------------------------------------------------


def test_a_users_own_set_is_written_from_their_hive_settings() -> None:
    assert to_hive(hive_settings("nightly", sets=HIVE_SETTINGS)) == (
        "SET hive.exec.parallel=true\n"
        "SET mapreduce.job.reduces=8\n"
        "SET hive.exec.orc.split.strategy=ETL")


def test_a_users_set_and_a_shipped_one_go_together() -> None:
    lines = to_hive(hive_settings("dynamic_partitions", "nightly", sets=HIVE_SETTINGS))
    assert lines.splitlines()[0] == "SET hive.exec.dynamic.partition=true"
    assert lines.splitlines()[-1] == "SET hive.exec.orc.split.strategy=ETL"


def test_a_name_in_no_set_is_refused_listing_every_set() -> None:
    with pytest.raises(ValueError) as refused:
        hive_settings("nightly")
    message = str(refused.value)
    assert 'hive_settings("nightly")' in message
    assert "dynamic_partitions, map_joins, statistics_on_write, merge_small_files" in message
    assert "sets=HIVE_SETTINGS" in message


def test_a_list_of_names_is_refused_saying_to_pass_them_one_by_one() -> None:
    with pytest.raises(TypeError, match=r'hive_settings\("map_joins", "dynamic_partitions"\)'):
        hive_settings(["map_joins", "dynamic_partitions"])


def test_a_misspelt_name_is_refused_saying_to_check_the_spelling() -> None:
    with pytest.raises(ValueError, match='(?s)no set named "map_join".*Check the spelling'):
        hive_settings("map_join")


def test_a_users_set_named_like_a_shipped_one_is_refused() -> None:
    with pytest.raises(ValueError, match="dynamic_partitions.*the Toolbox ships"):
        hive_settings("dynamic_partitions",
                      sets={"dynamic_partitions": {"hive.exec.dynamic.partition": False}})


def test_no_name_is_refused() -> None:
    with pytest.raises(TypeError, match="was given no set"):
        hive_settings()


@pytest.mark.parametrize("sets, said", [
    ({"nightly": {"hive exec": 1}}, "'hive exec'"),
    ({"nightly": {"hive.exec.parallel": "true; DROP TABLE x"}}, "';'"),
    ({"nightly": {"hive.exec.parallel": "a\nb"}}, "a line break"),
    ({"nightly": {"hive.exec.parallel": None}}, "None"),
    ({"nightly": {}}, "no settings"),
    ({"nightly": ["hive.exec.parallel=true"]}, "a dict"),
    (["nightly"], "a dict"),
], ids=["a space in a name", "a semicolon", "a line break", "None", "empty", "a list as a set",
        "a list as sets"])
def test_a_set_that_cant_be_written_as_set_lines_is_refused(sets, said) -> None:
    with pytest.raises((TypeError, ValueError)) as refused:
        hive_settings("nightly", sets=sets)
    assert said in str(refused.value)


def test_two_sets_giving_one_setting_different_values_are_refused() -> None:
    sets = {"few": {"mapreduce.job.reduces": 2}, "many": {"mapreduce.job.reduces": 20}}
    with pytest.raises(ValueError, match="mapreduce.job.reduces.*2.*20"):
        hive_settings("few", "many", sets=sets)


# --- Shown and run as a Statement is ---------------------------------------------------------


def test_show_hive_prints_each_line_ending_in_a_semicolon_under_its_names(capsys) -> None:
    show_hive(hive_settings("dynamic_partitions"))
    assert capsys.readouterr().out == (
        "-- Session settings: dynamic_partitions, sent one line at a time\n"
        "SET hive.exec.dynamic.partition=true;\n"
        "SET hive.exec.dynamic.partition.mode=nonstrict;\n")


def test_show_hive_lists_the_settings_first_in_a_pipeline_as_given(capsys) -> None:
    settings = hive_settings("statistics_on_write")
    write_day = one_day()
    show_hive(settings, write_day)
    out = capsys.readouterr().out
    assert out.startswith("-- 1 of 2: settings\n-- Session settings: statistics_on_write, ")
    assert "\n\n-- 2 of 2: write_day\nSELECT" in out


def test_run_sends_each_line_as_a_call_of_its_own() -> None:
    sent = []
    assert run(hive_settings("dynamic_partitions"), send=sent.append) is None
    assert sent == ["SET hive.exec.dynamic.partition=true",
                    "SET hive.exec.dynamic.partition.mode=nonstrict"]


def test_the_example_database_takes_set_lines(tmp_path) -> None:
    run(hive_settings("merge_small_files"), send=example_database.send)
    answer = example_database.send("SET hive.merge.tezfiles=true")
    assert list(answer.columns) == ["key", "value"]
    assert answer.values.tolist() == [["hive.merge.tezfiles", "true"]]


def test_session_settings_say_how_to_see_them() -> None:
    assert repr(hive_settings("map_joins")) == (
        "<Session settings map_joins - show_hive(...) shows their SET lines>")


# --- Named in Lineage's footers --------------------------------------------------------------


def test_lineage_footers_name_the_settings_passed_with_the_statements(tmp_path) -> None:
    settings = hive_settings("map_joins", "statistics_on_write")
    html_file, markdown_file = export_lineage(settings, one_day(), to=tmp_path / "l.html")
    for text in (markdown_file.read_text(encoding="utf-8"),
                 html_file.read_text(encoding="utf-8")):
        assert ("Session settings sent before these Statements, one line at a time (map_joins "
                "and statistics_on_write): SET hive.auto.convert.join=true | "
                "SET hive.auto.convert.join.noconditionaltask=true | "
                "SET hive.ignore.mapjoin.hint=false | SET hive.stats.autogather=true | SET hive.stats.column.autogather=true.") in text
    # Drawn nowhere else: only the footer holds them.
    assert markdown_file.read_text(encoding="utf-8").count("SET hive.auto.convert.join=") == 1


def test_lineage_of_settings_alone_is_refused() -> None:
    with pytest.raises(TypeError, match="Session settings move no data"):
        export_lineage(hive_settings("map_joins"))
