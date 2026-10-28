import logging
import os

_STREAM_FORMAT = "%(levelname)s: %(message)s"
_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def _resolve_level() -> int:
    """Log level from ``PYGWALKER_LOG_LEVEL`` (name or number); defaults to INFO."""
    raw = os.getenv("PYGWALKER_LOG_LEVEL")
    if not raw:
        return logging.INFO
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    level = logging.getLevelName(raw.upper())
    return level if isinstance(level, int) else logging.INFO


def _has_stream_handler(logger: logging.Logger) -> bool:
    # FileHandler subclasses StreamHandler, so match the exact class.
    return any(type(handler) is logging.StreamHandler for handler in logger.handlers)


def _has_file_handler(logger: logging.Logger, path: str) -> bool:
    target = os.path.abspath(path)
    return any(getattr(handler, "baseFilename", None) == target for handler in logger.handlers)


def init_logging() -> None:
    """Configure the shared ``pygwalker`` logger.

    Console (stderr) logging is always on, matching the historical behaviour. Two optional
    environment variables let a dev session or agent capture logs centrally:

    - ``PYGWALKER_LOG_LEVEL`` — logger level (e.g. ``DEBUG``, ``INFO``, or a number).
    - ``PYGWALKER_LOG_FILE``  — also append logs to this file (created if needed).

    The function is idempotent: repeated calls will not add duplicate handlers.
    """
    logger = logging.getLogger("pygwalker")
    logger.setLevel(_resolve_level())

    if not _has_stream_handler(logger):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(_STREAM_FORMAT))
        logger.addHandler(stream_handler)

    log_file = os.getenv("PYGWALKER_LOG_FILE")
    if log_file and not _has_file_handler(logger, log_file):
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
        logger.addHandler(file_handler)
