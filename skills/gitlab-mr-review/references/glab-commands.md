# glab Command Reference

Complete reference for GitLab CLI commands used in MR workflows.

## Inline Comments via API

glab CLI doesn't support inline comments natively. Use `glab api` to post comments to specific lines.

### Get project path and SHA refs

```bash
# URL-encoded project path
PROJECT=$(glab repo view --json fullPath -q .fullPath | sed 's/\//%2F/g')

# SHA values from MR
REFS=$(glab api "projects/$PROJECT/merge_requests/<id>" | jq -r '.diff_refs')
BASE_SHA=$(echo $REFS | jq -r '.base_sha')
HEAD_SHA=$(echo $REFS | jq -r '.head_sha')
START_SHA=$(echo $REFS | jq -r '.start_sha')
```

### Post inline comment

```bash
echo '{
  "body": "Your comment here",
  "position": {
    "position_type": "text",
    "base_sha": "'$BASE_SHA'",
    "head_sha": "'$HEAD_SHA'",
    "start_sha": "'$START_SHA'",
    "old_path": "src/file.py",
    "new_path": "src/file.py",
    "new_line": 42
  }
}' | glab api "projects/$PROJECT/merge_requests/<id>/discussions" \
  -X POST -H "Content-Type: application/json" --input -
```

### Position field rules

| Scenario | Fields needed |
|----------|---------------|
| Comment on added line (`+`) | `new_line` only |
| Comment on removed line (`-`) | `old_line` only |
| Comment on context line | Both `old_line` and `new_line` |
| File renamed | `old_path` differs from `new_path` |

### Line number calculation from diff

```diff
@@ -38,6 +42,8 @@
 context line      # old=38, new=42
+added line        # new=43 (next new line number)
-removed line      # old=39 (next old line number)
 context line      # old=39, new=44
```

### Batch comments helper

For multiple comments, loop through collected issues:

```bash
for comment in "${COMMENTS[@]}"; do
  FILE=$(echo $comment | cut -d: -f1)
  LINE=$(echo $comment | cut -d: -f2)
  MSG=$(echo $comment | cut -d: -f3-)

  echo "{\"body\":\"$MSG\",\"position\":{\"position_type\":\"text\",\"base_sha\":\"$BASE_SHA\",\"head_sha\":\"$HEAD_SHA\",\"start_sha\":\"$START_SHA\",\"old_path\":\"$FILE\",\"new_path\":\"$FILE\",\"new_line\":$LINE}}" | \
    glab api "projects/$PROJECT/merge_requests/$MR_ID/discussions" -X POST -H "Content-Type: application/json" --input -
done
```

## MR Commands

### List & View

| Command | Description |
|---------|-------------|
| `glab mr list` | List open MRs in current project |
| `glab mr list --state all` | List all MRs (open, merged, closed) |
| `glab mr list --author @me` | List your MRs |
| `glab mr list --reviewer @me` | List MRs where you're reviewer |
| `glab mr view <id>` | View MR details |
| `glab mr view <id> --web` | Open MR in browser |
| `glab mr diff <id>` | View MR diff |

### Create & Update

| Command | Description |
|---------|-------------|
| `glab mr create` | Create MR interactively |
| `glab mr create --fill` | Create with auto-filled title/description from commits |
| `glab mr create --title "T" --description "D"` | Create with title and description |
| `glab mr create -l "label1,label2"` | Create with labels |
| `glab mr create --assignee @user` | Create with assignee |
| `glab mr create --reviewer @user` | Create with reviewer |
| `glab mr create --draft` | Create as draft MR |
| `glab mr create --web` | Create and open in browser |
| `glab mr update <id> --title "New"` | Update title |
| `glab mr update <id> -l "label"` | Add label |
| `glab mr update <id> --unlabel "label"` | Remove label |
| `glab mr update <id> --assignee @user` | Set assignee |
| `glab mr update <id> --reviewer @user` | Set reviewer |
| `glab mr update <id> --draft` | Convert to draft |
| `glab mr update <id> --ready` | Mark ready for review |

### Review Actions

| Command | Description |
|---------|-------------|
| `glab mr approve <id>` | Approve MR |
| `glab mr revoke <id>` | Revoke approval |
| `glab mr note <id> -m "text"` | Add comment |
| `glab mr checkout <id>` | Checkout MR branch locally |

### Merge & Close

| Command | Description |
|---------|-------------|
| `glab mr merge <id>` | Merge MR |
| `glab mr merge <id> --squash` | Squash and merge |
| `glab mr merge <id> --remove-source-branch` | Merge and delete source branch |
| `glab mr merge <id> --when-pipeline-succeeds` | Merge when CI passes |
| `glab mr close <id>` | Close MR without merging |
| `glab mr reopen <id>` | Reopen closed MR |

## CI/CD Commands

| Command | Description |
|---------|-------------|
| `glab ci status` | Show current pipeline status |
| `glab ci list` | List recent pipelines |
| `glab ci view` | View current pipeline |
| `glab ci view <job_id>` | View specific job output |
| `glab ci trace` | Trace running job |
| `glab ci retry` | Retry failed jobs |
| `glab ci run` | Trigger new pipeline |
| `glab ci run -b <branch>` | Trigger pipeline on branch |

## Issue Commands

| Command | Description |
|---------|-------------|
| `glab issue list` | List issues |
| `glab issue view <id>` | View issue |
| `glab issue create` | Create issue |
| `glab issue close <id>` | Close issue |

## Repo Commands

| Command | Description |
|---------|-------------|
| `glab repo view` | View repo info |
| `glab repo clone <repo>` | Clone repository |
| `glab repo fork` | Fork repository |

## Auth & Config

| Command | Description |
|---------|-------------|
| `glab auth login` | Authenticate with GitLab |
| `glab auth status` | Check auth status |
| `glab config set` | Configure glab |

## Common Flags

| Flag | Description |
|------|-------------|
| `--repo owner/repo` | Specify repository |
| `-R owner/repo` | Short form of --repo |
| `--web` | Open in web browser |
| `-y` | Skip confirmation prompts |
| `--json` | Output as JSON |

## Output Formats

```bash
# JSON output for scripting
glab mr list --json id,title,author

# Specific fields
glab mr view <id> --json state,merge_status,pipeline
```

## Examples

### Full Review Workflow
```bash
# 1. View MR
glab mr view 123

# 2. Check diff
glab mr diff 123

# 3. Check CI
glab ci status

# 4. Checkout locally to test
glab mr checkout 123

# 5. Add comments
glab mr note 123 -m "src/api.py:42 - Consider input validation"

# 6. Approve or request changes
glab mr approve 123
# or
glab mr update 123 -l "Changes Requested"
```

### Quick MR Creation
```bash
# Create MR from current branch
glab mr create --fill --reviewer @teammate -l "Needs Review"
```

### Pipeline Management
```bash
# Check status and retry if failed
glab ci status
glab ci retry

# View failed job logs
glab ci view <failed_job_id>
```
