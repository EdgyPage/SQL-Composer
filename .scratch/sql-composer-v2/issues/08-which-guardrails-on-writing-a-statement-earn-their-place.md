# Which guardrails on how a Statement is written earn their place?

Type: grilling
Status: open
Blocked by: 01, 03

## Question

A Python-first SQL beginner gains most from guards against the mistakes they are likely to make,
but every guard is also one more thing to understand. The user's steer (charting, Q2
elaboration): v1's *guarantees* can come back, as long as each is a lightweight function rather
than a model to learn, and each is shown working on the example database. Given the chosen
syntax, decide which guards stay and how each announces itself:

- typo-proof columns through Table references (settled in spirit during charting);
- escaped literals;
- a Hive-validity check before a string is handed over;
- **duplicated rows**: a join on a non-key column multiplies rows and silently inflates a `SUM`.
  Catching it needs a Table reference to declare its key;
- **unsafe re-grouping**: moving from days to weeks is safe for a `SUM` but wrong for a
  `COUNT(DISTINCT ...)` or an average of averages, and a ratio must be recomputed from its parts;
- anything the Hive research surfaces.

For each guard: refuse or warn, how to opt out, what the message says, and the smallest function
that expresses it - no Metric/Dimension vocabulary. This ticket is about the *shape* of a
Statement; how much it reads and returns belongs to the load-safety ticket.
