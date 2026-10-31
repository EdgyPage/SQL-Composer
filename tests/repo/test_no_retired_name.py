"""No page a user reads names a call or a path Toolbox 8.0 took out. Toolbox 8.0, ticket 19.

8.0 replaced 7.2's one-action admin notebooks with the Workflow notebooks in admin/workflows/,
made every Conversion a batch whose index is admin/workflows/convert/<name>/, and took out
finish_conversion and conversion_notebook. The upgrade steps, CHANGES.md and the frozen 7.2
Example projects name them on purpose, to say what changed, and are not read here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sqlglot_composer import upgrades

ROOT = Path(__file__).resolve().parents[2]
# Every page a user reads: the README template, the glossary, the how-tos and Worked examples,
# the Copilot files, both Example projects, the Toolbox's docstrings and refusals, and the
# pages generated from them.
READ = [ROOT / "docs" / "clean-branch-readme.md", ROOT / "CONTEXT.md",
        *sorted((ROOT / "worked_examples").rglob("*.py")),
        *sorted((ROOT / "copilot").glob("*.txt")),
        *sorted((ROOT / "example_projects").rglob("*.md")),
        *sorted((ROOT / "example_projects").rglob("*.ipynb")),
        *[path for path in sorted((ROOT / "sqlglot_composer").glob("*.py"))
          if path.name != "upgrades.py"],
        ROOT / "sqlglot_composer" / "how_to.html", ROOT / "sqlglot_composer" / "examples.html"]
RETIRED = [
    *[f"admin/{name}.ipynb" for name in upgrades.RETIRED_IN_8_0],
    "admin/conversions/", "finish_conversion", "conversion_notebook",
]


@pytest.mark.parametrize("path", READ, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_no_page_names_a_retired_call_or_path(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    named = [retired for retired in RETIRED if re.search(re.escape(retired), text)]
    assert named == [], f"{path.relative_to(ROOT).as_posix()} names what 8.0 took out"
