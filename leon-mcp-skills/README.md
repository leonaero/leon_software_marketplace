# Leon MCP Skills — Claude Code Plugin

Claude Code skills for operating the **Leon MCP server** through natural language. This plugin is dedicated to operators who have connected the Leon MCP server (see [Prerequisite](#prerequisite-the-leon-mcp-server) below). Once the MCP is connected, these skills route each request to the right MCP tool, in the right order, with the business-logic quirks a raw tool schema won't warn you about.

## Skills

### `/leon-mcp-skills:leon-flight-search`

Searches for and looks up flights in Leon via the Leon MCP tools.

**Use when you need to:**
- Find flights by date range, route, aircraft, crew, status, cancellation, ferry flag, or tags
- Find all flights on a trip you already know the number for
- Pull full detail (aircraft, times, actual Journey Log data) once you have flight NIDs
- Check the last flight from/to a given airport, or see what changed recently

```
/leon-mcp-skills:leon-flight-search show me flights from EGLL to LFPB last week
```

Picks the right tool among several overlapping search tools and flags the pagination, date-range, and default-value traps a schema alone won't surface.

---

### `/leon-mcp-skills:leon-trip-manager`

Manages the trip and flight lifecycle in Leon via the Leon MCP tools.

**Use when you need to:**
- Create a trip together with its flights, or add a flight to an existing trip
- Edit flights or trip metadata
- Cancel/restore a flight, or delete a trip
- Reassign an aircraft, or add/remove flight and trip tags

```
/leon-mcp-skills:leon-trip-manager create a trip for D-LEON, EPWA-EDDF tomorrow at 09:00
```

Ensures the right tool is picked in the right order, with the required information gathered up front.

---

### `/leon-mcp-skills:leon-report-builder`

Builds custom, column-driven data reports in Leon via the Report Wizard MCP tools.

**Use when you need to:**
- Generate a custom report or data extract that goes beyond a simple lookup
- Choose columns and filters and deliver the result as HTML, Excel, or PDF

```
/leon-mcp-skills:leon-report-builder export all flights this month with block times to Excel
```

Describes the general `columns-list` → `report` workflow for any Report Wizard scope. Flight is the only scope available today; more scopes follow the same two-tool pattern.

---

## Prerequisite: the Leon MCP Server

These skills operate the Leon MCP server, so that server must be connected in your Claude Code client first. Each operator account has its own dedicated MCP server. See **[Using the Leon MCP Server](../README.md#using-the-leon-mcp-server)** in the marketplace README for the full connection and authentication instructions.

In short:

- **Server URL:** `https://{oprId}.mcpserver.leon.aero/` — where `{oprId}` is your operator account identifier.
- **Authentication:** every request needs an access token in the `Authorization: Bearer {access_token}` header. Tokens are created via a manually-created API key or the OAuth code grant.

## Installation

Add this plugin to Claude Code:

```bash
/plugin marketplace add leonaero/leon_software_marketplace
```

Or for local development:

```bash
claude --plugin-dir ./leon-mcp-skills
```

## Plugin Structure

```
leon-mcp-skills/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   ├── leon-flight-search/
│   │   └── SKILL.md             # Flight search skill
│   ├── leon-trip-manager/
│   │   └── SKILL.md             # Trip/flight lifecycle skill
│   └── leon-report-builder/
│       └── SKILL.md             # Report Wizard skill
├── README.md
└── LICENSE
```

## How It Works

Each skill is a routing and know-how layer over the live Leon MCP tools:

1. **Right tool for the job** — the Leon MCP exposes many similarly-named tools. Each skill maps the request to the correct tool (and the correct order of calls) instead of guessing.
2. **Schema is the source of truth** — the skills read the live tool schema for exact field names and constraints, and layer on the business-logic quirks a schema can't express.
3. **Trap avoidance** — pagination limits, date-range defaults, cancellation/restore semantics, and other easy-to-miss behaviors are called out so requests don't silently return the wrong data.

## License

Apache 2.0
