"""Sound sensor wrapper producing analog + digital-like output."""
from __future__ import annotations

import logging
from collections import deque
from math import isnan
from typing import Callable, Dict, Optional

from . import simulate
from .grove_utils import resolve_analog

LOGGER = logging.getLogger(__name__)


class SoundSensor:
    """Return averaged analog loudness and derived digital value."""

    def __init__(
        self,
        port: str,
        adc_address: int = 0x04,
        simulate_mode: bool = False,
        simulator: Optional[Callable[[], tuple[int, bool]]] = None,
        moving_average_samples: int = 5,
    ) -> None:
        self.channel = resolve_analog(port)
        self.adc_address = adc_address
        self._simulate = simulate_mode
        self._simulator = simulator or simulate.EnvSimulator().sound
        self._samples = deque(maxlen=moving_average_samples)
        self._adc = None
        if not simulate_mode:
            try:
                from grove.adc import ADC

                self._adc = ADC(address=adc_address)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Sound sensor using simulation: %s", exc)
                self._simulate = True

    def _read_raw(self) -> tuple[int, bool]:
        if self._simulate or self._adc is None:
            analog, digital = self._simulator()
            return int(analog), bool(digital)

        try:
            value = self._adc.read(self.channel)
            if value is None or isinstance(value, float) and isnan(value):
                raise RuntimeError("Invalid ADC value for sound sensor")
            analog = int(value)
            digital = analog > 550
            return analog, digital
        except Exception as exc:  # pragma: no cover
            LOGGER.error("Sound sensor read failed: %s", exc, exc_info=True)
            return 0, False

    def read(self) -> Dict[str, int | bool]:
        analog, digital = self._read_raw()
        self._samples.append(analog)
        avg = int(sum(self._samples) / len(self._samples)) if self._samples else analog
        return {"sound_adc": avg, "sound_digital": bool(digital)}
