# Initiative Data JSON Schema

This is the JSON payload `scripts/render_dashboard.py` injects into the dashboard template. Build this object from Jira query results, write it to a file, then render. Include one entry per requested initiative under `initiatives` - the template's header dropdown is populated dynamically from these keys, so a single file can hold one or several initiatives.

```jsonc
{
  "generatedAt": "2026-07-13T15:55:00+03:00",   // ISO timestamp, informational only
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
