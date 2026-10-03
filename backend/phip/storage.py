"""
Protheon Session Management & Data Storage
"""

import sqlite3
import os
import time
import threading
import logging
import uuid
import json

from phip.state import global_bus

logger = logging.getLogger("protheon.storage")

class SessionManager:
    def __init__(self, db_path="logs/protheon_data.db", flush_interval=2.0):
        dirpath = os.path.dirname(db_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

        self.current_session_id = None
        self.is_recording = False
        self.is_paused = False

        self._buffer_telemetry = []
        self._buffer_events = []
        self._lock = threading.Lock()
        self._flush_interval = flush_interval

        self._running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="db-flush")
        self._flush_thread.start()

        # Subscribe to Event Bus
        global_bus.subscribe("SessionStarted", self._on_session_started)
        global_bus.subscribe("SessionStopped", self._on_session_stopped)
        global_bus.subscribe("SessionPaused", self._on_session_paused)
        global_bus.subscribe("SessionResumed", self._on_session_resumed)

    def _init_db(self):
        # Sessions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                duration INTEGER,
                calibration_profile TEXT,
                software_version TEXT,
                firmware_version TEXT,
                operating_mode TEXT,
                notes TEXT
            )
        """)
        # Telemetry table (maintaining compatibility with previous structure, but session_id is now TEXT)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp INTEGER,
                t_raw INTEGER, i_raw INTEGER, m_raw INTEGER, r_raw INTEGER, p_raw INTEGER,
                t_pct REAL, i_pct REAL, m_pct REAL, r_pct REAL, p_pct REAL,
                gesture TEXT,
                status INTEGER
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id)")
        
        # Events table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp INTEGER,
                event_type TEXT,
                payload TEXT
            )
        """)
        self.conn.commit()

    def start_session(self, name="New Session", mode="HARDWARE", calib_profile="default", version="0.2.0"):
        if self.is_recording:
            self.stop_session()
            
        session_id = str(uuid.uuid4())
        start_time = int(time.time() * 1000)
        
        self.conn.execute("""
            INSERT INTO sessions (id, name, start_time, end_time, duration, calibration_profile, software_version, operating_mode, notes)
            VALUES (?, ?, ?, 0, 0, ?, ?, ?, '')
        """, (session_id, name, start_time, calib_profile, version, mode))
        self.conn.commit()
        
        self.current_session_id = session_id
        self.is_recording = True
        self.is_paused = False
        
        logger.info(f"Started Session: {session_id}")
        global_bus.publish("SessionStarted", session_id=session_id)
        return session_id

    def stop_session(self):
        if not self.is_recording or not self.current_session_id:
            return
            
        self.flush()
        end_time = int(time.time() * 1000)
        
        # Calculate duration
        cursor = self.conn.cursor()
        cursor.execute("SELECT start_time FROM sessions WHERE id = ?", (self.current_session_id,))
        row = cursor.fetchone()
        duration = 0
        if row:
            duration = end_time - row[0]
            
        self.conn.execute("""
            UPDATE sessions SET end_time = ?, duration = ? WHERE id = ?
        """, (end_time, duration, self.current_session_id))
        self.conn.commit()
        
        old_id = self.current_session_id
        self.is_recording = False
        self.is_paused = False
        self.current_session_id = None
        
        logger.info(f"Stopped Session: {old_id}")
        global_bus.publish("SessionStopped", session_id=old_id)

    def pause_session(self):
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            global_bus.publish("SessionPaused", session_id=self.current_session_id)

    def resume_session(self):
        if self.is_recording and self.is_paused:
            self.is_paused = False
            global_bus.publish("SessionResumed", session_id=self.current_session_id)

    def rename_session(self, session_id, new_name):
        self.conn.execute("UPDATE sessions SET name = ? WHERE id = ?", (new_name, session_id))
        self.conn.commit()

    def add_notes(self, session_id, notes):
        self.conn.execute("UPDATE sessions SET notes = ? WHERE id = ?", (notes, session_id))
        self.conn.commit()

    def log_telemetry(self, timestamp, raw, pct, gesture, status=0):
        """Buffer a telemetry record."""
        if not self.is_recording or self.is_paused:
            return
            
        row = (
            self.current_session_id, timestamp,
            raw.get('thumb', 0), raw.get('index', 0), raw.get('middle', 0),
            raw.get('ring', 0), raw.get('pinky', 0),
            pct.get('thumb', 0), pct.get('index', 0), pct.get('middle', 0),
            pct.get('ring', 0), pct.get('pinky', 0),
            gesture, status,
        )
        with self._lock:
            self._buffer_telemetry.append(row)

    def log_event(self, event_type, payload_dict):
        if not self.is_recording:
            return
            
        timestamp = int(time.time() * 1000)
        row = (
            self.current_session_id,
            timestamp,
            event_type,
            json.dumps(payload_dict)
        )
        with self._lock:
            self._buffer_events.append(row)

    def _flush_loop(self):
        while self._running:
            time.sleep(self._flush_interval)
            self.flush()

    def flush(self):
        with self._lock:
            if not self._buffer_telemetry and not self._buffer_events:
                return
            t_batch = self._buffer_telemetry[:]
            e_batch = self._buffer_events[:]
            self._buffer_telemetry.clear()
            self._buffer_events.clear()

        try:
            if t_batch:
                self.conn.executemany("""
                    INSERT INTO telemetry (session_id, timestamp,
                        t_raw, i_raw, m_raw, r_raw, p_raw,
                        t_pct, i_pct, m_pct, r_pct, p_pct, gesture, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, t_batch)
            if e_batch:
                self.conn.executemany("""
                    INSERT INTO events (session_id, timestamp, event_type, payload)
                    VALUES (?, ?, ?, ?)
                """, e_batch)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database write error: {e}")

    def close(self):
        self.stop_session()
        self._running = False
        self.flush()
        self.conn.close()
        logger.info("SessionManager closed.")

    # Event handlers
    def _on_session_started(self, session_id):
        pass
    def _on_session_stopped(self, session_id):
        pass
    def _on_session_paused(self, session_id):
        pass
    def _on_session_resumed(self, session_id):
        pass
