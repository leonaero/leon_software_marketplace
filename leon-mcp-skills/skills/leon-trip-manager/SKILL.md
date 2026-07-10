---
name: leon-trip-manager
description: >
  Manages the trip and flight lifecycle in Leon via the Leon MCP (LeonTest) tools: creating
  trips, adding flights to existing trips, editing flights/trip metadata, cancelling/restoring
  flights, deleting trips, reassigning aircraft, managing flight/trip tags, and looking up trips,
  flights, aircraft and airports. Use whenever the user wants to create a trip, add or edit a
  flight, cancel/restore a flight, delete a trip, change a flight's aircraft, add/remove tags, or
  find a trip/flight — even from partial details (registration, trip number, airport name).
  Trigger on "create a trip", "add a flight to trip X", "cancel this flight", "reassign the
  aircraft", "delete trip", or any request naming a Leon trip/flight number or the
  create-trip/create-flight/edit-flights/update-trip tools.
---

# Leon Trip Manager

## Purpose

Trip creation and editing in Leon spans many similarly-named MCP tools. The goal here isn't to
re-document their fields (the live tool schema already tells you that, and it can change under
us) — it's to make sure the right tool gets picked for the right job, in the right order, with
the right information gathered up front, and to flag the handful of business-logic quirks that a
schema alone won't tell you. Always read the actual tool schema you're about to call for exact
field names and constraints; treat what follows as the map, not the manual.

Passenger management (adding/removing pax on a flight) is out of scope for this skill.

## Which tool for which job

| You want to... | Use |
|---|---|
| Create a new trip together with its flight(s) | `create-trip` |
| Add one more flight to a trip that already exists | `create-flight` |
| Change an existing flight (time, airports, aircraft, notes...) | `edit-flights` |
| Change trip-level metadata (type, status, notes) | `update-trip` |
| Put a flight (or several) on a different aircraft | `set-aircraft-on-flight` |
| Cancel a flight | `cancel-flight` |
| Undo a cancellation | `restore-flights` |
| Remove a trip entirely | `delete-trip` |
| Add / remove / wipe tags on a flight | `add-tags-to-flight` / `remove-tags-from-flight` / `clear-tags-from-flight` |
| Find a trip by its number | `search-trips-by-trip-number` |
| Get full detail for trip(s) you already have the NID for | `get-trips-by-trip-nids` |
| Get full detail for flight(s) you already have the NID for | `get-flights-by-flight-nids` |
| Resolve an aircraft registration to a NID | `get-aircraft-by-registration` |
| See the whole fleet | `get-fleet` |
| Resolve a virtual tail | `get-virtual-aircraft` |
| Resolve an airport by name/city, fuzzy | `search-airports-by-wildcard` |
| Resolve an airport by exact code | `get-airport-by-code` |
| Resolve a tag by name | `search-flight-tags-by-name` |
| See what changed recently | `get-modified-trip-nid-list` / `get-modified-flight-nid-list` |

Broader flight search (by date range, route, status, crew, etc.) and pre-commit sanity checks
(airport hours, aircraft double-booking, open defects) are deliberately out of scope here — those
belong to other skills. This one assumes you either already have a trip/flight identifier or can
get one from a trip number.

Resolve names/registrations/trip numbers to NIDs *before* calling a mutating tool — don't guess
an identifier. If a lookup returns more than one plausible match, show the candidates to the
user instead of picking one.

## Non-obvious things worth knowing

These are business-logic quirks, not field lists — they don't change every time the schema does.

1. **Trip vs. flight granularity.** `create-trip` makes a trip and its flights together (a round
   trip is just two flights in one call); `create-flight` only adds a leg to a trip that already
   exists. Using the wrong one either duplicates a trip or fails to extend one.
2. **Real and virtual aircraft are separate ID spaces and mutually exclusive per flight.** Never
   set both a real and a virtual aircraft identifier on the same flight, and never assume a
   virtual tail unless the user actually asked for one.
3. **Flights are cancelled, not deleted.** There's no "delete a single flight" — cancelling one
   also wipes its Journey Log, and undoing that is a separate restore call. "Delete this flight"
   from a user almost always means cancel; full removal only happens by deleting the whole trip.
4. **You can't read back a trip's notes/commercial flag/supplementary info before updating it.**
   There's no tool that returns those for an existing trip, so a partial `update-trip` call risks
   silently clearing what you didn't ask for — get the full desired state from the user rather
   than assuming untouched fields survive.
5. **Airport codes and airport location NIDs are two different identifier systems.** Tools that
   write flights want a code string (ICAO/IATA/FAA/custom); tools that search/filter want a
   numeric location NID. Don't resolve one when the tool you're calling wants the other.
6. **Times are UTC.** If the user gives a local time, convert it before calling — don't assume
   the number they gave you is already UTC.
7. **Trip/flight type and status enums aren't consistent across tools** — case and vocabulary
   differ between the tools that write them and the tools that read them back. Don't copy an
   enum value straight from one tool's output into another tool's input; check what the target
   tool actually accepts.
8. **Some tools explicitly forbid guessing a value** (e.g. flight distance, ICAO flight type) —
   leave it unset if the user didn't state it, rather than estimating.
9. **A field described as "optional" isn't always safe to omit.** Some schemas require the key
   to be present (even if nullable) even though it's conceptually optional. If a call gets
   rejected for a missing field, that's usually why.
10. **Creating a flight has side effects beyond writing the row.** The same automation that runs
    when a flight is created from the Leon UI also runs via the API: standard checklist items get
    generated, and crew already on duty for that aircraft/time may get auto-assigned. Don't
    assume a freshly created flight is a blank slate — check what actually landed on it.
11. **Save-time validation can be operator-specific.** Leon lets each operator configure which
    warnings on flight save are hard blockers versus dismissible, and which permission groups can
    dismiss them. The same payload can be accepted for one operator/user and rejected for
    another — don't treat a validation error as a universal rule.
12. **A flight with zero PAX can get auto-flagged as ferry/empty-leg depending on trip type**, and
    that automatic behavior has exceptions (e.g. Ambulance-type trips are excluded from it). If
    you set passenger count to 0, check the resulting flight rather than assuming the ferry/empty
    flag matches exactly what you sent.
13. **Trip number is always system-generated and immutable.** It's assigned automatically when
    `create-trip` runs — it can't be requested or set to a specific value at creation, and it
    can't be changed afterward via `update-trip` or any other tool. Don't ask the user what
    number they want, and don't offer to change one on an existing trip.
14. **Changing a flight's aircraft or airports invalidates its block time.** Block time is
    derived from the route and the aircraft flying it, so an `edit-flights` call that changes
    either one needs the block/flight time recalculated as part of the same edit — don't leave
    the old block time sitting on a flight after changing what it was calculated from.

## Common scenarios

For each: what to gather from the user first, then the tool sequence. No parameter-level detail
here — check the live schema of each tool when you actually call it.

### Create a new trip

**Collect:** route (departure/arrival airports — a leg per flight if it's a round trip or
multi-leg), date and time per leg (and which timezone the user is thinking in, if not stated as
UTC), aircraft (registration, or "virtual" if applicable), trip type and status if relevant to
the user's workflow. Don't ask for a trip number — it's always auto-generated and can't be set.

**Flow:** resolve the aircraft registration → resolve/convert times to UTC → `create-trip` with
one flight entry per leg → report back the resulting trip number and flight identifiers.

### Add a flight to an existing trip

**Collect:** which trip (number or NID), the new leg's route and time, and the aircraft for that
leg (may differ from the trip's other legs).

**Flow:** resolve the trip number to a NID (`search-trips-by-trip-number`) → optionally pull the
trip's existing legs for context (`get-trips-by-trip-nids`) → resolve the aircraft → `create-flight`.

### Edit an existing flight

**Collect:** which flight (number, or trip + leg description), and exactly what's changing
(time, route, aircraft, notes...) — only what's changing, not a full restatement of the flight.
If aircraft or airports are changing, also recalculate and include the new block time — see the
note above.

**Flow:** locate the flight — via its trip's flight list (`get-trips-by-trip-nids`) if you only
have a trip number, or directly with `get-flights-by-flight-nids` if you already have the flight
NID — then `edit-flights` with just the changed fields.

### Edit trip metadata

**Collect:** which trip, and the full desired state of every field being touched (type, status,
notes, commercial flag) — since there's no way to read the current notes/commercial flag/
supplementary info back before writing, don't assume anything not stated survives. Trip number
can't be changed here (or anywhere) — see the note above.

**Flow:** resolve the trip → `update-trip`.

### Reassign the aircraft on a flight

**Collect:** which flight(s), and the new aircraft (registration).

**Flow:** resolve the registration → `set-aircraft-on-flight`.

### Cancel or restore a flight

**Collect:** which flight, and whether they mean cancel (keeps the flight, marks it cancelled,
wipes its Journey Log) vs. actually wanting it gone (which means deleting the trip instead).

**Flow:** locate the flight (via its trip, or directly if you already have the flight NID) →
`cancel-flight`, or `restore-flights` to undo a prior cancellation.

### Delete a trip

**Collect:** which trip, and confirmation that removing every flight on it is intended.

**Flow:** resolve the trip number → pull its flight list so the user can see what's on it
(`get-trips-by-trip-nids`) → `delete-trip`.

### Manage tags on a flight

**Collect:** which flight, which tag(s) by name, and whether it's add/remove/clear-all.

**Flow:** resolve tag name(s) to their definitions (`search-flight-tags-by-name`) → `add-tags-to-flight` / `remove-tags-from-flight` / `clear-tags-from-flight`.

### Look up a trip or flight

**Collect:** a trip number (if that's all they have), or the trip/flight NID(s) if they already
know them.

**Flow:** `search-trips-by-trip-number` to turn a number into a NID; `get-trips-by-trip-nids` /
`get-flights-by-flight-nids` for full detail once you have the NID(s).
