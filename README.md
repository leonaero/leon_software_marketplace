# Leon Software — Claude Code Plugin Marketplace

Official Claude Code plugin marketplace by **Leon Software**. Provides AI-powered skills for working with Leon — from writing validated GraphQL queries against the Leon Aviation API to operating the Leon MCP server through natural language.

## Available Plugins

### [Leon API Tools](./leon-api-tools)

Claude Code skills for writing validated GraphQL queries, designing integration architectures, and generating integration guides for the Leon Aviation API.

**Skills included:**

| Skill | Description |
|-------|-------------|
| `/leon-api-tools:gql-query-writer` | Write, validate, debug, and fix GraphQL queries against the live Leon schema |
| `/leon-api-tools:leon-api-integration-architect` | Analyze integration requirements and produce validated designs with auth, scopes, and workflows |
| `/leon-api-tools:integration-guide-writer` | Generate polished integration guides in Markdown, DOCX, or PDF format |

Skills work together via delegation: `integration-guide-writer` delegates to `leon-api-integration-architect`, which delegates query validation to `gql-query-writer`. Every query is validated against the live schema — no hallucinated fields or types.

**Requirements:** Python 3.9+

### [Leon MCP Skills](./leon-mcp-skills)

A set of skills dedicated to operators who have connected the **Leon MCP server**. Once the MCP is connected in your Claude Code client (see [Using the Leon MCP Server](#using-the-leon-mcp-server) below), these skills route each request to the right MCP tool, in the right order, and flag the business-logic quirks a raw tool schema won't warn you about.

**Skills included:**

| Skill | Description |
|-------|-------------|
| `/leon-mcp-skills:leon-flight-search` | Find and look up flights by date range, route, aircraft, crew, status, tags, trip, or NID |
| `/leon-mcp-skills:leon-trip-manager` | Manage the trip/flight lifecycle — create, edit, cancel/restore, delete, reassign aircraft, tag |
| `/leon-mcp-skills:leon-report-builder` | Build custom, column-driven Report Wizard reports and export them as HTML, Excel, or PDF |

**Requirements:** a connected Leon MCP server (see below).

## Using the Leon MCP Server

The `leon-mcp-skills` plugin operates Leon's **Model Context Protocol (MCP)** server, so that server must be connected in your Claude Code client before those skills can do anything.

### What is Model Context Protocol (MCP)?

The **Model Context Protocol (MCP)** is an open standard that lets AI agents and tools communicate with applications in a structured, secure way. MCP servers expose data and functionality that clients (such as AI agents) can access, enabling workflow automation and seamless integration between systems. Read more about the standard at [modelcontextprotocol.io](https://modelcontextprotocol.io/).

### Accessing Leon's MCP server

Each operator account has its own dedicated MCP server:

```
https://{oprId}.mcpserver.leon.aero/
```

where `{oprId}` is your **operator account identifier** in Leon.

### Authentication

All requests to the MCP server require an **access token**, passed in the `Authorization` header of every HTTP request:

```
Authorization: Bearer {access_token}
```

### Obtaining access tokens

Access tokens can be created in two ways:

1. **Using a manually created API key**
2. **Using the OAuth code grant**

### Example request

```http
GET https://{oprId}.mcpserver.leon.aero/mcp
Authorization: Bearer {access_token}
```

## Installation

```bash
/plugin marketplace add leonaero/leon_software_marketplace
```

## Leon API Resources

- **API Documentation Portal:** http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/
- **Schema (Beta JSON):** https://api-schema-doc.s3.eu-west-1.amazonaws.com/schema-beta.json
- **Sample Queries:** https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/
- **API Registration Form:** https://leonsoftware.atlassian.net/servicedesk/customer/portal/4/group/8/create/40

## License

Apache 2.0
