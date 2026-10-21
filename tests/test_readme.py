"""The Clean branch README's examples run."""

from __future__ import annotations

import doctest
import re
from pathlib import Path

import pytest

from conftest import skip_unless_the_example_database_runs, toolbox_module

TEMPLATE = Path(__file__).resolve().parents[1] / "docs" / "clean-branch-readme.md"


def python_blocks(markdown: str) -> list[str]:
    return re.findall(r"^```python\n(.*?)^```$", markdown, re.MULTILINE | re.DOTALL)


BLOCKS = python_blocks(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("number", range(len(BLOCKS)))
def test_the_readme_examples_run(number: int) -> None:
    shared: dict = {}
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE)
    report = []
    for block in BLOCKS[: number + 1]:
        if "send=example_database.send" in block:
            skip_unless_the_example_database_runs()
        test = doctest.DocTestParser().get_doctest(block, shared, "README", None, 0)
        runner.run(test, out=report.append, clear_globs=False)
        shared = test.globs
    assert runner.failures == 0, "".join(report)


def test_the_readme_counts_the_names_the_star_import_brings() -> None:
    # The README's counts are written by hand: each is checked here against the Toolbox.
    names = toolbox_module().__all__
    text = " ".join(TEMPLATE.read_text(encoding="utf-8").split())
    assert f"the {len(names)} names listed here" in text
