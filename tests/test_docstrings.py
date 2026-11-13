"""Every public name has a docstring with a worked example, and every example runs.

The examples run as doctests with every public name in scope, plus, from dev's Example
database, each of its tables by name, such as `job_runs`, and its `query` and `execute`,
standing in for the user's own: a docstring shows only the call and the Hive it emits, and
imports nothing the Toolbox doesn't ship (Toolbox 8.7, ticket 12). A docstring's
first line becomes the name's line in the Clean branch README's cheat sheet, so it is one
sentence of at most 80 characters.

The two constants, TOOLBOX_VERSION and VERSION, can't carry a docstring of their own: theirs
is the Toolbox's own (`sqlglot_composer.__doc__`).
"""

from __future__ import annotations

import doctest
import inspect
from pathlib import Path

import pytest

import example_database
import sqlglot_composer

PUBLIC = list(sqlglot_composer.__all__)
# The admin module's names, as admin.drop_table: imported by name, not by the star import.
ADMIN = [f"admin.{name}" for name in sqlglot_composer.admin.__all__]
# The project module's names, as project.start, imported by name like the admin module's.
ADMIN += [f"project.{name}" for name in sqlglot_composer.project.__all__]
CONSTANTS = {"TOOLBOX_VERSION", "VERSION"}


def docstring_of(name: str) -> str:
    """A public name's docstring."""
    if name in CONSTANTS:
        return sqlglot_composer.__doc__ or ""
    value = sqlglot_composer
    for part in name.split("."):
        value = getattr(value, part)
    return inspect.getdoc(value) or ""


def first_line(name: str) -> str:
    return docstring_of(name).strip().splitlines()[0]


@pytest.mark.parametrize("name", PUBLIC + ADMIN)
def test_every_public_name_has_a_worked_example(name: str) -> None:
    doc = docstring_of(name)
    assert doc.strip(), f"{name} has no docstring"
    assert ">>>" in doc, f"{name}'s docstring has no >>> example"
    if name in CONSTANTS:
        assert f">>> {name}" in doc


@pytest.mark.parametrize("name", PUBLIC + ADMIN)
def test_an_example_names_no_example_database(name: str) -> None:
    """The Example database is dev's alone, so an example uses its tables, query and execute
    by name, as a user's notebook names its own (Toolbox 8.7, ticket 12)."""
    assert "example_database" not in docstring_of(name)


@pytest.mark.parametrize("name", PUBLIC + ADMIN)
def test_a_first_line_is_one_short_sentence(name: str) -> None:
    line = first_line(name)
    assert len(line) <= 80, f"{name}: {len(line)} characters"
    assert line.endswith("."), f"{name}: the first line isn't a sentence"
    assert ". " not in line.rstrip("."), f"{name}: the first line is more than one sentence"


@pytest.mark.parametrize("name", sorted(set(PUBLIC) - CONSTANTS) + ["TOOLBOX_VERSION"] + ADMIN)
def test_the_worked_example_runs(
        name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    doc = docstring_of(name)
    monkeypatch.chdir(tmp_path)
    scope = {public: getattr(sqlglot_composer, public) for public in PUBLIC}
    scope.update(example_database.doctest_names())
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
