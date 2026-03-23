# Leon API Tools — Claude Code Plugin

Claude Code skills for working with the **Leon Aviation API**. This plugin helps Leon Software support teams and integrators write validated GraphQL queries and generate complete integration guides.

## Skills

### `/leon-api-tools:write-graphql-query`

Generates, validates, debugs, and fixes GraphQL queries for the Leon API based on the live schema.

**Use when you need to:**
- Write new queries or mutations from scratch
- Validate an existing query against the current schema
- Debug and fix a broken query
- Look up available types, fields, and arguments

```
/leon-api-tools:write-graphql-query list of flights with crew assignments for a date range
```

The skill fetches the live Leon GraphQL schema from S3, discovers relevant types and fields, writes the query, and validates it automatically using a Python validator script.

**Requirements:** Python 3.9+ (packages `graphql-core` and `requests` are auto-installed on first run)

---

### `/leon-api-tools:integration-guide-writer`

Generates complete integration guides and workflow documentation for external Leon API integrators.

**Use when you need to:**
- Create a step-by-step integration guide for an external developer
- Design an end-to-end API workflow based on business requirements
- Produce guides in Markdown, DOCX, or PDF format

```
/leon-api-tools:integration-guide-writer we want to sync flight schedules with our ground handling system every hour
```

The skill analyzes the business requirement, maps it to API capabilities, designs a numbered workflow, writes and validates all example queries, and outputs a production-ready guide. Includes built-in support for Trip Support / Flight Support integration patterns.

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
│   ├── plugin.json              # Plugin manifest
│   └── settings.json            # Default permissions
├── skills/
│   ├── integration-guide-writer/
│   │   ├── SKILL.md             # Skill definition
│   │   ├── api-docs.md          # Leon API reference
│   │   └── workflow-trip-support.md  # Trip support workflow blueprint
│   └── write-graphql-query/
│       ├── SKILL.md             # Skill definition
│       ├── requirements.txt     # Python dependencies
│       └── scripts/
│           └── validate_query.py  # Schema validator
├── README.md
├── LICENSE
└── .gitignore
```

## How It Works

1. **Schema fetching** — The `validate_query.py` script downloads the Leon GraphQL schema from the public S3 endpoint and caches it locally. The schema is the same one used by the [Leon API documentation portal](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/).

2. **Query validation** — Every query produced by the skills is validated against the live schema before being presented. No hallucinated fields or types.

3. **Integration guides** — The guide writer skill cross-references the API documentation, authentication flows, and schema to produce step-by-step guides that integrators can follow without any prior Leon API knowledge.

## Leon API Resources

- **API Documentation Portal:** http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/
- **Schema (Beta JSON):** https://api-schema-doc.s3.eu-west-1.amazonaws.com/schema-beta.json
- **Sample Queries:** https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/
- **API Registration Form:** https://leonsoftware.atlassian.net/servicedesk/customer/portal/4/group/8/create/40

## License

Apache 2.0
