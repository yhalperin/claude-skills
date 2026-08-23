---
name: L3_Agents_Status
description: >-
  Fetches all Jira Themes labeled "L3-Agents" in project IAI and generates a
  dated PPTX status presentation. Use this skill whenever the user asks to
  create, refresh, or update the L3-Agents status slide deck, wants a progress
  report on L3-Agents themes, or uses phrases like "generate the status",
  "update the slides", "L3 agents progress", "create the presentation", or
  "refresh the deck". The skill fetches live Jira data, resolves agent names
  from parent Master Features (cf[11140]), extracts business value and impact
  from descriptions, sorts rows by status (Done → In Progress → Discovery →
  Planned → Open), and saves a date-stamped PPTX to the standard output folder.
  Always use this skill for L3-Agents status slide requests — even if the user
  just says "make the slides" in context of L3 agents work.
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

---

## Step 1 — Fetch all L3-Agents themes

Use the `jira_search` tool with:
- **JQL**: `project = IAI AND issuetype = Theme AND labels = "L3-Agents" ORDER BY key ASC`
- **fields**: `summary,description,status,customfield_14422,customfield_11140,labels`
- **limit**: 50

---

## Step 2 — Resolve Agent names from parent issues

For each theme, read `customfield_11140.value` (the parent issue key):
- If the value is `IAI-3686` → agent = `"Not mapped yet"`, agentKey = `"IAI-3686"`
- Otherwise → use `jira_get_issue` to fetch that key's `summary`

Fetch all unique non-`IAI-3686` parent keys in parallel to save time.

---

## Step 3 — Extract Business Value and Impact from description

Parse each theme's description looking for these section markers (case-insensitive):
- **Goal / Business Value** → use as the *Business Value* field
- **Impact** → use as the *Impact* field
- **Value** section → split into Business Value (first bullet/sentence) and Impact (second)

If no structured sections exist, use the first meaningful sentence as Business Value and leave Impact as `"TBD"`.

**Summarise to one line each** (≤ 15 words). The slides are compact — long text wraps badly.

Examples of good one-liners:
- Business Value: `"AI-driven permission recommendations & privilege tagging"`
- Impact: `"2× privileged entitlement coverage"`

---

## Step 4 — Determine Dev Phase

Use this heuristic based on Jira status:

| Jira Status | Dev Phase |
|---|---|
| Done | 6 |
| In Progress | 4 |
| HL Dev Discovery | 1 |
| HL Product Discovery | 1 |
| Planned | 2 |
| Open | 1 |

The 6 phases are:
1. Discovery & Research
2. Data Ingestion
3. MLOps & Algorithm
4. Embedded in Product
5. Conversational Layer
6. Test & Monitoring

---

## Step 5 — Get latest Planned PI

From `customfield_14422.value` (an array like `["27-Q1", "26-Q2"]`):
- Parse each as `YY-Qn` where YY = 2-digit year, n = quarter number
- Return the one with the highest `year * 10 + quarter` value
- If the array is empty or missing, use `"—"`

---

## Step 6 — Sort rows

Sort all themes by status in this priority order, then by Jira key ascending within each group:

1. Done
2. In Progress
3. HL Dev Discovery
4. HL Product Discovery
5. Planned
6. Open

---

## Step 7 — Build the data payload and run the PPTX script

Create a JSON file at a temporary path (e.g. `%TEMP%\l3_agents_data.json`) with this structure:

```json
{
  "rows": [
    {
      "agent": "Agent Name (PARENT-KEY)",
      "theme": "Theme Summary\n(IAI-XXXX)",
      "business_value": "One-line business value",
      "impact": "One-line impact",
      "status": "In Progress",
      "pi": "27-Q1",
      "dev_phase": 4
    }
  ],
  "output_dir": "C:\\Users\\yhalperin\\Documents\\L3_status_presentations"
}
```

For `agent`:
- Mapped: `"Agent Name (PARENT-KEY)"` — e.g. `"AI Permission Tagging (IGA-45610)"`
- Unmapped: `"Not mapped yet"`

For `theme`: always `"Theme summary\n(IAI-XXXX)"` — the Jira key on a second line.

Then run the bundled PPTX generator, replacing `<skill_dir>` with the directory containing this SKILL.md:

```powershell
python "<skill_dir>\scripts\generate_pptx.py" --data "%TEMP%\l3_agents_data.json"
```

The script prints the full output path on success.

---

## Step 8 — Report to the user

Tell the user:
- The full path to the generated file
- Number of slides and total rows
- How many themes are not yet mapped to a Master Feature
- Any warnings (e.g. themes with no description, missing PI)
