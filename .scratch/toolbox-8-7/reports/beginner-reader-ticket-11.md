# Beginner reader: Copilot file 19 (Metric request), toolbox-8-7 ticket 11

Run 2026-11-13 by `.claude/agents/beginner-reader.md` on Opus, on the files as the held-out round
measured them (files version fafed8e96292). Advisory only: nothing was edited. The user decides
what changes; the ticket's Answer lists each point and what was done with it.

Files read: `copilot/19_metric_request.txt` (7,046 characters), `copilot/00_start_here.txt`,
`docs/clean-branch-readme.md` ("Have Copilot write it"), `CONTEXT.md` ("Metric request") and
`docs/agents/instruction-rules.md`.

## The three costliest stops

1. **What "your chatbot that knows your databases" is, and what to do with what it gives
   back, is never said. Stuck.** The file names it four times (lines 6, 9, 28, 66), as do 00,
   the README and CONTEXT, but none says what it is, whether I have one, or whether it is
   Copilot in another chat. Line 9 then says "To build a Statement once it is defined, load
   file 03", while line 66 says the chatbot writes SQL: if it gives SQL, file 07 (Hive into
   Toolbox code) would be the next file, not 03. The route from a Metric request back into my
   Project is never shown.
2. **The steps around file 19 assume code and Table references. Several rereads.** File 00's
   step 4 is done "when Copilot answers with code", step 5 is "Run it", and its Self-check asks
   that the question name each table by its Table reference. The README's steps 3 and 4 say to
   give import lines and "Run its answer". File 19 gives no code, and its user may not know the
   tables. No rule says to skip those steps, or whether a pasted Table reference counts as "the
   user names a column" (file 19, line 56).
3. **"One column or two?" is asked sometimes or always, and two examples break the file's own
   rules. A reread, and a risk for Copilot.** Step 2 and the Decision rules (lines 54-55) ask it
   only "If a column could be two numbers"; the Self-check (line 130) reads as every column,
   every time. Example 2 (line 98) asks two questions in one message, against "Ask one question
   per message" (line 40). Examples 1 to 3 leave out the formula and the "line on what you
   understood" that Output (lines 71-72) says every message holds. Copilot copies its examples.

## Every stop, in reading order

### `copilot/00_start_here.txt`

- **Line 59**, "a new metric defined for your chatbot, not code": to me Copilot is my chatbot.
  Which chatbot? (A reread, stuck later.)
- **Steps 4 to 6 and the Self-check**, "Done when Copilot answers with code" and "Run it": no
  branch for file 19, as step 1 has one for Excel, so the done condition can't be met. (A
  reread.)
- **Lines 101-103**, the Which file line: clear, but for "your chatbot". (A moment.)

### `docs/clean-branch-readme.md`, "Have Copilot write it"

- **Lines 1589-1591**: "to define the columns from" read twice. The four steps after it ask for
  import lines and "Run its answer", which don't fit file 19. (A reread.)

### `copilot/19_metric_request.txt`

- **Line 1**, "(sqlglot Composer 8.6)": consistent with version.txt; a beginner wouldn't notice.
- **Lines 5-9**: see stop 1. "Statement" isn't defined in this file, and "metric", its main
  word, isn't in Terms. (Stuck.)
- **Step 1 (lines 21-23)**: which question comes first? Three actions in one step. (A moment.)
- **Step 2 (lines 24-27)**: "of a column" and "of two columns" read oddly; is "what will you do
  with them?" a third question or the reason? Two branches in one step, and line 55 narrows "two
  columns" to those "only ever added, compared or divided". (A reread.)
- **Step 3 (lines 28-30)**, "ask what Decision rules list": "Decision" is a glossary word here
  (a Workflow's Decision); the missing "the" makes it worse. (A reread.)
- **Step 4 (lines 31-34)**: no rule says when to ask for rows and when to make them up; "or step
  3 for what they correct" means "or go back to step 3". (A reread.)
- **Step 6 (line 36)**: three Self-check lines are about past messages, which can't be fixed at
  the end. (A moment.)
- **Line 43**, `100 x failed runs`: "x" for times; Python made me expect `*`. (A moment.)
- **Lines 48 and 52, Output lines 83-84**: "one total, or per day" is also a grain, so one
  choice can land in part 4 or part 5. (A moment.)
- **Lines 50-51**, "'over' is more than, or at least?": needed rephrasing as "does 'over 10'
  include 10?". A good probe once understood. (A moment.)
- **Lines 56-58**, never guess a column name: does that cover the new column's own name, which
  every "Recommended" answer might propose? Does a pasted Table reference count as the user
  naming one? (A moment.)
- **Output (lines 71-72)**: clear, but the examples don't follow it. (A reread.)
- **Example 2 (lines 97-99)**: two questions in one message. (A reread.)
- **Pushing back (lines 101-105)**: "your rows" are never shown (the arithmetic holds); "You
  write" where: in the request, or the next message? (A moment.)
- **The finished section (lines 107-125)**: the clearest part; the worked example made the nine
  parts make sense. `delivered_on` and `promised_on` count as names the user gave only because
  they came from the sample rows, which is implied. (A moment.)
- **Self-check line 130**: conflicts with lines 54-55. (A reread.)

### `CONTEXT.md`

- **Line 522**, "Text a user writes": file 19's step 5 has Copilot write it. (A moment.)
- **Line 527**: the chatbot "defines" the columns here and in the README, "writes the column" in
  file 19 line 9, and writes SQL in line 66. Does it end in SQL or a description? (A reread.)
- **Line 461**, Statistics' "_Avoid_: ... metrics": searching for "metric" hits this first, which
  made me wonder whether the word is banned. (A moment.)

## Against `docs/agents/instruction-rules.md`

**Met:** the literal header; sections, then numbered steps; Terms; an Output contract with a
fixed form; four examples of different cases; a Self-check mostly observable in the answer; two
bold rules; the size limit; prohibitions paired with what to do instead.

**Short:**

- **One action per step:** steps 1, 2 and 4 each hold more than one action or an unruled branch.
- **Decision rules cover every case:** step 4's ask-or-make-up choice has no rule; "One column
  or two?" always or only when unclear conflicts between step 2, line 54 and line 130.
- **Examples:** two break the Output contract and one the one-question rule.
- **Terms defined where used:** "Statement" and "metric".
- **00 covers every case:** its steps 4 and 5 and its Self-check, and the README's steps, don't
  cover a file that gives no code.
- **Names in backticks:** row values such as TEST, DELIVERED and CANCELLED are in plain text.
