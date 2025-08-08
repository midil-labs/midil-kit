import click

from midil.version import __version__
from midil.cli.commands._common import console


@click.command("version")
@click.option(
    "-s",
    "--short",
    "short",
    default=False,
    is_flag=True,
    required=False,
    help="Display only the short version number.",
)
def version_command(short: bool) -> None:
    """
    Displays the version of the Midil package.
    """
    if short:
        console.print(__version__)
    else:
        console.print(f"🌊 MIDIL Kit version: {__version__}")
        console.print("A Python SDK for backend systems development @midil.io")
