# Release Data JSON Schema

This is the JSON payload `scripts/render_dashboard.py` injects into the dashboard template. Build this object from Jira query results, write it to a file, then render.

```jsonc
{
  "release": {
    "name": "pCloud 15.0",                          // display title
    "jql": "fixVersion = \"pcloud 15.0\"",           // shown in the footer for traceability
    "generatedAt": "2026-07-09T13:45:00+03:00",      // ISO timestamp, shown in footer
    "phase": "Code Freeze"                            // optional free-text badge; omit key to hide
  },
  "totals": {
    "total": 401,
    "done": 315,
    "inProgress": 34,
    "toDo": 52
  },
  "byType": [
    { "type": "Story", "count": 289, "done": 240, "inProgress": 30, "toDo": 19 },
    { "type": "Task", "count": 25, "done": 20, "inProgress": 3, "toDo": 2 },
    { "type": "Theme", "count": 23, "done": 13, "inProgress": 8, "toDo": 2 },
    { "type": "Bug", "count": 22, "done": 18, "inProgress": 3, "toDo": 1 },
    { "type": "Epic", "count": 21, "done": 15, "inProgress": 5, "toDo": 1 }
  ],
  "highlights": [
    "FIPS 140-3 compliance rolled out across Vault, PVWA and CPM.",
    "AWS PrivateLink support shipped for PVWA."
  ],
  "themes": [
    {
      "key": "DVP-8077",
      "title": "FIPS 140-3 Vault Fix",
      "status": "Done",              // raw Jira status label, shown on the pill
      "statusCategory": "done",      // normalized: "done" | "in_progress" | "to_do" — drives color
      "category": "Security & Compliance",  // your own grouping bucket (see below) — drives the category cards
      "groups": ["EPV", "EPV pCloud"]  // raw values from Jira's "Groups" field on the issue — shown as the Group column
    }
  ],
  "epics": [
    { "key": "SHLD-28666", "title": "Support Privatelink in PVWA", "status": "Done", "statusCategory": "done", "category": "Private Networking", "groups": ["EPV pCloud"] }
  ],
  "bugs": [
    {
      "key": "PCPSM-6408",
      "title": "taskhostw.exe stack-buffer error on PSM 14.9 + Windows Server 2025",
      "component": "PSM",
      "priority": "High",            // Critical | High | Medium | Low | Undefined (any string works)
      "status": "Testing",
      "statusCategory": "in_progress"
    }
  ]
}
```

## Field notes

- **`statusCategory`** must be one of `done`, `in_progress`, `to_do` on every theme/epic/bug — it drives all pill/dot colors. Map Jira's `status.category` field: `Done` → `done`, `In Progress` → `in_progress`, anything else (`To Do`, `Open`, `Backlog`) → `to_do`. Jira states like `RollingOut`/`Archived` usually map to `done`.
- **`category`** (themes/epics only) is a short label you assign by reading the title/description/labels — e.g. "Security & Compliance", "Migration", "UX / Centralization", "Performance", "Networking". Aim for 4-7 buckets. Items with no obvious bucket go in `"Uncategorized"`. This drives the category cards' grouping/headers only.
- **`groups`** (themes/epics only) is the raw value(s) of Jira's own "Groups" field on the issue (a multiselect custom field, e.g. `customfield_22720` — confirm the field id per instance via `jira_search_fields` with keyword `"group"`). Pull it into the query's `fields` list and pass the array through as-is (e.g. `["EPV", "EPV pCloud"]`); omit or use `[]` if the field is empty. This is shown as its own "Group" column on each row — do **not** substitute `category` here, they are different things.
- **`byType`** should cover every issue type present in the release, not just the ones with detail sections. Each entry renders as a small status donut + counter, so provide the `done` / `inProgress` / `toDo` split per type (they should sum to `count`) — not just the raw total. Get these via three `statusCategory = ...` JQL queries scoped with `AND issuetype = "<Type>"` (cheap `limit:1` queries reading only `total`), same pattern as the overall `totals`. Just pass through every type you have data for — the template itself always: hides `Test Plan` and `Sub-task` entries, merges `Story` + `Task` into one "Story / Task" donut, and orders the visible donuts as Theme → Epic → Story / Task → Bug → Test Execution (any other types render after, sorted by count). Don't pre-filter, merge, or reorder `byType` yourself.
- **`highlights`** are 4-7 short, plain-English bullets for a non-technical reader — lead with impact, not ticket IDs.
- All arrays default to `[]` in the template if omitted, so partial data (e.g. no bugs yet in an early phase) renders fine.
