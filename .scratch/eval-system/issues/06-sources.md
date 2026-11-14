# Sources: Used and Read lines, failures tied to doc ids

Type: task
Status: open
Blocked by: 01
Size: M

## Question

The user: "I want to be able to have the sources of llm outputs evaluated to better target fixes
and improvements in the usability documentation." (Q6.)

## Done when

- `copilot-proxy.md` and `metric-proxy.md` tell a proxy to end each reply with `Used: <ids>`,
  the pattern, rule and worked-pattern ids of the loaded file it followed; the zero-context
  user's phase messages tell it to end with `Read: <file> <section>, ...`.
- The scorers read those lines; a reply missing one is recorded as "no source", not failed.
- `eval_runs` keeps, per round, each task's result with its cited ids and the loaded file's
  version.
- A per-round attribution summary ranks the ids by how often failing replies cite them, against
  how often passing replies do, and lists failures that cited nothing; ticket 09 shows it.
- A test holds that every id a file defines can be cited, and a cited id the file doesn't define
  is flagged.
