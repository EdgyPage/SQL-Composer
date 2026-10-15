# Session settings, the Unchecked statement and the Admin log

Type: task
Status: open
Blocked by: -
Size: M

## Question

Map family 3 and ADR 0006. `hive_settings(name)` from the user's `HIVE_SETTINGS` in settings.py
or a shipped set (each documented with why); `unchecked_hive(text)`, run like a Statement, with
no Guard, Warning or Load limit inside, drawn opaque in Lineage, marked in dry runs, a note
naming the admin function that does the job, where one does, on text starting DROP, ALTER or
TRUNCATE; the Admin log appended on each run of an Admin statement or
an Unchecked statement, at `ADMIN_LOG` (default `admin_log.md` beside the notebook). The entry's
git commit is read as Lineage reads it, from `.git`'s files (`lineage.scripts_commit`), never by
starting git: ADR 0004 allows the Toolbox no process but the Example database's.

## Done when

- Settings sent and shown in Lineage footers; an Unchecked statement run, drawn and logged; the
  log appended, never rewritten; `show_hive` writes nothing to it.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).
