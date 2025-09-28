# midil/cli/commands/launch.py
import click
from midil.cli.core.launchers.uvicorn import UvicornLauncher
from midil.cli.utils import print_logo
from midil.version import __version__, __service_version__
from midil.cli.utils import console
from midil.settings import get_api_settings
from typing import Optional


@click.command("launch")
@click.option("--port", required=False, help="Port to run the server on")
@click.option("--reload", is_flag=True, help="Reload the server on code changes")
def launch_command(port: Optional[int], reload: bool):
    """Launch a MIDIL service from the current directory."""
    print_logo()
    settings = get_api_settings()
    port = port or settings.server.port
    launcher = UvicornLauncher(port=port, reload=reload)
    app_name = launcher.project_dir.name

    console.print(
        f"\n"
        f"[dim]🛸 [bold magenta]Launching[/bold magenta] "
        f"[bold white]{app_name}[/bold white] "
        f"[bold green](v{__service_version__})[/bold green]\n"
        f"   using [bold white]midil-kit[/bold white] "
        f"[bold green](v{__version__})[/bold green]\n"
        f"   on port [bold yellow]{port}[/bold yellow]\n\n"
        f"✨ [italic magenta]Sit back, relax, and watch the magic happen![/italic magenta][/dim]\n",
        justify="center",
    )

    launcher.run()
