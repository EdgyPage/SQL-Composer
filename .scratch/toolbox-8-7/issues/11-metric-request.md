# Copilot file 19, Metric request

Type: task
Status: open
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
