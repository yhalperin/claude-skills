---
name: pi-boards-update
description: >-
  Fetches Jira Theme data ONCE for a given Program Increment (PI) and refreshes
  BOTH the PI Commitment Dashboard and the PI Readiness Dashboard in a single
  run. When the user wants both boards updated, or asks to "refresh PI boards",
  "update dashboards for PI X", "sync both PI dashboards", or similar — use
  this skill instead of running the two individual dashboard skills separately.
  Accepts a PI name argument (e.g. "27-Q1"). Publishes the Readiness board to
  AWS Amplify automatically; opens the Commitment board locally.
disable-model-invocation: true
---

## Overview

Both dashboards share the same Jira query base:
```
issuetype = Theme AND cf[14422] = "<PI>" ORDER BY key
```

This skill fetches **once** with all fields both dashboards need, then derives
each dashboard's data locally — no duplicate round-trips to Jira.

**Union of required fields:**
```
key,summary,status,assignee,customfield_22721,customfield_22720,
customfield_10126,customfield_13920,customfield_13641,customfield_21221,
customfield_20928
```

| Field | Used by |
|---|---|
| `key`, `summary`, `status`, `assignee` | Both |
| `customfield_22721` — Divisions | Both |
| `customfield_22720` — Groups | Both |
| `customfield_10126` — Flagged | Readiness only |
| `customfield_13920` — Throughput Type | Readiness only |
| `customfield_13641` — Commitment Level | Commitment only |
| `customfield_21221` — Finish Date | Commitment only |
| `customfield_20928` — Initiative Name | Commitment only |

---

## Skill Locations (keep in sync)

- `C:\Users\yhalperin\.claude\skills\pi-boards-update\`
- `C:\Users\yhalperin\.cursor\skills\pi-boards-update\`

Sync command:
```bash
robocopy "C:\Users\yhalperin\.claude\skills\pi-boards-update" "C:\Users\yhalperin\.cursor\skills\pi-boards-update" /MIR
```

---

## Workflow

### Step 1 — Confirm PI

Default PI: `27-Q1`. If the user specified a different PI in their request, use
it. No need to ask if it's already clear.

### Step 2 — Build the combined JQL

```
issuetype = Theme AND cf[14422] = "27-Q1"
AND status in ("Ready for Implementation", "Planned", "In Progress",
               "Open", "HL Dev Discovery", "HL Product Discovery")
ORDER BY key
```

Note: the Readiness dashboard requires the `status in (...)` filter to exclude
issues in unusual workflow states. The Commitment dashboard does not filter by
status in JQL — but including this filter also produces valid Commitment data
since committed themes will all be in one of those statuses.

### Step 3 — Fetch all pages from Jira

Via `user-policy-broker` MCP `jira_search` (never bypass):
- **Fields:** `key,summary,status,assignee,customfield_22721,customfield_22720,customfield_10126,customfield_13920,customfield_13641,customfield_21221,customfield_20928`
- **Paginate at `limit=25`** (`start_at` 0, 25, 50, ...) — this instance silently truncates larger limits
- Record the `total` from the first response
- Stop when `start_at + max_results >= total`
- Decode HTML entities (`&amp;` → `&`) during transform
- Record the current timestamp as `FETCHED_AT` (e.g. `"2026-08-06 10:30"`)

### Step 4 — Derive the Readiness themes file

Transform each issue into the readiness schema. Write to scratch:
`C:\Users\yhalperin\AppData\Local\Temp\pi_readiness_themes.json`

Per-theme fields for readiness:
```json
{
  "id": "KEY-123",
  "title": "Theme title (HTML-decoded)",
  "status": "Planned",
  "owner": "Display Name or null",
  "divisions": ["Division A"],
  "groups": ["Group X"],
  "flagged": false,
  "throughputType": "A. Feature",
  "url": "https://ca-il-jira.il.cyber-ark.com:8443/browse/KEY-123"
}
```

- `owner` = assignee display name, or `null` if unassigned
- `flagged` = `true` if `customfield_10126` is non-empty
- `throughputType` = raw `customfield_13920` value or `null`

### Step 5 — Derive the Commitment themes file

Filter from the same raw data: only include themes where
`customfield_13641` value equals `"Commitment"` (case-insensitive).
This gives committed-only themes.

Transform into commitment schema. Write to:
`C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_themes.json`

Per-theme fields for commitment:
```json
{
  "id": "KEY-123",
  "title": "Theme title",
  "divisions": ["Division A"],
  "group": "Group X",
  "committed": true,
  "commitmentLevel": "Commitment",
  "finishDate": "2026-08-15",
  "objectiveName": "Initiative Name text or null",
  "url": "https://ca-il-jira.il.cyber-ark.com:8443/browse/KEY-123"
}
```

Notes:
- `group` = first value of `customfield_22720` array or `null` (single string, not array)
- `committed` = always `true` (these are filtered to committed-only)
- `finishDate` = `customfield_21221` date string or `null`
- `objectiveName` = `customfield_20928` text value or `null`

### Step 5b — Fetch division totals for Commitment dashboard

For each unique division name found in the full raw dataset (Step 3), fetch just
the total count with `limit=1`:
```
JQL: issuetype = Theme AND cf[14422] = "<PI>" AND cf[22721] = "<Division>" ORDER BY key
```
Also fetch total for all-divisions combined (no division filter) as `"__all__"`.

Write results to:
`C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_div_totals.json`

Example:
```json
{"IGA": 56, "Secrets Manager": 262, "__all__": 1334}
```

### Step 6 — Write the JQL to a file (for Readiness render)

The Readiness render script requires `--jql-file` (direct `--jql` is unreliable
on Windows due to shell quote handling). Write the JQL from Step 2 to:
`C:\Users\yhalperin\AppData\Local\Temp\pi_boards_jql.txt`

### Step 7 — Render the Readiness Dashboard

```bash
python "C:\Users\yhalperin\.claude\skills\pi-readiness-dashboard\scripts\render_dashboard.py" \
  --themes "C:\Users\yhalperin\AppData\Local\Temp\pi_readiness_themes.json" \
  --pi "<PI>" \
  --division "All" \
  --jql-file "C:\Users\yhalperin\AppData\Local\Temp\pi_boards_jql.txt" \
  --fetched-at "<FETCHED_AT>"
```

Note the output path from stdout (under `C:\Users\yhalperin\Documents\PI_Readiness_Boards\`).

### Step 8 — Publish the Readiness Dashboard to AWS Amplify

```bash
python "C:\Users\yhalperin\.claude\skills\pi-readiness-dashboard\scripts\publish.py" \
  --html "<readiness_output_path>"
```

This pushes to `main` of `pi-readiness-dashboard-site`. The live URL is:
`https://main.d22fzeddx4r5jl.amplifyapp.com`

### Step 9 — Render the Commitment Dashboard

```bash
python "C:\Users\yhalperin\.claude\skills\pi-commitment-dashboard\scripts\render_dashboard.py" \
  --themes "C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_themes.json" \
  --division-totals "C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_div_totals.json" \
  --pi "<PI>" \
  --fetched-at "<FETCHED_AT>"
```

Note the output path from stdout (under `C:\Users\yhalperin\Documents\PI_Commitment_Boards\`).

### Step 10 — Report

```
PI Boards Updated — <PI>
=======================
Jira data as of: <FETCHED_AT>
Total themes fetched: <N>

Readiness Dashboard
  Themes: <N_readiness> (after status filter)
  Output: <readiness_output_path>
  Live:   https://main.d22fzeddx4r5jl.amplifyapp.com

Commitment Dashboard
  Committed themes: <N_committed>
  Output: <commitment_output_path>

Both boards now open in your browser.
```

---

## Jira Instance Constants

| Concept | Field | Notes |
|---|---|---|
| Divisions | `customfield_22721` | multi-select array |
| Groups | `customfield_22720` | multi-select array |
| PlannedPI | `customfield_14422` | e.g. `"27-Q1"` |
| Flagged | `customfield_10126` | non-empty = flagged |
| Throughput Type | `customfield_13920` | single-select |
| Commitment Level | `customfield_13641` | `"Commitment"` = committed |
| Finish Date | `customfield_21221` | ISO date or null |
| Initiative Name | `customfield_20928` | text field, objective name |
| Base URL | `https://ca-il-jira.il.cyber-ark.com:8443` | |

Always route through `user-policy-broker` MCP.

---

## Re-running for a Refresh

Repeat Steps 2–10 with fresh data. Every render auto-generates a timestamped
filename so no boards are overwritten. Always re-publish the Readiness dashboard
(Step 8) so the live Amplify site reflects the latest data.
