# Keys

Type: task
Status: open
Blocked by: -
Size: M

## Question

Map family 1 and ADR 0005. A write into a Saved table with a Key is refused unless the
Toolbox proves each output row unique on it (GROUP_BY over the Key, SELECT_DISTINCT, row_number
kept at 1 per Key, a join keeping the reading table's Key), opt-out `unproven_key=True`; a
Derived table's Key, which 4.1 already works out from its GROUP_BY, SELECT_DISTINCT, a SELECT of
only totals or the one table it reads, is carried through key-keeping joins and a row_number kept
at 1 too; Lineage
marks Key columns and where an output loses its Key; create_table writes
`PRIMARY KEY (...) DISABLE NOVALIDATE`.

## Done when

- Each proof and each refusal tested in both Editions; the golden corpora hold the DDL; the
  Example projects' Saved tables declare their Keys and still write.
- A how-to on Keys (what they catch, the opt-out, why Hive never checks them).
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).
