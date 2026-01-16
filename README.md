# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/claude-code) — Anthropic's official CLI for Claude.

## Available Skills

| Skill | Description |
|-------|-------------|
| [skill-installer](skills/skill-installer) | Install skills from GitHub URLs |
| [gitlab-mr-review](skills/gitlab-mr-review) | GitLab MR management with inline code comments |

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

### gitlab-mr-review

GitLab Merge Request management using glab CLI with inline code comments support.

**Features:**
- **Inline Comments** — add comments to specific lines via GitLab API
- **Code Review Flow** — structured review with post-action prompts
- **MR Management** — create, update, merge MRs, manage labels
- **CI/CD Status** — check pipelines, view job logs

**Example prompts:**
- "Review MR 123"
- "Check merge request !456"
- "Create MR from current branch"
- "Show pipeline status"

**Requirements:**
- [glab](https://gitlab.com/gitlab-org/cli) CLI installed and authenticated
- `jq` for JSON parsing

## License

MIT
