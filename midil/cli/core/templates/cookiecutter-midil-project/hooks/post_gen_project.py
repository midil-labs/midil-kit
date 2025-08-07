import os
from pathlib import Path


def handle_conditional_files() -> None:
    """Remove files based on user configuration choices."""
    # Remove Docker files if not needed
    if "{{ cookiecutter.include_docker }}" != "y":
        docker_files = ["Dockerfile", "docker-compose.yml"]
        for file in docker_files:
            if os.path.exists(file):
                os.remove(file)


def create_directories() -> None:
    """Create additional directories for project structure."""
    directories = [
        "tests",
        "{{ cookiecutter.project_slug }}",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def create_init_files() -> None:
    """Create __init__.py files for Python packages."""
    init_files = [
        "{{ cookiecutter.project_slug }}/__init__.py",
        "tests/__init__.py",
    ]

    for init_file in init_files:
        Path(init_file).touch()


def main() -> None:
    handle_conditional_files()
    create_directories()
    create_init_files()


if __name__ == "__main__":
    main()
