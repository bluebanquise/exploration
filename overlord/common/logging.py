import logging
import os
import sys
from typing import Any, Dict, List, Tuple

def configure_logging(log_file: str = None, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("overlord")
    if logger.handlers:
        # Already configured
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # if log_file:
    #     os.makedirs(os.path.dirname(log_file), exist_ok=True)
    #     file_handler = logging.FileHandler(log_file)
    #     file_handler.setFormatter(formatter)
    #     logger.addHandler(file_handler)

    return logger