# The split into composer core

Type: task
Status: resolved
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

## Answer

Built in the commit that resolves this ticket (ADR 0003).

- `composer_core/` holds every shared file once, `CHANGES.md` too, plus three new files:
  `__init__.py` (the four-part message and `_stop`), `checks.py` (the import self-check, run on
  each folder, then across the two) and `public.py` (the public names). spark_composer's copies,
  `tools/make_spark_edition.py` and `swap()` are gone.
- Each Edition's `__init__.py` is the same apart from its names (a test holds it). Before
  importing anything of composer_core it checks the core is beside it and whole (its
  `__init__.py` and `checks.py`, and that its `__init__.py` isn't an Edition's); then it checks
  both folders and across them, imports and checks engine.py, then writing.py, plugs both into
  `edition.py`, and re-exports. engine.py comes first, before writing.py, since SQL Composer's
  writing.py imports sqlglot, which check_installed checks.
- Every import stop is headed by the folder you imported, even renamed; each message names the
  folder the problem is in.
- Each engine.py has a small `_stop`, so its stops name its own folder.
- `editions.use()` aliases the Edition package and its own two files (`writing`, `engine`): the
  tests import those by name, and the core needs no alias. The plan said "the top level only";
  the two files are the Edition's own, so aliasing them is what makes the shared tests run.
- The export ships `composer_core/`, stamped "Composer core <version>, exported ...", with its
  file list; the allowlist and README say two folders.
- The goldens are byte-identical. Both galleries changed in two intended places: the
  `__init__` docstring's paragraph about the two folders, and the GuardRefused and LoadRefused
  docstrings, whose tracebacks now say `composer_core.refusals...` and say how to catch them.
- Docs: ADR 0003 (ADR 0002 superseded in part), CLAUDE.md's "Two Editions" and Drift, CONTEXT.md
  (Composer core; Toolbox, Edition, Clean branch), standards.md's Parity, the README template,
  the beginner reader's brief, the drift reviewer's brief, the drift hook's watched folders.

**Code review (2026-10-05).** Standards: no hard violation; fixed the stop header (the folder
you imported, as before the split, so a renamed copy names itself), the stamp parsed in one
place, `version_of`'s docstring, tailored "why" lines for each folder, the engine.py blank lines,
writing.py's import order, the gallery tool's import order and long lines, a duplicated
stamping loop in the tests. Kept: the forwarders in edition.py (the seam) and the engines'
`_stop` wrappers (each names its own folder). Spec: fixed the drift reviewer's brief, the
mix-up refusal's message (an object from a leftover folder), the three broken-core cases (now
four-part stops, with tests), CLAUDE.md's Drift section, the README's gallery line.

**Beginner reader (2026-10-05).** Five stops; fixed: the header, "__init__.py" named with its
folder, the core called `composer_core` in messages, the README's "two folders" sentence and
"another Toolbox folder", how to catch GuardRefused and LoadRefused, and the unplugged refusal's
fix shows both import lines.

