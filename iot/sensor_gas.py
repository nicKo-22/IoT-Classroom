"""Grove Gas Sensor v1.5 wrapper."""
from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

from . import simulate
from .grove_utils import resolve_analog

LOGGER = logging.getLogger(__name__)


class GasSensor:
    """Return the ADC value of the gas sensor."""

    def __init__(
        self,
        port: str,
        adc_address: int = 0x04,
        simulate_mode: bool = False,
        simulator: Optional[Callable[[], int]] = None,
    ) -> None:
        self.channel = resolve_analog(port)
        self.adc_address = adc_address
        self._simulate = simulate_mode
        self._simulator = simulator or simulate.EnvSimulator().gas
        self._adc = None
        if not simulate_mode:
            try:
                from grove.adc import ADC

                self._adc = ADC(address=adc_address)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Gas sensor using simulation: %s", exc)
                self._simulate = True

    def read(self) -> Optional[Dict[str, int]]:
        if self._simulate or self._adc is None:
            return {"gas_adc": int(self._simulator())}
        try:
            from math import isnan  # pragma: no cover

            value = self._adc.read(self.channel)
            if value is None or isinstance(value, float) and isnan(value):
                raise RuntimeError("Invalid ADC value for gas sensor")
            return {"gas_adc": int(value)}
        except Exception as exc:  # pragma: no cover
            LOGGER.error("Gas sensor read failed: %s", exc, exc_info=True)
            return None
