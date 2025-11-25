"""Wrapper around Seeed DHT sensors with simulation fallback."""
from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

from . import simulate
from .grove_utils import resolve_port

LOGGER = logging.getLogger(__name__)


class DHTSensor:
    """Read temperature and humidity from a DHT11/DHT22 sensor."""

    def __init__(
        self,
        port: str,
        sensor_type: str = "11",
        simulate_mode: bool = False,
        simulator: Optional[Callable[[], tuple[float, float]]] = None,
    ) -> None:
        self.port = resolve_port(port)
        self.sensor_type = sensor_type
        self._simulate = simulate_mode
        self._simulator = simulator or simulate.EnvSimulator().temperature_humidity
        self._sensor = None
        if not simulate_mode:
            try:
                from seeed_dht import DHT

                self._sensor = DHT(sensor_type, self.port)
            except Exception as exc:  # pragma: no cover - hardware import
                LOGGER.warning("Falling back to simulation for DHT sensor: %s", exc)
                self._simulate = True

    def read(self) -> Optional[Dict[str, float]]:
        """Return the latest temperature/humidity sample."""
        if self._simulate or self._sensor is None:
            temp, hum = self._simulator()
            return {"temperature_c": temp, "humidity_pct": hum}

        try:
            humidity, temperature = self._sensor.read()
            if humidity is None or temperature is None:
                raise RuntimeError("Invalid reading from DHT sensor")
            return {
                "temperature_c": round(float(temperature), 2),
                "humidity_pct": round(float(humidity), 2),
            }
        except Exception as exc:  # pragma: no cover - hardware runtime
            LOGGER.error("DHT read failed: %s", exc, exc_info=True)
            return None
