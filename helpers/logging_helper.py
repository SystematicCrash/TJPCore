import logging
from pathlib import Path
from helpers.config_helper import get_config

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_runtime_logger = logging.getLogger("runtime_logger")
_runtime_logger.setLevel(logging.DEBUG)
_runtime_logger.propagate = False  

def _setup_logger(console: bool = True):
    log_file = Path(get_config("logging.filename"))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.touch(exist_ok=True)

    formatter = logging.Formatter(
        "{levelname}: {message} - {asctime}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    if console:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(
            filename=log_file,
            mode=get_config("logging.filemode"),
            encoding="utf-8",
        )

    handler.setFormatter(formatter)
    _runtime_logger.addHandler(handler)

_setup_logger(console=False)

def logger(message: str, mode: str = "warning"):
    if mode not in _LOG_LEVELS:
        raise ValueError(f"{mode} is not a valid mode")
    _runtime_logger.log(_LOG_LEVELS[mode], message)
