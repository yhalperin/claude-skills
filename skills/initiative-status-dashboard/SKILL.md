---
name: initiative-status-dashboard
description: >-
  Traverses one or more Jira Initiatives (Initiative -> Master Feature ->
  leaf Feature, via the "Parent Link" field) using the MCP policy broker's
  jira_search/jira_get_issue tools, and renders them as a distinctive,
  self-contained HTML dashboard (KPI cards, Master-Feature milestone table,
  dynamic Jira-Group workload distribution, filterable allocation swimlane
  matrix, a Master-Feature x Planned-PI delivery schedule table, an
  Automated Insights panel flagging status/progress mismatches and
  Planned-PI deadline risks with a detailed drill-down Insights tab, and a
  manually-editable Risks panel) that opens directly in a browser.
  Supports a combined dashboard for several initiatives at once via a header
  dropdown. Re-runnable at any point to refresh with current Jira state
  without losing manually-logged risks. Use when the user asks to generate
  an initiative status dashboard/board, summarize one or more initiatives'
  progress, or visualize Jira initiative/master-feature rollup as a
  shareable HTML page.
disable-model-invocation: true
---

# Initiative Status Dashboard

Produces one self-contained HTML file - no server, no build step - visualizing one or more Jira Initiatives: KPI cards (overall progress, timeline, group distribution), a Master-Feature milestone table, a Jira-Group allocation swimlane matrix, a Master-Feature x Planned-PI delivery schedule table, an Automated Insights panel (with a full drill-down "Insights" tab), and a Risks panel with local persistence. The visual design is already built into `assets/template.html` - do not redesign it per run, only feed it fresh data.

## Workflow

1. **Confirm scope.** Get the Initiative issue key(s) to traverse (e.g. `JAG-36913`, or several at once). If the user gave them, use them. Ask only if genuinely ambiguous.

2. **Fetch data from Jira.** Use the `user-policy-broker` MCP tools (`jira_get_issue`, `jira_search`, `jira_search_fields`) per broker usage rules - never bypass the broker. For each Initiative:
   - Fetch the Initiative issue itself, including its **Planned PI** custom field (fields `summary,status,customfield_<planned_pi_id>` - confirm the id once per instance via `jira_search_fields` with keyword `"Planned PI"`, e.g. `customfield_14422`, exact name `"PlannedPI"`, a multiselect option field returned as `{ "value": ["27-Q1", "26-Q2"] }`).
   - Level 2 - Master Features: `jira_search` with JQL `"Parent Link" = <INITIATIVE_KEY>` (fields `summary,status,issuetype,customfield_<planned_pi_id>`). This Jira instance links hierarchy via the **"Parent Link"** custom field (commonly `customfield_11140`), not the standard `parent` field - confirm the id once per instance via `jira_search_fields` with keyword `"parent"` if the JQL above returns nothing.
   - Level 3 - Features: for each Master Feature key, `jira_search` with JQL `"Parent Link" = <MF_KEY>` (fields `summary,status,issuetype,customfield_<planned_pi_id>,customfield_22029` or whatever the Group field id resolves to - confirm via `jira_search_fields` with keyword `"group"`).
   - **Stop at Level 3.** These leaf issues are the dashboard's "Feature" entries regardless of their literal Jira issue type name (this org typically uses `Theme`, not `Feature` - there is no distinct Feature issue type here). Do not traverse further into any children/Epics nested under them.

3. **Map fields** per issue, with fallbacks so nothing renders broken:
   - Status category -> dashboard status + progress: `Done` -> `Completed`/100, `In Progress` -> `In Progress`/50, `Blocked`/Flagged -> `Blocked`/10, `To Do`/Backlog -> `Planned`/0.
   - `group`: Jira Group custom field value, else `"Platform Core"`.
   - `date`/`targetDate`/`stats.timelineTarget`/`horizon`: the issue's own **Planned PI** value (Initiative -> `stats.timelineTarget`/`horizon`, Master Feature -> `targetDate`, Feature -> `date`). Planned PI is a multi-value field - if an issue has several PI values assigned, take the **chronologically latest one** and use its raw label verbatim (e.g. `"27-Q1"`) as the displayed value; don't convert it to a calendar date. Empty -> `"TBD"`. See "Planned PI quarters" below for the format and how to pick the latest.
   - Master Feature `progress` = round(average of its features' `progress`); its own `status`/color use the same status-category mapping applied to the Master Feature issue itself.
   - `stats.totalFeatures`/`completedFeatures` = counts across all features under that initiative.

### Planned PI quarters

Planned PI values look like `"26-Q2"` or `"27-Q1"`: `<fiscal-year>-Q<1-4>`. This company's fiscal year `YY` starts **August 1 of calendar year `YY-1`** (e.g. FY27 starts Aug 2026), so: Q1 = Aug-Oct, Q2 = Nov-Jan, Q3 = Feb-Apr, Q4 = May-Jul (of that fiscal year).

To pick the latest value when an issue has multiple: convert each to an ordinal `year * 4 + (quarter - 1)` and take the max - this sorts correctly without needing real calendar dates. (Simple string comparison of `"YY-Qn"` labels also happens to sort correctly here, since both parts are fixed-width, but the ordinal is clearer to compute explicitly.)

4. **Build the Planned PI calendar** (`piCalendar` in the schema) - this is what powers the Automated Insights panel's "Planned PI ending soon / already ended" checks. Look for a fiscal-quarter timeline file already in the workspace (e.g. the sibling `pi-readiness-dashboard` skill's `assets/pi_timeline.json`) and flatten its `programIncrement` entries (`name`, `start`, `end`) across all `fiscalYears` into `piCalendar[name] = {start, end}`. If a Planned PI value shows up in your fetched Jira data but you have no source for its exact dates (e.g. a legacy label from before a fiscal-calendar change, or simply not in the timeline file), either ask the user for its end date or omit it from `piCalendar` - never fabricate a date; the dashboard just skips deadline checks for PIs it can't resolve. This map is shared across all initiatives in the file (top-level, not per-initiative).

5. **Assemble the JSON** matching [DATA_SCHEMA.md](DATA_SCHEMA.md) exactly - one key per initiative under `initiatives`, plus the top-level `piCalendar`, all in a single file even when given several initiative IDs (the template's dropdown switches between them at runtime). Write it to a temp file, e.g. `initiative_data.json`. No extra work is needed for the "PI Delivery Schedule" tab or the "Automated Insights" panel/"Insights" tab beyond this - the template derives everything else (schedule columns/rows, mismatch detection grouped by finding, PI-deadline items grouped by Planned PI, deadline countdowns using the real current date) live from `masterFeatures`/`features`/`piCalendar`.

6. **Render**:
   ```bash
   python scripts/render_dashboard.py --data initiative_data.json
   ```
   This injects the JSON into `assets/template.html` and writes `dashboard_<keys>.html` next to the data file (a **stable** filename, not timestamped - see "Re-running" below), then opens it in the default browser. Pass `--out <path>` to control the filename, or `--no-open` to skip auto-opening.

7. Report a traversal summary per initiative: Initiative title, # Master Features, # Features resolved, any fallbacks used (missing dates/groups), and a quick note of what the Automated Insights panel surfaced (e.g. "flagged 2 status mismatches and 1 Planned-PI group with 6 items still open for 26-Q2, ending in 12 days - full breakdown on the Insights tab").

## Re-running for a status update

Same initiative key(s), same workflow. Manually-added risks live in the browser's `localStorage`, keyed by initiative id **and** the file's origin/path - so reuse the exact same output filename (the script's default is already stable and reproducible per initiative-key-set) to keep risks intact across regenerations. If the user needs to move the dashboard to a different path/machine, tell them to use the in-dashboard **Export** button first and **Import** after regenerating.

## Additional resources

- Exact JSON shape and field semantics: [DATA_SCHEMA.md](DATA_SCHEMA.md)
- Dashboard markup/styling (edit only for structural bugs - preserve the design): [assets/template.html](assets/template.html)
- Example data file for reference: [examples/jag-36913-data.json](examples/jag-36913-data.json)
