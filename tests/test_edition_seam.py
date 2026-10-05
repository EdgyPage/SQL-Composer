"""edition.py: the one place the rest of the Toolbox reaches the Edition's own two files.

The Edition plugs its writing.py and engine.py in when it is imported. A Python runs one
Edition only, and a lineage's time and version are read through one function each, so a tool
can pin them and write the same files every time.
"""

from __future__ import annotations

import pytest
from conftest import edition, toolbox_module

from sql_composer import (
    FROM,
    SELECT,
    WHERE,
    equals,
    example_database,
    export_lineage,
    statement,
)

job_runs = example_database.job_runs


def test_the_edition_that_was_imported_is_plugged_in() -> None:
    seam = toolbox_module("edition")
    assert seam.FOLDER == edition().folder
    assert seam.PRODUCT == edition().product
    assert seam.VERSION == toolbox_module().VERSION


def test_a_second_edition_in_the_same_python_stops_the_import() -> None:
    seam = toolbox_module("edition")
    with pytest.raises(ImportError) as stop:
        seam.plug("other_composer", "Other Composer", "Other Composer 1.0", None, None)
    message = str(stop.value)
    assert message.startswith("other_composer stopped on import:")
    assert f"other_composer was imported after {edition().folder}, in the same Python" in message
    assert f"`from {edition().folder} import ...` or every one `from other_composer import" in message
    assert "restart the notebook's kernel" in message
    assert seam.FOLDER == edition().folder  # still the Edition that was imported first


def test_plugging_in_the_same_edition_again_changes_nothing() -> None:
    seam = toolbox_module("edition")
    before = (seam.FOLDER, seam.PRODUCT, seam.VERSION)
    seam.plug(seam.FOLDER, seam.PRODUCT, seam.VERSION, seam._writing, seam._engine)
    assert (seam.FOLDER, seam.PRODUCT, seam.VERSION) == before


def test_using_the_toolbox_before_an_edition_is_plugged_in_is_refused(monkeypatch) -> None:
    seam = toolbox_module("edition")
    monkeypatch.setattr(seam, "_writing", None)
    with pytest.raises(RuntimeError, match="no Edition of the Toolbox was imported"):
        seam.hive_text(None)


def test_a_lineage_with_its_time_and_version_pinned_is_the_same_every_time(
        tmp_path, monkeypatch) -> None:
    import datetime

    lineage = toolbox_module("lineage")
    monkeypatch.setattr(lineage, "_now", lambda: datetime.datetime(2026, 9, 25, 6, 0))
    monkeypatch.setattr(lineage, "_version", lambda: "Pinned Composer 9.9")
    monkeypatch.chdir(tmp_path)
    failed = statement(SELECT(job_runs.run_id), FROM(job_runs),
                       WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")))
    first = [path.read_bytes() for path in export_lineage(failed, to=tmp_path / "failed.html")]
    second = [path.read_bytes() for path in export_lineage(failed, to=tmp_path / "failed.html")]
    assert first == second
    assert b"Made by export_lineage on 2026-09-25 06:00" in first[1]
    assert b"with Pinned Composer 9.9." in first[1]
