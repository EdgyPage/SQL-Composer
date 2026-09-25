# How can one offline HTML file render an explorable graph?

Type: research
Status: resolved
Blocked by: -
Findings: branch `research/offline-graph-html`, file `research/offline-graph-html.md`

## Question

The lineage export must be a single HTML file that opens with no network access. sqlglot's own
`Node.to_html()` loads vis.js from `unpkg.com` pinned to `@latest`, so it can't be used as it
stands. The export also goes through a copy-paste install, so its size and file count matter.

Survey the options, and for each give its size, any dependency and its licence, how explorable
it is (pan, zoom, click to expand, highlight a path back to the tables), and rough effort:

- vendoring vis-network (minified size, licence, whether it inlines cleanly into one file);
- a hand-written layered layout drawn as inline SVG with a small amount of JavaScript;
- a collapsible tree built from nested `<details>` elements, with no JavaScript at all;
- Mermaid or similar, if it can run fully offline.

Also establish what `sqlglot.lineage` returns for a whole Statement - every output column in one
call - and what shape the resulting graph has. The findings feed the lineage-view prototype.

## Answer

Draw it ourselves. Compute a layered layout in Python (longest-path layers, barycenter ordering)
and emit inline SVG with about 20 lines of vanilla JavaScript for pan, zoom and
click-to-highlight-ancestors. A 141-line prototype does this with no dependency and no extra file
to paste; its page is about 6 KB and was checked in a browser. vis-network 10.1.2 (Apache-2.0 OR
MIT) inlines cleanly but is 652 KB of minified JS, and Mermaid 12 is 5.6 MB, so both are ruled out.
If layout quality suffers near 200 nodes, `@dagrejs/dagre` (49 KB, MIT) can be inlined for layout
alone while the SVG stays ours.

Whatever draws it, `sqlglot.lineage(None, ...)` does not hand over a finished graph. It returns
one tree per output column. Shared CTE columns come back as single nodes, but base-table leaves
are duplicated under alias names, and columns used only in `WHERE`, `JOIN ... ON` or `GROUP BY`
are absent. So the export must merge leaves on `db.table.column` and add filter and join-key edges
itself. sqlglot's `Node` can't be hashed, so graph code keys nodes on `id(node)`. A nested
`<details>` tree needs no JS but repeats every shared source under each output, so it works as a
fallback section below the graph, not as the main view.

Still open: the prototype has no dummy nodes, so an edge that skips a layer can cut across nodes
(about 15-20 more lines). Also unverified is whether a corporate browser policy blocks inline
`<script>` on `file://` pages; if it does, only the `<details>` tree survives. That check was
added to "What does the work environment actually have?".

Findings: branch `research/offline-graph-html` (commit `7d88423`), file
`research/offline-graph-html.md`, with the probe, the prototype and its HTML output under
`research/offline-graph-html/`.
