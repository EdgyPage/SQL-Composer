# Project file kinds: one module for the registry and each kind of Project file

Type: task
Status: claimed
Blocked by: 11
Size: M

## Question

From the architecture review of 2026-10-22 (candidate 3); the user: "Do candidates 3 and 4 and 5
on the architecture task". Toolbox 7.1, which isn't exported yet.

What one kind of Project file is (a Table folder, a Table reference, a Building block, the
registry itself) is spread across about nine places in `sqlglot_composer/project.py`: its path
(`_shown`, and `.rstrip("/")` in `_remove` and `register`), the "/" an archived folder gets,
its label (`_KINDS`), its remover (`_REMOVES`), how it is found on disk (inline in `check`),
its file naming (`named_as`), whether a reference change rewrites the Database modules, and
the name to stem mapping (`table_stem`, `_table_name`, two inline `replace(".", "__", 1)`, and
stem back to name in `check`, which is lossy for a database whose name holds `__`). `register`
picks the kind by "has a dot". `_registry`, `_in_use`, `_add_rows` and `_mark_removed` re-read
and rewrite the whole registry.csv, once per table in `add_references`. `run_tables` reads the
registry's rows itself, and `tests/test_project.py` parses registry.csv itself.

## Done when

- One private module of the Toolbox (not brought by the star import, listed in
  `tools/toolbox_registry.py`) owns the registry (whether a name is listed, listing it, marking
  it removed, the rows in force) and, for each kind, its path, label, remover, how it is found
  on disk, and how its name maps to its file or folder stem and back. Each kind is data in one
  place: a new kind would be one entry.
- project.py's actions (new_table, remove_table, new_block, remove_block, add_references,
  remove_reference, register, check, run_tables, refresh_reference_sheet) ask it; none
  spells a kind's path, label or stem itself.
- An action that lists or checks several names reads registry.csv once.
- The kinds and their mappings are tested as data, without `chdir`; tests read the registry
  through the module, not by parsing registry.csv.
- What a user sees doesn't change: the same files, the same registry.csv, the same reports
  and refusals. The lossy stem for a database name holding `__` is reported in the Answer
  (with a test that pins today's behaviour), not changed, unless the fix is a refusal at the
  one place such a name enters.
- No public name added.
