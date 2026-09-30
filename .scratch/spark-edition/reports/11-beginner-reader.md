## Beginner-reader report, ticket 11 (`writing.py`'s docstrings; the `tables.py` module docstring)

The reader read only the two changed places, and looked up one word, "Edition", in CONTEXT.md.

1. **`sql_composer/tables.py:7-8`**, "the one place values become Hive literals. `writing.py`
   writes them as Hive text." "Them" could be the column objects or the literals. A literal
   already sounds like text, so "writes them as Hive text" reads as the same thing said twice.
   "The one place" doesn't name the function; the reader had to grep to find `literal`.
   **Reread.**
2. **`writing.py:1`**, "every step only sqlglot can take", and **`:5-6`**, "Each Edition has a
   file of this name with the same functions." Looking up "Edition" in CONTEXT.md was a stop.
   Then the two lines seemed to contradict each other: the Spark Edition has no sqlglot, so how
   can its file hold "the steps only sqlglot can take", or `sql_text` ("Write a sqlglot tree")?
   And only one Edition is in the folder. **Stuck.**
3. **`writing.py:23` vs `:28`.** `sql_text` ("Write a sqlglot tree as Hive") and `hive_text` ("A
   Statement, or one part of it, as Hive") take the same argument, and `hive_text` only calls
   `sql_text`. The reader couldn't tell why there are two. "sqlglot tree" is never explained.
   **Reread.**
4. **`writing.py:43`**, "hive_function's call, built and read back once, or why its arguments
   don't fit." It reads as if the function returns a reason, but it raises an error.
   `hive_function` isn't explained here, and why "once" matters only shows in the comment at
   `:46`. **Stuck.**
5. **`writing.py:33`**, "read back and written again, to compare". It doesn't say who compares or
   why; the self-check is only named in the comment at `:46`. **Reread.**
6. **`writing.py:4`**, "Hive's own functions": own as opposed to what? The reader guessed the
   Toolbox's Python functions. **A moment.**
7. **`writing.py:82, :91`**, "sqlglot 30 renamed…": the reader had to guess that 30 is a version
   number, and what `this` means. **A moment.**
8. **`writing.py:90`**: `drop` sits next to the public `drop_table`, and neither name has an
   underscore, so the reader wondered whether they were meant to call it. **A moment.**

### The three costliest stops

1. Stop 2: the Edition claim contradicts "only sqlglot".
2. Stop 4: `read_back_function`'s "or why".
3. Stop 1: the ambiguous "them" in `tables.py`.
