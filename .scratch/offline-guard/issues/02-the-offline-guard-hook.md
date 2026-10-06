# The offline guard hook

Type: task
Status: resolved
Blocked by: 01
Size: S

## Question

Plan step 2: `.claude/hooks/offline_guard.py`, a PreToolUse hook on Edit|Write|NotebookEdit that judges the file as the edit would leave it with `offline_policy` and denies with the findings; wired in `.claude/settings.json`; tested as a hook.

## Done when

- A Write or Edit adding network code is denied, a clean one passes, run as a hook.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).

## Answer

Built in 61f38fc, fixed up after its code review in the commit that resolves this ticket.

- **The hook.** `.claude/hooks/offline_guard.py`, a PreToolUse hook wired in
  `.claude/settings.json` as its own entry (matcher `Edit|Write|NotebookEdit`) beside
  protect_main's. It works out the file as the edit would leave it: Write's content; Edit's file
  on disk (empty if none) with `old_string` replaced by `new_string`, once or with
  `replace_all`, matched as Claude Code matches it (CRLF read as LF, straight quotes matching
  curly ones), and when Claude Code would find no `old_string`, the new text alone, dedented;
  NotebookEdit's notebook with the cell replaced, inserted or deleted (by id or `cell-N`), or the
  new cell alone if the notebook or cell can't be found. It judges that text with
  `offline_policy.findings_in` under the file's path in its checkout, and refuses with each
  finding as `file:line kind: code`, one plain line each (control characters and line
  separators stripped, 160 characters, at most 20 then "... and N more"), then the way through:
  the Toolbox reaches nothing but `send`; a reviewed site goes in ALLOWED with a reason and the
  user's OK. User-copied folders say instead that nothing is allowed there. It never imports or
  runs the edited code and starts no process.
- **Which checkout.** The session's project is `$CLAUDE_PROJECT_DIR` (or the hook's own
  checkout); a file in `.claude/worktrees/<name>/` is judged at its path in that worktree, by
  that worktree's own policy, so an ALLOWED entry added in a worktree counts there. A file
  outside the project, or of a kind or in a folder the policy doesn't read
  (`offline_policy.is_read`, new), passes. `tools/offline_policy.py` itself is judged as
  maintainer code, so ALLOWED can be edited.
- **Code that doesn't parse** is refused in the Toolbox and user-copied code (it could hide
  anything), and passes elsewhere, where tools and tests may be mid-change.
- **The fail rule.** Fail closed for a file the policy reads in the Toolbox or user-copied code
  (`STRICT_FOLDERS`, held to the policy's by a test, so it works when the policy won't load):
  an unreadable file or a broken policy refuses the edit and says why. Fail open elsewhere, with
  a stderr note and exit code 1 (Claude Code shows it without blocking), so a broken policy never
  refuses the edit that fixes it. Input that isn't a call names no file, so it fails open too.
- **Shared hook code.** `.claude/hooks/hook_io.py` (new) holds `read_hook_input`, which now reads
  stdin as UTF-8 bytes (a piped stdin on Windows decodes in cp1252, so an Edit with non-ASCII
  text didn't match), `plain_line` and `deny`; protect_main, drift_review and drift_stop use it.
- **The tests.** `tests/repo/test_offline_guard.py`, 27 tests running the hook as a hook, each
  seen red: every case the brief listed, plus whole-file judging, replace_all, CRLF, curly
  quotes and UTF-8 matching, edits not found, unparseable code, a declared encoding, notebooks
  (replace, insert, markdown, delete, a broken cell), plain lines, worktrees, planted checkouts,
  the policy file, a folder named in capitals, and the fail rule both ways. Two ALLOWED entries
  cover its `subprocess` import and its `run_hook`. `test_offline_policy.py` gains three (an
  encoding cookie, `.pyw`, no skipped folder in the strict folders).
- **Live.** The session's hooks come from the main checkout, which hasn't this hook yet, so an
  Edit adding `import requests` to `composer_core/running.py` in the worktree went through (it
  was reverted at once). The same call piped to the worktree's hook is denied with
  "composer_core/running.py:12 network: import requests" and the way through. It will fire live
  once merged to dev.

**Code review (2026-10-06).** The spec review found bypasses, all fixed test first:

- A `.git` planted inside the Toolbox made its folder a checkout with no policy: the checkout is
  now the project, or a worktree in `.claude/worktrees/`, never the nearest `.git`.
- A `pyvenv.cfg` (or a folder named like a cache) inside the Toolbox hid its files from the
  hook and the export: the policy now skips no folder in the Toolbox or user-copied code.
- Unparseable code hid every finding, including a notebook whose one broken cell hid the
  others: refused in the strict folders (above).
- `# coding: utf-7` hid a line from the policy: a file declaring any encoding but UTF-8 is now
  "unreadable". `.pyw` files are now read as Python.

The standards review's smells: the duplicated `plain_path` and deny JSON went into `hook_io.py`
(above), and `read_hook_input` left drift_list for it; `reads` was renamed `is_read`, and the
hook's `read`, `refusal` and `alone` became `text_on_disk`, `why_refused` and `new_cell`; the
file path travels as a `PurePosixPath`; the docstring says "policy" for "rule", which the
glossary avoids. Kept: the hook's own copy of the strict folders (needed when the policy won't
load; a test holds it). Left for ticket 05: the name "offline guard" beside the glossary's
**Guard**, the user's choice in the map. Not done: the policy still reads a notebook's cells as
one text (a broken cell now refuses the edit in the strict folders); MultiEdit, if a Claude Code
still has it, isn't matched, as protect_main's matcher doesn't match it either.
