"""The suite on many cores: how many workers, which tests share one, and the memory each holds.

pytest-xdist runs the suite in worker processes, as `pyproject.toml`'s `-n auto --dist
loadgroup` says (Toolbox 8.7, ticket 03):

- **How many.** A run of the whole suite takes `WORKERS` workers, or fewer on a computer with
  fewer cores: other runs share this computer. A narrower run, such as one file, takes none and
  runs in one process, which starts sooner. `-n 4` or `-n 0` on the command line chooses.
- **Which tests share one.** `GROUPS` is the one map from a costly fixture to the group of tests
  that share it. conftest.py marks every test that uses one, directly or through another
  fixture, with its group (`xdist_group`), and `--dist loadgroup` sends a group's tests to one
  worker, one after another, so the fixture is made once. A new costly fixture gets a line
  here.
- **Memory.** When a worker's last test of a group or a test file is done, its fixtures of that
  scope are torn down, and each costly fixture removes its temporary folder. Then the worker
  collects its garbage and notes the memory Python holds, in allocated blocks; the run's summary
  shows each worker's notes, so a worker whose memory keeps growing is seen.

Every worker loads conftest.py, so the offline trap is installed in each, as in a run in one
process.
"""

from __future__ import annotations

import statistics
from pathlib import Path

import pytest

# The most workers a run of the whole suite takes.
WORKERS = 8

# Each costly fixture, as the file that defines it and its name, and the group of the tests
# that use it.
GROUPS = {
    "tests/repo/test_export_clean.py::clean_build": "clean_tree",
    "tests/test_usability_loop.py::built_main": "mains_tree",
    "tests/test_copilot_eval.py::references": "copilot_eval_references",
    "tests/test_copilot_eval.py::controls": "copilot_eval_controls",
    "tests/test_copilot_files.py::ran": "copilot_stand_in_project",
    "tests/test_example_projects.py::projects": "example_projects",
    "tests/test_excel_eval.py::hive": "excel_stand_in_hive",
    "tests/test_pivot_tables.py::written": "pivot_workbooks",
    "tests/test_workbook_hive.py::hive": "workbook_hive_stand_in_hive",
    "tests/test_workbook_power_query.py::hive": "workbook_power_query_stand_in_hive",
    "tests/test_workbook_pivots.py::built": "pivot_workbooks_read",
}


def worker_count(args: list[str], tests: Path, cores: int | None) -> int:
    """How many workers a run takes: WORKERS, or the computer's cores if fewer, for a run of the
    whole suite, whose `args` all name the `tests` folder; none for a narrower run."""
    if not all(Path(arg).resolve() == tests for arg in args):
        return 0
    return min(WORKERS, cores or 1)


def group_of(item: pytest.Item) -> str | None:
    """The group of a test that uses a costly fixture in GROUPS, directly or through another
    fixture, or None. A test using two takes the first in GROUPS' order."""
    # pytest keeps the fixtures a test uses, its own and those they use, only in this private
    # attribute; pytest is pinned in requirements-dev.txt, and the tests in
    # test_faster_suite.py fail if it moves.
    used = {f"{definitions[-1].baseid}::{name}"
            for name, definitions in item._fixtureinfo.name2fixturedefs.items()}
    for fixture, group in GROUPS.items():
        if fixture in used:
            return group
    return None


def unit_of(item: pytest.Item | None) -> str | None:
    """What a test runs as part of: its group, or else its file, whose fixtures it shares."""
    if item is None:
        return None
    return group_of(item) or item.nodeid.split("::")[0]


def memory_lines(notes: dict[str, list[int]]) -> list[str]:
    """One line for each worker, from its notes of the blocks Python held after each group or
    file: how many it took, and the blocks after the first, at the middle, after the last and at
    most, in thousands."""
    lines = []
    for worker, blocks in sorted(notes.items()):
        if not blocks:
            continue
        counts = [blocks[0], int(statistics.median(blocks)), blocks[-1], max(blocks)]
        first, middle, last, most = (f"{count // 1000:,}k" for count in counts)
        lines.append(f"{worker}: {len(blocks)} groups and files; after the first {first}, "
                     f"the median {middle}, after the last {last}, at most {most}")
    return lines
