from midil.cli.main import cli
from midil.version import __service_version__, __version__
from midil.logger.setup import setup_logger
from midil.settings import LoggerSettings


__all__ = ["cli", "__service_version__", "__version__"]

logger_settings = LoggerSettings().logger
setup_logger(
    level=logger_settings.log_level,
    enable_http_logging=logger_settings.enable_http_logging,
)
