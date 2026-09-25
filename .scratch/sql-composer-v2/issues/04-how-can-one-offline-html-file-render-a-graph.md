# How can one offline HTML file render an explorable graph?

Type: research
Status: open
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
