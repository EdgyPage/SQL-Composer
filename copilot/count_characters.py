# sqlglot Composer 7.2 - copy it, then edit your copy
"""Count the characters of each Copilot file, against the 8,000 Copilot takes at once.

    python count_characters.py                    counts the .txt files beside this script
    python count_characters.py my_copy.txt        counts the files and folders you name

Every character counts: letters, spaces, tabs and line breaks. Each file is counted twice: as
saved, and as it would be with Windows line breaks, where each line break is two characters,
as some copies and pastes make it. A file fits when the larger count is at most 8,000. It
exits with 1 when any file is over or isn't there, and 0 when every one fits.

It needs nothing but Python, and reads only the files you name.
"""

import sys
from pathlib import Path

LIMIT = 8000


def characters(text: str) -> int:
    """How many characters a text is, each line break one character."""
    return len(text.replace("\r\n", "\n"))


def characters_on_windows(text: str) -> int:
    """How many characters a text is with Windows line breaks, each line break two."""
    plain = text.replace("\r\n", "\n")
    return len(plain) + plain.count("\n")


def files_in(names: list[str]) -> list[Path]:
    """Each file named, and each .txt file in each folder named; with no name, the .txt files
    beside this script."""
    paths = [Path(name) for name in names]
    if not paths:
        paths = [Path(__file__).resolve().parent]
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found += sorted(path.glob("*.txt"))
        else:
            found.append(path)
    return found


def main(argv: list[str] | None = None) -> int:
    """Print each file's characters and what is left of the limit; 1 when any file is over or
    isn't there."""
    if argv is None:
        argv = sys.argv[1:]
    any_over = False
    for path in files_in(argv):
        if not path.is_file():
            print(f"{path}: no such file")
            any_over = True
            continue
        text = path.read_text(encoding="utf-8")
        saved, on_windows = characters(text), characters_on_windows(text)
        to_spare = LIMIT - max(saved, on_windows)
        if to_spare < 0:
            any_over = True
            verdict = f"OVER by {-to_spare:,}"
        else:
            verdict = f"{to_spare:,} to spare"
        print(f"{path.name}: {saved:,} characters ({on_windows:,} with Windows line breaks), "
              f"limit {LIMIT:,}: {verdict}")
    return 1 if any_over else 0


if __name__ == "__main__":
    sys.exit(main())
