# Keys are checked before writing, and carried through every step

Status: accepted

Hive and Spark never enforce a primary key: a table declared with one takes repeated keys without
a word, and a join on part of a key quietly multiplies rows. Up to 4.1 the Toolbox used a table's
key only for the repeated-rows Warning on a join, and `check_key` counted repeated keys after the
fact. On 2026-10-15 the user asked for keys to make fewer errors on the tables they build and
join, and to show in Lineage.

So in 5.0 a table's Key, its primary key, declared on its Table reference, does four things:

- **A write into a Saved table with a Key is refused unless the Toolbox can prove each output row
  unique on it**: a GROUP_BY over the Key's columns, a SELECT_DISTINCT, a row_number kept at 1 per
  Key, or a join that keeps the reading table's Key. A write that is unique for a reason the
  Toolbox can't see carries an opt-out, such as `unproven_key=True`, as every Guard has.
- **A Derived table's Key reaches further.** 4.1 already works one out from a Derived table's
  GROUP_BY columns, its SELECT_DISTINCT, a SELECT of only totals, or the one table it reads; 5.0
  carries it through joins that keep the reading table's Key and through a row_number kept at 1
  per Key, so the repeated-rows Warning and the check above see through more Derived tables
  instead of asking for `many_matches=`.
- **Lineage marks each output column that is part of a Key**, and says where an output lost one.
- **`create_table` writes the Key into the table** as `PRIMARY KEY (...) DISABLE NOVALIDATE`, which
  Hive 3 keeps as information for other people and tools, and never checks.

## Considered options

- **Warn instead of refusing** for a 5.x, refusing later. Rejected: a write that can't be shown
  unique is the very error the user asked to make less often, and every other Guard refuses with
  an opt-out.
- **Run `check_key` after every write**, on the day just written. The user declined: it costs a
  query per write, and stays a call of its own.
- **Leave keys out of the table definition.** Rejected: the user wants the key known to whoever
  reads the table, and `DISABLE NOVALIDATE` costs nothing.

## Consequences

- Some writes 4.1 let through are refused in 5.0, so 5.0 is a major version, and CHANGES says how
  to read the refusal and when the opt-out is right.
- A Saved table with no Key is written as before, unchecked; its Table reference says it has
  none.
- The proof is only as wide as the cases above; each new way the Toolbox learns to prove a Key
  is a change to this check, with its test.
