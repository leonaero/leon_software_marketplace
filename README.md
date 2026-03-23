# Leon Software — Claude Code Plugin Marketplace

Official Claude Code plugin marketplace by **Leon Software**. Provides AI-powered skills for working with the Leon Aviation API — from writing validated GraphQL queries to generating complete integration guides for external developers.

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
