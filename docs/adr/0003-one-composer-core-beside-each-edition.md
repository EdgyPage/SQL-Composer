# The two Editions share one Composer core folder, instead of a generated copy each

Status: accepted

ADR 0002 built the Toolbox twice, as two folders that each held every file: SQL Composer's
shared files were written by hand, and Spark Composer's were generated from them with the
folder's and product's names swapped, and a test failed while a copy was stale. On 2026-10-05
the user asked to share as much as possible between the two, to stop them drifting and to
simplify testing, and said copying two folders at work instead of one was fine.

So every file both Editions run is now written once, in `composer_core/`, the Composer core:
every function a user calls, the import self-check and `CHANGES.md`. Each Edition's folder
holds only what is its own: `writing.py`, which turns a Statement into Hive, `engine.py`, which
checks the library and runs the Example database, its Example gallery, and a short
`__init__.py`. That `__init__.py` checks both folders, plugs its `writing.py` and `engine.py`
into the core's `edition.py`, and re-exports the public names, so a user still writes
`from sql_composer import ...` or `from spark_composer import ...`. At work, the user copies
`composer_core` and one Edition's folder, side by side.

This supersedes ADR 0002's generated copies, and its sentence that every other file of
`spark_composer` is generated from `sql_composer`'s. The rest of ADR 0002 stands: the tree the
Toolbox owns, the printer Spark Composer writes, sqlglot as that printer's oracle, and the
declared differences.

## Considered options

- **Keep the generated copies.** One folder to copy, but every shared change had to be
  regenerated, and a stale copy was caught only by a test. The user preferred two folders.
- **One folder that detects its library.** ADR 0002 rejected it: the import self-check couldn't
  say which library a copy needs. Here each Edition still has its own folder, named for its
  library, so the self-check can say so.
- **A neutral import line, `from composer import *`**, with the core finding the one Edition
  folder beside it. Every example and template would then ship once, but the Edition would be
  chosen by which folder was copied, not by the import line. The user chose the Edition's
  folder as the import line.

## Consequences

- A Python runs one Edition: the core holds one plugged-in Edition, and importing the second
  stops, saying to use one per notebook.
- The core's docstrings name SQL Composer. Spark Composer's Example gallery and its doctests
  read them with the names swapped, as its Worked examples always were.
- The import self-check runs on both folders, and stops if the two come from different versions
  or exports.
- The export ships `composer_core/` beside both Editions' folders, and the README says to copy
  two folders.
- Ticket 03 of the 4.0 work then renamed SQL Composer's folder `sqlglot_composer`, and its
  product name sqlglot Composer, to match `spark_composer`, as the user asked (2026-10-05). The
  names above are as they were when this was decided.
