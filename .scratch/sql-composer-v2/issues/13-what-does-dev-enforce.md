# What does `dev` enforce, and which maintainer agents does it carry?

Type: grilling
Status: resolved
Blocked by: 05

## Question

The user wants their principles enforced without having to repeat them. Decide:

- what `dev`'s CLAUDE.md states;
- which rules run as tests - the Clean-branch export allowlist, the Toolbox's import allowlist,
  downward-only imports between Levels, and any beginner-readability limits such as a docstring
  example on every function;
- which maintainer agents exist (a code reviewer that knows these principles, a test writer, the
  Clean-branch exporter, others) and what each one is told.

A principle that has to be repeated in prose is one a check should replace.

## Comments

**From "How does the Toolbox survive being pasted over an existing directory?" (2026-09-25).**
Checks for `dev` to carry:

- a test that every Toolbox file declares the same `TOOLBOX_VERSION`;
- the export script stamping line 1 of each file, writing the file list into `__init__.py`, and
  placing the README at `.github/README.md`;
- `main`'s allowlist is now the `sql_composer/` folder plus `.github/README.md`.

**From "What's in the Toolbox?" (2026-09-25).** Two candidate checks:

- every Toolbox docstring carries one `>>>` worked example on the example database's Table
  references, showing the Hive it emits. Decide whether `dev` runs these as doctests;
- the Clean branch README has a cheat sheet generated from each docstring's first line, so a check
  should fail when it is stale.

"Retire v1 from `dev` and carry over the salvage" waits on this ticket.

## Answer

**Every principle a test can hold lives in `pytest`, CI runs it, and a small set of hooks and
agents cover what no test can.** Anything mechanical is a test, anything that takes judgement goes
to a hook or an agent, and `CLAUDE.md` points to them instead of restating them. The work Python is
taken to be **3.11**. That is the Toolbox's floor, and ruff targets `py311`.

**Where checks run:**

- **`pytest` holds every check.** A GitHub Actions workflow on `dev` runs it on each push, twice,
  both on Python 3.11: once with sqlglot 25.24.2 (the bottom of the supported range) and once
  with 30.19.0 (the pin).
- There's no git pre-commit hook, since git doesn't version hooks and CI catches the same things.
- `main` gets no CI, since a workflow file there would sit outside its own allowlist.

**Tests:**

- **Import allowlist:** a test reads every `sql_composer/` file's imports. It allows only the
  standard library, pandas, numpy, sqlglot and other Toolbox modules. The Toolbox never imports
  a Level.
- **Doctests:** every docstring's `>>>` example runs as a doctest. The test setup supplies
  `job_runs` and `jobs`, so a docstring shows only the call and the Hive. A separate test fails if
  a public name has no docstring or no `>>>` example.
- **Beginner-readability limits:**
  - a test lists all 59 public names, so a name is added or removed only by editing that list;
  - each docstring's first line is one sentence of at most 80 characters, since it becomes the
    cheat-sheet line;
  - ruff's complexity limit (C901, at most 10) applies to every function.

  There are no caps on function or module length and no banned constructs. Those are left to the
  reviewer.
- **Refusals:** a test goes through every Guard and Load limit in `refusals.py`. It fails if one
  has no test showing it refuse, or no test showing its opt-out let the Statement through. One
  helper builds every four-part message, so the code itself enforces the message shape.
- **Versions:** every file declares the same `TOOLBOX_VERSION`, and `CHANGES.md` has a section for
  it.
- **Pointers and pins:**
  - every file path named in `CLAUDE.md`, `docs/agents/` and the README template exists;
  - the sqlglot pin in `requirements-dev.txt` falls inside the supported range in `__init__.py`;
  - the CI runs cover both the bottom of that range and the pin.
- **Levels:** a test checks that imports point only downward. It runs on `dev` only, over the
  example database's scripts, which sit in folders named after the glossary terms:
  `table_references/`, `building_blocks/` and `statements/`. No checker ships, since that would
  add a 60th name.
- **Export:** a `dev` test runs the Clean-branch build without git and checks the allowlist, the
  stamp, the file list and the README.
- **Example gallery:** a test regenerates `sql_composer/examples.html` and fails if it differs from
  the committed copy (see below).

**The Clean-branch export is a script, not an agent.** `tools/export_clean.py` builds the Clean
tree in a temporary folder:

- it stamps line 1 of every Toolbox file;
- it writes the file list into `__init__.py`;
- it generates `.github/README.md` from a template kept on `dev`, adding a cheat sheet built from
  the docstrings' first lines.

It then imports the stamped copy, checks the allowlist, and commits that tree to `main` locally.
The user pushes it. The cheat sheet exists only in exported output, so it can't go stale. The
script **refuses while any drift item is open** (below).

**Hooks,** in a tracked `.claude/settings.json`:

- **Protecting `main`:** refuses `git commit` and file edits while `main` is checked out, unless
  the export script is the one running. Agents are the realistic risk here. The user's own hand
  edits stay the user's choice.
- **Drift reviewer:** runs just *after* a `git commit` whose diff touches `sql_composer/`, the
  README template, `CONTEXT.md`, `CLAUDE.md`, `docs/` or `requirements-dev.txt`. Commits that
  only touch the tracker skip it. It checks for six kinds of drift:
  1. **Version:** the diff adds, removes or renames a public name, or changes what a Statement
     emits, and `TOOLBOX_VERSION` hasn't changed. The session asks the user whether to raise it,
     and neither the hook nor the session ever raises it alone.
  2. **Change notes:** a change the user would notice has no plain-words line in `CHANGES.md`
     under the current version.
  3. **Docstrings:** docstring prose, or a refusal message, no longer matches what the code does.
     The doctest checks the example, not the words.
  4. **Glossary:** a new domain word appears in a name, message or doc and isn't in `CONTEXT.md`,
     or a word the glossary says to avoid is used.
  5. **Standing docs:** `docs/agents/standards.md`, the README template or `CLAUDE.md` says
     something the diff has made untrue.
  6. **Worked examples:** an example's "why" sentence that the diff has made untrue.

  The drift reviewer never edits files. It adds one open item per finding to a tracked list,
  `.scratch/drift.md`, naming the commit. The session fixes the items **as its next commits**,
  and each fix closes its item. A `No-drift: <item> - <why>` line in a commit message closes a
  false alarm, and the reviewer accepts it only if the reason holds.
- **Session end:** a session can't end while an item it opened is still open. Together with the
  export's refusal, drift can sit on `dev` for a few commits but never reaches `main`.

**Maintainer agents:** two.

- **Code reviewer:** the existing `code-review` skill, pointed at `docs/agents/standards.md`.
  That file holds only what no test can enforce:
  - the beginner-readability judgement;
  - glossary words in code and messages;
  - no abstraction that has to be studied before it can be used;
  - no new public name without a ticket.
- **Beginner reader:** `.claude/agents/beginner-reader.md`. It reads the cheat sheet, the
  docstrings and one example Statement as a Python-first SQL beginner, and reports every place it
  had to stop and study, with the line it stopped on. **It only advises:** it never edits, and the
  user decides what changes.
- **Not agents:** test writing uses the `tdd` skill, the glossary uses `domain-modeling`, the
  export is a script, and `CHANGES.md` is written in the commit that raises the version.

**Definition of done** for a `task` ticket that changes code:

1. `pytest` passes;
2. `code-review` has run against the ticket as its spec, and its findings are fixed or answered
   in the ticket;
3. the ticket leaves no open drift item;
4. if anything a beginner sees has changed (a public name, a docstring, a refusal message, the
   README template or a worked example), the beginner reader has run and its report is linked
   from the ticket.

**`CLAUDE.md` on `dev`** stays short and mostly points elsewhere:

- the Dev and Clean branch model, with `main` written only by the export script, which the hook
  enforces;
- the map, and "read its Notes first";
- one line: `pytest` holds every principle a test can hold, so run it before you commit, and CI
  runs it on both sqlglot versions. It doesn't list what the tests check;
- the drift list and how items close;
- a pointer to `standards.md`, not a copy of it;
- the definition of done and when to run each agent;
- the existing issue-tracker, triage and domain-doc sections.

**Example gallery.** The user asked for searchable worked examples, both inside functions and
outside them, kept in step with the code.

- **Standalone worked examples:** one short Statement script each, in the example database's
  `statements/` folder. Its module docstring gives a title and one sentence on why you'd write
  it. It imports `job_runs` and `jobs` like any Level 2 script, so the Levels check covers it.
- **The page:** `sql_composer/examples.html` holds every docstring example and every standalone
  one. Each entry shows:
  - its title and why;
  - the Python;
  - the Hive it emits;
  - the result table on the example database, where the executor can run it;
  - the Toolbox names it uses, worked out from the code rather than typed in.

  The page is self-contained, with no dependency, and a few lines of script filter entries by any
  word, including a Toolbox name. Everything is plain HTML, so if scripts don't run at work,
  Ctrl+F still searches it, and no Markdown twin is needed.
- **Kept in step:** the page is generated and also committed on `dev`, and a test fails if
  regenerating it changes it. Any change in the Hive the Toolbox emits therefore shows up as a
  gallery diff when the change is reviewed, which works as golden-output testing.
- **It ships:** the page sits inside `sql_composer/`, so it ships with the Toolbox and is on the
  self-check's file list.

**Development files:**

- `pyproject.toml` keeps only pytest and ruff settings, with no packaging section;
- `requirements-dev.txt` pins sqlglot 30.19.0, pandas, numpy, pytest and ruff. networkx and
  duckdb are dropped, and duckdb returns only if the example database ticket asks for it;
- `.gitignore` gains `.claude/worktrees/` and `.claude/settings.local.json`.

Ruled out:

- **A local pre-commit hook;**
- **A drift reviewer that edits files itself, or that blocks a commit.** Its findings become
  the next commits instead;
- **Committing the cheat sheet;**
- **Test-writer, exporter, changelog and glossary agents;**
- **Caps on function or module length, and banned constructs;**
- **A Levels checker shipped to work;**
- **"Case" for a worked example,** since it was one of v1's concepts.

Handed on:

- **"Retire v1 from `dev` and carry over the salvage"** sets up everything that doesn't need the
  Toolbox:
  - the development files and `.gitignore`;
  - the CI workflow;
  - `.claude/settings.json` with the hook protecting `main`, the drift reviewer and the
    session-end hook, plus an empty `.scratch/drift.md`;
  - `docs/agents/standards.md`, the beginner-reader agent and the new `CLAUDE.md`;
  - the pointer test.
- **"Build the Toolbox core"** adds the checks that need the Toolbox as it builds it:
  - the import allowlist;
  - `TOOLBOX_VERSION` and `CHANGES.md`;
  - doctests, with the test that each public name has one;
  - the name list, the first-line length and the complexity limit;
  - refusal coverage;
  - the pin-in-range test.
- **New task tickets:** "Build the Clean-branch export" and "Build the Example gallery".
- **"What does the example database demonstrate, and where does it run?"** gets the Levels folder
  names and the standalone worked examples.

**Changed by "What does the Example database demonstrate, and where does it run?" (2026-09-25).**
The Levels test covers `worked_examples/building_blocks/` and `worked_examples/statements/`. There
is no `table_references/` folder, because the Example database's Table references ship inside the
Toolbox as `example_database`.

**Changed by the PySpark edition (2026-09-29).** `pytest` will run once per Edition (`python -m
pytest`, and `python -m pytest --edition spark`), CI will grow to four jobs (both ends of each
Edition's library range), and the drift reviewer gains a seventh kind, `parity`, and watches
`worked_examples/` and the Spark folder.
