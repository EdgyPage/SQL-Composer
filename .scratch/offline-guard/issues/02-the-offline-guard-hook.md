# The offline guard hook

Type: task
Status: open
Blocked by: 01
Size: S

## Question

Plan step 2: `.claude/hooks/offline_guard.py`, a PreToolUse hook on Edit|Write|NotebookEdit that judges the file as the edit would leave it with `offline_policy` and denies with the findings; wired in `.claude/settings.json`; tested as a hook.

## Done when

- A Write or Edit adding network code is denied, a clean one passes, run as a hook.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
