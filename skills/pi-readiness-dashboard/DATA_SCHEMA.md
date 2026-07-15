# Data Schema

## Themes JSON (`--themes`)

A flat JSON array, one entry per Jira Theme issue:

```json
[
  {
    "id": "AGAI-1440",
    "title": "Token exchange - Identity support & tests",
    "divisions": ["Secrets Manager"],
    "groups": ["Secure AI Agents"],
    "status": "In Progress",
    "owner": "Tal Zamir",
    "flagged": false,
    "throughputType": null,
    "url": "https://ca-il-jira.il.cyber-ark.com:8443/browse/AGAI-1440"
  }
]
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | Jira issue key. |
| `title` | string | Issue summary, HTML-entity-decoded (`&amp;` -> `&`). |
| `divisions` | string[] | From `customfield_22721`, HTML-entity-decoded. Usually 1 item but can be more (fan-out). Empty array if unset. |
| `groups` | string[] | From `customfield_22720`, HTML-entity-decoded. Empty array if unset. |
| `status` | string | **The exact, raw Jira status name** (e.g. `"Ready for Implementation"`, `"Planned"`, `"In Progress"`, `"Open"`, `"HL Product Discovery"`, `"HL Dev Discovery"`). Never collapse into an aggregated label like `"Not Ready"` or `"Carry Over"` — the dashboard shows this value verbatim in badges/legends/charts and only classifies it into a category (see `STATUS_META` in `assets/template.html`) for KPI math. |
| `owner` | string \| null | Assignee display name, or `null` if unassigned. |
| `flagged` | boolean | `true` if `customfield_10126` (Flagged) has a non-empty value (e.g. contains `"Impediment"`). |
| `throughputType` | string \| null | From `customfield_13920` ("Throughput Type", single-select). The raw option value (e.g. `"A. Feature"`, `"B. Tech"`, `"C. Security"`, `"D. Support"`), or `null` if unset. Drives the dashboard's in-browser Throughput Type filter (defaults to showing `"A. Feature"` + unset only). |
| `url` | string | `<jira_base_url>/browse/<id>`. |

## HR Tree JSON (`--hrtree`)

A dict mapping canonical Division name -> sorted list of canonical Group names. Bundled default: [assets/hr_tree.json](assets/hr_tree.json), parsed once from the PMO_RnD_Team_Group HR export. Only regenerate this if the user provides an updated HR org-chart file.

```json
{
  "Secrets Manager": ["CP", "Conjur Cloud", "Conjur Enterprise", "SWA", "..."],
  "Identity": ["Identity Core & Infra", "..."]
}
```

Divisions found in `--themes` but absent from this tree are bucketed as **"Other / Unmapped"** in the dashboard automatically — no data is dropped.

## Status -> category mapping (`STATUS_META` in `assets/template.html`)

The dashboard always displays the raw status, but internally classifies each into one of 4 categories for KPI math (readiness score, Carry-Over %, Not Ready %, Quality Flags scoping):

| Raw status | Category |
|---|---|
| `Ready for Implementation` | `ready` |
| `Planned` | `planned` |
| `In Progress` | `carryOver` |
| `Open`, `HL Product Discovery`, `HL Dev Discovery` | `notReady` |
| *(anything else, unrecognized)* | `notReady` (fallback, slate color) |

If a project surfaces a new raw status not in this table, add an entry to `STATUS_META` in `assets/template.html` (color + category) - otherwise it still displays correctly via the neutral fallback, just uncategorized as `notReady`.

## PI Readiness Index formula

```
PI Readiness Index = (readyCount + plannedCount) / (totalCount - carryOverCount) * 100
```

- **Numerator**: themes categorized `ready` + `planned` (i.e. committed and scoped for the PI).
- **Denominator**: all in-scope themes (respecting active Division/Group/Throughput Type filters) *excluding* `carryOver` (`In Progress`) themes. Carry-Over is excluded from both sides because that work already rolled over from a prior PI - it's neither new-PI readiness nor a fair thing to divide by.
- `notReady` themes (`Open`, `HL Product Discovery`, `HL Dev Discovery`) stay in the denominator only, so a growing unscoped backlog still dilutes the score even though it isn't counted as "carry-over debt."
- Target benchmark: **>60%** (Optimal ≥60%, Caution ≥40%, Critical <40%).
- The dashboard renders the live numbers for this formula directly under the score on the KPI card (e.g. `10 ÷ 792 = 13%`).

This replaced an earlier weighted-penalty formula (`ready*1.0 + planned*0.7 + carryOver*0.1 - missingOwner*0.4 - flagged*0.5, all / total`) which is no longer used for the headline score. Quality Flags (missing owner / flagged) are still tracked internally (used by the table's Flags/Risk column and the AI insights band) but there is no dedicated "Quality Flags" KPI card, and they no longer factor into the readiness percentage itself.

## Net New Scope

```
Net New Scope = totalCount - carryOverCount   (i.e. every Theme whose category !== "carryOver")
```

Every Theme that is not `In Progress` - the actual new scope being planned for the PI, as opposed to work already committed and rolling over. Rendered as its own KPI card immediately to the right of PI Readiness Index, with a per-status breakdown chip row (same chip pattern as Carry-Over/Not Ready).

## Ownership Responsibility Matrix (`OWNERSHIP_META` in `assets/template.html`)

Maps each raw status to the function that currently owns it:

| Raw status | Owner |
|---|---|
| `Open` | Product Management |
| `HL Product Discovery` | Product Management |
| `HL Dev Discovery` | R&D |
| `Planned` | R&D |
| `Ready for Implementation` | R&D |
| `In Progress` | R&D (excluded from the matrix calc - see below) |

The Ownership Responsibility Matrix section (counters + split bar + donut chart) and its AI insight are computed **only over Net New Scope** (`category !== "carryOver"`, i.e. `In Progress` themes are excluded entirely) - business rule: carry-over is already committed R&D execution, not a live ownership question. If a new raw status appears, add it to `OWNERSHIP_META` in `assets/template.html` (defaults to R&D if left unmapped).

## PI Timeline schema (`assets/pi_timeline.json`)

A fiscal-year PI timeline export (`--timeline`, defaults to the bundled [assets/pi_timeline.json](assets/pi_timeline.json)). `render_dashboard.py` searches `fiscalYears[].programIncrements[]` for the entry whose `name` matches `--pi` (e.g. `"27-Q1"`) and embeds just that one object - the dashboard only ever renders the target PI's timeline, never the whole fiscal year.

```json
{
  "exportType": "fiscal-year-timeline",
  "exportedAt": "2026-07-15T10:52:39.970Z",
  "fiscalYears": [
    {
      "fiscalYear": 2027,
      "programIncrements": [
        {
          "id": "26j25ihgq",
          "name": "27-Q1",
          "start": "2026-08-02",
          "end": "2026-11-07",
          "sprints": 7,
          "conceptualPlanningDate": null,
          "midPIPlanningDate": "2026-09-19",
          "phases": {
            "prePlanning": { "start": "2026-06-03", "end": "2026-08-01" },
            "planning": { "start": "2026-08-02", "end": "2026-08-08" },
            "execution": { "start": "2026-08-09", "end": "2026-11-07" },
            "retrospective": { "start": "2026-11-08", "end": "2026-11-21" }
          }
        }
      ]
    }
  ]
}
```

| Field (within a `programIncrements[]` entry) | Notes |
|---|---|
| `name` | Must exactly match `--pi` (e.g. `"27-Q1"`) for this PI's timeline to be picked up. |
| `start` / `end` | Overall PI date range (used in the timeline subtitle + sprint count). |
| `sprints` | Shown in the timeline subtitle. |
| `midPIPlanningDate` | If present, annotated as a small flag under the Execution phase card. |
| `phases.prePlanning` / `.planning` / `.execution` / `.retrospective` | Each `{start, end}` (`YYYY-MM-DD`, inclusive). All 4 are rendered as a **strictly proportional** segment bar - each segment's width = `phaseDays / totalDays * 100`, no readability floor - so the bar always correlates 1:1 with real elapsed/remaining time (e.g. a 1-week Planning phase renders visibly thinner than a 13-week Execution phase), plus one compact inline chip each. Missing phase keys are simply skipped. |

**Current-phase highlighting** is entirely client-side: on every page load, the dashboard's JS compares the *browser's* current date (`new Date()`) against each phase's `[start, end]` to mark it `completed` / `current` / `upcoming`, and positions a small "Today" dot marker along the bar accordingly. This means the highlighted phase is always correct whenever the static HTML is opened, regardless of when it was generated - no re-render needed as time passes. The current phase's chip additionally shows a live "N days left" countdown (`Math.round((phaseEnd - today) / 86400000)`); other phases just show their date range. If `--pi` isn't found anywhere in the file (or `--timeline` points to a missing/absent file), `PI_TIMELINE` embeds as `null` and the whole section is hidden via JS - this is expected/safe, not an error condition to fix. The whole strip is intentionally lightweight (a single thin bar + one line of small pill chips) - don't re-expand it into larger cards unless the user asks.
