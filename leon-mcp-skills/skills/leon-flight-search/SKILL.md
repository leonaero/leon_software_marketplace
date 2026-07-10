---
name: leon-flight-search
description: >
  Searches for and looks up flights in Leon via the Leon MCP (LeonTest) tools: broad flight
  search by date range, route, aircraft, crew, status, cancellation or tags; finding all flights
  on a known trip; pulling full detail once you have flight NIDs; checking the last flight
  from/to an airport; seeing what changed recently; and falling back to Report Wizard when
  search-flights' filters aren't enough. Use whenever the user wants to find, search, look up,
  or list flights — even from partial or fuzzy criteria (route, date range, aircraft
  registration, crew member, trip number, tag). Trigger on "find flights", "search flights",
  "show me flights from X to Y", "when did we last fly to Z", "what flights changed recently",
  or any request naming the search-flights/find-last-flight-from/
  find-last-flight-to/get-report-wizard-flight-scope-report tools.
---

# Leon Flight Search

## Purpose

Finding flights in Leon means picking from several MCP tools with overlapping-looking purposes
but different filters, limits, and default behaviors. The goal here isn't to re-document their
fields (the live tool schema already tells you that) — it's to get you to the right tool for the
right kind of search, with the right filters resolved up front, and to flag the pagination/date-
range/default-value traps that a schema alone won't warn you about.

Creating, editing, cancelling, restoring, or tagging flights and trips is out of scope here — see
`leon-trip-manager` for that. Passenger lists, Journey Log content, permits, fuel prices, and
crew assignment are also out of scope — each has its own specialized tooling; this skill only
finds and identifies flights, not the data attached to them beyond core schedule/aircraft facts.

## Which tool for which job

| You want to... | Use |
|---|---|
| Find flights by date range, route, aircraft, crew, status, cancellation, ferry flag, tags, or country | `search-flights` |
| Find all flights on a trip you already have the number for | `search-trips-by-trip-number` → `get-trips-by-trip-nids` |
| Get full detail (aircraft, times, actual Journey Log data) for flight(s) you already have the NID for | `get-flights-by-flight-nids` |
| Check whether there's ever been (or is scheduled to be) a flight from a given airport | `find-last-flight-from` |
| Check whether there's ever been (or is scheduled to be) a flight to a given airport | `find-last-flight-to` |
| See which flights were created, changed, or deleted recently | `get-modified-flight-nid-list` |
| See which flights' Journey Logs were created, changed, or deleted recently | `get-modified-journey-log-nid-list` |
| When `search-flights`' filters aren't enough (custom column combos, unsupported filter) | `get-report-wizard-flight-scope-columns-list` → `get-report-wizard-flight-scope-report` |
| Resolve an airport by name/city, fuzzy | `search-airports-by-wildcard` |
| Resolve an airport by exact code | `get-airport-by-code` |
| Resolve an aircraft registration to a NID | `get-aircraft-by-registration` |
| Resolve a tag by name | `search-flight-tags-by-name` |
| Resolve a crew member to a NID | `search-contacts-by-wildcard` / `get-flights-crew` |

Resolve names/registrations/tags/crew to NIDs *before* calling the search tool — don't guess an
identifier. If a lookup returns more than one plausible match, show the candidates to the user
instead of picking one.

## Non-obvious things worth knowing

These are business-logic and API quirks, not field lists — they don't change every time the
schema does.

1. **`search-flights` requires a date range, capped at 6 months.** There's no way to search
   without `timeRange`, and the span between `fromDateTimeUTC`/`toDateTimeUTC` can't exceed 6
   calendar months — split a longer request into multiple calls.
2. **`search-flights` pagination isn't automatic.** If the number of results returned equals the
   `limit` you passed, `shouldRerunRequestForNextPageWithOffset` comes back `true` — you must
   rerun the same query with `offset` set to the count already received, and keep repeating until
   you get fewer results than `limit`. Don't treat the first page as the whole answer.
3. **`flightNumber` and `tripNumber` in `search-flights` are wildcard/partial matches, not exact
   lookups.** "10-2025" matches any trip number containing it. Don't use `flightNumber` unless
   you're confident in the exact value — the tool itself says to leave it unset rather than guess.
4. **`cancelled` and `ferry` are three-way filters, not booleans defaulting to false.** Leaving
   either unset returns both sides (cancelled and non-cancelled, ferry and non-ferry); you have
   to explicitly pass `false` to exclude one side. Don't assume "not set" behaves like "set to
   false."
5. **Country filters use ISO 3166-1 alpha-3 codes.** "POL", not "PL" or "Poland".
6. **`find-last-flight-from`/`find-last-flight-to` default to past flights only.** If the
   question could mean "is one scheduled" rather than "has one ever happened", pass
   `searchType: ALL_FLIGHTS` explicitly — otherwise future scheduled flights are silently
   excluded from the result.
7. **`find-last-flight-from`/`find-last-flight-to` only return real flights.** Simulations,
   reservations, and aircraft repositioning legs are excluded — don't rely on these tools to
   check for other movement types.
8. **`get-flights-by-flight-nids` doesn't return trip context.** It gives flight/aircraft/
   Journey Log detail but no trip number or trip NID. If the user needs to know which trip a
   flight belongs to, get it via `search-flights` (which does include `trip.tripNumber`) or
   `get-trips-by-trip-nids` instead.
9. **Report Wizard is a two-step, column-driven tool.** Always call
   `get-report-wizard-flight-scope-columns-list` first to get valid column `id`s — the report
   output is keyed by column `label`, not `id`, and you only get `flightNid` back if you
   explicitly include `unique_id` in the column list.
10. **Report Wizard's date range cap (92 days) differs from `search-flights`'s (6 months).**
    Don't reuse the same chunking assumptions between the two tools.
11. **"Recently changed" tools only look back a maximum of one week.**
    `get-modified-flight-nid-list` and `get-modified-journey-log-nid-list` cap at 7 days from the
    given date to now. For anything older, use `search-flights` with an explicit date range
    instead.
12. **Journey Log fields returned by `search-flights`/`get-flights-by-flight-nids` are actual
    post-flight data, not planned data.** A flight with populated `atd`/`ata`/fuel figures has
    already happened; an *empty* Journey Log doesn't mean the flight isn't scheduled — check
    `startTimeUTC`/`endTimeUTC` for the plan, not the Journey Log fields, when the question is
    "when is this flight."
13. **Default to non-cancelled flights only, and always say so.** Unless the user asks for
    cancelled flights or the context clearly calls for them (e.g. "what got cancelled last
    week"), call `search-flights` with `cancelled: false`. Whichever way you filtered, tell the
    user explicitly that cancelled flights are excluded from the result — don't let that
    filtering pass silently, since someone reading the list has no way to know what was left out.
14. **Always state each flight's trip status when reporting results.** CONFIRMED, OPTION, and
    OPPORTUNITY carry very different weight, and results can otherwise read as if every flight is
    equally solid. Include the status next to route and time for every flight you report back,
    even in a short summary — don't drop it to save space.

## Common scenarios

For each: what to gather from the user first, then the tool sequence. No parameter-level detail
here — check the live schema of each tool when you actually call it.

### Search for flights matching criteria

**Collect:** the date range (required — ask if not given, and note it can't exceed 6 months),
plus whichever of route, aircraft, crew, status, tags, ferry flag, ICAO flight type, or country
actually matter to the request. Ask about cancelled flights only if it's unclear whether they
should be included — otherwise default to excluding them (see the note below).

**Flow:** resolve any airport/aircraft/tag/crew names to NIDs first → `search-flights` with
`cancelled: false` unless the user asked for cancelled flights or the context implies it → if
`shouldRerunRequestForNextPageWithOffset` comes back true, repeat with `offset` until exhausted.
When reporting results, always (a) note that cancelled flights were excluded (or, if included,
say so) and (b) state each flight's trip status (CONFIRMED/OPTION/OPPORTUNITY) — see points 13
and 14 above.

**If `search-flights`' filters don't cover what's needed** (e.g. filtering or sorting on a data
point it doesn't expose as a parameter, or the user wants a specific combination of fields back),
fall back to Report Wizard instead of trying to force it through `search-flights`: call
`get-report-wizard-flight-scope-columns-list` to see what's available → pick the column `id`s
that match what's needed, including `unique_id` if you need `flightNid` back for further lookups
→ `get-report-wizard-flight-scope-report` with those columns plus whatever filters apply. Keep
in mind its date range caps at 92 days (vs. 6 months for `search-flights`), so a long window may
need several calls.

### Look up all flights on a known trip

**Collect:** the trip number.

**Flow:** `search-trips-by-trip-number` to get the trip NID → `get-trips-by-trip-nids` for the
flight list.

### Get full detail on specific flights

**Collect:** the flight NID(s) — usually already in hand from a prior search.

**Flow:** `get-flights-by-flight-nids`.

### Check whether a flight has ever gone from/to an airport

**Collect:** the airport, an optional aircraft filter, and whether "ever" should include
scheduled future flights or only past ones.

**Flow:** resolve the airport → `find-last-flight-from` or `find-last-flight-to` with an explicit
`searchType`.

### See what's changed recently

**Collect:** how far back to look (max 7 days), and whether they mean flight changes or Journey
Log changes specifically.

**Flow:** `get-modified-flight-nid-list` for flight changes, `get-modified-journey-log-nid-list`
for Journey Log changes.

