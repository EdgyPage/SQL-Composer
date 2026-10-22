"""The Clean branch README's examples run."""

from __future__ import annotations

import doctest
import importlib
import re
from pathlib import Path

import pytest

from conftest import project_on_the_path, skip_unless_the_example_database_runs, toolbox_module

TEMPLATE = Path(__file__).resolve().parents[1] / "docs" / "clean-branch-readme.md"


def python_blocks(markdown: str) -> list[str]:
    return re.findall(r"^```python\n(.*?)^```$", markdown, re.MULTILINE | re.DOTALL)


BLOCKS = python_blocks(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("number", range(len(BLOCKS)))
def test_the_readme_examples_run(
        number: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The examples run as from a notebook in a new folder: project.start() makes a Project
    # there, and the notebook imports the Project's own files, such as warehouse.py, from it.
    monkeypatch.chdir(tmp_path)
    shared: dict = {}
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE)
    report = []
    with project_on_the_path(tmp_path, ("references", "building_blocks", "warehouse")):
        for block in BLOCKS[: number + 1]:
            # A query, the Example database's or warehouse.py's, runs on the Example database.
            if "query=" in block:
                skip_unless_the_example_database_runs()
            # The block before may have made the files this one imports, such as warehouse.py.
            importlib.invalidate_caches()
            test = doctest.DocTestParser().get_doctest(block, shared, "README", None, 0)
            runner.run(test, out=report.append, clear_globs=False)
            shared = test.globs
    assert runner.failures == 0, "".join(report)


def test_the_readme_counts_the_names_the_star_import_brings() -> None:
    # The README's counts are written by hand: each is checked here against the Toolbox.
    names = toolbox_module().__all__
    text = " ".join(TEMPLATE.read_text(encoding="utf-8").split())
    assert f"the {len(names)} names listed here" in text
