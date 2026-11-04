# Beginner reader: ticket 08, CHANGES' 8.3 and the Upgrade (2026-11-04)

Run on the newest Opus on CHANGES.md's `## 8.3` and `upgrades.to_8_3`, upgrading a copy of the
8.2 intermediate Project and converting a tagged script twice. 10 stops; what was done:

| # | The stop | Done |
|---|---|---|
| 1 | "convert again under a new name" gives no separate copy: the dev name is the table's | the steps say to give each table a new name in RENAME, such as `{"mart.daily_close": "daily_close_v2"}`, and where the scripts are kept |
| 2 | the Upgrade's checklist says nothing is left to do | `to_8_3` marks each batch whose scripts hold `<PARM` at the top of the convert notebook, and lists it in admin/upgrade_8.3.md |
| 3 | to_8_3's docstring describes as the Upgrade's what the user does | "you convert it again yourself, as the mark and CHANGES.md's 8.3 say" |
| 4 | how to find such batches | the Upgrade finds them |
| 5 | "writes the tag itself as text" | "compares its column with the tag's own text, matching no row" |
| 6 | "step 2's text and each decisions cell's tell of" | "step 2 and each decisions cell now say to paste the DECISIONS project.check() prints" |
| 7 | a step 7 cell you wrote in is kept without partition= | "if you wrote in convert's step 7, add partition=PARTITION to its call yourself" |
| 8 | step 3's refusal changes a pasted DECISIONS' behaviour | a To update bullet says so |
| 9 | "which prints ... and compares" | rewritten as three plain clauses |
| 10 | "where you ran a call in a new cell before" | "before 8.3 you typed that call in a new cell" |

Aside, fixed: project.upgrade()'s docstring example said "from 7.1 to 8.2"; it says 8.3.
