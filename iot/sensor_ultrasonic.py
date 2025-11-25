"""Ultrasonic ranging sensor abstraction."""
from __future__ import annotations

import logging
import time
from typing import Optional

from . import simulate
from .grove_utils import resolve_port

LOGGER = logging.getLogger(__name__)


class UltrasonicSensor:
    """Measure distance in meters using Grove Ultrasonic Ranger."""

    def __init__(
        self,
        port: str,
        simulate_mode: bool = False,
        simulator: Optional[simulate.RadarSimulator] = None,
        timeout_ms: int = 25,
    ) -> None:
        self.port = resolve_port(port)
        self.timeout_ms = timeout_ms
        self._simulate = simulate_mode
        self._simulator = simulator or simulate.RadarSimulator()
        self._sensor = None
        if not simulate_mode:
            try:
                from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

                self._sensor = GroveUltrasonicRanger(self.port)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Ultrasonic sensor in simulation: %s", exc)
                self._simulate = True

    def read_distance(self, angle: Optional[int] = None) -> Optional[float]:
        """Return distance in meters, None on timeout."""
        if self._simulate or self._sensor is None:
            target_angle = angle if angle is not None else 0
            samples = self._simulator.scan(target_angle, target_angle, 5)
            return samples[0][1]
        start = time.time()
        try:
            distance_cm = self._sensor.get_distance()
            if distance_cm is None:
                return None
            if (time.time() - start) * 1000 > self.timeout_ms:
                LOGGER.warning("Ultrasonic read timed out")
                return None
            return max(0.02, float(distance_cm) / 100.0)
        except Exception as exc:  # pragma: no cover
            LOGGER.error("Ultrasonic read failed: %s", exc, exc_info=True)
            return None
