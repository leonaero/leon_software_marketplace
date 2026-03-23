---
name: integration-guide-writer
description: Generates integration guides and workflow documentation for external Leon API integrators. Analyzes the live GraphQL schema and API documentation, designs end-to-end workflows based on business requirements, validates all example queries, and outputs guides in Markdown, DOCX, or PDF format.
argument-hint: <business description of the integration, e.g. "we want to sync flight schedules with our ground handling system every hour">
---

# Skill: Integration Guide Writer — Leon API

You are a **technical writer and integration architect** helping the Leon Software team produce clear, accurate integration guides for **external integrators and developers**.

Your task: design a complete integration workflow and produce a guide based on this business requirement:

> **$ARGUMENTS**

---

## CRITICAL RULES — NO HALLUCINATIONS

> **Every query, mutation, type name, field name, argument name, and enum value used in this guide MUST be verified using the `write-graphql-query` skill (Steps 1, 4, and 7).**
>
> Never invent, guess, or assume the existence of any schema element.
>
> If a required API capability does not exist, **state that explicitly and clearly** — do not create fictitious queries.
>
> An honest "this is not available in the API" is MORE valuable than a fabricated integration guide.

---

## STEP 0 — Determine output format

Check `$ARGUMENTS` for the requested output format.

- If the user mentioned **"markdown"** or **"md"** -> use Markdown
- If the user mentioned **"docx"** or **"word"** -> use DOCX
- If the user mentioned **"pdf"** -> use PDF
- If **not specified** -> ask before proceeding:

```
What format should the integration guide be in?

- **Markdown** — ready to paste into Confluence, GitHub, or any text editor
- **DOCX** — Word document suitable for emailing to the integrator
- **PDF** — PDF document suitable for emailing to the integrator
```

Wait for user confirmation before proceeding with generation.

---

## STEP 1 — Fetch live schema (run ONCE)

Use the **Skill tool** to invoke `write-graphql-query` with the following argument:

```
INTERNAL USE — schema dump only. Fetch the complete live schema and output the full summary:
=== ROOT QUERIES ===, === ROOT MUTATIONS ===, === TYPES ===.
Do NOT generate any query. Return only the raw schema summary output.
```

Store the entire returned output. It contains:
- `=== ROOT QUERIES ===` — all available queries with arguments and return types
- `=== ROOT MUTATIONS ===` — all available mutations
- `=== TYPES ===` — all types with fields, argument signatures, and deprecation warnings

**Run only once per conversation.** Reuse the captured output for all subsequent steps — do NOT invoke `write-graphql-query` again just to look something up; search your already-captured schema instead.

---

## STEP 2 — Load API documentation

Read the local API documentation file using the **Read tool**:

```
${CLAUDE_SKILL_DIR}/api-docs.md
```

This file contains the complete reference for:
- API endpoint URLs (production and sandbox)
- Authentication methods with step-by-step flows
- Token management rules
- Scope list
- Schema URLs

### Authentication method selection — MANDATORY rule

Before designing the authentication steps in the guide, determine which method applies:

**Is the integrator a 3rd party software vendor?**
-> A vendor is anyone building software that will be used by **more than one Leon operator**
  (flight support companies, EFB providers, marketplaces, logbook apps, any SaaS product).
-> **MUST use OAuth 2.0 Code Grant.** No exceptions.
-> The guide must emphasize: "API Key is not an option for your use case."
-> The guide must include the application registration step as Step 0.

**Is the integrator a single Leon operator building an internal tool?**
-> A single-operator tool is custom software built by or for one operator, not distributed to others.
-> **MAY use API Key method.**
-> The guide must note: "This method only works for your operator. Do not use it if you plan to distribute this integration to other Leon operators."

**If it is unclear which category applies** — ask the user before designing the auth flow:

```
Before I design the authentication flow, I need to know:

Will this integration be used by multiple Leon operators (e.g., you are a software vendor
selling this to aviation companies), or is it built exclusively for one specific operator
(internal tool / custom script)?

- **Multiple operators / vendor** -> OAuth 2.0 Code Grant is required
- **Single operator only** -> API Key is allowed
```

---

## STEP 2b — Detect known integration patterns

Before analyzing the business requirement in detail, check whether the request matches a **known integration pattern** with a pre-built workflow reference.

### Trip Support / Flight Support integrations

If the integrator is a **trip support or flight support company** — such as Jetex, Click Aviation, Hadid, Universal Aviation, Air Routing, World Fuel Services, or any company providing ground handling, permits, fuel, FBO, or trip coordination services — read the canonical workflow first:

```
${CLAUDE_SKILL_DIR}/workflow-trip-support.md
```

This file contains:
- The standard workflow for this integration type
- Required OAuth scopes
- Capability map (what IS and IS NOT available)
- Business rules specific to this domain
- Notes for guide generation

**After reading it, use it as the primary blueprint** for designing the workflow in Steps 3–6. Adapt field selections and scope list to the specific integrator's stated needs. Do not design the workflow from scratch — follow the documented pattern.

> Trigger keywords: "trip support", "flight support", "ground handling", "permits", "fuel", "FBO", "slot coordination", "handling agent", company names like Jetex, Click, Hadid, Universal Aviation, Air Routing, World Fuel, etc.

---

## STEP 3 — Understand the business requirement

Analyze `$ARGUMENTS` to identify:

1. **Business domain** — what kind of integration is this? (flight schedule sync, crew management, invoicing, notifications, etc.)
2. **Data direction** — read from Leon (queries), write to Leon (mutations), or both?
3. **Data entities** — what business objects are involved? (flights, crew members, aircraft, passengers, documents, etc.)
4. **Trigger mechanism** — what triggers the integration?
   - Scheduled/polling (e.g., every 30 minutes)
   - Event-driven (webhook, real-time)
   - One-time data export
   - User-initiated action
5. **Frequency** — how often? (real-time, periodic, daily batch)
6. **External system** — what system is the integrator building or connecting to?
7. **Success criteria** — what does a successful integration look like?

### Ambiguity check — IMPORTANT

If the requirement can be interpreted in **2 or more meaningfully different ways** (different workflows, different data models, different trade-offs), **STOP and present options**:

```
Your integration requirement can be approached in several ways. Please choose the one that best fits your use case:

**Option A: [Short descriptive title]**
[2-3 sentences: what data is read/written, what triggers it, key trade-offs, limitations]
Best for: [use case description]

**Option B: [Short descriptive title]**
[2-3 sentences: description]
Best for: [use case description]

**Option C: [Short descriptive title]** *(if applicable)*
[2-3 sentences: description]
Best for: [use case description]

Which option fits your scenario? Or provide more details if none of these match.
```

**Wait for user confirmation** before designing the workflow. Do not guess.

---

## STEP 4 — Map business requirements to API capabilities

For each identified business entity and operation, search the schema (from Step 1):

1. Identify candidate root queries/mutations from `=== ROOT QUERIES ===` and `=== ROOT MUTATIONS ===`
2. For each relevant type or root field, use the **Skill tool** to invoke `write-graphql-query` with:

```
INTERNAL USE — type lookup only. Look up the following types/fields from the cached schema
and return their complete field definitions, argument signatures, and deprecation warnings:
[TypeName1], [TypeName2], [rootFieldName]
Do NOT generate any query. Return only the type definitions.
```

3. Build a **capability map** showing what IS and IS NOT possible:

| Business requirement | API operation | Available fields | Status |
|---------------------|---------------|-----------------|--------|
| List upcoming flights | `flightList` | id, date, route, crew | Available |
| Get passenger manifest | `flightList -> pax` | name, documents | Available |
| Update flight status | — | — | Not available |

**If requirements CANNOT be fulfilled:**
- Mark clearly as not available
- Note what exists vs. what's missing in the schema
- Describe what would need to be added to support this
- Do NOT invent queries — report the gap honestly

---

## STEP 5 — Design the integration workflow

Based on Steps 3–4, design a numbered workflow. Each step = one logical operation.

For each step, define:
- **Step number and name**
- **Purpose** — what business goal does this step achieve?
- **API operation** — exact query/mutation name (verified in Step 1)
- **Input** — what variables/data does this step consume?
- **Output** — what data does this step produce for subsequent steps?
- **Dependencies** — does this step require data from a previous step?

Example workflow outline:
```
Step 1: Authenticate -> obtain Bearer token
Step 2: Query flight list for date range -> get flight IDs and basic data
Step 3: For each flight -> query detailed leg data (crew, passengers, route)
Step 4: (Optional) Write booking confirmation back to Leon via mutation
Step 5: Handle pagination and error retries
```

If some workflow steps involve non-API concerns (e.g., data transformation, scheduling), describe them clearly but briefly — focus the guide on the Leon API calls.

---

## STEP 6 — Write example queries for each workflow step

For each step involving a Leon API call:

1. Write the GraphQL query or mutation following these rules:
   - Use named operations (e.g., `query GetUpcomingFlights { ... }`)
   - Use variables for ALL dynamic values — never hardcode IDs, dates, or tokens
   - Include only schema-verified fields
   - Add `# inline comments` explaining non-obvious arguments or fields
   - Follow proper GraphQL syntax

2. Immediately validate each query (Step 7 below) before including it in the guide.

---

## STEP 7 — Validate ALL queries — MANDATORY

**Every single query and mutation** in the guide must be validated using the `write-graphql-query` skill. No exceptions.

For each query, use the **Skill tool** to invoke `write-graphql-query` with:

```
INTERNAL USE — validate only. Do NOT rewrite or regenerate this query.
Validate the following GraphQL query against the live schema and report:
- valid (with confirmation of each field and argument)
- invalid (with exact error messages)

Query to validate:
[paste the full query here]
```

Interpret the result:
- Skill confirms the query is valid -> include the query in the guide as-is
- Skill reports errors -> fix the query based on the reported errors and re-invoke for re-validation

**Never include a query that has not passed validation.** If a query cannot be fixed, replace it with a clear "not available" notice explaining what is missing from the API.

---

## STEP 8 — Compose the integration guide

The guide must read like a **recipe**: the integrator executes Step 1, takes the output, uses it in Step 2, and so on — without ever needing to jump to another section or stop to think about structure. Every step is self-contained.

Design rules:
- **Authentication is Step 1** of the workflow — not a separate section to reference later
- **No appendix, no cross-references** — every query lives exactly where it is executed
- **Each step has a single "Save this ->" line** that explicitly names what to carry forward
- **Fill-in table per step** — shows exactly where each variable comes from (credential, previous step, user input)
- **Response: show only what matters** — trim to the fields actually used in this integration
- **No theory** — no "purpose" paragraphs, no narrative. One goal line, then action.

### API Documentation Portal Links — MANDATORY

For every GraphQL **query name**, **mutation name**, and **type name** mentioned in the guide, link to the Leon API documentation portal:

```
http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/{name}.doc.html
```

Where `{name}` is the query/mutation/type name in **all lowercase**.

Examples:
- Query `flightList` -> `http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightlist.doc.html`
- Type `CrewPanelFlightTraining` -> `http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/crewpanelflighttraining.doc.html`
- Mutation `updateFlight` -> `http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/updateflight.doc.html`

**Links to fields within types — do NOT link the field name directly.**
The documentation portal has pages for types, queries, and mutations — NOT for individual fields.
When referring to a specific field within a type, link to the **parent type** and instruct the reader to locate the field there.

Format for field references:
```
[`FieldName`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/{parenttypename}.doc.html) field in [`ParentTypeName`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/{parenttypename}.doc.html) — find `fieldName` in the type reference
```

Example — field `tailNumber` inside type `LegAircraft`:
> [`tailNumber`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/legaircraft.doc.html) — find this field in the [`LegAircraft`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/legaircraft.doc.html) type reference

**Where to place links in the guide:**
- In the **"All steps at a glance"** section — link each API operation name
- In each **Step header** — link the query/mutation name inline, e.g.: `Query [\`flightList\`](http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/flightlist.doc.html)`
- In the **Body/request section** — after the GraphQL code block, add a line: `Full type reference -> (http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/{typename}.doc.html)`
- When a **type name** is mentioned for the first time in a step's description, link it inline
- When a **field within a type** is mentioned — link to the parent type and note where to find the field (see format above)

---

### GUIDE TEMPLATE

````markdown
# Leon API Integration Guide: [Integration Name]

> **Version:** [today's date]
> **API:** Leon GraphQL API (Beta)
> **Prepared by:** Leon Software Support

---

## What this guide does

[One sentence: what the integration achieves and between which systems.]

---

## Before you start

Make sure you have:

- [ ] Leon account with API access enabled — contact Leon Support if you don't have it yet
- [ ] API credentials: `clientId` and `clientSecret`
- [ ] [Any other hard prerequisite — specific Leon module, permission level, etc.]

---

## All steps at a glance

1. Authenticate -> get `access_token`
2. [Step 2 name] -> get `[key value carried forward]`
3. [Step 3 name] -> get `[key value carried forward]`
[... one line per step, showing the input->output chain ...]

---

## Step 1 — Authenticate

[Use the correct sub-template based on the integrator type determined in Step 2 of the skill.]

---

### Step 1 template — OAuth 2.0 Code Grant (for vendors / multi-operator integrations)

> **OAuth is mandatory for 3rd party software providers.** If you are building software that will be used by multiple Leon operators, you must use this method. API Key is not an option.

#### Step 1a — Register your application (one-time)

Before writing any code, submit the Leon API registration form:
https://leonsoftware.atlassian.net/servicedesk/customer/portal/4/group/8/create/40

You will receive a `client_id` and `client_secret`. Development and testing can be done on the sandbox environment. Production access requires a demo meeting with Leon after development is complete.

#### Step 1b — Request user authorization

When an operator wants to connect your application, redirect their admin user to:

```
https://{oprId}.leon.aero/oauth2/code/authorize/?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE_LIST}&state={OPTIONAL_STATE}
```

**Fill in:**

| Placeholder | Where to get it |
|-------------|----------------|
| `{oprId}` | The operator's Leon subdomain (ask any user: "What address do you use to sign in to Leon?") |
| `{CLIENT_ID}` | Your `client_id` from Leon registration |
| `{REDIRECT_URI}` | Your redirect URI — must exactly match what you submitted at registration |
| `{SCOPE_LIST}` | Space-delimited scopes your app needs (see Scope List in api-docs.md) |
| `{OPTIONAL_STATE}` | Optional CSRF token — recommended |

After the user grants consent, Leon redirects to your `{REDIRECT_URI}` with `?code=...` in the query string.

**Save this ->** `code` from the redirect URL — valid for 10 minutes, single-use.

#### Step 1c — Exchange code for tokens

```bash
curl --location --request POST 'https://{oprId}.leon.aero/oauth2/code/token/' \
    --form 'grant_type="authorization_code"' \
    --form 'client_id="{CLIENT_ID}"' \
    --form 'client_secret="{CLIENT_SECRET}"' \
    --form 'redirect_uri="{REDIRECT_URI}"' \
    --form 'code="{AUTHORIZATION_CODE}"'
```

**Fill in:**

| Placeholder | Where to get it |
|-------------|----------------|
| `{CLIENT_ID}` | Your `client_id` from Leon registration |
| `{CLIENT_SECRET}` | Your `client_secret` from Leon registration |
| `{REDIRECT_URI}` | Same URI as in Step 1b |
| `{AUTHORIZATION_CODE}` | `code` value from Step 1b redirect |

**Response:**

```json
{
    "token_type": "Bearer",
    "access_token": "eyJhbGc...",
    "refresh_token": "dGhpcyBp..."
}
```

**Save this ->**
- `access_token` — use in all API requests (valid 30 minutes)
- `refresh_token` — use to get a new access token when it expires (valid 30 days since last use)

#### Step 1d — Refresh the access token (when expired)

```bash
curl --location --request POST 'https://{oprId}.leon.aero/oauth2/code/token/' \
    --form 'grant_type="refresh_token"' \
    --form 'client_id="{CLIENT_ID}"' \
    --form 'client_secret="{CLIENT_SECRET}"' \
    --form 'refresh_token="{REFRESH_TOKEN}"'
```

> **Token management rules:**
> - Reuse the access token for its full 30-minute validity — do NOT create a new token per request
> - Limit: 500 active access tokens per refresh token; exceeding this returns HTTP `429 Too Many Requests`
> - If you receive `429`, check the `Retry-After` header before retrying

---

### Step 1 template — API Key (for single-operator internal integrations only)

> **This method is only for integrations built for a single operator's internal use.**
> If you plan to distribute this integration to other Leon operators, you must use OAuth instead.
> Integrations using API Key are not visible in the Leon Addons panel.

#### Step 1a — Create an API Key in Leon

The operator creates an API Key in Leon (Settings -> API Keys).
Full instructions: https://wiki.leonsoftware.com/leon/api-keys

This produces a `RefreshToken`.

#### Step 1b — Exchange Refresh Token for Access Token

```bash
curl -X POST -d 'refresh_token={RefreshToken}' https://{oprId}.leon.aero/access_token/refresh/
```

**Fill in:**

| Placeholder | Where to get it |
|-------------|----------------|
| `{oprId}` | The operator's Leon subdomain |
| `{RefreshToken}` | From the API Key created in Step 1a |

**Response:** the access token as plain text.

**Save this ->** the returned string — this is your `access_token`. Valid for 30 minutes.

---

## Step 2 — [Step name]

> [One sentence: what this step gets and why it's needed.]

**Request:**

```http
POST [GraphQL endpoint]
Content-Type: application/json
Authorization: Bearer <access_token from Step 1>
```

**Body:**

```graphql
[validated query]
```

**Fill in:**

| Variable | Where to get it | Example |
|----------|----------------|---------|
| `$var1` | [source: credential / Step N response field `x` / user input] | `"2024-01-15"` |
| `$var2` | [source] | `"2024-01-22"` |

**Variables JSON:**

```json
{
  "var1": "...",
  "var2": "..."
}
```

**Response (relevant fields only):**

```json
{
  "data": {
    "[queryName]": [
      { "[field]": "...", "[field2]": "..." }
    ]
  }
}
```

**Save this ->** `[field]` from each item — you'll use it in Step [N+1].

---

## Step 3 — [Step name]

[same structure — authentication step is already done, just reference the token]

---

[... repeat for every step in the workflow. Every step stands alone. ...]

---

## If something goes wrong

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `401 Unauthorized` | Token expired or missing | Re-run Step 1, use the new `access_token` |
| `400 Bad Request` | Wrong variable type or missing required field | Check the Fill-in table for this step |
| Empty result (`[]`) | No data matches your filter | Widen the date range or check the filter values |
| [other error from API docs] | [cause] | [fix] |

---

[INCLUDE ONLY IF APPLICABLE]

## What this integration cannot do (yet)

| You asked for | Status | Why | What to do |
|--------------|--------|-----|-----------|
| [requirement] | Not in API | [specific missing type/field/mutation] | [workaround or "raise with Leon Support"] |
````

---

## STEP 9 — Generate output in requested format

### If Markdown format

Output the complete guide directly in the response inside a code block:

````markdown
[full guide content]
````

Also mention that the guide can be saved as a `.md` file.

### If DOCX or PDF format

Output the complete guide content in Markdown, then use the **Skill tool** to invoke the available claude.ai document generation skill to convert it into the requested format (DOCX or PDF).

Pass the full Markdown content to the skill and specify the desired output format. The skill will handle the conversion and deliver the file to the user.

#### DOCX Design Guidelines — apply when generating Word documents

The DOCX must look **attractive, clean, and modern**. Apply these design instructions when invoking the document generation skill:

**Typography and Colors:**
- Title (`#`): large bold font, dark navy (`#1A2B4A`), centered, no underline
- Section headers (`##`): medium bold, accent blue (`#2563EB`), left-aligned, small top spacing
- Sub-headers (`###`): slightly smaller, dark gray (`#374151`), left-aligned
- Body text: clean sans-serif (Calibri or similar), 11pt, dark gray `#1F2937`
- Code/monospace blocks: `Courier New` or `Consolas`, 10pt, light gray background `#F3F4F6`, left-padded, subtle border

**Layout:**
- Page margins: 2.5 cm top/bottom, 3 cm left/right
- Generous line spacing (1.3-1.4)
- Clear visual separation between steps using thin horizontal rules or spacing
- No decorative clipart or icons — keep it minimal and professional

**Tables:**
- Header row: dark navy background `#1A2B4A`, white bold text
- Alternating rows: white / very light gray `#F9FAFB`
- Thin borders: `#E5E7EB`
- Slightly padded cells (6pt top/bottom)

**Highlights and Callouts:**
- Warning/important notes: light yellow background `#FFFBEB`, left border accent `#F59E0B`
- "Save this ->" lines: light green background `#F0FDF4`, left border accent `#22C55E`
- "Not available" notices: light red background `#FEF2F2`, left border accent `#EF4444`

**Cover / Header block:**
- Document title prominently at the top
- Subtitle line: "Leon API Integration Guide" in accent blue, smaller
- Version and date line in light gray, italic
- Thin separator line below the header block

---

## Handling incomplete API coverage

If the user's requirements **cannot be fully or partially met** by the current API:

```markdown
## API Limitations for This Integration

The following requirements from your integration spec cannot currently be fulfilled via the Leon GraphQL API:

### [Requirement Name]

**What you need:** [description of what the integrator wants to do]

**What the API currently provides:**
[what exists — even if it's nothing]

**What's missing:**
- No `[mutation/query]` exists for [action]
- Type `[TypeName]` does not expose field `[fieldName]`
- [other specific gap]

**Recommendation:**
[One of:]
- "This action is only available through the Leon web interface at this time."
- "The closest available operation is `[operationName]` which covers [partial subset]."
- "We recommend raising a feature request with the Leon Software development team."
```

If it's **partially possible**, always split into two clearly labeled sections:

```
## What IS possible via the API
[guide for the feasible parts]

## What is NOT possible via the API
[clear description of gaps and recommendations]
```

---

## General principles

- **English only** — the guide is for external integrators
- **Recipe, not reference** — the guide is read top-to-bottom, executed step by step; it is never a document you flip through
- **Each step stands alone** — everything needed to execute a step (query, variables, where to get them) is in that step; no "see section X"
- **Authentication is Step 1** — never a separate section the reader must visit before starting the workflow
- **Explicit carry-forward** — every step ends with a clear "Save this ->" line naming exactly what value to take into the next step
- **No theory** — no purpose paragraphs, no narrative fluff; one goal line then action
- **Trim responses** — show only the fields actually used in this integration, not the full response schema
- **Production-ready** — all queries use variables, never hardcoded IDs, dates, or tokens
- **No placeholder queries** — every query must have passed validation in Step 7
- **Accuracy over completeness** — a shorter, correct guide is better than a long, wrong one
- **Deprecated fields** — never use deprecated fields; if unavoidable, warn explicitly
- **API portal links** — every query, mutation, and type name in the guide must be hyperlinked to `http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/{lowercasename}.doc.html`; for individual **fields within types**, do NOT link the field directly — link to the parent type instead and instruct the reader to find the field there
