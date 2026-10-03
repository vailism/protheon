#ifndef CONFIG_H
#define CONFIG_H

// =============================================================
// PHIP Hardware Configuration
// =============================================================
// ⚠️  ASSUMPTION: These pin assignments must match YOUR wiring.
//     If your flex sensor for "thumb" is on A3 instead of A0,
//     change it here. Getting this wrong will command the wrong
//     finger's servo.
// =============================================================

// ---------------------------------------------------------
// PIN DEFINITIONS — FLEX SENSORS (Analog Input)
// ---------------------------------------------------------
#define PIN_FLEX_THUMB  A0
#define PIN_FLEX_INDEX  A1
#define PIN_FLEX_MIDDLE A2
#define PIN_FLEX_RING   A3
#define PIN_FLEX_PINKY  A4

// ---------------------------------------------------------
// PIN DEFINITIONS — SERVOS (Digital PWM Output)
// ---------------------------------------------------------
// Note: The Servo library uses Timer1 internally.
//       Pins 9,10 lose analogWrite() PWM capability,
//       which is fine since we use them as servo outputs.
#define PIN_SERVO_THUMB  3
#define PIN_SERVO_INDEX  5
#define PIN_SERVO_MIDDLE 6
#define PIN_SERVO_RING   9
#define PIN_SERVO_PINKY  10

// ---------------------------------------------------------
// SERIAL COMMUNICATION
// ---------------------------------------------------------
#define SERIAL_BAUD_RATE 115200

// ---------------------------------------------------------
// TIMING
// ---------------------------------------------------------
// Telemetry send interval (20ms = 50Hz)
#define SENSOR_READ_DELAY_MS 20

// Communication timeout: if no command received from host
// within this period, enter safe state. Set to 0 to disable.
// 3000ms = 3 seconds without any PING or command → safe stop.
#define COMMS_TIMEOUT_MS 3000

// ---------------------------------------------------------
// SAFETY LIMITS — ADC
// ---------------------------------------------------------
// A disconnected/shorted flex sensor typically reads 0 or 1023.
// Values outside this range are flagged as faults.
#define ADC_MIN_SAFE 10
#define ADC_MAX_SAFE 1010

// ---------------------------------------------------------
// SAFETY LIMITS — SERVOS
// ---------------------------------------------------------
// ⚠️  IMPORTANT: 0-180 is the electrical range.
//     Your mechanical hand may be damaged by extreme angles.
//     Reduce these limits to match your physical mechanism.
//     Start conservative (e.g., 10-170) and widen after testing.
#define SERVO_MIN_ANGLE 0
#define SERVO_MAX_ANGLE 180

#endif // CONFIG_H
