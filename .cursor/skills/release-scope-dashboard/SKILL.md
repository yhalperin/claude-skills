---
name: release-scope-dashboard
description: >-
  Extracts a release's scope and current status from Jira (via the MCP
  policy broker's jira_search tools) and renders it as a distinctive,
  self-contained HTML dashboard (completion gauge, per-type status donuts,
  Themes/Epics grouped into headline sections with status and Jira Group,
  filterable bug list, sticky jump-to-section nav) that opens directly
  in a browser instead of a Confluence page. Re-runnable at any point in a
  release's lifecycle (planning, mid-development, code freeze, RC, GA) to
  regenerate a dashboard reflecting the current Jira state. Use when the
  user asks to summarize a release's scope, generate a release status
  dashboard/report/page, or visualize Jira release progress as a shareable
  HTML page.
disable-model-invocation: true
---

# Release Scope Dashboard

Produces one self-contained HTML file — no server, no build step — visualizing a release's completion %, per-issue-type status breakdown, Themes/Epics grouped into headline sections with status, and a searchable/sortable bug table, with a sticky nav for jumping between sections. The visual design (industrial "release control room": dark theme, Big Shoulders Display + IBM Plex Mono + Archivo, amber/green/crimson status coding) is already built into `assets/template.html` — do not redesign it per run, only feed it fresh data.

## Workflow

1. **Confirm scope.** Get the Jira `fixVersion` (or equivalent release identifier) to query, e.g. `"pcloud 15.0"`. If the user gave one, use it. Ask only if genuinely ambiguous. A `phase` label (e.g. "Code Freeze", "RC", "GA'd") is optional — infer a reasonable one from the done% if not given, or omit it.

2. **Fetch data from Jira.** Use the `user-policy-broker` MCP tools (`jira_search`, etc.) per `/user-policy-broker/broker-usage` rules — never bypass the broker. Base JQL: `fixVersion = "<release>"`.
   - Status totals — three cheap `limit:1` queries reading only the `total` field:
     `statusCategory = Done`, `statusCategory = "In Progress"`, `statusCategory = "To Do"`.
   - Type composition with status split — page through lightweight fields (`issuetype,status`) sorted `ORDER BY issuetype ASC` and tally `done`/`inProgress`/`toDo` per `issuetype`, OR run three `statusCategory = ...` `limit:1` queries per distinct type if the type set is already known. See `byType` in [DATA_SCHEMA.md](DATA_SCHEMA.md).
   - Full `Theme` + `Epic` details: `issuetype in (Theme, Epic)` with fields `summary,status,priority,labels,components,issuetype` plus Jira's "Groups" custom field (look it up once via `jira_search_fields` with keyword `"group"` — id varies per instance, e.g. `customfield_22720`).
   - Full `Bug` details: `issuetype = Bug` with fields `summary,status,priority,labels,components`.

3. **Categorize Themes/Epics** into 4-7 short buckets by reading titles/descriptions/labels (e.g. "Security & Compliance", "Migration", "UX / Centralization", "Performance", "Networking"). This varies per release — use judgment, don't hardcode categories from a prior run. This is separate from the real Jira "Groups" field (step 2) — both are shown, don't conflate them.

4. **Write highlights**: 4-7 short, plain-English bullets summarizing the release for a non-technical cross-team reader — lead with impact/why, not ticket IDs.

5. **Assemble the JSON** matching [DATA_SCHEMA.md](DATA_SCHEMA.md) exactly, especially the normalized `statusCategory` (`done` | `in_progress` | `to_do`) on every theme/epic/bug. Write it to a temp file, e.g. `release_data.json`.

6. **Render**:
   ```bash
   python scripts/render_dashboard.py --data release_data.json
   ```
   This injects the JSON into `assets/template.html`, writes a timestamped output HTML file next to the data file, and opens it in the default browser. Pass `--out <path>` to control the filename, or `--no-open` to skip auto-opening.

7. Report the output file path to the user.

## Re-running for a status update

Same release identifier, same workflow — Jira totals/lists will simply reflect whatever has changed. Don't overwrite previous snapshots: the script timestamps filenames by default so the user can compare phases over time if they keep multiple runs.

## Additional resources

- Exact JSON shape and field semantics: [DATA_SCHEMA.md](DATA_SCHEMA.md)
- Dashboard markup/styling (edit only for structural bugs — preserve the aesthetic): [assets/template.html](assets/template.html)
