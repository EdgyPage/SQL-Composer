# Records local only, and no local paths in git

Type: task
Status: open
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
