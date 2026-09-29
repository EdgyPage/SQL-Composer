"""Table references: checking themselves, and being written and checked against Hive."""

from __future__ import annotations

import pandas as pd
import pytest

from sql_composer import (
    Table,
    check_key,
    check_table_reference,
    create_table,
    drop_table,
    example_database,
    to_hive,
    write_table_reference,
)
from sql_composer.example_database import job_runs, jobs


def describing(columns, partitions=(), days=()):
    """A stand-in for `send` at work: it answers DESCRIBE and SHOW PARTITIONS like Hive."""

    def send(hive: str) -> pd.DataFrame:
        if hive.startswith("DESCRIBE"):
            rows = [(name, kind, "") for name, kind in columns]
            if partitions:
                rows += [("", None, None), ("# Partition Information", None, None),
                         ("# col_name", "data_type", "comment")]
                rows += [(name, "string", "") for name in partitions]
            return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])
        assert hive.startswith("SHOW PARTITIONS"), hive
        return pd.DataFrame({"partition": list(days)})

    return send


# --- Table(...) checks itself ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"date_partition": "day"}, "date_partition names 'day'"),
        ({"date_partition": "dt", "key": ["id"]}, "key names 'id'"),
        ({"date_partition": "dt", "does_not_add_up": ["x"]}, "does_not_add_up names 'x'"),
        ({"date_partition": None, "date_format": "%Y%m%d"}, "no date_partition"),
        ({"date_partition": "dt", "date_format": "%d.%m"}, "%Y exactly once"),
    ],
)
def test_a_table_reference_refuses_names_that_arent_its_columns(arguments, message) -> None:
    with pytest.raises(ValueError, match=message):
        Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, **arguments)


def test_date_partition_must_be_given() -> None:
    with pytest.raises(TypeError):
        Table("ops.t", columns={"dt": "string"})


def test_a_table_name_must_be_a_hive_name() -> None:
    with pytest.raises(ValueError, match="isn't a table name"):
        Table("ops.t; drop", columns={"dt": "string"}, date_partition=None)


# --- write_table_reference -------------------------------------------------------------------


def test_write_table_reference_writes_a_file_that_imports(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = write_table_reference("ops.job_runs", send=example_database.send)
    scope: dict = {}
    exec(path.read_text(encoding="utf-8"), scope)
    written = scope["job_runs"]
    assert repr(written) == repr(job_runs)
    assert '"status": "string",  # SUCCESS / FAILED / TEST, NULL while running' in \
        path.read_text(encoding="utf-8")


def test_write_table_reference_never_overwrites(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "jobs.py").write_text("mine", encoding="utf-8")
    with pytest.raises(FileExistsError, match="nothing was written"):
        write_table_reference("ops.jobs", send=example_database.send)
    assert (tmp_path / "jobs.py").read_text(encoding="utf-8") == "mine"


def test_write_table_reference_finds_a_date_format(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = describing([("n", "int"), ("day", "string"), ("region", "string")],
                      partitions=["day", "region"],
                      days=["day=20260923/region=LON", "day=20260924/region=PAR"])
    text = write_table_reference("mart.events", send=send).read_text(encoding="utf-8")
    assert 'date_partition="day",  # TODO check: also partitioned by region' in text
    assert 'date_format="%Y%m%d",' in text


def test_write_table_reference_leaves_a_partition_that_isnt_a_date_to_you(tmp_path,
                                                                        monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = describing([("n", "int"), ("region", "string")], partitions=["region"],
                      days=["region=LON"])
    text = write_table_reference("mart.by_region", send=send).read_text(encoding="utf-8")
    assert "date_partition=None,  # TODO: partitioned by region" in text


# --- What a real warehouse sends back ---------------------------------------------------------


def answering(describe_rows, partitions, sent=None):
    """A stand-in for `send` answering with the rows given, noting every command it is sent."""

    def send(hive: str) -> pd.DataFrame:
        if sent is not None:
            sent.append(hive)
        if hive.startswith("DESCRIBE"):
            return pd.DataFrame(describe_rows, columns=["col_name", "data_type", "comment"])
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": partitions})
        return pd.DataFrame({"run_id": [], "copies": []})

    return send


# Spark lists DESCRIBE with a None comment, no blank row before the partitions, and more sections
# after them, such as the columns that have a default value.
SPARK_DESCRIBE = [
    ("run_id", "bigint", None), ("status", "string", None), ("dt", "string", None),
    ("# Partition Information", "", ""), ("# col_name", "data_type", "comment"),
    ("dt", "string", None),
    ("", "", ""), ("# Column Default Values", "", ""), ("status", "string", "'NEW'"),
]
# Hive lists a blank row before the partitions, an empty comment, and nothing after them.
HIVE_DESCRIBE = [
    ("run_id", "bigint", ""), ("status", "string", ""), ("dt", "string", ""),
    ("", None, None), ("# Partition Information", None, None),
    ("# col_name", "data_type", "comment"), ("dt", "string", ""),
]
# Spark lists a newer kind of table's partitioning as one row per column or function of one.
SPARK_PARTITIONING = [
    ("run_id", "bigint", None), ("status", "string", None), ("dt", "string", None),
    ("", "", ""), ("# Partitioning", "", ""), ("Part 0", "dt", ""),
]


@pytest.mark.parametrize("describe", [SPARK_DESCRIBE, HIVE_DESCRIBE, SPARK_PARTITIONING],
                         ids=["spark", "hive", "spark_partitioning"])
def test_describe_is_read_as_hive_and_spark_list_it(describe, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = answering(describe, ["dt=2026-09-24"])
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt")
    assert repr(check_table_reference(t, send=send)) == "ops.runs matches its Table reference."
    text = write_table_reference("ops.runs", send=send).read_text(encoding="utf-8")
    assert '"Part 0"' not in text
    assert 'date_partition="dt",\n' in text


def test_every_escaped_character_of_a_partition_value_is_read(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sent = []
    send = answering(SPARK_DESCRIBE, ["region=eu%3Dwest/dt=2026%2F09%2F24/note=50%25%5Cx"], sent)
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt", date_format="%Y/%m/%d", key=["run_id"])
    check_key(t, send=send)
    assert "runs.dt = '2026/09/24'" in sent[-1]


def test_a_section_after_the_partitions_is_not_read_as_partitions(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = answering(SPARK_DESCRIBE, ["dt=2026-09-24"])
    text = write_table_reference("ops.runs", send=send).read_text(encoding="utf-8")
    assert 'date_partition="dt",\n' in text
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt")
    assert repr(check_table_reference(t, send=send)) == "ops.runs matches its Table reference."


def test_an_escaped_partition_value_is_read_as_its_day(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    send = answering(SPARK_DESCRIBE, ["dt=2026%2F09%2F23", "dt=2026%2F09%2F24"])
    text = write_table_reference("ops.runs", send=send).read_text(encoding="utf-8")
    assert 'date_format="%Y/%m/%d",' in text


def test_the_null_day_is_never_the_newest() -> None:
    sent = []
    send = answering(SPARK_DESCRIBE, ["dt=2026-09-23", "dt=__HIVE_DEFAULT_PARTITION__"], sent)
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt", key=["run_id"])
    assert repr(check_key(t, send=send)) == "ops.runs: the key (run_id) holds on 2026-09-23."
    assert "runs.dt = '2026-09-23'" in sent[-1]


def test_a_reserved_table_name_is_quoted_in_what_is_sent(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    sent = []
    write_table_reference("ops.order", send=answering(SPARK_DESCRIBE, ["dt=2026-09-24"], sent))
    assert sent == ["DESCRIBE ops.`order`", "SHOW PARTITIONS ops.`order`"]


# --- check_table_reference --------------------------------------------------------------------


def test_a_changed_date_format_is_a_problem() -> None:
    send = describing([("run_id", "bigint"), ("dt", "string")], partitions=["dt"],
                      days=["dt=20260924"])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt")
    verdict = check_table_reference(t, send=send)
    assert not verdict.ok
    assert "change the line to date_format=\"%Y%m%d\"," in repr(verdict)


def test_a_date_partition_that_is_gone_is_a_problem() -> None:
    send = describing([("run_id", "bigint"), ("dt", "string")])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt")
    assert "dt is no longer a partition column" in repr(check_table_reference(t, send=send))


def test_a_different_column_order_is_only_a_note() -> None:
    send = describing([("b", "int"), ("a", "int")])
    t = Table("ops.t", columns={"a": "INT", "b": "int"}, date_partition=None)
    verdict = check_table_reference(t, send=send)
    assert verdict.ok
    assert "only if a Statement writes to this table" in repr(verdict)


def test_a_table_hive_cant_describe_is_reported_not_raised() -> None:
    t = Table("ops.gone", columns={"run_id": "bigint"}, date_partition=None)
    verdict = check_table_reference(t, send=example_database.send)
    assert not verdict.ok
    assert repr(verdict).startswith("ops.gone: DESCRIBE failed, so nothing was compared.")
    assert "no table 'ops.gone'" in repr(verdict)


def test_a_send_that_fails_is_reported_not_raised() -> None:
    def broken(hive: str):
        raise ConnectionError("the query API is down")

    verdict = check_table_reference(job_runs, send=broken)
    assert not verdict.ok
    assert "the query API is down" in repr(verdict)


def test_a_date_format_back_to_the_usual_one_says_to_remove_the_line() -> None:
    send = describing([("run_id", "bigint"), ("dt", "string")], partitions=["dt"],
                      days=["dt=2026-09-24"])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt",
              date_format="%Y%m%d")
    verdict = check_table_reference(t, send=send)
    assert not verdict.ok
    assert "remove the date_format line" in repr(verdict)
    assert 'date_format="%Y-%m-%d"' not in repr(verdict)


def test_a_derived_table_cant_be_checked() -> None:
    from sql_composer import FROM, SELECT, derived, statement

    teams = derived("teams", statement(SELECT(jobs.team), FROM(jobs)))
    with pytest.raises(TypeError, match="not on a table.s name as text"):
        check_table_reference(teams, send=example_database.send)


# --- check_key --------------------------------------------------------------------------------


def test_check_key_needs_a_key() -> None:
    t = Table("ops.jobs", columns={"job_id": "bigint"}, date_partition=None)
    with pytest.raises(ValueError, match="declares no key"):
        check_key(t, send=example_database.send)


@pytest.mark.needs_example_database
def test_check_key_on_a_table_with_no_date_partition() -> None:
    assert repr(check_key(jobs, send=example_database.send)) == \
        "ops.jobs: the key (job_id) holds."


# --- create_table -----------------------------------------------------------------------------


def test_create_table_refuses_untyped_columns() -> None:
    t = Table("mart.t", columns={"a": None, "b": "int", "dt": "string"}, date_partition="dt")
    with pytest.raises(ValueError, match="a has no type"):
        create_table(t)


def test_create_table_refuses_a_type_hive_doesnt_have() -> None:
    t = Table("mart.t", columns={"a": "int(", "dt": "string"}, date_partition="dt")
    with pytest.raises(ValueError, match="isn't a Hive type"):
        create_table(t)


def test_create_table_may_exist() -> None:
    t = Table("mart.t", columns={"a": "decimal(10,2)"}, date_partition=None)
    assert to_hive(create_table(t, may_exist=True)) == (
        "CREATE TABLE IF NOT EXISTS mart.t (\n  a DECIMAL(10, 2)\n)\nSTORED AS ORC")


# --- drop_table -------------------------------------------------------------------------------


def test_drop_table_drops_only_if_it_exists() -> None:
    t = Table("mart.daily_runs", columns={"runs": "bigint", "dt": "string"},
              date_partition="dt")
    assert to_hive(drop_table(t)) == "DROP TABLE IF EXISTS mart.daily_runs"


def test_drop_table_needs_a_real_tables_reference() -> None:
    with pytest.raises(TypeError, match="not on a table.s name as text"):
        drop_table("mart.daily_runs")
