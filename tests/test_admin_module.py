"""The admin module: changes to the user's own Saved tables, written and checked for them.

Map family 4 and ADR 0006. `from sqlglot_composer import admin` (the star import leaves it
out) gives drop_table, drop_partitions, add_columns, set_properties and move_to_own_folder.
Each makes
an ordinary Statement, or for the move a list of them, which run sends like any other and logs
in the Admin log; show_hive prints what it changes, what can't be undone and what to check
first, ahead of its Hive; and each refuses a table that isn't one of the user's Saved tables.
The golden corpus pins every one's Hive and notes (the `edge:admin:*` cases).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module
from hive_corpus_cases import warehouse

import sqlglot_composer
from sqlglot_composer import (
    FROM,
    SELECT,
    Statement,
    Table,
    admin,
    all_of,
    any_of,
    between,
    create_table,
    derived,
    equals,
    example_database,
    export_lineage,
    less_than,
    run_query, run_execute,
    set_admin_log,
    show_hive,
    statement,
    to_hive,
)
from sqlglot_composer.describe import StandIn

job_runs = example_database.job_runs
# Where the warehouse says a Saved table is before it is moved: a folder it shares with others.
SHARED = "hdfs://namenode:8020/data/your_team/tables"


def saved(name: str = "mart.daily_runs", columns: dict[str, str | None] | None = None,
          partitioned_by: list[str] | None = None, **storage: object) -> Table:
    """One of the user's Saved tables, in its own folder, partitioned by dt unless
    partitioned_by= or columns= says otherwise."""
    columns = columns or {"job_id": "bigint", "runs": "bigint", "dt": "string"}
    if partitioned_by is None:
        partitioned_by = ["dt"] if "dt" in columns else []
    database, table = name.split(".")
    location = storage.pop("location", f"/data/your_team/{database}.db/{table}")
    return Table(name, columns=columns, partitioned_by=partitioned_by or None,
                 location=location, **storage)


def at_work(t: Table, **answer: str | bool | tuple[str, ...] | pd.DataFrame) -> StandIn:
    """A stand-in warehouse holding t, at a folder it shares with others unless `answer` names
    another."""
    return warehouse(t, **{"location": SHARED, **answer})


# --- Where it is ---------------------------------------------------------------------------


def test_admin_is_imported_by_name_and_the_star_import_leaves_it_out() -> None:
    assert "admin" not in sqlglot_composer.__all__
    assert "drop_table" not in sqlglot_composer.__all__
    assert not hasattr(sqlglot_composer, "drop_table")
    assert admin.__all__ == ["drop_table", "drop_partitions", "add_columns", "set_properties",
                             "move_to_own_folder", "check_the_copy"]


def test_drop_days_is_gone() -> None:
    assert not hasattr(admin, "drop_days")


# --- Each refuses a table that isn't one of the user's Saved tables ------------------------


def _refusing(call: str) -> Callable[[object], Statement | list[Statement]]:
    return {
        "drop_table": lambda t: admin.drop_table(t),
        "drop_partitions": lambda t: admin.drop_partitions(
            t, where=less_than(job_runs.dt, "2025-01-01")),
        "add_columns": lambda t: admin.add_columns(t, query=at_work(saved())),
        "set_properties": lambda t: admin.set_properties(t),
        "move_to_own_folder": lambda t: admin.move_to_own_folder(t, query=at_work(saved())),
        "check_the_copy": lambda t: admin.check_the_copy(t, query=at_work(saved())),
    }[call]


@pytest.mark.parametrize("call", admin.__all__)
def test_a_table_someone_else_owns_is_refused(call: str) -> None:
    with pytest.raises(ValueError, match=rf"admin\.{call}\(\.\.\.\) was given ops\.job_runs, "
                                         "which isn't one of your Saved tables"):
        _refusing(call)(job_runs)


@pytest.mark.parametrize("call", admin.__all__)
def test_a_name_or_a_derived_table_is_refused(call: str) -> None:
    with pytest.raises(TypeError, match="not on a table.s name as text"):
        _refusing(call)("mart.daily_runs")
    runs = derived("runs", statement(SELECT(job_runs.run_id),
                                     FROM(job_runs, reads_all_partitions=True)))
    with pytest.raises(TypeError, match="or on a Derived table"):
        _refusing(call)(runs)


def test_need_saved_table_is_the_one_check() -> None:
    need = toolbox_module("tables").need_saved_table
    t = saved()
    assert need(t, "repair_partitions(...)") is t
    with pytest.raises(ValueError,
                       match=r"repair_partitions\(\.\.\.\) was given ops\.job_runs"):
        need(job_runs, "repair_partitions(...)")


# --- drop_table and drop_partitions -----------------------------------------------------------


def test_drop_table_drops_only_if_it_exists() -> None:
    assert to_hive(admin.drop_table(saved())) == "DROP TABLE IF EXISTS mart.daily_runs"


def test_show_hive_prints_what_it_changes_and_what_cant_be_undone_first(
        capsys: pytest.CaptureFixture[str]) -> None:
    text = show_hive(admin.drop_table(saved(purge=True)))
    lines = text.splitlines()
    assert lines[-1] == "DROP TABLE IF EXISTS mart.daily_runs;"
    assert all(line.startswith("-- ") for line in lines[:-1])
    notes = " ".join(line[3:] for line in lines[:-1])
    assert "drops the table mart.daily_runs" in notes
    assert "Can't be undone when the table itself has external.table.purge true" in notes
    assert "Check first: DESCRIBE FORMATTED mart.daily_runs" in notes


def test_without_purge_the_notes_say_the_files_stay() -> None:
    notes = " ".join(admin.drop_table(saved())._admin_about)
    assert "files stay in the table's folder, /data/your_team/mart.db/daily_runs" in notes


REGION_RUNS = saved("mart.region_runs", columns={"job_id": "bigint", "runs": "bigint",
                                                 "region": "string", "dt": "string"},
                    partitioned_by=["region", "dt"])
region_runs = REGION_RUNS


@pytest.mark.parametrize(("where", "dropped"), [
    (equals(region_runs.region, "EU"), "region = 'EU'"),
    (less_than(region_runs.dt, "2025-01-01"), "dt < '2025-01-01'"),
    (all_of(equals(region_runs.region, "EU"), less_than(region_runs.dt, "2025-01-01")),
     "region = 'EU', dt < '2025-01-01'"),
    ([equals(region_runs.region, "EU"), between(region_runs.dt, "2025-01-01", "2025-01-31")],
     "region = 'EU', dt >= '2025-01-01', dt <= '2025-01-31'"),
], ids=["equals", "less_than", "all_of", "a list, with between"])
def test_drop_partitions_drops_the_partitions_where_picks(
        where: object, dropped: str) -> None:
    assert to_hive(admin.drop_partitions(region_runs, where=where)) == (
        f"ALTER TABLE mart.region_runs DROP IF EXISTS PARTITION ({dropped})")


def test_drop_partitions_writes_a_value_as_it_is_given() -> None:
    compact = saved(columns={"job_id": "bigint", "day": "string"}, partitioned_by=["day"])
    assert to_hive(admin.drop_partitions(compact, where=less_than(compact.day, "20250101"))
                   ).endswith("PARTITION (day < '20250101')")


@pytest.mark.parametrize(("where", "says"), [
    (any_of(equals(region_runs.region, "EU"), equals(region_runs.region, "US")),
     "where= holds any_of(...)."),
    (equals(region_runs.job_id, 3),
     "region_runs.job_id isn't one of mart.region_runs's partition columns."),
    (equals(region_runs.dt, region_runs.region),
     "dt is compared with region_runs.region, which isn't a value."),
    (equals(job_runs.dt, "2025-01-01"), "job_runs.dt isn't a column of region_runs."),
], ids=["any_of", "not a partition column", "a column compared with a column",
        "another table's column"])
def test_drop_partitions_refuses_what_drop_partition_cant_take(where: object,
                                                               says: str) -> None:
    with pytest.raises(ValueError) as refused:
        admin.drop_partitions(region_runs, where=where)
    assert says in " ".join(str(refused.value).split())


def test_drop_partitions_refuses_a_table_with_no_partitions() -> None:
    whole = saved(columns={"job_id": "bigint"})
    with pytest.raises(ValueError, match="whose Table reference has no partitioned_by=") as (
            refused):
        admin.drop_partitions(whole, where=equals(whole.job_id, 3))
    # Its fix names the write that replaces such a table whole.
    assert "INSERT_OVERWRITE(daily_runs)" in str(refused.value)


def test_drop_partitions_needs_where() -> None:
    # where= is required: Python itself names it when it is left out.
    with pytest.raises(TypeError, match="required keyword-only argument: 'where'"):
        admin.drop_partitions(region_runs)


def test_drop_partitions_refuses_a_tuple_in_where_naming_the_list_it_takes() -> None:
    with pytest.raises(ValueError, match=r"was given a tuple in where=") as refused:
        admin.drop_partitions(region_runs, where=(equals(region_runs.region, "EU"),))
    assert "as a list: where=[..., ...]" in str(refused.value)


# --- add_columns ------------------------------------------------------------------------------

WIDER = {"job_id": "bigint", "runs": "bigint", "fails": "bigint", "note": "string",
         "dt": "string"}


def test_add_columns_adds_what_the_table_lacks_with_cascade() -> None:
    t = saved(columns=WIDER)
    assert to_hive(admin.add_columns(t, query=at_work(t, lacking=("fails", "note")))) == (
        "ALTER TABLE mart.daily_runs ADD COLUMNS (\n  fails BIGINT,\n  note STRING\n) CASCADE")


def test_add_columns_cascades_into_any_partitioned_table() -> None:
    t = saved(columns={"job_id": "bigint", "note": "string", "region": "string"},
              partitioned_by=["region"])
    assert to_hive(admin.add_columns(t, query=at_work(t, lacking=("note",)))) == (
        "ALTER TABLE mart.daily_runs ADD COLUMNS (\n  note STRING\n) CASCADE")


def test_add_columns_sends_describe_and_writes_no_cascade_without_partitions() -> None:
    t = saved(columns={"job_id": "bigint", "note": "string"})
    query = at_work(t, lacking=("note",))
    adding = admin.add_columns(t, query=query)
    assert query.sent == ["DESCRIBE mart.daily_runs"]
    assert to_hive(adding) == "ALTER TABLE mart.daily_runs ADD COLUMNS (\n  note STRING\n)"


@pytest.mark.parametrize("lacking, refusal", [
    ((), "has every column of its Table reference already"),
    (("fails",), "lists fails before note, which the table has already"),
])
def test_add_columns_refuses_what_it_cant_add(lacking: tuple[str, ...], refusal: str) -> None:
    t = saved(columns=WIDER)
    with pytest.raises(ValueError, match=refusal):
        admin.add_columns(t, query=at_work(t, lacking=lacking))


def test_add_columns_refuses_a_new_partition_and_a_column_with_no_type() -> None:
    region = saved(columns={"job_id": "bigint", "region": "string", "dt": "string"},
                   partitioned_by=["region", "dt"])
    with pytest.raises(ValueError, match="region is a partition column in the Table "
                                         "reference, but not in the table"):
        admin.add_columns(region, query=at_work(region, lacking=("region",)))
    untyped = saved(columns={"job_id": "bigint", "fails": None, "dt": "string"})
    with pytest.raises(ValueError, match="fails has no type"):
        admin.add_columns(untyped, query=at_work(untyped, lacking=("fails",)))
    odd = saved(columns={"job_id": "bigint", "fails": "integer", "dt": "string"})
    with pytest.raises(ValueError,
                       match=r"admin\.add_columns\(mart\.daily_runs, query=\.\.\.\): "
                             "fails's type 'integer'"):
        admin.add_columns(odd, query=at_work(odd, lacking=("fails",)))


# --- set_properties ---------------------------------------------------------------------------


def test_set_properties_sets_what_the_table_reference_gives() -> None:
    t = saved(purge=False, compression="ZLIB", properties={"made_by": "daily"})
    assert to_hive(admin.set_properties(t)) == (
        "ALTER TABLE mart.daily_runs SET TBLPROPERTIES (\n"
        "  'external.table.purge'='false',\n"
        "  'orc.compress'='ZLIB',\n"
        "  'made_by'='daily'\n"
        ")")


def test_set_properties_refuses_a_table_reference_that_gives_none() -> None:
    with pytest.raises(ValueError, match="gives no purge=, compression= or properties="):
        admin.set_properties(saved())


# --- move_to_own_folder and check_the_copy ----------------------------------------------------


# The comparison's answer when every Partition matches: its columns, and no row.
MATCHING = pd.DataFrame({"dt": [], "old_rows": [], "copied_rows": []})


def comparing(t: Table, compared: pd.DataFrame = MATCHING,
              **answer: str | bool | tuple[str, ...]) -> StandIn:
    """The warehouse's answers for check_the_copy: DESCRIBE FORMATTED as at_work gives it,
    then `compared` for the comparison of the counts."""
    return at_work(t, rows=compared, **answer)


def comparisons(query: StandIn) -> list[str]:
    """The Hive of each comparison of the counts the stand-in was sent."""
    return [hive for hive in query.sent if hive.startswith("WITH old_counts AS (")]


def test_the_move_creates_and_copies_then_the_check_keeps_files_drops_and_renames() -> None:
    t = saved(key=["job_id", "dt"])
    moves = admin.move_to_own_folder(t, query=at_work(t))
    hives = [to_hive(step) for step in moves]
    assert len(hives) == 2
    assert hives[0].startswith("CREATE EXTERNAL TABLE IF NOT EXISTS mart.daily_runs_moving (")
    assert "LOCATION '/data/your_team/mart.db/daily_runs'" in hives[0]
    assert hives[1].startswith("INSERT OVERWRITE TABLE mart.daily_runs_moving PARTITION(dt)")
    assert [step._admin_call for step in moves] == [
        f"admin.move_to_own_folder(mart.daily_runs, query=...)[{n}]" for n in range(2)]
    finish = admin.check_the_copy(t, query=comparing(t))
    assert [to_hive(step) for step in finish] == [
        "ALTER TABLE mart.daily_runs SET TBLPROPERTIES (\n  'external.table.purge'='false'\n)",
        "DROP TABLE IF EXISTS mart.daily_runs",
        "ALTER TABLE mart.daily_runs_moving RENAME TO mart.daily_runs"]
    assert [step._admin_call for step in finish] == [
        f"admin.check_the_copy(mart.daily_runs, query=...)[{n}]" for n in range(3)]


def test_every_step_of_the_move_goes_to_execute() -> None:
    t = saved()
    sent = []
    for step in admin.move_to_own_folder(t, query=at_work(t)):
        run_execute(step, sent.append)
    for step in admin.check_the_copy(t, query=comparing(t)):
        run_execute(step, sent.append)
    assert len(sent) == 5
    with pytest.raises(ValueError, match="run_query was given an Admin statement"):
        run_query(admin.move_to_own_folder(t, query=at_work(t))[0], at_work(t))


def test_the_move_copies_the_whole_table_in_one_write() -> None:
    t = REGION_RUNS
    copy = admin.move_to_own_folder(t, query=at_work(t))[1]
    assert to_hive(copy) == (
        "INSERT OVERWRITE TABLE mart.region_runs_moving PARTITION(region, dt)\nSELECT\n"
        "  region_runs.job_id,\n  region_runs.runs,\n  region_runs.region,\n  region_runs.dt\n"
        "FROM mart.region_runs AS region_runs")
    # Each Partition is filled from the rows, which needs dynamic partitioning sent first.
    assert any('run_execute(hive_settings("dynamic_partitions"), execute) before it' in item
               for item in copy._admin_about)


def test_the_check_compares_each_partition_rows_with_no_value_too() -> None:
    t = REGION_RUNS
    query = comparing(t)
    admin.check_the_copy(t, query=query)
    compare, = comparisons(query)
    for counts, alias in (("old_counts", "region_runs"),
                          ("copied_counts", "region_runs_moving")):
        assert (f"{counts} AS (\n  SELECT\n"
                f"    COALESCE(CAST({alias}.region AS STRING), '__HIVE_DEFAULT_PARTITION__') "
                f"AS region,\n"
                f"    COALESCE(CAST({alias}.dt AS STRING), '__HIVE_DEFAULT_PARTITION__') "
                "AS dt,\n"
                "    COUNT(*) AS row_count\n") in compare
    assert ("LEFT JOIN copied_counts\n"
            "  ON copied_counts.region = old_counts.region "
            "AND copied_counts.dt = old_counts.dt\n"
            "WHERE\n  copied_counts.row_count IS NULL\n"
            "  OR copied_counts.row_count <> old_counts.row_count") in compare


def test_the_check_of_an_unpartitioned_table_compares_its_rows_whole() -> None:
    whole = saved(columns={"job_id": "bigint"})
    query = comparing(whole, pd.DataFrame({"old_rows": [], "copied_rows": []}),
                      location="/data/elsewhere")
    admin.check_the_copy(whole, query=query)
    compare, = comparisons(query)
    assert "GROUP BY" not in compare
    assert "FROM old_counts\nCROSS JOIN copied_counts\n" in compare


def test_a_managed_table_is_moved_without_setting_purge() -> None:
    t = saved()
    managed = {"location": "hdfs://namenode:8020/warehouse/mart.db/daily_runs",
               "managed": True}
    moves = admin.move_to_own_folder(t, query=at_work(t, **managed))
    finish = admin.check_the_copy(t, query=comparing(t, **managed))
    assert not any("TBLPROPERTIES" in to_hive(step) for step in moves + finish)
    assert len(finish) == 2
    assert "its files go too, since it is managed" in finish[0]._admin_about[0]


@pytest.mark.parametrize("answer, refusal", [
    ({"location": "hdfs://namenode:8020/data/your_team/mart.db/daily_runs"},
     "is at its own folder already"),
    ({"lacking": ("runs",)}, "has no column runs, which its Table reference lists"),
])
@pytest.mark.parametrize("call", [admin.move_to_own_folder, admin.check_the_copy])
def test_the_move_refuses_a_table_it_cant_or_neednt_move(
        call: Callable[..., list[Statement]], answer: dict[str, str | tuple[str, ...]],
        refusal: str) -> None:
    t = saved()
    with pytest.raises(ValueError, match=refusal):
        call(t, query=comparing(t, **answer))


def test_the_check_stops_the_move_and_logs_it_when_a_partition_differs(
        tmp_path: Path) -> None:
    log = set_admin_log(tmp_path / "admin_log.md")
    t = saved()
    differ = pd.DataFrame({"dt": ["2026-09-24"], "old_rows": [3], "copied_rows": [2]})
    with pytest.raises(ValueError, match="The move of mart.daily_runs stopped") as refused:
        admin.check_the_copy(t, query=comparing(t, differ))
    assert "then call admin.check_the_copy again." in str(refused.value)
    assert len(admin.check_the_copy(t, query=comparing(t))) == 3
    text = log.read_text(encoding="utf-8")
    assert "- Call: `admin.check_the_copy(mart.daily_runs, query=...)`" in text
    assert "- Result: failed, with ValueError:" in text
    assert text.count("- Result: worked") == 1


def test_the_drop_comes_only_from_the_check() -> None:
    """A loop over move_to_own_folder's steps can't drop the old table before the
    comparison: none of them drops anything."""
    t = saved()
    moves = admin.move_to_own_folder(t, query=at_work(t))
    assert not any("DROP" in to_hive(step) for step in moves)


@pytest.mark.parametrize("make", [
    pytest.param(lambda: admin.drop_table(saved()), id="drop_table"),
    pytest.param(lambda: admin.drop_partitions(region_runs, where=equals(region_runs.region,
                                                                         "EU")),
                 id="drop_partitions"),
    pytest.param(lambda: admin.set_properties(saved(purge=True)), id="set_properties"),
])
def test_an_admin_statement_goes_to_execute_and_gives_back_none(
        make: Callable[[], Statement]) -> None:
    sent = []
    assert run_execute(make(), sent.append) is None
    assert sent == [to_hive(make())]


def test_an_admin_statement_given_to_run_query_is_refused_naming_run_execute() -> None:
    sent = []
    with pytest.raises(ValueError, match=r"Send it with run_execute\(s, execute\)\."):
        run_query(admin.drop_table(saved()), sent.append)
    assert sent == []


@pytest.mark.parametrize("make", [
    pytest.param(lambda **given: admin.add_columns(saved(columns=WIDER), **given),
                 id="add_columns"),
    pytest.param(lambda **given: admin.move_to_own_folder(saved(), **given),
                 id="move_to_own_folder"),
    pytest.param(lambda **given: admin.check_the_copy(saved(), **given),
                 id="check_the_copy"),
])
def test_send_is_refused_naming_query(make: Callable[..., object]) -> None:
    with pytest.raises(TypeError) as refused:
        make(send=at_work(saved(columns=WIDER)))
    message = str(refused.value)
    assert "was given send=, which Toolbox 7.0 replaced." in message
    assert "Pass query= instead" in message


# --- Each is an ordinary Statement, logged when run -------------------------------------------


def test_each_run_is_logged_in_the_admin_log_and_show_hive_logs_nothing(tmp_path: Path) -> None:
    log = set_admin_log(tmp_path / "admin_log.md")
    t = saved()
    show_hive(admin.drop_partitions(t, where=less_than(t.dt, "2025-01-01")))
    assert not log.exists()
    sent = []
    run_execute(admin.drop_partitions(t, where=less_than(t.dt, "2025-01-01")), sent.append)
    assert sent == ["ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-01-01')"]
    assert ('- Call: `admin.drop_partitions(mart.daily_runs, where=less_than(daily_runs.dt, '
            '"2025-01-01"))`' in log.read_text(encoding="utf-8"))


def test_an_admin_statement_isnt_a_query_to_read_or_split() -> None:
    drop = admin.drop_partitions(region_runs, where=equals(region_runs.region, "EU"))
    with pytest.raises(TypeError, match="derived names a Statement made by statement"):
        derived("dropped", drop)
    assert repr(drop) == "<Statement - print(to_hive(s)) shows it>"
    assert create_table(saved())._admin_call is None


def test_the_notes_and_fixes_that_name_an_admin_function_call_it_as_it_is() -> None:
    """Unchecked statements' notes and check_table_reference's fixes, written before the admin
    module, name its functions: each exists and takes the keywords they write."""
    unchecked, tables = toolbox_module("unchecked"), toolbox_module("tables")
    texts = [call for _, call in unchecked._ALTERED_BY] + [tables.MOVE_IT, tables._SET_IT,
                                                           "admin.drop_table(t)"]
    for text in texts:
        for name, arguments in re.findall(r"admin\.(\w+)\(([^)]*)\)", text):
            assert name in admin.__all__, text
            # **removed only catches the send= that 7.0 replaced, to refuse it.
            parameters = [parameter.name for parameter
                          in inspect.signature(getattr(admin, name)).parameters.values()
                          if parameter.kind is not inspect.Parameter.VAR_KEYWORD]
            written = [part.split("=")[0].strip() for part in arguments.split(",")]
            assert written == parameters, text


def test_a_table_with_no_partitions_isnt_moved_into_a_folder_inside_its_own() -> None:
    whole = saved(columns={"job_id": "bigint"})
    with pytest.raises(ValueError, match="is inside the folder it is in now"):
        admin.move_to_own_folder(whole, query=at_work(
            whole, location="hdfs://namenode:8020/data/your_team"))
    moves = admin.move_to_own_folder(whole, query=at_work(whole, location="/data/elsewhere"))
    assert to_hive(moves[1]) == ("INSERT OVERWRITE TABLE mart.daily_runs_moving\nSELECT\n"
                                 "  daily_runs.job_id\nFROM mart.daily_runs AS daily_runs")


def test_lineage_leaves_admin_statements_out(tmp_path: Path) -> None:
    read = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True))
    export_lineage(read, admin.drop_table(saved()), to=tmp_path / "pipeline.html")
    with pytest.raises(ValueError, match="only Admin statements"):
        export_lineage(admin.drop_table(saved()), to=tmp_path / "admin.html")
