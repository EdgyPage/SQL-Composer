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
from escaping_cases import INJECTION_PAYLOADS, WRITTEN, WRITTEN_IDS
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
    assert [(name, fn) for name, fn, _ in callers] == [("writing.py", "sql_text")]
    raising = callers[0][2]
    keywords = {k.arg: ast.unparse(k.value) for k in raising.keywords}
    assert keywords["unsupported_level"] == "ErrorLevel.RAISE"


def test_only_the_edition_files_read_hive_or_name_its_dialect() -> None:
    """parse_one, ErrorLevel and dialect= are sqlglot's alone: writing.py and engine.py hold them."""
    for name, tree in _toolbox_trees().items():
        if name in ("writing.py", "engine.py"):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword):
                assert node.arg not in ("dialect", "read"), f"{name}: {ast.unparse(node)}"
            if isinstance(node, (ast.Name, ast.Attribute, ast.alias)):
                named = getattr(node, "id", None) or getattr(node, "attr", None) or node.name
                assert named not in ("parse_one", "ErrorLevel"), f"{name}: {named}"
            if isinstance(node, ast.Constant):
                assert node.value != "hive", f"{name} names the hive dialect, line {node.lineno}"


def test_no_sql_text_is_built_with_an_f_string() -> None:
    """No f-string or .format() is handed to sqlglot or a Node, so no value is pasted into SQL."""
    for name, tree in _toolbox_trees().items():
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            target = ast.unparse(call.func)
            if not target.startswith(("exp.", "sqlglot.", "Node", "trees.")):
                continue
            for argument in [*call.args, *(k.value for k in call.keywords)]:
                assert not isinstance(argument, ast.JoinedStr), f"{name}: {ast.unparse(call)}"
                assert not (isinstance(argument, ast.Call)
                            and ast.unparse(argument.func).endswith(".format")), name
