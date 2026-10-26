# Toolbox 7.2: Conversions, Upgrades and one version file

Label: wayfinder:map

The user (2026-10-26), with 7.1 exported, asked for two things in 7.2, grilled the same day:

- **Conversions**: "convert existing and valid hive sql in to more maintainable patterns inside
  the composer. I have other people's work that I need to convert to my patterns", mostly
  "large monster sql statements that are often hundreds of lines long with unmaintanable hand
  written lists and many joins across tables", "built on the unscalable assumption of ad-hoc
  rigor. There is lots of effective if/else statements and long INs", each to land in a table
  under their control.
- **Upgrades**: "the groundwork for version conversions down the line eg 7.1 to 7.2 so I can
  preserve my work between versions", so a new feature never means redoing "onetime actions like
  table references or statement constructions by hand. It's a small job now with one or two
  tables, but quickly gets out of control."

And, asked during the grilling: the version out of every file ("It's becoming exhausting to
examine every single file change when the line is just a version number change"), and, once the
map was asked for, "documentation on how to actually use the conversions in the examples and
howto files".

## Notes

### The version

- **7.2, the user's number.** Ticket 01 raises it, in the one version file it makes. CHANGES.md's
  `## 7.2` has a "To update from 7.1" part, which ticket 02 reduces to: copy the folder in,
  restart the kernel, run `project.upgrade()`.
- **The glossary lands with the ticket that makes it true**, as 7.0's map set: each ticket holds
  its CONTEXT.md words, grilled on 2026-10-26. The ADRs, 0013 and 0014, record decisions and
  were drafted with this map.

### Two names

- **Conversion**: someone else's Hive in, the user's Composer code out. **Upgrade**: a Project's
  files carried from one Toolbox version to the next. "Convert" is never used for an Upgrade.
  _Avoid_ for both: migration (already avoided for Project action and Admin statement), port,
  translate.

### One version file (ADR 0013)

- **`sqlglot_composer/version.txt`** holds the Toolbox version; the export adds its time, the dev
  commit, and each file's git hash (`git hash-object`'s value, worked out with `hashlib`).
- **No file names the version or carries a line-1 stamp.** `TOOLBOX_VERSION` and `VERSION` stay
  public, read from `version.txt`.
- **The import**: a missing or unlisted file stops it, as now; a hash that doesn't match warns,
  naming the file. A dev folder, with no hashes listed, skips the hash check.

### Upgrades

- **Files only.** An Upgrade carries the Project's files: Table references, Building blocks,
  Table notebooks, `warehouse.py`, the Template copies in `admin/templates/`, the Registry, the
  Database modules. It never sends anything to the warehouse; a change a version makes there
  stays an Admin statement the user runs, which the report names.
- **`admin/project_version.txt`** is the Toolbox version that last wrote the Project, written
  only by `project.start()` and `project.upgrade()`. A Project with none is a 7.1 Project.
- **`project.upgrade()`**, a Project action, runs each version's step in order from the Project's
  version to the Toolbox's, and logs it. 7.1 is the floor: no steps for earlier versions.
- **Mechanical changes are made; judgement is marked.** Each file is archived to `admin/removed/`
  before it's rewritten. What needs the user is marked three ways: a `# UPGRADE 7.2: <what to
  change>` comment at the line, a checklist `admin/upgrade_7.2.md` with one box per mark, and
  `project.check()` listing every mark left. The user (2026-10-26): "I am open to moving files
  around by hand so long as it is clearly demarcated." Files only Project actions write (the
  Registry, the Database modules) are rewritten whole, unmarked; the Template copies are the
  user's code and are marked like it.
- **A newer Toolbox than the Project only warns**, at import and in `project.check()`: "run
  `project.upgrade()`". The user: "I would lean on warn just to 'ensure compatibility'". Nothing
  is refused.
- **Every Toolbox version ships an Upgrade step**, even an empty one (the user, 2026-10-26), and a
  dev test upgrades the previous version's Example projects, kept frozen on dev, and checks them
  against the current ones.

### Conversions (ADR 0014)

- **A Project action, run from the admin folder**, in `admin/convert.ipynb`. The Hive comes pasted
  into a cell or from a file the user saves (the user can't always get a `.hql` file): both are
  kept as `original.hql` in the Conversion folder.
- **Two steps.** The **scan** reads the Hive and reports, with line numbers: the tables it reads,
  which have no Table reference, what will convert, what will stay Unchecked, and each opt-out a
  Guard will need. Writes nothing. The **Conversion** then adds the missing Table references
  through the user's `query` (as `add_references` does, `key=None  # TODO` and all) and writes the
  Conversion folder. It needs `query`, never `execute`.
- **A name is demanded** (the user: "Demand a conversion name which I can supply"): it names the
  Conversion folder, `admin/conversions/<name>/`, and its notebook. The Registry lists Conversion
  folders.
- **The Saved table's name and `location=` are the user's**, added at the end:
  `project.finish_conversion("<name>", table="mart.team_runs")` makes the Table folder and its
  Table reference and moves the logic in. Its `partitioned_by` is pre-filled, from the original's
  `PARTITION(...)` where it had one, else with a placeholder, and the reference refuses it until
  it names a real column (the user: "pre-fill a partition column that fails if the column doesn't
  exist so I am reminded to fill it in").
- **What the notebook holds**: all the logic in one Table notebook's logic cell, each CTE a
  function giving back a Derived table; nothing split into Building blocks or Aliases (the user's
  call, later). Every long `IN` list and every lookup becomes a named constant in the first cell.
- **if/else chains** become `mapped(column, {...}, otherwise=...)` where every branch tests one
  column against a constant, else `first_match([(condition, value), ...], otherwise=...)`. Long
  INs become `is_in(column, NAMED_LIST)`.
- **The fallback goes only as wide as it must**: `hive_function` for an unwrapped function; an
  Unchecked expression (`unchecked_column`, `unchecked_condition`) for one expression; an
  Unchecked derived table (`unchecked_derived`) for a CTE; an Unchecked statement only for a
  top-level query the Toolbox can't read. The user: "I'd rather have 80% of what I need".
- **Opt-outs copy the original**: each join or read a Guard would refuse is converted with its
  opt-out, marked `# CONVERSION: the original did this; check it`, listed in the scan, and listed
  by `project.check()` while left in the Project.
- **Checking** (the user: "give me the tools to check the conversions"): the converted Statement's
  Hive is compared with the original's, both normalised by sqlglot, at every Conversion; and the
  notebook has a cell that compares their rows through the user's `query`, with a `where=` on
  the partitions, reporting the rows that differ.

### The docs

- **Every new public name opens its docstring with a Worked example**, as 7.0 set.
- **Two Intermediate how-tos**: "Convert someone else's Hive" and "Upgrade your Project to a new
  Toolbox version", each run on the Example database and its Example project, from a sample of
  legacy Hive shipped with the Example database: CTEs, a long IN, an if/else chain, a function
  the Toolbox wraps through `hive_function`, and one piece that stays Unchecked.
- **The Intermediate Example project carries a finished Conversion**, so the end state can be
  read and copied, and the README's file map names every file a Conversion and an Upgrade make.

## Tickets

- [01 One version file, at 7.2, and the ADRs](issues/01-one-version-file-at-7-2.md)
- [02 The Project's version and project.upgrade()](issues/02-the-projects-version-and-upgrade.md)
- [03 Unchecked expressions and the Unchecked derived table](issues/03-unchecked-expressions.md)
- [04 first_match and mapped](issues/04-first-match-and-mapped.md)
- [05 Reading Hive into the Toolbox's objects](issues/05-reading-hive.md)
- [06 Writing a Statement out as Python](issues/06-writing-python.md)
- [07 The scan, the Conversion folder and finish_conversion](issues/07-the-conversion-folder.md)
- [08 Checking a Conversion](issues/08-checking-a-conversion.md)
- [09 The docs: how-tos, Worked examples and the Example project](issues/09-the-docs.md)

The order is the user's habit from 7.0: one at a time, by number. The real dependencies are in
each ticket's `Blocked by:`: 02, 03 and 04 need only 01, and could run side by side if the user
asks, though all three touch CHANGES.md.

## Records this changes

- CONTEXT.md, ticket by ticket: Toolbox version (01); Upgrade, Project and Project action (02);
  Unchecked expression and Unchecked derived table, and Unchecked statement's last sentence (03);
  Conversion, Conversion folder and Registry (07). Each ticket holds the words.
- `docs/adr/0013-the-version-lives-in-one-file.md` and
  `docs/adr/0014-a-conversion-keeps-what-converts.md`, drafted with this map; ADR 0006's Status
  names 0014 (01).
- CLAUDE.md: this map (with the map); the version-file rule for the drift section (01); "every
  version ships an Upgrade step" (02).
- `.claude/hooks/drift-reviewer.md`'s version item (01).
- `docs/clean-branch-readme.md`, the how-tos, the gallery and the Intermediate Example project
  (09, and wherever an earlier ticket breaks one).

## Decisions so far

- [01 One version file, at 7.2, and the ADRs](issues/01-one-version-file-at-7-2.md):
  `version.txt` says `sqlglot Composer 7.2` on dev, the export adds time, commit and LF git
  hashes; a differing file warns, a missing or extra one stops; the export refuses a file the
  registry doesn't list; the Example projects' stamp names the version alone.
- [02 The Project's version and project.upgrade()](issues/02-the-projects-version-and-upgrade.md):
  `admin/project_version.txt`; `upgrades.py`'s `STEPS` and `Upgrade` (add, rewrite, mark);
  each step logged and archived to `admin/removed/<time>-upgrade_<version>/`; the first
  Upgrade runs from `admin/check_project.ipynb`, and adds `admin/upgrade.ipynb`.
- [04 first_match and mapped](issues/04-first-match-and-mapped.md): built in a worktree beside
  03; `Case` gains a `this` part; values of one kind as `equals` mixes them; a None key in
  mapped is refused with the fill_null way to label NULL rows.

## Not yet specified

- **Whether the scan takes `INSERT OVERWRITE ... SELECT` and leading `SET` lines.** Recommended in
  the grilling (take the SELECT, drop their target, carry `PARTITION(...)` as the suggested
  partition column; `SET` lines become a `hive_settings(...)`; a script of several statements is
  refused, saying to split it), and the user's pre-filled partition column assumes the first.
  Ticket 05 confirms with the user before building it.
- **The converted notebook's exact shape**: which cells, in what order. Ticket 06 shows the user
  one converted sample before writing the writer's tests.

## Out of scope

- Upgrade steps for versions before 7.1, and an Upgrade that sends anything to the warehouse.
- Refusing anything while a Project is older than its Toolbox: it warns only.
- A Conversion choosing Building blocks, Aliases or a Key; converting into an existing Table
  folder; one Conversion of several queries.
- Stopping the import on a file whose hash doesn't match.
