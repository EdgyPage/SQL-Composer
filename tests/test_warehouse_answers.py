"""What the tools that ask the warehouse do with an answer they can't use, and their reports."""

from __future__ import annotations

import pandas as pd
import pytest

from sql_composer import (
    Table,
    all_columns,
    check_key,
    check_table_reference,
    first_look,
    write_table_reference,
)

RUNS_DESCRIBE = [
    ("run_id", "bigint", ""), ("status", "string", ""), ("dt", "string", ""),
    ("", None, None), ("# Partition Information", None, None),
    ("# col_name", "data_type", "comment"), ("dt", "string", ""),
]


def runs(**more):
    return Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
                 date_partition="dt", key=["run_id"], **more)


def answering(describe=RUNS_DESCRIBE, days=("dt=2026-09-24",), show_partitions=None):
    """A stand-in for `send`: DESCRIBE gives `describe`, SHOW PARTITIONS gives `days`."""

    def send(hive: str):
        if hive.startswith("DESCRIBE"):
            return pd.DataFrame(describe, columns=["col_name", "data_type", "comment"])
        if hive.startswith("SHOW PARTITIONS"):
            if show_partitions is not None:
                return show_partitions(hive)
            return pd.DataFrame({"partition": list(days)})
        return pd.DataFrame({"run_id": [], "copies": []})

    return send


# --- An answer the tools can't use ---------------------------------------------------------


@pytest.mark.parametrize("answer", [
    pytest.param(lambda hive: None, id="none"),
    pytest.param(lambda hive: pd.DataFrame(), id="no_columns"),
    pytest.param(lambda hive: [("dt=2026-09-24",)], id="a_list"),
])
@pytest.mark.parametrize("tool", [
    pytest.param(lambda send: write_table_reference("ops.runs", send=send),
                 id="write_table_reference"),
    pytest.param(lambda send: check_key(runs(), send=send), id="check_key"),
])
def test_an_answer_that_isnt_a_frame_is_refused(tool, answer, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises((TypeError, ValueError), match="What happened:.*send gave back"):
        tool(answer)


def test_a_send_that_isnt_a_function_is_refused(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(TypeError, match="send=None isn't a function"):
        write_table_reference("ops.runs", send=None)


def test_a_describe_with_no_columns_is_refused_by_write_table_reference(
        tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="DESCRIBE ops.runs listed no columns"):
        write_table_reference("ops.runs", send=answering(describe=[]))


def test_check_table_reference_reports_a_describe_with_no_columns() -> None:
    verdict = check_table_reference(runs(), send=answering(describe=[]))
    assert not verdict.ok
    assert "DESCRIBE listed no columns, so nothing was compared" in repr(verdict)
    assert "remove its line" not in repr(verdict)


def test_check_table_reference_reports_an_answer_it_cant_read() -> None:
    verdict = check_table_reference(runs(), send=lambda hive: None)
    assert not verdict.ok
    assert "DESCRIBE failed, so nothing was compared" in repr(verdict)


# --- A table with no days yet ----------------------------------------------------------------


def test_a_saved_table_with_no_days_yet_matches() -> None:
    verdict = check_table_reference(runs(), send=answering(days=()))
    assert verdict.ok
    text = repr(verdict)
    assert text.startswith("ops.runs matches its Table reference.")
    assert "has no days yet" in text
    assert "None" not in text and "date_partition=None" not in text


def test_write_table_reference_names_the_date_partition_of_a_table_with_no_days(
        tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    text = write_table_reference("ops.runs", send=answering(days=())).read_text(encoding="utf-8")
    assert 'date_partition="dt",  # TODO check: no days yet; once it has one' in text


# --- A day the Table reference can't read ----------------------------------------------------


def test_check_key_on_a_day_written_another_way_says_what_to_run() -> None:
    verdict = check_key(runs(), send=answering(days=("dt=20260924",)))
    assert not verdict.ok
    assert "isn't written like date_format='%Y-%m-%d', the usual one" in repr(verdict)
    assert "check_table_reference" in repr(verdict)


def test_a_failed_show_partitions_is_reported_on_one_readable_line() -> None:
    def fails(hive):
        raise RuntimeError("the cluster is down")

    text = repr(check_table_reference(runs(), send=answering(show_partitions=fails)))
    assert "It said: RuntimeError: the cluster is down" in text
    assert "  " not in text.splitlines()[-1].removeprefix("  - ")


@pytest.mark.parametrize(("days", "said"), [
    pytest.param(("dt=latest",), "isn't written like date_format='%Y-%m-%d', the usual one",
                 id="not_a_day"),
    pytest.param(("dt=2026-9-24",), "isn't written like date_format='%Y-%m-%d', the usual "
                 "one: change the line to date_partition=None,",
                 id="a_day_python_reads_but_hive_wouldnt_match"),
    pytest.param(("dt=20260924",), 'change the line to date_format="%Y%m%d"', id="another_way"),
])
def test_check_table_reference_says_which_line_a_newest_day_needs(days, said) -> None:
    assert said in repr(check_table_reference(runs(), send=answering(days=days)))


def test_check_key_on_a_table_with_no_days_says_so() -> None:
    verdict = check_key(runs(), send=answering(days=()))
    assert not verdict.ok
    assert repr(verdict) == "ops.runs: SHOW PARTITIONS found no days to check."


def test_check_table_reference_gives_the_line_for_a_changed_type() -> None:
    old = Table("ops.runs", columns={"run_id": "int", "status": "string", "dt": "string"},
                date_partition="dt")
    assert 'run_id is bigint in the table: change its line to "run_id": "bigint",' in repr(
        check_table_reference(old, send=answering()))


def test_check_table_reference_notes_columns_in_another_order() -> None:
    shuffled = Table("ops.runs", columns={"status": "string", "run_id": "bigint",
                                          "dt": "string"}, date_partition="dt")
    verdict = check_table_reference(shuffled, send=answering())
    assert verdict.ok
    assert "The table's order is: run_id, status, dt." in repr(verdict)


def test_check_table_reference_notes_a_partition_an_unpartitioned_reference_leaves_out() -> None:
    flat = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
                 date_partition=None)
    assert "name it in date_partition=" in repr(check_table_reference(flat, send=answering()))


# --- Arguments the tools can't use -----------------------------------------------------------


@pytest.mark.parametrize("call", [
    pytest.param(lambda: first_look("ops.jobs"), id="first_look"),
    pytest.param(lambda: all_columns("ops.jobs"), id="all_columns"),
])
def test_a_table_name_as_text_is_refused(call) -> None:
    with pytest.raises(TypeError, match="not its name as text"):
        call()


@pytest.mark.parametrize(("arguments", "said"), [
    pytest.param({"columns": {"run_id": int}, "date_partition": None},
                 "run_id's type is <class 'int'>", id="a_python_type"),
    pytest.param({"columns": {"dt": "string"}, "date_partition": 5},
                 "date_partition=5 isn't text", id="a_number_partition"),
])
def test_table_refuses_arguments_that_arent_text(arguments, said) -> None:
    with pytest.raises(TypeError, match=said):
        Table("ops.runs", **arguments)


@pytest.mark.parametrize(("table", "file"), [
    ("dim.calendar", "t_calendar.py"),
    ("dim.pandas", "t_pandas.py"),
    ("dim.pytest", "t_pytest.py"),
    ("dim.sql_composer", "t_sql_composer.py"),
    ("dim.customers", "customers.py"),
])
def test_write_table_reference_never_shadows_a_module(table, file, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    describe = [("id", "bigint", "")]
    assert write_table_reference(table, send=answering(describe=describe)).name == file


def test_write_table_reference_leaves_out_days_it_cant_bound(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = answering(days=("dt=2026-9-24",))
    text = write_table_reference("ops.runs", send=send).read_text(encoding="utf-8")
    assert ("date_partition=None,  # TODO: partitioned by dt; its newest dt, '2026-9-24', "
            "isn't a day the Toolbox can bound") in text


def test_a_first_partition_that_holds_no_days_points_to_the_others(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    describe = [
        ("run_id", "bigint", ""), ("region", "string", ""), ("dt", "string", ""),
        ("", None, None), ("# Partition Information", None, None),
        ("# col_name", "data_type", "comment"), ("region", "string", ""), ("dt", "string", ""),
    ]
    send = answering(describe=describe, days=("region=eu/dt=2026-09-24",))
    text = write_table_reference("ops.runs", send=send).read_text(encoding="utf-8")
    assert "isn't a day the Toolbox can bound; if dt holds the days, name it" in text
