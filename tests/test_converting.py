"""Reading someone else's Hive as the Toolbox's own Python: Toolbox 7.2's ticket 05.

converting.translate reads one Hive query with sqlglot and writes the Python that builds it
again from Clause functions. What no Toolbox function writes stays Hive at the smallest size it
can be (ADR 0014). These tests read the Python it writes; tests/test_conversions.py runs it.
"""

from __future__ import annotations

import pytest
from conftest import toolbox_module

converting = toolbox_module("converting")

# The Example database's tables a Conversion reads in these tests, with their columns.
COLUMNS = {
    "ops.job_runs": ["run_id", "job_id", "dt", "status", "duration_mins"],
    "ops.jobs": ["job_id", "job_name", "team"],
}


def translate(hive: str) -> converting.Translation:
    return converting.translate(hive, COLUMNS.get, database="ops")


def found(translation: converting.Translation, kind: str) -> list[str]:
    return [str(one) for one in translation.findings if one.kind == kind]


# --- What it reads ---------------------------------------------------------------------------


def test_a_query_becomes_a_statement_of_clause_functions() -> None:
    done = translate("SELECT r.job_id, r.status FROM ops.job_runs r "
                     "WHERE r.dt = '2026-09-24' ORDER BY r.job_id DESC LIMIT 5")
    assert done.assignments == [("r", 'AS(ops.job_runs, "r")')]
    assert done.query == (
        "statement(\n"
        "    SELECT(\n        r.job_id,\n        r.status,\n    ),\n"
        "    FROM(r),\n"
        '    WHERE(equals(r.dt, "2026-09-24")),\n'
        "    ORDER_BY(descending(r.job_id)),\n"
        "    LIMIT(5),\n"
        ")")
    assert done.tables == ["ops.job_runs"]
    assert done.databases == {"ops"}


def test_a_table_read_under_its_own_name_needs_no_alias() -> None:
    assert translate("SELECT job_runs.job_id FROM ops.job_runs").assignments == [
        ("job_runs", "ops.job_runs")]


def test_a_table_named_without_its_database_is_in_the_one_given() -> None:
    assert translate("SELECT job_id FROM job_runs").tables == ["ops.job_runs"]


def test_a_column_named_without_its_table_is_found_by_its_name() -> None:
    done = translate("SELECT job_name, status FROM ops.job_runs r JOIN ops.jobs j "
                     "ON r.job_id = j.job_id")
    assert "j.job_name" in done.query and "r.status" in done.query


def test_a_cte_is_a_derived_table() -> None:
    done = translate("WITH failed AS (SELECT job_id FROM ops.job_runs WHERE status = 'FAILED') "
                     "SELECT f.job_id FROM failed f")
    assert done.assignments[1] == ("failed", 'derived("failed", statement(\n'
                                   "    SELECT(job_runs.job_id),\n    FROM(job_runs),\n"
                                   '    WHERE(equals(job_runs.status, "FAILED")),\n))')
    assert done.assignments[2] == ("f", 'AS(failed, "f")')


def test_a_long_in_list_is_a_named_constant() -> None:
    done = translate("SELECT run_id FROM ops.job_runs WHERE status IN ('A', 'B', 'C', 'D')")
    assert done.constants == [("STATUS_VALUES", '["A", "B", "C", "D"]')]
    assert "is_in(job_runs.status, STATUS_VALUES)" in done.query
    assert found(done, "constant") == [
        "line 1: the IN list of 4 values is the constant STATUS_VALUES"]


def test_a_short_in_list_stays_where_it_is() -> None:
    done = translate("SELECT run_id FROM ops.job_runs WHERE status IN ('A', 'B')")
    assert 'is_in(job_runs.status, ["A", "B"])' in done.query and not done.constants


def test_a_lookup_case_is_mapped_from_a_named_dict() -> None:
    done = translate("SELECT CASE job_id WHEN 1 THEN 'one' WHEN 2 THEN 'two' ELSE 'many' END "
                     "AS label FROM ops.job_runs")
    assert done.constants == [("LABEL_BY_JOB_ID", '{\n    1: "one",\n    2: "two",\n}')]
    assert 'AS(mapped(job_runs.job_id, LABEL_BY_JOB_ID, otherwise="many"), "label")' in done.query


def test_a_case_comparing_one_column_with_values_is_mapped_too() -> None:
    done = translate("SELECT CASE WHEN status = 'F' THEN 1 WHEN status = 'O' THEN 0 END AS x "
                     "FROM ops.job_runs")
    assert "mapped(job_runs.status, X_BY_STATUS)" in done.query


def test_an_if_else_chain_is_first_match() -> None:
    done = translate("SELECT CASE WHEN duration_mins > 60 THEN 'long' "
                     "WHEN status = 'FAILED' THEN 'failed' ELSE 'ok' END AS kind "
                     "FROM ops.job_runs")
    assert ('first_match([ (more_than(job_runs.duration_mins, 60), "long"), '
            '(equals(job_runs.status, "FAILED"), "failed"), ], otherwise="ok")'
            in " ".join(done.query.split()))


def test_one_when_is_if_else() -> None:
    done = translate("SELECT CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END AS f "
                     "FROM ops.job_runs")
    assert 'if_else(equals(job_runs.status, "FAILED"), 1, 0)' in done.query


def test_a_sum_over_one_when_with_no_else_is_its_where() -> None:
    done = translate("SELECT SUM(CASE WHEN status = 'FAILED' THEN duration_mins END) AS m "
                     "FROM ops.job_runs")
    assert 'sum_of(job_runs.duration_mins, where=equals(job_runs.status, "FAILED"))' in done.query


def test_a_hive_function_is_kept_as_hive_function_when_it_writes_back_the_same() -> None:
    done = translate("SELECT regexp_extract(status, 'F(A)', 1) AS f FROM ops.job_runs")
    assert 'hive_function("regexp_extract", job_runs.status, "F(A)", 1)' in done.query
    assert not found(done, "unchecked")


def test_a_comparison_written_value_first_is_turned_round() -> None:
    assert ("less_than(job_runs.duration_mins, 60)"
            in translate("SELECT run_id FROM ops.job_runs WHERE 60 > duration_mins").query)


def test_like_becomes_starts_with_or_contains() -> None:
    done = translate("SELECT run_id FROM ops.job_runs WHERE status LIKE 'F%' "
                     "AND status LIKE '%AIL%'")
    assert 'starts_with(job_runs.status, "F")' in done.query
    assert 'contains(job_runs.status, "AIL")' in done.query


def test_a_window_function_is_the_toolboxs_own() -> None:
    done = translate("SELECT ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY dt DESC) AS n, "
                     "LAG(duration_mins, 2) OVER (PARTITION BY job_id ORDER BY dt) AS before "
                     "FROM ops.job_runs")
    assert ("row_number(over=window(PARTITION_BY=[job_runs.job_id], "
            "ORDER_BY=[descending(job_runs.dt)]))") in done.query
    assert ("lag(job_runs.duration_mins, over=window(PARTITION_BY=[job_runs.job_id], "
            "ORDER_BY=[job_runs.dt]), back=2)") in done.query


def test_union_all_is_a_stack() -> None:
    done = translate("SELECT job_id FROM ops.jobs UNION ALL SELECT job_id FROM ops.job_runs")
    assert done.query.startswith("UNION_ALL(\n    statement(")


def test_set_lines_are_session_settings() -> None:
    done = translate("SET hive.exec.parallel=true;\nSELECT job_id FROM ops.jobs")
    assert done.settings == {"hive.exec.parallel": "true"}
    assert done.constants[0][0] == "HIVE_SETTINGS"


def test_a_table_with_no_table_reference_is_a_finding_not_a_refusal() -> None:
    done = translate("SELECT a FROM ops.elsewhere")
    assert done.missing == ["ops.elsewhere"]
    assert found(done, "table") == ["line 1: ops.elsewhere has no Table reference yet"]


# --- What stays Hive ---------------------------------------------------------------------------


def test_an_expression_no_function_writes_is_an_unchecked_column() -> None:
    done = translate("SELECT CAST(duration_mins AS INT) AS mins FROM ops.job_runs")
    assert ('AS(unchecked_column("CAST({duration_mins} AS INT)", '
            'duration_mins=job_runs.duration_mins), "mins")') in done.query
    assert found(done, "unchecked")[0].startswith("line 1: CAST(duration_mins AS INT) stays Hive")


def test_a_brace_in_kept_hive_is_doubled_so_only_placeholders_are_filled() -> None:
    done = translate("SELECT CAST(regexp_extract(status, 'A{2}') AS INT) AS x FROM ops.job_runs")
    assert "'A{{2}}'" in done.query and "{status}" in done.query


def test_a_condition_no_function_writes_is_an_unchecked_condition() -> None:
    done = translate("SELECT run_id FROM ops.job_runs WHERE status RLIKE '^F'")
    assert ('WHERE(unchecked_condition("{status} RLIKE \'^F\'", status=job_runs.status))'
            in done.query)


def test_a_cte_no_statement_can_be_is_an_unchecked_derived_table() -> None:
    done = translate("WITH e AS (SELECT job_id, x FROM ops.jobs LATERAL VIEW "
                     "explode(array(1, 2)) t AS x) SELECT e.job_id FROM e")
    name, value = done.assignments[0]
    assert name == "e" and value.startswith('unchecked_derived("e", ')
    assert value.endswith('columns={\n    "job_id": None,\n    "x": None,\n})')
    assert "the CTE e stays Hive: LATERAL VIEW" in found(done, "unchecked")[0]


def test_a_query_the_toolbox_cant_read_is_one_unchecked_statement() -> None:
    done = translate("SELECT job_id, x FROM ops.jobs LATERAL VIEW explode(array(1, 2)) t AS x")
    assert done.query.startswith('unchecked_hive("SELECT')
    assert "the whole query stays an Unchecked statement" in found(done, "unchecked")[0]


# --- INSERT, every form ------------------------------------------------------------------------


@pytest.mark.parametrize(("hive", "write"), [
    ("INSERT INTO TABLE mart.t SELECT run_id FROM ops.job_runs", "INSERT_INTO"),
    ("INSERT INTO mart.t SELECT run_id FROM ops.job_runs", "INSERT_INTO"),
    ("INSERT OVERWRITE TABLE mart.t SELECT run_id FROM ops.job_runs", "INSERT_OVERWRITE"),
    ("INSERT OVERWRITE mart.t SELECT run_id FROM ops.job_runs", "INSERT_OVERWRITE"),
])
def test_each_insert_keeps_its_query_and_how_it_wrote(hive: str, write: str) -> None:
    done = translate(hive)
    assert done.write == write and done.written_table == "mart.t"
    assert done.query.startswith("statement(")
    assert found(done, "dropped")[0].startswith(f"line 1: its {write.replace('_', ' ')} mart.t")


def test_an_inserts_partition_keeps_its_columns_and_values() -> None:
    done = translate("INSERT OVERWRITE TABLE mart.t PARTITION (dt='2026-09-24', status) "
                     "SELECT run_id, status FROM ops.job_runs")
    assert done.partition_columns == ["dt", "status"]
    assert done.static_partition == {"dt": '"2026-09-24"'}


def test_an_inserts_column_list_names_the_selects_columns() -> None:
    done = translate("INSERT INTO mart.t (a, b) SELECT run_id, job_id FROM ops.job_runs")
    assert done.insert_columns == ["a", "b"]
    assert 'AS(job_runs.run_id, "a")' in done.query and 'AS(job_runs.job_id, "b")' in done.query


def test_a_with_before_insert_is_read() -> None:
    done = translate("WITH c AS (SELECT run_id FROM ops.job_runs) "
                     "INSERT OVERWRITE TABLE mart.t SELECT c.run_id FROM c")
    assert [name for name, _ in done.assignments][:2] == ["job_runs", "c"]


@pytest.mark.parametrize(("hive", "said"), [
    ("INSERT INTO TABLE mart.t VALUES (1, 'a')", "its INSERT writes VALUES, not a query"),
    ("INSERT OVERWRITE DIRECTORY '/tmp/x' SELECT run_id FROM ops.job_runs",
     "it writes files into DIRECTORY '/tmp/x', not a table"),
    ("FROM ops.job_runs INSERT OVERWRITE TABLE mart.a SELECT run_id "
     "INSERT INTO TABLE mart.b SELECT job_id", "it is one FROM with 2 INSERTs, into mart.a, mart.b"),
    ("SELECT 1 FROM ops.jobs; SELECT 2 FROM ops.jobs", "it holds 2 statements"),
    ("INSERT INTO mart.t (a, b) SELECT run_id FROM ops.job_runs",
     "its INSERT lists the columns a, b, and its query doesn't give one column for each"),
])
def test_what_a_conversion_cant_take_is_refused_saying_what_to_do(hive: str, said: str) -> None:
    with pytest.raises(converting.ConversionRefused, match="^" + said.replace("(", r"\(")
                       .replace(")", r"\)")):
        translate(hive)


# --- Opt-outs, from a refusal ----------------------------------------------------------------------

LOGIC = ('x = derived("x", statement(\n    SELECT(r.a),\n    FROM(r),\n))\n'
         'y = statement(\n    SELECT(AS(sum_of(p.fails), "f")),\n    FROM(p),\n'
         '    JOIN(j, ON=equals(p.job_id, j.job_id)),\n    ORDER_BY("f"),\n)\n')


@pytest.mark.parametrize(("refusal", "added", "line"), [
    ("Opt-out:        FROM(r, reads_all_partitions=True)", "FROM(r, reads_all_partitions=True)",
     "    FROM(r, reads_all_partitions=True),"),
    ("Opt-out:        JOIN(j, ON=..., many_matches=True)", "JOIN(j, many_matches=True)",
     "    JOIN(j, ON=equals(p.job_id, j.job_id), many_matches=True),"),
    ("Opt-out:        sum_of(p.fails, adds_up=True)", "sum_of(p.fails, adds_up=True)",
     '    SELECT(AS(sum_of(p.fails, adds_up=True), "f")),'),
    ("Opt-out:        ORDER_BY(..., sorts_everything=True), but not in a Statement",
     "ORDER_BY(..., sorts_everything=True)", '    ORDER_BY("f", sorts_everything=True),'),
])
def test_an_opt_out_goes_on_the_call_its_refusal_names_marked(refusal: str, added: str,
                                                               line: str) -> None:
    logic, said = converting.with_opt_out(LOGIC, refusal)
    assert said == added
    lines = logic.splitlines()
    at = lines.index(line)
    keyword = added.split(", ")[-1].split("=")[0]
    assert lines[at - 1] == ("    " + converting.CONVERSION_MARK.format(keyword=keyword))


def test_an_opt_out_already_there_or_named_by_no_refusal_is_none() -> None:
    logic, _ = converting.with_opt_out(LOGIC, "Opt-out:        FROM(r, reads_all_partitions=True)")
    assert converting.with_opt_out(logic, "Opt-out:        FROM(r, reads_all_partitions=True)") \
        is None
    assert converting.with_opt_out(LOGIC, "Opt-out:        none - it can't be switched off.") is None
