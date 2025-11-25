"""SQLite based persistence for IoT metrics."""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

LOGGER = logging.getLogger(__name__)


class SQLiteStorage:
    """Persist samples locally when the network is unavailable."""

    def __init__(self, db_path: str, retention_days: int = 90) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._create_tables()

    def _create_tables(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS env_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    temperature_c REAL,
                    humidity_pct REAL,
                    light_adc REAL,
                    sound_adc REAL,
                    sound_digital INTEGER,
                    gas_adc REAL,
                    room TEXT,
                    device TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS radar_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    sector_payload TEXT NOT NULL,
                    min_distance_m REAL,
                    objects_count INTEGER,
                    room TEXT,
                    device TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS publish_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def insert_env(self, sample: Dict) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO env_samples (
                    ts, temperature_c, humidity_pct, light_adc,
                    sound_adc, sound_digital, gas_adc, room, device
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample.get("timestamp"),
                    sample.get("temperature_c"),
                    sample.get("humidity_pct"),
                    sample.get("light_adc"),
                    sample.get("sound_adc"),
                    int(sample.get("sound_digital")) if sample.get("sound_digital") is not None else None,
                    sample.get("gas_adc"),
                    sample.get("room"),
                    sample.get("device"),
                ),
            )

    def insert_radar(self, sample: Dict) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO radar_samples (
                    ts, sector_payload, min_distance_m, objects_count, room, device
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    sample.get("timestamp"),
                    json.dumps({k: v for k, v in sample.items() if k.startswith("sector_")}),
                    sample.get("min_distance_m"),
                    sample.get("objects_count"),
                    sample.get("room"),
                    sample.get("device"),
                ),
            )

    def purge_old(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "DELETE FROM env_samples WHERE ts < datetime('now', ?)",
                (f"-{self.retention_days} days",),
            )
            self._conn.execute(
                "DELETE FROM radar_samples WHERE ts < datetime('now', ?)",
                (f"-{self.retention_days} days",),
            )

    def enqueue_pending(self, category: str, sample: Dict) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO publish_queue (category, payload) VALUES (?, ?)",
                (category, json.dumps(sample)),
            )

    def dequeue_pending(
        self, category: str, limit: int = 50
    ) -> List[Tuple[int, Dict]]:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT id, payload FROM publish_queue WHERE category = ? ORDER BY id LIMIT ?",
                (category, limit),
            )
            rows = cursor.fetchall()
        parsed: List[Tuple[int, Dict]] = []
        for row_id, payload in rows:
            parsed.append((row_id, json.loads(payload)))
        return parsed

    def delete_pending(self, ids: Sequence[int]) -> None:
        if not ids:
            return
        with self._lock, self._conn:
            self._conn.executemany(
                "DELETE FROM publish_queue WHERE id = ?", [(row_id,) for row_id in ids]
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()
