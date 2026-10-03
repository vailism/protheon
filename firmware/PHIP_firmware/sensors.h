#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>

// Fault bitmask flags — one bit per finger
#define FAULT_THUMB  0x01
#define FAULT_INDEX  0x02
#define FAULT_MIDDLE 0x04
#define FAULT_RING   0x08
#define FAULT_PINKY  0x10

// Struct to hold a single snapshot of all 5 flex sensors
struct SensorData {
    uint16_t thumb;
    uint16_t index;
    uint16_t middle;
    uint16_t ring;
    uint16_t pinky;
    uint8_t  faults;  // Bitmask of which sensors are out of range
    bool     isValid; // True only if faults == 0
};

// Initialize sensor pins
void sensors_init();

// Read all analog pins into the provided struct
// Returns true if ALL values are within safe expected ranges
bool sensors_read(SensorData* data);

#endif // SENSORS_H
