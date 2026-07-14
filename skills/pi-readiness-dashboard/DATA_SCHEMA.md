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
