"""
Protheon Analytics Engine
"""

import sqlite3
import numpy as np
from collections import Counter
import logging

logger = logging.getLogger("protheon.analytics")

class AnalyticsEngine:
    def __init__(self, db_path="logs/protheon_data.db"):
        self.db_path = db_path

    def analyze_session(self, session_id):
        """Generates comprehensive metrics for a given session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Fetch basic session metadata
            cursor.execute("SELECT start_time, end_time, duration FROM sessions WHERE id = ?", (session_id,))
            meta = cursor.fetchone()
            if not meta:
                return None
                
            runtime_ms = meta[2] if meta[2] > 0 else 0
            
            # Fetch all telemetry
            cursor.execute("""
                SELECT timestamp, t_pct, i_pct, m_pct, r_pct, p_pct, gesture, status
                FROM telemetry
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return {"error": "No telemetry data found for session."}
                
            total_samples = len(rows)
            
            # Unpack data
            timestamps = np.array([r[0] for r in rows])
            sensors = {
                'thumb': np.array([r[1] for r in rows]),
                'index': np.array([r[2] for r in rows]),
                'middle': np.array([r[3] for r in rows]),
                'ring': np.array([r[4] for r in rows]),
                'pinky': np.array([r[5] for r in rows]),
            }
            gestures = [r[6] for r in rows]
            statuses = [r[7] for r in rows]
            
            # 1. Sensor Metrics
            sensor_metrics = {}
            for finger, data in sensors.items():
                sensor_metrics[finger] = {
                    "min": float(np.min(data)),
                    "max": float(np.max(data)),
                    "mean": float(np.mean(data)),
                    "median": float(np.median(data)),
                    "std_dev": float(np.std(data)),
                    "range": float(np.max(data) - np.min(data)),
                }
            
            # 2. Gesture Metrics
            gesture_counts = Counter(gestures)
            gesture_metrics = {
                "distribution": dict(gesture_counts),
                "total_transitions": sum(1 for i in range(1, len(gestures)) if gestures[i] != gestures[i-1]),
            }
            
            # 3. System Metrics
            estops = sum(1 for s in statuses if (s & 0x80))
            sys_metrics = {
                "runtime_sec": runtime_ms / 1000.0,
                "total_samples": total_samples,
                "avg_sample_rate_hz": total_samples / (runtime_ms / 1000.0) if runtime_ms > 0 else 0.0,
                "emergency_stops": estops,
            }
            
            return {
                "sensor_metrics": sensor_metrics,
                "gesture_metrics": gesture_metrics,
                "system_metrics": sys_metrics
            }
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
