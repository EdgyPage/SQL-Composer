# Record the Edition split in the docs, and watch it for drift

Type: task
Status: claimed
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
