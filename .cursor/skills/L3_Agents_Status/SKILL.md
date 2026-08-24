---
name: L3_Agents_Status
description: >-
  Fetches all Jira Themes labeled "L3-Agents" in project IAI and generates a
  dated PPTX status presentation. Use this skill whenever the user asks to
  create, refresh, or update the L3-Agents status slide deck, wants a progress
  report on L3-Agents themes, or uses phrases like "generate the status",
  "update the slides", "L3 agents progress", "create the presentation", or
  "refresh the deck". The skill fetches live Jira data, resolves agent names,
  computes time-in-status from changelogs, derives a health indicator (On Track /
  At Risk / Off Track) based on ETA, status, time-in-status and PI timeline, and
  saves a date-stamped PPTX to the standard output folder. Always use this skill
  for L3-Agents status slide requests — even if the user just says "make the
  slides" in context of L3 agents work.
---

# L3-Agents Status Slide Generator

Produces a PPTX status deck for all Jira Themes labeled `L3-Agents` in project IAI.

## Output location
`C:\Users\yhalperin\Documents\L3_status_presentations\l3-agents-status-YYYY-MM-DD.pptx`

## Jira field reference
| Field | ID |
|---|---|
| Planned PI | `customfield_14422` |
| Parent Link (Master Feature / Agent) | `customfield_11140` |
| Finish Date (ETA) | `customfield_21221` |

## PI Timeline file
`C:\Users\yhalperin\source\pi-timeline-fy2027.json`

Contains `fiscalYears[].programIncrements[]` entries, each with `name` (e.g. `"27-Q1"`),
`start`, `end`, and `phases.execution.end`. Use `phases.execution.end` as the **PI deadline**
for health calculations.

---

## Step 1 — Fetch all L3-Agents themes

Use `jira_search` with:
- **JQL**: `project = IAI AND issuetype = Theme AND labels = "L3-Agents" ORDER BY key ASC`
- **fields**: `summary,description,status,customfield_14422,customfield_11140,customfield_21221,labels`
- **limit**: 50

Collect all returned issue keys (e.g. `["IAI-3982", "IAI-3985", ...]`).

---

## Step 2 — Resolve Agent names from parent issues

For each theme, read `customfield_11140.value` (the parent issue key):
- If the value is `IAI-3686` → agent = `"Not mapped yet"`, agentKey = `"IAI-3686"`
- Otherwise → use `jira_get_issue` to fetch that key's `summary`

Fetch all unique non-`IAI-3686` parent keys in parallel.

---

## Step 3 — Fetch changelogs for time in status

Call `jira_batch_get_changelogs` with all the IAI theme keys from Step 1.

For each issue, scan its changelog items for entries where `field == "status"` (or `fieldId == "status"`).
Find the **most recent** such entry and note its `created` timestamp.
Compute:

```
time_in_status_days = (today − created_date).days
```

If no status-change entry exists in the changelog (the issue was never transitioned),
use the issue's `created` date as the fallback. Cap the display at 999 days.

---

## Step 4 — Extract Business Value and Impact from description

Parse each theme's description looking for section markers (case-insensitive):
- **Goal / Business Value** → use as *Business Value*
- **Impact** → use as *Impact*
- **Value** section → first bullet/sentence = Business Value, second = Impact

If no structured sections: first meaningful sentence = Business Value, Impact = `"TBD"`.

Keep each to one line (≤ 15 words) — the slides are compact.

---

## Step 5 — Load PI timeline and get PI end dates

Read `C:\Users\yhalperin\source\pi-timeline-fy2027.json`.

For each theme, take the latest Planned PI (see Step 7 below for how to pick it),
then look it up in the timeline to get `phases.execution.end` as `pi_end`.

If the PI name is not found in the file, set `pi_end = null`.

---

## Step 6 — Compute health indicator

For each theme, evaluate these rules in priority order and return the **first match**:

| Priority | Condition | Health |
|---|---|---|
| 1 | `status == "Done"` | **On Track** |
| 2 | `finish_date < today` AND status ≠ Done | **Off Track** |
| 3 | `finish_date > pi_end` (ETA slips beyond PI deadline) | **Off Track** |
| 4 | `pi_end` is in the past AND status not in (Done, In Progress) | **Off Track** |
| 5 | `finish_date` within 14 days of `pi_end` AND status not in (Done, In Progress) | **At Risk** |
| 6 | `finish_date` is null AND status in (Open, Planned) AND `time_in_status_days > 21` | **At Risk** |
| 7 | `time_in_status_days > 42` AND status in (Open, Planned, HL Product Discovery) | **At Risk** |
| 8 | `time_in_status_days > 21` AND status in (Open, HL Product Discovery) | **At Risk** |
| 9 | `finish_date` is null AND status not in (Done, In Progress) | **At Risk** |
| 10 | _(none of the above)_ | **On Track** |

`today` = date this skill is run.

---

## Step 7 — Get latest Planned PI

From `customfield_14422.value` (an array like `["27-Q1", "26-Q2"]`):
- Parse each as `YY-Qn`
- Return the one with the highest `year * 10 + quarter` value
- If empty/missing → `"—"`

---

## Step 8 — Sort rows

Sort by status priority (then by Jira key ascending within each group):

1. Done  2. In Progress  3. HL Dev Discovery  4. HL Product Discovery  5. Planned  6. Open

---

## Step 9 — Build the data payload and run the PPTX script

Create a JSON file at `%TEMP%\l3_agents_data.json` with this structure:

```json
{
  "rows": [
    {
      "agent":               "Agent Name (PARENT-KEY)",
      "theme":               "Theme Summary\n(IAI-XXXX)",
      "business_value":      "One-line business value",
      "impact":              "One-line impact",
      "status":              "In Progress",
      "time_in_status_days": 14,
      "pi":                  "27-Q1",
      "finish_date":         "2026-10-15",
      "health":              "On Track"
    }
  ],
  "output_dir": "C:\\Users\\yhalperin\\Documents\\L3_status_presentations"
}
```

Field notes:
- `agent`: `"Name (KEY)"` for mapped; `"Not mapped yet"` for unmapped
- `theme`: summary on first line, `(IAI-XXXX)` on second line
- `finish_date`: ISO date string (`"YYYY-MM-DD"`) or `null`
- `time_in_status_days`: integer ≥ 0
- `health`: `"On Track"` | `"At Risk"` | `"Off Track"`
- `dev_phase` is NOT included in the payload (removed from slide to make room for Health)

Then run the bundled PPTX generator, replacing `<skill_dir>` with the directory of this SKILL.md:

```powershell
python "<skill_dir>\scripts\generate_pptx.py" --data "%TEMP%\l3_agents_data.json"
```

The script prints the full output path to stdout on success.

---

## Step 10 — Report to the user

Tell the user:
- Full path to the generated PPTX
- Number of slides and rows
- Summary of health: how many On Track / At Risk / Off Track
- Any themes with no finish date or missing PI
- Any Off Track themes (by name, so they're easy to spot)
