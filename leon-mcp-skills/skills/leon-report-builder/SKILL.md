---
name: leon-report-builder
description: >
  Builds custom data reports in Leon via the Report Wizard MCP (LeonTest) tools —
  column-driven reports over a given "scope" of data. Only the flight scope is available today
  (get-report-wizard-flight-scope-columns-list / get-report-wizard-flight-scope-report), but more
  scopes (e.g. crew, trip) are expected later following the same two-tool pattern. Use whenever
  the user wants a custom report, export, or data extract that goes beyond a simple lookup —
  something with chosen columns, filters, and a delivery format (HTML, Excel, PDF). Trigger on
  "build a report", "generate a report", "create a report of...", "export flights/crew/... to
  Excel/PDF", or any request naming a get-report-wizard-*-columns-list /
  get-report-wizard-*-report tool.
---

# Leon Report Builder

## Purpose

Report Wizard is organized by "scope" — a data domain, each exposed as a matching pair of tools:
`get-report-wizard-<scope>-columns-list` (no input, returns the columns available for that
scope) and `get-report-wizard-<scope>-report` (takes a `columnList` plus scope-specific filters,
returns the rows). **Flight is the only scope available right now.** More scopes will be added
over time using the same two-tool pattern — if a request is about a scope that doesn't have
flight-scope tools obviously covering it (e.g. a crew-only or trip-only report), `tool_search`
for `get-report-wizard-<scope>` before concluding it isn't supported yet.

This skill describes the general schema for using any Report Wizard scope, not just a fixed
recipe for flight reports — the same workflow applies once new scopes appear. It does not
replace `leon-flight-search` (which finds/identifies flights) — use this skill specifically when
the goal is a structured, column-based report or export, typically meant to be delivered as a
file.

## Core principles

These apply regardless of which scope you're working with:

1. **Always ask for the desired output format before building anything** — HTML, Excel (xlsx),
   or PDF — if the user hasn't already said. The format determines the downstream tool you hand
   the data to, so it's worth confirming up front rather than assuming and redoing the work.
2. **Request the minimum columns that satisfy the request.** Don't pull every available column
   "just in case" — check the columns-list output, pick only what's needed to answer the request
   or populate the report, and add an identifier column (e.g. `unique_id` in flight scope) only
   if you'll need it for a follow-up lookup.
3. **Push filters into the tool call first.** Every scope's report tool exposes some filters
   (for flight scope: aircraft, airports, crew, date range, cancellation). Apply as many of the
   user's constraints as the tool supports directly as parameters before calling it.
4. **Only filter in your own code when the tool has no equivalent parameter.** If a constraint
   the user asked for isn't exposed as a filter, fetch the data using whatever filters *are*
   available (to keep the result as narrow as possible), then filter the returned rows yourself.
   Don't skip an available tool-side filter just because you'll also need code-side filtering for
   something else — combine both rather than doing everything in code.

## Which tools for which scope

| Scope | Columns tool | Report tool |
|---|---|---|
| Flight | `get-report-wizard-flight-scope-columns-list` | `get-report-wizard-flight-scope-report` |
| Anything else | Not yet available as of this writing — `tool_search` for `get-report-wizard-<scope>` before assuming it doesn't exist | — |

Resolver tools you'll likely need to turn user-given names into filter NIDs (flight scope, and
probably future scopes too): `search-airports-by-wildcard` / `get-airport-by-code` (airports),
`get-aircraft-by-registration` / `get-fleet` (aircraft), `search-contacts-by-wildcard` /
`get-flights-crew` (crew). Resolve names *before* calling the report tool — don't guess a NID.

## Flight scope specifics

These two apply only to the flight scope (not a general Report Wizard rule — they'll need
re-evaluating whenever a new scope has an analogous concept):

1. **Default to `isCanceled: false`, and always say so.** Unless the user asks for cancelled
   flights or the context clearly calls for them (e.g. "what got cancelled last month"), call
   `get-report-wizard-flight-scope-report` with `isCanceled: false`. Whichever way you filtered,
   tell the user explicitly whether cancelled flights are included or excluded in the report —
   don't let that filtering pass silently.
2. **Always include a trip/flight status column, even beyond "minimal columns."** CONFIRMED,
   OPTION, and OPPORTUNITY carry very different weight, and a report can otherwise read as if
   every row is equally solid. Check the columns list for the status column and include it in
   every flight-scope report you build — this is one case where it's worth adding a column the
   user didn't explicitly ask for, and it's worth mentioning that you added it.

## Non-obvious things worth knowing

1. **The columns-list tool must always be called fresh, per scope, before building a report.**
   Column `id`s aren't documented anywhere static and shouldn't be assumed or reused from memory
   across sessions — always confirm them via the current `columns-list` call.
2. **Report output is keyed by column `label`, not `id`.** You pick columns by `id` in the
   request, but each result row comes back as a map keyed by the human-readable `label`. Use the
   `columns-list` response to map between the two when presenting results.
3. **There's no built-in pagination on the flight-scope report tool.** It has no `limit`,
   `offset`, or cursor — one call returns everything matching your filters at once. The practical
   ceiling on result size comes from how narrow your filters are and the tool's own date-range
   cap, not from paging through results. If a future scope's report tool *does* expose pagination
   parameters, treat them the way `search-flights` works in `leon-flight-search`: keep rerunning
   with the next offset/cursor until a page comes back short or empty — don't assume the first
   response is complete just because this scope's tool doesn't page today.
4. **Date range caps are scope-specific — don't generalize one scope's limit to another.**
   Flight scope caps at 92 days per call; a future scope may cap differently. Check the tool's
   own schema/description each time rather than reusing a remembered number.
5. **`dateFilter` (or whatever a scope calls its date range) is usually required, not optional.**
   Don't assume a report can run over "all time" — plan for chunking a long request into several
   calls if the user's date range exceeds the cap.
6. **Getting `flightNid` (or the scope's equivalent row identifier) back requires asking for it
   explicitly.** In flight scope this means including `unique_id` in the column list — it's not
   returned automatically just because you have other columns.

## Common scenarios

### Build a report

**Collect:** what the report needs to answer or contain (which drives column selection), any
filter criteria the user already knows (date range, aircraft, route, crew, cancellation, etc.),
and — if not already stated — the desired output format (ask: HTML, Excel, or PDF).

**Flow:**
1. Identify the scope. If it's flight-related, use the flight scope tools; for anything else,
   `tool_search` for a matching `get-report-wizard-<scope>` pair before assuming it's unsupported.
2. Call `get-report-wizard-<scope>-columns-list` to see what's available.
3. Pick the minimal set of column `id`s that satisfies the request (plus a row identifier column
   if follow-up lookups will be needed). For flight scope, also include the status column
   regardless — see "Flight scope specifics" above.
4. Resolve any names (airports, aircraft, crew, tags) to NIDs, then push every applicable filter
   into the report call — date range, route, aircraft, crew, cancellation, etc. For flight scope,
   default `isCanceled: false` unless told otherwise, and flag that choice when presenting
   results.
5. Call `get-report-wizard-<scope>-report`. If the user's date range exceeds the scope's cap,
   split it into multiple calls and combine the results.
6. If a requested constraint isn't covered by the tool's filters, apply it to the returned rows
   in code rather than pulling unfiltered data and hoping it's small enough to eyeball.
7. Hand the resulting rows to the appropriate tool for the confirmed output format: the `xlsx`
   skill for Excel, the `pdf` skill for PDF, or an HTML file/artifact for HTML.
