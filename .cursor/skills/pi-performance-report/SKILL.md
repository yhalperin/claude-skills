---
name: pi-performance-report
description: >
  Generates a PI Performance Report for any Jira division or group. Fetches Theme issues
  across PIs, computes 6 key planning health indicators (velocity, carryover rate, cycle
  time, single-PI success rate, theme fit rate, throughput trend), and produces a
  self-contained HTML file with inline SVG charts, a velocity recommendation table, and
  a Theme Breakdown Quality analysis (Epic count per Theme).
  Use this skill whenever the user asks to: analyze PI performance, measure group or
  division velocity, calculate theme cycle time, understand multi-PI carryover, generate
  a planning or delivery report for a Jira division or group, assess scope quality of a
  PI, check Epic decomposition quality, or wants a performance dashboard they can email
  or share.
---

# PI Performance Report

## What this skill produces

A standalone HTML report at `<division-slug>-pi-performance-report.html` containing:

1. **6 Planning Health Indicator cards** (scorecard at the top)
2. **Global KPI strip** — total/done/in-progress/not-started + **Done breakdown by PI span** (1 PI / 2 PIs / 3+ PIs)
3. **PI-level charts** — status by PI (c1), done-themes PI-span breakdown per PI (c2), delivery pattern by PI (c3)
4. **Group charts** — status by group (c4), delivery state by group (c5) — groups come from `cf[22720]` (Groups field), **not** project keys
5. **PI Capacity vs. Recommended Velocity** — color-coded heatmap table comparing assigned themes vs. recommended velocity range per group per PI
6. **Cycle Time & Velocity section** — avg/median cycle time by group (c6), throughput per PI window (c7, FinishWork-date-based), velocity recommendation table
7. **Theme Breakdown Quality section** — Epic count per Theme via `cf[11140]` (Parent Link), with KPI boxes, per-theme tables, and a grouped bar chart (c8) showing distribution by group

---

## Step 1 — Gather inputs

Ask the user only for what they haven't already provided:

| Input | Default |
|-------|---------|
| Division name | (required) |
| PI scope | Last 4 PIs (e.g. `26-Q1,26-Q2,27-Q1,27-Q2`) |
| Output file | `C:\Users\yhalperin\Documents\PI_perfomance_reprot\<slug>-pi-performance-report.html` |

> Derive the `<slug>` from the division name: lowercase, spaces → hyphens, `&` → removed.
> "Privilege Cloud" → `privilege-cloud`. "Access & Risk" → `access-risk`.

---

## Step 2 — Build JQL

Read `references/jql-patterns.md` for known-division JQL patterns.

Generic pattern (use when no specific pattern exists):
```
PlannedPI in (<pi-list>) AND status != Archived AND issuetype = Theme
AND Divisions = "<Division Name>" AND NOT labels in (Bucket, bucket)
```

Always exclude bucket labels. Always include `issuetype = Theme` and `status != Archived`.

---

## Step 3 — Fetch Jira data (three passes)

**Pass A — all themes** (status counts, multi-PI counts, group assignment):
```
jira_search fields: summary,status,project,labels,customfield_14422,customfield_22721,customfield_23021,customfield_22720
limit: 50, paginate until start_at >= total
```

**Pass B — themes with StartWork** (cycle time, throughput):
```
same JQL + AND cf[12258] is not EMPTY
fields: summary,status,project,labels,customfield_12258,customfield_12259,customfield_14422,customfield_22721,customfield_23021,customfield_22720
limit: 50, paginate
```

**Pass C — Epic breakdown quality** (count Epics linked to each Theme):
```
issuetype = Epic AND cf[11140] in (<theme-key-list>) AND status != Archived
fields: summary,status,customfield_11140
limit: 50, paginate until all results fetched
```
> `cf[11140]` is the "Parent Link" field that points from an Epic to its parent Theme.
> Theme key list must be chunked — Jira JQL has a limit; batch in groups of 50 theme keys.

Custom field IDs:
| Field | ID |
|-------|----|
| StartWork | `customfield_12258` |
| FinishWork | `customfield_12259` |
| PlannedPI | `customfield_14422` (array) |
| Divisions | `customfield_22721` |
| Participating Products | `customfield_23021` |
| **Groups** | **`customfield_22720`** (use this — not project.key — for group breakdown) |
| **Parent Link (Epic→Theme)** | **`customfield_11140`** |

---

## Step 4 — Compute metrics in PowerShell

Read `references/metric-formulas.md` for the exact PowerShell script.

### PI window boundaries

Load from `C:\Users\yhalperin\source\pi-timeline-fy2027.json` for official window dates.
Also apply these user-confirmed overrides for fiscal year 2026:

```
26-Q1: ends 2026-04-11  (user-confirmed)
26-Q2: ends 2026-08-01  (user-confirmed)
27-Q1: use pi-timeline-fy2027.json
27-Q2: use pi-timeline-fy2027.json
```

Throughput (c7) maps each Done theme's `FinishWork` date to a PI window — **not** the PlannedPI field value.

### The 6 planning health indicators

| # | Metric | Formula | 🟢 | 🟡 | 🔴 |
|---|--------|---------|----|----|-----|
| 1 | Division Velocity | avg(done per PI window) | trending ↑ | flat | declining |
| 2 | Throughput Trend | done: PI-3 → PI-2 → PI-1 | +% growth | flat | negative |
| 3 | Avg Cycle Time | avg(FinishWork − StartWork) for Done | < 70d | 70–100d | > 100d |
| 4 | Carryover Rate | themes with PICount > 1 / total | < 30% | 30–50% | > 50% |
| 5 | Single-PI Success | Done themes with PICount = 1 / Done total | > 60% | 40–60% | < 40% |
| 6 | Theme Fit Rate | Done themes with cycle ≤ 91d / Done with cycle | > 70% | 50–70% | < 50% |

### Per-group velocity recommendation
```
Recommendation = avg(completed PIs throughput per group) ± 20%
```
Groups come from `customfield_22720`. Take the first value if the field is an array.
For Privilege Cloud, the observed groups are: **EPV pCloud**, **pCloud**, **DV**.

### Theme Breakdown Quality categories

| Category | Epic count | Signal |
|----------|-----------|--------|
| No Epics | 0 | Theme not broken down at all |
| Monolithic | 1 | Theme not meaningfully decomposed |
| Healthy | 2–7 | Good decomposition |
| Over-fragmented | > 7 | Possibly broken into pieces too small |

---

## Step 5 — Generate the HTML

Read `references/html-generation.md` for the full CSS and JavaScript chart code.

### Critical: SVG chart rendering

**Always use `document.createElementNS`** — never `innerHTML` for SVG.
Using `innerHTML` with SVG string-building breaks because void SVG elements
(`<line>`, `<circle>`, `<rect>`, `<path>`) need self-closing tags; `createElementNS` avoids this entirely.

```javascript
var NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs) {
  var e = document.createElementNS(NS, tag);
  for (var k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}
function txt(tag, attrs, content) {
  var e = el(tag, attrs);
  e.textContent = String(content);
  return e;
}
```

Also: **never name a local variable `el`** — it shadows the helper above. Use `container` instead.
Also: **always use `<div id="cN">` for chart containers** — never `<canvas>`.

### Chart functions provided (see `references/html-generation.md`)
- `stackedBar(id, cats, series, opts)` — stacked bars, bottom-to-top
- `lineChart(id, cats, series, opts)` — line + area fill + dots
- `groupedBar(id, cats, series, opts)` — side-by-side bars, supports `opts.refLine`

### HTML section order
1. `<head>` with full inline CSS (include `.badge`, `.kpi-row`, `.kpi-num`, `.kpi-lbl`, `.score-*` styles)
2. `<h1>` + meta line
3. **Scorecard** (`.scorecard` grid, 6 × `.sc-card`)
4. `<h2>Global Summary</h2>` + `.kpi-grid` (Total / Done / InProgress / NotStarted)
5. **Done themes breakdown row** — 3 KPI boxes: "Completed in 1 PI", "Took 2 PIs", "Took 3+ PIs" with count and % each
6. **PI charts section**:
   - **c1** — Status by PI (stacked bar: Done / In Progress / Not Started)
   - **c2** — Done themes by PI span per PI (stacked bar: 1 PI / 2 PIs / 3+ PIs)
   - **c3** — Themes per PI — Delivery State (4-way split: Done–1PI / Done–MultiPI / In Progress / Not Started)
7. **Group Breakdown section** (header: "Group Breakdown"):
   - **c4** — Status by Group (stacked bar)
   - **c5** — Delivery State by Group (4-way stacked bar)
   - Status Detail table (columns: Group / Done–1PI / Done–MultiPI / In Progress / Not Started)
8. **PI Capacity vs. Recommended Velocity** — color-coded heatmap table + insights block
9. **Cycle Time & Velocity section**:
   - **c6** — Avg/Median cycle time by group (grouped bar)
   - **c7** — Throughput: Themes Completed per PI Window (stacked bar, FinishWork-date-mapped, active PI labeled)
   - Velocity recommendation table (columns: Group / Done Themes Measured / Avg Cycle / Median Cycle / Historic Throughput / Recommended Velocity badge)
10. **Theme Breakdown Quality section**:
    - KPI boxes: No Epics / Monolithic (1 Epic) / Healthy (2–7) / Over-fragmented (>7)
    - Table of Over-fragmented themes (Theme Key / Group / Epic Count)
    - Table of Monolithic themes (Theme Key / Group)
    - **c8** — Epic count distribution by group (`groupedBar`)
    - Insights block
11. `<script>` block at end of `<body>` (all chart calls inside `(function(){...})()`

> **Do NOT include a "Completion Rate Trend" line chart** — it is confusing and has been removed.
> **Do NOT include P90 Cycle** in the velocity table — only Avg Cycle and Median Cycle.
> Always label "Done Themes Measured" (not just "Themes Measured") in the velocity table.

---

## Step 6 — Open the file

```powershell
New-Item -ItemType Directory -Force "C:\Users\yhalperin\Documents\PI_perfomance_reprot" | Out-Null
Invoke-Item "<output-path>"
```

---

## Output file path

**Directory:** `C:\Users\yhalperin\Documents\PI_perfomance_reprot\`
**File name:** `<division-slug>-pi-performance-report.html`

Examples:
- "Privilege Cloud" → `C:\Users\yhalperin\Documents\PI_perfomance_reprot\privilege-cloud-pi-performance-report.html`
- "Access & Risk"   → `C:\Users\yhalperin\Documents\PI_perfomance_reprot\access-risk-pi-performance-report.html`

---

## Data quality rules

- Exclude negative cycle times (FinishWork < StartWork) — they are data errors.
- Themes without StartWork: include in status/carryover counts, exclude from cycle time.
- Themes without FinishWork but status = Done: count in Done totals; exclude from throughput (c7).
- Active PI throughput is partial — label affected bars "(active)".
- Deduplicate themes by key before processing (paginated Jira results can overlap).
- Group field (`customfield_22720`) may be an array — take the first non-null value as the primary group.

---

## Working reference report

A working report generated for Privilege Cloud is at:
`C:\Users\yhalperin\Documents\PI_perfomance_reprot\privilege-cloud-pi-performance-report.html`

Use it as a style and structure reference. Do not overwrite it unless the user is regenerating Privilege Cloud.
