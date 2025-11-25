"""Shared helpers for Grove/Seeed based projects."""
from __future__ import annotations

import logging
import logging.handlers
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Callable, Dict, Iterable, List, Optional

import yaml


DIGITAL_PREFIX = "D"
ANALOG_PREFIX = "A"

# Minimal map needed for fallbacks that require a BCM pin (servo on D12 → GPIO12).
DIGITAL_TO_BCM: Dict[int, int] = {
    18: 18,
}


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/app.log"


def load_yaml_config(path: str) -> Dict:
    """Load config.yaml if present."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def ensure_parent_dir(path: str) -> None:
    """Create parent directory for the given file path."""
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def setup_logging(cfg: LoggingConfig) -> None:
    """Configure console + rotating file logging."""
    level = getattr(logging, cfg.level.upper(), logging.INFO)
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    logging.basicConfig(level=level, format=log_format)

    ensure_parent_dir(cfg.file)
    file_handler = logging.handlers.RotatingFileHandler(
        cfg.file, maxBytes=2_000_000, backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    root = logging.getLogger()
    root.addHandler(file_handler)


def env_flag(name: str, default: bool = False) -> bool:
    """Parse environment variable into bool."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip() in {"1", "true", "TRUE", "yes", "on"}


def resolve_port(port: str) -> int:
    """Turn a Grove style digital port name into an integer channel."""
    if isinstance(port, int):
        return port
    if not isinstance(port, str):
        raise TypeError(f"Unsupported port type: {port!r}")
    port = port.strip().upper()
    if port.startswith(DIGITAL_PREFIX):
        return int(port[1:])
    return int(port)


def resolve_analog(port: str) -> int:
    """Turn an analog port (e.g. A0) into channel number."""
    if isinstance(port, int):
        return port
    if not isinstance(port, str):
        raise TypeError(f"Unsupported analog port type: {port!r}")
    port = port.strip().upper()
    if port.startswith(ANALOG_PREFIX):
        return int(port[1:])
    return int(port)


def digital_to_bcm(port: str) -> int:
    """Return BCM pin for digital port when available."""
    number = resolve_port(port)
    if number not in DIGITAL_TO_BCM:
        raise KeyError(
            f"Digital port D{number} missing BCM mapping; update DIGITAL_TO_BCM"
        )
    return DIGITAL_TO_BCM[number]


def register_signal_handlers(callback: Callable[[int, Optional[object]], None]) -> None:
    """Attach SIGINT/SIGTERM handlers for clean shutdown."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, callback)


def chunked(items: List, size: int) -> Iterable[List]:
    """Yield successive chunks of length `size`."""
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def compute_median(values: Iterable[float]) -> Optional[float]:
    """Return the median or None when the iterable is empty."""
    data = [v for v in values if v is not None]
    if not data:
        return None
    return median(data)
