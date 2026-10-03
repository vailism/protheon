"""
Protheon ML Lab (Advisory Layer)
"""

import sqlite3
import numpy as np
import logging
import time
from collections import Counter

logger = logging.getLogger("protheon.ml")

class MLAgent:
    """
    A lightweight, non-destructive ML agent using k-NN for gesture classification.
    Runs strictly in advisory mode, cross-checking the rule-based engine.
    """
    def __init__(self, db_path="logs/protheon_data.db"):
        self.db_path = db_path
        self.is_trained = False
        self.X_train = []
        self.y_train = []
        
        # Hyperparameters
        self.k = 3

    def train_on_session(self, session_id):
        """Train k-NN on a recorded session where gestures were labeled."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t_pct, i_pct, m_pct, r_pct, p_pct, gesture
                FROM telemetry
                WHERE session_id = ? AND gesture != 'UNKNOWN' AND gesture != 'TRANSITIONING'
            """, (session_id,))
            
            rows = cursor.fetchall()
            
            if not rows or len(rows) < 10:
                return False, "Not enough labeled data in session."
                
            self.X_train = np.array([[r[0], r[1], r[2], r[3], r[4]] for r in rows])
            self.y_train = [r[5] for r in rows]
            self.is_trained = True
            
            logger.info(f"Trained ML agent on {len(self.X_train)} samples from session {session_id}.")
            return True, f"Trained on {len(self.X_train)} samples. Gestures: {list(set(self.y_train))}"
            
        except Exception as e:
            logger.error(f"ML training failed: {e}")
            return False, str(e)
        finally:
            conn.close()

    def predict(self, percentages):
        """Predict gesture using k-NN."""
        if not self.is_trained or len(self.X_train) == 0:
            return "UNKNOWN", 0.0
            
        # Extract features
        x = np.array([
            percentages.get('thumb', 0),
            percentages.get('index', 0),
            percentages.get('middle', 0),
            percentages.get('ring', 0),
            percentages.get('pinky', 0)
        ])
        
        # Calculate Euclidean distances
        distances = np.linalg.norm(self.X_train - x, axis=1)
        
        # Get k nearest neighbors
        nearest_indices = np.argsort(distances)[:self.k]
        nearest_labels = [self.y_train[i] for i in nearest_indices]
        
        # Majority vote
        vote_counts = Counter(nearest_labels)
        prediction = vote_counts.most_common(1)[0][0]
        confidence = vote_counts[prediction] / self.k
        
        return prediction, confidence
