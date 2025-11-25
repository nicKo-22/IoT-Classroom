"""Servo based radar scan implementation."""
from __future__ import annotations

import logging
import time
from typing import List, Optional, Sequence, Tuple

from .grove_utils import compute_median, digital_to_bcm
from .sensor_ultrasonic import UltrasonicSensor

LOGGER = logging.getLogger(__name__)


class ServoController:
    """Drive a standard servo via RPi.GPIO with Grove port notation."""

    def __init__(
        self,
        port: str,
        min_duty: float = 2.5,
        max_duty: float = 12.5,
        frequency: int = 50,
        simulate_mode: bool = False,
    ) -> None:
        self.port = port
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.frequency = frequency
        self._simulate = simulate_mode
        self._gpio = None
        self._pwm = None
        if not simulate_mode:
            try:
                import RPi.GPIO as GPIO

                self._gpio = GPIO
                self._gpio.setmode(GPIO.BCM)
                bcm_pin = digital_to_bcm(port)
                self._gpio.setup(bcm_pin, GPIO.OUT)
                self._pwm = GPIO.PWM(bcm_pin, frequency)
                self._pwm.start(0)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Servo falling back to simulation: %s", exc)
                self._simulate = True

    def angle_to_duty(self, angle: float) -> float:
        span = self.max_duty - self.min_duty
        return self.min_duty + (angle / 180.0) * span

    def set_angle(self, angle: float) -> None:
        if self._simulate or self._pwm is None:
            return
        safe_angle = max(0.0, min(180.0, angle))
        duty = self.angle_to_duty(safe_angle)
        self._pwm.ChangeDutyCycle(duty)

    def cleanup(self) -> None:
        if self._simulate or self._pwm is None or self._gpio is None:
            return
        self._pwm.stop()
        self._gpio.cleanup()


class RadarScanner:
    """Perform sweeping scans combining servo + ultrasonic."""

    def __init__(
        self,
        servo: ServoController,
        ultrasonic: UltrasonicSensor,
        angle_step: int = 5,
        settle_ms: int = 100,
        reads_per_angle: int = 3,
        max_distance_m: float = 4.0,
    ) -> None:
        self.servo = servo
        self.ultrasonic = ultrasonic
        self.angle_step = angle_step
        self.settle_ms = settle_ms
        self.reads_per_angle = reads_per_angle
        self.max_distance = max_distance_m

    def _angles(self) -> Sequence[int]:
        forward = list(range(0, 181, self.angle_step))
        backward = list(range(180 - self.angle_step, -1, -self.angle_step))
        return forward + backward

    def _read_angle(self, angle: int) -> Optional[float]:
        readings = []
        for _ in range(self.reads_per_angle):
            distance = self.ultrasonic.read_distance(angle)
            if distance is not None:
                readings.append(min(self.max_distance, distance))
            time.sleep(0.005)
        return compute_median(readings)

    def sweep(self) -> List[Tuple[int, Optional[float]]]:
        samples: List[Tuple[int, Optional[float]]] = []
        for angle in self._angles():
            self.servo.set_angle(angle)
            time.sleep(self.settle_ms / 1000.0)
            distance = self._read_angle(angle)
            samples.append((angle, distance))
        return samples

    def shutdown(self) -> None:
        self.servo.cleanup()
