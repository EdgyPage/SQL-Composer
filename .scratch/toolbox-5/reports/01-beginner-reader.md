# Beginner reader: ticket 01, Keys

Run on 2026-10-15 against a0781b5 plus the review fixes then uncommitted. Advisory only.
13 stops; what was done about each is in the ticket's Answer.

1. `10_save_a_table.py` shows `key=["run_id"]` and `31_keys.py` `key=["job_id", "dt"]`, and
   INSERT_INTO's and INSERT_OVERWRITE's docstrings one of each: should a Key name the Date
   partition? Nothing said both work the same. (stuck)
2. `31_keys.py`'s Lineage list gave numbered's Key as (job_id, newest_first), then newest's
   as "told apart by job_id", explained only by the paragraph after it. (reread)
3. Running the refusal: "SELECT leaves out job_runs.run_id, which is part of job_runs' Key
   (run_id)" pointed at adding run_id, which can't help a table with no run_id. (stuck)
4. "A column the rest decide doesn't count", and CHANGES' "past a column that another column
   of the Key decides". (reread)
5. "so it adds at most one row to each": each what? (reread)
6. "counts the day as one value" came clear only after the first refusal. (reread)
7. Lineage of example 1 says "GROUP_BY makes one row for each job_id" for a GROUP_BY that
   holds dt too. (reread)
8. create_table's docstring sends the reader to the README to learn which Edition leaves the
   Key out, and its example has no key=. (a moment)
9. `minutes BIGINT...` in the how-to's source: nothing says `...` stands for lines that differ
   between Editions; on the page, PRIMARY KEY names dt, which sits under PARTITIONED BY.
   (a moment)
10. "one for each job_id, status, not one for each job_id": `(job_id, status)` would read
    better. (a moment)
11. `many_matches=True`, yet the write is still refused: two checks to tell apart. (reread)
12. `10_save_a_table.py`: a long Key passage inside a "two new pieces of SQL" bullet.
    (reread)
13. check_key says "key" and "the key (run_id)" beside "Key" everywhere else. (a moment)
