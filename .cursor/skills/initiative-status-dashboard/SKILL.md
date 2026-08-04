---
name: initiative-status-dashboard
description: >-
  Traverses one or more Jira Initiatives (Initiative -> Master Feature ->
  leaf Feature, via the "Parent Link" field) using the MCP policy broker's
  jira_search/jira_get_issue tools, and renders them as a distinctive,
  self-contained HTML dashboard (KPI cards, a Master-Feature milestone card
  grid, dynamic Jira-Group workload distribution, a Master-Feature x
  Planned-PI delivery schedule table with a multi-select Group filter, a
  per-item traffic-light Health indicator, clickable Jira deep links on every
  issue key, and an Automated Insights panel flagging status/progress
  mismatches, Planned-PI deadline risks, and Initiative timeline slippage
  with a detailed drill-down Insights tab) that opens directly in a browser.
  Supports a combined dashboard for
  several initiatives at once via a header dropdown. Re-runnable at any
  point to refresh with current Jira state. Use when the user asks to
  generate an initiative status dashboard/board, summarize one or more
  initiatives' progress, or visualize Jira initiative/master-feature
  rollup as a shareable HTML page.
disable-model-invocation: true
---

# Initiative Status Dashboard

Produces one self-contained HTML file - no server, no build step - visualizing one or more Jira Initiatives: KPI cards (overall progress, timeline, group distribution), a Master-Feature milestone panel swimlaned by target Planned PI with per-item, click-to-explain Health badges (clicking a card jumps to that Master-Feature's row on the PI Delivery Schedule tab), a Master-Feature x Planned-PI delivery schedule table with a multi-select Group filter, clickable Jira deep links on every issue key shown anywhere on the board, and an Automated Insights panel (with a full drill-down "Insights" tab). Whenever 2+ initiatives are loaded, the dashboard opens on an **Overview** landing page summarizing every initiative's progress and Planned-Timeline-vs-Actual at a glance, with each card/dropdown entry drilling into that initiative's full detail view (a single-initiative dashboard skips the Overview entirely and opens straight into the detail view, unchanged from before). The visual design is already built into `assets/template.html` - do not redesign it per run, only feed it fresh data.

## Workflow

1. **Confirm scope.** Get the Initiative issue key(s) to traverse (e.g. `JAG-36913`, or several at once). If the user gave them, use them - this includes an Initiative key arriving as the entire prompt from a Slack `@Cursor` mention or an Automation, which counts as fully confirmed scope just like a typed-out IDE request. Ask only if genuinely ambiguous **and there is an interactive user able to answer** - see "Running autonomously" below for the unattended case. Also determine the Jira **browse base URL** (`jiraBaseUrl` in the schema, e.g. `"https://your-jira-host/browse/"`) so issue keys can be deep-linked - infer it from context if the user has already shared a Jira issue link (this session or a prior one for the same Jira instance) or from an existing dashboard's data file for this instance; otherwise ask once, or omit it if there's nobody to ask. Without it, names simply render as plain text (no broken behavior either way).

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

5. **Assemble the JSON** matching [DATA_SCHEMA.md](DATA_SCHEMA.md) exactly - one key per initiative under `initiatives`, plus the top-level `piCalendar` and `jiraBaseUrl` (if known), all in a single file even when given several initiative IDs (the template's dropdown switches between them at runtime). Write it to a temp file, e.g. `initiative_data.json`. No extra work is needed for the "PI Delivery Schedule" tab (including its Group filter), the Health badges, the Jira deep links, the "Automated Insights" panel/"Insights" tab, or the multi-initiative Overview page beyond this - the template derives everything else (schedule columns/rows, Group filter options, per-item Health, mismatch detection grouped by finding, PI-deadline items grouped by Planned PI, deadline countdowns using the real current date, linking every embedded issue key found in a name/title, and the Overview's per-initiative progress/timeline cards) live from `masterFeatures`/`features`/`piCalendar`/`jiraBaseUrl`.

6. **Render**:
   ```bash
   python scripts/render_dashboard.py --data initiative_data.json
   ```
   This is the one fully-scripted, non-interactive step in this whole workflow - plain `argparse`, no prompts, a clean non-zero exit code with a message on stderr if `--data`/the template can't be read or the JSON has no `initiatives`. It injects the JSON into `assets/template.html` and writes `dashboard_<keys>.html` next to the data file (a **stable** filename, not timestamped - see "Re-running" below), then opens it in the default browser. Pass `--out <path>` to control the filename, or **`--no-open`** when there's no browser to open it in (always use this in a Cloud Agent/Slack/Automation run - see below).

7. Report a traversal summary per initiative: Initiative title, # Master Features, # Features resolved, any fallbacks used (missing dates/groups), a quick count of items with a "Warning"/"At Risk" Health badge, and a note of what the Automated Insights panel surfaced (e.g. "flagged 2 status mismatches, 1 Planned-PI group with 6 items still open for 26-Q2 ending in 12 days, and an Off Track timeline slip (latest PI 27-Q2 vs Delivery Target 26-07) - full breakdown on the Insights tab").

## Re-running for a status update

Same initiative key(s), same workflow - just re-fetch and re-render. There's no local state to preserve between runs (the Health badges, Automated Insights, and filters are all derived live from the JSON + the real current date), so simply overwrite the previous output file.

## Running autonomously (Slack, Cloud Agents, Automations)

This entire workflow works unchanged from an interactive IDE/CLI Agent chat - nothing above requires the non-interactive path. The difference only matters when there's genuinely nobody available to answer a follow-up question, e.g. a Cloud Agent triggered by a Slack `@Cursor` mention or an Automation, where the whole task arrives as one message (typically just the Initiative issue key(s)) and there's no next turn to clarify anything in.

The repo's [`.cursor/rules/initiative-status-dashboard.mdc`](../../rules/initiative-status-dashboard.mdc) is the enforced contract for that case - always-applied, so it's in effect for every agent working in this repo, not just when this skill happens to be invoked. In short: an Initiative key given as the whole prompt is already-confirmed scope (never stall on "should I proceed?"), any other missing/ambiguous field falls back to this file's documented placeholders (`"TBD"`, omitting an unresolvable Planned PI, etc.) instead of a question nobody can answer, step 6 always runs with `--no-open`, and a blocked Jira MCP call with nobody available to approve it gets reported plainly rather than silently dropped or left hanging.

## Additional resources

- Exact JSON shape and field semantics: [DATA_SCHEMA.md](DATA_SCHEMA.md)
- Dashboard markup/styling (edit only for structural bugs - preserve the design): [assets/template.html](assets/template.html)
- Example data file for reference: [examples/jag-36913-data.json](examples/jag-36913-data.json)
- Autonomous/non-interactive execution contract (Slack, Cloud Agents, Automations): [`.cursor/rules/initiative-status-dashboard.mdc`](../../rules/initiative-status-dashboard.mdc) at the repo root
