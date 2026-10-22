"""How much of the Toolbox the test suite uses: each function's calls, and the lines no test reaches.

Run from the repo's top, on dev only (coverage is in requirements-dev.txt, not requirements.txt):

    .venv/Scripts/python tools/usage_report.py

It runs the whole suite once, in this Python, and writes .scratch/toolbox-7/usage-report.md:
every function of sqlglot_composer/ with how many times the suite called it, most first, and,
file by file, the lines no test reached. A function called often is a busy path, where a
simpler shape removes the most chances of a bug; a line nothing reaches is dead, or untested.
Tests that start a second Python, such as the Example projects' and the export's, aren't
counted: their calls happen in that other Python.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from types import CodeType

import coverage
import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLBOX = ROOT / "sqlglot_composer"
REPORT = ROOT / ".scratch" / "toolbox-7" / "usage-report.md"
# The sys.monitoring tool id this report counts calls under; coverage takes its own.
TOOL = 4


def count_calls() -> Counter[tuple[str, str, int]]:
    """Start counting each call of a Toolbox function, as (file, function, first line); the
    count fills in as the suite runs. Code outside the Toolbox is let go after its first call."""
    calls: Counter[tuple[str, str, int]] = Counter()
    folder = str(TOOLBOX)
    monitoring = sys.monitoring

    def started(code: CodeType, _offset: int) -> object:
        if not code.co_filename.startswith(folder):
            return monitoring.DISABLE
        calls[(Path(code.co_filename).name, code.co_qualname, code.co_firstlineno)] += 1
        return None

    monitoring.use_tool_id(TOOL, "usage_report")
    monitoring.register_callback(TOOL, monitoring.events.PY_START, started)
    monitoring.set_events(TOOL, monitoring.events.PY_START)
    return calls


def stop_counting() -> None:
    sys.monitoring.set_events(TOOL, 0)
    sys.monitoring.free_tool_id(TOOL)


def ranges(lines: list[int]) -> str:
    """Line numbers as ranges, such as 3-5, 9."""
    parts, start = [], None
    for index, line in enumerate(lines):
        if start is None:
            start = line
        if index + 1 == len(lines) or lines[index + 1] != line + 1:
            parts.append(str(start) if start == line else f"{start}-{line}")
            start = None
    return ", ".join(parts)


def report(calls: Counter[tuple[str, str, int]], measured: coverage.Coverage) -> str:
    """The report's Markdown: calls by function, then the lines nothing reached, by file."""
    lines = ["# Toolbox usage in the test suite", "",
             "Written by tools/usage_report.py. Calls counted in the suite's own Python.", "",
             "## Calls per function, most first", "", "| Calls | Function |", "|---|---|"]
    lines += [f"| {count} | {file}:{line} {name} |"
              for (file, name, line), count in calls.most_common()]
    lines += ["", "## Lines no test reached", ""]
    for path in sorted(TOOLBOX.glob("*.py")):
        missing = measured.analysis2(str(path))[3]
        if missing:
            lines.append(f"- {path.name}: {ranges(sorted(missing))}")
    return "\n".join(lines) + "\n"


def main() -> int:
    measured = coverage.Coverage(source=[str(TOOLBOX)], data_file=None)
    calls = count_calls()
    measured.start()
    try:
        status = pytest.main(["-q", "-p", "no:cacheprovider", str(ROOT / "tests")])
    finally:
        measured.stop()
        stop_counting()
    REPORT.write_text(report(calls, measured), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT).as_posix()}: {len(calls)} functions called; "
          f"the suite {'passed' if status == 0 else 'failed'}.")
    return int(status)


if __name__ == "__main__":
    sys.exit(main())
