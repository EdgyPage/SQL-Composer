"""sqlglot Composer stops on import when sqlglot is missing, out of range or behaves differently."""

from __future__ import annotations

import sys

import pytest
import sqlglot

import sqlglot_composer
from conftest import import_stop


def test_a_python_without_sqlglot_stops_the_import(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "sqlglot", None)  # makes `import sqlglot` fail
    with pytest.raises(ImportError) as error:
        sqlglot_composer.engine.check_installed()
    assert f"ImportError: {error.value}" == import_stop(
        what="sqlglot Composer needs sqlglot, and this Python can't import it.",
        why="sqlglot Composer writes every Statement as Hive through sqlglot, and reads the Hive "
        "back to check it, so it can't build anything without it.",
        fix='Install sqlglot from a notebook cell with %pip install "sqlglot>=25.24.2,<31.0.0", '
        "then restart the kernel. If you can't install packages, ask whoever looks after your "
        "environment.",
    )


@pytest.mark.parametrize("version", ["25.24.1", "31.0.0", "unknown"])
def test_a_sqlglot_outside_the_range_stops_the_import(monkeypatch, version) -> None:
    monkeypatch.setattr(sqlglot, "__version__", version)
    with pytest.raises(ImportError) as error:
        sqlglot_composer.engine.check_installed()
    assert f"ImportError: {error.value}" == import_stop(
        what="sqlglot Composer needs sqlglot 25.24.2 or newer, below 31.0.0, and this Python has "
        f"sqlglot {version}.",
        why="sqlglot Composer is checked only on that range of sqlglot. Another sqlglot can write "
        "Hive differently, so a Statement could come out wrong without anything saying so.",
        fix="Install a sqlglot in that range from a notebook cell with %pip install "
        '"sqlglot>=25.24.2,<31.0.0", then restart the kernel. '
        "If you can't install packages, "
        "ask whoever looks after your environment.",
    )


def test_a_sqlglot_that_behaves_differently_stops_the_import(monkeypatch) -> None:
    from sqlglot import exp

    real = exp.convert
    monkeypatch.setattr(exp, "convert",
                        lambda value, *args, **kw: exp.Literal.string("changed")
                        if value == "O'Brien\\" else real(value, *args, **kw))
    with pytest.raises(ImportError) as error:
        sqlglot_composer.engine.check_installed()
    assert f"ImportError: {error.value}" == import_stop(
        what=f"sqlglot {sqlglot.__version__} is in the supported range, but behaves "
        "differently: Hive string escaping has changed. Nothing has been built or sent.",
        why="sqlglot Composer relies on this behaviour to write Hive safely, so a Statement could "
        "come out wrong.",
        fix="Install again the sqlglot version that sqlglot Composer is tested on, from a notebook cell with "
        '%pip install --force-reinstall "sqlglot==30.19.0", then restart the kernel. '
        "If you can't install packages, "
        "ask whoever looks after your environment.",
    )


def test_a_newer_sqlglot_in_range_prints_a_note(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sqlglot, "__version__", "30.20.1")
    sqlglot_composer.engine.check_installed()
    assert capsys.readouterr().out == (
        "Note: sqlglot 30.20.1 is newer than any version sqlglot Composer was tested on "
        "(30.19.0). Its behaviour checks passed.\n")
