"""
Protheon Experiment & Trial Engine
"""

import time
import logging
from phip.state import global_bus

logger = logging.getLogger("protheon.experiment")

class ExperimentRunner:
    def __init__(self):
        self.is_running = False
        self.trials = []
        self.current_trial = 0
        self.results = []
        
        self._target_gesture = None
        self._trial_start_time = 0
        self._callback = None

    def load_experiment(self, trials):
        """
        trials = [{'gesture': 'PINCH', 'hold_time': 2.0}, ...]
        """
        self.trials = trials
        self.current_trial = 0
        self.results = []

    def start(self, update_callback):
        if not self.trials:
            return False
            
        self.is_running = True
        self._callback = update_callback
        self._start_next_trial()
        return True

    def _start_next_trial(self):
        if self.current_trial >= len(self.trials):
            self.is_running = False
            self._callback({"status": "COMPLETE", "results": self.results})
            return
            
        trial = self.trials[self.current_trial]
        self._target_gesture = trial['gesture']
        self._trial_start_time = time.time()
        
        self._callback({
            "status": "WAITING",
            "trial_idx": self.current_trial + 1,
            "total_trials": len(self.trials),
            "target": self._target_gesture,
            "instruction": f"Perform gesture: {self._target_gesture}"
        })

    def process_telemetry(self, gesture):
        if not self.is_running:
            return
            
        if gesture == self._target_gesture:
            reaction_time = time.time() - self._trial_start_time
            
            self.results.append({
                "trial": self.current_trial + 1,
                "target": self._target_gesture,
                "reaction_time": reaction_time,
                "success": True
            })
            
            logger.info(f"Trial {self.current_trial + 1} complete. RT: {reaction_time:.3f}s")
            
            self._callback({
                "status": "SUCCESS",
                "reaction_time": reaction_time,
                "target": self._target_gesture
            })
            
            self.current_trial += 1
            # Add a small delay between trials
            # For a real UI, this delay should be non-blocking. Here it's a simplification.
            # We just move to the next trial.
            self._start_next_trial()

    def abort(self):
        self.is_running = False
        self._callback({"status": "ABORTED", "results": self.results})
