# mxLogging.py - thin layer over the stdlib logging module
#
# - a PRINT level (25) for application messages: above INFO, below WARNING
# - Logger.print() to emit at that level (markup is interpreted for these messages only)
# - setup_mxLogger() wires the "mxcloudshare" package logger to a Rich console handler on
#   stderr (stdout stays clean for command output) and, optionally, to a log file.
#
# getLogger() returns a plain logging.Logger, so every call goes through the handlers
# configured by setup_mxLogger(), including those of other modules under "mxcloudshare".

import logging

from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.text import Text

PRINT = 25
PRINT_NAME = "PRINT"

PACKAGE_LOGGER = "mxcloudshare"

valid_levels = {
    "DEBUG": logging.DEBUG,
    "PRINT": PRINT,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LEVEL_STYLES = {
    logging.CRITICAL: "bold magenta",
    logging.ERROR: "bold red",
    logging.WARNING: "bold yellow",
    logging.INFO: "dim",
    logging.DEBUG: "dim",
}

# Marks the handlers installed by setup_mxLogger() so a second call replaces only those.
_OWNED = "_mx_owned"

logging.addLevelName(PRINT, PRINT_NAME)


def _print(self: logging.Logger, message, *args, **kwargs):
    """Log 'message % args' with severity PRINT; Rich markup is interpreted."""
    if self.isEnabledFor(PRINT):
        kwargs.setdefault("stacklevel", 2)
        kwargs.setdefault("extra", {}).setdefault("markup", True)
        self._log(PRINT, message, args, **kwargs)


logging.Logger.print = _print


class _ConsoleHandler(RichHandler):
    """RichHandler that prints PRINT messages bare and others as 'LEVEL: message'."""

    def __init__(self):
        super().__init__(
            console=Console(stderr=True, soft_wrap=True),
            show_time=False,
            show_level=False,
            show_path=False,
            markup=False,
            highlighter=NullHighlighter(),
        )

    def render_message(self, record, message):
        rendered = super().render_message(record, message)
        if record.levelno == PRINT or not isinstance(rendered, Text):
            return rendered
        style = _LEVEL_STYLES.get(max(k for k in _LEVEL_STYLES if k <= record.levelno), "")
        return Text.assemble((f"{record.levelname}: ", style), rendered)

    def emit(self, record):
        # RichHandler lays records out in a full-width grid, which pads every line with
        # trailing spaces once stderr is piped or redirected. One bare line is enough here.
        try:
            message = self.format(record)  # includes the traceback text, if any
            self.console.print(self.render_message(record, message), soft_wrap=True)
        except Exception:
            self.handleError(record)


def getLogger(name: str | None = None) -> logging.Logger:
    """Return the stdlib logger for `name`; without a name, the package logger."""
    return logging.getLogger(name or PACKAGE_LOGGER)


def setup_mxLogger(
    log_file: str | None = None,
    log_level: str | None = None,
    file_mode: str = "a",
) -> logging.Logger:
    """
    Configure the package logger. Safe to call repeatedly: handlers from a previous call are replaced.

    Args:
        log_file: path of a log file (full timestamps, names and levels). None logs to the console only.
        log_level: one of valid_levels (case-insensitive). Unknown names fall back to INFO.
        file_mode: 'a' to append to the log file, 'w' to truncate it.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)

    for handler in logger.handlers[:]:
        if getattr(handler, _OWNED, False):
            logger.removeHandler(handler)
            handler.close()

    logger.setLevel(valid_levels.get((log_level or "INFO").upper(), logging.INFO))
    # Own the output: don't also hand records to the root logger's handlers.
    logger.propagate = False

    handlers: list[logging.Handler] = [_ConsoleHandler()]
    if log_file:
        file_handler = logging.FileHandler(log_file, mode=file_mode)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        handlers.append(file_handler)

    for handler in handlers:
        setattr(handler, _OWNED, True)
        logger.addHandler(handler)

    return logger
