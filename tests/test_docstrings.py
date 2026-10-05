"""Every public name has a docstring with a worked example, and every example runs.

The examples run as doctests with every public name in scope, plus `job_runs` and `jobs` from
the Example database, so a docstring shows only the call and the Hive it emits. A docstring's
first line becomes the name's line in the Clean branch README's cheat sheet, so it is one
sentence of at most 80 characters.

The two constants, TOOLBOX_VERSION and VERSION, can't carry a docstring of their own: theirs
is the Toolbox's own (`sql_composer.__doc__`).
"""

from __future__ import annotations

import doctest
import inspect

import pytest

import editions
import sql_composer
from conftest import edition, skip_unless_the_example_database_runs

PUBLIC = list(sql_composer.__all__)
CONSTANTS = {"TOOLBOX_VERSION", "VERSION"}
# Examples that run a query, and so need the Example database to run here.
RUNS_A_QUERY = ("run(", "check_key(")


def docstring_of(name: str) -> str:
    """A public name's docstring, naming this run's Edition: the Composer core's are written
    once, naming SQL Composer."""
    if name in CONSTANTS:
        return sql_composer.__doc__ or ""
    return editions.named_for(edition(), inspect.getdoc(getattr(sql_composer, name)) or "")


def first_line(name: str) -> str:
    return docstring_of(name).strip().splitlines()[0]


@pytest.mark.parametrize("name", PUBLIC)
def test_every_public_name_has_a_worked_example(name: str) -> None:
    doc = docstring_of(name)
    assert doc.strip(), f"{name} has no docstring"
    assert ">>>" in doc, f"{name}'s docstring has no >>> example"
    if name in CONSTANTS:
        assert f">>> {name}" in doc


@pytest.mark.parametrize("name", PUBLIC)
def test_a_first_line_is_one_short_sentence(name: str) -> None:
    line = first_line(name)
    assert len(line) <= 80, f"{name}: {len(line)} characters"
    assert line.endswith("."), f"{name}: the first line isn't a sentence"
    assert ". " not in line.rstrip("."), f"{name}: the first line is more than one sentence"


@pytest.mark.parametrize("name", sorted(set(PUBLIC) - CONSTANTS) + ["TOOLBOX_VERSION"])
def test_the_worked_example_runs(name: str, tmp_path, monkeypatch) -> None:
    doc = docstring_of(name)
    if any(call in doc for call in RUNS_A_QUERY):
        skip_unless_the_example_database_runs()
    monkeypatch.chdir(tmp_path)
    scope = {public: getattr(sql_composer, public) for public in PUBLIC}
    scope["job_runs"] = sql_composer.example_database.job_runs
    scope["jobs"] = sql_composer.example_database.jobs
    test = doctest.DocTestParser().get_doctest(doc, scope, name, None, 0)
    runner = doctest.DocTestRunner(
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    )
    report = []
    runner.run(test, out=report.append)
    assert runner.failures == 0, "".join(report)


def test_cross_join_says_what_it_opts_out_of() -> None:
    """Its name is an opt-out, so its docstring names the Guard it lets through."""
    paragraphs = docstring_of("CROSS_JOIN").split("\n\n")
    opt_out = next(" ".join(p.split()) for p in paragraphs if "opt-out" in p)
    assert "JOIN" in opt_out.replace("CROSS_JOIN", "") and "ON=" in opt_out
