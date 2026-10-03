"""
Protheon Session Replay Engine
"""

import sqlite3
import threading
import time
import logging

from phip.hardware import HardwareInterface

logger = logging.getLogger("protheon.replay")

class ReplayHardware(HardwareInterface):
    """
    Acts like physical hardware or the simulator, but streams data
    from a previously recorded session in SQLite.
    Crucially, any send_command attempts are explicitly ignored
    for safety to guarantee replay mode never moves real servos.
    """
    def __init__(self, db_path="logs/protheon_data.db", session_id=None):
        self.db_path = db_path
        self.session_id = session_id
        
        self._running = False
        self._thread = None
        self._callbacks = []
        self._state_callbacks = []
        self._playback_speed = 1.0
        
        self._packets_played = 0

    def set_session(self, session_id):
        self.session_id = session_id

    def set_speed(self, speed):
        self._playback_speed = speed

    def connect(self, port=None):
        if not self.session_id:
            logger.error("No session ID specified for replay.")
            return False
            
        self._running = True
        self._thread = threading.Thread(target=self._replay_loop, daemon=True, name="sim-replay")
        self._thread.start()
        
        logger.info(f"Replay started for session {self.session_id}")
        for cb in self._state_callbacks:
            cb("CONNECTED")
        return True

    def disconnect(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        for cb in self._state_callbacks:
            cb("DISCONNECTED")
        logger.info("Replay stopped.")

    @property
    def is_connected(self):
        return self._running

    @property
    def state(self):
        return "CONNECTED" if self._running else "DISCONNECTED"

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def add_state_callback(self, callback):
        self._state_callbacks.append(callback)

    def send_command(self, cmd_type, arg1=0, arg2=0):
        # EXPLICITLY BLOCKED FOR SAFETY
        logger.debug(f"Replay intercepted command: {cmd_type}")
        return True

    def send_stop(self):
        return True

    def send_ping(self):
        return True

    def get_stats(self):
        return {'received': self._packets_played, 'dropped': 0, 'state': self.state, 'port': 'REPLAY'}

    @staticmethod
    def list_ports():
        return ['REPLAY']

    def _replay_loop(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, t_raw, i_raw, m_raw, r_raw, p_raw, status
                FROM telemetry
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (self.session_id,))
            
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("No telemetry found to replay.")
                self.disconnect()
                return
                
            start_real_time = time.time()
            start_sim_time = rows[0][0]
            
            for row in rows:
                if not self._running:
                    break
                    
                target_sim_time = row[0]
                dt_sim = (target_sim_time - start_sim_time) / 1000.0
                dt_real = time.time() - start_real_time
                
                # Wait until we reach the target time (adjusted by speed)
                sleep_time = (dt_sim / self._playback_speed) - dt_real
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                data = {
                    'timestamp': row[0],
                    'sensors': {
                        'thumb': row[1],
                        'index': row[2],
                        'middle': row[3],
                        'ring': row[4],
                        'pinky': row[5],
                    },
                    'servos': {'thumb': 0, 'index': 0, 'middle': 0, 'ring': 0, 'pinky': 0}, # we don't necessarily replay servo commands
                    'status': row[6],
                    'estop': bool(row[6] & 0x80),
                    'sensor_faults': row[6] & 0x1F,
                }
                
                self._packets_played += 1
                for cb in self._callbacks:
                    try:
                        cb(data)
                    except Exception as e:
                        logger.error(f"Replay callback error: {e}")
                        
        except Exception as e:
            logger.error(f"Replay loop failed: {e}")
        finally:
            conn.close()
            self.disconnect()
