from pathlib import Path
import subprocess
from typing import Optional

from midil.cli.core.launchers.base import BaseLauncher
from midil.cli.commands._common import console


class UvicornLauncher(BaseLauncher):
    def __init__(
        self,
        app_module: str = "main:app",
        port: int = 8000,
        reload: bool = True,
        extra_args: Optional[list[str]] = None,
        project_dir: Optional[Path] = None,
    ):
        self.app_module = app_module
        self.port = port
        self.reload = reload
        self.extra_args = extra_args or []
        self.project_dir = project_dir or Path.cwd()

    def discover_app(self) -> Path:
        """
        Discover the FastAPI app file based on the app_module.
        By default, expects 'main.py' in the project directory.
        """
        module_file = self.app_module.split(":")[0]
        app_path = self.project_dir / f"{module_file}.py"
        if not app_path.exists():
            raise FileNotFoundError(
                f"🚫 Cannot find {module_file}.py in {self.project_dir}."
            )
        return app_path

    def build_command(self) -> list[str]:
        """
        Build the uvicorn command as a list of arguments.
        """
        cmd = [
            "uvicorn",
            self.app_module,
            f"--port={self.port}",
        ]
        if self.reload:
            cmd.append("--reload")
        cmd.extend(self.extra_args)
        return cmd

    def run(self) -> None:
        """Auto-discover FastAPI app and launch it with uvicorn."""
        self.discover_app()
        command = self.build_command()
        console.print(
            f"🚀 Launching FastAPI app: {self.app_module} on port {self.port}..."
        )
        subprocess.run(command, cwd=str(self.project_dir))
