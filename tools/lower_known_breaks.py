"""Lower tests/repo/known_breaks.py to what the code breaks now, never raising a count.

Toolbox 8.0's refactor fixes breaks of the standard file by file, and the list may only shrink:
run this after a fix, with ruff's findings saved first, and it lowers each count that fell and
drops each that reached zero. A count that rose is printed and left alone, for the code to be
fixed instead:

    .venv/Scripts/python -m ruff check --no-cache --output-format json sqlglot_composer \
        tests tools worked_examples > ruff.json
    .venv/Scripts/python tools/lower_known_breaks.py ruff.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "tests" / "repo" / "known_breaks.py"
WIDTH = 96

sys.path[:0] = [str(ROOT / "tests" / "repo"), str(ROOT / "tests"), str(ROOT / "tools")]

import known_breaks  # noqa: E402
import test_standard  # noqa: E402


def breaks_now(ruff_findings: Path) -> dict[str, Counter[str]]:
    """Every break of the standard today, by file and rule: ruff's, read from its saved
    findings, and the tree rules'."""
    found: dict[str, Counter[str]] = {}
    for finding in json.loads(ruff_findings.read_text(encoding="utf-8")):
        path = Path(finding["filename"]).resolve().relative_to(ROOT).as_posix()
        found.setdefault(path, Counter())[finding["code"]] += 1
    for path, counted in test_standard.every_tree_break().items():
        found.setdefault(path, Counter()).update(counted)
    return found


def lowered_counts(now: dict[str, Counter[str]]) -> tuple[dict[str, dict[str, int]], list[str]]:
    """The list with each count lowered to today's, and each count that rose, which stays."""
    lowered: dict[str, dict[str, int]] = {}
    rose = []
    for path, rules in known_breaks.KNOWN_BREAKS.items():
        for rule, known in rules.items():
            count = now.get(path, Counter())[rule]
            if count > known:
                rose.append(f"{path}: {rule}, {known} known, {count} now")
            kept = min(count, known)
            if kept:
                lowered.setdefault(path, {})[rule] = kept
    for path, rules in now.items():
        for rule, count in rules.items():
            if rule not in known_breaks.KNOWN_BREAKS.get(path, {}):
                rose.append(f"{path}: {rule}, 0 known, {count} now")
    return lowered, rose


def list_text(counts: dict[str, dict[str, int]]) -> list[str]:
    """The list's entries as known_breaks.py writes them, one file each, wrapped at 96."""
    lines = []
    for path in sorted(counts):
        parts = [f'"{rule}": {count}' for rule, count in sorted(counts[path].items())]
        one_line = f'    "{path}": {{{", ".join(parts)}}},'
        if len(one_line) <= WIDTH:
            lines.append(one_line)
            continue
        lines.append(f'    "{path}": {{')
        line = "       "
        for number, part in enumerate(parts, 1):
            piece = f" {part}," if number < len(parts) else f" {part}}},"
            if len(line) + len(piece) > WIDTH:
                lines.append(line)
                line = "       "
            line += piece
        lines.append(line)
    return lines


def write_list(counts: dict[str, dict[str, int]]) -> None:
    """Write known_breaks.py's KNOWN_BREAKS as `counts`, keeping the rest of the file."""
    text = LIST.read_text(encoding="utf-8")
    start = text.index("KNOWN_BREAKS: dict[str, dict[str, int]] = {\n")
    end = text.index("\n}\n", start)
    body = "\n".join(list_text(counts))
    text = f"{text[:start]}KNOWN_BREAKS: dict[str, dict[str, int]] = {{\n{body}{text[end:]}"
    LIST.write_text(text, encoding="utf-8")


def main(arguments: list[str]) -> int:
    """Lower the list, and say what rose."""
    lowered, rose = lowered_counts(breaks_now(Path(arguments[0])))
    write_list(lowered)
    for line in rose:
        print(f"Rose, left for the code to fix: {line}")
    print(f"Lowered {LIST.relative_to(ROOT).as_posix()}.")
    return 1 if rose else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
