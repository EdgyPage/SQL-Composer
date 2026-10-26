# The Toolbox's version lives in one file, with each file's hash

Status: accepted 2026-10-26, to be built by Toolbox 7.2; replaces v2's per-file version line
and line-1 export stamp (`.scratch/sql-composer-v2/issues/05-how-does-the-toolbox-survive-an-overwrite-install.md`)

Since v2 every Python file of the Toolbox has carried `TOOLBOX_VERSION = "7.1"`, and the export
has written a line 1 into every file, `# sqlglot Composer 7.1, exported ... - generated from dev,
do not edit`. The import compares both across the folder and stops on a file that disagrees, so
a paste that mixes two versions is caught. The user asked for the per-file line in v2, so that
dev tested end-to-end consistency explicitly.

On 2026-10-26 the user asked for both to go: "It's becoming exhausting to examine every single
file change when the line is just a version number change." A version raise touches every file
on dev, and every export touches every file on `main`, whatever changed.

So in 7.2:

- **`sqlglot_composer/version.txt` holds the Toolbox and its version**, `sqlglot Composer 7.2`,
  and nothing else on dev; naming the Toolbox lets the import stop on another Toolbox's file.
  The export adds the export's date and time, the dev commit it came from, and one line per
  other file of the folder with that file's git hash, the value `git hash-object` gives, which
  Python's `hashlib` works out without git. Both sides hash a file with its line endings as LF,
  so a copy saved with Windows line endings matches.
- **No file of the folder names the version or carries a stamp.** `TOOLBOX_VERSION` and
  `VERSION` stay public names, read from `version.txt`.
- **The import's self-check reads `version.txt`.** A file missing from the folder, or one in it
  that `version.txt` doesn't list, still stops the import, since it breaks imports outright. A
  file whose hash isn't the one listed warns, naming each such file: a file edited by hand and
  one pasted from another version look the same, and either may still work. A dev folder, whose
  `version.txt` lists no hashes, skips the hash check.
- **A version raise is one line in one file**, and an export changes only the files whose
  content changed, and `version.txt`.

## Considered options

- **Keep the per-file line, stop the stamp.** Rejected: a version raise would still touch every
  file, the half of the noise that lands on dev.
- **Keep both, and teach the drift reviewer and the diffs to skip them.** Rejected: the noise is
  in every diff the user reads, not only the reviewer's.
- **Stop on a hash that doesn't match, as the version line did.** Rejected by the user's "warn
  just to ensure compatibility": with hashes, a file edited at work stops the import as a file
  from another version would, and the warning names it either way.
- **The export commit alone, no per-file hashes.** Rejected: one commit can't say which file of
  a mixed paste is the odd one out.

## Consequences

- The self-check, the export, `tools/toolbox_registry.py`, the tools that stamp pages and the
  Example projects' Lineage footers, and the tests that read either mark all change.
- The drift reviewer's version item asks about `version.txt`'s version line; it still never
  raises it.
- A Project records its own version beside it, in `admin/project_version.txt`, which an Upgrade
  compares with `version.txt`.
