# Toolbox 5.0 orchestration: checkpoint

A fresh session picking up the Toolbox 5.0 build reads this first, then `CLAUDE.md` and the
map's Notes and "Decisions so far". The session that writes it updates it at each milestone
(a merge, a wave's start or end, a user decision, a CI result).

Last updated: 2026-10-16. Waves 1-2 merged; the user answered wave 2's questions and set the Spark CI failures aside. Wave 3: one agent applies the two decisions, then ticket 09 (no export).

## The plan (the user's brief)

- Waves by "Blocked by:": wave 1 = 01, 02, 03; wave 2 = 04, 05, 06, 07, 08; wave 3 = 09.
- One worktree subagent per ticket in a wave, in parallel. Each resets to `dev`, works TDD in
  both Editions, runs the five checks (ruff; pytest; pytest --edition spark with JAVA_HOME;
  low sqlglot 25.24.2; tools/offline_policy.py) with exit codes checked, runs the code-review
  skill and the beginner reader in the foreground, appends `## Answer`, sets Status: resolved,
  adds a map "Decisions so far" line, and commits on its own branch only.
- The orchestrator merges each finished branch into `dev` with `--no-ff`, starts a drift
  review subagent ("Read .claude/hooks/drift-reviewer.md and follow it for commit <sha>"),
  fixes its items as the next commits, runs the three test runs on merged `dev` before the
  next wave, pushes `dev` when green, and checks CI's four jobs via GitHub's public API.
- Never raise TOOLBOX_VERSION before ticket 09 (the user chose 5.0); never export or push
  `main`. A new ALLOWED entry in tools/offline_policy.py needs the user's OK.

## Where it stands

Last checked: 2026-10-15, evening; `dev` local tip 289a8bb. `origin/dev` is at f1c8aaa
(all of waves 1 and 2), CI run 38865605762.

| Ticket | Branch (worktree `.claude/worktrees/agent-<id>/`) | State |
|---|---|---|
| 01 Keys | `worktree-agent-a6d7b135a93d73477` | merged (2b944b7); drift fixes merged (5b24a4c, 34f0f77) |
| 02 The Saved table's storage | `worktree-agent-a6f3bd488edfd2022` | merged (3a83175); drift fixes 84c32fd |
| 03 Session settings, Unchecked statement, Admin log | `worktree-agent-af9eba55aa5919751` | merged (641a749); drift fix c5e251c |
| 04 The admin module | `worktree-agent-a488bd9fe0f586e60` | merged (958408f); drift fixes D173-D178 merged (2883021, closed) |
| 05 Joins | `worktree-agent-aa687d203297246a7` | merged (cdcd71e); drift fixes D169-D172 merged (3ca3e7e, closed) |
| 06 Windows | `worktree-agent-a645f39d46eaedee7` | merged (e523617), drift fixes D166-D168 merged (f7f2e04, closed) |
| 07 Stacking and subtotals | `worktree-agent-af1a5baa3f9895606` | merged (5a329a1; how-tos 35, 36; 86 names); drift D179-D180 fixed by 8406f79 |
| 08 Upkeep and speed | `worktree-agent-a0f9ffdeaa6cbfa6a` | merged (6396219); drift fixes D181-D182 merged (fdafa76), D183 fixed (a655ac2) |
| 09 Ship 5.0 | `worktree-agent-a4c3d9aa4d966c508` | agent running: Part A applies the user's two decisions (kept_day narrowed to Windows; map_joins sends hive.ignore.mapjoin.hint=false), Part B raises TOOLBOX_VERSION to 5.0, CHANGES and README; no export. Then merge, close D156 with its version commit, drift review, three runs, push |

A fresh session can't message these agents (their ids live only in the session that started
them). For a branch whose agent never reported: check `git -C <worktree> status`, `git log
dev..<branch>` and the ticket's Status line in the worktree; finish it with a new agent in
that worktree (commit or stash what's there first), or merge it if it's resolved and its
checks pass.

Drift open: only D156 (`version`, closed by ticket 09 raising TOOLBOX_VERSION to "5.0"; the
stop hook nags about it each turn, which is expected).

## The user's answers to wave 2's questions (2026-10-16)

The user took every recommendation (recorded in the map's Decisions): narrow `kept_day` to
Statements with a Window; "map_joins" also sends `hive.ignore.mapjoin.hint=false`; everything
else as built. The Spark CI failures are set aside for now, by the user: ticket 09 goes ahead
without CI green, and still never exports or pushes `main`.

## Open problem: CI red for Spark Composer

Run 38815958379 on 849b3c1: both sqlglot jobs passed; both Spark jobs (pyspark 3.5.0 and
4.0.4) failed in the pytest step. Job logs need admin rights (public API gives 403) and the
annotations only say "exit code 1"; the user was asked to paste the failing pytest summary.
Suspect: the Linux-only (NEEDS_WINUTILS) tests in `tests/spark_edition/`, chiefly
`test_spark_hive_tables.py` and `test_spark_reads_the_hive.py`, changed by tickets 01 and 02
and never run locally (no WSL or Docker on this machine).

## The user's decisions so far (also in the map)

- Spark Composer leaves `PRIMARY KEY` out of create_table (declared difference `primary_key`).
- `hive_settings(..., sets=HIVE_SETTINGS)` and `set_admin_log(ADMIN_LOG)`: passed in, as built.
- Each Saved table's Table reference writes its own `location=` (no BASE_LOCATION).
- Indexing: satisfied with the map's answer (Hive 3 has none; ticket 02's how-to explains).

## Practical notes learned

- Low-sqlglot venv: `<scratchpad of session 1cb5895a...>/scratchpad/venv-low` (sqlglot
  25.24.2). The older `venv-sqlglot-low` is broken. Subagents could not create venvs
  (Permission denied); they used `pip --target` plus PYTHONPATH. A fresh session makes its
  own: `python -m venv <dir>`, `pip install -r requirements-dev.txt`, then
  `pip install "sqlglot==25.24.2"` (two steps: requirements-dev pins 30.19.0).
- JAVA_HOME="/c/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot".
- Regenerate after a merge, never hand-merge: `tools/hive_corpus.py`,
  `tools/example_gallery.py`, `tools/how_to_page.py` (each also `--edition spark`),
  `tools/example_project.py` and `tools/example_project.py --project intermediate`
  (`--edition spark` there needs `--into`; dev keeps only sqlglot's projects).
- Merge conflicts so far: the map (keep both lines), CONTEXT.md, CHANGES.md's 5.0 section
  (one `### To update from 4.x`, `### New`, `### Refused now`), composer_core/running.py's
  show_hive, the galleries (regenerate). A branch's owner agent can merge `dev` into its own
  branch with full context, which worked well for ticket 01.
- How-tos must be numbered without gaps (`tools/how_to_page.py` range,
  `tests/test_how_tos.py`, `tests/repo/test_export_clean.py`). Dev has 1-32 (31 storage,
  32 keys). Wave-2 agents each take the next free number from 33; renumber at merge.
- Tickets 04 and 08 were both told to put the "is one of the user's Saved tables" check in
  `composer_core/tables.py` as `need_saved_table(t, what)`; keep one at merge.
- Ticket 08 was told to mention `JOIN(..., broadcast=True)` (ticket 05) in one sentence that
  can be kept once 05 lands.
- Core docstrings are read in Spark Composer's gallery with the Edition names swapped: never
  name an Edition in a core docstring to say something true of only one.
- `.scratch/drift.md` is CRLF in the working copy; a drift reviewer appends items and a
  `- <sha>: D<n>` line; close an item by marking `[x]` and ` - closed by <sha>` in a
  `docs(drift): ...` commit.
- Wave 2's shared brief: `wave2-brief.md` in that session's scratchpad (copied below in
  short): setup with `git reset --hard dev`, read map/ADRs/wave-1 Answers, five checks, reviews
  in the foreground, Answer + Status + map line, commit on own branch, report back.

## What's next

1. Merge each wave-2 branch as it finishes; drift review after each; fix items.
2. Fix the Spark CI failure once its log is known; push `dev`; confirm CI's four jobs green.
3. Three test runs on merged `dev`; push; CI green.
4. Wave 3: ticket 09 (ship 5.0, raises TOOLBOX_VERSION, closes D156). Never export or push
   `main`: that is the user's step.
