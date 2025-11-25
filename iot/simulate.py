"""Simulation utilities for development on non-hardware hosts."""
from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Tuple


class EnvSimulator:
    """Generate pseudo realistic environmental sensor values."""

    def __init__(self, seed: int | None = None) -> None:
        self._start = time.time()
        self._rng = random.Random(seed or int(self._start))

    def _phase(self) -> float:
        return (time.time() - self._start) / 60.0

    def temperature_humidity(self) -> Tuple[float, float]:
        phase = self._phase()
        temp = 24 + 3 * math.sin(phase / 20) + self._rng.uniform(-0.5, 0.5)
        humidity = 55 + 8 * math.cos(phase / 25) + self._rng.uniform(-1.0, 1.0)
        return round(temp, 2), max(30.0, min(90.0, round(humidity, 2)))

    def light(self) -> int:
        phase = self._phase()
        base = 600 + 200 * math.sin(phase / 10)
        noise = self._rng.uniform(-50, 50)
        value = int(max(0, min(1023, base + noise)))
        return value

    def gas(self) -> int:
        phase = self._phase()
        base = 350 + 150 * math.sin(phase / 15)
        noise = self._rng.uniform(-60, 60)
        return int(max(0, min(1023, base + noise)))

    def sound(self) -> Tuple[int, bool]:
        peak = 150 if self._rng.random() > 0.8 else 30
        analog = min(1023, int(self._rng.gauss(400 + peak, 40)))
        digital = analog > 550
        return analog, digital


class RadarSimulator:
    """Approximate radar readings with virtual obstacles."""

    def __init__(self, sectors: int = 6) -> None:
        self.sectors = sectors
        # Pretend there are obstacles in sector 1 and 4 by default.
        self.obstacles: Dict[int, Tuple[float, float]] = {
            1: (0.5, 1.0),
            4: (0.7, 1.3),
        }
        self._rng = random.Random(time.time())

    def _sector_for_angle(self, angle: float) -> int:
        sector_width = 180 / self.sectors
        return min(int(angle // sector_width), self.sectors - 1)

    def _distance_for_angle(self, angle: float) -> float:
        sector = self._sector_for_angle(angle)
        if sector in self.obstacles:
            rng_min, rng_max = self.obstacles[sector]
            return self._rng.uniform(rng_min, rng_max)
        return self._rng.uniform(1.5, 3.5)

    def scan(self, start: int, stop: int, step: int) -> List[Tuple[int, float]]:
        samples: List[Tuple[int, float]] = []
        direction = 1 if stop >= start else -1
        stop_inclusive = stop + direction
        for angle in range(start, stop_inclusive, step * direction):
            distance = self._distance_for_angle(angle) + self._rng.uniform(-0.05, 0.05)
            samples.append((max(0, min(180, angle)), max(0.05, distance)))
        return samples
