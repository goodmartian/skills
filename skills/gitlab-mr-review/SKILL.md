---
name: gitlab-mr-review
description: |
  GitLab Merge Request management using glab CLI with inline code comments support.
  Use when working with MRs:
  (1) Code review - view diff, analyze changes, add INLINE comments to specific lines
  (2) MR management - create, update, merge MRs, manage labels and assignees
  (3) CI/CD status - check pipeline status, view job logs
  (4) Discussions - work with threads, reply to comments, resolve discussions
  Triggers: "review MR", "check MR", "create MR", "merge", "pipeline status", "glab", "inline comment"
---

# GitLab MR Review

Work with GitLab Merge Requests using `glab` CLI. **Key feature: inline comments on specific code lines.**

## Quick Reference

```bash
glab mr list                    # List open MRs
glab mr view <id>               # View MR details
glab mr diff <id>               # View MR diff
glab mr approve <id>            # Approve MR
glab mr merge <id>              # Merge MR
glab ci status                  # Pipeline status
```

See `references/glab-commands.md` for full command reference.

## Inline Comments (Key Feature)

glab CLI doesn't support inline comments directly. Use `glab api` to add comments to specific lines.

**Comment rules:**
- Comments are posted from the user's GitLab account
- Write strict, factual comments without emojis
- Be direct and specific about the issue
- Do not post comments until user explicitly confirms the action

### Step 1: Get SHA refs from MR

```bash
# Get project path (URL-encoded)
PROJECT=$(glab repo view --json fullPath -q .fullPath | sed 's/\//%2F/g')

# Get SHA values
glab api "projects/$PROJECT/merge_requests/<mr_id>" | jq -r '.diff_refs | "base_sha=\(.base_sha)\nhead_sha=\(.head_sha)\nstart_sha=\(.start_sha)"'
```

### Step 2: Add inline comment

```bash
echo '{
  "body": "Comment text here",
  "position": {
    "position_type": "text",
    "base_sha": "<base_sha>",
    "head_sha": "<head_sha>",
    "start_sha": "<start_sha>",
    "old_path": "path/to/file.py",
    "new_path": "path/to/file.py",
    "new_line": 42
  }
}' | glab api "projects/$PROJECT/merge_requests/<mr_id>/discussions" -X POST -H "Content-Type: application/json" --input -
```

### Position rules

| Line type | Field to use | Example |
|-----------|--------------|---------|
| Added (`+`) | `new_line` | `"new_line": 42` |
| Removed (`-`) | `old_line` | `"old_line": 38` |
| Context (unchanged) | `new_line` + `old_line` | Both fields |

**Important:**
- JSON format is required (otherwise comment won't attach to line)
- Both `old_path` and `new_path` are required (same value for renamed files)
- Line numbers from diff hunk headers: `@@ -38,6 +42,8 @@`

### Determining line numbers from diff

```
@@ -38,6 +42,8 @@        <- old starts at 38, new starts at 42
 unchanged line           <- old=38, new=42
+added line               <- new=43 (use new_line)
-removed line             <- old=39 (use old_line)
 unchanged line           <- old=39, new=44
```

## Code Review Flow

1. **Get MR info**: `glab mr view <id>`
2. **Get diff**: `glab mr diff <id>` (or `> /tmp/mr_diff.txt` for large diffs)
3. **Analyze changes**: Identify issues with file:line references
4. **Collect comments**: Build list of inline comments internally (don't show to user)
5. **Show summary**: Brief review output
6. **Ask user action**: Use AskUserQuestion
7. **Execute action**: Add inline comments via API if requested

## Post-Review Actions

After review, ALWAYS ask user what action to take:

```json
{
  "questions": [{
    "question": "What action to take on this MR?",
    "header": "MR Action",
    "multiSelect": false,
    "options": [
      {"label": "Approve", "description": "Approve MR (glab mr approve)"},
      {"label": "Comment", "description": "Add inline comments to specific lines"},
      {"label": "Request changes", "description": "Inline comments + 'Changes Requested' label"},
      {"label": "Nothing", "description": "Show review results only"}
    ]
  }]
}
```

| Choice | Commands |
|--------|----------|
| Approve | `glab mr approve <id>` |
| Comment | Add inline comments via API (see above) |
| Request changes | Inline comments + `glab mr update <id> -l "Changes Requested"` |
| Nothing | No action |

## Labels

Standard review labels:
- `Needs Review` - awaiting review
- `Changes Requested` - requires fixes
- `Approved` - ready to merge

```bash
glab mr update <id> -l "Changes Requested"
glab mr update <id> --unlabel "Needs Review"
```

## Review Checklist

**Critical**
- No security vulnerabilities (injection, XSS, auth bypass)
- No breaking changes to public APIs
- Tests pass, coverage adequate
- No hardcoded secrets/credentials

**Important**
- Code follows project conventions
- Error handling present
- Documentation updated if needed

**Recommended**
- Clear naming and structure
- No code duplication

## Output Format

Keep it brief, no fluff:

```markdown
## Code Review: MR !<id>

**Title:** <title>
**Author:** @<username>

### Issues
1. `file.py:42` - SQL injection in query

### Recommendations
1. `utils.py:15` - Extract to separate function

**Verdict:** Approve / Request Changes
```

**Don't include:**
- "Positive notes" section
- Emojis
- Empty sections
- Generic phrases like "code is secure"

## MR Management

### Create MR
```bash
glab mr create --fill -l "Needs Review"
glab mr create --title "Feature X" --description "Details"
```

### Update MR
```bash
glab mr update <id> --title "New title"
glab mr update <id> -l "Priority::High"
glab mr update <id> --assignee @username
glab mr update <id> --reviewer @reviewer
```

### Merge
```bash
glab mr merge <id>
glab mr merge <id> --squash --remove-source-branch
```

## CI/CD

```bash
glab ci status              # Current pipeline status
glab ci list                # List pipelines
glab ci view <job_id>       # View job output
glab ci retry               # Retry failed pipeline
```

## Large MR Strategy

For diffs > 1500 lines:

1. **Save diff to file**: `glab mr diff <id> > /tmp/mr_diff.txt`
2. **Search patterns**: `grep -n "pattern" /tmp/mr_diff.txt`
3. **Analyze by file**: `glab mr diff <id> -- path/to/file.py`
4. **Prioritize by risk**: API endpoints > core logic > utilities > tests
