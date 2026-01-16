#!/usr/bin/env python3
"""
Skill Installer - Install Claude Code skills from GitHub URLs.

Supports:
- GitHub repositories: github.com/user/repo
- GitHub folders: github.com/user/repo/tree/branch/path/to/skill
- GitHub files: github.com/user/repo/blob/branch/skill.skill
- Raw URLs: raw.githubusercontent.com/...
- Direct .skill file URLs

Features:
- Smart updates: preserves personalized CONTEXT.md files
- Batch installation: install multiple skills at once
- Update checking: verify if local skills need updates

Usage:
    python install_skill.py <github_url> <destination_path>
    python install_skill.py --batch "url1,url2" <destination_path>
    python install_skill.py --check <github_url> <destination_path>
"""

import sys
import os
import re
import json
import shutil
import tempfile
import zipfile
import argparse
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, Dict, List


# Template markers indicating CONTEXT.md hasn't been personalized
TEMPLATE_MARKERS = [
    '<!-- REPLACE',
    '<!-- CUSTOMIZE',
    '<!-- TODO',
    'REPLACE ME',
    'REPLACE_ME',
    'your-value-here',
    'YOUR_VALUE',
    '[your ',
    '<your-',
]


def is_context_personalized(content: str) -> bool:
    """
    Check if CONTEXT.md has been personalized by the user.

    Returns True if the content appears to be customized (no template markers found).
    Returns False if it still contains template placeholders.
    """
    content_lower = content.lower()
    for marker in TEMPLATE_MARKERS:
        if marker.lower() in content_lower:
            return False
    return True


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compare_files(file1: Path, file2: Path) -> bool:
    """Compare two files by content. Returns True if identical."""
    if not file1.exists() or not file2.exists():
        return False
    return compute_file_hash(file1) == compute_file_hash(file2)


def check_existing_skill(existing_path: Path, new_path: Path) -> Dict[str, str]:
    """
    Check existing skill installation and determine update strategy.

    Returns dict with:
        'skill_md': 'same' | 'different' | 'missing'
        'context_md': 'personalized' | 'template' | 'missing' | 'same'
        'strategy': 'skip' | 'update' | 'merge'
    """
    result = {
        'skill_md': 'missing',
        'context_md': 'missing',
        'strategy': 'update'
    }

    existing_skill_md = existing_path / 'SKILL.md'
    new_skill_md = new_path / 'SKILL.md'

    # Check SKILL.md
    if existing_skill_md.exists():
        if new_skill_md.exists() and compare_files(existing_skill_md, new_skill_md):
            result['skill_md'] = 'same'
        else:
            result['skill_md'] = 'different'

    # Check CONTEXT.md
    existing_context = existing_path / 'CONTEXT.md'
    new_context = new_path / 'CONTEXT.md'

    if existing_context.exists():
        content = existing_context.read_text(encoding='utf-8')
        if is_context_personalized(content):
            result['context_md'] = 'personalized'
            result['strategy'] = 'merge'  # Need to preserve user's CONTEXT.md
        else:
            if new_context.exists() and compare_files(existing_context, new_context):
                result['context_md'] = 'same'
            else:
                result['context_md'] = 'template'

    # Determine overall strategy
    if result['skill_md'] == 'same' and result['context_md'] in ('same', 'missing'):
        result['strategy'] = 'skip'

    return result


def parse_github_url(url: str) -> Tuple[str, dict]:
    """
    Parse GitHub URL and return type and components.

    Returns:
        Tuple of (url_type, components)
        url_type: 'repo', 'folder', 'file', 'raw', 'direct'
    """
    url = url.strip().rstrip('/')

    # Handle github.com without https://
    if url.startswith('github.com'):
        url = 'https://' + url

    # Raw GitHub URL
    if 'raw.githubusercontent.com' in url:
        return 'raw', {'url': url}

    # Direct .skill file URL
    if url.endswith('.skill') and 'github.com' not in url:
        return 'direct', {'url': url}

    # GitHub blob (file)
    blob_match = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)',
        url
    )
    if blob_match:
        owner, repo, branch, path = blob_match.groups()
        return 'file', {
            'owner': owner,
            'repo': repo,
            'branch': branch,
            'path': path
        }

    # GitHub tree (folder)
    tree_match = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)',
        url
    )
    if tree_match:
        owner, repo, branch, path = tree_match.groups()
        return 'folder', {
            'owner': owner,
            'repo': repo,
            'branch': branch,
            'path': path
        }

    # GitHub repository (with or without branch)
    repo_match = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?/?$',
        url
    )
    if repo_match:
        owner, repo, branch = repo_match.groups()
        return 'repo', {
            'owner': owner,
            'repo': repo,
            'branch': branch or 'main'
        }

    # Simple github.com/user/repo format
    simple_match = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)/?$',
        url
    )
    if simple_match:
        owner, repo = simple_match.groups()
        return 'repo', {
            'owner': owner,
            'repo': repo.replace('.git', ''),
            'branch': 'main'
        }

    raise ValueError(f"Unsupported URL format: {url}")


def download_file(url: str, dest_path: Path) -> None:
    """Download file from URL to destination."""
    print(f"  Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try 'master' branch if 'main' fails
            if '/main/' in url:
                alt_url = url.replace('/main/', '/master/')
                print(f"  Trying alternate branch: {alt_url}")
                urllib.request.urlretrieve(alt_url, dest_path)
            else:
                raise
        else:
            raise


def fetch_github_api(endpoint: str) -> dict:
    """Fetch data from GitHub API."""
    api_url = f"https://api.github.com/{endpoint}"
    req = urllib.request.Request(
        api_url,
        headers={'Accept': 'application/vnd.github.v3+json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def download_github_folder(owner: str, repo: str, branch: str,
                           path: str, dest_dir: Path) -> None:
    """Download a folder from GitHub repository."""
    print(f"  Fetching folder contents: {path}")

    try:
        contents = fetch_github_api(
            f"repos/{owner}/{repo}/contents/{path}?ref={branch}"
        )
    except urllib.error.HTTPError:
        # Try master branch
        contents = fetch_github_api(
            f"repos/{owner}/{repo}/contents/{path}?ref=master"
        )

    for item in contents:
        item_path = dest_dir / item['name']

        if item['type'] == 'file':
            download_file(item['download_url'], item_path)
        elif item['type'] == 'dir':
            item_path.mkdir(parents=True, exist_ok=True)
            download_github_folder(
                owner, repo, branch,
                f"{path}/{item['name']}", item_path
            )


def download_github_repo(owner: str, repo: str, branch: str,
                         dest_dir: Path) -> Path:
    """Download entire GitHub repository as zip."""
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        download_file(zip_url, tmp_path)

        # Extract zip
        with zipfile.ZipFile(tmp_path, 'r') as zf:
            zf.extractall(dest_dir)

        # Find extracted folder (usually repo-branch)
        extracted = list(dest_dir.iterdir())
        if len(extracted) == 1 and extracted[0].is_dir():
            return extracted[0]
        return dest_dir

    finally:
        tmp_path.unlink(missing_ok=True)


def install_skill_file(skill_file: Path, dest_dir: Path) -> Path:
    """Install .skill file (zip archive) to destination."""
    print(f"  Installing skill from: {skill_file}")

    # .skill files are zip archives
    with zipfile.ZipFile(skill_file, 'r') as zf:
        # Get skill name from archive
        names = zf.namelist()
        if names:
            skill_name = names[0].split('/')[0]
        else:
            skill_name = skill_file.stem

        skill_dest = dest_dir / skill_name
        skill_dest.mkdir(parents=True, exist_ok=True)

        zf.extractall(dest_dir)

    return skill_dest


def find_skill_in_folder(folder: Path) -> Optional[Path]:
    """Find SKILL.md in folder to determine skill root."""
    # Check current folder
    if (folder / 'SKILL.md').exists():
        return folder

    # Check immediate subfolders
    for item in folder.iterdir():
        if item.is_dir() and (item / 'SKILL.md').exists():
            return item

    return None


def perform_smart_update(existing_path: Path, new_path: Path,
                         force: bool = False, interactive: bool = True) -> bool:
    """
    Perform smart update of existing skill.

    Returns True if update was performed, False if skipped.
    """
    status = check_existing_skill(existing_path, new_path)

    print(f"  Existing skill found at: {existing_path}")
    print(f"    SKILL.md: {status['skill_md']}")
    print(f"    CONTEXT.md: {status['context_md']}")

    if status['strategy'] == 'skip' and not force:
        print("  ⏭️  Already up to date, skipping")
        return False

    # Handle personalized CONTEXT.md
    if status['context_md'] == 'personalized':
        new_context = new_path / 'CONTEXT.md'
        if new_context.exists():
            # Save new version as .new for user to review
            context_new = existing_path / 'CONTEXT.md.new'
            shutil.copy2(new_context, context_new)
            print(f"  📝 New CONTEXT.md template saved as: {context_new.name}")
            print("     Your personalized CONTEXT.md will be preserved")

    if not force and interactive:
        if status['skill_md'] == 'different':
            response = input("  Update SKILL.md? [Y/n]: ").strip().lower()
            if response == 'n':
                print("  Skipping SKILL.md update")
                return False

    # Perform update - preserve personalized CONTEXT.md
    backup_context = None
    if status['context_md'] == 'personalized':
        backup_context = existing_path / 'CONTEXT.md'
        backup_content = backup_context.read_text(encoding='utf-8')

    # Update files (except personalized CONTEXT.md)
    for item in new_path.iterdir():
        dest_item = existing_path / item.name

        # Skip CONTEXT.md if personalized
        if item.name == 'CONTEXT.md' and status['context_md'] == 'personalized':
            continue

        if item.is_dir():
            if dest_item.exists():
                shutil.rmtree(dest_item)
            shutil.copytree(item, dest_item)
        else:
            shutil.copy2(item, dest_item)

    return True


def install_skill(url: str, dest_path: str,
                  force: bool = False,
                  check_only: bool = False,
                  interactive: bool = True) -> Optional[Path]:
    """
    Main installation function.

    Args:
        url: GitHub URL or direct skill URL
        dest_path: Destination directory for installation
        force: Force overwrite without prompts
        check_only: Only check if update is needed, don't install
        interactive: Allow interactive prompts

    Returns:
        Path to installed skill, or None if skipped/check-only
    """
    dest_dir = Path(dest_path).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    url_type, components = parse_github_url(url)
    print(f"  URL type: {url_type}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        skill_path = None

        if url_type == 'raw' or url_type == 'direct':
            # Direct file download
            filename = url.split('/')[-1]
            file_path = tmp_path / filename
            download_file(components['url'], file_path)

            if filename.endswith('.skill'):
                skill_path = install_skill_file(file_path, dest_dir)
            else:
                # Copy single file
                shutil.copy2(file_path, dest_dir / filename)
                skill_path = dest_dir / filename

        elif url_type == 'file':
            # GitHub blob (file)
            raw_url = (
                f"https://raw.githubusercontent.com/"
                f"{components['owner']}/{components['repo']}/"
                f"{components['branch']}/{components['path']}"
            )
            filename = components['path'].split('/')[-1]
            file_path = tmp_path / filename
            download_file(raw_url, file_path)

            if filename.endswith('.skill'):
                skill_path = install_skill_file(file_path, dest_dir)
            else:
                shutil.copy2(file_path, dest_dir / filename)
                skill_path = dest_dir / filename

        elif url_type == 'folder':
            # GitHub folder
            folder_name = components['path'].split('/')[-1]
            folder_path = tmp_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

            download_github_folder(
                components['owner'],
                components['repo'],
                components['branch'],
                components['path'],
                folder_path
            )

            # Find skill root
            skill_root = find_skill_in_folder(folder_path)
            if skill_root:
                skill_name = skill_root.name
                skill_dest = dest_dir / skill_name

                # Check for existing installation
                if skill_dest.exists():
                    if check_only:
                        status = check_existing_skill(skill_dest, skill_root)
                        print(f"  Status: {status['strategy']}")
                        return None

                    if perform_smart_update(skill_dest, skill_root, force, interactive):
                        skill_path = skill_dest
                    else:
                        return None
                else:
                    shutil.copytree(skill_root, skill_dest)
                    skill_path = skill_dest
            else:
                print("  ⚠️  Warning: No SKILL.md found in folder")
                skill_dest = dest_dir / folder_name
                if skill_dest.exists():
                    shutil.rmtree(skill_dest)
                shutil.copytree(folder_path, skill_dest)
                skill_path = skill_dest

        elif url_type == 'repo':
            # Full repository
            repo_path = download_github_repo(
                components['owner'],
                components['repo'],
                components['branch'],
                tmp_path
            )

            # Find skill in repository
            skill_root = find_skill_in_folder(repo_path)
            if skill_root:
                skill_name = skill_root.name
                skill_dest = dest_dir / skill_name

                # Check for existing installation
                if skill_dest.exists():
                    if check_only:
                        status = check_existing_skill(skill_dest, skill_root)
                        print(f"  Status: {status['strategy']}")
                        return None

                    if perform_smart_update(skill_dest, skill_root, force, interactive):
                        skill_path = skill_dest
                    else:
                        return None
                else:
                    shutil.copytree(skill_root, skill_dest)
                    skill_path = skill_dest
            else:
                # Copy entire repo
                repo_name = components['repo']
                skill_dest = dest_dir / repo_name
                if skill_dest.exists():
                    shutil.rmtree(skill_dest)
                shutil.copytree(repo_path, skill_dest)
                skill_path = skill_dest

    if skill_path and not check_only:
        print(f"\n✅ Skill installed successfully!")
        print(f"   Location: {skill_path}")

        # Verify installation
        skill_md = skill_path / 'SKILL.md' if skill_path.is_dir() else None
        if skill_md and skill_md.exists():
            print(f"   SKILL.md: Found")
        else:
            print(f"   ⚠️  Warning: SKILL.md not found - may not be a valid skill")

        return skill_path

    return None


def install_skills_batch(urls: List[str], dest_path: str,
                         force: bool = False,
                         interactive: bool = True) -> List[Path]:
    """
    Install multiple skills from a list of URLs.

    Args:
        urls: List of GitHub URLs
        dest_path: Destination directory for installation
        force: Force overwrite without prompts
        interactive: Allow interactive prompts

    Returns:
        List of successfully installed skill paths
    """
    installed = []
    failed = []

    print(f"Installing {len(urls)} skills...\n")

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            result = install_skill(
                url, dest_path,
                force=force,
                interactive=interactive
            )
            if result:
                installed.append(result)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed.append((url, str(e)))
        print()

    # Summary
    print("=" * 50)
    print(f"✅ Installed: {len(installed)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for url, error in failed:
            print(f"   - {url}: {error}")

    return installed


def main():
    parser = argparse.ArgumentParser(
        description='Install Claude Code skills from GitHub URLs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/user/skill-repo ~/.claude/skills/
  %(prog)s https://github.com/user/repo/tree/main/skills/my-skill ./skills/
  %(prog)s --batch "url1,url2,url3" ~/.claude/skills/
  %(prog)s --check https://github.com/user/skill-repo ~/.claude/skills/
        """
    )

    parser.add_argument(
        'url',
        help='GitHub URL of the skill to install (or comma-separated URLs with --batch)'
    )
    parser.add_argument(
        'destination',
        help='Destination directory for installation'
    )
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Install multiple skills (URL should be comma-separated list)'
    )
    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='Only check if update is needed, do not install'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force overwrite without prompts'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Assume yes to all prompts (non-interactive mode)'
    )

    args = parser.parse_args()

    interactive = not args.yes

    try:
        if args.batch:
            # Parse comma-separated URLs
            urls = [u.strip() for u in args.url.split(',') if u.strip()]
            if not urls:
                print("❌ No URLs provided")
                sys.exit(1)

            install_skills_batch(
                urls, args.destination,
                force=args.force,
                interactive=interactive
            )
        else:
            install_skill(
                args.url, args.destination,
                force=args.force,
                check_only=args.check,
                interactive=interactive
            )
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
