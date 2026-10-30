# A Conversion writes Table folders, a checklist, and runs again safely

Type: task
Status: open
Blocked by: 13
Size: L

## Question

The user (2026-10-30): "Why do I have to create manual files when the answer of what to do was
already given back to me as code? If we know the code, then implement it." Running again: "make
two functions one for overwrite, one that doesn't", settled as `overwrite=True` ("much better").

## Done when

- A Conversion writes `tables/<dev>__<table>/` for each table itself, with `create()`,
  `preview()` and `write()`; `finish_conversion` is gone, and its admin notebook cell with it.
- `tables/<t>/conversion/` holds the statement the table came from, its checklist items and,
  after ticket 16, its compare result. `admin/workflows/convert/<name>/` holds only the scripts
  as given, their order, and the tables that came from them.
- Each `# CONVERSION:` decision gets the default that keeps the original's rows, a box on the
  table's checklist and a line on the instance's; nothing is a placeholder a CREATE answers.
- A statement that can't convert is an Unchecked statement in its own Table folder, listed; the
  batch goes on.
- Running `convert` again rewrites a file whose hash is the one it wrote, keeps an edited one
  and writes the fresh one beside it, listed; `overwrite=True` replaces every file, archiving
  each first.
- The convert Workflow's first two steps (convert, the checklist) are in its step list, and the
  graph's fiddling count for convert falls by every hand step they remove.
- CONTEXT.md's Conversion folder entry says it is the batch's index.
