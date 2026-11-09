"""connect in warehouse.py: each notebook gives the Project its connection. 8.6's ticket 01.

Until 8.6, warehouse.py set `conn = example_database` when imported, so a notebook reached
whatever warehouse.py named. Now warehouse.py's connect(connection) sets the one connection its
query and execute pass each Hive string to, and each notebook connects at its top: each runs on
its own, and picks the account it runs as. Called before connect, query and execute refuse with
the Toolbox's four parts; connect refuses an object with no query or no execute.
"""

from __future__ import annotations

import ast
import importlib
import re
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest
from conftest import project_on_the_path, toolbox_module

from sqlglot_composer import example_database, notebooks, project

# The line each Toolbox notebook's setup cell holds for the user to fill in.
PLACEHOLDER = "# connect(your_connection)"
# A refusal's four parts, as the Toolbox writes every one.
FOUR_PARTS = re.compile(r"\n  What happened:  (.*)\n  Why it matters: (.*)"
                        r"\n  Usual fix:      (.*)\n  Opt-out:        (.*)", re.DOTALL)


@pytest.fixture
def warehouse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    """A new Project's warehouse.py, imported as a notebook there imports it."""
    monkeypatch.chdir(tmp_path)
    project.start()
    with project_on_the_path(tmp_path, ("warehouse",)):
        importlib.invalidate_caches()
        yield importlib.import_module("warehouse")


class Recording:
    """A connection that keeps each Hive string it is given, and gives back one row."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def query(self, hive: str) -> pd.DataFrame:
        self.sent.append(("query", hive))
        return pd.DataFrame({"one": [1]})

    def execute(self, hive: str) -> str:
        self.sent.append(("execute", hive))
        return "dropped"


class QueryOnly:
    def query(self, hive: str) -> pd.DataFrame:
        return pd.DataFrame()


class ExecuteOnly:
    def execute(self, hive: str) -> None:
        return None


def parts_of(message: str) -> tuple[str, ...]:
    """A refusal's what, why, fix and opt-out, checked to be written as the Toolbox writes
    them."""
    found = FOUR_PARTS.fullmatch(message)
    assert found, message
    what, why, fix, opt_out = found.groups()
    written = toolbox_module()._four_part_message(what=what, why=why, fix=fix, opt_out=None)
    assert message == written
    return what, why, fix, opt_out


def test_warehouse_py_holds_connect_query_and_execute(warehouse: ModuleType) -> None:
    text = Path(warehouse.__file__).read_text(encoding="utf-8")
    assert text == project.WAREHOUSE_TEXT
    defined = {node.name: node for node in ast.parse(text).body
               if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")}
    assert sorted(defined) == ["connect", "execute", "query"]
    assert ast.unparse(defined["connect"].returns) == "None"
    assert ast.unparse(defined["query"].returns) == "pd.DataFrame"
    assert ast.unparse(defined["execute"].returns) == "None"
    assert "conn = " not in text and "example_database" not in text.split('"""')[2]


def test_query_and_execute_pass_each_hive_string_to_the_connection(
        warehouse: ModuleType) -> None:
    connection = Recording()
    warehouse.connect(connection)
    assert list(warehouse.query("SELECT 1 AS one")["one"]) == [1]
    assert warehouse.execute("DROP TABLE mart.gone") is None  # what it gives back is dropped
    assert connection.sent == [("query", "SELECT 1 AS one"),
                               ("execute", "DROP TABLE mart.gone")]


def test_connect_again_replaces_the_connection(warehouse: ModuleType) -> None:
    first, second = Recording(), Recording()
    warehouse.connect(first)
    warehouse.connect(second)
    warehouse.query("SELECT 1 AS one")
    assert first.sent == [] and len(second.sent) == 1


def test_the_example_database_is_a_connection(warehouse: ModuleType) -> None:
    warehouse.connect(example_database)
    assert list(warehouse.query("SELECT 1 AS one")["one"]) == [1]


@pytest.mark.parametrize("call", ["query", "execute"])
def test_before_connect_each_call_refuses(warehouse: ModuleType, call: str) -> None:
    with pytest.raises(RuntimeError) as refused:
        getattr(warehouse, call)("SELECT 1 AS one")
    what, why, fix, opt_out = parts_of(str(refused.value))
    assert what.startswith("No connection: call connect(...) first.")
    assert f"{call}(...)" in what
    assert "Each notebook runs on its own" in why
    assert "setup cell" in fix and "connect(example_database)" in fix
    assert opt_out == "none - this one can't be switched off."


@pytest.mark.parametrize(("given", "missing"), [
    (QueryOnly(), "execute(sql)"), (ExecuteOnly(), "query(sql)"),
    (None, "query(sql) or execute(sql)"), ("text", "query(sql) or execute(sql)")])
def test_connect_refuses_a_connection_lacking_a_call(warehouse: ModuleType, given: object,
                                                     missing: str) -> None:
    with pytest.raises(TypeError) as refused:
        warehouse.connect(given)
    what, _, fix, _ = parts_of(str(refused.value))
    # Each call it lacks is named, both when it lacks both.
    assert f"has no {missing} to call" in what
    assert type(given).__name__ in what
    assert "connect(example_database)" in fix
    assert "functions in your Project's warehouse.py" in fix
    # Nothing was connected: query still refuses.
    with pytest.raises(RuntimeError, match="No connection"):
        warehouse.query("SELECT 1 AS one")


def test_warehouse_py_imports_nothing_of_the_project(warehouse: ModuleType) -> None:
    tree = ast.parse(Path(warehouse.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
    # Not even the Toolbox: it is the user's own file, which any script of theirs can import.
    assert imported == {"typing", "pandas"}


def warehouse_notebooks(root: Path) -> list[Path]:
    """Each notebook start() wrote that imports from warehouse."""
    return [path for path in sorted(root.rglob("*.ipynb"))
            if "from warehouse import" in path.read_text(encoding="utf-8")]


def test_each_notebook_that_reaches_the_warehouse_connects_at_its_top(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    project.start()
    found = warehouse_notebooks(tmp_path)
    assert {path.stem for path in found} >= {
        "check_references", "run_tables", "convert", "promote", "new_table", "references",
        "change_a_saved_table", "upgrade"}
    for path in found:
        code = [text for kind, text in notebooks.read_cells(path) if kind == "code"]
        connecting = [text for text in code if "from warehouse import" in text][0]
        assert "connect" in connecting.split("from warehouse import")[1].split("\n")[0], path
        assert PLACEHOLDER in connecting.split("\n"), path
        assert "team_connection" in connecting, path
        # The cell connecting is before any other cell that reaches the warehouse.
        assert code.index(connecting) <= 2, path


def test_each_table_notebook_template_connects_at_its_top() -> None:
    templates = toolbox_module("project_templates")
    for name, text in templates.TEMPLATES.items():
        if "# %%" not in text:
            continue
        first = text.split("# %%\n")[1]
        assert "from warehouse import connect, query" in first, name
        assert PLACEHOLDER in first.split("\n"), name


def test_start_says_to_connect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    said = repr(project.start())
    assert said.split("\n")[-1].startswith("Next: ")
    assert "connect(...)" in said.split("\n")[-1]
    assert "conn," not in said
