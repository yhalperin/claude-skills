# Initiative Data JSON Schema

This is the JSON payload `scripts/render_dashboard.py` injects into the dashboard template. Build this object from Jira query results, write it to a file, then render. Include one entry per requested initiative under `initiatives` - the template's header dropdown is populated dynamically from these keys, so a single file can hold one or several initiatives.

```jsonc
{
  "generatedAt": "2026-07-13T15:55:00+03:00",   // ISO timestamp, informational only
  "piCalendar": {                                // optional, shared across all initiatives - see "Planned PI calendar" below
    "26-Q2": { "end": "2026-08-01" },             // legacy PI (no known start) - the last one before the current fiscal system
    "27-Q1": { "start": "2026-08-02", "end": "2026-11-07" },
    "27-Q2": { "start": "2026-11-08", "end": "2027-01-30" },
    "27-Q3": { "start": "2027-01-31", "end": "2027-04-24" },
    "27-Q4": { "start": "2027-04-25", "end": "2027-07-31" }
  },
  "initiatives": {
    "jag-36913": {                               // key: lowercased initiative issue key - drives dropdown value + localStorage risk scoping
      "title": "JAG-36913: Priv Cloud centralization + guided flows + Dark mode",  // Initiative issue summary, prefixed with its key
      "status": "On Track",                       // "On Track" | "At Risk" | "Blocked" - free text shown on the header pill
      "statusColor": "emerald",                   // "emerald" | "amber" | "rose" - drives the pill color, pick per statusColor rule below
      "scope": "TBD",                              // free text scope badge; "TBD" if no clear scope field exists
      "horizon": "Target 27-Q1",                    // "Target <Planned PI>" using the Initiative issue's own Planned PI (latest value if several), else "Target TBD"
      "timelineRange": "TBD",                       // free text, e.g. "Jul 2026 - Oct 2026" or "TBD"
      "stats": {
        "totalFeatures": 14,                        // count of all leaf features across all master features
        "completedFeatures": 5,                      // count of leaf features with status "Completed"
        "timelineTarget": "27-Q1",                    // the Initiative issue's own Planned PI (latest value if several), else "TBD" - see Planned PI notes below
        "timelineVariance": "On Schedule"              // "On Schedule" | "Delayed" | "Ahead of Schedule" | "At Risk"
      },
      "risks": [],                                    // seed risks shown only the first time this initiative id is opened in a given browser;
                                                        // leave [] unless the user gave you specific risks to seed. Real usage adds/edits risks
                                                        // via the dashboard UI, persisted in localStorage keyed by initiative id - NOT by re-running this skill.
      "masterFeatures": [
        {
          "name": "Master-Feature: Priv Cloud centralization (SHLD-28144)",   // "Master-Feature: <summary> (<key>)"
          "status": "In Progress",                     // Completed | In Progress | Blocked | Planned - mapped from this issue's own Jira status category
          "progress": 50,                                // round(average of this master feature's features[].progress)
          "targetDate": "27-Q1",                          // this Master Feature's own Planned PI value (latest if several), else "TBD"
          "features": [
            {
              "name": "Safe page visibility (SHLD-28189)",   // "<summary> (<key>)" of the leaf issue (see traversal notes in SKILL.md - may be a "Theme" issue type)
              "group": "EPV",                                  // Jira "Group" custom field value on this issue, or "Platform Core" if empty
              "status": "In Progress",                          // Completed | In Progress | Blocked | Planned
              "progress": 50,                                    // 100 | 50 | 10 | 0 per the status mapping table in SKILL.md
              "date": "27-Q1"                                     // this Feature's own Planned PI value (latest if several), else "TBD"
            }
          ]
        }
      ]
    }
  }
}
```

## Field notes

- **`initiatives` keys** must be the lowercased initiative issue key (e.g. `"jag-36913"`). The dropdown, localStorage risk scoping, and CSV export filenames all derive from this key - do not use an arbitrary slug.
- **`statusColor`**: default `"emerald"`/`"On Track"`. Use `"rose"`/`"Blocked"` only if the Initiative issue itself is Blocked or any Master-Feature is Blocked. Use `"amber"`/`"At Risk"` if progress looks stalled relative to target dates, or leave as the default if there isn't enough signal - don't over-infer.
- **`progress` on features**: 100 (status category Done), 50 (In Progress), 10 (Blocked/Flagged), 0 (To Do/Backlog). See the mapping table in [SKILL.md](SKILL.md).
- **`progress` on masterFeatures**: `Math.round` of the mean of its `features[].progress`; 0 if it has no features yet.
- **`group`**: pull from the Jira "Group" custom field on the leaf issue (id varies per instance - confirm via `jira_search_fields` with keyword `"group"`, e.g. `customfield_22029`). Fall back to `"Platform Core"` if empty. This is a single value here (unlike the sibling `release-scope-dashboard` skill's `groups` array) - if the field is multiselect, join with `", "` or take the first value.
- **`targetDate` / `date` / `stats.timelineTarget` / `horizon`**: sourced from each issue's own **Planned PI** custom field (confirm id via `jira_search_fields` with keyword `"Planned PI"`), not `duedate`. Format is `"<fiscal-year>-Q<1-4>"`, e.g. `"27-Q1"`. This company's FY `YY` starts Aug 1 of calendar year `YY-1` (Q1 Aug-Oct, Q2 Nov-Jan, Q3 Feb-Apr, Q4 May-Jul). If an issue has multiple Planned PI values, take the latest by ordinal `year*4 + (quarter-1)` and use its raw label as-is - never convert it to a calendar date. Fall back to `"TBD"` if the field is empty. Each level (Initiative, Master Feature, Feature) reads its **own** Planned PI value directly off that issue - this is not a rollup/aggregation from child issues.
- **`risks`**: almost always `[]`. This is only a first-run seed; don't try to keep it in sync with real risk data on every regeneration - that's what the in-dashboard Add/Export/Import UI and localStorage are for.
- All fields default gracefully to "TBD" placeholders in the template - never omit a key, but "TBD" / `0` / `[]` are safe fallbacks throughout.

## Planned PI calendar (`piCalendar`)

Optional top-level map from a Planned PI label (as it appears in `targetDate`/`date`/`stats.timelineTarget`/`horizon`) to its exact `{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }` calendar dates. It powers the dashboard's **Automated Insights** panel's "Planned PI ending soon" / "Planned PI already ended" checks (see below) - without it, those specific checks are silently skipped (status/progress mismatch checks still run regardless).

- Source real `{name, start, end}` triples from a fiscal-quarter timeline file if the workspace has one (e.g. the sibling `pi-readiness-dashboard` skill's `assets/pi_timeline.json` - flatten every `programIncrement` across all its `fiscalYears` entries into `piCalendar[name] = {start, end}`).
- `start` may be omitted for a legacy/edge PI whose exact start isn't known (e.g. a label used right before a fiscal-calendar system changed) - only `end` is required for the deadline checks to work.
- Never fabricate exact dates for a PI you have no source for. If a Planned PI value shows up in the fetched Jira data but isn't in your timeline source and you can't otherwise pin down its `end` date, just omit it from `piCalendar` - the dashboard skips deadline-risk checks for it rather than guessing wrong.
- This is shared across every initiative in the file, not per-initiative, since PIs are company-wide.

## Automated Insights (no data to author - fully derived by the template)

The dashboard computes an "Automated Insights" panel entirely client-side from `masterFeatures`/`features` plus `piCalendar` - there's nothing to add to the JSON for this beyond `piCalendar` itself. It flags, live and using the real current date on every page load:

- **Status/progress mismatch**: a Master-Feature marked `Completed` while its features average under 100% progress, or marked `Planned` while one or more of its features already show progress (or are fully `Completed`) - i.e. the Master-Feature's own Jira status looks stale relative to its children. Each mismatched Master-Feature is its own finding group.
- **Planned PI ending soon / already ended**: every Feature or Master-Feature that isn't `Completed` yet and whose own Planned PI (resolved via `piCalendar`) ends within 14 days or has already passed is collapsed into ONE finding group per `(Planned PI, ended-vs-soon)` pair - e.g. "6 items still open for Planned PI 26-Q2, which ends in 12 days" - rather than one card per item.

Findings surface in two places, kept in sync automatically:

- **Executive Summary tab**: one compact, clickable card per finding group (title + severity badge). Clicking a card jumps to the Insights tab and scrolls/highlights that group.
- **Insights tab** (next to "PI Delivery Schedule"): the full breakdown - every finding group rendered as its own section with a table of every item behind it (name, type, status, progress, Planned PI).

Because these come purely from data you already provide, just make sure `piCalendar` is populated with whatever real PI dates you can source (see above) - the insight logic itself never needs to change per run.
