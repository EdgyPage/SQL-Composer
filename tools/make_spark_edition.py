"""Write Spark Composer's shared files from SQL Composer's. Run it after editing `sql_composer/`.

    python tools/make_spark_edition.py

Each shared file goes through `editions.swap()`, which changes the folder's and the product's
names and refuses anything it can't be sure of; `CHANGES.md` is copied as it is. The Edition
files, `writing.py` and `engine.py`, are Spark Composer's own and are left alone, and so is its
`examples.html`, which `tools/example_gallery.py --edition spark` writes. Running this twice
changes nothing. A test fails while a copy is stale, and names this command.
"""

from __future__ import annotations

import sys
from pathlib import Path

import editions

ROOT = Path(__file__).resolve().parent.parent
COMMAND = "python tools/make_spark_edition.py"


def generated() -> dict[str, str]:
    """Each generated file of Spark Composer's folder, by name, as it should read."""
    source = ROOT / editions.SQL_COMPOSER.folder
    return {name: editions.swap((source / name).read_text(encoding="utf-8"), name)
            for name in editions.SHARED_FILES + editions.VERBATIM_FILES}


def main() -> int:
    target = ROOT / editions.SPARK_COMPOSER.folder
    target.mkdir(exist_ok=True)
    try:
        files = generated()
    except editions.SwapRefused as refused:
        print(f"Nothing was written: {refused}", file=sys.stderr)
        return 1
    for name, text in files.items():
        (target / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {len(files)} files in {editions.SPARK_COMPOSER.folder}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
