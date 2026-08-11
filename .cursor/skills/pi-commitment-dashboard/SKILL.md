---
name: pi-commitment-dashboard
description: >-
  Builds a self-contained "PI Commitment Dashboard" HTML dashboard from live
  Jira Theme issues for a given Program Increment (default: 27-Q1). Shows
  commitment statistics per Division on a summary view (% committed Themes out
  of total, color-coded progress bars), then drills down per Division into
  committed Themes grouped under 5-6 Strategic Area objectives with FinishDate
  chips. Fetches Themes via the user-policy-broker MCP's jira_search tool,
  transforms them into a flat JSON array, and renders a self-contained HTML
  file that opens directly in a browser (local only, no Amplify publish).
  Re-runnable at any point to refresh with current Jira state.
  Use when the user asks to generate, build, run, or refresh a PI commitment
  dashboard/board, wants to see committed themes per division, asks about
  division commitment percentages, "% committed", "committed themes dashboard",
  "theme commitment", "committed themes per division", or any request to show
  PI Theme commitment by division or strategic area.
disable-model-invocation: true
---

## Sync Requirement

Both `C:\Users\yhalperin\.cursor\skills\pi-commitment-dashboard\` and
`C:\Users\yhalperin\.claude\skills\pi-commitment-dashboard\` must always be
kept in sync. Sync command:
```bash
robocopy "C:\Users\yhalperin\.claude\skills\pi-commitment-dashboard" "C:\Users\yhalperin\.cursor\skills\pi-commitment-dashboard" /MIR
```

---

## Jira Instance Constants

| Concept | Field | Notes |
|---|---|---|
| Divisions | `customfield_22721` | multi-select array |
| PlannedPI | `customfield_14422` | e.g. `"27-Q1"` |
| Commitment Level | `customfield_13641` | single-select; committed = value is `"Commitment"` |
| Finish Date | `customfield_21221` | date field, ISO format `YYYY-MM-DD` or null |
| Initiative Name | `customfield_20928` | text field; groups Themes into objectives (often null) |
| Base URL | `https://ca-il-jira.il.cyber-ark.com:8443` | used for issue links |

Always go through `user-policy-broker` MCP; never bypass.

---

## Dashboard Layout

**Summary View (default)**
- Header: "PI Commitment Dashboard — \<PI\>", Division filter dropdown, "Jira Data as of" badge
- Top KPI row: Total Themes | Total Committed | Overall % Committed
- Division Cards grid (2-3 columns, responsive): one card per Division
  - Division name
  - Large % committed (green ≥70%, amber 40–70%, red <40%)
  - Progress bar
  - "X committed / Y total" count
  - Click → drill-down

**Drill-Down View (per Division)**
- Breadcrumb: ← Back to Summary | Division name
- Division stats bar: X committed / Y total, % committed badge
- Objectives sections (grouped by Strategic Area):
  - Objective header with committed theme count badge
  - Per-Theme row: ID badge (Jira link), title, FinishDate chip (green ≥30 days, amber <30 days, red = past)
  - Themes with no Strategic Area → "Unassigned" section
- Division dropdown stays active (switch division without going back to summary)

---

## Workflow

**Step 1 — Confirm scope**

Default PI: `27-Q1`. Ask the user if they want a different PI or a specific Division scope (default = All).

**Step 2 — Build JQL**

```
issuetype = Theme AND cf[14422] = "27-Q1" ORDER BY key
```

Fetch ALL Themes (no status filter, no commitment filter in JQL) so we can compute committed vs. total per division from the full dataset.

If a specific Division is requested, append: `AND cf[22721] = "<Division>"`.

**Step 3 — Fetch from Jira**

Via `user-policy-broker` MCP `jira_search`:
- Fields: `key,summary,customfield_22721,customfield_13641,customfield_21221,customfield_20928`
- Paginate at `limit=25` (`start_at` 0, 25, 50, ...)
- After each page, accumulate results
- Decode HTML entities (`&amp;` → `&`) during transform
- Stop when `start_at + max_results >= total`

**Step 4 — Transform and assemble** into schema per DATA_SCHEMA.md:
- `status` is not needed for this dashboard; omit
- `committed` = `true` if `customfield_13641` value equals `"Commitment"` (case-insensitive), else `false`
- `divisions` = array from `customfield_22721`; empty array if null
- `finishDate` = `customfield_21221` date value (string `YYYY-MM-DD`) or `null`
- `objectiveName` = `customfield_20928` text value ("Initiative Name") or `null`
- `url` = `<base_url>/browse/<key>`
- Verify `len(array) == total` and no duplicate `id`s

**Step 5 — Write themes JSON**

Write transformed array to a scratch file, e.g.:
`C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_themes.json`

**Step 5b — Derive status themes (Planned + In Progress)**

From the same raw Jira data already fetched in Step 3, extract every theme whose
status is `"Planned"` or `"In Progress"`. Transform each into a slim object:
```json
{"id": "KEY-123", "divisions": ["Division A"], "status": "Planned"}
```
Write to: `C:\Users\yhalperin\AppData\Local\Temp\pi_status_themes.json`
This drives the "In-flight" second bar shown on each division row in the summary.

**Step 5c — Fetch division totals**

For each unique division found in Step 3, query with `limit=1` to get just the `total` count:
```
JQL: issuetype = Theme AND cf[14422] = "<PI>" AND cf[22721] = "<Division>" ORDER BY key
```
Also query without division filter for `__all__`. Write results to a JSON file:
```json
{"IGA": 56, "AI data and Labs": 69, ..., "__all__": 1334}
```

**Step 6 — Render**

```bash
python "C:\Users\yhalperin\.claude\skills\pi-commitment-dashboard\scripts\render_dashboard.py" \
  --themes "C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_themes.json" \
  --division-totals "C:\Users\yhalperin\AppData\Local\Temp\pi_commitment_div_totals.json" \
  --status-themes "C:\Users\yhalperin\AppData\Local\Temp\pi_status_themes.json" \
  --pi "27-Q1" \
  --fetched-at "YYYY-MM-DD HH:MM"
```

Always pass `--fetched-at` with the actual Jira query time.

**Step 7 — Report**

Report: PI, Division scope, total Themes fetched, committed count, overall % committed, per-division committed/total, output path.

---

## Re-running for a refresh

Repeat steps 2–7 with fresh data. Every render gets its own timestamped filename.

---

## Additional Resources

- `DATA_SCHEMA.md` — JSON shape and field semantics
- `assets/template.html` — dashboard markup/styling
- `scripts/render_dashboard.py` — renders HTML from JSON
