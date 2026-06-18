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

## How to Install a Skill

1. Copy the skill folder (e.g. `skills/pi-planning/`) into your Claude Code skills directory:
   - **Windows:** `C:\Users\<you>\.claude\skills\`
   - **Mac/Linux:** `~/.claude/skills/`
2. In Claude Code, invoke the skill with `/pi-planning` (or whatever the skill name is).
3. Claude will load the skill and act as a specialized assistant for that domain.

## Contributing

These skills are built from real workflows. If you adapt them for your team or have improvements, PRs are welcome.

## License

MIT
