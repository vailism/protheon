#include "servos.h"
#include "config.h"

static Servo srv[5];
static const uint8_t servo_pins[5] = {
    PIN_SERVO_THUMB, PIN_SERVO_INDEX, PIN_SERVO_MIDDLE,
    PIN_SERVO_RING, PIN_SERVO_PINKY
};

// Track last commanded angle per finger for telemetry reporting
static int current_angle[5] = {SERVO_MIN_ANGLE, SERVO_MIN_ANGLE, 
                                SERVO_MIN_ANGLE, SERVO_MIN_ANGLE, SERVO_MIN_ANGLE};

void servos_init() {
    for (int i = 0; i < 5; i++) {
        srv[i].attach(servo_pins[i]);
        srv[i].write(SERVO_MIN_ANGLE);
        current_angle[i] = SERVO_MIN_ANGLE;
    }
}

void servos_set(int finger_idx, int angle) {
    if (finger_idx < 0 || finger_idx > 4) return;
    
    // Hardware-level safety enforcement
    angle = constrain(angle, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
    current_angle[finger_idx] = angle;
    srv[finger_idx].write(angle);
}

int servos_get_angle(int finger_idx) {
    if (finger_idx < 0 || finger_idx > 4) return 0;
    return current_angle[finger_idx];
}

void servos_stop() {
    // Open hand position as safe default
    for (int i = 0; i < 5; i++) {
        servos_set(i, SERVO_MIN_ANGLE);
    }
}

void servos_detach_all() {
    for (int i = 0; i < 5; i++) {
        srv[i].detach();
    }
}
