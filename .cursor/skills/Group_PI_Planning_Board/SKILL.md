---
name: Group_PI_Planning_Board
description: >
  Launches the Group PI Program Board planning application for a specific Group/ART and Planned PI.
  Fetches live Epic and Theme data from Jira via MCP, writes it to the app's data file, starts
  the Vite dev server, and opens the board in the browser.
  Use when the user says "start PI board", "launch planning board", "open PI board",
  "start the group board", "launch group PI planner", or anything that sounds like starting
  the PI program board for a group or ART.
---

# Group PI Planning Board — Launch Skill

## Jira field IDs

```
Planned PI:   cf[14422]  →  customfield_14422
Groups:       cf[22720]  →  customfield_22720
Team:         cf[10090]  →  customfield_10090
Start Sprint: cf[21222]  →  customfield_21222
Finish Sprint:cf[21223]  →  customfield_21223
```

## App location

```
C:\Users\yhalperin\source\group-pi-board\
```

Dev server port: **5181**
Data file: `C:\Users\yhalperin\source\group-pi-board\public\pi-data.json`

## Steps

### 1. Extract PI and Group from the user's message

Parse the user's message for:
- **PI**: e.g. "27-Q1", "Q1", "Q2", "27-Q2" → normalise to "27-Q1" format
- **Group**: e.g. "Commerce ART", "Platform ART", "Data ART"

If either is missing, ask the user for the missing value before proceeding.

### 2. Fetch Jira data via MCP

Call `jira_search` using the `user-policy-broker` MCP with:

```
JQL: issuetype in (Theme, Epic)
     AND cf[14422] = "{PI}"
     AND cf[22720] = "{Group}"
ORDER BY issuetype DESC, key ASC

fields: key, summary, issuetype, status, parent, subtasks,
        customfield_14422, customfield_22720, customfield_10090,
        customfield_21222, customfield_21223

maxResults: 200
```

### 3. Transform and write pi-data.json

Transform the MCP response into the schema below and write it to:
`C:\Users\yhalperin\source\group-pi-board\public\pi-data.json`

**Schema:**
```json
{
  "pi": "27-Q1",
  "group": "Commerce ART",
  "fetchedAt": "<ISO timestamp>",
  "themes": [
    { "key": "THEME-001", "name": "Theme Name", "color": "#8b5cf6" }
  ],
  "teams": [
    { "id": "team-id", "name": "Team Name" }
  ],
  "epics": [
    {
      "key": "JAG-1234",
      "summary": "Epic summary",
      "status": "In Progress",
      "teamId": "team-id",
      "themeKey": "THEME-001",
      "startSprintId": "Q1S1",
      "finishSprintId": "Q1S4",
      "issueCount": 8,
      "originalStartSprintId": "Q1S1",
      "originalFinishSprintId": "Q1S4"
    }
  ]
}
```

**Transformation rules:**
- Themes: issues where `issuetype.name === "Theme"`. Assign colors in order:
  `["#8b5cf6", "#10b981", "#f59e0b", "#06b6d4", "#ec4899", "#f97316"]`
- Epics: issues where `issuetype.name === "Epic"`
- `teamId`: use `customfield_10090.id` or `customfield_10090.value` or slugify the name
- `themeKey`: use `fields.parent.key` (the parent Theme's key)
- `startSprintId`: map `customfield_21222` (sprint name like "27-Q1 Sprint 2") to ID "Q1S2".
  Sprint name → ID mapping:
  - "27-Q1 Sprint N" → "Q1SN", "27-Q1 IP" → "Q1S7"
  - "27-Q2 Sprint N" → "Q2SN", "27-Q2 IP" → "Q2S6"
  - "27-Q3 Sprint N" → "Q3SN", "27-Q3 IP" → "Q3S6"
  - "27-Q4 Sprint N" → "Q4SN", "27-Q4 IP" → "Q4S7"
- `issueCount`: `fields.subtasks.length`
- `originalStartSprintId` = same as `startSprintId` (baseline for change tracking)
- `originalFinishSprintId` = same as `finishSprintId`

### 4. Start the dev server (if not already running)

Check if port 5181 is in use:
```powershell
netstat -ano | findstr ":5181 " | findstr "LISTENING"
```

If NOT listening: start the server in background:
```powershell
cd "C:\Users\yhalperin\source\group-pi-board"
npm run dev
```
Wait ~8 seconds for `Local: http://localhost:5181` to appear in output.

If already listening: skip this step.

### 5. Open the board in the browser

Open:
```
http://localhost:5181?pi={PI}&group={URL-encoded Group}
```
Example: `http://localhost:5181?pi=27-Q1&group=Commerce+ART`

Use the `browser_navigate` tool or instruct the user to open the URL.

### 6. Report status

Summarise:
```
Group PI Planning Board is ready.

Group:        Commerce ART
PI:           27-Q1
Themes:       4 found
Epics:        13 fetched from Jira
URL:          http://localhost:5181?pi=27-Q1&group=Commerce+ART
Data source:  Live Jira (fetched at <timestamp>)
```
