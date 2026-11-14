# Records local only, and no local paths in git

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

The user: "I want good evaluation instructions to be passed around from machine to machine, the
actual records don't need to be shared at all." And: "Let's make it a rule from now on not to push
that stuff." (Q9, Q11, Q12.)

## Done when

- `.gitignore` holds `.eval-local/`.
- **Untracked, kept on disk** (`git rm --cached`, moved under `.eval-local/`): every usability
  and Copilot evaluation run folder, the memo, `results.md` files and round summaries, and any
  other record a pipeline writes. Instructions stay tracked: tools, `docs/`, `.claude/agents/`,
  tasks with their keys, tests, maps and tickets.
- **Tracked files hold no local path:** the five old reports and tickets that quote full paths
  (`.scratch/spark-edition/reports/09-beginner-reader.md`, `24-beginner-reader.md`,
  `26-beginner-reader-spark.md`, `.scratch/sql-composer-v2/reports/22-beginner-reader.md`,
  `.scratch/toolbox-7/issues/15-usage-tests-and-a-ranking.md`, `16-dead-and-stale-code-out.md`)
  have each path made relative or replaced with `<user folder>`.
- **A test** reads every tracked file and refuses one holding an absolute user path
  (`C:\Users\<name>\`, `C:/Users/<name>/`, `/c/Users/<name>/`, a `/home/<name>/`), the user's
  folder name, an AppData, Temp or scratchpad path, or an email address, with an allowlist for the
  tests that name these patterns to check for them.
- **A commit hook** runs the same check on staged files and refuses the commit; the export to main
  runs it on the Clean tree.
- CLAUDE.md names the rule and `.eval-local/`.

## Answer

Built 2026-11-14: `tools/local_paths.py` (the one reader), `.claude/hooks/local_paths_hook.py`
(registered in `.claude/settings.json`), `tests/repo/test_local_paths.py` and
`tests/repo/test_local_paths_hook.py`, `check_local_paths` in `tools/export_clean.py`, and a
section in CLAUDE.md.

**Untracked, kept on disk** (`git rm --cached`; also git-ignored at these old paths, since the
pipelines still write there until tickets 03 to 05): `.scratch/usability-loop/runs/`,
`.scratch/usability-loop/results.md`, `.scratch/copilot-eval/runs/`,
`.scratch/copilot-eval/memo/`, `.scratch/copilot-eval/results.md` (18,000-odd files).
`.scratch/copilot-eval/excel-files-11-12-misses.md` stays tracked: it is a findings note, and
the check passes it.

**After merging, the parent's step:** a merge deletes the untracked files from the main
checkout, so run `.venv/Scripts/python tools/eval_runs.py copy-records` there BEFORE merging. It
copies those paths into `.eval-local/` (`usability/runs`, `usability/results.md`,
`copilot/runs`, `copilot/results.md`, and the memo through `carry-over` into `memo/`), skips a
file already there and deletes nothing.

**The check's rules** (`tools/local_paths.py`): an absolute user path (`C:\Users\<name>`,
`C:/Users/<name>`, `/c/Users/...`, `/Users/...`, `/home/...`) unless the name is a placeholder
(`<...>`, `$`, `%`, `{`, `...`, `*`, `name`, `user`, `username`, `you`, `me`); the user's
folder name as a whole word, read at run time from the folder after `Users` or `home` in the
repo's own path (not `Path.home` or `getpass`, which the code audit refuses, so no AUDITED entry
was needed), and not held in the repo; an AppData `Local|Roaming|LocalLow`, `Temp/claude` or
`/scratchpad/` path; an email whose domain isn't example.com, .org, .net, anthropic.com or
users.noreply.github.com. A file that isn't UTF-8 isn't read. `NAMES_THE_PATTERNS` lists the
files that name the patterns to check for them: the module and its two tests, and
`tests/repo/test_code_audit.py`.

**Where it runs:** the test reads every file `git ls-files` gives; the hook refuses a
`git commit` (any `git ... commit`) on the staged files as they lie on disk, and, when the
command also runs `git add` or `commit -a`, on every modified and untracked, not-ignored file;
`export_clean.build` runs `check_local_paths` on the Clean tree before the allowlist check.

**De-pathed** (paths relative, `<user folder>` or `<scratchpad>`): the six named files, and by
the test `.scratch/spark-edition/reports/23-beginner-reader.md`,
`.scratch/toolbox-5/orchestration.md` and `.scratch/drift.md` (D451).

**Left for tickets 03 to 05** (they still point at the old record folders, now ignored, and
write there): `tools/usability_loop.py`, `tools/copilot_eval.py`, `tools/copilot_eval_tasks.py`,
`tools/excel_eval.py`, `tools/metric_eval.py`, `tests/test_eval_memo.py`, `docs/usability-loop.md`
and `docs/copilot-eval.md`. Moving them to `.eval-local/` is those tickets' work; the history
scrub is ticket 10.

**Decided:** the hook reads the staged files from disk, not the index, because the repo's one
git helper (`drift_list.git`) returns text, and a new subprocess site needs an ALLOWED entry. A
commit made with the user's own hand isn't hooked; the test catches it.
