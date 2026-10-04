# Narrow the Edition seam

Type: task
Status: resolved
Blocked by: 07

## Question

The two writing.py files are the two adapters at the Edition seam. Ticket 05 took describe_text
and show_partitions_text off it. What candidate 8 of [report.html](../report.html) found
besides:

1. **`Ordered.nulls_first` carries nothing**: it is always `not desc`, SQL Composer's writer
   passes it on, and Spark Composer's ignores it. Any other value would make the Editions write
   different Hive with no declared difference.
2. **Spark Composer's date-call writer** keeps its own copy of trees.DATE_CALLS's names, and
   writes `date_sub(d, n)` as `DATE_ADD(d, n * -1)` without brackets, so a computed day count
   such as `a + b` would come out `a + b * -1`. No caller passes one today.
3. **Spark Composer's type parser** has four `raise ValueError(...)` lines that can't be
   reached, since create_table checks every type against HIVE_TYPES first.
4. **EDITION_INTERFACE's comment** says the functions are what each Edition offers the shared
   files, but `example_database_cannot_run` is there for the dev tools and tests.

## Decisions (made under the user's goal to implement every candidate worth it, 2026-10-03)

- **`nulls_first` leaves the tree**: SQL Composer's writer derives it from `desc`, as Hive's
  default is; Spark Composer's writes ASC or DESC.
- **Spark Composer writes a date call's name from the node** and puts a day count that is a
  sum, difference or quotient in brackets, as sqlglot does; a test runs both writers on each
  kind of calculation, a column, a CAST and a bracketed count.
- **The unreachable type errors become one**: a single line saying the type wasn't checked.
- **The interface comment says who calls it**: the shared files, and the dev tools and tests.
  A comment has no test; the code review checked it against who calls the function.
- **Not done, as not worth it:** making Spark Composer's "as SQL Composer writes it" switch
  public for tools/hive_corpus.py, which would add a function to both writing.py files to save
  one tool's reach into a private name; and one parser for the type grammar, which would grow
  a shared file to serve one Edition's writer.

## Done when

- Each of 1-4 has a test or a check that holds it.
- Both runs pass; the goldens are unchanged.
- The code-review skill has run with this ticket as its spec, and the drift items are closed.

## Answer

Built in `ba4568a`, reworked after the review in `6fbdfce` and after drift item D116.

- `Ordered.nulls_first` left the tree; SQL Composer's writer derives it from `desc`.
- Spark Composer writes a date call's name from the node, and brackets a day count that is a
  sum, a difference or a quotient, as sqlglot does; tests/repo/test_writers_agree.py runs both
  writers on each kind of calculation, a column, a CAST and a bracketed count.
- Spark Composer's four unreachable type errors are one, `_unchecked`, with a test.
- EDITION_INTERFACE's comment says who calls `example_database_cannot_run`.

**Code review (2026-10-03), `ba4568a`.** Standards: no hard violation but a latent parity one,
which the spec axis found too: Spark Composer bracketed every day count that isn't a number,
where sqlglot brackets only some calculations. Fixed in `6fbdfce`; its drift review (D116)
found a product still differed, fixed in `d2da1c2`, with every arithmetic kind
tested. Also fixed: the local's name, `_unchecked`'s message for part of a type.

| Items | Opened by | Closed by |
|---|---|---|
| D116 | `6fbdfce` | `d2da1c2` |

