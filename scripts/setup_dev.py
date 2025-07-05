#!/usr/bin/env python3
"""
Development setup script for midil-kit.

This script helps set up the development environment by:
1. Installing Poetry if not present
2. Installing dependencies
3. Setting up pre-commit hooks
4. Running initial checks
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(
    command: str, check: bool = True, capture_output: bool = False
) -> Optional[subprocess.CompletedProcess]:
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None


def check_poetry_installed() -> bool:
    """Check if Poetry is installed."""
    result = run_command("poetry --version", check=False, capture_output=True)
    return bool(result and result.returncode == 0)


def install_poetry() -> bool:
    """Install Poetry if not already installed."""
    if check_poetry_installed():
        print("Poetry is already installed.")
        return True

    print("Installing Poetry...")
    install_script = "curl -sSL https://install.python-poetry.org | python3 -"
    result = run_command(install_script)
    return result is not None


def setup_project() -> bool:
    """Set up the project dependencies and tools."""
    print("Setting up midil-kit development environment...")

    # Install dependencies
    print("\n1. Installing dependencies...")
    result = run_command("poetry install")
    if not result:
        print("Failed to install dependencies.")
        return False

    # Install pre-commit hooks
    print("\n2. Installing pre-commit hooks...")
    result = run_command("poetry run pre-commit install")
    if not result:
        print("Failed to install pre-commit hooks.")
        return False

    # Run initial formatting
    print("\n3. Running initial code formatting...")
    result = run_command("poetry run black .")
    if not result:
        print("Failed to format code.")
        return False

    result = run_command("poetry run isort .")
    if not result:
        print("Failed to sort imports.")
        return False

    # Run tests
    print("\n4. Running tests...")
    result = run_command("poetry run pytest")
    if not result:
        print("Some tests failed.")
        return False

    print("\n✅ Development environment setup complete!")
    return True


def main() -> None:
    """Main setup function."""
    print("Midil Kit - Development Setup")
    print("=" * 40)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print(
            "Error: pyproject.toml not found. Please run this script from the project root."
        )
        sys.exit(1)

    # Install Poetry if needed
    if not check_poetry_installed():
        if not install_poetry():
            print("Failed to install Poetry. Please install it manually.")
            sys.exit(1)

    # Setup project
    if not setup_project():
        print("Failed to set up the project.")
        sys.exit(1)

    print("\n🎉 Setup complete! You can now:")
    print("  - Run tests: poetry run pytest")
    print("  - Format code: poetry run black .")
    print("  - Check types: poetry run mypy .")
    print("  - Run examples: poetry run python examples/basic_usage.py")


if __name__ == "__main__":
    main()
