# One version file, at 7.2, and the ADRs

Type: task
Status: open
Blocked by: -
Size: L

## Question

The user (2026-10-26): "let's move all the version numbers out of every file out of the files
themselves and in to a text file in the folder location with git hashes. It's becoming
exhausting to examine every single file change when the line is just a version number change."
And 7.2 is the user's number for this round. ADR 0013 records the design; ADR 0014 was drafted
with the map and lands here too.

## Done when

- `sqlglot_composer/version.txt` exists. On dev it holds the version, `7.2`, and nothing else.
  The export adds the export's date and time, the dev commit it came from, and one line per file
  of the folder with its git hash, the value `git hash-object` gives, worked out with `hashlib`.
  The format is plain lines a person can read, and the README's file map names the file.
- No file of `sqlglot_composer/` holds a `TOOLBOX_VERSION = ...` line, and the export writes no
  line-1 stamp into any file. `TOOLBOX_VERSION` and `VERSION` stay public, read from
  `version.txt`; `__init__.py`'s doctest shows `'7.2'`.
- The import's self-check (`checks.py`) reads `version.txt`: a file missing from the folder, or
  one `version.txt` doesn't list, stops the import as now; a file whose hash differs warns, once,
  naming every such file and the usual fix (paste it again from the download). A `version.txt`
  with no hashes, as on dev, skips the hash check. A folder with no `version.txt` stops, saying so.
- `tools/export_clean.py`, `tools/toolbox_registry.py`, `tools/example_gallery.py`,
  `tools/how_to_page.py`, `tools/example_project.py` and the tests that read either mark
  (`tests/test_import_self_check.py`, `tests/repo/test_toolbox_checks.py`,
  `tests/repo/test_export_clean.py`, `tests/test_docstrings.py`, `tests/test_how_tos.py`,
  `tests/repo/test_dead_code.py`) read or write `version.txt` instead. A test holds that the
  version is written in one place on dev.
- The drift reviewer's version item (`.claude/hooks/drift-reviewer.md`) asks about
  `version.txt`'s version; CLAUDE.md's Drift section says where the version lives. Neither
  raises it.
- Everything that names the current version says 7.2: CONTEXT.md's Toolbox version, the
  clean-branch README template, the tools' pages, the Example projects' Lineage footers
  (regenerated). CHANGES.md has a `## 7.2` with a "To update from 7.1" part holding the
  copy-and-restart step, which ticket 02 completes, and a line saying the version moved to
  `version.txt`.
- ADRs 0013 and 0014 committed as drafted, or as the review leaves them. ADR 0006's Status says
  0014 extends it.
- CLAUDE.md's Definition of done. Nothing a beginner sees changes but the version and the
  import's warning: the beginner reader reads the new warning and stop.

## Glossary

CONTEXT.md's **Toolbox version** becomes:

> The feature number of the Toolbox (`7.2`), raised only when a big feature lands, and written in
> one place: the Toolbox folder's `version.txt`, which also lists each of its files' hashes. Two
> copies of the same Toolbox version are told apart by when they were exported.
> _Avoid_: release, build, hash
