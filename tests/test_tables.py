"""Table references: checking themselves, and being written and checked against Hive."""

from __future__ import annotations

import importlib
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest
from conftest import skip_unless_the_example_database_runs

from sqlglot_composer import (
    AS,
    Table,
    check_key,
    check_table_reference,
    create_table,
    derived,
    FROM,
    SELECT,
    WHERE,
    equals,
    example_database,
    first_look,
    run,
    statement,
    to_hive,
    unchecked_hive,
    write_table_reference,
)
from sqlglot_composer.example_database import job_runs, jobs


def describing(columns: list[tuple[str, str]],
               partitions: list[str] | tuple[str, ...] = ()) -> Callable[..., pd.DataFrame]:
    """A stand-in for `query` at work: it answers DESCRIBE like Hive, listing a partition
    column among the columns and again under its Partition Information."""

    def query(hive: str) -> pd.DataFrame:
        assert hive.startswith("DESCRIBE"), hive
        rows = [(name, kind, "") for name, kind in columns]
        if partitions:
            rows += [("", None, None), ("# Partition Information", None, None),
                     ("# col_name", "data_type", "comment")]
            rows += [(name, dict(columns).get(name, "string"), "") for name in partitions]
        return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])

    return query


# --- Table(...) checks itself ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"partitioned_by": ["day"]}, "partitioned_by names 'day'"),
        ({"partitioned_by": ["dt"], "key": ["id"]}, "key names 'id'"),
        ({"does_not_add_up": ["x"]}, "does_not_add_up names 'x'"),
    ],
)
def test_a_table_reference_refuses_names_that_arent_its_columns(
        arguments: dict[str, list[str]], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, **arguments)


@pytest.mark.parametrize("arguments", [
    {"date_partition": "dt"}, {"date_partition": None}, {"date_format": "%Y%m%d"},
    {"date_partition": "dt", "date_format": "%Y%m%d"},
], ids=["date_partition", "date_partition_none", "date_format", "both"])
def test_the_day_arguments_of_6_are_refused_naming_partitioned_by(
        arguments: dict[str, str | None]) -> None:
    with pytest.raises(TypeError, match="which Toolbox 7.0 replaced") as refused:
        Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, **arguments)
    said = str(refused.value)
    assert 'Write partitioned_by=["dt"] where it said date_partition="dt"' in said
    assert "remove date_format=" in said


def test_a_table_needs_no_partitions_and_no_key() -> None:
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"})
    assert t._partitioned_by == [] and t._key is None


def test_a_table_is_partitioned_by_any_columns_in_the_order_given() -> None:
    t = Table("ops.t", columns={"n": "int", "load_id": "bigint", "region": "string"},
              partitioned_by=["region", "load_id"])
    assert t._partitioned_by == ["region", "load_id"]


def test_a_table_name_must_be_a_hive_name() -> None:
    with pytest.raises(ValueError, match="isn't a table name"):
        Table("ops.t; drop", columns={"dt": "string"})


# --- The text of a table and of a column -----------------------------------------------------


def test_a_tables_text_is_as_from_writes_it_and_a_columns_as_select_does() -> None:
    assert str(jobs) == f"{jobs}" == "ops.jobs AS jobs"
    assert str(jobs.job_id) == f"{jobs.job_id}" == "jobs.job_id"
    assert f"SELECT {jobs.job_id} FROM {jobs}" == "SELECT jobs.job_id FROM ops.jobs AS jobs"
    # Its repr, what a notebook shows for it, stays the Table reference's.
    assert repr(jobs) == "Table('ops.jobs', columns: job_id, job_name, team, region)"


def test_a_second_name_and_a_derived_table_give_the_name_from_reads() -> None:
    earlier = AS(job_runs, "earlier")
    assert f"{earlier}" == "ops.job_runs AS earlier"
    assert f"{earlier.run_id}" == "earlier.run_id"
    latest = derived("latest", statement(SELECT(jobs.job_id), FROM(jobs)))
    assert f"{latest}" == "latest"
    assert f"{AS(latest, 'newest')}" == "latest AS newest"
    assert f"{latest.job_id}" == "latest.job_id"


def test_a_name_hive_needs_quoted_is_quoted_in_the_text() -> None:
    odd = Table("ops.from", columns={"select": "string"})
    assert f"{odd}" == "ops.`from` AS `from`"
    assert f"{getattr(odd, 'select')}" == "`from`.`select`"


def test_a_format_spec_works_on_a_table_and_a_column_as_on_a_str() -> None:
    assert f"[{jobs.team:>12}]" == f"[{'jobs.team':>12}]" == "[   jobs.team]"
    assert f"[{jobs:<20}]" == "[ops.jobs AS jobs    ]"
    assert format(jobs.team, "^13") == "  jobs.team  "
    with pytest.raises(ValueError):  # what a str gives for a spec for numbers
        f"{jobs.team:d}"


def test_the_text_of_a_table_and_its_columns_is_hive_that_runs() -> None:
    skip_unless_the_example_database_runs()
    by_hand = unchecked_hive(f"SELECT {jobs.job_id}, {jobs.job_name} FROM {jobs} "
                             f"ORDER BY {jobs.job_id}", returns_rows=True)
    rows = run(by_hand, query=example_database.query)
    assert list(rows.columns) == ["job_id", "job_name"]
    assert list(rows["job_id"]) == [1, 2, 3, 4]


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
        Table("ops.runs", columns={"status": "string", "dt": "string"}, partitioned_by=["dt"],
              descriptions=descriptions)


def test_write_table_reference_writes_every_partition_column_in_hives_order(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = describing([("n", "int"), ("day", "string"), ("load_id", "bigint")],
                      partitions=["day", "load_id"])
    path = write_table_reference("mart.events", query=query)
    text = path.read_text(encoding="utf-8")
    assert '    partitioned_by=["day", "load_id"],\n' in text
    assert "date_partition" not in text and "date_format" not in text
    # The file it writes is a Table reference that runs, partitioned as Hive says.
    monkeypatch.syspath_prepend(str(tmp_path))
    reference = importlib.import_module("mart__events")
    assert reference.events._partitioned_by == ["day", "load_id"]


def test_write_table_reference_writes_no_partitioned_by_for_an_unpartitioned_table(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = describing([("n", "int"), ("region", "string")])
    text = write_table_reference("mart.by_region", query=query).read_text(encoding="utf-8")
    assert "partitioned_by" not in text
    assert "date_partition" not in text


# --- What a real warehouse sends back ---------------------------------------------------------


def answering(describe_rows: list[tuple[str, str | None, str | None]],
              sent: list[str] | None = None) -> Callable[..., pd.DataFrame]:
    """A stand-in for `query` answering DESCRIBE with the rows given, and any other command
    with no repeated keys, noting every command it is sent."""

    def query(hive: str) -> pd.DataFrame:
        if sent is not None:
            sent.append(hive)
        if hive.startswith("DESCRIBE"):
            return pd.DataFrame(describe_rows, columns=["col_name", "data_type", "comment"])
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
    query = answering(describe)
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              partitioned_by=["dt"])
    assert repr(check_table_reference(t, query=query)) == "ops.runs matches its Table reference."
    text = write_table_reference("ops.runs", query=query).read_text(encoding="utf-8")
    assert '"Part 0"' not in text
    assert 'partitioned_by=["dt"],\n' in text


def test_a_section_after_the_partitions_is_not_read_as_partitions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    query = answering(COMPACT_DESCRIBE)
    text = write_table_reference("ops.runs", query=query).read_text(encoding="utf-8")
    assert 'partitioned_by=["dt"],\n' in text
    t = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
              partitioned_by=["dt"])
    assert repr(check_table_reference(t, query=query)) == "ops.runs matches its Table reference."


def test_a_reserved_table_name_is_quoted_in_what_is_sent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    sent = []
    write_table_reference("ops.order", query=answering(COMPACT_DESCRIBE, sent))
    # DESCRIBE alone: the partition columns are in what it lists.
    assert sent == ["DESCRIBE ops.`order`"]


# --- check_table_reference --------------------------------------------------------------------


@pytest.mark.parametrize(("partitioned_by", "hives"), [
    (["dt"], ["region", "dt"]), (["region", "dt"], ["dt", "region"]), ([], ["dt"]),
], ids=["another_column_too", "another_order", "an_unpartitioned_reference"])
def test_a_partitioned_by_that_differs_is_a_problem_with_its_line(
        partitioned_by: list[str], hives: list[str]) -> None:
    query = describing([("run_id", "bigint"), ("region", "string"), ("dt", "string")],
                      partitions=hives)
    t = Table("ops.t", columns={"run_id": "bigint", "region": "string", "dt": "string"},
              partitioned_by=partitioned_by)
    verdict = check_table_reference(t, query=query)
    assert not verdict.ok
    assert (f"the table is partitioned by {', '.join(hives)}: change the line to "
            f"partitioned_by={json.dumps(hives)},") in repr(verdict)


def test_a_partitioned_by_the_table_no_longer_has_is_a_problem() -> None:
    query = describing([("run_id", "bigint"), ("dt", "string")])
    t = Table("ops.t", columns={"run_id": "bigint", "dt": "string"}, partitioned_by=["dt"])
    verdict = check_table_reference(t, query=query)
    assert not verdict.ok
    assert "the table isn't partitioned: remove the line partitioned_by=." in repr(verdict)


def test_a_partitioned_by_that_matches_is_no_problem() -> None:
    query = describing([("run_id", "bigint"), ("region", "string"), ("dt", "string")],
                      partitions=["region", "dt"])
    t = Table("ops.t", columns={"run_id": "bigint", "region": "string", "dt": "string"},
              partitioned_by=["region", "dt"])
    assert repr(check_table_reference(t, query=query)) == "ops.t matches its Table reference."


def test_a_different_column_order_is_only_a_note() -> None:
    query = describing([("b", "int"), ("a", "int")])
    t = Table("ops.t", columns={"a": "INT", "b": "int"})
    verdict = check_table_reference(t, query=query)
    assert verdict.ok
    assert "only if a Statement writes to this table" in repr(verdict)


def test_a_table_hive_cant_describe_is_reported_not_raised() -> None:
    t = Table("ops.gone", columns={"run_id": "bigint"})
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


def test_a_derived_table_cant_be_checked() -> None:
    from sqlglot_composer import FROM, SELECT, derived, statement

    teams = derived("teams", statement(SELECT(jobs.team), FROM(jobs)))
    with pytest.raises(TypeError, match="not on a table.s name as text"):
        check_table_reference(teams, query=example_database.query)


# --- check_key --------------------------------------------------------------------------------


def test_check_key_needs_a_key() -> None:
    t = Table("ops.jobs", columns={"job_id": "bigint"})
    with pytest.raises(ValueError, match="declares no key"):
        check_key(t, query=example_database.query)


@pytest.mark.needs_example_database
def test_check_key_on_an_unpartitioned_table_reads_it_whole() -> None:
    assert repr(check_key(jobs, query=example_database.query)) == \
        "ops.jobs: the key (job_id) holds."


RUNS = Table("ops.runs", columns={"run_id": "bigint", "status": "string", "dt": "string"},
             partitioned_by=["dt"], key=["run_id"])


def test_check_key_on_a_partitioned_table_needs_where_or_reads_all_partitions() -> None:
    sent = []
    with pytest.raises(ValueError, match="nothing says which Partitions to check") as refused:
        check_key(RUNS, query=answering(COMPACT_DESCRIBE, sent))
    assert "where=equals(runs.dt, <value>)" in str(refused.value)
    assert "reads_all_partitions=True" in str(refused.value)
    assert sent == []


def test_check_key_reads_what_where_picks_and_says_so() -> None:
    sent = []
    verdict = check_key(RUNS, query=answering(COMPACT_DESCRIBE, sent),
                        where=equals(RUNS.dt, "2026-09-24"))
    assert repr(verdict) == "ops.runs: the key (run_id) holds where runs.dt = '2026-09-24'."
    assert "WHERE\n  runs.dt = '2026-09-24'" in sent[-1]


def test_check_key_reads_every_partition_when_asked() -> None:
    sent = []
    verdict = check_key(RUNS, query=answering(COMPACT_DESCRIBE, sent), reads_all_partitions=True)
    assert repr(verdict) == "ops.runs: the key (run_id) holds."
    assert "WHERE" not in sent[-1]


@pytest.mark.needs_example_database
def test_check_key_reports_a_repeat_where_where_picks() -> None:
    alerts = Table("ops.run_alerts", columns={"alert_id": "bigint", "run_id": "bigint",
                   "severity": "string", "dt": "string"}, partitioned_by=["dt"], key=["run_id"])
    verdict = check_key(alerts, query=example_database.query,
                        where=equals(alerts.dt, "2026-09-24"))
    assert not verdict.ok
    assert repr(verdict).startswith(
        "ops.run_alerts: the key (run_id) repeats where run_alerts.dt = '2026-09-24'.")


# --- first_look -------------------------------------------------------------------------------


def test_first_look_reads_a_partitioned_table_with_no_where() -> None:
    hive = to_hive(first_look(RUNS))
    assert "WHERE" not in hive
    assert hive.endswith("FROM ops.runs AS runs\nLIMIT 20")


@pytest.mark.needs_example_database
def test_first_look_runs_on_a_partitioned_table() -> None:
    from sqlglot_composer import run

    # Every Partition is read, without a Load limit refusing the read.
    rows = run(first_look(job_runs), query=example_database.query)
    assert set(rows["dt"]) == {"2026-09-23", "2026-09-24"}


# --- create_table -----------------------------------------------------------------------------


def test_create_table_refuses_untyped_columns() -> None:
    t = Table("mart.t", columns={"a": None, "b": "int", "dt": "string"}, partitioned_by=["dt"])
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
    t = Table("mart.t", columns={"a": kind, "dt": "string"}, partitioned_by=["dt"])
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
    t = Table("mart.t", columns={"a": kind})
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
    t = Table("mart.t", columns={"a": kind}, location="/data/your_team/mart.db/t")
    assert to_hive(create_table(t)).startswith(f"CREATE EXTERNAL TABLE mart.t (\n  a {written}")


def test_create_table_may_exist() -> None:
    t = Table("mart.t", columns={"a": "decimal(10,2)"}, location="/data/your_team/mart.db/t")
    assert to_hive(create_table(t, may_exist=True)) == (
        "CREATE EXTERNAL TABLE IF NOT EXISTS mart.t (\n  a DECIMAL(10, 2)\n)\nSTORED AS ORC\n"
        "LOCATION '/data/your_team/mart.db/t'")

