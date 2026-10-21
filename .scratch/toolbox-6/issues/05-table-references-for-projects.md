# Table references for Projects

Type: task
Status: open
Blocked by: 01, 03
Size: M

## Question

Map Notes, "write_table_reference", "Aliases". `write_table_reference(name, send, folder=None)`
writes `<db>__<table>.py` (no `t_` rule), with a commented Aliases heading and examples below
the `Table(...)`, and fills `Table`'s new optional `descriptions={column: text}` from DESCRIBE's
comments. `Table` refuses a `descriptions` key that isn't one of its columns.

## Done when

- Generated files import as `from references.<db>__<table> import <table>`.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
