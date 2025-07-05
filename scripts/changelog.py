#!/usr/bin/env python3
"""
Changelog management script for midil-kit.

This script helps generate and manage changelog entries based on git commits
following conventional commit format.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ChangelogManager:
    def __init__(self, changelog_file: str = "CHANGELOG.md"):
        self.changelog_file = Path(changelog_file)
        self.commit_types = {
            "feat": "Added",
            "fix": "Fixed",
            "docs": "Documentation",
            "style": "Style",
            "refactor": "Refactored",
            "test": "Tests",
            "chore": "Chore",
            "perf": "Performance",
            "ci": "CI/CD",
            "build": "Build",
            "revert": "Reverted",
        }

    def get_git_commits(self, since: Optional[str] = None) -> List[Dict]:
        """Get git commits since a given tag or commit."""
        cmd = ["git", "log", "--pretty=format:%H|%s|%b|%an|%ad", "--date=short"]

        if since:
            cmd.append(f"{since}..HEAD")
        else:
            cmd.append("--all")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            print(
                "Error: Could not get git commits. Make sure you're in a git repository."
            )
            sys.exit(1)

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split("|", 4)
            if len(parts) >= 5:
                commit_hash, subject, body, author, date = parts
                commits.append(
                    {
                        "hash": commit_hash,
                        "subject": subject,
                        "body": body,
                        "author": author,
                        "date": date,
                    }
                )

        return commits

    def parse_commit(self, commit: Dict) -> Optional[Tuple[str, str, str, bool]]:
        """Parse a commit message and extract conventional commit information."""
        subject = commit["subject"]

        # Match conventional commit format: type(scope): description
        pattern = r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$"
        match = re.match(pattern, subject)

        if not match:
            return None

        commit_type, scope, description = match.groups()
        scope = scope or "general"

        # Check for breaking changes
        breaking = "BREAKING CHANGE:" in commit["body"] if commit["body"] else False

        return commit_type, scope, description, breaking

    def categorize_commits(self, commits: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize commits by type."""
        categorized: Dict[str, List[Dict]] = {}

        for commit in commits:
            parsed = self.parse_commit(commit)
            if not parsed:
                continue

            commit_type, scope, description, breaking = parsed

            if commit_type not in self.commit_types:
                continue

            category = self.commit_types[commit_type]
            if category not in categorized:
                categorized[category] = []

            categorized[category].append(
                {
                    "description": description,
                    "scope": scope,
                    "breaking": breaking,
                    "hash": commit["hash"][:8],
                    "date": commit["date"],
                }
            )

        return categorized

    def generate_changelog_content(self, categorized: Dict[str, List[Dict]]) -> str:
        """Generate changelog content from categorized commits."""
        if not categorized:
            return "No conventional commits found.\n"

        content = "## [Unreleased]\n\n"

        # Add breaking changes first
        breaking_changes = []
        for category, commits in categorized.items():
            for commit in commits:
                if commit["breaking"]:
                    breaking_changes.append(
                        f"- **BREAKING:** {commit['description']} ({commit['scope']})"
                    )

        if breaking_changes:
            content += "### Breaking Changes\n"
            content += "\n".join(breaking_changes) + "\n\n"

        # Add regular changes by category
        for category in [
            "Added",
            "Fixed",
            "Performance",
            "Refactored",
            "Tests",
            "Documentation",
            "Style",
            "Chore",
            "CI/CD",
            "Build",
        ]:
            if category in categorized:
                content += f"### {category}\n"
                for commit in categorized[category]:
                    if not commit[
                        "breaking"
                    ]:  # Skip breaking changes here as they're already listed
                        content += f"- {commit['description']} ({commit['scope']})\n"
                content += "\n"

        return content

    def update_changelog(
        self, since: Optional[str] = None, preview: bool = False
    ) -> str:
        """Update the changelog file with new entries."""
        commits = self.get_git_commits(since)
        categorized = self.categorize_commits(commits)
        new_content = self.generate_changelog_content(categorized)

        if preview:
            return new_content

        if not self.changelog_file.exists():
            print(f"Error: {self.changelog_file} does not exist.")
            sys.exit(1)

        # Read existing content
        with open(self.changelog_file, "r") as f:
            content = f.read()

        # Replace the [Unreleased] section
        pattern = r"## \[Unreleased\].*?(?=\n## \[|\Z)"
        replacement = new_content.rstrip()

        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            # If no [Unreleased] section exists, add it at the beginning
            lines = content.split("\n")
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith("## ["):
                    insert_index = i
                    break

            lines.insert(insert_index, replacement)
            new_content = "\n".join(lines)

        # Write back to file
        with open(self.changelog_file, "w") as f:
            f.write(new_content)

        return f"Updated {self.changelog_file} with {len(commits)} commits."

    def get_latest_tag(self) -> Optional[str]:
        """Get the latest git tag."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def create_release(self, version: str, release_type: str = "patch") -> str:
        """Create a new release by updating version and changelog."""
        # Get the latest tag
        latest_tag = self.get_latest_tag()

        # Update changelog
        self.update_changelog(since=latest_tag)

        # Read the changelog to get the new content
        with open(self.changelog_file, "r") as f:
            content = f.read()

        # Replace [Unreleased] with the new version
        today = datetime.now().strftime("%Y-%m-%d")
        new_version_section = f"## [{version}] - {today}\n"

        # Find and replace the [Unreleased] section
        pattern = r"## \[Unreleased\](.*?)(?=\n## \[|\Z)"
        replacement = new_version_section + r"\1"

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Add the version link at the bottom
        if latest_tag:
            link_line = f"\n[{version}]: https://github.com/midil/midil-kit/compare/{latest_tag}...v{version}"
        else:
            link_line = f"\n[{version}]: https://github.com/midil/midil-kit/releases/tag/v{version}"

        # Add the link if it doesn't exist
        if f"[{version}]:" not in new_content:
            new_content += link_line

        # Write back to file
        with open(self.changelog_file, "w") as f:
            f.write(new_content)

        return f"Created release {version}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage changelog for midil-kit")
    parser.add_argument(
        "action", choices=["update", "preview", "release"], help="Action to perform"
    )
    parser.add_argument("--since", help="Generate changelog since this tag/commit")
    parser.add_argument("--version", help="Version for new release")
    parser.add_argument("--file", default="CHANGELOG.md", help="Changelog file path")

    args = parser.parse_args()

    manager = ChangelogManager(args.file)

    if args.action == "update":
        result = manager.update_changelog(since=args.since)
        print(result)

    elif args.action == "preview":
        result = manager.update_changelog(since=args.since, preview=True)
        print(result)

    elif args.action == "release":
        if not args.version:
            print("Error: --version is required for release action")
            sys.exit(1)
        result = manager.create_release(args.version)
        print(result)


if __name__ == "__main__":
    main()
