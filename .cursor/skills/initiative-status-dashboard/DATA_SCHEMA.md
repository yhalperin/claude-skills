# Initiative Data JSON Schema

This is the JSON payload `scripts/render_dashboard.py` injects into the dashboard template. Build this object from Jira query results, write it to a file, then render. Include one entry per requested initiative under `initiatives` - the template's header dropdown is populated dynamically from these keys, so a single file can hold one or several initiatives.

```jsonc
{
  "generatedAt": "2026-07-13T15:55:00+03:00",   // ISO timestamp, informational only
  "jiraBaseUrl": "https://your-jira-host/browse/",  // optional, shared across all initiatives - see "Jira deep links" below
  "piCalendar": {                                // optional, shared across all initiatives - see "Planned PI calendar" below
    "26-Q2": { "end": "2026-08-01" },             // legacy PI (no known start) - the last one before the current fiscal system
    "27-Q1": { "start": "2026-08-02", "end": "2026-11-07" },
    "27-Q2": { "start": "2026-11-08", "end": "2027-01-30" },
    "27-Q3": { "start": "2027-01-31", "end": "2027-04-24" },
    "27-Q4": { "start": "2027-04-25", "end": "2027-07-31" }
  },
  "initiatives": {
    "jag-36913": {                               // key: lowercased initiative issue key - drives the header dropdown value
      "title": "JAG-36913: Priv Cloud centralization + guided flows + Dark mode",  // Initiative issue summary, prefixed with its key
      "status": "On Track",                       // "On Track" | "At Risk" | "Blocked" - free text shown on the header pill
      "statusColor": "emerald",                   // "emerald" | "amber" | "rose" - drives the pill color, pick per statusColor rule below
      "scope": "TBD",                              // free text scope badge; "TBD" if no clear scope field exists
      "horizon": "Target 27-Q1",                    // "Target <Planned PI>" using the Initiative issue's own Planned PI (latest value if several), else "Target TBD"
      "timelineRange": "26-07",                     // Initiative issue's Jira "Delivery Target" field value, verbatim (e.g. "26-07" = July 2026); "TBD" if empty - see "Delivery Target field" below
      "stats": {
        "totalFeatures": 14,                        // count of all leaf features across all master features
        "completedFeatures": 5,                      // count of leaf features with status "Completed"
        "timelineTarget": "27-Q1",                    // the Initiative issue's own Planned PI (latest value if several), else "TBD" - see Planned PI notes below
        "timelineVariance": "On Schedule"              // "On Schedule" | "Delayed" | "Ahead of Schedule" | "At Risk" - your best-guess fallback; the template auto-overrides this to "Off Track" whenever it can prove timelineTarget's PI ends after timelineRange (see "Delivery Target field" below), so don't try to hand-compute that case
      },
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

- **`initiatives` keys** must be the lowercased initiative issue key (e.g. `"jag-36913"`). The dropdown and CSV export filenames all derive from this key - do not use an arbitrary slug.
- **`statusColor`**: default `"emerald"`/`"On Track"`. Use `"rose"`/`"Blocked"` only if the Initiative issue itself is Blocked or any Master-Feature is Blocked. Use `"amber"`/`"At Risk"` if progress looks stalled relative to target dates, or leave as the default if there isn't enough signal - don't over-infer.
- **`progress` on features**: 100 (status category Done), 50 (In Progress), 10 (Blocked/Flagged), 0 (To Do/Backlog). See the mapping table in [SKILL.md](SKILL.md).
- **`progress` on masterFeatures**: `Math.round` of the mean of its `features[].progress`; 0 if it has no features yet.
- **`group`**: pull from the Jira "Group" custom field on the leaf issue (id varies per instance - confirm via `jira_search_fields` with keyword `"group"`, e.g. `customfield_22029`). Fall back to `"Platform Core"` if empty. This is a single value here (unlike the sibling `release-scope-dashboard` skill's `groups` array) - if the field is multiselect, join with `", "` or take the first value. Also drives the multi-select Group filter on the PI Delivery Schedule tab (see below) - no separate JSON field needed for that.
- **`targetDate` / `date` / `stats.timelineTarget` / `horizon`**: sourced from each issue's own **Planned PI** custom field (confirm id via `jira_search_fields` with keyword `"Planned PI"`), not `duedate`. Format is `"<fiscal-year>-Q<1-4>"`, e.g. `"27-Q1"`. This company's FY `YY` starts Aug 1 of calendar year `YY-1` (Q1 Aug-Oct, Q2 Nov-Jan, Q3 Feb-Apr, Q4 May-Jul). If an issue has multiple Planned PI values, take the latest by ordinal `year*4 + (quarter-1)` and use its raw label as-is - never convert it to a calendar date. Fall back to `"TBD"` if the field is empty. Each level (Initiative, Master Feature, Feature) reads its **own** Planned PI value directly off that issue - this is not a rollup/aggregation from child issues. This value also drives each item's **Health** badge (see below).
- **`timelineRange`**: sourced from the Initiative issue's own Jira **"Delivery Target"** custom field (confirm id via `jira_search_fields` with keyword `"Delivery Target"`, e.g. `customfield_22933`). The field comes back as `{ "value": "YY-MM" }`, e.g. `"26-07"` (July 2026) or `"26-12"` (December 2026) - use that string verbatim, do NOT convert it to a month name. Fall back to `"TBD"` if empty or in an unrecognized shape. See "Delivery Target field" below for how this powers the automatic Off Track check.
- All fields default gracefully to "TBD" placeholders in the template - never omit a key, but "TBD" / `0` / `[]` are safe fallbacks throughout.

## Jira deep links (`jiraBaseUrl`)

Optional top-level string - the "browse" URL prefix for your Jira instance, e.g. `"https://your-jira-host/browse/"` (a trailing slash is added automatically if missing). When present, the template automatically turns the Jira issue key embedded in every Master-Feature/Feature/Initiative name into a clickable deep link to that issue - **only the key text itself is linked**, not the whole name, and any surrounding punctuation (parentheses, the colon after an Initiative's key prefix) stays plain text. This covers every place a name/title is shown: Executive Summary milestone cards, PI Delivery Schedule rows and Feature cards, the Automated Insights cards/tables, and Health-badge reason popovers.

Two shapes are recognized automatically - no extra JSON needed beyond names already following the conventions in this schema:

- **Trailing `(KEY-123)`** - every Master-Feature/Feature `name` already ends this way (e.g. `"Master-Feature: Foo (SHLD-28144)"` -> only `SHLD-28144` becomes a link).
- **Leading `KEY-123:`** - an Initiative's `title` (e.g. `"DPA-13462: [2026] Delegated administration..."` -> only `DPA-13462` becomes a link).

If `jiraBaseUrl` is omitted, names simply render as plain text exactly as before - never guess a Jira host.

## Planned PI calendar (`piCalendar`)

Optional top-level map from a Planned PI label (as it appears in `targetDate`/`date`/`stats.timelineTarget`/`horizon`) to its exact `{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }` calendar dates. It powers the dashboard's **Automated Insights** panel's "Planned PI ending soon" / "Planned PI already ended" checks and the per-item **Health** badges (see below) - without it, those specific checks are silently skipped (status/progress mismatch checks still run regardless).

- Source real `{name, start, end}` triples from a fiscal-quarter timeline file if the workspace has one (e.g. the sibling `pi-readiness-dashboard` skill's `assets/pi_timeline.json` - flatten every `programIncrement` across all its `fiscalYears` entries into `piCalendar[name] = {start, end}`).
- `start` may be omitted for a legacy/edge PI whose exact start isn't known (e.g. a label used right before a fiscal-calendar system changed) - only `end` is required for the deadline checks to work.
- Never fabricate exact dates for a PI you have no source for. If a Planned PI value shows up in the fetched Jira data but isn't in your timeline source and you can't otherwise pin down its `end` date, just omit it from `piCalendar` - the dashboard skips deadline-risk checks for it rather than guessing wrong.
- This is shared across every initiative in the file, not per-initiative, since PIs are company-wide.

## Delivery Target field (`timelineRange`) and the automatic Off Track check

`timelineRange` holds the Initiative issue's own Jira **"Delivery Target"** custom field value verbatim - a `"YY-MM"` label like `"26-12"` (December 2026) representing the committed delivery month. The template parses this to that month's last calendar day and compares it against `stats.timelineTarget`'s own resolved PI end date (via `piCalendar`):

- If the latest Planned PI ends **after** the Delivery Target month, the Initiative has slipped past what was committed - the "Status Sync" badge on the Planned Timeline KPI card is automatically forced to **"Off Track"** (overriding whatever you authored in `stats.timelineVariance`), and a matching Automated Insight is raised (see below).
- If either date can't be resolved (`timelineRange` isn't a parseable `"YY-MM"` string, or `stats.timelineTarget`'s PI isn't in `piCalendar`), the check is silently skipped and your authored `stats.timelineVariance` stands as-is - never guess dates yourself to force this.
- This means you should NOT try to hand-compute "Off Track" in `stats.timelineVariance` - just author your best-guess fallback there for cases the automatic check can't resolve, and populate `timelineRange` + `piCalendar` accurately; the template derives the verdict live.

## Health Indicator (no data to author - fully derived by the template)

Every Master-Feature and Feature card/row shows a small traffic-light **Health** badge (Executive Summary milestone cards, and both the Master-Feature row and each Feature card on the PI Delivery Schedule tab). It always takes the **worst** of up to three signals, recomputed live against the real current date on every render:

1. **Deadline health** (Features and Master-Features): the item is `Blocked` -> At Risk; its own Planned PI (`targetDate`/`date`, resolved via `piCalendar`) has already ended while it isn't `Completed` -> At Risk; that PI ends within 14 days while still open -> Warning; otherwise Good. A `Completed` item is never deadline-flagged (a stale "Completed" is caught by signal 2 instead). Any Planned PI not in `piCalendar` is never guessed - defaults to Good.
2. **Self mismatch health** (Master-Features only): does the Master-Feature's own `status` look stale next to its rolled-up `progress`? Marked `Completed` while `progress < 100` -> At Risk if `progress < 50`, else Warning (e.g. **marked Completed but only 40% of its features are actually done -> At Risk**, not Good). Marked `Planned` while one or more features already show progress -> At Risk if any are fully `Completed`, else Warning. These use the exact same thresholds as the "status/progress mismatch" Automated Insight, so the badge and the insight always agree.
3. **Roll-up health** (Master-Features only): a Master-Feature's badge can never be healthier than its worst Feature - **if even one Feature underneath it is Warning or At Risk, the Master-Feature is too**.

Nothing needs to be added to the JSON for this beyond `masterFeatures`/`features` and `piCalendar` already being populated accurately.

**Why this health? (click-to-explain).** Every badge that isn't Good is clickable - clicking it opens a small popover listing the exact reason(s) it isn't Good in plain English (e.g. *"Marked Completed, but its features are only 40% done on average (2/5 completed)."*, or, rolled up from a child, *"Feature 'X': Planned PI 26-Q2 ends in 5 days, and this is still In Progress."*). Good badges have no reasons and aren't clickable. This uses the exact same `computeMasterFeatureHealth`/`computeFeatureHealth` results as the badge color itself, so the popover text and the badge color can never disagree.

**Click-through from Executive Summary to Schedule.** Clicking anywhere on a Master-Feature milestone card in the Executive Summary tab (outside the Health badge itself, which opens its own popover instead) jumps to the PI Delivery Schedule tab with that Master-Feature isolated via the same row filter used by clicking a row there directly.

## Group filter (PI Delivery Schedule tab)

The PI Delivery Schedule tab includes a multi-select **Filter by Group** pill row, built live from the distinct `group` values found across all `features[]` in the current initiative (the same values used by the Group Distribution KPI on the Executive Summary tab). Selecting one or more groups restricts the schedule table to only features (and Master-Feature rows that still have a match) in those groups; selecting none shows everything. No separate JSON field is needed - just populate `group` accurately on every feature.

## Automated Insights (no data to author - fully derived by the template)

The dashboard computes an "Automated Insights" panel entirely client-side from `masterFeatures`/`features` plus `piCalendar`/`timelineRange` - there's nothing to add to the JSON for this beyond those fields. It flags, live and using the real current date on every page load:

- **Status/progress mismatch**: a Master-Feature marked `Completed` while its features average under 100% progress, or marked `Planned` while one or more of its features already show progress (or are fully `Completed`) - i.e. the Master-Feature's own Jira status looks stale relative to its children. Each mismatched Master-Feature is its own finding group.
- **Planned PI ending soon / already ended**: every Feature or Master-Feature that isn't `Completed` yet and whose own Planned PI (resolved via `piCalendar`) ends within 14 days or has already passed is collapsed into ONE finding group per `(Planned PI, ended-vs-soon)` pair - e.g. "6 items still open for Planned PI 26-Q2, which ends in 12 days" - rather than one card per item.
- **Initiative timeline slippage (Off Track)**: one group when the Initiative's latest Planned PI ends later than its Jira Delivery Target (see above) - e.g. "Latest Planned PI (27-Q2) ends 194 days after the Initiative's Jira Delivery Target (26-07) - marked Off Track".

Findings surface in two places, kept in sync automatically:

- **Executive Summary tab**: one compact, clickable card per finding group (title + severity badge). Clicking a card jumps to the Insights tab and scrolls/highlights that group.
- **Insights tab** (next to "PI Delivery Schedule"): the full breakdown - every finding group rendered as its own section with a table of every item behind it (name, type, status, progress, Planned PI).

Because these come purely from data you already provide, just make sure `piCalendar` is populated with whatever real PI dates you can source (see above) - the insight logic itself never needs to change per run.
