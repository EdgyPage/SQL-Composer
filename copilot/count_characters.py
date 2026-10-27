"""Count the characters of each Copilot file, against the 8,000 Copilot takes before a chat.

    python count_characters.py                    counts the .txt files beside this script
    python count_characters.py my_copy.txt        counts the files and folders you name

Every character counts: letters, spaces, tabs and line breaks. Each file is counted twice: as
saved, and as it would be with Windows line breaks, where each line break is two characters,
as some copies and pastes make it. A file fits when the larger count is at most 8,000. It
exits with 1 when any file is over, and 0 when every one fits.

It needs nothing but Python, and reads only the files you name.
"""

from __future__ import annotations

import sys
from pathlib import Path

LIMIT = 8000


def characters(text: str) -> tuple[int, int]:
    """How many characters a text is: with one character for each line break, and with two,
    as Windows writes a line break."""
    plain = text.replace("\r\n", "\n")
    return len(plain), len(plain) + plain.count("\n")


def files_in(names: list[str]) -> list[Path]:
    """Each file named, and each .txt file in each folder named; with no name, the .txt files
    beside this script."""
    paths = [Path(name) for name in names] or [Path(__file__).resolve().parent]
    found = []
    for path in paths:
        found += sorted(path.glob("*.txt")) if path.is_dir() else [path]
    return found


def main(argv: list[str] | None = None) -> int:
    """Print each file's characters and what is left of the limit; 1 when any file is over."""
    over = False
    for path in files_in(sys.argv[1:] if argv is None else argv):
        saved, windows = characters(path.read_text(encoding="utf-8"))
        most = max(saved, windows)
        left = LIMIT - most
        over = over or left < 0
        said = f"OVER by {-left:,}" if left < 0 else f"{left:,} to spare"
        print(f"{path.name}: {saved:,} characters ({windows:,} with Windows line breaks), "
              f"limit {LIMIT:,}: {said}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
