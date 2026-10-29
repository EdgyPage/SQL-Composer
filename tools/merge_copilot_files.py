"""Merge the Copilot files into one document, `copilot/all_in_one/all_copilot_files.txt`.

    python tools/merge_copilot_files.py

The Copilot files, `copilot/[0-9][0-9]_*.txt`, are one per objective, each at most the 8,000
characters Copilot takes at once. For convenience, this writes them into one document as well,
in order, each under a line naming it: for reading them all at once, searching them, or a chat
that takes more than 8,000 characters. It is far over that limit, so it lives in a folder of its
own, which the per-file checks don't read. `tools/copilot_files.py` runs this after writing the
files, and a test holds the document to them.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COPILOT = ROOT / "copilot"
MERGED = COPILOT / "all_in_one" / "all_copilot_files.txt"
# What the document is, at its top, for someone who opens it before the README.
HEADER = ("Every Copilot file in one document, for reading or searching them together. It is\n"
          "many times the 8,000 characters Copilot takes at once, so it is not for Copilot: there,\n"
          "paste or attach the separate files in copilot/, as 00_start_here.txt says.\n\n")


def merged() -> str:
    """Every Copilot file, in order, each under a line naming it."""
    parts = [f"===== {path.name} =====\n\n{path.read_text(encoding='utf-8').rstrip()}\n"
             for path in sorted(COPILOT.glob("[0-9][0-9]_*.txt"))]
    return HEADER + "\n".join(parts)


def main() -> int:
    """Write the merged document into copilot/all_in_one/."""
    MERGED.parent.mkdir(exist_ok=True)
    MERGED.write_text(merged(), encoding="utf-8", newline="\n")
    print(f"Wrote {MERGED.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
