# Build both Editions in the export, still shipping one

Type: task
Status: resolved
Blocked by: 15, 22

## Question

Make `tools/export_clean.py` able to build both folders, while `EXPORTED` still names only
`sql_composer`, so `main` can go on being re-exported as 2.1 until ticket 26.

- `build(source, into, when, editions=EXPORTED)`, with one `when` for every folder and
  `stamp_text(product, ...)`, so both folders carry the same export time and their own product.
- Per-Edition `_FILES` and the tiered import allowlist from `tools/editions.py`.
- A fresh-Python import of each stamped folder, with the other library blocked (importing
  `spark_composer` needs pyspark but no JVM).
- Checks: lockstep versions; generated copies current; the two Editions' descriptions equal
  apart from VERSION's value; the allowlist and the `git archive` cover the EXPORTED folders.
- Refusals: EXPORTED names a folder the commit lacks; the README names an Edition that isn't
  shipped.
- In `__init__`: a stamp reader that knows each product, and a stop for a file pasted in from the
  other Edition ("tables.py is from the other Edition"), tested both ways.

Tests build both Editions into a temp folder; the real export and `--preview` still produce the
sqlglot-only 2.1 tree.

## Done when

The Definition of done in `CLAUDE.md` holds; `tests/repo/test_export_clean.py` covers every new
refusal; `python tools/export_clean.py --preview <folder>` gives the same sqlglot-only tree as
before.

## Answer

`tools/export_clean.py` builds every Edition `EXPORTED` in `tools/editions.py` names, which is
still SQL Composer alone, so the real export and `--preview` give the same 2.1 tree as before
(`afc5fc2`; reworked in `e25c8ec` after the reviews and the beginner reader).

- **One build for each Edition.** Every folder gets one stamp time and its own product's name,
  its own `_FILES`, and its own import tier. Each stamped folder is imported in a fresh Python
  where the other Edition's library is `None` in `sys.modules`, so importing it fails loudly.
- **Checks across the Editions:**
  - each is in the commit (`committed_files` archives only the folders the commit has, so the
    build's refusal is the one you see);
  - one version, with a fix that says to set it in `sql_composer/`, run
    `python tools/make_spark_edition.py`, then set it in Spark's `writing.py` and `engine.py`;
  - Spark Composer's shared files are the copies `make_spark_edition.generated()` writes, read
    as text, so a checkout that writes CRLF passes;
  - both cheat sheets are the same but for VERSION's line, and a refusal names the first line
    that differs.
- **The allowlist and `git archive`** cover every exported folder.
- **The README template** may not name, in any spelling, an Edition the export doesn't ship.
- **The import self-check** reads either Edition's stamp. `__init__.py` knows the folder it
  belongs in, and every other file's stamp names its own, so a file from the other folder,
  `__init__.py` included, stops the import. The stop names every such file, the folder it came
  from and the folder it sits in, and says to copy the folder in again from its own folder of
  the download. `_stop` names the folder the import found. A folder is the Toolbox folder its
  name and its files' stamps agree on, so one you renamed imports as in 2.1 (`0d4dc38`); a
  renamed one is the folder most of its other files' stamps name, so a pasted `__init__.py`
  can't decide it (`0842be6`).
- **Tests:**
  - `tests/repo/test_export_clean.py` sets `EXPORTED` to both Editions and covers every new
    refusal: a missing folder (through `export()`), versions, a stale copy, cheat sheets that
    differ, the blocked library, and the README in four spellings. It also exports both
    Editions from a repo with `core.autocrlf` on.
  - `tests/test_import_self_check.py` pastes `tables.py`, `examples.html`, `CHANGES.md`, two
    files at once, and the other folder's `__init__.py`, in both runs.

**Not done, and why:**

- **`build()` takes no list of Editions,** where the spec wrote
  `build(source, into, when, editions=EXPORTED)`. Every function reads `editions.EXPORTED`
  when it is called, and the tests set it with monkeypatch. So nothing has to pass the list
  from function to function, which the review found speculative.
- **The README template's sentence on what stops the import** still leaves out a file from the
  other folder. A 2.1 export ships one folder, and ticket 26 rewrites the template for both
  (D73 said the same).

## Comments

**Code review (2026-09-30), `afc5fc2`.**

- **Fixed in `e25c8ec`:**
  - The stale-copy check compared LF text with the bytes `git archive` writes. Under
    `core.autocrlf`, which a fresh Windows install sets, those are CRLF, so the real two-Edition
    export was refused. It now compares text, through `make_spark_edition.generated(source)`,
    so the copy rule lives in one place.
  - A `__init__.py` pasted from the other folder made the stop name a healthy file and tell
    the user to delete the healthy folder. The check is now by the folder the file sits in.
  - The missing-folder refusal couldn't be reached from `export()`, since `git archive` failed
    first.
  - The version refusal sent the reader to edit generated copies and printed a dict.
  - Refusals without a fix now have one, and refusals name the folder of a bad file again.
  - The README check caught only two spellings.
  - The stamp is kept apart from the import's description.
  - Tests were added for the blocked library and for `export()` with both Editions.
- **Answered, not changed:**
  - `_PRODUCT` keeps its name. It is the product's name as the stamp writes it, which the
    glossary calls the Edition's name.
  - A stamp naming any "<word> Composer" is read as from another folder, named from its stamp.
    That is true of both real Editions, and a third is unlikely.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D73 | `afc5fc2` | `e25c8ec` |
| D74 | `e25c8ec` | `0d4dc38` |
| D75 | `0d4dc38` | `0842be6` |

**Beginner reader:** [report](../reports/24-beginner-reader.md), read at `afc5fc2`. The reader
built both Editions and made 18 paste mistakes in fresh Pythons.

- **Changed:**
  - Stop 1 (the costliest): the other folder's `__init__.py` now stops naming itself, the
    folder it came from and the folder the import found.
  - Stop 2: the fix says to copy the folder in again from its own folder of the download, not
    from the other.
  - Stop 3: the why says a `.py` file could make a Statement fail, and an `examples.html` or
    `CHANGES.md` may not describe the folder's code.
  - Stop 4: the stop says "folder", not Edition.
  - Stop 5: the package docstring lists a file from another Toolbox folder.
  - Stop 6: every such file is named.
- **Answered, not changed:**
  - Stop 7: a file of another version is caught by the version stop first. Its fix is the same,
    and the two Editions share one version.
  - Outside the brief: copying every file of one folder over the other's still imports, as the
    other folder under this one's name. It is whole and of one export, like a renamed folder,
    which must import as in 2.1 (D74, D75), and its `VERSION` says which it is.
