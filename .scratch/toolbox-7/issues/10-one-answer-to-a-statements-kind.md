# One answer to "what kind of Statement is this?"

Type: task
Status: resolved
Blocked by: 08
Size: M

## Question

From the architecture review of 2026-10-22 (candidate 1); the user: "Do one and two on the
architecture task". Built with 09, which rewrites run() and needs the same answer for its
mix-up refusal.

A Statement is a record whose meaning lives in its readers: `running.run`, `settings_needed`,
`_admin_hive`, `upkeep._MADE_BY`, `clauses.derived`, `stacking`, the Lineage sections and
`project.run_tables` each work out what a Statement is from its private fields (`_ddl`,
`_ddl.kind`, `_write`, `_admin_call`, `_admin_check`, `_stack`), and the four kinds of step
(Statement, Session settings, Unchecked statement, Python step) are switched on with
`isinstance` in about twenty places.

## Done when

- One private module of the Toolbox answers, for any step, what kind it is (a read, a plan, a
  write, a CREATE or upkeep Statement, an Admin statement, Session settings, an Unchecked
  statement, a Python step) and which of the user's calls sends it, from a mark its maker set,
  not from which fields happen to be filled.
- run_query, run_execute, show_hive, settings_needed, run_tables, Stack, derived, upkeep and
  Lineage ask it; none outside it reads `_ddl.kind`, `_write` or `_admin_*` to tell a kind.
- One table-driven test: each maker, the kind it makes and the call that sends it.
- No public name added; `tools/toolbox_registry.py` lists the new file.

## Answer

Built 2026-10-22 with ticket 09 (03e0075). `sqlglot_composer/kinds.py`: `kind(step)`,
`sent_by(step)`, `is_a_query(step)`, `SENT_BY` and `WORDS`. statement(...) marks a read or a
write, create_table a create, repair_partitions and compute_statistics upkeep, explain a plan,
the admin module an Admin statement; SessionSettings, UncheckedStatement and PythonStep carry
their kind as a class attribute. run_query, run_execute, show_hive, settings_needed,
_statement_tree, derived, Stack, explain, export_lineage and run_tables ask it.
`tests/test_kinds.py` holds each maker's kind and call. Registered in toolbox_registry.

## Reviews

- Spec: explain's refusal still read `_ddl.kind` to name the maker; it now names it from the
  kind, and only an upkeep Statement's maker (repair or compute) from its Hive tree, which
  says which of the two made it. `_admin_hive` in to_hive is the Admin statement's own text,
  not a kind.
- Standards: see ticket 09's.
