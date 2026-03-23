# Workflow: Trip Support / Flight Support Integration

> **Source:** [FlightSupport.md](https://bitbucket.org/leondevteam/api-documentation/src/master/standard-workflows/flight-support/FlightSupport.md) + integration diagram (TripSupportIntegrationDiagram.pdf)
>
> Use this document as the **primary blueprint** when generating guides for flight support and trip support companies (e.g. Jetex, Click Aviation, Hadid, Universal Aviation and similar providers of ground handling, permits, fuel, FBO, or trip coordination services to Leon operators).

---

## What is this integration?

This integration workflow is dedicated to **3rd party companies providing services to air operators using Leon**. It allows flight support providers to exchange data with Leon, reducing manual work and eliminating email-based coordination.

Leon users can request services directly from their flight checklist. The flight support company receives those requests via the API, arranges services, and writes results (status, messages, slot times, permits) back to Leon.

---

## Authentication

Flight support companies are **always 3rd party vendors** serving multiple Leon operators.

> **MANDATORY: OAuth 2.0 Code Grant.** API Key is not permitted.

**Required scope — only one:**

```
INTEGRATION_FLIGHT_SUPPORT
```

This single scope covers all queries and mutations in this integration. No additional scopes are needed.

---

## Architecture Overview

The integration has two directions:

```
Leon ──[FlightSupportQuery]──► Flight Support system
Leon ◄─[FlightSupportMutation]── Flight Support system
```

### Reading from Leon — `FlightSupportQuery`

| Query | When to use |
|-------|-------------|
| `getCreatedFlightServiceList` | Fetch newly created service requests from Leon operators |
| `getModifiedFlightServiceList` | Fetch service requests that have been changed |
| `getModifiedFlightScheduleList` | Fetch flights whose schedule has changed |

All three queries return the [`FlightSupportFlight`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightsupportflight.doc.html) type — find specific fields in the [`FlightSupportFlight`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightsupportflight.doc.html) type reference.

### Writing to Leon — `FlightSupportMutation`

| Mutation | Arguments | Purpose |
|----------|-----------|---------|
| `setServiceStatus` | `flightNid`, `services` | Update the status of arranged services — triggers checklist status updates in Leon |
| `sendFlightSupportMessage` | `flightNid`, `content`, `createdBy` | Send a message visible to the Leon operator |
| `setSlotAdepTime` | `flightNid`, `time` | Set the departure airport slot time |
| `setSlotAdesTime` | `flightNid`, `time` | Set the arrival airport slot time |
| `flightPermits` | (via `FlightPermitsMutation`) | Write permit data back to Leon |

---

## Workflow Steps

### Step 1 — Authenticate

OAuth 2.0 Code Grant with scope `INTEGRATION_FLIGHT_SUPPORT`. See `api-docs.md` for the full flow.

### Step 2 — Fetch new service requests

Poll `getCreatedFlightServiceList` to receive service requests that Leon operators have newly created for your company. Each result is a [`FlightSupportFlight`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightsupportflight.doc.html) containing the flight details and the list of requested services.

**Save this →** `flightNid` for each flight — used in all write-back mutations.

### Step 3 — Poll for changes

Poll two additional queries regularly:

- `getModifiedFlightServiceList` — operator has changed which services are requested (added, removed, or modified a service on an existing flight)
- `getModifiedFlightScheduleList` — flight schedule has changed (times, airports, aircraft, cancellation)

When either query returns results, update your internal records and re-process affected flights accordingly.

### Step 4 — Arrange services and write back to Leon

After arranging services, write results back using `FlightSupportMutation`:

**Update service status:**
```
setServiceStatus(flightNid, services)
```
Sets [`FlightSupportServiceStatus`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightsupportservicestatus.doc.html) for each service. This automatically updates the corresponding checklist item status in Leon (see mapping table below).

**Send a message to the operator:**
```
sendFlightSupportMessage(flightNid, content, createdBy)
```

**Set slot times:**
```
setSlotAdepTime(flightNid, time)
setSlotAdesTime(flightNid, time)
```

**Write permit data:**
```
flightPermits  [via FlightPermitsMutation]
```

---

## Service Configuration

### Available services

All possible services are listed in the [`FlightSupportServiceEnum`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightsupportserviceenum.doc.html) type reference.

By default, all services are available at all locations. To limit services per airport, use the mutation:

```
setFlightSupportAvailableAirportServiceList
```

Sample query: [setFlightSupportAvailableAirportServiceList.txt](https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/flight-support/mutation/setFlightSupportAvailableAirportServiceList.txt)

> If you define a list for any airport, services will be available **only** at airports for which a list is explicitly defined.

---

## Service Status → Checklist Status Mapping

When `setServiceStatus` is called, Leon automatically updates the corresponding checklist item. The mapping is:

| Flight Support Service | Checklist Item | PENDING | ACTIVE | BRIEFED | CONFIRMED | COMPLETED | CANCELLED | NOT_REQUIRED |
|------------------------|---------------|---------|--------|---------|-----------|-----------|-----------|--------------|
| CATERING_ADEP | Catering | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| CREW_TRANSPORT_ADEP | Crew Transport (ADEP) | RQS | RQS | RQS | YES | YES | QSM | NAP |
| HANDLING_ADEP | Handling (ADEP) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| PAX_TRANSPORT_ADEP | PAX transport (ADEP) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| PPR_ADEP | PPR (ADEP) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| SLOT_ADEP | Slot (ADEP) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| TAKE_OFF_PERMIT_ADEP | Departure Permission | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| VIP_LOUNGE_ADEP | VIP Lounge (ADEP) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| CREW_TRANSPORT_ADES | Crew Transport (ADES) | RQS | RQS | RQS | YES | YES | QSM | NAP |
| HANDLING_ADES | Handling (ADES) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| PAX_TRANSPORT_ADES | PAX transport (ADES) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| PPR_ADES | PPR (ADES) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| SLOT_ADES | Slot (ADES) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| VIP_LOUNGE_ADES | VIP Lounge (ADES) | RQS | RQS | RQS | CNF | CNF | REJ | NAP |
| FUEL_ADEP | Fuel | RQS | RQS | RQS | YES | YES | QSM | NAP |
| PRELIMINARY_FPL_PREPARATION_ADEP | Preliminary FPL | PRS | PRS | PRS | CNF | CNF | REJ | NAP |
| FINAL_FPL_PREPARATION_ADEP | Final FPL | PRS | PRS | PRS | CNF | CNF | REJ | NAP |
| ATC_FPL_FILING_ADEP | ATC flight plan | OKI | OKI | OKI | ACK | ACK | NOO | NAP |
| WEATHER_PACKAGE_ADEP | Weather | RQS | RQS | RQS | ACK | ACK | QSM | NAP |
| JEPPESEN_CHARTS_ADEP | Jeppesen | RQS | RQS | RQS | ACK | ACK | QSM | NAP |
| AIRPORT_FEES_ADEP | Airport Fees (ADEP) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| AIRPORT_FEES_ADES | Airport Fees (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| TECHNICAL_LANDING_ADES | Landing permit(s) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| HOTEL_ADES | Hotel | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| CREW_VISA_ADES | Crew Visa (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| API_ADEP | API (ADEP) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| API_ADES | API (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| PARKING_ADES | Parking | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| SECURITY_ADEP | Security (ADEP) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| SECURITY_ADES | Security (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| SUPERVISION_ADEP | Supervision (ADEP) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| SUPERVISION_ADES | Supervision (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| EQUIPMENT_ADEP | Equipment (ADEP) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| EQUIPMENT_ADES | Equipment (ADES) | PRS | PRS | CNF | CNF | CNF | REJ | NAP |
| STANDARD_BRIEFING_ADEP | Standard briefing | PRS | PRS | COM | COM | COM | REJ | NAP |
| STANDARD_EROPS_BRIEFING_ADEP | Standard EROPS briefing | PRS | PRS | COM | COM | COM | REJ | NAP |
| EAPIS_ADEP | eAPIS (ADEP) | YES | YES | YES | YES | YES | QSM | NAP |
| EAPIS_ADES | eAPIS (ADES) | YES | YES | YES | YES | YES | QSM | NAP |
| CBP_US_ADEP | CBP US (ADEP) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| CBP_US_ADES | CBP US (ADES) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| CATERING_ADES | Catering (ADES) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| HANGAR_ADEP | Hangar (ADEP) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |
| HANGAR_ADES | Hangar (ADES) | RQS | RQS | CNF | CNF | CNF | REJ | NAP |

**Status codes:** RQS = Requested, CNF = Confirmed, REJ = Rejected, YES = Yes, QSM = ?, PRS = In progress, OKI = OK, ACK = Acknowledged, COM = Completed, NOO = No, NAP = Not Applicable

**Fallback rule:** If the target checklist status is not found (e.g. disabled by the operator), the best available match is applied in priority order. If no match is found, `QSM` (question mark) is set.

---

## Sample Queries

Full sample queries covering all scenarios are available at:
https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/flight-support/

---

## Leon User Documentation

- [Integration configuration in Leon](https://wiki.leonsoftware.com/leon/integrations#flight-support-service-providers-and-suppliers)
- [Making a request from Leon checklist](https://wiki.leonsoftware.com/leon/checklist#integrated-flight-service-providers-and-suppliers)

---

## Notes for Guide Generation

1. **One scope only** — `INTEGRATION_FLIGHT_SUPPORT` covers everything. Do not add other scopes.
2. **Validate all queries** via `gql-query-writer` before including in the guide — use the sample queries at the Bitbucket link above as a reference, but always validate against the live schema.
3. **This is a bidirectional integration** — always document both the read and write sides.
4. **Service status → checklist mapping** is important for operators to understand — include the relevant rows from the table above in the guide, filtered to only the services the integrator actually uses.
5. **Contact for issues:** customer portal at customer.leon.aero.
