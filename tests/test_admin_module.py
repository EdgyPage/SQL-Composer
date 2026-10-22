"""The admin module: changes to the user's own Saved tables, written and checked for them.

Map family 4 and ADR 0006. `from sqlglot_composer import admin` (the star import leaves it
out) gives drop_table, drop_days, add_columns, set_properties and move_to_own_folder. Each makes
an ordinary Statement, or for the move a list of them, which run sends like any other and logs
in the Admin log; show_hive prints what it changes, what can't be undone and what to check
first, ahead of its Hive; and each refuses a table that isn't one of the user's Saved tables. The
golden corpus pins every one's Hive and notes (the `edge:admin:*` cases).
"""

from __future__ import annotations

import datetime
import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module
from hive_corpus_cases import BASE, warehouse

import sqlglot_composer
from sqlglot_composer import (
    FROM,
    SELECT,
    Statement,
    Table,
    admin,
    create_table,
    derived,
    example_database,
    export_lineage,
    run,
    set_admin_log,
    show_hive,
    statement,
    to_hive,
)

job_runs = example_database.job_runs


def saved(name: str = "mart.daily_runs", columns: dict[str, str | None] | None = None,
          date_partition: str | None = "dt", **storage: object) -> Table:
    """One of the user's Saved tables."""
    columns = columns or {"job_id": "bigint", "runs": "bigint", "dt": "string"}
    return Table(name, columns=columns, date_partition=date_partition, location=BASE,
                 **storage)


# --- Where it is ---------------------------------------------------------------------------


def test_admin_is_imported_by_name_and_the_star_import_leaves_it_out() -> None:
    assert "admin" not in sqlglot_composer.__all__
    assert "drop_table" not in sqlglot_composer.__all__
    assert not hasattr(sqlglot_composer, "drop_table")
    assert admin.__all__ == ["drop_table", "drop_days", "add_columns", "set_properties",
                             "move_to_own_folder"]


# --- Each refuses a table that isn't one of the user's Saved tables ------------------------


def _refusing(call: str) -> Callable[[object], Statement | list[Statement]]:
    return {
        "drop_table": lambda t: admin.drop_table(t),
        "drop_days": lambda t: admin.drop_days(t, before="2025-01-01"),
        "add_columns": lambda t: admin.add_columns(t, query=warehouse(saved())),
        "set_properties": lambda t: admin.set_properties(t),
        "move_to_own_folder": lambda t: admin.move_to_own_folder(t, query=warehouse(saved())),
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
    with pytest.raises(ValueError, match=r"repair_partitions\(\.\.\.\) was given ops\.job_runs"):
        need(job_runs, "repair_partitions(...)")


# --- drop_table and drop_days ------------------------------------------------------------------


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
    assert "files stay in the table's folder, /data/your_team/tables/mart/daily_runs" in notes


@pytest.mark.parametrize("before", ["2025-01-01", datetime.date(2025, 1, 1)])
def test_drop_days_drops_every_day_before_one(before: str | datetime.date) -> None:
    assert to_hive(admin.drop_days(saved(), before=before)) == (
        "ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-01-01')")


def test_drop_days_writes_the_day_as_the_table_writes_days() -> None:
    compact = saved(date_format="%Y%m%d")
    assert to_hive(admin.drop_days(compact, before=datetime.date(2025, 1, 1))).endswith(
        "PARTITION (dt < '20250101')")
    with pytest.raises(ValueError, match="writes days like '20250101'"):
        admin.drop_days(compact, before="2025-01-01")


def test_drop_days_refuses_a_table_with_no_date_partition() -> None:
    with pytest.raises(ValueError, match="has no Date partition") as refused:
        admin.drop_days(saved(columns={"job_id": "bigint"}, date_partition=None),
                        before="2025-01-01")
    # Its fix names the write that replaces such a table whole.
    assert "INSERT_OVERWRITE(daily_runs)" in str(refused.value)


# --- add_columns -------------------------------------------------------------------------------

WIDER = {"job_id": "bigint", "runs": "bigint", "fails": "bigint", "note": "string",
         "dt": "string"}


def test_add_columns_adds_what_the_table_lacks_with_cascade() -> None:
    t = saved(columns=WIDER)
    assert to_hive(admin.add_columns(t, query=warehouse(t, lacking=("fails", "note")))) == (
        "ALTER TABLE mart.daily_runs ADD COLUMNS (\n  fails BIGINT,\n  note STRING\n) CASCADE")


def test_add_columns_sends_describe_and_writes_no_cascade_without_days() -> None:
    sent = []
    t = saved(columns={"job_id": "bigint", "note": "string"}, date_partition=None)
    answer = warehouse(t, lacking=("note",))
    adding = admin.add_columns(t, query=lambda hive: sent.append(hive) or answer(hive))
    assert sent == ["DESCRIBE mart.daily_runs"]
    assert to_hive(adding) == "ALTER TABLE mart.daily_runs ADD COLUMNS (\n  note STRING\n)"


@pytest.mark.parametrize("lacking, refusal", [
    ((), "has every column of its Table reference already"),
    (("fails",), "lists fails before note, which the table has already"),
])
def test_add_columns_refuses_what_it_cant_add(lacking: tuple[str, ...], refusal: str) -> None:
    t = saved(columns=WIDER)
    with pytest.raises(ValueError, match=refusal):
        admin.add_columns(t, query=warehouse(t, lacking=lacking))


def test_add_columns_refuses_a_new_partition_and_a_column_with_no_type() -> None:
    region = saved(columns={"job_id": "bigint", "region": "string", "dt": "string"},
                   partitioned_by=["region"])
    with pytest.raises(ValueError, match="region is a Partition in the Table reference"):
        admin.add_columns(region, query=warehouse(region, lacking=("region",)))
    untyped = saved(columns={"job_id": "bigint", "fails": None, "dt": "string"})
    with pytest.raises(ValueError, match="fails has no type"):
        admin.add_columns(untyped, query=warehouse(untyped, lacking=("fails",)))
    odd = saved(columns={"job_id": "bigint", "fails": "integer", "dt": "string"})
    with pytest.raises(ValueError, match=r"admin\.add_columns\(mart\.daily_runs, query=\.\.\.\): "
                                         "fails's type 'integer'"):
        admin.add_columns(odd, query=warehouse(odd, lacking=("fails",)))


# --- set_properties ----------------------------------------------------------------------------


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


# --- move_to_own_folder ------------------------------------------------------------------------


def test_the_move_creates_copies_compares_keeps_files_drops_and_renames() -> None:
    t = saved(key=["job_id"])
    moves = admin.move_to_own_folder(t, query=warehouse(t, days=("2026-09-23", "2026-09-24")))
    hives = [to_hive(step) for step in moves]
    assert hives[0].startswith("CREATE EXTERNAL TABLE IF NOT EXISTS mart.daily_runs_moving (")
    assert "LOCATION '/data/your_team/tables/mart/daily_runs'" in hives[0]
    assert hives[1].startswith("INSERT OVERWRITE TABLE mart.daily_runs_moving "
                               "PARTITION(dt = '2026-09-23')")
    assert hives[2].endswith("daily_runs.dt = '2026-09-24'")
    assert hives[3].startswith("WITH old_days AS (")
    assert hives[4] == ("ALTER TABLE mart.daily_runs SET TBLPROPERTIES (\n"
                        "  'external.table.purge'='false'\n)")
    assert hives[5] == "DROP TABLE IF EXISTS mart.daily_runs"
    assert hives[6] == "ALTER TABLE mart.daily_runs_moving RENAME TO mart.daily_runs"
    assert [step._admin_call for step in moves] == [
        f"admin.move_to_own_folder(mart.daily_runs, query=...)[{n}]" for n in range(7)]


def test_a_managed_table_is_moved_without_setting_purge() -> None:
    t = saved()
    moves = admin.move_to_own_folder(t, query=warehouse(
        t, location="hdfs://namenode:8020/warehouse/mart.db/daily_runs", kind="MANAGED_TABLE"))
    assert not any("TBLPROPERTIES" in to_hive(step) for step in moves)
    assert "its files go too, since it is managed" in moves[-2]._admin_about[0]


def test_rows_with_no_day_are_said_not_to_be_copied() -> None:
    t = saved()
    moves = admin.move_to_own_folder(t, query=warehouse(
        t, days=("2026-09-24", "__HIVE_DEFAULT_PARTITION__")))
    assert len(moves) == 6
    assert any("aren't copied" in item for item in moves[0]._admin_about)


@pytest.mark.parametrize("answer, refusal", [
    ({"location": f"{BASE}/mart/daily_runs"}, "is at its own folder already"),
    ({"lacking": ("runs",)}, "has no column runs, which its Table reference lists"),
])
def test_the_move_refuses_a_table_it_cant_or_neednt_move(
        answer: dict[str, str | tuple[str, ...]], refusal: str) -> None:
    t = saved()
    with pytest.raises(ValueError, match=refusal):
        admin.move_to_own_folder(t, query=warehouse(t, **answer))


def test_the_comparison_stops_the_move_and_logs_it_when_a_day_differs(tmp_path: Path) -> None:
    log = set_admin_log(tmp_path / "admin_log.md")
    t = saved()
    moves = admin.move_to_own_folder(t, query=warehouse(t))
    compare = moves[2]
    differ = pd.DataFrame({"dt": ["2026-09-24"], "old_rows": [3], "copied_rows": [2]})
    with pytest.raises(ValueError, match="The move of mart.daily_runs stopped"):
        run(compare, query=lambda hive: differ)
    assert run(compare, query=lambda hive: differ.iloc[0:0]).empty
    text = log.read_text(encoding="utf-8")
    assert "- Call: `admin.move_to_own_folder(mart.daily_runs, query=...)[2]`" in text
    assert "- Result: failed, with ValueError:" in text
    assert text.count("- Result: worked") == 1


# --- Which of the user's calls each step goes to ------------------------------------------------


def recording() -> tuple[Callable[[str], pd.DataFrame], Callable[[str], None],
                         list[tuple[str, str]]]:
    """A query and an execute that keep each Hive they are given, with which of them it went
    to: the query gives back the comparison's columns with no row, a day that differs."""
    sent = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(("query", hive))
        return pd.DataFrame({"dt": [], "old_rows": [], "copied_rows": []})

    def execute(hive: str) -> None:
        sent.append(("execute", hive))

    return query, execute, sent


def test_the_moves_comparison_reads_through_query_and_the_rest_go_to_execute() -> None:
    t = saved()
    query, execute, sent = recording()
    moves = admin.move_to_own_folder(t, query=warehouse(t))
    for step in moves:
        run(step, query=query, execute=execute)
    assert [call for call, _ in sent] == ["execute", "execute", "query", "execute", "execute",
                                          "execute"]
    assert [hive for _, hive in sent] == [to_hive(step) for step in moves]


@pytest.mark.parametrize("make", [
    pytest.param(lambda: admin.drop_table(saved()), id="drop_table"),
    pytest.param(lambda: admin.drop_days(saved(), before="2025-01-01"), id="drop_days"),
    pytest.param(lambda: admin.set_properties(saved(purge=True)), id="set_properties"),
])
def test_an_admin_statement_goes_to_execute_and_gives_back_none(
        make: Callable[[], Statement]) -> None:
    query, execute, sent = recording()
    assert run(make(), query=query, execute=execute) is None
    assert sent == [("execute", to_hive(make()))]


def test_an_admin_statement_without_the_call_it_needs_is_refused_naming_it() -> None:
    query, execute, sent = recording()
    with pytest.raises(TypeError, match=r"run needs execute=, and wasn't given it\."):
        run(admin.drop_table(saved()), query=query)
    compare = admin.move_to_own_folder(saved(), query=warehouse(saved()))[2]
    with pytest.raises(TypeError, match=r"run needs query=, and wasn't given it\."):
        run(compare, execute=execute)
    assert sent == []


@pytest.mark.parametrize("make", [
    pytest.param(lambda **given: admin.add_columns(saved(columns=WIDER), **given),
                 id="add_columns"),
    pytest.param(lambda **given: admin.move_to_own_folder(saved(), **given),
                 id="move_to_own_folder"),
])
def test_send_is_refused_naming_query(make: Callable[..., object]) -> None:
    with pytest.raises(TypeError) as refused:
        make(send=warehouse(saved(columns=WIDER)))
    message = str(refused.value)
    assert "was given send=, which Toolbox 7.0 replaced." in message
    assert "Pass query= instead" in message


# --- Each is an ordinary Statement, logged when run --------------------------------------------


def test_each_run_is_logged_in_the_admin_log_and_show_hive_logs_nothing(tmp_path: Path) -> None:
    log = set_admin_log(tmp_path / "admin_log.md")
    t = saved()
    show_hive(admin.drop_days(t, before="2025-01-01"))
    assert not log.exists()
    sent = []
    run(admin.drop_days(t, before="2025-01-01"), execute=sent.append)
    assert sent == ["ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-01-01')"]
    assert ('- Call: `admin.drop_days(mart.daily_runs, before="2025-01-01")`'
            in log.read_text(encoding="utf-8"))


def test_an_admin_statement_isnt_a_query_to_read_or_split() -> None:
    drop = admin.drop_days(saved(), before="2025-01-01")
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


def test_a_table_with_no_days_isnt_moved_into_a_folder_inside_its_own() -> None:
    whole = saved(columns={"job_id": "bigint"}, date_partition=None)
    with pytest.raises(ValueError, match="is inside the folder it is in now"):
        admin.move_to_own_folder(whole, query=warehouse(whole))
    moves = admin.move_to_own_folder(whole, query=warehouse(whole, location="/data/elsewhere"))
    assert to_hive(moves[1]) == ("INSERT OVERWRITE TABLE mart.daily_runs_moving\nSELECT\n"
                                 "  daily_runs.job_id\nFROM mart.daily_runs AS daily_runs")


def test_lineage_leaves_admin_statements_out(tmp_path: Path) -> None:
    read = statement(SELECT(job_runs.run_id), FROM(job_runs, reads_all_partitions=True))
    export_lineage(read, admin.drop_table(saved()), to=tmp_path / "pipeline.html")
    with pytest.raises(ValueError, match="only Admin statements"):
        export_lineage(admin.drop_table(saved()), to=tmp_path / "admin.html")
