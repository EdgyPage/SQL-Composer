# Beginner reader: ticket 14, CHANGES.md's 8.7 and the 8.7 Upgrade's marks

Run 2026-11-13 by `.claude/agents/beginner-reader.md` (Opus) on CHANGES.md's `## 8.7`, the
marks and checklist lines `upgrades.to_8_7` writes (and the 8.6 texts it rewords), and the
README template's 8.6 to 8.7 Update bullet. It ran `project.upgrade()` on copies of
`tests/upgrade_from/8.6/intermediate` and `tests/upgrade_from/8.5/intermediate` in its
scratchpad, and edited nothing. From 8.6 the Upgrade left 18 boxes, all the same text.

## Stops, ranked by cost

1. **The mark on a rewritten import said the line works** ("this line now finds it beside your
   Project"), when in the download it fails, and named neither line to change: the import
   (delete it) and the `connect(example_database)` under it. "in its place" had no clear
   referent; "at work" implied a place the line is right; "your Table references for its
   tables" is meaningless for an Example project's made-up tables. Suggested: "8.7's Toolbox
   has no Example database, so this import fails: delete it, and in the connect(...) below
   write your team's connection, such as connect(conn)."
2. **CHANGES didn't say early who the Example database bullet concerns**, nor that a copy of an
   Example project can no longer run and is read on `docs/example_projects.html`; "What you do
   by hand" was buried mid-bullet. Suggested a bullet of its own near the top.
3. **"beside your Project" and "the Toolbox's own repo"** are places a user with only a
   download can't find; a dev-only reason leaked into user text. Suggested dropping the place:
   "rewritten to `import example_database`, which only the Toolbox's development copy has: in
   your download it fails until you take it out." Design note for the user: a rewrite to
   `# connect(your_connection)` would leave a state a user recognises.
4. **Eighteen identical boxes, and "Done for you" reads as success** ("imported the Example
   database in ... from beside the Project"). Suggested "wrote X's import ... as `import
   example_database`, marked for you", and a short mark.
5. **`_WAREHOUSE_NAMES_IT` seemed to put the connection into warehouse.py**, undoing 8.6's
   lesson; its last clause is a garden path. Suggested: "write connect(conn) here, as a new
   Project's warehouse.py does. Your real connection goes in each notebook's connect(...)".
6. **8.6's checklist after 8.5 to 8.7**: `_CONNECTED` gave an instruction with no box, beside
   "Nothing: 8.6 needs nothing changed by hand"; "which the Toolbox no longer holds" was
   ambiguous. Suggested: "...as warehouse.py's conn was. The 8.7 Toolbox has no Example
   database, and its Upgrade marks each of these lines in admin/upgrade_8.7.md." Also: 8.6's
   checklist lists the schedule notebook, as 8.6's step runs 8.7's start().
7. **`_EXAMPLE_DATABASE_UNREAD`**: "write X for Y" needed a reread, and told the user to type an
   import that fails. Suggested: "take out this import of example_database and connect with
   your team's connection in its place."
8. **"such as `connect(conn)`": where does conn come from?** Suggested "with `conn` imported as
   the comment above that line shows".
9. **"say what 8.7 can do" is vague.** Suggested "now offer your own connection".
10. **`CONN_GONE`**: "the notebook running this" means the notebook importing the file.
    Suggested rewording.
11. **The new schedule notebook is added, connected, then marked**: why a new notebook comes
    with a broken import. Suggested saying it copies the other notebooks' connect lines.
12. **"rewrote warehouse.py" is vague.** Suggested naming its docstring and refusals.
13. **NEW_RUNS marks**: "run it" could be the run or the notebook; for several names the
    example showed only one.
14. **What's new**: the intro's gerund subject; `engine.py` never introduced; "whose tables";
    `example_project(...)` "a line of the page alone"; where a Hivevar default's quotes go.
15. **`CONNECT_HERE`**: "import connect with them" means add connect to this import line.
16. **Side findings**: `project.upgrade()`'s docstring still showed "7.1 to 8.6"; the README's
    8.5 bullet says notebooks are connected to the Example database with no word that 8.7
    then marks them.

## What came of each

- **Taken:** 1 (a mark of its own for an import a `connect(...)` line follows, saying to
  delete the import and fill in the `connect(...)` below, `conn` imported as the comment
  shows; the other mark says the line fails in the download and to take it out), 2 (a bullet
  of its own, and "What you do by hand" its own bullet), 3 (no "beside your Project" or "own
  repo" in any mark, CHANGES or the README), 4 (the Done-for-you line), 5, 6 (`_CONNECTED`),
  7, 8, 9, 10 (`CONN_GONE`), 11 (the line saying it copies their connect lines, so their mark
  is on it too), 12, 13, 14 (all five), and 16 (both).
- **Kept:** 15. `CONNECT_HERE` is 8.6's own mark, which Projects 8.6 upgraded already hold
  word for word; only its tail naming the Example database is reworded.
- **For the user:** 3's design note. The step rewrites to `import example_database` because
  the frozen 8.6 Example projects must upgrade into dev's current ones, which import it so;
  a rewrite to `# connect(your_connection)` would leave a user's notebook in a state they
  recognise, but dev's Example projects would then not run. The mark now says to delete the
  line. 6's note on the schedule notebook in 8.6's checklist is ticket 08's, unchanged here.
