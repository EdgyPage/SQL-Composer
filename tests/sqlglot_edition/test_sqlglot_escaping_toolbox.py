"""Where SQL Composer writes SQL text: in one function of writing.py, never from an f-string.

These read SQL Composer's own source to hold that sqlglot writes every piece of SQL text in one
place, and that nothing but writing.py and engine.py speaks sqlglot. The escaping checks every
Edition passes, reading the Hive back by its characters, are in `tests/test_escaping_toolbox.py`.
"""

from __future__ import annotations

import ast

from conftest import toolbox_folder

TOOLBOX = toolbox_folder()


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
