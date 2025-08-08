# midil/cli/commands/launch.py
import click
from midil.cli.core.launchers.uvicorn import UvicornLauncher


@click.command("launch")
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--reload", is_flag=True, help="Reload the server on code changes")
def launch_command(port, reload):
    """Launch a MIDIL service from the current directory."""
    UvicornLauncher(port=port, reload=reload).run()
