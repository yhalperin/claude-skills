---
name: initiative-status-dashboard
description: >-
  Traverses one or more Jira Initiatives (Initiative -> Master Feature ->
  leaf Feature, via the "Parent Link" field) using the MCP policy broker's
  jira_search/jira_get_issue tools, and renders them as a distinctive,
  self-contained HTML dashboard (KPI cards, a Master-Feature milestone card
  grid, dynamic Jira-Group workload distribution, a Master-Feature x
  Planned-PI delivery schedule table with a multi-select Group filter, a
  per-item traffic-light Health indicator, and an Automated Insights panel
  flagging status/progress mismatches, Planned-PI deadline risks, and
  Initiative timeline slippage with a detailed drill-down Insights tab)
  that opens directly in a browser. Supports a combined dashboard for
  several initiatives at once via a header dropdown. Re-runnable at any
  point to refresh with current Jira state. Scope can be provided as direct
  Jira key(s) OR as a natural-language search (by investment area, PM,
  RND lead, project, keyword, status, etc.) which is translated to JQL
  automatically. Use when the user asks to generate an initiative status
  dashboard/board, summarize one or more initiatives' progress, visualize
  Jira initiative/master-feature rollup as a shareable HTML page, or search
  for initiatives matching specific criteria.
disable-model-invocation: true
---

# Initiative Status Dashboard

Produces one self-contained HTML file - no server, no build step - visualizing one or more Jira Initiatives: KPI cards (overall progress, timeline, group distribution), a Master-Feature milestone card grid with per-item, click-to-explain Health badges (clicking a card jumps to that Master-Feature's row on the PI Delivery Schedule tab), a Master-Feature x Planned-PI delivery schedule table with a multi-select Group filter, and an Automated Insights panel (with a full drill-down "Insights" tab). The visual design is already built into `assets/template.html` - do not redesign it per run, only feed it fresh data.

## Help / usage examples

If the user's request is `/initiative-status-dashboard help` (or includes `--help`), reply with the block below and **stop** - do not fetch any data:

```
Initiative Status Dashboard – usage examples

  By Jira key (one or more):
    /initiative-status-dashboard DPA-14520
    /initiative-status-dashboard DPA-14520 JAG-36913

  By investment area / label:
    /initiative-status-dashboard for all initiatives in investment area "Atlas"
    /initiative-status-dashboard investment area Olympus

  By Responsible PM:
    /initiative-status-dashboard all initiatives where PM is "Jane Doe"

  By Assigned R&D Lead:
    /initiative-status-dashboard RND lead "John Smith"

  By project:
    /initiative-status-dashboard all initiatives in project DPA

  By keyword in title:
    /initiative-status-dashboard initiatives containing "security"

  By status:
    /initiative-status-dashboard all in-progress initiatives in project DPA

  Combined filters:
    /initiative-status-dashboard investment area Atlas, PM "Jane Doe"

  Refresh existing dashboard (re-fetch + re-render):
    /initiative-status-dashboard DPA-14520   ← same command, run again

  Show this help:
    /initiative-status-dashboard help
```

---

## Workflow

1. **Resolve scope.** Determine which Initiative issue key(s) to traverse. Three input modes are supported:

   **a) Direct key(s)** — one or more Jira keys like `DPA-14520` or `JAG-36913 DPA-14520`.
   Use them directly; skip to step 2.

   **b) Named-field search** — the user describes initiatives by a field value rather than a key.
   Common patterns and how to translate them to JQL:

   | User says | JQL fragment | Notes |
   |---|---|---|
   | investment area "Atlas" | `labels = "Atlas"` or `component = "Atlas"` | Try `labels` first; if 0 results try `component`; if still 0, use `jira_search_fields` with keyword `"investment area"` to find the right custom field |
   | PM / product lead "Jane" | `cf[20021] = "Jane Doe"` | `customfield_20021` = Responsible PM (confirm via `jira_search_fields "Responsible PM"` if unsure) |
   | RND lead "John" | `cf[21851] = "John Smith"` | `customfield_21851` = Assigned RND Lead (confirm via `jira_search_fields "RND Lead"` if unsure) |
   | project DPA | `project = DPA` | Standard Jira project key |
   | contains "security" | `summary ~ "security"` | Free-text title search |
   | in-progress / active | `statusCategory = "In Progress"` | Use Jira status category, not status name |
   | critical | `cf[11143] = "Yes"` | Critical Item custom field |

   Build the full JQL: `issuetype = Initiative AND <filter(s)>` and run `jira_search` to get matching keys.
   - **0 results** → report "No initiatives matched. Try refining your search." and stop.
   - **1–5 results** → list them (key + title + status) and proceed with all unless the user said "show me" / "list" (in which case stop after listing).
   - **6+ results** → list them all and ask the user to confirm which to include before fetching data.

   **c) Ambiguous / no scope given** — ask the user: "Which initiative(s) should I build the dashboard for? You can give me a Jira key (e.g. `DPA-14520`) or describe them (e.g. 'all Atlas initiatives' or 'initiatives where PM is Jane Doe')."

2. **Fetch data from Jira.** Use the `user-policy-broker` MCP tools (`jira_get_issue`, `jira_search`, `jira_search_fields`) per broker usage rules - never bypass the broker. For each Initiative:
   - Fetch the Initiative issue itself, including its **Planned PI** custom field (fields `summary,status,customfield_<planned_pi_id>` - confirm the id once per instance via `jira_search_fields` with keyword `"Planned PI"`, e.g. `customfield_14422`, exact name `"PlannedPI"`, a multiselect option field returned as `{ "value": ["27-Q1", "26-Q2"] }`) and its **Delivery Target** custom field (confirm the id via `jira_search_fields` with keyword `"Delivery Target"`, e.g. `customfield_22933`; returned as `{ "value": "YY-MM" }`, e.g. `"26-07"` (July 2026) or `"26-12"` (December 2026) -> `timelineRange`).
   - Level 2 - Master Features: `jira_search` with JQL `"Parent Link" = <INITIATIVE_KEY>` (fields `summary,status,issuetype,customfield_<planned_pi_id>`). This Jira instance links hierarchy via the **"Parent Link"** custom field (commonly `customfield_11140`), not the standard `parent` field - confirm the id once per instance via `jira_search_fields` with keyword `"parent"` if the JQL above returns nothing.
   - Level 3 - Features: for each Master Feature key, `jira_search` with JQL `"Parent Link" = <MF_KEY>` (fields `summary,status,issuetype,customfield_<planned_pi_id>,customfield_22029` or whatever the Group field id resolves to - confirm via `jira_search_fields` with keyword `"group"`).
   - **Stop at Level 3.** These leaf issues are the dashboard's "Feature" entries regardless of their literal Jira issue type name (this org typically uses `Theme`, not `Feature` - there is no distinct Feature issue type here). Do not traverse further into any children/Epics nested under them.

3. **Map fields** per issue, with fallbacks so nothing renders broken:
   - Status category -> dashboard status + progress: `Done` -> `Completed`/100, `In Progress` -> `In Progress`/50, `Blocked`/Flagged -> `Blocked`/10, `To Do`/Backlog -> `Planned`/0.
   - `group`: Jira Group custom field value, else `"Platform Core"`.
   - `date`/`targetDate`/`stats.timelineTarget`/`horizon`: the issue's own **Planned PI** value (Initiative -> `stats.timelineTarget`/`horizon`, Master Feature -> `targetDate`, Feature -> `date`). Planned PI is a multi-value field - if an issue has several PI values assigned, take the **chronologically latest one** and use its raw label verbatim (e.g. `"27-Q1"`) as the displayed value; don't convert it to a calendar date. Empty -> `"TBD"`. See "Planned PI quarters" below for the format and how to pick the latest. This same value also drives that item's traffic-light **Health** badge (see below) - no separate field needed.
   - `timelineRange`: the Initiative issue's own **Delivery Target** value, verbatim (e.g. `"26-07"`). Empty/unrecognized shape -> `"TBD"`. Do NOT try to hand-derive `stats.timelineVariance`'s "Off Track" case from this yourself - the template cross-checks `timelineRange` against `stats.timelineTarget` (via `piCalendar`) automatically on render; just populate both fields accurately and let it compute the verdict.
   - Master Feature `progress` = round(average of its features' `progress`); its own `status`/color use the same status-category mapping applied to the Master Feature issue itself.
   - `stats.totalFeatures`/`completedFeatures` = counts across all features under that initiative.

### Planned PI quarters

Planned PI values look like `"26-Q2"` or `"27-Q1"`: `<fiscal-year>-Q<1-4>`. This company's fiscal year `YY` starts **August 1 of calendar year `YY-1`** (e.g. FY27 starts Aug 2026), so: Q1 = Aug-Oct, Q2 = Nov-Jan, Q3 = Feb-Apr, Q4 = May-Jul (of that fiscal year).

To pick the latest value when an issue has multiple: convert each to an ordinal `year * 4 + (quarter - 1)` and take the max - this sorts correctly without needing real calendar dates. (Simple string comparison of `"YY-Qn"` labels also happens to sort correctly here, since both parts are fixed-width, but the ordinal is clearer to compute explicitly.)

4. **Build the Planned PI calendar** (`piCalendar` in the schema) - this powers both the Automated Insights panel's "Planned PI ending soon / already ended" checks AND every item's traffic-light **Health** badge. Look for a fiscal-quarter timeline file already in the workspace (e.g. the sibling `pi-readiness-dashboard` skill's `assets/pi_timeline.json`) and flatten its `programIncrement` entries (`name`, `start`, `end`) across all `fiscalYears` into `piCalendar[name] = {start, end}`. If a Planned PI value shows up in your fetched Jira data but you have no source for its exact dates (e.g. a legacy label from before a fiscal-calendar change, or simply not in the timeline file), either ask the user for its end date or omit it from `piCalendar` - never fabricate a date; the dashboard just skips deadline/health checks for PIs it can't resolve (and defaults their Health to "Good" rather than guessing).

5. **Assemble the JSON** matching [DATA_SCHEMA.md](DATA_SCHEMA.md) exactly - one key per initiative under `initiatives`, plus the top-level `piCalendar`, all in a single file even when given several initiative IDs (the template's dropdown switches between them at runtime). Write it to a temp file, e.g. `initiative_data.json`. No extra work is needed for the "PI Delivery Schedule" tab (including its Group filter), the Health badges, or the "Automated Insights" panel/"Insights" tab beyond this - the template derives everything else (schedule columns/rows, Group filter options, per-item Health, mismatch detection grouped by finding, PI-deadline items grouped by Planned PI, deadline countdowns using the real current date) live from `masterFeatures`/`features`/`piCalendar`.

6. **Render**:
   ```bash
   python scripts/render_dashboard.py --data initiative_data.json
   ```
   This injects the JSON into `assets/template.html` and writes `dashboard_<keys>.html` next to the data file (a **stable** filename, not timestamped - see "Re-running" below), then opens it in the default browser. Pass `--out <path>` to control the filename, or `--no-open` to skip auto-opening.

7. Report a traversal summary per initiative: Initiative title, # Master Features, # Features resolved, any fallbacks used (missing dates/groups), a quick count of items with a "Warning"/"At Risk" Health badge, and a note of what the Automated Insights panel surfaced (e.g. "flagged 2 status mismatches, 1 Planned-PI group with 6 items still open for 26-Q2 ending in 12 days, and an Off Track timeline slip (latest PI 27-Q2 vs Delivery Target 26-07) - full breakdown on the Insights tab").

## Re-running for a status update

Same initiative key(s), same workflow - just re-fetch and re-render. There's no local state to preserve between runs (the Health badges, Automated Insights, and filters are all derived live from the JSON + the real current date), so simply overwrite the previous output file.

## Additional resources

- Exact JSON shape and field semantics: [DATA_SCHEMA.md](DATA_SCHEMA.md)
- Dashboard markup/styling (edit only for structural bugs - preserve the design): [assets/template.html](assets/template.html)
- Example data file for reference: [examples/jag-36913-data.json](examples/jag-36913-data.json)
