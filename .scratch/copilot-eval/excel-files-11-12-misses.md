# Files 11 and 12: the held-out misses, by cause (ticket 20)

Ticket 20's held-out round, on files fac0fd8, after its two dev rounds: Sonnet 100%, Haiku 94%
(33 of 35), one task short of the 95% ticket 18 set. As ticket 18 says, tuning stops after two
rounds and the misses are written up here, grouped by cause, for targeted fixes. Every other
threshold holds.

## Cause 1: a step written as a sql block of its own (X69; X68 on dev)

Haiku wrote a step, a CTE two finals read, as a ```sql block holding only `WITH costs AS
(...)`, with no SELECT after it, which doesn't parse; then repeated it, correctly, inside each
final's query. Dev round 1's X68 did the same for a connection-only Power Query query, and the
fix for it (fac0fd8) went into file 12's step 2, which covers queries. X69's step is a Table of
formulas that other Tables read, which file 11's step 5 covers ("each step a CTE, `WITH step AS
(...)`"), and step 5 doesn't say the CTE never stands alone.

**Fix:** say it once, in file 11's step 5, where every step is: "each step a CTE, `WITH step
AS (...)`, inside each final's query that reads it, never a ```sql block of its own"; file 12's
step 2 can then point to it. File 11 is at 8,000 characters with Windows line breaks, so the
words come out of it elsewhere, or file 12's step 2 shortens to make room for moving the
whole rule.

## Cause 2: a loaded Table taken for a step when another query reads its query (X70)

In X70, query `owner_load` is loaded into Table `owner_load`, which adds a formula column,
`avg_mins`, and query `busiest_owner` reads the query `owner_load`, not the Table. Nothing
reads the Table, so it is a final; Haiku took it for a step, as a query another reads is one,
and gave no query for it. Sonnet answered it right, but said in its answer it had to choose.
File 11's step 2 reads the roles by what reads what, but doesn't say a query and the Table it
loads are two things, each read or not on its own.

**Fix:** a line in file 11's step 2 or file 12's step 2: "A query and the Table it loads are
read apart: the query is a step when another query reads it, and the Table is a final when
nothing reads the Table, with the Table's formula columns added to the query's."

## Not a file's cause: a Table no workbook holds (X54, dev rounds 1 and 2)

Haiku twice gave X54, whose workbook holds Table `job_runs` alone, a second final,
`scheduler_runs`, which X56 holds: one task's Tables carried into another's answer. Each proxy
answers some 18 workbooks in one reply; Copilot answers one per chat. No rule in the files
would change it, and it should not recur in Copilot.

## Limits of the stand-in Hive, which the score can't see

- sqlglot reads Hive's VARIANCE and VAR_SAMP as one node, so a reply writing VARIANCE, Hive's
  population form, is run as the sample one, and would score correct where Hive gives
  another number.
- Excel's inequality criteria skip text cells, and the sample's dates are text: in a real
  workbook, `"<="&[@dt]` over text dates counts nothing. The tasks hold the dates as text, as
  the Example database does, and the references read the criteria as a person meant them.

## After ticket 21

Cause 1 is fixed: file 11's step 5 says it for every step, and X69, X72 and X74 pass since.
Cause 2 is not, for Haiku: with either wording, aa75911's ("read apart") or f80b90b's ("a formula
reads the Table, never the query"), Haiku took held-out X73's loaded Table for a step, and on
f80b90b X70's too. The query and its Table share a name, which Haiku reads as one thing. The
next fix to try is an example, not a rule: file 12's worked example, or a short one in its step
2, showing query q loading Table q, query r reading query q, and Table q a final of its own,
scored on new held-out tasks.
