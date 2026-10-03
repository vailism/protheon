"""
Protheon Data Export Subsystem
"""

import sqlite3
import csv
import json
import os
import zipfile
import logging

logger = logging.getLogger("protheon.export")

class DataExporter:
    def __init__(self, db_path="logs/protheon_data.db"):
        self.db_path = db_path

    def export_session_csv(self, session_id, out_dir="exports"):
        os.makedirs(out_dir, exist_ok=True)
        csv_path = os.path.join(out_dir, f"session_{session_id}_telemetry.csv")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, t_raw, i_raw, m_raw, r_raw, p_raw,
                       t_pct, i_pct, m_pct, r_pct, p_pct, gesture, status
                FROM telemetry
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            rows = cursor.fetchall()
            
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "thumb_raw", "index_raw", "middle_raw", "ring_raw", "pinky_raw",
                    "thumb_percent", "index_percent", "middle_percent", "ring_percent", "pinky_percent",
                    "gesture", "status"
                ])
                for row in rows:
                    writer.writerow(row)
                    
            logger.info(f"Exported telemetry CSV for session {session_id} to {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return None
        finally:
            conn.close()

    def export_session_metadata(self, session_id, out_dir="exports"):
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, f"session_{session_id}_metadata.json")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Metadata
            cursor.execute("""
                SELECT id, name, start_time, end_time, duration, calibration_profile, 
                       software_version, firmware_version, operating_mode, notes
                FROM sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            metadata = {
                "id": row[0],
                "name": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "duration": row[4],
                "calibration_profile": row[5],
                "software_version": row[6],
                "firmware_version": row[7],
                "operating_mode": row[8],
                "notes": row[9]
            }
            
            # Events
            cursor.execute("SELECT timestamp, event_type, payload FROM events WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
            events = []
            for ev_row in cursor.fetchall():
                events.append({
                    "timestamp": ev_row[0],
                    "type": ev_row[1],
                    "payload": json.loads(ev_row[2])
                })
            
            metadata["events"] = events
            
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return json_path
        except Exception as e:
            logger.error(f"Failed to export Metadata: {e}")
            return None
        finally:
            conn.close()

    def export_session_zip(self, session_id, out_dir="exports"):
        csv_path = self.export_session_csv(session_id, out_dir)
        json_path = self.export_session_metadata(session_id, out_dir)
        
        if not csv_path or not json_path:
            return None
            
        zip_path = os.path.join(out_dir, f"experiment_{session_id}.zip")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(csv_path, os.path.basename(csv_path))
                zipf.write(json_path, os.path.basename(json_path))
                
            # Cleanup intermediate files
            os.remove(csv_path)
            os.remove(json_path)
            
            logger.info(f"Exported complete ZIP package for session {session_id}")
            return zip_path
        except Exception as e:
            logger.error(f"Failed to create ZIP: {e}")
            return None
