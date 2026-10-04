# Narrow the Edition seam

Type: task
Status: claimed
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
  calculation in brackets, as sqlglot does; a test runs both writers on a calculation, a
  column, a CAST and a bracketed count.
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
