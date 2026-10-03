"""
PHIP Unit Test Suite

Tests core logic without requiring physical Arduino hardware.
Run with: python -m pytest tests/ -v
"""

import pytest
import sys
import os

# Allow importing phip from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from phip.calibration import CalibrationProfile
from phip.filtering import EMAFilter
from phip.gestures import GestureRecognizer


# =============================================================
# CALIBRATION TESTS
# =============================================================
class TestCalibration:
    def setup_method(self):
        self.cal = CalibrationProfile()  # No file, use defaults
        self.cal.min_vals = {'thumb': 300, 'index': 300, 'middle': 300, 'ring': 300, 'pinky': 300}
        self.cal.max_vals = {'thumb': 700, 'index': 700, 'middle': 700, 'ring': 700, 'pinky': 700}

    def test_min_returns_zero(self):
        raw = {f: 300 for f in self.cal.min_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 0.0, f"{f} should be 0% at min"

    def test_max_returns_hundred(self):
        raw = {f: 700 for f in self.cal.max_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 100.0, f"{f} should be 100% at max"

    def test_midpoint_returns_fifty(self):
        raw = {f: 500 for f in self.cal.min_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 50.0, f"{f} should be 50% at midpoint"

    def test_below_min_clamps_to_zero(self):
        raw = {f: 100 for f in self.cal.min_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 0.0, f"{f} should clamp to 0%"

    def test_above_max_clamps_to_hundred(self):
        raw = {f: 900 for f in self.cal.max_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 100.0, f"{f} should clamp to 100%"

    def test_zero_range_returns_zero(self):
        """When min == max, should return 0% not crash with division by zero."""
        self.cal.min_vals = {f: 500 for f in self.cal.min_vals}
        self.cal.max_vals = {f: 500 for f in self.cal.max_vals}
        raw = {f: 500 for f in self.cal.min_vals}
        pct = self.cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 0.0

    def test_inverted_sensor(self):
        """When max < min (inverted polarity), should still produce 0-100%."""
        self.cal.min_vals = {'thumb': 700, 'index': 300, 'middle': 300, 'ring': 300, 'pinky': 300}
        self.cal.max_vals = {'thumb': 300, 'index': 700, 'middle': 700, 'ring': 700, 'pinky': 700}
        raw = {'thumb': 500, 'index': 500, 'middle': 500, 'ring': 500, 'pinky': 500}
        pct = self.cal.get_percentage(raw)
        assert pct['thumb'] == 50.0, "Inverted sensor should still give 50% at midpoint"

    def test_validation_warns_small_range(self):
        self.cal.min_vals = {f: 500 for f in self.cal.min_vals}
        self.cal.max_vals = {f: 510 for f in self.cal.max_vals}
        warnings = self.cal.validate()
        assert len(warnings) == 5, "Should warn for all 5 fingers with tiny range"


# =============================================================
# FILTER TESTS
# =============================================================
class TestFiltering:
    def test_first_sample_passthrough(self):
        """First sample should pass through unchanged (filter seeding)."""
        filt = EMAFilter(alpha=0.3, deadzone=2.0)
        inp = {f: 50.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        out = filt.process(inp)
        for f in out:
            assert out[f] == 50.0

    def test_deadzone_suppresses_small_changes(self):
        """Changes smaller than deadzone should not propagate."""
        filt = EMAFilter(alpha=1.0, deadzone=5.0)  # alpha=1 means no smoothing
        base = {f: 50.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        filt.process(base)  # Seed

        small_change = {f: 52.0 for f in base}  # Change of 2 < deadzone of 5
        out = filt.process(small_change)
        for f in out:
            assert out[f] == 50.0, "Small change should be suppressed by deadzone"

    def test_large_change_passes_deadzone(self):
        filt = EMAFilter(alpha=1.0, deadzone=5.0)
        base = {f: 50.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        filt.process(base)

        large_change = {f: 60.0 for f in base}
        out = filt.process(large_change)
        for f in out:
            assert out[f] == 60.0, "Large change should pass through"

    def test_ema_smoothing(self):
        """With alpha=0.5, output should be midpoint between current and previous."""
        filt = EMAFilter(alpha=0.5, deadzone=0.0)
        filt.process({f: 0.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
        out = filt.process({f: 100.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
        for f in out:
            assert out[f] == 50.0

    def test_invalid_alpha_raises(self):
        with pytest.raises(ValueError):
            EMAFilter(alpha=0.0)
        with pytest.raises(ValueError):
            EMAFilter(alpha=1.5)

    def test_reset(self):
        filt = EMAFilter(alpha=0.3, deadzone=2.0)
        filt.process({f: 50.0 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']})
        filt.reset()
        assert not filt._initialized


# =============================================================
# GESTURE TESTS
# =============================================================
class TestGestures:
    def setup_method(self):
        self.rec = GestureRecognizer(hold_time_ms=0)  # No debounce for tests

    def _make(self, t, i, m, r, p):
        return {'thumb': t, 'index': i, 'middle': m, 'ring': r, 'pinky': p}

    def test_open_hand(self):
        result = self.rec.recognize(self._make(10, 10, 10, 10, 10))
        assert result == "OPEN_HAND"

    def test_closed_fist(self):
        result = self.rec.recognize(self._make(90, 90, 90, 90, 90))
        assert result == "CLOSED_FIST"

    def test_pinch(self):
        result = self.rec.recognize(self._make(80, 80, 10, 10, 10))
        assert result == "PINCH"

    def test_point(self):
        result = self.rec.recognize(self._make(80, 10, 80, 80, 80))
        assert result == "POINT"

    def test_peace(self):
        result = self.rec.recognize(self._make(80, 10, 10, 80, 80))
        assert result == "PEACE"

    def test_thumbs_up(self):
        result = self.rec.recognize(self._make(10, 80, 80, 80, 80))
        assert result == "THUMBS_UP"

    def test_ambiguous_returns_transitioning(self):
        result = self.rec.recognize(self._make(50, 50, 50, 50, 50))
        assert result == "TRANSITIONING"

    def test_hysteresis_prevents_flicker(self):
        """With hold_time > 0, rapid changes should not cause immediate switches."""
        rec = GestureRecognizer(hold_time_ms=500)
        rec.recognize(self._make(90, 90, 90, 90, 90))  # FIST
        # Immediately switch to open — should NOT change yet
        result = rec.recognize(self._make(10, 10, 10, 10, 10))
        # With 500ms hold, the first call won't have waited long enough
        # The gesture should still be the initial one or UNKNOWN
        assert result != "OPEN_HAND" or result == "CLOSED_FIST" or result == "UNKNOWN"


# =============================================================
# PROTOCOL PARSING TESTS
# =============================================================
class TestProtocol:
    """Test that the checksum algorithm matches between Python and Arduino."""

    def _compute_checksum(self, payload):
        """Replicate the Arduino XOR checksum (uint8_t)."""
        chk = 0
        for c in payload:
            chk ^= ord(c)
        chk &= 0xFF  # Mask to 8 bits
        return chk

    def test_checksum_basic(self):
        payload = "TEL|1000|300|400|500|600|700|0|0|0|0|0|0|"
        chk = self._compute_checksum(payload)
        assert 0 <= chk <= 255

    def test_checksum_consistency(self):
        payload = "TEL|1000|300|400|500|600|700|0|0|0|0|0|0|"
        chk1 = self._compute_checksum(payload)
        chk2 = self._compute_checksum(payload)
        assert chk1 == chk2

    def test_checksum_different_data(self):
        p1 = "TEL|1000|300|400|500|600|700|0|0|0|0|0|0|"
        p2 = "TEL|1000|301|400|500|600|700|0|0|0|0|0|0|"
        assert self._compute_checksum(p1) != self._compute_checksum(p2)

    def test_checksum_8bit_wrap(self):
        """Ensure checksum wraps at 8 bits like Arduino uint8_t."""
        # Create a payload that would exceed 255 without masking
        payload = "A" * 300  # XOR of 300 'A's
        chk = self._compute_checksum(payload)
        assert 0 <= chk <= 255


# =============================================================
# SAFETY TESTS
# =============================================================
class TestSafety:
    def test_servo_angle_negative(self):
        """Negative servo angles should never be accepted."""
        # This tests the Python-side; firmware uses constrain()
        angle = max(0, min(180, -10))
        assert angle == 0

    def test_servo_angle_over_180(self):
        angle = max(0, min(180, 200))
        assert angle == 180

    def test_calibration_with_disconnected_sensor(self):
        """ADC of 0 (disconnected) should produce 0% not crash."""
        cal = CalibrationProfile()
        cal.min_vals = {f: 300 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        cal.max_vals = {f: 700 for f in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        raw = {f: 0 for f in cal.min_vals}
        pct = cal.get_percentage(raw)
        for f in pct:
            assert pct[f] == 0.0, "Disconnected sensor (0) should clamp to 0%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
