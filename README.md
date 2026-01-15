# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code) — Anthropic's official CLI for Claude.

## Available Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [skill-installer](skills/skill-installer) | Install skills from GitHub URLs | [Install](#skill-installer) |

## Installation

1. Clone or download the skill folder
2. Copy to `~/.claude/skills/` (global) or `.claude/skills/` (project)

```bash
git clone https://github.com/goodmartian/skills.git
cp -r skills/skills/SKILL_NAME ~/.claude/skills/
```

## Skills

### skill-installer

Install Claude Code skills directly from GitHub URLs.

**Features:**
- Supports repositories, folders, and `.skill` files
- Auto-detects skill structure (finds SKILL.md)
- Fallback from `main` to `master` branch

**Supported URL formats:**
```
github.com/user/repo
github.com/user/repo/tree/main/path/to/skill
github.com/user/repo/blob/main/skill.skill
raw.githubusercontent.com/user/repo/main/file.skill
```

**Install:**
```bash
cp -r skills/skill-installer ~/.claude/skills/
```

## Repository Structure

```
skills/
├── README.md
├── skills/
│   └── skill-installer/
│       ├── SKILL.md
│       └── scripts/
│           └── install_skill.py
└── ...
```

## License

MIT
