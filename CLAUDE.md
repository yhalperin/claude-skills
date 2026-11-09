# Project Brief: Claude Skills Library

## What This Is
A repository of **Cursor / Claude Code skills** — Markdown-based instruction sets that turn Claude into
a specialized assistant for specific engineering and program management workflows. Skills are installed
once and invoked by name; they can include step-by-step process guidance, templates, checklists, and
Python render scripts.

## Skills Available

| Skill | Invoke with | What it does |
|---|---|---|
| `pi-planning` | `/pi-planning` | PI Planning facilitator: theme readiness, sprint-based epic planning, meeting agendas, all 4 PI lifecycle phases |
| `initiative-status-dashboard` | `/initiative-status-dashboard` | Traverses Jira Initiative → Master Feature → Feature hierarchy; renders a self-contained HTML dashboard with KPIs, health badges, and filters |
| `pi-readiness-dashboard` | `/pi-readiness-dashboard` | Builds a PI Readiness Command Center HTML dashboard from live Jira Theme issues |
| `release-scope-dashboard` | `/release-scope-dashboard` | Extracts release scope and current status from Jira; renders an HTML dashboard with completion gauge, per-type donuts, and bug list |

## Tech Stack
- Pure Markdown (`SKILL.md`) + Python render scripts
- No server, no build step, no dependencies to install in this repo

## How to Install a Skill

Skills live in `.cursor/skills/` at the repo root. Copy a skill folder to the right location:

```powershell
# Claude Code (Windows):
Copy-Item -Recurse .cursor\skills\pi-planning "$env:USERPROFILE\.claude\skills\pi-planning"

# Cursor personal/user-level (Windows):
Copy-Item -Recurse .cursor\skills\pi-planning "$env:USERPROFILE\.cursor\skills\pi-planning"
```

Then **start a new chat** and invoke with `/pi-planning` or by describing the task naturally.

> **Note for Cursor Cloud Agents:** Only project-level skills (`.cursor/skills/` inside the target repo)
> are visible. If you want a skill available in a Cloud Agent on a different repo, copy the skill folder
> into that repo's `.cursor/skills/`.

## Repo Layout
```
.cursor/
  skills/
    pi-planning/                  SKILL.md + supporting files
    initiative-status-dashboard/  SKILL.md + render scripts + data schema
    pi-readiness-dashboard/       SKILL.md + render scripts
    release-scope-dashboard/      SKILL.md + render scripts
  rules/
    initiative-status-dashboard.mdc   Cursor rule (project-level context)
```

## Integrations
- **Jira**: Skills use `user-policy-broker` MCP tools (`jira_search`, `jira_get_issue`) — Jira access
  is required at runtime (configured in Cursor/Claude Code MCP settings)
- **`initiative-status-slack-bot`** repo: uses the `initiative-status-dashboard` skill via Cursor SDK
  (`Agent.prompt()`) to respond to Slack `/initiative_status` commands

## Development Notes
- Each skill is self-contained; edit `SKILL.md` and test end-to-end in a fresh chat before committing
- Skills are **read-only** — they query Jira but never write to it
- Render scripts (Python) live alongside `SKILL.md` and are run by the agent via shell
- Remote: `https://github.com/yhalperin/claude-skills`
