# The split into composer core

Type: task
Status: open
Blocked by: 01
Size: XL

## Question

`git mv` the shared files and CHANGES.md into `composer_core/`; delete spark_composer's copies;
write each Edition's thin `__init__.py` (import composer_core or stop, self-check, import
writing and engine, check_installed, plug, re-export), `composer_core/public.py` (the public
names) and `composer_core/checks.py` (the self-check across two folders). Edition files import
composer_core absolutely; Spark Composer's helper process finds composer_core. Simplify
tools/editions.py, tests/conftest.py and `use()`; delete tools/make_spark_edition.py, swap()
and the staleness tests; test_writers_agree loads Spark's writing.py by path; the export ships
composer_core. ADR 0003, CLAUDE.md "Two Editions", standards.md Parity, the drift hook's
watched folders.

## Done when

- Byte-identical goldens and galleries; importing both Editions refuses; a missing composer_core stops with "copy composer_core beside this folder".
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
