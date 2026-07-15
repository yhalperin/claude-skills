---
name: pi-readiness-dashboard
description: >-
  Builds a self-contained "PI Readiness Command Center" HTML dashboard from
  live Jira Theme issues: a PI Timeline band (Pre-Planning/Planning/
  Execution/Retrospective phase dates with today's phase highlighted), KPI
  cards incl. Net New Scope, a full-width AI insights band, a status/division
  bar chart, a portfolio composition donut, an Ownership Responsibility
  Matrix (Product Management vs R&D split on Net New scope) with its own
  donut, and a themes registry table - with in-browser Division -> Group
  cascading and Throughput Type drill-down filters, and every raw Jira
  status (e.g. Open, HL Product Discovery, In Progress) shown verbatim
  throughout in a status-accurate color scheme (e.g. In Progress = blue).
  Fetches Themes via the
  user-policy-broker MCP's jira_search tool for a chosen Program Increment
  (PI) and an optional Division scope (All Divisions or one specific
  division), maps PI status, HR Division/Group fields, and Throughput Type,
  and renders a static file that opens directly in a browser. Re-runnable at
  any point to refresh with current Jira state. Use when the user asks to
  generate, build, run, or refresh a PI Readiness dashboard/board, or wants a
  PI planning readiness snapshot for a specific PI and/or Division.
disable-model-invocation: true
---

# PI Readiness Dashboard

Produces one self-contained HTML file - no server, no build step - visualizing Jira Theme issues for a chosen Program Increment (PI). Layout, top to bottom: 5 KPI cards (Readiness Index, **Net New Scope**, Carry-Over, Ready/Planned, Not Ready), a full-width "AI & Strategic Insights" band, a status/division bar chart + portfolio composition donut, an **Ownership Responsibility Matrix** row (Product Management vs R&D counters + split donut, Net New Scope only), and a full-width themes registry table. Every status-related display (badges, chart legends, breakdown chips) shows the exact raw Jira status (e.g. `Open`, `HL Product Discovery`, `HL Dev Discovery`, `In Progress`) rather than a collapsed label, using a status-accurate color scheme: green = Ready, teal = Planned, **blue = In Progress**, slate = Open, amber = HL Product Discovery, violet = HL Dev Discovery. There is no "Quality Flags" KPI card - owner/flag risk is only surfaced in the table's Flags/Risk column and the AI insights band. The visual design is already built into `assets/template.html` - do not redesign it per run, only feed it fresh data.

**Net New Scope** = every Theme that is NOT `In Progress` (`totalCount - carryOverCount`); it's the actual new scope being planned for the PI, as opposed to committed carry-over. **Ownership Responsibility Matrix**: `assets/template.html`'s `OWNERSHIP_META` maps each raw status to whoever owns it right now - `Open`/`HL Product Discovery` -> Product Management, `Planned`/`Ready for Implementation`/`HL Dev Discovery`/`In Progress` -> R&D - and the Ownership Split donut + counters + AI insight are computed **only over Net New Scope** (excluding `In Progress`), per business rule (carry-over is already committed R&D execution, not a live ownership question).

The rendered dashboard also ships with a client-side, in-browser Division -> Group cascading filter (separate from the fetch-time `--division` scope below): a Division dropdown and a dependent Group dropdown driven by `assets/hr_tree.json`. Selecting a Division populates the Group dropdown with that Division's canonical HR groups (plus any live-only groups observed on its Jira data); selecting a Group further narrows the KPI cards, donut, table, and insights to that Group, while the bar chart keeps showing all sibling Groups (with the selected one highlighted) for context. This requires no data changes - it works against whatever Themes were embedded at render time.

A third in-browser dropdown filters by **Throughput Type** (`throughputType` in the schema). Unlike Division/Group (which drill into a fixed universe), this one rescopes the whole universe first - it defaults to **"A. Feature + Empty (Default)"** (business rule: only Feature work + unclassified Themes count toward PI readiness; Tech/Security/Support throughput is out of scope by default), and switching it also recomputes which Divisions/Groups even appear as options. Other selectable values are "All Types" and each distinct raw value observed in the data (e.g. `"B. Tech"`, `"C. Security"`, `"D. Support"`) plus "Empty / Unset only". The Reset button restores all three filters (Division, Group, Throughput Type) to their defaults.

At the very top of the board, above the KPI cards, is a compact **PI Timeline** strip (a single thin proportional bar + a row of small inline chips, deliberately lightweight so it doesn't dominate the screen): the target PI's Pre-Planning/Planning/Execution/Retrospective phase dates, a small dot "Today" marker on the bar, and one chip per phase - the current one is highlighted and shows a live "N days left" countdown to that phase's end date; others just show their date range (dimmed if upcoming, checked off if completed). This is driven entirely by [assets/pi_timeline.json](assets/pi_timeline.json) (a fiscal-year PI timeline export) - see "Timeline fetch" in the workflow below. If the target PI isn't found in that file, this section is simply hidden; it never blocks rendering.

The bar and the chip row are deliberately built to stay visually locked together: each phase keeps its own hue (violet/amber/blue/emerald for Pre-Planning/Planning/Execution/Retrospective) at every stage - full/pulsing when current, solid/muted when completed, faint outline when upcoming - so every phase boundary is a visible color change in the bar, not just a single "current vs. everything else" split. Each chip below is sized (flex-basis, with a min-width floor for very short phases so the label never clips) to match its segment's width % 1:1, and carries the same hue as a left accent border, so a chip always sits directly under - and is unmistakably the same color as - the segment it describes. A thin vertical "Today" guideline drops from the dot straight through the chip row so it's obvious which phase chip "today" falls under even at a glance.

## Jira instance constants (`ca-il-jira.il.cyber-ark.com`)

Known field IDs for this instance - re-derive via `jira_search_fields` only if a lookup below fails or the instance differs:

| Concept | Field | Notes |
|---|---|---|
| Divisions | `customfield_22721` | multi-select |
| Groups | `customfield_22720` | multi-select |
| Target PI | `customfield_14422` ("PlannedPI") | e.g. `"27-Q1"` |
| Flagged/Impediment | `customfield_10126` | non-empty value (e.g. contains `"Impediment"`) means flagged |
| Throughput Type | `customfield_13920` | single-select; observed values: `"A. Feature"`, `"B. Tech"`, `"C. Security"`, `"D. Support"` (plus unset) |
| Base URL | `https://ca-il-jira.il.cyber-ark.com:8443` | used for issue links |

## Status handling

The dashboard always shows the **exact, raw Jira status** on every theme - in badges, chart legends, and breakdown chips - never a collapsed label like `"Not Ready"` or `"Carry Over"`. Do not rename/merge statuses during the transform step (step 4 below); pass them through verbatim.

Internally, `assets/template.html`'s `STATUS_META` classifies each raw status into one of 4 categories used only for KPI math (readiness score, Carry-Over %, Not Ready %, Quality Flags scoping) - see the table in [DATA_SCHEMA.md](DATA_SCHEMA.md#status---category-mapping-status_meta-in-assetstemplatehtml). The known statuses for this instance/project are:

The **PI Readiness Index** itself is `(ready + planned) / (total - carryOver) * 100` - see [DATA_SCHEMA.md](DATA_SCHEMA.md#pi-readiness-index-formula) for the full rationale. Carry-Over is excluded from both sides of the ratio (already rolled over from a prior PI); Not Ready backlog stays in the denominator only, so it still dilutes the score.

| Raw Jira status | Category |
|---|---|
| `Ready for Implementation` | ready |
| `Planned` | planned |
| `In Progress` | carry-over |
| `Open`, `HL Dev Discovery`, `HL Product Discovery` | not ready |

If the user's Jira project surfaces other status names, ask which category (ready/planned/carry-over/not-ready) each belongs to before fetching, then add them to `STATUS_META` in `assets/template.html` (pick a distinct Tailwind color + chart hex) - don't guess, and don't just lump unknowns into an existing bucket's display label (they'll still render safely via the neutral fallback if left unmapped).

## Workflow

1. **Confirm scope.** Ask only what's genuinely ambiguous:
   - **Target PI** (the `customfield_14422` value, e.g. `"27-Q1"`). If unsure it's valid, check via `jira_get_field_options` for that field on a Theme issue/project before fetching.
   - **Division scope**: `"All"` (default) or one specific canonical division name. Canonical divisions are the keys of [assets/hr_tree.json](assets/hr_tree.json) - list them as options if asking.

2. **Build the JQL.**
   ```
   issuetype = Theme AND cf[22721] is not EMPTY AND cf[14422] = "<PI>"
   AND status in ("Ready for Implementation", "Planned", "In Progress",
                   "Open", "HL Dev Discovery", "HL Product Discovery")
   ORDER BY key
   ```
   If Division scope is not `"All"`, append: `AND cf[22721] = "<Division>"`.

3. **Fetch from Jira**, via the `user-policy-broker` MCP's `jira_search` (never bypass the broker):
   - Fields: `key,summary,status,assignee,customfield_22721,customfield_22720,customfield_10126,customfield_13920`.
   - **Paginate at `limit=25`** (`start_at` 0, 25, 50, ...) - larger limits (50/100) truncate tool output on this instance even with minimal fields.
   - After each page, immediately write the raw results to a simplified JSON file (`key,title,status,owner,divisions,groups,flagged,throughputType`) in a scratch build directory - don't hold everything in context, and this survives truncation/retries.
   - Decode HTML entities in title/divisions/groups (`&amp;` -> `&`) as you transform each page.
   - Stop when `start_at + max_results >= total`.

4. **Transform and assemble** into the schema in [DATA_SCHEMA.md](DATA_SCHEMA.md): `status` = the raw Jira status name, unchanged, `owner` = assignee display name or `null` if `"Unassigned"`, `flagged` = boolean from the impediment field, `throughputType` = the raw `customfield_13920` option value or `null` if unset, `url` = `<base_url>/browse/<key>`. Merge all pages into one JSON array file, e.g. `themes.json`. Verify count: `len(array) == total` reported by the first `jira_search` call, and no duplicate `id`s.

5. **HR tree.** Use the bundled [assets/hr_tree.json](assets/hr_tree.json) as-is (canonical Division -> Group hierarchy). Only regenerate it if the user provides a new HR org-chart export; otherwise never re-derive it per run. Divisions present in Jira but missing from this tree are handled automatically by the template (bucketed as "Other / Unmapped") - don't treat that as an error.

6. **PI Timeline (optional, for the head-of-board phase band).** Use the bundled [assets/pi_timeline.json](assets/pi_timeline.json) as-is - it's a fiscal-year PI timeline export (see [DATA_SCHEMA.md](DATA_SCHEMA.md#pi-timeline-schema-assetspi_timelinejson) for the shape) and `render_dashboard.py` automatically extracts whichever `programIncrement` matches `--pi`. Only replace this bundled file if the user supplies a newer export (e.g. a new fiscal year); if the target PI isn't in it, the timeline band is just hidden - not an error, don't block the run on it.

7. **Render.** Write the exact JQL from step 2 to a small text file first (e.g. `jql.txt`) and pass it via `--jql-file` - on Windows/PowerShell, passing the JQL directly via `--jql` is unreliable because the embedded double quotes get mangled by shell/CRT argument parsing.
   ```bash
   python scripts/render_dashboard.py --themes themes.json --pi "27-Q1" --division "All" --jql-file jql.txt
   ```
   Pass the exact `--division` value from step 1 (e.g. `"Secrets Manager"`) when scoped, matching a key in `hr_tree.json`. Add `--out <path>` to control the filename, or `--no-open` to skip auto-opening. This writes a stable filename derived from PI + division (e.g. `pi_readiness_27-q1_all.html`) next to the themes file. `--timeline` defaults to the bundled `assets/pi_timeline.json`; only pass it explicitly if using a different timeline export.

8. **Report a fetch summary**: PI, Division scope, total Themes fetched, per-raw-status counts, whether a PI Timeline was found/rendered (and today's highlighted phase), and the output path. Mention that Division, Group, and Throughput Type can all be further drilled into live in the browser (top-right dropdowns) without re-running anything - that filtering works against whatever Themes were embedded at render time. Also mention the dashboard defaults to "A. Feature + Empty" Throughput Type, so the KPI cards on first load are narrower than the total fetched count.

## Re-running for a refresh

Same PI/Division scope, repeat steps 2-7 with fresh data. Each combination of PI + Division produces a stable filename, so regenerating overwrites the same file rather than accumulating new ones - confirm with the user before reusing vs. producing a new dated copy. Only re-run to pull newer Jira data or change the fetch-time PI/Division scope - the in-browser Division/Group/Throughput Type filters, raw-status display, and PI Timeline (it's date-driven, not "now"-driven at render time, so it auto-highlights the correct phase whenever the file is opened) need no re-run.

## Additional resources

- Exact JSON shape and field semantics: [DATA_SCHEMA.md](DATA_SCHEMA.md)
- Dashboard markup/styling (edit only for structural bugs - preserve the design): [assets/template.html](assets/template.html)
- Canonical Division -> Group hierarchy: [assets/hr_tree.json](assets/hr_tree.json)
- Bundled PI timeline export (Pre-Planning/Planning/Execution/Retrospective dates per PI): [assets/pi_timeline.json](assets/pi_timeline.json)
- Example themes data file for reference: [examples/sample_themes.json](examples/sample_themes.json)
