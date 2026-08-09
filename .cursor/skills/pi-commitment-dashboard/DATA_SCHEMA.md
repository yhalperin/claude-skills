# PI Commitment Dashboard — Data Schema

## Themes JSON (`--themes`)

Flat JSON array, one entry per Jira Theme issue:

```json
[
  {
    "id": "AGAI-1440",
    "title": "Token exchange - Identity support & tests",
    "divisions": ["Secrets Manager"],
    "committed": true,
    "commitmentLevel": "Committed",
    "finishDate": "2026-10-15",
    "objectiveName": "Accelerate AI-Driven Customer Insights",
    "url": "https://ca-il-jira.il.cyber-ark.com:8443/browse/AGAI-1440"
  }
]
```

| Field | Type | Source | Notes |
|---|---|---|---|
| `id` | string | issue key | e.g. `"AGAI-1440"` |
| `title` | string | `summary` | HTML-entity-decoded |
| `divisions` | string[] | `customfield_22721` | HTML-decoded. Usually 1 item, can fan-out. Empty array if unset. |
| `committed` | boolean | derived | `true` if `commitmentLevel == "Commitment"` (the actual Jira value) |
| `commitmentLevel` | string \| null | `customfield_13641` | Raw option value (`"Commitment"`, `"Stretch"`, `"Normal"`) or `null` |
| `finishDate` | string \| null | `customfield_21221` | ISO date `YYYY-MM-DD` or `null` |
| `objectiveName` | string \| null | `customfield_20928` | "Initiative Name" text field or `null` (most themes have null) |
| `url` | string | constructed | `https://ca-il-jira.il.cyber-ark.com:8443/browse/<id>` |

## Snapshot Metadata

Two separate timestamps shown in dashboard header:

| Field | CLI source | Meaning |
|---|---|---|
| `fetchedAt` | `--fetched-at "2026-08-06 10:30"` | When Jira data was actually pulled. Shown as amber "Jira Data as of" badge. |
| `renderedAt` | `datetime.now()` at render time | When this HTML file was generated. Shown as small de-emphasized note. |

## Commitment Calculation (per Division)

```
committedCount   = count of themes where committed == true
totalCount       = count of all themes for this division
commitmentPct    = committedCount / totalCount * 100
```

Color thresholds:
- green: commitmentPct >= 70
- amber: commitmentPct >= 40
- red: commitmentPct < 40

## Division Fanout

A Theme with `divisions: ["A", "B"]` counts toward BOTH Division A and Division B in all statistics. The same theme appears in both division drill-downs.

## Objective Grouping

In the drill-down view, only committed Themes (`committed == true`) are shown, grouped by `objectiveName`. Themes where `objectiveName == null` are placed in an "Unassigned" bucket at the bottom of the list.

## FinishDate Chip Colors

Computed client-side on page load relative to today's date:
- green: finishDate is ≥30 days from today
- amber: finishDate is 1–29 days from today
- red: finishDate is today or in the past
- grey: finishDate is null ("No date")
