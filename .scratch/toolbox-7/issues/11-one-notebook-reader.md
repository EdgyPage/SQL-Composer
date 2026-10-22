# One reader and writer for a Project's notebooks

Type: task
Status: resolved
Blocked by: 08
Size: S

## Question

From the architecture review of 2026-10-22 (candidate 2); the user: "Do one and two on the
architecture task".

A Project's notebook format has one private writer (`project._write_notebook`,
`project._template_cells`) and no reader. Tools import those private names
(`tools/how_to_page.py`, `tools/example_project.py`, `tests/test_how_tos.py`), and about ten
places read cells with their own `"".join(cell["source"])`, disagreeing on `.get` vs `[]`, on
stripping, and on bad JSON. One bug follows: `project._importers` skips a notebook that isn't
JSON, but `project._logic_cell` doesn't, so `project.load` on a broken notebook raises a bare
JSONDecodeError instead of the Toolbox's refusal.

## Done when

- One private module of the Toolbox reads a notebook (its cells as kind and text, and a Table
  notebook's logic cell) and writes one (from a Template's cells), and refuses a notebook that
  isn't JSON or has no cells with the Toolbox's four-part refusal, naming the file.
- `project.load` on a broken notebook gives that refusal; a test holds it.
- project.py, the tools and the tests use it; nothing outside it imports `_write_notebook` or
  `_template_cells` or joins `cell["source"]` itself. `tools/offline_policy.py` and
  `tools/code_audit.py` keep their own readers: they read the repo without importing the
  Toolbox.
- No public name added; `tools/toolbox_registry.py` lists the new file.

## Answer

Built 2026-10-22 in a worktree (e5e43a0), merged into dev as 98b3723; drift fixes 2f27ee6;
review fixes efcb9d6.
`sqlglot_composer/notebooks.py`: `read_cells`, `logic_cell`, `template_cells`,
`write_notebook`, `LOGIC`. project.load refuses a notebook that isn't JSON or has no list of
cells Jupyter can read, naming it; `_importers` still passes over a broken notebook, so
remove_block isn't stopped by one that imports nothing. The tools and tests use it;
offline_policy, code_audit and the offline hook keep their own readers.

## Reviews

- Spec (2026-10-22): nothing missing. Answered: test_levels now checks the first logic cell,
  as load does; an empty list of cells is read as no cells (a Template may write one);
  `_importers` catches the refusal's ValueError.
- Standards (2026-10-22): no breach. `found` renamed `listed`. Answered: `shown`/`call`
  travel together for the refusal, and a cell stays a plain (kind, text) pair, as the
  standards prefer plain functions and values to machinery.
- Beginner reader: see ticket 09's.
- Drift: 98b3723 opened D248 and D249, closed by 2f27ee6.
