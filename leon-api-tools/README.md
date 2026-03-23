# Leon API Tools — Claude Code Plugin

Claude Code skills for working with the **Leon Aviation API**. This plugin helps Leon Software support teams and integrators write validated GraphQL queries, design integration architectures, and generate complete integration guides.

## Skills

### `/leon-api-tools:gql-query-writer`

Generates, validates, debugs, and fixes GraphQL queries for the Leon API based on the live schema.

**Use when you need to:**
- Write new queries or mutations from scratch
- Validate an existing query against the current schema
- Debug and fix a broken query
- Look up available types, fields, and arguments

```
/leon-api-tools:gql-query-writer list of flights with crew assignments for a date range
```

The skill fetches the live Leon GraphQL schema from S3, discovers relevant types and fields, writes the query, and validates it automatically using a Python validator script.

**Requirements:** Python 3.9+ (packages `graphql-core` and `requests` are auto-installed on first run)

---

### `/leon-api-tools:leon-api-integration-architect`

Analyzes a Leon API integration requirement and produces a complete, validated integration design: auth method, required scopes, workflow steps, capability map, and validated GraphQL queries.

**Use when you need to:**
- Design an end-to-end API integration based on business requirements
- Determine which auth method, scopes, and queries an integrator needs
- Map business requirements to API capabilities and identify gaps
- Produce a structured integration design for Trip Support / Flight Support patterns

```
/leon-api-tools:leon-api-integration-architect we want to sync flight schedules with our ground handling system every hour
```

The skill delegates query validation to `gql-query-writer` to ensure every query in the design is verified against the live schema.

---

### `/leon-api-tools:integration-guide-writer`

Generates complete integration guides and workflow documentation for external Leon API integrators in Markdown, DOCX, or PDF format.

**Use when you need to:**
- Create a step-by-step integration guide for an external developer
- Produce guides in Markdown, DOCX, or PDF format
- Turn a validated integration design into a polished, developer-facing document

```
/leon-api-tools:integration-guide-writer we want to sync flight schedules with our ground handling system every hour
```

The skill delegates architecture analysis to `leon-api-integration-architect`, then formats the result into a guide that an external developer can execute top-to-bottom without confusion.

**Delegation chain:** `integration-guide-writer` -> `leon-api-integration-architect` -> `gql-query-writer`

---

## Installation

Add this plugin to Claude Code:

```bash
/plugin marketplace add leonaero/leon_software_marketplace
```

Or for local development:

```bash
claude --plugin-dir ./leon-api-tools
```

## Plugin Structure

```
leon-api-tools/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   ├── gql-query-writer/
│   │   ├── SKILL.md             # Skill definition
│   │   └── scripts/
│   │       ├── .gitignore
│   │       ├── requirements.txt # Python dependencies
│   │       └── validate_query.py  # Schema validator
│   ├── integration-guide-writer/
│   │   ├── SKILL.md             # Skill definition
│   │   └── scripts/
│   └── leon-api-integration-architect/
│       ├── SKILL.md             # Skill definition
│       ├── api-docs.md          # Leon API reference
│       └── workflow-trip-support.md  # Trip support workflow blueprint
├── README.md
└── LICENSE
```

## How It Works

1. **Schema fetching** — The `validate_query.py` script downloads the Leon GraphQL schema from the public S3 endpoint and caches it locally. The schema is the same one used by the [Leon API documentation portal](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/).

2. **Query validation** — Every query produced by the skills is validated against the live schema before being presented. No hallucinated fields or types.

3. **Integration architecture** — The `leon-api-integration-architect` skill analyzes business requirements, maps them to API capabilities, selects auth methods, designs workflows, and delegates query validation to `gql-query-writer`.

4. **Integration guides** — The `integration-guide-writer` skill delegates architecture analysis to `leon-api-integration-architect`, then formats the validated design into a polished, step-by-step guide that integrators can follow without any prior Leon API knowledge.

## Leon API Resources

- **API Documentation Portal:** http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/
- **Schema (Beta JSON):** https://api-schema-doc.s3.eu-west-1.amazonaws.com/schema-beta.json
- **Sample Queries:** https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/
- **API Registration Form:** https://leonsoftware.atlassian.net/servicedesk/customer/portal/4/group/8/create/40

## License

Apache 2.0
