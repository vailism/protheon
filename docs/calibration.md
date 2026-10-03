# Sensor Calibration

Calibration maps the raw resistance range of physical flex sensors (read via ADC) into a normalized 0-100% space.

## Process
1. **Open Calibration:** The user fully extends all fingers. The ADC value for each finger is recorded as the `min` boundary.
2. **Closed Calibration:** The user clenches a tight fist. The ADC value is recorded as the `max` boundary.

## Normalization
The backend calculates:
`percentage = ((raw - min) / (max - min)) * 100.0`

The result is strictly clamped to `[0.0, 100.0]`.

## Profile Storage
Profiles are saved in JSON format under `profiles/`.

```json
{
  "min": {
    "thumb": 300,
    "index": 315
  },
  "max": {
    "thumb": 650,
    "index": 680
  },
  "calibrated": true
}
```

## Failure Conditions
- **min == max**: Prevents division by zero. Clamps to 0%.
- **Inverted Polarity**: Automatically handled if `max < min`.
- **Tiny Range**: Generates UI warnings, often indicating disconnected sensors or short circuits.
