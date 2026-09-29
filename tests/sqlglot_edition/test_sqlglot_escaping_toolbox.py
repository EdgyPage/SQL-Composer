"""The escaping matrix through SQL Composer, where the check needs sqlglot itself.

These read the Hive back with sqlglot's parser, or read SQL Composer's own source to hold that
sqlglot writes every piece of SQL text in one place. The escaping checks every Edition passes
are in `tests/test_escaping_toolbox.py`.
"""

from __future__ import annotations

import ast
import datetime

import pytest
import sqlglot
from sqlglot import exp

from conftest import toolbox_folder
from escaping_cases import INJECTION_PAYLOADS, REFUSED_CONTROL_CHARACTERS, STRING_CASES
from sql_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Table,
    at_least,
    at_most,
    contains,
    count_rows,
    equals,
    less_than,
    more_than,
    not_equals,
    starts_with,
    statement,
    to_hive,
)
from sql_composer.example_database import job_runs

TOOLBOX = toolbox_folder()
# The cases the Toolbox writes; it refuses the rest (tests/test_escaping_toolbox.py).
WRITTEN = [case for case in STRING_CASES if case[0] not in REFUSED_CONTROL_CHARACTERS]
WRITTEN_IDS = [label for label, _value, _expected in WRITTEN]

COMPARISONS = [
    (equals, "="),
    (not_equals, "<>"),
    (at_least, ">="),
    (at_most, "<="),
    (more_than, ">"),
    (less_than, "<"),
]


def _statement_with(condition) -> str:
    return to_hive(statement(
        SELECT(job_runs.run_id),
        FROM(job_runs),
        WHERE(condition, equals(job_runs.dt, "2026-09-24")),
    ))


def _literals(hive: str) -> list[str]:
    """Every string literal's value in a Hive string, read back by sqlglot's Hive parser."""
    statements = [s for s in sqlglot.parse(hive, read="hive") if s]
    assert len(statements) == 1, "a value started a second statement"
    return [node.this for node in statements[0].find_all(exp.Literal) if node.is_string]


@pytest.mark.parametrize(("_label", "value", "_expected"), WRITTEN, ids=WRITTEN_IDS)
@pytest.mark.parametrize("function", [contains, starts_with])
def test_a_like_pattern_keeps_the_value_whole(function, _label, value, _expected) -> None:
    hive = _statement_with(function(job_runs.status, value))
    patterns = [literal for literal in _literals(hive) if literal != "2026-09-24"]
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    assert escaped in patterns[0]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
@pytest.mark.parametrize(("function", "_operator"), COMPARISONS,
                         ids=[f.__name__ for f, _ in COMPARISONS])
def test_an_injection_payload_stays_one_value_in_a_whole_statement(function, _operator,
                                                                    payload) -> None:
    hive = _statement_with(function(job_runs.status, payload))
    assert payload in _literals(hive)
    tree = sqlglot.parse_one(hive, read="hive")
    assert not list(tree.find_all(exp.Or)), "the payload became an OR"


def test_the_partition_of_a_write_is_the_day_the_toolbox_formats() -> None:
    saved = Table("mart.odd", columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
                  date_partition="dt")
    hive = to_hive(statement(
        INSERT_OVERWRITE(saved),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, datetime.date(2026, 9, 24))),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    ))
    assert "PARTITION(dt = '2026-09-24')" in hive
    assert _literals(hive) == ["2026-09-24", "2026-09-24"]


def _toolbox_trees():
    return {path.name: ast.parse(path.read_text(encoding="utf-8"))
            for path in sorted(TOOLBOX.glob("*.py"))}


def test_sql_text_is_written_in_exactly_one_function() -> None:
    callers = []
    for name, tree in _toolbox_trees().items():
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            for call in ast.walk(function):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "sql"):
                    callers.append((name, function.name, call))
    # The import-time behaviour checks in __init__.py call .sql() on sqlglot's own nodes to
    # check sqlglot itself; they write nothing the Toolbox sends.
    writers = [(name, fn) for name, fn, _ in callers if name != "__init__.py"]
    assert writers == [("tables.py", "hive_text")]
    raising = [call for name, fn, call in callers if fn == "hive_text"][0]
    keywords = {k.arg: ast.unparse(k.value) for k in raising.keywords}
    assert keywords["unsupported_level"] == "ErrorLevel.RAISE"


def test_no_sql_text_is_built_with_an_f_string() -> None:
    """No f-string or .format() is handed to sqlglot, so no value can be pasted into SQL."""
    for name, tree in _toolbox_trees().items():
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            target = ast.unparse(call.func)
            if not target.startswith(("exp.", "sqlglot.")):
                continue
            for argument in [*call.args, *(k.value for k in call.keywords)]:
                assert not isinstance(argument, ast.JoinedStr), f"{name}: {ast.unparse(call)}"
                assert not (isinstance(argument, ast.Call)
                            and ast.unparse(argument.func).endswith(".format")), name
