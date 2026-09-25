# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files in `.scratch/`, on the `dev` branch only.

This repo has a GitHub remote (`EdgyPage/SQL-Composer`) but does **not** use GitHub Issues.
Create and read files under `.scratch/` instead.

## Conventions

- One effort per directory: `.scratch/<effort-slug>/`
- Tickets are one file each at `.scratch/<effort-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is a `Status:` line near the top of each issue file (see `triage-labels.md`)
- Comments append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<effort-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the number.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md`, carrying a `Label: wayfinder:map` line.
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, with the question in the body. A
  `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:`
  line records `open`/`claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top (`Blocked by: -` when none). A ticket is
  unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked and
  unclaimed; the lowest number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append
  a context pointer (the ticket's name as a link, plus a one-line gist) to the map's
  Decisions-so-far.
- **Research findings** live on a throwaway `research/<name>` branch; the ticket carries a
  `Findings:` line naming the branch and file.
