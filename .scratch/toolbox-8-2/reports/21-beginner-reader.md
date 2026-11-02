# Beginner reader: ticket 21's merged changes (43f19bc)

The reader (opus, 2026-11-01) read the TODO-line messages, new_table's steps 2 and 3,
change_a_saved_table's step 2, promote's decisions step, the README's convert naming and
section endings, and the `# proposed from its logic` mark. It read as a Python-first beginner,
and ran the docstrings and a copy of the Starter project. Each stop is listed with what changed;
the review in ticket 21 says the same.

1. **change_a_saved_table's step 2 stops on the Example database (stuck).** Its check, SHOW
   PARTITIONS, finds no Saved table there, and the refusal's fix points to ops tables.
   *Changed:* the step says the Example database holds no Saved table, so on it the check
   stops: run this step at work.
2. **TODO lines: required, or "when you like"?** The README's "Done when no TODO line is
   left" read against the message, and nothing said how to fill in `does_not_add_up=` when no
   column is one. *Changed:* the README's references step says how: name its columns, or delete
   its TODO when none is.
3. **The convert naming's "then its database".** *Changed:* "the original's database", with why
   (two databases' tables of one name stay apart), and RENAME is optional.
4. **An eighth section ending, "then go on to 4. Count, join and stay safe."** *Changed:*
   "section 4".
5. **new_table step 2's "do as the rules below say", with no list.** *Changed:* dropped.
6. **write_decisions with an empty decisions cell printed nothing.** *Changed:* "Wrote no
   answer: the decisions cell answers no table."
7. **Smaller, left as they are:**
   - the Kept message's hint to write the reference again;
   - promote step 2's location wording;
   - run_workflow's docstring;
   - the mark's "answer "key"", which the reader guessed right;
   - a docstring line that wraps.
