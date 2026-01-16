# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code) — Anthropic's official CLI for Claude.

## Available Skills

| Skill | Description |
|-------|-------------|
| [skill-installer](skills/skill-installer) | Install skills from GitHub URLs |

## Quick Install

```bash
git clone https://github.com/goodmartian/skills.git
cp -r skills/skills/skill-installer ~/.claude/skills/
```

## Skills

### skill-installer

Install Claude Code skills directly from GitHub URLs.

**Features:**
- **Smart Updates** — preserves personalized CONTEXT.md during updates
- **Batch Installation** — install multiple skills at once
- **Update Checking** — verify if local skills need updates
- **Git Fallback** — uses sparse checkout if API fails

**Example prompts:**
- "Install skill from https://github.com/user/my-skill"
- "Установи скилл https://github.com/user/repo/tree/main/skills/cool-skill"
- "Add skill from this GitHub link"
- "Download and install https://github.com/user/skill-repo"

**Supported URL formats:**
```
github.com/user/repo
github.com/user/repo/tree/main/path/to/skill
github.com/user/repo/blob/main/skill.skill
raw.githubusercontent.com/user/repo/main/file.skill
```

## License

MIT
