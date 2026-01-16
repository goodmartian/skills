---
name: skill-installer
description: |
  Install Claude Code skills from GitHub URLs. Supports repositories, folders, and .skill files.
  Features smart updates (preserves personalized CONTEXT.md), batch installation, and update checking.

  Use when user provides a GitHub link to install a skill, mentions "install skill from GitHub",
  "add skill from URL", "download skill", or shares a link containing a skill they want to use.

  Triggers: (1) User shares GitHub URL with skill, (2) User asks to install/add/download a skill
  from a link, (3) User mentions "установить скилл" or "install skill" with a URL.
---

# Skill Installer

Install skills from GitHub URLs with automatic detection of skill structure.

## Features

- **Smart Updates**: Preserves personalized CONTEXT.md files during updates
- **Batch Installation**: Install multiple skills at once
- **Update Checking**: Verify if local skills need updates without installing
- **Branch Fallback**: Automatically tries `master` if `main` fails

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

## CLI Options

```
python scripts/install_skill.py [OPTIONS] <url> <destination>

Options:
  -b, --batch    Install multiple skills (comma-separated URLs)
  -c, --check    Only check if update needed, don't install
  -f, --force    Force overwrite without prompts
  -y, --yes      Non-interactive mode (assume yes to all prompts)
```

## Examples

### Basic Installation
```bash
python scripts/install_skill.py https://github.com/user/my-skill ~/.claude/skills/
```

### Install from Folder
```bash
python scripts/install_skill.py https://github.com/user/repo/tree/main/skills/pdf-editor ~/.claude/skills/
```

### Batch Installation
```bash
python scripts/install_skill.py --batch "https://github.com/user/skill1,https://github.com/user/skill2" ~/.claude/skills/
```

### Check for Updates
```bash
python scripts/install_skill.py --check https://github.com/user/my-skill ~/.claude/skills/
```

### Force Update (Non-Interactive)
```bash
python scripts/install_skill.py --force --yes https://github.com/user/my-skill ~/.claude/skills/
```

## Smart Update Behavior

When updating an existing skill:

1. **SKILL.md**: Compares content, asks before overwriting
2. **CONTEXT.md**:
   - If personalized → preserves your version, saves new template as `CONTEXT.md.new`
   - If still template → can be updated normally
3. **Other files**: Updated as normal

### Template Detection

CONTEXT.md is considered "template" (not personalized) if it contains markers like:
- `<!-- REPLACE` or `<!-- CUSTOMIZE`
- `REPLACE ME` or `REPLACE_ME`
- `your-value-here` or `YOUR_VALUE`
- `[your ` or `<your-`

## Error Handling

- If `main` branch fails → script tries `master` automatically
- If no SKILL.md found → warns user but still copies files
- If destination exists → performs smart update (see above)

---

## Fallback: Manual Installation (if Python unavailable)

If Python is not available, you can install skills manually using built-in agent tools:

### Step 1: Fetch SKILL.md
```
Use WebFetch to download:
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md
```

### Step 2: Create Directory
```bash
mkdir -p ~/.claude/skills/{skill-name}
```

### Step 3: Save Files
Use Write tool to save fetched content to:
- `~/.claude/skills/{skill-name}/SKILL.md`
- `~/.claude/skills/{skill-name}/CONTEXT.md` (if exists)

### Step 4: Fetch Additional Files
Check for and download:
- `scripts/` directory contents
- `templates/` directory contents
- Any other referenced files

### Step 5: Verify
```bash
ls -la ~/.claude/skills/{skill-name}/
cat ~/.claude/skills/{skill-name}/SKILL.md | head -20
```
