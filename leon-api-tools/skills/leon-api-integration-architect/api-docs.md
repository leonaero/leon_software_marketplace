# Leon API Documentation — Reference Extract

> Source: https://bitbucket.org/leondevteam/api-documentation
> Extracted for use by the `leon-api-integration-architect` skill.

---

## API Endpoint

### Production
```
https://{oprId}.leon.aero/api/graphql/
```

### Development / Sandbox
```
https://{oprId}.sandbox.leon.aero/api/graphql/
```

**What is `{oprId}`?**
Each Leon operator has a dedicated subdomain used to sign in. The `oprId` is the first segment of that domain.
Example: if the operator signs in at `demo.leon.aero`, then `oprId = demo`.
If you don't know the oprId, ask any user of that Leon instance what address they use to sign in.

---

## Authentication — CRITICAL RULES

> ⚠️ **The authentication method is NOT a free choice. It depends on who is building the integration.**

### Rule 1 — 3rd party software providers MUST use OAuth 2.0 Code Grant

If you are building software that will be used by **multiple Leon operators** (i.e., you are a vendor, a marketplace, a flight support company, an EFB provider, or any other 3rd party application developer), you **must** use the **OAuth 2.0 Code Grant** method.

- Your integration **will be visible in the Leon Addons panel**
- Your application must be **registered with Leon** before development can begin
- Using API Key instead of OAuth for a multi-operator application is **not permitted**

### Rule 2 — API Key is only for single-operator custom integrations

If you are a Leon **customer** building an integration **exclusively for your own operator** (internal tooling, custom scripts, one-off automation), you may use the manually created API Key method.

- These integrations **will NOT be visible in the Addons panel**
- The API Key is tied to a specific operator — it cannot be used across multiple operators
- This method is **not suitable for 3rd party software products**

---

## Authentication Method A — OAuth 2.0 Code Grant (mandatory for vendors)

### Step 0 — Register your application

Before any development, submit the registration form to Leon:
https://leonsoftware.atlassian.net/servicedesk/customer/portal/4/group/8/create/40

Required information:
- Application name
- Application type (marketplace, flight support, EFB, SMS, pilot logbook, etc.)
- Redirect URI (where Leon sends the browser after user consent)
- Application description (displayed in Addons panel)
- Phone number for securing the client secret
- Application / company logo
- Contact information
- Company website URL

After registration, Leon provides:
- `client_id`
- `client_secret`

Development and testing can be done on `sandbox.leon.aero`. Production access requires a demo meeting with Leon after development is complete.

---

### Step 1 — Request authorization code

Redirect the operator's admin user to:

```
https://{oprId}.leon.aero/oauth2/code/authorize/?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE_LIST}&state={OPTIONAL_STATE}
```

Parameters:
- `{oprId}` — operator's Leon ID (provided by the operator)
- `{CLIENT_ID}` — your client ID from registration
- `{REDIRECT_URI}` — must exactly match the URI submitted during registration
- `{SCOPE_LIST}` — space-delimited list of required scopes (see Scope List section)
- `{OPTIONAL_STATE}` — optional CSRF protection value; will be echoed back to your redirect URI

> Note: For most applications, only users with **admin privileges** can authorize a 3rd party application.
> Exception: "personal" applications (e.g., pilot logbook) can be authorized by individual users.

After the user grants consent, Leon redirects the browser to your `{REDIRECT_URI}` with:
- `code` — authorization code (single-use, valid for 10 minutes)
- `state` — echoed back if you provided it

---

### Step 2 — Exchange authorization code for tokens

```bash
curl --location --request POST 'https://{oprId}.leon.aero/oauth2/code/token/' \
    --form 'grant_type="authorization_code"' \
    --form 'client_id="{CLIENT_ID}"' \
    --form 'client_secret="{CLIENT_SECRET}"' \
    --form 'redirect_uri="{REDIRECT_URI}"' \
    --form 'code="{AUTHORIZATION_CODE}"'
```

> ⚠️ Note the trailing slash in the URL — it is required.

Successful response:
```json
{
    "token_type": "Bearer",
    "expires_in": 1234567890,
    "access_token": "{ACCESS_TOKEN}",
    "refresh_token": "{REFRESH_TOKEN}"
}
```

Token lifecycle:
- **Access token** — valid for **30 minutes**
- **Refresh token** — valid for **30 days since last use**

---

### Step 3 — Refresh the access token (when expired)

```bash
curl --location --request POST 'https://{oprId}.leon.aero/oauth2/code/token/' \
    --form 'grant_type="refresh_token"' \
    --form 'client_id="{CLIENT_ID}"' \
    --form 'client_secret="{CLIENT_SECRET}"' \
    --form 'refresh_token="{REFRESH_TOKEN}"'
```

---

### Step 4 — Make GraphQL requests

```bash
curl 'https://{oprId}.leon.aero/api/graphql/' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer {ACCESS_TOKEN}' \
    --data-binary '{"query":"{ ... }"}'
```

---

### ⚠️ Token Management Rules (critical for OAuth integrations)

**Do NOT generate a new access token for each API call.**

- There is a limit of **500 active access tokens per refresh token**
- Each access token is valid for **30 minutes**
- If the limit is exceeded, Leon returns HTTP `429 Too Many Requests` with a `Retry-After` header
- **Correct pattern:** obtain one access token, reuse it for all calls until it expires, then refresh

---

## Authentication Method B — API Key (single-operator only)

> ⚠️ Only use this method if you are building an integration for a single operator's internal use.
> 3rd party software vendors must NOT use this method.

### Step 1 — Generate a Refresh Token in Leon

The operator creates an API key in Leon at:
https://wiki.leonsoftware.com/leon/api-keys

This produces a `RefreshToken`.

### Step 2 — Exchange Refresh Token for Access Token

```bash
curl -X POST -d 'refresh_token={RefreshToken}' https://{oprId}.leon.aero/access_token/refresh/
```

Response: a short-lived access token (30 minutes), returned as plain text.

### Step 3 — Make GraphQL requests

```bash
curl 'https://{oprId}.leon.aero/api/graphql/' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer {ACCESS_TOKEN}' \
    --data-binary '{"query":"{ ... }"}'
```

---

## Scope List

Required scopes must be declared during OAuth authorization. Include only the scopes your application actually needs.

| Scope | Description |
|-------|-------------|
| `GRAPHQL_ACFT` | Aircraft see |
| `GRAPHQL_ACFT_EDIT` | Aircraft edit |
| `GRAPHQL_ACTIVITY_HISTORY` | Activity history |
| `GRAPHQL_AIRCRAFT_ACTIVITIES` | Aircraft activities |
| `GRAPHQL_AIRCRAFT_AVAILABILITY` | Aircraft availability |
| `GRAPHQL_AIRCRAFT_FLIGHTS` | Aircraft flights list |
| `GRAPHQL_CREW_AVAILABILITY` | Crew availability |
| `GRAPHQL_AIRPORT` | Airport |
| `GRAPHQL_CREW_MEMBER` | Crew Members |
| `GRAPHQL_CREW_MEMBER_EDIT` | Crew Members edit |
| `GRAPHQL_CREW_PANEL` | Crew Calendar and Timeline |
| `GRAPHQL_DUTY_EDIT` | Duty edit |
| `GRAPHQL_DUTY_SEE` | Duty see |
| `GRAPHQL_FEASIBILITY_CHECK` | Feasibility check |
| `GRAPHQL_FLIGHT` | Flight see |
| `GRAPHQL_FLIGHT_EDIT` | Flight edit |
| `GRAPHQL_FLIGHT_WATCH` | Flight Watch see |
| `GRAPHQL_FLIGHT_WATCH_EDIT` | Flight Watch edit |
| `GRAPHQL_FTL` | FTL |
| `GRAPHQL_HANDLING_AGENT` | Handling Agents |
| `GRAPHQL_JOURNEY_LOG` | Journey Log |
| `GRAPHQL_JOURNEY_LOG_EDIT` | Journey Log edit |
| `GRAPHQL_OPERATOR` | Operator |
| `GRAPHQL_PASSENGER` | PAX List see |
| `GRAPHQL_PASSENGER_EDIT` | PAX List edit |
| `GRAPHQL_POSITIONING_SEE` | Positioning see |
| `GRAPHQL_POSITIONING_EDIT` | Positioning edit |
| `GRAPHQL_RESERVATION_SEE` | Reservation see |
| `GRAPHQL_RESERVATION_EDIT` | Reservation edit |
| `GRAPHQL_SALES_BOOKINGS` | Bookings |
| `GRAPHQL_SALES_QUOTE_EDIT` | Quote edit |
| `GRAPHQL_SCHEDULE_ORDER_SEE` | Schedule see |
| `GRAPHQL_SCHEDULE_ORDER_EDIT` | Schedule edit |
| `GRAPHQL_CONTACT` | Contact see |
| `GRAPHQL_CONTACT_EDIT` | Contact edit |
| `GRAPHQL_LOGIN` | Login |
| `INTEGRATION_FLIGHT_SUPPORT` | Integration Flight Support |
| `LOGBOOK` | Logbook |

Full scope list: https://bitbucket.org/leondevteam/api-documentation/raw/master/authentication/ScopeList.md

---

## Data Synchronization Strategy — Polling vs Webhooks

> **Recommended approach for synchronization: polling with `*Changes` queries.**
> Webhooks (GraphQL subscriptions) are supported but polling is more reliable for most integration use cases.

### Option A — Polling with `*Changes` queries (PREFERRED)

Leon exposes dedicated queries for fetching records that have changed since a given point in time. These are the recommended approach for keeping an external system in sync with Leon data.

Example: [`flightsChanges`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightschanges.doc.html) — returns flights that have been created, modified, or cancelled since a given timestamp.

**Why prefer polling:**
- Stateless — no webhook endpoint to maintain
- Resilient to downtime — if your system is offline, you catch up on the next poll by using the last-processed timestamp
- Predictable load — you control the polling interval
- No JWT validation infrastructure required

**Recommended polling interval:** 1–5 minutes for near-real-time sync; longer for batch use cases.

**Pattern:**
1. Store `lastSyncTimestamp` after each successful poll
2. Call `*Changes` query with `since: lastSyncTimestamp`
3. Process returned records
4. Update `lastSyncTimestamp` to current time

### Option B — GraphQL Subscriptions via Webhooks

Leon supports event-driven notifications by registering a GraphQL subscription as a webhook. When a subscribed event occurs, Leon POSTs the subscription payload to your specified URL.

**When webhooks may be appropriate:**
- You need sub-minute latency and cannot tolerate polling delay
- You are building a UI or notification system that must react instantly
- The `*Changes` query does not cover the specific event you need

**Webhook limits:**
- Maximum **10 webhooks per refresh token** at any given time
- Each webhook is tied to a specific refresh token (valid 30 days, extended on access token generation)

**Registration:** use the `createSubscriptionWebhook` mutation (see [`WebhookMutationSection`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/webhookmutationsection.doc.html)):

```graphql
mutation {
  webhook {
    createSubscriptionWebhook(
      refreshToken: "<refreshToken>",
      label: "MY_WEBHOOK",           # unique, min 5 characters
      subscription: "subscription Sub($var: String!) { ... }",
      variables: "{\"var\": \"value\"}",
      webhookUrl: "<your-endpoint-url>"
    ) {
      ... on NonNullBooleanValue { result: value }
      ... on CreateSubscriptionWebhookViolationList {
        error: value { message path }
      }
    }
  }
}
```

**Deletion:**
```graphql
mutation {
  webhook {
    deleteSubscriptionWebhook(label: "MY_WEBHOOK")
  }
}
```

**Notification format:**
- Leon sends a **POST** request to your `webhookUrl`
- Body: JSON containing the subscription payload
- Header: `Authorization: Bearer <JWT>` — **must be validated** before trusting the payload

**JWT validation (mandatory for security):**
- Algorithm: **RS512**
- Public key: `https://{oprId}.leon.aero/.well-known/keys/leon-subscriptions-webhook-1.pub`
- Required claims to verify:
  - `iss` must equal `Leon Software`
  - `aud` must equal the webhook URL you registered
  - `exp` must not be in the past

**Available subscriptions:** [`http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/subscription.doc.html`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/subscription.doc.html)

---

## Schema & Validation

- **Beta schema (JSON):** https://api-schema-doc.s3.eu-west-1.amazonaws.com/schema-beta.json
- **Staging schema (JSON):** http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/schema-staging.json
- **Documentation portal:** http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/

> The staging schema is updated daily after 07:00 UTC and reflects the next production release.
> It is recommended to validate your integration against the staging schema automatically before each Leon release.

---

## GraphQL Tooling

Recommended clients for development:
- [Altair GraphQL Client](https://altairgraphql.dev/) — standalone desktop/browser client
- [Prisma GraphQL Playground](https://github.com/prisma/graphql-playground) — IDE for GraphQL

---

## FAQ

**I am a 3rd party application developer. What do I do?**
Follow the OAuth 2.0 Code Grant flow. This is mandatory. Start by submitting the registration form.

**I am a Leon customer building an internal tool. What do I do?**
Use the manually created API Key method. Create the key in Leon's API Keys settings.

**The data I need is missing from the schema. What do I do?**
Contact Leon Support via the customer portal at customer.leon.aero describing what queries or mutations you need.

**Where are sample queries?**
https://bitbucket.org/leondevteam/api-documentation/src/master/sample-queries/