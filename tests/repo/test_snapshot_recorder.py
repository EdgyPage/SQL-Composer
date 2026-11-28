"""The snapshot's recorder keeps one snapshot for each sqlglot CI tests (Toolbox 8.10).

CI runs the whole suite at sqlglot's pin and at the newest version the Toolbox is tested on,
and a few texts differ between them, so `tests/snapshot_recorder.py` reads and writes the
snapshot of the sqlglot it runs on, and checks none on any other. The user (2026-11-28): "test
for both."
"""

from __future__ import annotations

from pathlib import Path

import pytest

import snapshot_recorder

PIN, NEWEST = "30.23.0", "30.34.0"


@pytest.fixture
def snapshots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A snapshot folder of its own, with a snapshot for each sqlglot CI tests that knows one
    text, a different one for each, and a run that made nothing yet."""
    monkeypatch.setattr(snapshot_recorder, "SNAPSHOT", tmp_path)
    monkeypatch.setattr(snapshot_recorder, "versions_ci_tests", lambda: (PIN, NEWEST))
    monkeypatch.setattr(snapshot_recorder, "texts_made_by_this_test", [])
    monkeypatch.setattr(snapshot_recorder, "hashes_made_in_this_run", set())
    monkeypatch.setattr(snapshot_recorder, "WRITING", False)
    (tmp_path / "known.txt").write_text(f"{snapshot_recorder.hash_of('hive', 'AT THE PIN')}\n",
                                        encoding="utf-8")
    (tmp_path / f"known-{NEWEST}.txt").write_text(
        f"{snapshot_recorder.hash_of('hive', 'AT THE NEWEST')}\n", encoding="utf-8")
    return tmp_path


def run_on(monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    """The run as if on sqlglot `version`."""
    monkeypatch.setattr(snapshot_recorder, "sqlglot_version", lambda: version)


def snapshot_texts(folder: Path) -> dict[str, str]:
    """Each snapshot file in `folder`, by its name, with its text."""
    return {path.name: path.read_text(encoding="utf-8") for path in folder.iterdir()}


def test_the_pin_keeps_known_txt_and_the_newest_tested_a_file_named_for_its_version(
        snapshots: Path) -> None:
    assert snapshot_recorder.snapshot_files() == {PIN: snapshots / "known.txt",
                                                  NEWEST: snapshots / "known-30.34.0.txt"}


@pytest.mark.parametrize(("version", "text"), [(PIN, "AT THE PIN"), (NEWEST, "AT THE NEWEST")])
def test_a_run_checks_the_snapshot_of_the_sqlglot_it_runs_on(
        snapshots: Path, monkeypatch: pytest.MonkeyPatch, version: str, text: str) -> None:
    run_on(monkeypatch, version)
    known = snapshot_recorder.known_hashes()
    snapshot_recorder.texts_made_by_this_test.append(("hive", text))
    assert snapshot_recorder.take_unknown_texts(known) == []
    other = "AT THE NEWEST" if text == "AT THE PIN" else "AT THE PIN"
    snapshot_recorder.texts_made_by_this_test.append(("hive", other))
    assert snapshot_recorder.take_unknown_texts(known) == [f"A hive text:\n{other}"]
    assert snapshot_recorder.why_no_snapshot_is_checked() is None


def test_a_whole_run_fails_on_a_text_its_own_snapshot_holds_and_no_test_made(
        snapshots: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_on(monkeypatch, NEWEST)
    failure = snapshot_recorder.finish_the_run(whole=True)
    assert failure.startswith("tests/snapshot/known-30.34.0.txt: 1 of its texts no test made")
    snapshot_recorder.hashes_made_in_this_run.add(snapshot_recorder.hash_of("hive",
                                                                            "AT THE NEWEST"))
    assert snapshot_recorder.finish_the_run(whole=True) is None


def test_another_sqlglot_checks_no_snapshot_and_says_why_in_one_line(
        snapshots: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_on(monkeypatch, "30.35.0")
    known = snapshot_recorder.known_hashes()
    assert known is None
    snapshot_recorder.texts_made_by_this_test.append(("hive", "ANYTHING"))
    assert snapshot_recorder.take_unknown_texts(known) == []
    assert snapshot_recorder.finish_the_run(whole=True) is None
    why = snapshot_recorder.why_no_snapshot_is_checked()
    assert why == ("No snapshot was checked: tests/snapshot/ keeps one for each sqlglot CI "
                   "tests, 30.23.0 and 30.34.0, and this is 30.35.0, which can write some "
                   "texts differently.")


def test_writing_writes_the_snapshot_of_the_sqlglot_it_runs_on_and_no_other(
        snapshots: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_on(monkeypatch, NEWEST)
    monkeypatch.setattr(snapshot_recorder, "WRITING", True)
    pin_before = (snapshots / "known.txt").read_text(encoding="utf-8")
    snapshot_recorder.hashes_made_in_this_run.update({"bbb", "aaa"})
    assert snapshot_recorder.finish_the_run(whole=True) is None
    assert (snapshots / "known-30.34.0.txt").read_text(encoding="utf-8") == "aaa\nbbb\n"
    assert (snapshots / "known.txt").read_text(encoding="utf-8") == pin_before


@pytest.mark.parametrize(("version", "whole", "refusal"), [
    (NEWEST, False, "tests/snapshot/known-30.34.0.txt: SNAPSHOT_WRITE=1 writes it only from a "
                    "run of the whole suite in which every test passed."),
    ("30.35.0", True, "SNAPSHOT_WRITE=1 writes a snapshot only on a sqlglot CI tests, 30.23.0 "
                      "or 30.34.0, and this is 30.35.0."),
])
def test_writing_is_refused_from_part_of_the_suite_or_on_another_sqlglot(
        snapshots: Path, monkeypatch: pytest.MonkeyPatch, version: str, whole: bool,
        refusal: str) -> None:
    run_on(monkeypatch, version)
    monkeypatch.setattr(snapshot_recorder, "WRITING", True)
    before = snapshot_texts(snapshots)
    assert snapshot_recorder.finish_the_run(whole) == refusal
    assert snapshot_texts(snapshots) == before
