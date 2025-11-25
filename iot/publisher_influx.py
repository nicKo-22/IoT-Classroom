"""InfluxDB publisher supporting v1 and v2 servers."""
from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

from .grove_utils import chunked

LOGGER = logging.getLogger(__name__)


class InfluxPublisher:
    """Buffer samples and write them to InfluxDB with retries."""

    def __init__(self, config: Dict, storage, room: str, device: str) -> None:
        influx_cfg = config.get("influx", {})
        self.version = str(influx_cfg.get("version", "1"))
        self.measure_env = influx_cfg.get("measurement_env", "env_sensors")
        self.measure_radar = influx_cfg.get("measurement_radar", "radar")
        self.batch_size = influx_cfg.get("batch_size", 10)
        self.flush_interval = influx_cfg.get("flush_interval_s", 30)
        self.tags = {
            "room": influx_cfg.get("tags", {}).get("room") or room,
            "device": influx_cfg.get("tags", {}).get("device") or device,
        }
        self.storage = storage
        self.env_buffer: List[Dict] = []
        self.radar_buffer: List[Dict] = []
        self.client = None
        self.write_api = None
        self.bucket: Optional[str] = None
        if self.version == "2":
            self._setup_v2()
        else:
            self._setup_v1()

    def _setup_v1(self) -> None:
        try:
            from influxdb import InfluxDBClient

            host = os.getenv("INFLUX_HOST", "127.0.0.1")
            port = int(os.getenv("INFLUX_PORT", "8086"))
            username = os.getenv("INFLUX_USER")
            password = os.getenv("INFLUX_PASSWORD")
            database = os.getenv("INFLUX_DB", "iot_classroom")
            ssl = os.getenv("INFLUX_SSL", "0") in {"1", "true", "TRUE"}
            self.client = InfluxDBClient(
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                ssl=ssl,
                verify_ssl=ssl,
            )
            LOGGER.info("InfluxDB v1 client ready for %s:%s/%s", host, port, database)
        except Exception as exc:  # pragma: no cover
            LOGGER.error("Failed to initialize InfluxDB v1 client: %s", exc)
            self.client = None

    def _setup_v2(self) -> None:
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS

            url = os.getenv("INFLUX_URL")
            token = os.getenv("INFLUX_TOKEN")
            org = os.getenv("INFLUX_ORG")
            bucket = os.getenv("INFLUX_BUCKET")
            if not all([url, token, org, bucket]):
                raise ValueError("Missing InfluxDB v2 environment variables")
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = bucket
            LOGGER.info("InfluxDB v2 client ready for %s", url)
        except Exception as exc:  # pragma: no cover
            LOGGER.error("Failed to initialize InfluxDB v2 client: %s", exc)
            self.client = None

    def enqueue_env(self, sample: Dict) -> None:
        self.env_buffer.append(sample)

    def enqueue_radar(self, sample: Dict) -> None:
        self.radar_buffer.append(sample)

    def _fields_from_sample(self, sample: Dict) -> Dict:
        return {
            key: value
            for key, value in sample.items()
            if key not in {"timestamp", "room", "device"} and value is not None
        }

    def _point_from_sample(self, measurement: str, sample: Dict) -> Dict:
        return {
            "measurement": measurement,
            "time": sample.get("timestamp"),
            "tags": self.tags,
            "fields": self._fields_from_sample(sample),
        }

    def _write_with_retry(self, writer, payload) -> bool:
        for attempt in range(3):
            try:
                writer(payload)
                return True
            except Exception as exc:  # pragma: no cover
                delay = 2 ** attempt
                LOGGER.warning(
                    "Influx write failed (attempt %s): %s", attempt + 1, exc, exc_info=True
                )
                time.sleep(delay)
        return False

    def _write_v1(self, measurement: str, samples: List[Dict]) -> bool:
        if not self.client:
            return False
        payload = [self._point_from_sample(measurement, sample) for sample in samples]

        def _writer(points):
            self.client.write_points(points)

        return self._write_with_retry(_writer, payload)

    def _write_v2(self, measurement: str, samples: List[Dict]) -> bool:
        if not self.client or not self.write_api:
            return False

        def _writer(_payload):
            from influxdb_client import Point  # pragma: no cover
            from influxdb_client.client.write_api import SYNCHRONOUS  # noqa: F401

            points = []
            for sample in samples:
                point = Point(measurement).time(sample.get("timestamp"))
                for tag_key, tag_value in self.tags.items():
                    if tag_value:
                        point = point.tag(tag_key, tag_value)
                for field_key, field_value in self._fields_from_sample(sample).items():
                    point = point.field(field_key, field_value)
                points.append(point)
            self.write_api.write(bucket=self.bucket, record=points)

        return self._write_with_retry(_writer, samples)

    def flush(self) -> None:
        writer = self._write_v2 if self.version == "2" else self._write_v1
        if self.env_buffer:
            self._flush_buffer(writer, "env", self.measure_env, self.env_buffer)
            self.env_buffer.clear()
        if self.radar_buffer:
            self._flush_buffer(writer, "radar", self.measure_radar, self.radar_buffer)
            self.radar_buffer.clear()
        self._replay_pending(writer, "env", self.measure_env)
        self._replay_pending(writer, "radar", self.measure_radar)

    def _flush_buffer(
        self, writer, category: str, measurement: str, buffer: List[Dict]
    ) -> None:
        for batch in chunked(buffer, self.batch_size):
            if not writer(measurement, batch):
                for sample in batch:
                    self.storage.enqueue_pending(category, sample)
                LOGGER.warning(
                    "Stored %s %s samples for retry in SQLite", len(batch), category
                )
                break

    def _replay_pending(self, writer, category: str, measurement: str) -> None:
        while True:
            pending = self.storage.dequeue_pending(category, self.batch_size)
            if not pending:
                break
            ids = [row_id for row_id, _ in pending]
            samples = [sample for _, sample in pending]
            if writer(measurement, samples):
                self.storage.delete_pending(ids)
                LOGGER.info("Replayed %s queued %s samples", len(ids), category)
            else:
                LOGGER.warning("Retry for queued %s samples failed; will retry later", category)
                break
