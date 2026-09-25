# How does the Toolbox survive being pasted over an existing directory?

Type: grilling
Status: open
Blocked by: -

## Question

At work the user pastes files on top of an existing directory, overwriting on a name clash. Their
own scripts sit beside the Toolbox and import it laterally. Pasting never deletes anything, so a
Toolbox file that is renamed or removed in a later version stays behind, still importable, quietly
serving old code.

Decide:

- the Toolbox's shape - one file, a few flat files, or a package directory;
- names that cannot collide with the user's own files;
- what happens to a removed or renamed file - a frozen file list, an import-time check for stray
  files, or an explicit "delete these" note with each drop;
- how the user tells which Toolbox version is installed.

Keep the copy cheap: every file is a manual paste.
