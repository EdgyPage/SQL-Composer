# Beginner reader: Toolbox 7.2 ticket 01 (version.txt and the import self-check)

Read 2026-10-26 at e04f477, on the `__init__.py` docstring, the README template's Update section,
CHANGES.md's `## 7.2`, and every message in `tests/test_import_self_check.py`, each seen for real
by importing broken copies. Saved by the session (the reader writes no file). Line numbers are
e04f477's.

## What read cleanly

- The missing `version.txt` stop: clear, with a concrete fix.
- The missing-file and extra-file stops: unchanged and clear.
- Several changed files named in one warning ("engine.py, examples.html, writing.py differ").
- A copy saved with Windows line endings: no false warning.
- The warning points at the user's own import line, not a Toolbox file.

## Stops, in reading order

1. `__init__.py:9` and README: "if its version.txt is missing or from another Toolbox folder".
   There has been one Toolbox since 6.0, so when is there another? A reread and a lookup.
2. `__init__.py:11` and README: "edited by hand or pasted from another one": another file, or
   another download? A moment.
3. README Update step 1: "Note which version you have: `sqlglot_composer.VERSION` says". If the
   import stops, `VERSION` can't be read; nothing says to read `version.txt`'s first line.
4. CHANGES 7.2: "Copy the folder in over 7.1's ... Delete the old folder first": copy over and
   delete first contradict; the reason given doesn't explain why deleting matters.
5. CHANGES 7.2: "with its git hash" (do I need git at work?) and "a new version changes only the
   files whose code changed" (a maintainer's reason, which reads like leave to copy only the
   changed files).
6. CHANGES 7.2: "`TOOLBOX_VERSION` and `VERSION` give the same answers as before": they give 7.2.
7. CHANGES 7.2 with the warning's Why: a mixed folder that "could come out wrong" used to stop
   and now warns; nothing says why that is safe now.
8. The warning's What: "as version.txt lists it" first read as "version.txt lists it as
   differing".
9. The warning's Usual fix and Opt-out: if the change was meant (a fix a colleague made), nothing
   says what to do, and the warning returns at every kernel start. Its `UserWarning` isn't the
   glossary's Warning, which runs while a Statement is composed and has an opt-out.
10. The unreadable `version.txt` stop: "such as \"sqlglot Composer 7.2\"" is a literal that will
    read oddly on 8.0.
11. The "from another Toolbox" stop, met for real with a UTF-8 BOM on line 1 (old Notepad, or
    PowerShell 5's `Set-Content -Encoding UTF8`): "version.txt is from <a byte-order mark>sqlglot Composer",
    a false diagnosis. `utf-8-sig` would read it.
12. The extra-file stop when the new folder is dragged into the old one: it calls a folder a
    "file", and the download "left over from an earlier version". Older logic.
13. Editing `version.txt` to quiet the warning: one hash line deleted makes that file "extra";
    all deleted turns every check off. The file says "don't edit", so low.
14. `--preview`'s cheat sheet shows `VERSION` as "not exported (dev)": the preview's export line
    didn't match the self-check's pattern.

## The three costliest

1. Stop 9: no next step for a change made on purpose, and the word clash with Warning.
2. Stop 11: a BOM or typo in line 1 gives a false diagnosis about another Toolbox.
3. Stops 4, 5 and 7 together: the update path is unclear.

## What the session did

- 3: the Update step says to read `version.txt`'s first line when the import stops.
- 4, 5, 6, 7: the CHANGES step is "delete, then copy the whole folder"; no "git hash", no
  maintainer's reason; the version names say 7.2; it says why a differing file now only warns.
- 8, 9: the warning says "differs from the file the 7.2 download holds", and what to do when the
  change was meant: keep the change in a script of your own beside the folder.
- 10, 11: `version.txt` is read as `utf-8-sig`, and a first line naming anything but sqlglot
  Composer and a version gets one stop, with no claim of another Toolbox.
- 1, 2: "from another Toolbox folder" goes; "pasted from another download".
- 14: fixed with the drift reviewer's finding (`from dev commit .+`).
- 12, 13: left; the user decides. The `UserWarning` name is Python's own, and stays.
