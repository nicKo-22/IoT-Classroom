"""IoT Classroom entrypoint handling sensors, radar, and publishing."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from iot.grove_utils import (
    LoggingConfig,
    env_flag,
    load_yaml_config,
    register_signal_handlers,
    setup_logging,
)
from iot.publisher_influx import InfluxPublisher
from iot.radar_occupancy import RadarOccupancy
from iot.scheduler import IoTScheduler
from iot.sensor_dht import DHTSensor
from iot.sensor_light import LightSensor
from iot.sensor_sound import SoundSensor
from iot.sensor_gas import GasSensor
from iot.sensor_ultrasonic import UltrasonicSensor
from iot.servo_radar import RadarScanner, ServoController
from iot.simulate import EnvSimulator, RadarSimulator
from iot.storage_sqlite import SQLiteStorage

LOGGER = logging.getLogger("iot.main")


def iso_timestamp() -> str:
    """Return UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def build_sample(room: str, device: str, fields: dict) -> dict:
    sample = dict(fields)
    sample["room"] = room
    sample["device"] = device
    sample["timestamp"] = iso_timestamp()
    return sample


def main() -> None:
    load_dotenv()
    config = load_yaml_config("config.yaml")
    logging_cfg = LoggingConfig(**config.get("logging", {}))
    setup_logging(logging_cfg)

    room = config.get("room", "lab")
    device = config.get("device", "raspi")
    simulate_mode = config.get("simulate", False) or env_flag("SIMULATE", False)
    ports = config.get("ports", {})
    sampling = config.get("sampling", {})
    radar_cfg = config.get("radar", {})
    storage_cfg = config.get("storage", {})

    LOGGER.info("Simulation mode: %s", simulate_mode)

    storage = SQLiteStorage(
        db_path=storage_cfg.get("sqlite_path", "data/metrics.db"),
        retention_days=storage_cfg.get("retention_days", 90),
    )

    env_sim = EnvSimulator() if simulate_mode else None
    radar_sim = RadarSimulator(sectors=radar_cfg.get("sectors", 6)) if simulate_mode else None

    adc_address = int(ports.get("adc_address", 0x04))

    dht_sensor = DHTSensor(
        port=ports.get("dht", "D5"),
        sensor_type=str(config.get("dht", {}).get("sensor_type", "22")),
        simulate_mode=simulate_mode,
        simulator=env_sim.temperature_humidity if env_sim else None,
    )
    light_sensor = LightSensor(
        port=ports.get("light", "A0"),
        adc_address=adc_address,
        simulate_mode=simulate_mode,
        simulator=env_sim.light if env_sim else None,
    )
    sound_sensor = SoundSensor(
        port=ports.get("sound", "A1"),
        adc_address=adc_address,
        simulate_mode=simulate_mode,
        simulator=env_sim.sound if env_sim else None,
        moving_average_samples=int(sampling.get("sound_window", 3)),
    )
    gas_sensor = GasSensor(
        port=ports.get("gas", "A2"),
        adc_address=adc_address,
        simulate_mode=simulate_mode,
        simulator=env_sim.gas if env_sim else None,
    )
    ultrasonic_sensor = UltrasonicSensor(
        port=ports.get("ultrasonic", "D16"),
        simulate_mode=simulate_mode,
        simulator=radar_sim,
        timeout_ms=int(radar_cfg.get("timeout_ms", 25)),
    )
    servo_controller = ServoController(
        port=ports.get("servo_pwm", "D18"),
        min_duty=float(radar_cfg.get("servo_min_duty", 2.5)),
        max_duty=float(radar_cfg.get("servo_max_duty", 12.5)),
        simulate_mode=simulate_mode,
    )
    radar_scanner = RadarScanner(
        servo=servo_controller,
        ultrasonic=ultrasonic_sensor,
        angle_step=int(radar_cfg.get("angle_step_deg", 5)),
        settle_ms=int(radar_cfg.get("settle_ms", 100)),
        reads_per_angle=int(radar_cfg.get("reads_per_angle", 3)),
        max_distance_m=float(radar_cfg.get("max_distance_m", 4.0)),
    )
    occupancy = RadarOccupancy(
        sectors=int(radar_cfg.get("sectors", 6)),
        object_threshold_m=float(radar_cfg.get("object_threshold_m", 1.5)),
    )

    publisher = InfluxPublisher(config=config, storage=storage, room=room, device=device)

    scheduler = IoTScheduler()
    stop_event = threading.Event()

    def _handle_signal(signum, _frame) -> None:
        LOGGER.info("Signal %s received, shutting down", signum)
        stop_event.set()

    register_signal_handlers(_handle_signal)

    def job_temp_humidity() -> None:
        sample = dht_sensor.read()
        if not sample:
            return
        payload = build_sample(room, device, sample)
        storage.insert_env(payload)
        publisher.enqueue_env(payload)

    def job_light() -> None:
        sample = light_sensor.read()
        if not sample:
            return
        payload = build_sample(room, device, sample)
        storage.insert_env(payload)
        publisher.enqueue_env(payload)

    def job_sound() -> None:
        sample = sound_sensor.read()
        payload = build_sample(room, device, sample)
        storage.insert_env(payload)
        publisher.enqueue_env(payload)

    def job_gas() -> None:
        sample = gas_sensor.read()
        if not sample:
            return
        payload = build_sample(room, device, sample)
        storage.insert_env(payload)
        publisher.enqueue_env(payload)

    def job_radar() -> None:
        samples = radar_scanner.sweep()
        metrics = occupancy.process(samples)
        payload = build_sample(room, device, metrics)
        storage.insert_radar(payload)
        publisher.enqueue_radar(payload)

    def job_flush() -> None:
        publisher.flush()
        storage.purge_old()

    scheduler.add_interval_job(
        "temp_hum", int(sampling.get("temperature_humidity_s", 10)), job_temp_humidity
    )
    scheduler.add_interval_job("light", int(sampling.get("light_s", 5)), job_light)
    scheduler.add_interval_job("sound", int(sampling.get("sound_s", 1)), job_sound)
    scheduler.add_interval_job("gas", int(sampling.get("gas_s", 5)), job_gas)
    scheduler.add_interval_job("radar", int(sampling.get("radar_s", 5)), job_radar)
    scheduler.add_interval_job("flush", int(sampling.get("flush_s", 15)), job_flush)

    scheduler.start()
    publisher.flush()

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        LOGGER.info("Keyboard interrupt received")
    finally:
        stop_event.set()
        scheduler.shutdown()
        radar_scanner.shutdown()
        publisher.flush()
        storage.close()


if __name__ == "__main__":
    main()
