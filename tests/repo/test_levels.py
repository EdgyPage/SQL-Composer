"""The Levels of the user's own scripts, checked on the Worked examples in `worked_examples/`
and on each Example project in `example_projects/`.

A script imports only from lower Levels and from the Toolbox, never from a higher or equal
Level. Level 0 is `table_references/`, Level 1 `building_blocks/` and Level 2 `statements/`.
Each Example project is a Project, whose Levels are its own: Level 0 is `references/`, with
`send.py` beside it, Level 1 `building_blocks/`, and Level 2 each Table notebook's logic cell,
the code cell that starts `# logic`.
Most Worked examples read the Example database's Table references, inside the Toolbox;
`table_references/` holds the Table reference of the Saved table they write. Besides the Levels,
a script may import the standard library, what the Toolbox may import (pandas and numpy, from
`tools/toolbox_registry.py`), and the Toolbox only from its top level, as
`from sqlglot_composer import ...`.

Each Statement script's module docstring gives a title and one sentence on why, which the
Example gallery shows, and so does every script of an Example project.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

from toolbox_registry import SHARED_IMPORTS

ROOT = Path(__file__).resolve().parents[2]
WORKED_EXAMPLES = ROOT / "worked_examples"
EXAMPLE_PROJECTS = ROOT / "example_projects"
LEVELS = {"table_references": 0, "building_blocks": 1, "statements": 2}
# An Example project's scripts beside its Level folders, such as run_pipeline.py.
ABOVE_THE_LEVELS = 3
# Each name a script imports its Level's scripts by, with that Level.
IMPORTED_LEVELS = dict(LEVELS)
# A Project's Levels, by the name each is imported by: send.py is Level 0, beside references/.
PROJECT_LEVELS = {"references": 0, "send": 0, "building_blocks": 1}
LOGIC_LEVEL = 2
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


def projects() -> list[Path]:
    return sorted(path for path in EXAMPLE_PROJECTS.iterdir() if path.is_dir())


def project_scripts() -> list[tuple[Path, int]]:
    """Every script of every Example project, its Table references, its Building blocks and
    its send.py, with its Level. admin/templates/ holds Templates, not scripts."""
    found = []
    for project in projects():
        for folder in ("references", "building_blocks"):
            found += [(path, PROJECT_LEVELS[folder])
                      for path in sorted((project / folder).glob("*.py"))]
        found.append((project / "send.py", 0))
    return found


def logic_cells() -> list[tuple[Path, str]]:
    """Each Example project Table notebook's logic cell, the code cell that starts # logic."""
    found = []
    for project in projects():
        for notebook in sorted((project / "tables").glob("*/*.ipynb")):
            cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
            found += [(notebook, "".join(cell["source"])) for cell in cells
                      if cell["cell_type"] == "code"
                      and "".join(cell["source"]).startswith("# logic\n")]
    return found


def _project_id(script: tuple[Path, int]) -> str:
    return script[0].relative_to(EXAMPLE_PROJECTS).as_posix()


def _imported(node: ast.AST) -> list[str] | None:
    """The module names an import statement reads, or None if it isn't one."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return ["." * node.level + (node.module or "")]
    return None


def _problem(name: str, level: int, levels: dict[str, int] = IMPORTED_LEVELS) -> str | None:
    top = name.split(".")[0]
    if name.startswith("."):
        return f"{name} is a relative import; name the Level folder instead"
    if top == "sqlglot_composer":
        return None if name == "sqlglot_composer" else f"{name} reaches inside the Toolbox"
    if top == "composer_core":
        return f"{name} is the Toolbox's folder from before 6.0: import from sqlglot_composer"
    if top in levels:
        if levels[top] < level:
            return None
        return f"{name} is Level {levels[top]}, not below Level {level}"
    if top in sys.stdlib_module_names or top in SHARED_IMPORTS or top == "__future__":
        return None
    return f"{name} is neither a lower Level, the Toolbox, nor something the Toolbox may import"


def level_problems(source: str, level: int,
                   levels: dict[str, int] = IMPORTED_LEVELS) -> list[str]:
    """Every import in a Level `level` script that breaks the Levels rule."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        for name in _imported(node) or []:
            problem = _problem(name, level, levels)
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
        ("from sqlglot_composer.clauses import SELECT", 2, "reaches inside the Toolbox"),
        ("from sqlglot_composer.clauses import SELECT", 2, "reaches inside the Toolbox"),
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
        "from sqlglot_composer import FROM, SELECT, example_database\n"
        "from building_blocks.alerts_per_run import alerts_per_run\n"
    )
    assert level_problems(source, 2) == []


def check_title_and_why(path: Path, source: str | None = None) -> None:
    source = path.read_text(encoding="utf-8") if source is None else source
    doc = ast.get_docstring(ast.parse(source)) or ""
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
def test_a_statement_script_gives_a_title_and_why(path: Path) -> None:
    check_title_and_why(path)


def test_there_are_both_example_projects_with_every_level() -> None:
    assert [project.name for project in projects()] == ["intermediate", "starter"]
    for project in projects():
        assert list((project / "references").glob("*.py")), project.name
        assert list((project / "building_blocks").glob("*.py")), project.name
        assert [cell for notebook, cell in logic_cells() if project in notebook.parents]


@pytest.mark.parametrize("script", project_scripts(), ids=_project_id)
def test_an_example_projects_imports_point_only_downward(script: tuple[Path, int]) -> None:
    path, level = script
    assert level_problems(path.read_text(encoding="utf-8"), level, PROJECT_LEVELS) == []


@pytest.mark.parametrize("cell", logic_cells(), ids=lambda cell: _project_id((cell[0], 0)))
def test_a_table_notebooks_logic_imports_only_lower_levels(cell: tuple[Path, str]) -> None:
    assert level_problems(cell[1], LOGIC_LEVEL, PROJECT_LEVELS) == []


@pytest.mark.parametrize("script", project_scripts(), ids=_project_id)
def test_an_example_projects_script_gives_a_title_and_why(script: tuple[Path, int]) -> None:
    check_title_and_why(script[0])


def test_a_projects_send_sits_at_level_0() -> None:
    """send.py is Level 0, so any notebook may import it, and it may import no Level."""
    assert (EXAMPLE_PROJECTS / "starter" / "send.py", 0) in project_scripts()
    assert level_problems("from send import send\n", 1, PROJECT_LEVELS) == []
    (found,) = level_problems("from references.ops__jobs import jobs\n", 0, PROJECT_LEVELS)
    assert "Level 0, not below Level 0" in found


def test_a_script_above_the_levels_may_import_from_any_of_them() -> None:
    source = (
        "from statements import example_1_daily_job_runs\n"
        "from building_blocks.runs_per_job_day import runs_per_job_day\n"
        "from table_references.jobs import jobs\n"
    )
    assert level_problems(source, ABOVE_THE_LEVELS) == []


@pytest.mark.parametrize("path", scripts("statements"), ids=lambda p: p.name)
def test_a_pandas_result_says_so_in_its_first_line(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for function in tree.body:
        if isinstance(function, ast.FunctionDef) and function.name.endswith("_in_pandas"):
            first = (ast.get_docstring(function) or "").splitlines()[:1]
            assert first and PANDAS_LABEL in first[0], f"{path.name}: {function.name}"
