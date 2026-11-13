"""The suite on many cores, and what a local run keeps between runs (Toolbox 8.7, ticket 03).

`tests/workers.py` says how many workers a run takes and which tests share one, and
`tests/generated_memo.py` lets a "committed is generated" test skip regenerating what hasn't
changed, but never on CI. The code audit's own memo is tested beside it, in
`test_code_audit.py`.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import generated_memo
import snapshot_recorder
import workers
from conftest import TESTS, left_unchanged

ROOT = TESTS.parent


# --- How many workers, and which tests share one ---------------------------------------------


def test_a_run_of_the_whole_suite_takes_up_to_eight_workers_and_a_narrower_one_none() -> None:
    assert workers.worker_count([str(TESTS)], TESTS, 24) == 8
    assert workers.worker_count([str(TESTS)], TESTS, 4) == 4
    assert workers.worker_count([str(TESTS)], TESTS, None) == 1
    assert workers.worker_count([str(TESTS / "repo")], TESTS, 24) == 0
    assert workers.worker_count([str(TESTS), str(TESTS / "test_tables.py")], TESTS, 24) == 0


def fixtures_defined_in(path: Path) -> set[str]:
    """The name of each function decorated as a pytest fixture in the file at `path`."""
    defined = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.FunctionDef) and any(
                "fixture" in ast.unparse(decorator) for decorator in node.decorator_list):
            defined.add(node.name)
    return defined


@pytest.mark.parametrize("fixture", workers.GROUPS)
def test_each_costly_fixture_in_the_map_is_one_its_file_defines(fixture: str) -> None:
    path, name = fixture.split("::")
    assert name in fixtures_defined_in(ROOT / path)


def test_each_group_is_one_fixtures_alone() -> None:
    # Two fixtures in one group would hold both on one worker; each has its own.
    assert len(set(workers.GROUPS.values())) == len(workers.GROUPS)


def test_every_test_using_a_costly_fixture_carries_its_group(request: pytest.FixtureRequest
                                                             ) -> None:
    # The tests this run collected, the whole suite's or fewer. On a worker, the mark was in
    # place before pytest-xdist read it into the test's id, which says where it runs.
    on_a_worker = getattr(request.config.option, "loadgroup", False)  # set on a worker
    for item in request.session.items:
        group = workers.group_of(item)
        marked = [mark.kwargs.get("name") for mark in item.iter_markers("xdist_group")]
        if group:
            assert group in marked, item.nodeid
            assert item.nodeid.endswith(f"@{group}") or not on_a_worker, item.nodeid


def test_a_test_ends_its_unit_where_the_next_is_another_file_or_group(
        request: pytest.FixtureRequest) -> None:
    assert workers.unit_of(request.node) == "tests/repo/test_faster_suite.py"
    assert workers.unit_of(None) is None


def test_the_summary_shows_each_workers_memory_after_its_groups() -> None:
    assert workers.memory_lines({"gw1": [100_000, 130_000, 110_000], "gw0": []}) == [
        "gw1: 3 groups and files; after the first 100k, the median 110k, after the last 110k, "
        "at most 130k"]


# --- A tree tests share ----------------------------------------------------------------------


def test_a_test_that_only_reads_a_shared_tree_passes(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    with left_unchanged(tmp_path):
        assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "a"


def change_the_tree(folder: Path, change: str) -> None:
    if change == "edits a file":
        (folder / "a.txt").write_text("b", encoding="utf-8")
    elif change == "adds a file":
        (folder / "b.txt").write_text("b", encoding="utf-8")
    else:
        (folder / "a.txt").unlink()


@pytest.mark.parametrize("change", ["edits a file", "adds a file", "deletes a file"])
def test_a_test_that_changes_a_shared_tree_fails(tmp_path: Path, change: str) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    with pytest.raises(AssertionError, match="which other tests share"), \
            left_unchanged(tmp_path):
        change_the_tree(tmp_path, change)


# --- The memo of a "committed is generated" test ---------------------------------------------


@pytest.fixture
def memo_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repo of two files, `made.txt` the generated output and `source.txt` its input, a memo
    folder of its own, and a snapshot that knows one text, which the test made."""
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("made.txt", "source.txt"):
        (root / name).write_text(name, encoding="utf-8")
    monkeypatch.setattr(generated_memo, "ROOT", root)
    monkeypatch.setattr(generated_memo, "FOLDER", tmp_path / "memo")
    monkeypatch.setattr(generated_memo, "SHARED_INPUTS", ("source.txt",))
    monkeypatch.setattr(generated_memo, "INPUTS", {"made": ("made.txt",)})
    monkeypatch.delenv("CI", raising=False)
    made = ("hive", "SELECT 1")
    monkeypatch.setattr(snapshot_recorder, "texts_made_by_this_test", [made])
    monkeypatch.setattr(snapshot_recorder, "hashes_made_in_this_run", set())
    known = {snapshot_recorder.hash_of(*made)}
    monkeypatch.setattr(snapshot_recorder, "known_hashes", lambda: known)
    monkeypatch.setattr(snapshot_recorder, "WRITING", False)
    return root


def kept_and_asked_again(root: Path) -> bool:
    """Whether the memo says unchanged once the test passed and kept it, the snapshot's hashes
    of this run forgotten in between."""
    generated_memo.Memo("made").keep()
    snapshot_recorder.texts_made_by_this_test.clear()
    snapshot_recorder.hashes_made_in_this_run.clear()
    return generated_memo.Memo("made").is_unchanged()


def test_an_output_whose_inputs_are_unchanged_is_not_regenerated(memo_world: Path) -> None:
    assert not generated_memo.Memo("made").is_unchanged()  # never kept: regenerated
    assert kept_and_asked_again(memo_world)
    # The snapshot's hashes the test made when it regenerated are made in this run too.
    assert snapshot_recorder.hashes_made_in_this_run == {
        snapshot_recorder.hash_of("hive", "SELECT 1")}


@pytest.mark.parametrize("changed", ["source.txt", "made.txt"])
def test_a_changed_input_or_output_regenerates(memo_world: Path, changed: str) -> None:
    generated_memo.Memo("made").keep()
    (memo_world / changed).write_text("edited", encoding="utf-8")
    assert not generated_memo.Memo("made").is_unchanged()


def test_on_ci_every_output_regenerates(memo_world: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    assert not kept_and_asked_again(memo_world)


def test_a_memo_that_doesnt_read_regenerates(memo_world: Path) -> None:
    generated_memo.Memo("made").keep()
    generated_memo.Memo("made").memo_file.write_text("not json", encoding="utf-8")
    assert not generated_memo.Memo("made").is_unchanged()


def test_a_memo_whose_texts_the_snapshot_no_longer_knows_regenerates(
        memo_world: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snapshot_recorder, "known_hashes", lambda: set())
    assert not kept_and_asked_again(memo_world)


def test_each_generated_outputs_inputs_are_in_the_repo() -> None:
    for name, paths in generated_memo.INPUTS.items():
        for path in generated_memo.SHARED_INPUTS + paths:
            assert (ROOT / path).exists(), (name, path)


def test_the_memo_is_kept_where_git_ignores_it() -> None:
    folder = generated_memo.FOLDER.relative_to(ROOT).parts[0]
    assert f"{folder}/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


# --- How CI and pyproject.toml run it --------------------------------------------------------


def test_the_suite_runs_on_workers_grouped_by_fixture() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    addopts = re.search(r'^addopts = "(.*)"$', pyproject, re.MULTILINE).group(1).split()
    assert addopts[addopts.index("-n") + 1] == "auto"
    assert addopts[addopts.index("--dist") + 1] == "loadgroup"


def test_ci_regenerates_every_generated_output() -> None:
    workflow = (ROOT / ".github" / "workflows" / "dev.yml").read_text(encoding="utf-8")
    assert re.search(r'^\s+CI: "true"$', workflow, re.MULTILINE)


def test_xdist_is_pinned_for_dev() -> None:
    pins = dict(re.findall(r"^([\w.-]+)==([\w.]+)$",
                           (ROOT / "requirements-dev.txt").read_text(encoding="utf-8"),
                           re.MULTILINE))
    assert {"pytest-xdist", "execnet"} <= set(pins)
