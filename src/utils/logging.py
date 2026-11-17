"""Single logging setup for every CLI in the project."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: Optional[str] = None, logfile: Optional[Path] = None) -> None:
    """Configure the root logger once. Level falls back to $LOG_LEVEL, then INFO."""
    lvl = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    handlers = [logging.StreamHandler()]
    if logfile:
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(logfile))
    logging.basicConfig(level=lvl, format=FORMAT, handlers=handlers, force=True)
