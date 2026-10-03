"""
PHIP Data Storage — SQLite telemetry logging

Batches inserts to avoid committing on every single sample (50Hz = 50 commits/sec
would cause severe I/O pressure). Instead, batches are flushed periodically.
"""

import sqlite3
import os
import time
import threading
import logging

logger = logging.getLogger("phip.storage")


class DataLogger:
    def __init__(self, db_path="logs/phip_data.db", flush_interval=2.0):
        """
        Args:
            db_path: Path to SQLite database file
            flush_interval: Seconds between batch commits
        """
        dirpath = os.path.dirname(db_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self.session_id = int(time.time())
        self._buffer = []
        self._lock = threading.Lock()
        self._flush_interval = flush_interval

        # Background flush thread
        self._running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="db-flush")
        self._flush_thread.start()

        logger.info(f"DataLogger session {self.session_id} → {db_path}")

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp INTEGER,
                t_raw INTEGER, i_raw INTEGER, m_raw INTEGER, r_raw INTEGER, p_raw INTEGER,
                t_pct REAL, i_pct REAL, m_pct REAL, r_pct REAL, p_pct REAL,
                gesture TEXT,
                status INTEGER
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session ON telemetry(session_id)
        """)
        self.conn.commit()

    def log_telemetry(self, timestamp, raw, pct, gesture, status=0):
        """Buffer a telemetry record for batch insertion."""
        row = (
            self.session_id, timestamp,
            raw.get('thumb', 0), raw.get('index', 0), raw.get('middle', 0),
            raw.get('ring', 0), raw.get('pinky', 0),
            pct.get('thumb', 0), pct.get('index', 0), pct.get('middle', 0),
            pct.get('ring', 0), pct.get('pinky', 0),
            gesture, status,
        )
        with self._lock:
            self._buffer.append(row)

    def _flush_loop(self):
        """Background thread that periodically commits buffered data."""
        while self._running:
            time.sleep(self._flush_interval)
            self.flush()

    def flush(self):
        """Write all buffered rows to disk."""
        with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        try:
            self.conn.executemany("""
                INSERT INTO telemetry (session_id, timestamp,
                    t_raw, i_raw, m_raw, r_raw, p_raw,
                    t_pct, i_pct, m_pct, r_pct, p_pct, gesture, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database write error: {e}")

    def close(self):
        """Flush remaining data and close database."""
        self._running = False
        self.flush()
        self.conn.close()
        logger.info("DataLogger closed.")
