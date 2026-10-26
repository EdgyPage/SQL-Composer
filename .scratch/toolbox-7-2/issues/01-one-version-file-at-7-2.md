# One version file, at 7.2, and the ADRs

Type: task
Status: resolved
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

## Answer

Built 2026-10-26 on dev (e04f477; review fixes in the next commit).

- `sqlglot_composer/version.txt` holds `sqlglot Composer 7.2` on dev: the Toolbox's name as well
  as the version, so the import can tell a `version.txt` that isn't this Toolbox's (ADR 0013
  says so now). The export adds `exported <time> from dev commit <hash>`, two `#` comment lines
  for a reader, and `<git hash>  <name>` for every other file. Both sides hash with line endings
  as LF, so a copy saved with Windows line endings matches (ADR 0013 says so now).
- No `TOOLBOX_VERSION = ...` line in any file; `__init__.py` reads `TOOLBOX_VERSION` and
  `VERSION` from `version.txt`. The export writes nothing into the folder's own files: no stamp,
  no `_FILES` list. The Example projects keep a line-1 stamp, now naming the version alone
  (`sqlglot Composer 7.2 - copy it, then edit your copy`), so an export changes them only when
  the version changes; "no line-1 stamp" is read as the Toolbox folder's files, as ADR 0013
  says. The README keeps its stamp: one file, which names the export time anyway.
- The import stops on a missing or extra file, a missing `version.txt`, or one whose first line
  isn't `sqlglot Composer` and a version (read as `utf-8-sig`, so a byte-order mark is fine);
  it warns once, naming every file, on a hash that differs.
- The export refuses a file in the folder that `tools/toolbox_registry.py` doesn't list: the
  per-file version line used to catch a stray module, and the hash list can't, since the export
  lists whatever the folder holds.
- 7.2 named everywhere the current version is; CHANGES `## 7.2`; CONTEXT's Toolbox version; the
  README's file map and Update; the drift reviewer's version item; CLAUDE.md's Drift section;
  ADR 0006's Status.
- `tests/upgrade_from/7.1/` (the 7.1 Example projects, frozen, without Lineage pages) is in the
  same commit as the review fixes, for ticket 02; the dead-code and suite-layout tests and ruff
  leave it out.

## Reviews

- Standards (2026-10-26): fixed: `build_folder` returns the hashes, no callback; one pattern
  reads dev's `version.txt` (`DEV_VERSION_FILE`); `VersionFile` is a NamedTuple and the argument
  is `version_file`; the glossary no longer says "hashes" beside its _Avoid_ of hash. Answered:
  `git_hash` is in `checks.py` and the export on purpose, since the Toolbox can't import a tool,
  and `test_the_hash_is_gits_own` holds both to git's value; ADR 0006's Status is this ticket's
  "Done when".
- Spec (2026-10-26): fixed: the README's file map names `version.txt`; `test_dead_code.py`'s
  note. Answered above: the product name in `version.txt`, the Example projects' stamp, the
  registry check, the LF hashing (both now in ADR 0013). `test_docstrings.py` and
  `test_how_tos.py` read `TOOLBOX_VERSION` from the package and needed no change.
- Beginner reader: [reports/01-beginner-reader.md](../reports/01-beginner-reader.md). Taken:
  stops 1 to 11 and 14, as the report's last section lists; left for the user: 12 (a folder
  dragged into the old one) and 13 (editing `version.txt`).
- Drift: e04f477 clean. The drift reviewer's note that a preview's `version.txt` read as "not
  exported (dev)" is fixed, with a test.
