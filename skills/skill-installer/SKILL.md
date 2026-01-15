---
name: skill-installer
description: |
  Install Claude Code skills from GitHub URLs. Supports repositories, folders, and .skill files.

  Use when user provides a GitHub link to install a skill, mentions "install skill from GitHub",
  "add skill from URL", "download skill", or shares a link containing a skill they want to use.

  Triggers: (1) User shares GitHub URL with skill, (2) User asks to install/add/download a skill
  from a link, (3) User mentions "установить скилл" or "install skill" with a URL.
---

# Skill Installer

Install skills from GitHub URLs with automatic detection of skill structure.

## Supported URL Formats

| Format | Example |
|--------|---------|
| Repository | `github.com/user/skill-repo` |
| Folder | `github.com/user/repo/tree/main/skills/my-skill` |
| File | `github.com/user/repo/blob/main/my-skill.skill` |
| Raw | `raw.githubusercontent.com/user/repo/main/skill.skill` |

## Installation Workflow

1. **Ask user for destination path** if not specified
2. **Run the installation script**:
   ```bash
   python scripts/install_skill.py <github_url> <destination_path>
   ```
3. **Verify installation** — check SKILL.md exists in installed folder

## Common Destinations

- Global skills: `~/.claude/skills/`
- Project skills: `./.claude/skills/`

## Example Usage

```bash
# Install from repository
python scripts/install_skill.py https://github.com/user/my-skill ~/.claude/skills/

# Install from folder in repo
python scripts/install_skill.py https://github.com/user/repo/tree/main/skills/pdf-editor ~/.claude/skills/

# Install .skill file
python scripts/install_skill.py https://github.com/user/repo/blob/main/cool.skill ~/.claude/skills/
```

## Error Handling

- If `main` branch fails → script tries `master` automatically
- If no SKILL.md found → warns user but still copies files
- If destination exists → overwrites with new version
