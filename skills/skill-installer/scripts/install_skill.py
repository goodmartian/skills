#!/usr/bin/env python3
"""
Skill Installer - Install Claude Code skills from GitHub URLs.

Supports:
- GitHub repositories: github.com/user/repo
- GitHub folders: github.com/user/repo/tree/branch/path/to/skill
- GitHub files: github.com/user/repo/blob/branch/skill.skill
- Raw URLs: raw.githubusercontent.com/...
- Direct .skill file URLs

Usage:
    python install_skill.py <github_url> <destination_path>
"""

import sys
import os
import re
import json
import shutil
import tempfile
import zipfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple


def parse_github_url(url: str) -> Tuple[str, dict]:
    """
    Parse GitHub URL and return type and components.

    Returns:
        Tuple of (url_type, components)
        url_type: 'repo', 'folder', 'file', 'raw', 'direct'
    """
    url = url.strip().rstrip('/')

    # Raw GitHub URL
    if 'raw.githubusercontent.com' in url:
        return 'raw', {'url': url}

    # Direct .skill file URL
    if url.endswith('.skill') and not 'github.com' in url:
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
    print(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try 'master' branch if 'main' fails
            if '/main/' in url:
                alt_url = url.replace('/main/', '/master/')
                print(f"Trying alternate branch: {alt_url}")
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
    print(f"Fetching folder contents: {path}")

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
    print(f"Installing skill from: {skill_file}")

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


def install_skill(url: str, dest_path: str) -> None:
    """
    Main installation function.

    Args:
        url: GitHub URL or direct skill URL
        dest_path: Destination directory for installation
    """
    dest_dir = Path(dest_path).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    url_type, components = parse_github_url(url)
    print(f"URL type: {url_type}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

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
                if skill_dest.exists():
                    shutil.rmtree(skill_dest)
                shutil.copytree(skill_root, skill_dest)
                skill_path = skill_dest
            else:
                print("Warning: No SKILL.md found in folder")
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
                if skill_dest.exists():
                    shutil.rmtree(skill_dest)
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

    print(f"\n✅ Skill installed successfully!")
    print(f"   Location: {skill_path}")

    # Verify installation
    skill_md = skill_path / 'SKILL.md' if skill_path.is_dir() else None
    if skill_md and skill_md.exists():
        print(f"   SKILL.md: Found")
    else:
        print(f"   Warning: SKILL.md not found - may not be a valid skill")


def main():
    if len(sys.argv) < 3:
        print("Usage: install_skill.py <github_url> <destination_path>")
        print("\nExamples:")
        print("  install_skill.py https://github.com/user/skill-repo ~/.claude/skills/")
        print("  install_skill.py https://github.com/user/repo/tree/main/skills/my-skill ./skills/")
        sys.exit(1)

    url = sys.argv[1]
    dest_path = sys.argv[2]

    try:
        install_skill(url, dest_path)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
