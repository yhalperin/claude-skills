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
| [pi-planning](.cursor/skills/pi-planning/) | PI Planning facilitator for program managers and POs. Covers theme readiness assessment, sprint-based epic planning, grooming meeting agendas, and all four PI lifecycle phases — grounded in the PSDLC process. |
| [initiative-status-dashboard](.cursor/skills/initiative-status-dashboard/) | Traverses one or more Jira Initiatives (Initiative → Master Feature → leaf Feature) and renders them as a self-contained HTML dashboard with KPI cards, a Master-Feature milestone card grid with per-item Health badges, a Master-Feature × Planned-PI delivery schedule table with a multi-select Group filter, and an Automated Insights panel. |
| [pi-readiness-dashboard](.cursor/skills/pi-readiness-dashboard/) | Builds a self-contained "PI Readiness Command Center" HTML dashboard from live Jira Theme issues for a chosen Program Increment, with KPI cards, a status/division bar chart, a portfolio composition donut, a themes registry table, and an in-browser Division → Group drill-down filter. |
| [release-scope-dashboard](.cursor/skills/release-scope-dashboard/) | Extracts a release's scope and current status from Jira and renders it as a self-contained HTML dashboard with a completion gauge, per-type status donuts, Themes/Epics grouped into headline sections, and a filterable bug list. |

## Repo layout

Skills live directly under [`.cursor/skills/`](.cursor/skills/) at the repo root — the same path Cursor auto-discovers for **project-level** skills. That means:

- **Cloning/checking out this repo directly** (e.g. as the target repo for a Cursor Cloud Agent, or opening it as a Cursor project) makes every skill in this table available automatically — no copying required.
- **Claude Code**, or a **Cursor personal (user-level)** setup, don't read `.cursor/skills/` from an arbitrary repo — see "How to Install a Skill" below for those cases.

## How to Install a Skill

1. Copy the skill folder (e.g. `.cursor/skills/pi-planning/`) into your agent's skills directory:
   - **Claude Code — Windows:** `C:\Users\<you>\.claude\skills\`
   - **Claude Code — Mac/Linux:** `~/.claude/skills/`
   - **Cursor personal (user-level), any repo — Windows:** `C:\Users\<you>\.cursor\skills\`
   - **Cursor personal (user-level), any repo — Mac/Linux:** `~/.cursor/skills/`
   - **Cursor project-level, this repo's own agents/Cloud Agents:** already in place at `.cursor/skills/` — nothing to copy.
2. Invoke the skill with `/pi-planning` (or whatever the skill name is), or let the agent trigger it automatically based on its description.
3. The agent will load the skill and act as a specialized assistant for that domain.

> **Note:** Cursor Cloud Agents only ever see project-level skills (`.cursor/skills/` inside the repo they're operating on) — they have no access to a user's local `~/.cursor/skills/`. If you want a skill to be usable from a Slack-triggered or Automation-triggered Cloud Agent, the target repo needs its own `.cursor/skills/<skill-name>/` (either this repo directly, or copied into the project repo you're actually working in).

## Contributing

These skills are built from real workflows. If you adapt them for your team or have improvements, PRs are welcome.

## License

MIT
