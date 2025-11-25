"""Turn servo radar sweep samples into sector occupancy metrics."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple


Sample = Tuple[int, Optional[float]]


class RadarOccupancy:
    """Aggregate radar samples into occupancy statistics."""

    def __init__(self, sectors: int, object_threshold_m: float) -> None:
        if sectors <= 0:
            raise ValueError("Sectors must be positive")
        self.sectors = sectors
        self.object_threshold = object_threshold_m
        self._sector_width = 180 / sectors

    def _sector_index(self, angle: int) -> int:
        idx = int(angle // self._sector_width)
        return min(max(idx, 0), self.sectors - 1)

    def _sector_percentages(self, samples: Sequence[Sample]) -> Dict[str, float]:
        totals = [0] * self.sectors
        hits = [0] * self.sectors
        for angle, distance in samples:
            sector = self._sector_index(angle)
            totals[sector] += 1
            if distance is not None and distance <= self.object_threshold:
                hits[sector] += 1
        output = {}
        for idx in range(self.sectors):
            percent = 0.0 if totals[idx] == 0 else (hits[idx] / totals[idx]) * 100.0
            output[f"sector_{idx}_pct"] = round(percent, 2)
        return output

    def _objects_count(self, samples: Sequence[Sample]) -> int:
        count = 0
        active = False
        for _, distance in samples:
            occupied = distance is not None and distance <= self.object_threshold
            if occupied and not active:
                count += 1
                active = True
            elif not occupied and active:
                active = False
        return count

    def _min_distance(self, samples: Sequence[Sample]) -> Optional[float]:
        valid = [distance for _, distance in samples if distance is not None]
        if not valid:
            return None
        return round(min(valid), 3)

    def process(self, samples: Sequence[Sample]) -> Dict[str, float | int | None]:
        """Return sector occupancy %, min distance, and object count."""
        metrics = self._sector_percentages(samples)
        metrics["objects_count"] = self._objects_count(samples)
        metrics["min_distance_m"] = self._min_distance(samples)
        return metrics
