# Copilot file 19, Metric request

Type: task
Status: resolved
Blocked by: 02
Size: L

## Question

Users bring vague needs, often several columns muddled into one, or one split into two. The
user's words: "funnel users from non-specific requirements to specific ones WITHOUT detailed
table knowledge ... define new metrics most of all with visibility on math equations and
probing questions. The intention isn't to produce SQL, it's to produce a text instruction of
less ambiguous requirements to steer LLMs with indexed knowledge of databases on to defining
new columns for new metrics. I don't know how hard this will be." (Q8, Q16, Q17, Q21.)

## Done when

- **`tools/copilot_sources/19_metric_request.txt`** renders to `copilot/19_metric_request.txt`,
  8,000 characters or fewer, listed in file 00 and merged into the all-in-one file.
- **Copilot:**
  - asks one question at a time, each with a recommended answer;
  - shows the formula back after each change;
  - asks, for each requirement, "one column or two?", and "are these two really one?";
  - probes, as in "Does a retried run count once or twice?";
  - takes sample rows the user pastes, and works the example on them;
  - pushes back and offers thoughtful criticism, and the user's answer stands.
- **It ends with a Metric request, not SQL,** with a section per column:
  1. the name and one plain sentence;
  2. the formula in plain maths;
  3. each quantity, by column name where the user knows one, else in exact words;
  4. one row per what;
  5. the days counted;
  6. what is left out;
  7. the edge cases;
  8. a worked example;
  9. the open questions.
- **The evaluation:**
  - **Stand-in user:** a proxy plays a user with a vague goal and a secret answer key.
  - **Grilling:** a second proxy, loaded with file 19, grills it and writes the request.
  - **Stand-in chatbot:** a third proxy, given only the Example database's column descriptions
    from its Table references, defines the column in SQL.
  - **Scoring:** the column passes if it gives the key's numbers on the Example database.
  - **Baseline:** the same chatbot given only the vague goal.
  - **Tasks:** six, four dev and two held-out, at least two with a muddled column and one with
    sample rows. The memo is ticket 02's.
- **The thresholds,** set before the first round and recorded in `.scratch/copilot-eval/`:
  - file 19 beats the baseline by a clear margin on held-out;
  - no request holds SQL.

  If it falls short, the Answer says how far, and what the user would decide.
- CONTEXT.md's Metric request entry matches what was built.

## Thresholds (set 2026-11-13, before the first round)

On haiku, every proxy:

- **Held out:** arm C (file 19) passes at least 50 points more of M05 and M06 than arm A0 (the
  chatbot given the vague goal alone): with two tasks, at least one more.
- **No SQL:** none of the six Metric requests holds SQL (`metric_eval.holds_sql`).
- Reported, not a threshold: the dev split's margin, and the share of requests with all nine
  parts in every column.

Tuning: at most two rounds on dev after the first; the held-out round is run once.

## Answer

### Built 2026-11-13

- **Copilot file 19,** `tools/copilot_sources/19_metric_request.txt`, renders to
  `copilot/19_metric_request.txt`, 7,046 characters. File 00 lists it under Which file and in a
  Decision rule, and the all-in-one file merges it. The README's "Have Copilot write it" names
  it in one sentence. It follows the house style: Terms, six steps, Decision rules, Output,
  four examples and a Self-check.
  - It asks one question per message, with a recommended answer and why, and shows the whole
    formula back after each answer.
  - It asks "One column or two?" and "Are these two really one?".
  - It probes each quantity: what counts, what is left out, how a repeat counts ("Does a
    retried run count once or twice?"), which days, NULL, and edges such as a value equal to a
    limit.
  - It works every formula on the user's pasted sample rows, or on three it makes up and says so.
  - It pushes back once, with a number where it can; **if the user keeps their answer, it
    stands**.
  - It ends with the Metric request, a section per column with the nine numbered parts, in
    plain words and maths. Its finished example is about orders, a domain no task uses, so it
    gives no task's answer away.
- **The evaluation:**
  - `tools/metric_eval_tasks.py` holds six tasks on the Example database, M01 to M04 dev and
    M05 and M06 held out. Three muddle their columns: M02 and M05 ask one column where two are
    meant, and M04 asks two where one is. M03 brings sample rows. Each task has its vague
    opening, its secret answer key, its reference Hive, and the key's numbers worked out by
    hand. It also has a naive Hive, the reading the vague goal invites.
  - `tools/metric_eval.py` writes each proxy's messages (`messages`) and the chatbot's from
    Copilot's last turn (`chatbot`). It gathers a round's folders (`answers`), and scores and
    records them (`score`), with `plan` from the memo.
  - A column passes when its Hive gives the key's numbers on the Example database, whatever its
    columns are called or where they stand; extra columns are fine. Numbers are compared at two
    places. In arm C the request must also be there and hold no SQL.
- **Its tests,** `tests/test_metric_eval.py`:
  - each reference gives the key's numbers, and passes;
  - each naive Hive runs and fails, the negative controls;
  - a request holding SQL, or no request, fails a correct column;
  - only the stand-in user's message holds the answer key;
  - a held-out task in arm C is kept by the files version;
  - a scored round is recorded and kept in the memo.
- **`.claude/agents/metric-proxy.md`** is the proxy for all three parts, Read and Write only.
- **CONTEXT.md's Metric request entry** now names file 19, a section per column, the column
  names, and the open questions. Quantity, Grain and Sample rows, file 19's Terms, are new
  entries beside it.

### The thresholds and the rounds

Set before the first round, above and in `.scratch/copilot-eval/results.md`. On haiku, every
proxy:

| split | arm A0 (vague goal alone) | arm C (file 19) | margin | requests with SQL |
|---|---|---|---|---|
| dev, round 1 | 0 of 4 (0) | 4 of 4 (100) | 100 | 0 |
| held out, once | 0 of 2 (0) | 2 of 2 (100) | 100 | 0 |

Both thresholds hold, at the first and only held-out round, and no tuning round was needed.
`results.md` has what the baseline got wrong on each task and what the grilling did: 8 to 11 of
Copilot's turns, the splits and joins asked, sample rows worked, and the user's answer kept
where it overrode Copilot's recommendation.

Six tasks are few. These scores say file 19 works on these six, not how often it fails. The
stand-in users sometimes said more of their key than the question asked, which a real user
wouldn't.

**Decided:**

- **The arms are A0 and C,** as the Copilot evaluation names them: the chatbot given the vague
  goal alone, and the goal grilled with file 19.
- **The chatbot sees the Example database's Table references,** each table's columns, types,
  descriptions, partitions and Key, and no rows, as a chatbot knows an indexed database. It
  writes one Hive SELECT, run on the Example database. It is told the engine has no CAST, in
  both arms.
- **A column passes on the key's numbers at two decimal places,** matched column by column
  whatever their names or order, with extra columns allowed. A request may leave the column's
  name open, and the scorer doesn't judge names.
- **The nine parts are reported, not a threshold** ("whole" in results.md). A part's label may
  carry a note before its colon.
- **SQL in a request** is a SQL code block, or what only SQL writes in capitals (`SELECT ...
  FROM`, `CASE WHEN`, `GROUP BY`, `JOIN ... ON`). Plain maths and lower-case English, such as
  "select only finished runs", pass.
- **A conversation ends** when Copilot's turn holds `# Metric request`, or after 12 of
  Copilot's turns. The stand-in user says "That's all, please write the Metric request" once
  Copilot has no more questions, or after ten answers. M04 and M05 ended that way, after the
  tenth answer.
- **The memo** keys arm C on the stand-in user's whole message, file 19 and the chatbot's
  message. It keys A0 on the vague goal and the chatbot's message. A held-out task in C also
  carries the files version, through ticket 02's `hashed_key`, `task_plan`, `write_kept` and
  `read_kept`, and its round helpers.
- **The proxies were `copilot-proxy` agents** told their part in their message file. A
  `.claude/agents/` file written in a session can't be spawned in that session. Later rounds
  can spawn `metric-proxy`.
- **The beginner reader's points** are in
  [reports/beginner-reader-ticket-11.md](../reports/beginner-reader-ticket-11.md). Its main
  points:
  - file 19 never says what "your chatbot" is, or what to do with what it gives back;
  - file 00's and the README's steps assume code;
  - "One column or two?" is asked only when unclear in step 2, but always in the Self-check;
  - example 2 asks two questions in one message.

  It only advises, and the held-out score belongs to the files version it measured, so file
  19 is left as measured. The user decides which to take, then a new held-out round, on the
  next files version.
- **For the user to decide, with the beginner reader's points:** the code review found these
  in file 19 too. Each is a change to file 19, so each would need a new files version and a new
  held-out round.
  - Example 2 asks two questions in one message.
  - The Self-check asks "One column or two?" of every column, while step 2 asks it only when
    unclear.
  - Steps 5 and 6 have no goal or "Done when".
  - Nothing asks the user for a column name they know: M05's stand-in user knew `status` and
    `duration_mins`, but its request named only `status`.
- **The fix outside this ticket.** `docs/agents/standards.md` named `how_to.html`,
  `examples.html` and `test_standard.py` without their folders, which failed
  `test_pointers.py` at 9281614a and kept the suite from passing and the snapshot from being
  written. Each now has its folder. The `test_standard.py` line is as dev already has it since
  ticket 05.

## Code review

Run with this ticket as the spec and 9281614a as the fixed point. Its sub-agents ran as
`review-standards` and `review-spec`, on Sonnet.

**Standards**

- **Hard: one way per job.** **Fixed:**
  - `read_answers` was in three tools. It is now one, `eval_memo.read_answers(text,
    letter)`, which `copilot_eval`, `excel_eval`, `metric_eval` and their tests call.
  - `plan` and `messages` now go through `eval_memo.round_plan` and `print_round`, the
    `NOTHING_TO_ASK` line included. `round_plan_text` and `asked_tasks` are gone.
  - **Answered:** the parser stays the tool's own. `eval_memo.add_round_commands` adds
    `prompts`, `template` and `proxy`, the Copilot evaluation's, and this evaluation has
    `messages`, `chatbot` and `answers` instead. `_percent`, `results_row` and `record_row`
    write this evaluation's own table, as each tool writes its own.
- **Hard: glossary words.** **Fixed:** Quantity, Grain and Sample rows, which file 19's Terms
  use, are in `CONTEXT.md`.
- **Names.** **Fixed:**
  - `Score.missing_parts` is now `parts_missing`, so it no longer shares the function's name.
  - `found` no longer names three things: it is `given_back` (the DataFrame), `answer_rows`
    and `replies`, beside `Score.found`.
  - `said` is now `described`, `asked` is now `user_text`, and `CHATBOT` is now
    `CHATBOT_INSTRUCTIONS`.
- **Speaker from file names, and the `[5:7]` slice.** **Fixed:** one `TURN` pattern reads a
  turn file's number and speaker, and `SPEAKERS` names them.
- **Feature Envy on a table's private parts.** **Answered:** `copilot_eval.table_context` reads
  the same parts. The Toolbox has no public read of a Table reference's descriptions, and
  adding one is a public name, a ticket's decision.
- **`muddled` read only by tests; `compared_row`; the results header beside `results_row`.**
  **Answered:**
  - `muddled` is the task's record of what the ticket asks: at least two muddled tasks.
  - `compared_row` is called three times.
  - The header and the row live together, as in `copilot_eval`.
- **File 19's steps 5 and 6 lack a goal and a "Done when".** **Answered:** this is a change to
  file 19, left for the user under Decided.

**Spec**

- **Example 2's two questions, and the Self-check's "every column".** **Answered:** under
  Decided, for the user. File 19 stays as the held-out round measured it.
- **`metric-proxy` never run.** **Answered:** a `.claude/agents/` file can't be spawned in the
  session that writes it. The rounds used `copilot-proxy` with the same messages, and
  `docs/copilot-eval.md` says either serves.
- **Sample rows on one dev task only.** **Answered:** the ticket asks for at least one. A
  held-out task with rows is a fair next task for the user to add.
- **`holds_sql` catches capitals and blocks only.** **Answered:** lower-case "select ... from"
  is everyday English in a request ("select only finished runs"). No request held SQL in any
  form; each is in its run folder to read.
- **The answer keys' traps are in file 19's rules: TEST runs, retries, equality, days.**
  **Answered:**
  - Those are the questions file 19 is for, and the stand-in user answers each from the key,
    whatever Copilot recommends.
  - Where a recommendation differed from the key, the user overrode it: 28 or 30 days, rounding,
    runs still going. The request followed the user each time.
  - What file 19 adds is that the questions get asked. The chatbot sees only the request.
  - The finished example is about orders, which no task uses.
- **A weak baseline** (no clarifying at all), **and a floor-and-ceiling result.**
  **Answered:** the baseline is the one the ticket sets. A stronger comparison, the same
  chatbot told to ask its own questions, is the user's to ask for.
- **The scorer accepts extra columns and any column order, and doesn't check names or the
  nine parts.** **Answered:** under Decided. The chatbot names the column and may show its
  working, and the parts are reported.
- **The stand-in users volunteer their key.** **Answered:** recorded as a limit in the Answer
  and in `results.md`. A real user, who says less, would need more questions.
- **`metric_eval.py` changed between the rounds.** **Answered:** only the request reader and
  the parts label check changed, not the pass rule. `results.md` says so.
- **`fafed8e9` is not a committed version.** **Fixed:** the rows now give the commit's tree
  hash of `copilot/`, `git rev-parse --short HEAD:copilot`.
