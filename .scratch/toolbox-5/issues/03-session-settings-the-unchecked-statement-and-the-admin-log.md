# Session settings, the Unchecked statement and the Admin log

Type: task
Status: resolved
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

## Answer

Built on branch `worktree-agent-af9eba55aa5919751`, shared code only (`composer_core/`, no
Edition file changed), so both Editions show the same.

**What was built**

- `composer_core/unchecked.py`, a new core file (registered in `tools/editions.py`), holds:
  - `hive_settings(*names, sets=None)`: the SET lines of shipped or the user's own named sets.
    Shipped, each with why in the docstring: `"dynamic_partitions"` (the exact name ticket 02
    prints), `"map_joins"`, `"statistics_on_write"`, `"merge_small_files"`. Refuses no name, an
    unknown name (listing every set, "check the spelling"), a list of names, a user set named
    like a shipped one, a setting name or value that can't be one SET line, and two sets giving
    one setting different values. `run` sends each line as a call of its own and gives back
    None; `to_hive` gives the lines; `show_hive` prints them under a comment naming the sets.
  - `unchecked_hive(text)`: Hive written by hand, sent as written (a last `;` dropped). No
    Guard, Warning or Load limit looks inside (no automatic LIMIT, no dates cap). `show_hive`
    and so a dry run head it with `-- Unchecked statement, written by hand: no Guard, Warning or
    Load limit looked inside`. Text starting DROP, ALTER or TRUNCATE gets a note at the user's
    line (a Python warning of class `UncheckedNote`, not a glossary Warning), naming
    `admin.drop_days` (TRUNCATE, ALTER ... DROP PARTITION), `admin.drop_table` (DROP TABLE),
    `admin.add_columns`, `admin.set_properties` or `admin.move_to_own_folder`, or saying no
    admin function does the job yet.
  - The Admin log: `run` of an Unchecked statement, or of a Statement whose `_admin_call` is set
    (the hook ticket 04's Admin statements set, in `clauses.Statement`), sends it, then appends
    one Markdown entry: time, kind, the call, the tables the text names, the script and its
    commit (`lineage.scripts_commit`, read from `.git`'s files, no process), worked or the
    error (re-raised after the entry is written), and the Hive in a fence that survives
    backticks. The file is opened for appending only, with a heading written when new.
    `show_hive` and `to_hive` write nothing. Default: `admin_log.md` beside the script or
    notebook that calls `run`; `set_admin_log(path)` moves it (a relative path from the caller's
    folder; `set_admin_log()` back to the default).
- Lineage: `export_lineage` takes Session settings (named, with their SET lines, at the foot of
  both files) and Unchecked statements (one opaque step, "⚠ Unchecked statement", drawn as an
  output marked `unchecked`, with arrows from whole-table boxes for each table its text reads
  and into each it writes or changes, joined to that table's column boxes; ordered before the
  Statements that read what it writes; its report section says nothing inside was checked and
  shows its Hive). Checked in a browser: the page draws both views and lights the path.
- The Example database answers a `SET` line with its key and value, as Spark does.
- Golden corpora: `by_hand:*` cases (each shipped set, a user's set, settings before a read,
  Unchecked statements alone and before a read, a refusal); the corpus keeps a lineage
  footer's Session settings. Galleries, how-to pages and the Example projects' lineage pages
  regenerated. CHANGES.md has a 5.0 "New" section; CONTEXT.md's Saved table says it is what
  Hive calls an external table.

**Code review** (code-review skill, since 1e17ebc). Standards: `set_admin_log` is a public name
no ticket named: decided here (below, open question). Notes name admin functions that don't
exist until ticket 04: kept, as the brief allows, since 04 lands before 09 ships. "Partitions
after the day" and "external table" reworded and the glossary amended; the private docstring
fixed; the Call line made valid Python in a backtick-safe fence; the duplicated frame walk made
one `refusals.callers_frame`. Repeated isinstance switches, reading `_text`/`_lines`, the lazy
lineage import and the string kinds were left: plain functions over a class hierarchy, as the
standards prefer. `_admin_call` is the minimum the spec's "Admin statement ... appends" needs.
Spec: footer now records the SET lines, not only the names, and the corpus pins it; "sent
first" reworded so the footer doesn't claim an order export_lineage doesn't check. Several
commands in one Unchecked statement are allowed and documented ("one command in each").

**Beginner reader** (run on the docstrings, refusals, notes, show_hive marks, Admin log, lineage
texts and CHANGES). Fixed: the cheat-sheet heading and module docstring; the session caveat
("they hold only while your send keeps one session"); `run` gives back None; "a settings.py of
your own"; the two-sets fix; a list of names and a misspelt name get their own fix; the setting
name rule spelt out; "dropping a ; you end it with"; the note sentences split, "with its checks"
for "checked", no doubled "Note:"; the lone `;` after a comment explained; `set_admin_log`'s
paragraph ("call it at the top of each notebook or pipeline"), a TypeError for a non-path; the
cut-short call puts "..." after the quote; footer and export_lineage refusal wording; CHANGES
de-duplicated. Left: the admin.* names and "Admin statement" in the log heading (ticket 04
supplies them before 5.0 ships), Mermaid's `#96;` escape (existing behaviour).

**Open questions for the user**

- The map says HIVE_SETTINGS and ADMIN_LOG live in settings.py, but the Toolbox never imports
  the user's scripts. Chosen: the sets are passed, `hive_settings("nightly",
  sets=HIVE_SETTINGS)`, and the log path is set once per session with a new public name,
  `set_admin_log(ADMIN_LOG)`, as `set_load_limits` is. Public names go from 64 to 67.
- No how-to was added (numbering is shared with tickets 01, 02 and 04); the docstrings'
  examples are the gallery entries. A how-to on sending Session settings and an Unchecked
  statement, and the Example projects' pipelines sending a set first, could follow in 09.
