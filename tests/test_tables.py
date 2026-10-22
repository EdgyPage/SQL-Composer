"""Table references: checking themselves, and being written and checked against Hive."""

from __future__ import annotations

import importlib
import re
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

from sqlglot_composer import (
    Table,
    check_key,
    check_table_reference,
    create_table,
    FROM,
    SELECT,
    WHERE,
    equals,
    example_database,
    statement,
    to_hive,
    write_table_reference,
)
from sqlglot_composer.example_database import job_runs, jobs


def describing(columns: list[tuple[str, str]], partitions: list[str] | tuple[str, ...] = (),
               days: list[str] | tuple[str, ...] = ()) -> Callable[..., pd.DataFrame]:
    """A stand-in for `query` at work: it answers DESCRIBE and SHOW PARTITIONS like Hive."""

    def query(hive: str) -> pd.DataFrame:
        if hive.startswith("DESCRIBE"):
            rows = [(name, kind, "") for name, kind in columns]
            if partitions:
                rows += [("", None, None), ("# Partition Information", None, None),
                         ("# col_name", "data_type", "comment")]
                rows += [(name, "string", "") for name in partitions]
            return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])
        assert hive.startswith("SHOW PARTITIONS"), hive
        return pd.DataFrame({"partition": list(days)})

    return query


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
def test_a_table_reference_refuses_names_that_arent_its_columns(
        arguments: dict[str, str | list[str] | None], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, **arguments)


def test_date_partition_must_be_given() -> None:
    with pytest.raises(TypeError):
        Table("ops.t", columns={"dt": "string"})


def test_a_table_name_must_be_a_hive_name() -> None:
    with pytest.raises(ValueError, match="isn't a table name"):
        Table("ops.t; drop", columns={"dt": "string"}, date_partition=None)


# --- write_table_reference -------------------------------------------------------------------


def _imported_job_runs_reference(folder: Path) -> ModuleType:
    """references/ops__job_runs.py, imported from `folder` as a notebook beside references/
    imports it, and forgotten after, so another test can write its own."""
    sys.path.insert(0, str(folder))
    try:
        return importlib.import_module("references.ops__job_runs")
    finally:
        sys.path.remove(str(folder))
        for name in ("references.ops__job_runs", "references"):
            sys.modules.pop(name, None)


def test_write_table_reference_writes_a_file_that_imports(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "references").mkdir()
    path = write_table_reference("ops.job_runs", query=example_database.query, folder="references")
    assert path == Path("references") / "ops__job_runs.py"
    written = _imported_job_runs_reference(tmp_path).job_runs
    assert repr(written) == repr(job_runs)
    # Each column's DESCRIBE comment is its description.
    assert written._descriptions["status"] == "SUCCESS / FAILED / TEST, NULL while running"


def test_an_alias_under_the_aliases_heading_imports_beside_its_table(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "references").mkdir()
    path = write_table_reference("ops.job_runs", query=example_database.query, folder="references")
    text = path.read_text(encoding="utf-8")
    assert "# --- Aliases " in text and "#     <alias> = job_runs.status" in text
    # The heading's import names the folder the file was written into.
    assert "from references.ops__job_runs import job_runs, <alias>" in text
    # The user's Aliases, as the heading's examples show them.
    aliases = 'minutes = job_runs.duration_mins\nfailed = equals(job_runs.status, "FAILED")\n'
    path.write_text(text.replace("import Table", "import Table, equals") + aliases,
                    encoding="utf-8")
    reference = _imported_job_runs_reference(tmp_path)
    hive = to_hive(statement(SELECT(reference.minutes), FROM(reference.job_runs),
                             WHERE(reference.failed,
                                   equals(reference.job_runs.dt, "2026-09-24"))))
    assert hive.startswith("SELECT\n  job_runs.duration_mins\n")
    assert "job_runs.status = 'FAILED'" in hive


def test_write_table_reference_never_overwrites(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ops__jobs.py").write_text("mine", encoding="utf-8")
    with pytest.raises(FileExistsError, match="nothing was written") as refused:
        write_table_reference("ops.jobs", query=example_database.query)
    assert (tmp_path / "ops__jobs.py").read_text(encoding="utf-8") == "mine"
    # The file by its name, in the folder you're working in: a whole path differs per computer.
    assert "ops__jobs.py already exists in the folder you're working in" in str(refused.value)
    assert str(tmp_path.name) not in str(refused.value)


def test_write_table_reference_refuses_a_folder_that_isnt_there(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match=r"folder='refrences'\): there is no such folder"):
        write_table_reference("ops.jobs", query=example_database.query, folder="refrences")
    assert list(tmp_path.iterdir()) == []


def test_write_table_reference_refuses_a_name_with_no_database(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="has no database name") as refused:
        write_table_reference("jobs", query=example_database.query)
    assert 'Write the database first, like "ops.jobs".' in str(refused.value)


@pytest.mark.parametrize(("descriptions", "said"), [
    ({"stauts": "what the run ended as"}, "descriptions names 'stauts', which isn't one"),
    ({"status": 3}, "isn't a dict of columns and text"),
    (["status"], "isn't a dict of columns and text"),
])
def test_table_refuses_descriptions_of_columns_it_doesnt_have(
        descriptions: dict[str, str | int] | list[str], said: str) -> None:
    with pytest.raises(ValueError, match=said):
        Table("ops.runs", columns={"status": "string", "dt": "string"}, date_partition="dt",
              descriptions=descriptions)


def test_write_table_reference_finds_a_date_format(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = describing([("n", "int"), ("day", "string"), ("region", "string")],
                      partitions=["day", "region"],
                      days=["day=20260923/region=LON", "day=20260924/region=PAR"])
    text = write_table_reference("mart.events", query=query).read_text(encoding="utf-8")
    assert 'date_partition="day",  # TODO check: also partitioned by region' in text
    assert 'date_format="%Y%m%d",' in text


def test_write_table_reference_leaves_a_partition_that_isnt_a_date_to_you(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = describing([("n", "int"), ("region", "string")], partitions=["region"],
                      days=["region=LON"])
    text = write_table_reference("mart.by_region", query=query).read_text(encoding="utf-8")
    assert "date_partition=None,  # TODO: partitioned by region" in text


# --- What a real warehouse sends back ---------------------------------------------------------


def answering(describe_rows: list[tuple[str, str | None, str | None]], partitions: list[str],
              sent: list[str] | None = None) -> Callable[..., pd.DataFrame]:
    """A stand-in for `query` answering with the rows given, noting every command it is sent."""

    def query(hive: str) -> pd.DataFrame:
        if sent is not None:
            sent.append(hive)
        if hive.startswith("DESCRIBE"):
            return pd.DataFrame(describe_rows, columns=["col_name", "data_type", "comment"])
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": partitions})
        return pd.DataFrame({"run_id": [], "copies": []})

    return query


# Some warehouses list DESCRIBE with a None comment, no blank row before the partitions, and
# more sections after them, such as the columns that have a default value.
COMPACT_DESCRIBE = [
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
# A newer kind of table lists its partitioning as one row per column or function of one.
NEWER_PARTITIONING = [
    ("run_id", "bigint", None), ("status", "string", None), ("dt", "string", None),
    ("", "", ""), ("# Partitioning", "", ""), ("Part 0", "dt", ""),
]


@pytest.mark.parametrize("describe", [COMPACT_DESCRIBE, HIVE_DESCRIBE, NEWER_PARTITIONING],
                         ids=["compact", "hive", "newer_partitioning"])
def test_describe_is_read_as_warehouses_list_it(
        describe: list[tuple[str, str | None, str | None]], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = answering(describe, ["dt=2026-09-24"])
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt")
    assert repr(check_table_reference(t, query=query)) == "ops.runs matches its Table reference."
    text = write_table_reference("ops.runs", query=query).read_text(encoding="utf-8")
    assert '"Part 0"' not in text
    assert 'date_partition="dt",\n' in text


def test_every_escaped_character_of_a_partition_value_is_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    sent = []
    query = answering(COMPACT_DESCRIBE, ["region=eu%3Dwest/dt=2026%2F09%2F24/note=50%25%5Cx"], sent)
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt", date_format="%Y/%m/%d", key=["run_id"])
    check_key(t, query=query)
    assert "runs.dt = '2026/09/24'" in sent[-1]


def test_a_section_after_the_partitions_is_not_read_as_partitions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = answering(COMPACT_DESCRIBE, ["dt=2026-09-24"])
    text = write_table_reference("ops.runs", query=query).read_text(encoding="utf-8")
    assert 'date_partition="dt",\n' in text
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt")
    assert repr(check_table_reference(t, query=query)) == "ops.runs matches its Table reference."


def test_an_escaped_partition_value_is_read_as_its_day(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = answering(COMPACT_DESCRIBE, ["dt=2026%2F09%2F23", "dt=2026%2F09%2F24"])
    text = write_table_reference("ops.runs", query=query).read_text(encoding="utf-8")
    assert 'date_format="%Y/%m/%d",' in text


def test_the_null_day_is_never_the_newest() -> None:
    sent = []
    query = answering(COMPACT_DESCRIBE, ["dt=2026-09-23", "dt=__HIVE_DEFAULT_PARTITION__"], sent)
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              date_partition="dt", key=["run_id"])
    assert repr(check_key(t, query=query)) == "ops.runs: the key (run_id) holds on 2026-09-23."
    assert "runs.dt = '2026-09-23'" in sent[-1]


def test_a_reserved_table_name_is_quoted_in_what_is_sent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    sent = []
    write_table_reference("ops.order", query=answering(COMPACT_DESCRIBE, ["dt=2026-09-24"], sent))
    assert sent == ["DESCRIBE ops.`order`", "SHOW PARTITIONS ops.`order`"]


# --- check_table_reference --------------------------------------------------------------------


def test_a_changed_date_format_is_a_problem() -> None:
    query = describing([("run_id", "bigint"), ("dt", "string")], partitions=["dt"],
                      days=["dt=20260924"])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt")
    verdict = check_table_reference(t, query=query)
    assert not verdict.ok
    assert "change the line to date_format=\"%Y%m%d\"," in repr(verdict)


def test_a_date_partition_that_is_gone_is_a_problem() -> None:
    query = describing([("run_id", "bigint"), ("dt", "string")])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt")
    assert "dt is no longer a partition column" in repr(check_table_reference(t, query=query))


def test_a_different_column_order_is_only_a_note() -> None:
    query = describing([("b", "int"), ("a", "int")])
    t = Table("ops.t", columns={"a": "INT", "b": "int"}, date_partition=None)
    verdict = check_table_reference(t, query=query)
    assert verdict.ok
    assert "only if a Statement writes to this table" in repr(verdict)


def test_a_table_hive_cant_describe_is_reported_not_raised() -> None:
    t = Table("ops.gone", columns={"run_id": "bigint"}, date_partition=None)
    verdict = check_table_reference(t, query=example_database.query)
    assert not verdict.ok
    assert repr(verdict).startswith("ops.gone: DESCRIBE failed, so nothing was compared.")
    assert "no table 'ops.gone'" in repr(verdict)


def test_a_query_that_fails_is_reported_not_raised() -> None:
    def broken(hive: str) -> pd.DataFrame:
        raise ConnectionError("the query API is down")

    verdict = check_table_reference(job_runs, query=broken)
    assert not verdict.ok
    assert "the query API is down" in repr(verdict)


def test_a_date_format_back_to_the_usual_one_says_to_remove_the_line() -> None:
    query = describing([("run_id", "bigint"), ("dt", "string")], partitions=["dt"],
                      days=["dt=2026-09-24"])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, date_partition="dt",
              date_format="%Y%m%d")
    verdict = check_table_reference(t, query=query)
    assert not verdict.ok
    assert "remove the date_format line" in repr(verdict)
    assert 'date_format="%Y-%m-%d"' not in repr(verdict)


def test_a_derived_table_cant_be_checked() -> None:
    from sqlglot_composer import FROM, SELECT, derived, statement

    teams = derived("teams", statement(SELECT(jobs.team), FROM(jobs)))
    with pytest.raises(TypeError, match="not on a table.s name as text"):
        check_table_reference(teams, query=example_database.query)


# --- check_key --------------------------------------------------------------------------------


def test_check_key_needs_a_key() -> None:
    t = Table("ops.jobs", columns={"job_id": "bigint"}, date_partition=None)
    with pytest.raises(ValueError, match="declares no key"):
        check_key(t, query=example_database.query)


@pytest.mark.needs_example_database
def test_check_key_on_a_table_with_no_date_partition() -> None:
    assert repr(check_key(jobs, query=example_database.query)) == \
        "ops.jobs: the key (job_id) holds."


# --- create_table -----------------------------------------------------------------------------


def test_create_table_refuses_untyped_columns() -> None:
    t = Table("mart.t", columns={"a": None, "b": "int", "dt": "string"}, date_partition="dt")
    with pytest.raises(ValueError, match="a has no type"):
        create_table(t)


@pytest.mark.parametrize("kind", ["int(", "json", "uuid", "integer", "real", "double precision",
                                  "numeric(5,1)", "varchar", "char", "interval",
                                  "timestamp with local time zone", "array<json>", "map<string>",
                                  "struct<>", "struct<int>", "array<string", "decimal(10,2",
                                  "decimal", "decimal(10)", "decimal(40,2)", "decimal(5,10)",
                                  "char(300)", "varchar(70000)", "varchar(0)",
                                  "map<array<int>,string>", "struct<select:int>",
                                  "array<struct<any:string>>"])
def test_create_table_refuses_a_type_hive_doesnt_have(kind: str) -> None:
    t = Table("mart.t", columns={"a": kind, "dt": "string"}, date_partition="dt")
    with pytest.raises(ValueError, match=f"a's type '{re.escape(kind)}' isn't one "
                       "create_table can use"):
        create_table(t)


@pytest.mark.parametrize(("kind", "fix"), [
    ("integer", "For 'integer', write 'int'."), ("Long", "For 'Long', write 'bigint'."),
    ("decimal", "For 'decimal', write 'decimal(10,0)'."),
    ("varchar", "For 'varchar', write its length, such as 'varchar(50)'."),
])
def test_create_tables_refusal_says_what_to_write_for_a_type_people_often_use(
        kind: str, fix: str) -> None:
    t = Table("mart.t", columns={"a": kind}, date_partition=None)
    with pytest.raises(ValueError, match=re.escape(fix)):
        create_table(t)


@pytest.mark.parametrize(("kind", "written"), [
    ("BIGINT", "BIGINT"), ("decimal(10,0)", "DECIMAL(10, 0)"), ("decimal(38, 2)", "DECIMAL(38, 2)"),
    ("varchar(20)", "VARCHAR(20)"), ("char(255)", "CHAR(255)"),
    ("map<string,array<int>>", "MAP<STRING, ARRAY<INT>>"),
    ("array<string>", "ARRAY<STRING>"), ("map<string,int>", "MAP<STRING, INT>"),
    # A struct is in tests/sqlglot_checks/test_sqlglot_statements.py, since sqlglot Composer
    # refuses one where its sqlglot can't write a struct's colons.
])
def test_create_table_takes_each_type_hive_has(kind: str, written: str) -> None:
    t = Table("mart.t", columns={"a": kind}, date_partition=None, location="/data/tables")
    assert to_hive(create_table(t)).startswith(f"CREATE EXTERNAL TABLE mart.t (\n  a {written}")


def test_create_table_may_exist() -> None:
    t = Table("mart.t", columns={"a": "decimal(10,2)"}, date_partition=None,
              location="/data/tables")
    assert to_hive(create_table(t, may_exist=True)) == (
        "CREATE EXTERNAL TABLE IF NOT EXISTS mart.t (\n  a DECIMAL(10, 2)\n)\nSTORED AS ORC\n"
        "LOCATION '/data/tables/mart/t'")

