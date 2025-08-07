from midil.cli.core.pyproject import PyProject

try:
    from importlib.metadata import version

    __version__ = version("midil-kit")
except Exception:
    # Fallback to pyproject.toml version (development mode)
    __version__ = PyProject().version

__service_version__ = PyProject().version
