# One folder, version 6.0

Type: task
Status: resolved
Blocked by: 02
Size: L

## Question

Map Notes, "Spark and the one Toolbox". Move every `composer_core/` file into
`sqlglot_composer/` (imports become relative within the one package; `edition.py`'s indirection
folds into its callers where it only chose an Edition). Remove `tools/editions.py` and what
reads it, the name swap, and the tests that held two Editions alike. Raise `TOOLBOX_VERSION` to
`6.0` in every file, start CHANGES.md's `## 6.0`, and ship CHANGES.md at main's top. Update
CLAUDE.md (one pytest run, two CI jobs, no Editions section, the toolbox-6 map), CONTEXT.md
(drop Edition and Composer core; Toolbox is one folder; Clean branch and Toolbox version
reworded), and `.claude/hooks/drift-reviewer.md` (no parity kind). Write the ADR that supersedes
0003.

## Done when

- `from sqlglot_composer import *` works from a Project holding only `sqlglot_composer/`.
- The export builds main from the one folder.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

The version moved to 6.0 earlier, in `6d4e971` (ticket 11, for drift item D193), and CHANGES.md
started its 6.0 section there; this ticket did the rest, on the branch `toolbox-6/03-one-folder`.

- `composer_core/`'s files moved into `sqlglot_composer/`; its `__init__.py`'s helpers
  (`_four_part_message`, `_stop`) are now `sqlglot_composer/__init__.py`'s, which checks one
  folder. `edition.py` is gone: the files import `writing.py` and `engine.py` directly, the
  folder's name is `_FOLDER` in `__init__.py`, and lineage reads `VERSION` from the package.
  `checks.check_together` and the stops for a missing or wrong `composer_core` are gone; a
  folder missing `checks.py` stops in `__init__.py` itself.
- `CHANGES.md` is at the repo's top and ships at main's top, unstamped, beside `LICENSE` and
  `requirements.txt`; the import self-check no longer lists it.
- `tools/editions.py` is replaced by `tools/toolbox_registry.py` (the folder's name, product,
  files, pages, and what each file may import); its tests and `test_two_editions.py` and
  `test_edition_seam.py` went, `test_import_self_check.py` was rewritten for one folder.
- The export ships the Example projects and Templates at dev's paths, not one folder deeper per
  Edition, so their `PYTHONPATH=../..` holds on main.
- CONTEXT.md drops Edition and Composer core (both now avoid-words of Toolbox); CLAUDE.md, the
  drift reviewer and the beginner reader name one folder; ADR 0009 supersedes ADR 0003.

### Reviews

- Spec (2026-10-20): import order safe, no cycle from removing `edition.py`. Two gaps fixed in
  the follow-up commit: the export now also imports the stamped folder copied on its own
  (`check_imports_alone`, the old "copied without composer_core" check's successor), and refuses
  an `__init__.py` with no TOOLBOX_VERSION instead of failing on it. CHANGES.md's Spark note no
  longer says to copy a `composer_core`. The README's Update and history sections are ticket 04's.
- Standards (2026-10-20): "Edition", now an avoid-word, left the code's names:
  `refuse_what_another_folder_made`, `tests/sqlglot_checks/`, and three test names; ragged
  lines rewrapped. Kept on purpose: the self-check's vote over each file's stamp, which is what
  names a pasted-in old `composer_core` or `spark_composer` file, and the registry's per-file
  import rule (only `writing.py` and `engine.py` may import sqlglot).
- Beginner reader (2026-10-20): CHANGES.md's two-folder leftover, "Edition" in CHANGES.md and the
  README's 3.x section, the plural "Toolbox's folders" and the unclear PYTHONPATH from
  `table_references/` in both Example project READMEs and how-to 15, the README's 5.x step order,
  and a note for imports that named `composer_core` directly, all fixed in the follow-up commit.
