# Record the Edition split in the docs, and watch it for drift

Type: task
Status: resolved
Blocked by: 01

## Question

Before any code lands, write down the decision and point the drift reviewer at the new paths.

- `docs/adr/0002-a-pyspark-edition-beside-sqlglot.md`: context, the decision as ticket 01 records
  it, the rejected options (the DataFrame API, vendoring sqlglot, one package that detects its
  library, an in-process Spark for the Example database, trees stored in sqlglot's printed form),
  and the consequences. It supersedes ADR 0001's paragraph rejecting a hand-rolled AST
  (`docs/adr/0001-sqlglot-over-sqlalchemy.md:19-23`) for the tree only; the escaping argument
  still stands, and is met by the parity test against sqlglot. Add a status line to ADR 0001.
- `CONTEXT.md`: add the word **Edition** (_Avoid_: flavour, variant, port, fork, backend,
  dialect). Amend Toolbox, Toolbox version, Clean branch, Example database, Example gallery and
  the opening sentence ("a query API that accepts only strings") so each is true of both.
- `.claude/hooks/drift_list.py`: add `spark_composer/` and `worked_examples/` to
  `WATCHED_FOLDERS`, with cases in `tests/test_hooks.py`.
- `.claude/hooks/drift-reviewer.md`: a note that `spark_composer/`'s shared files are generated
  copies; `version` and `change-notes` judged against the version `main` was last exported with;
  a seventh kind, `parity` (a change to one Edition's user-visible behaviour, docstring, refusal,
  README or CHANGES without the matching change in the other, where no test holds it).
- `CLAUDE.md`: the Drift paragraph names the new watched paths.
- Dated "Changed by the PySpark edition (2026-09-29)" notes on v2 tickets 05, 06, 12, 13, 19 and
  20, and on the v2 map's Notes about what work allows.

A backticked path in a standing doc must exist when committed (`tests/test_pointers.py`), so
`spark_composer/` is named in plain words until ticket 15.

## Done when

The Definition of done in `CLAUDE.md` holds; the hook and pointer tests pass. This lands before
any commit adds `spark_composer/`.

## Answer

The split is written down. `docs/adr/0002-a-pyspark-edition-beside-sqlglot.md` records the
decision, its rejected options and consequences, and ADR 0001 carries a status line saying what
ADR 0002 supersedes. `CONTEXT.md` has **Edition**, and the Toolbox, Toolbox version, Clean branch,
Example database, Example gallery and opening sentence hold for both Editions. The drift hook
watches the Spark folder and `worked_examples/`, the reviewer judges `version` and
`change-notes` against the Editions `main` ships and has a seventh kind, `parity`, and CLAUDE.md's
Drift paragraph matches. The v2 tickets and map lines the Editions change carry dated notes.

## Comments

**Build decisions.** ADR 0002 supersedes ADR 0001 in two ways, not "for the tree only": ADR 0001
rejected a hand-rolled tree *and* Hive renderer together, and Spark Composer hand-writes its
Hive, so the ADR says so; SQL Composer still writes through sqlglot. The `version` and `parity`
kinds say a little more than asked (an Edition `main` already ships; a Worked example; "no ticket
says why they differ"), since that is what the kinds need to judge.

**Drift reviews.** 2c7cf99 opened D18-D20 (glossary: "build", "backend", "sandbox"), closed by
a119b9c; a119b9c was clean.

**Code review (2026-09-29), `97c687b...e8f00b4`.**

- *Standards:*
  - Fixed: "one package that detects its library" says "folder" (package is on the Toolbox's
    _Avoid_ list); Spark Composer is called by its name in both ADRs and the reviewer's brief;
    the Edition entry no longer says how each Edition prints, only what it needs at work and
    where it runs, and "almost the same Hive" (two differences are declared); ADR 0002 says "63
    public names" and "two files written by hand in each folder" plus its own gallery, and has a
    Status line; ADR 0001's status line says it no longer expects a Spark dialect string;
    `test_hooks` lists the two watched paths it expects.
  - Answered, not changed: "case", "builder" and "helper" appear in ADR 0002 in their plain
    senses (a test case, ADR 0001's "query builders", a helper process), not for the glossary's
    concepts. The ADR's file name keeps the slug ticket 05 gave it; the tracker keeps "the
    PySpark edition" as the effort's name. "SQL Composer" names both the project and one
    Edition, as the product has always been called; the glossary's heading is the project.
- *Spec:*
  - Fixed: the vendoring option is in ADR 0002; `change-notes` is judged against the Editions
    `main` ships; the Example gallery is one page per Edition; the ticket 06 note says four
    shapes; the ticket 13 note is in the future tense; the v2 map's "ADR 0001 still stands"
    carries a dated note.
  - Answered, not changed: claiming ticket 02 in the same commit is the tracker's own step.

