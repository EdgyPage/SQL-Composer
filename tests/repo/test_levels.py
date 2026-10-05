"""The Levels of the user's own scripts, checked on the Worked examples in `worked_examples/`.

A script imports only from lower Levels and from the Toolbox, never from a higher or equal
Level. Level 0 is `table_references/`, Level 1 `building_blocks/` and Level 2 `statements/`.
Most Worked examples read the Example database's Table references, inside the Toolbox;
`table_references/` holds the Table reference of the Saved table they write. Besides the Levels,
a script may import the standard library, what both Editions of the Toolbox may import (pandas
and numpy, from `tools/editions.py`), and the Toolbox only from its top level, as
`from sql_composer import ...`.

Each Statement script's module docstring gives a title and one sentence on why, which the
Example gallery shows.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from editions import SHARED_IMPORTS

ROOT = Path(__file__).resolve().parents[2]
WORKED_EXAMPLES = ROOT / "worked_examples"
LEVELS = {"table_references": 0, "building_blocks": 1, "statements": 2}
# The seven demonstrations decided in "What does the Example database demonstrate?".
DEMONSTRATIONS = [
    "repeated_rows", "regrouping", "left_join_then_where", "none_in_equals", "nan_in_a_list",
    "not_equals_drops_null", "latest_and_top_n",
]
PANDAS_LABEL = "computed in pandas, not by running this Hive"


def scripts(folder: str) -> list[Path]:
    return sorted((WORKED_EXAMPLES / folder).glob("*.py"))


def every_script() -> list[Path]:
    return [path for folder in LEVELS for path in scripts(folder)]


def _imported(node: ast.AST) -> list[str] | None:
    """The module names an import statement reads, or None if it isn't one."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return ["." * node.level + (node.module or "")]
    return None


def _problem(name: str, level: int) -> str | None:
    top = name.split(".")[0]
    if name.startswith("."):
        return f"{name} is a relative import; name the Level folder instead"
    if top == "sql_composer":
        return None if name == "sql_composer" else f"{name} reaches inside the Toolbox"
    if top == "composer_core":
        return f"{name} reaches inside the Toolbox: import from the Edition's folder"
    if top in LEVELS:
        if LEVELS[top] < level:
            return None
        return f"{name} is Level {LEVELS[top]}, not below Level {level}"
    if top in sys.stdlib_module_names or top in SHARED_IMPORTS or top == "__future__":
        return None
    return f"{name} is neither a lower Level, the Toolbox, nor something both Editions may import"


def level_problems(source: str, level: int) -> list[str]:
    """Every import in a Level `level` script that breaks the Levels rule."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        for name in _imported(node) or []:
            problem = _problem(name, level)
            if problem:
                problems.append(f"line {node.lineno}: {problem}")
    return problems


def test_the_worked_examples_have_building_blocks_and_statements() -> None:
    assert scripts("building_blocks"), "worked_examples/building_blocks/ has no script"
    names = {path.stem for path in scripts("statements")}
    assert set(DEMONSTRATIONS) <= names, set(DEMONSTRATIONS) - names


@pytest.mark.parametrize("path", every_script(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_imports_point_only_downward(path: Path) -> None:
    level = LEVELS[path.parent.name]
    assert level_problems(path.read_text(encoding="utf-8"), level) == []


@pytest.mark.parametrize(
    ("source", "level", "problem"),
    [
        ("from statements.repeated_rows import fixed", 1, "Level 2, not below Level 1"),
        ("from building_blocks.jobs_per_day import jobs_per_day", 1,
         "Level 1, not below Level 1"),
        ("from sql_composer.clauses import SELECT", 2, "reaches inside the Toolbox"),
        ("from composer_core.clauses import SELECT", 2, "reaches inside the Toolbox"),
        ("from . import jobs_per_day", 2, "relative import"),
        ("import requests", 2, "neither a lower Level"),
    ],
)
def test_the_levels_check_catches_a_wrong_import(source: str, level: int, problem: str) -> None:
    (found,) = level_problems(source, level)
    assert problem in found


def test_the_levels_check_lets_the_usual_imports_through() -> None:
    source = (
        "import datetime\n"
        "import pandas as pd\n"
        "from sql_composer import FROM, SELECT, example_database\n"
        "from building_blocks.alerts_per_run import alerts_per_run\n"
    )
    assert level_problems(source, 2) == []


@pytest.mark.parametrize("path", scripts("statements"), ids=lambda p: p.name)
def test_a_statement_script_gives_a_title_and_why(path: Path) -> None:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    lines = doc.splitlines()
    assert lines, f"{path.name} has no module docstring"
    title = lines[0]
    assert len(title) <= 80 and title.endswith("."), f"{path.name}: title {title!r}"
    why = [line for line in doc.split("\n\n") if line.startswith("Why: ")]
    assert len(why) == 1, f"{path.name} needs one paragraph starting 'Why: '"
    sentence = " ".join(why[0].split())
    assert sentence.endswith(".") and ". " not in sentence.rstrip("."), (
        f"{path.name}: the why is more than one sentence"
    )


@pytest.mark.parametrize("path", scripts("statements"), ids=lambda p: p.name)
def test_a_pandas_result_says_so_in_its_first_line(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for function in tree.body:
        if isinstance(function, ast.FunctionDef) and function.name.endswith("_in_pandas"):
            first = (ast.get_docstring(function) or "").splitlines()[:1]
            assert first and PANDAS_LABEL in first[0], f"{path.name}: {function.name}"
