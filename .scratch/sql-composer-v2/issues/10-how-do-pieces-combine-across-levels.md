# How do pieces combine across Levels - CTE, subquery, or saved table?

Type: grilling
Status: open
Blocked by: 01

## Question

When a Statement uses a Building block, the block can land in the final string as a CTE, as an
inline subquery, or as a separately written table that the Statement then reads.

A CTE keeps everything in one string, which sqlglot can trace directly, but Hive may recompute a
CTE that is referenced twice. A saved table is computed once, but it needs its own write
statement and a place to live, and its lineage has to be stitched across the boundary.

Decide the default, when (if ever) to save a table instead, and how a saved table's lineage links
back to its sources.

## Comments

**From "How does a composed Statement read?"** A sub-query Building block returns a named
Statement, `derived("latest", statement(...))`, whose output columns are checked attributes. The
prototype (branch `prototype/statement-styles`) tried two ways of placing it: an explicit
`WITH(latest)` clause, and a derived table inlined as a sub-query when `WITH` doesn't name it. A
third variant, where the Toolbox adds the `WITH` automatically, was tried in the ruled-out pandas
style. This ticket picks among them.
