# Claude Skills

A collection of [Claude Code](https://claude.ai/code) skills built around real-world engineering and program management workflows. These skills help Claude give more structured, process-aware assistance — grounded in actual SDLC and PI Planning practices rather than generic advice.

## What is a Skill?

A **skill** is a Markdown file (`SKILL.md`) that you drop into Claude Code's skills directory. When you invoke it with `/skill-name`, Claude loads the instructions and becomes a specialized assistant for that domain. Skills can include:

- Step-by-step process guidance
- Templates and output formats
- Domain-specific checklists
- Evaluation test cases

## Skills in this Repo

| Skill | Description |
|-------|-------------|
| [pi-planning](skills/pi-planning/) | PI Planning facilitator for program managers and POs. Covers theme readiness assessment, sprint-based epic planning, grooming meeting agendas, and all four PI lifecycle phases — grounded in the PSDLC process. |
| [initiative-status-dashboard](skills/initiative-status-dashboard/) | Traverses one or more Jira Initiatives (Initiative → Master Feature → leaf Feature) and renders them as a self-contained HTML dashboard with KPI cards, a Master-Feature milestone table, a Jira-Group allocation swimlane matrix, and a manually-editable Risks panel. |
| [pi-readiness-dashboard](skills/pi-readiness-dashboard/) | Builds a self-contained "PI Readiness Command Center" HTML dashboard from live Jira Theme issues for a chosen Program Increment, with KPI cards, a status/division bar chart, a portfolio composition donut, a themes registry table, and an in-browser Division → Group drill-down filter. |
| [release-scope-dashboard](skills/release-scope-dashboard/) | Extracts a release's scope and current status from Jira and renders it as a self-contained HTML dashboard with a completion gauge, per-type status donuts, Themes/Epics grouped into headline sections, and a filterable bug list. |

## How to Install a Skill

1. Copy the skill folder (e.g. `skills/pi-planning/`) into your agent's skills directory:
   - **Claude Code — Windows:** `C:\Users\<you>\.claude\skills\`
   - **Claude Code — Mac/Linux:** `~/.claude/skills/`
   - **Cursor — Windows:** `C:\Users\<you>\.cursor\skills\`
   - **Cursor — Mac/Linux:** `~/.cursor/skills/`
2. Invoke the skill with `/pi-planning` (or whatever the skill name is), or let the agent trigger it automatically based on its description.
3. The agent will load the skill and act as a specialized assistant for that domain.

## Contributing

These skills are built from real workflows. If you adapt them for your team or have improvements, PRs are welcome.

## License

MIT
