# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code) — Anthropic's official CLI for Claude.

## Available Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [skill-installer](skills/skill-installer) | Install skills from GitHub URLs | [Install](#skill-installer) |

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
- **Branch Fallback** — automatically tries `master` if `main` fails

**Supported URL formats:**
```
github.com/user/repo
github.com/user/repo/tree/main/path/to/skill
github.com/user/repo/blob/main/skill.skill
raw.githubusercontent.com/user/repo/main/file.skill
```

**CLI Options:**
```
python install_skill.py [OPTIONS] <url> <destination>

Options:
  -b, --batch    Install multiple skills (comma-separated URLs)
  -c, --check    Only check if update needed, don't install
  -f, --force    Force overwrite without prompts
  -y, --yes      Non-interactive mode (assume yes)
```

**Examples:**
```bash
# Basic installation
python install_skill.py https://github.com/user/my-skill ~/.claude/skills/

# Batch installation
python install_skill.py --batch "url1,url2,url3" ~/.claude/skills/

# Check for updates
python install_skill.py --check https://github.com/user/my-skill ~/.claude/skills/

# Force update (CI/CD friendly)
python install_skill.py --force --yes https://github.com/user/my-skill ~/.claude/skills/
```

**Install:**
```bash
cp -r skills/skill-installer ~/.claude/skills/
```

## Repository Structure

```
skills/
├── README.md
└── skills/
    └── skill-installer/
        ├── SKILL.md
        └── scripts/
            └── install_skill.py
```

## License

MIT
