# Beginner reader, ticket 17: Copilot file 19 (Metric request)

Run 2026-11-14 on Opus, on `copilot/19_metric_request.txt` (files version 1a40b5a88a53's file
19), file 00's lines on it and the README template's step 3. The reader can't write files; its
report is saved here as it gave it.

## Summary

17 stops: 2 stuck, 8 rereads, 7 moments. The three that cost the most:

1. What to paste as "column definitions". No file shows what one looks like; "their data
   dictionary" is the only source named. File 00 step 4 asks for Table references, then column
   definitions, which blurs the two, and file 00 says the chatbot already knows the column
   descriptions.
2. What to say to the chatbot, and what comes back. "Paste this into your chatbot" gives no
   words to say with it; the request doesn't ask for Hive, yet the closing line assumes Hive
   comes back. File 00 says to save it as a .hql file before file 14; file 19 skips that step.
3. How the asking ends. Step 3 lets Copilot stop when no question is left, but A4 says only
   the user ends it; neither file 00 nor the README tells the user to say "write it".

## Stops, in reading order

00_start_here.txt

1. 25-26 against 42: the chatbot "knows your databases and their column descriptions", then
   "paste your column definitions": where do they come from? Reread.
2. 38-42: a Table reference against column definitions (types but no meanings); does file 19
   need a Project? The README's step 3 has the same mix. Reread.
3. 45-48: step 5, "Run it", for file 19 where nothing runs. Moment.
4. 67-69 against 19:97-99: the .hql step before file 14 in 00, not in 19. Reread.

19_metric_request.txt

5. 7: "Load this file when a metric is not yet exact." Moment.
6. 12-13: no example of pasted definitions, not even for ops.orders. Stuck.
7. 14: "the chatbot at work that knows the databases; not Copilot": Copilot is also a chatbot
   at work. Moment.
8. 74-75: "order 3, cancelled, is left out", but nothing asks the user to paste sample rows.
   Reread, and a CONTEXT.md lookup.
9. 23-24 against 33-34: step 3's "until no rule leaves a question" against A4's "Only the user
   ends the asking". Stuck.
10. 39-40: "Unless the user says what it holds: M3" read first as "if the user says, M3".
    Reread twice.
11. 44-45, D4 read as a definition, not a ban; the example's part 3 writes delivered_on and
    promised_on without "ops.orders.", against D1 and S3. Reread.
12. 46-48: C1 clear only from line 80's examples; C2's "only" unclear. Reread.
13. 58-60, G2 points to parts by number before the Output template. Reread.
14. 69-70, M2's "called one in part 1". Reread.
15. 74 against 130: "no '= 50'" beside "on_time_pct = 100 x ...". Moment.
16. 79: "the top and bottom" read as top-N rows; it means numerator and denominator. Moment.
17. 86: "(P4)" and Patterns P4 and P6, with no P1-P3 or P5; 87's "by which column" terse.
    Moment each.

Closing line and README: "Paste this into your chatbot. For the Hive it gives back ..." The
request describes columns and asks for nothing. Stuck: the main "what do I do next".

## What worked

The Output template and the finished on-time example made the end goal clear at once. The
"When the user says, do" list showed what would be asked. File 00's decision rule found file 19
on the first try.
