#include "sensors.h"
#include "config.h"

// Per-finger validation (not just thumb)
static bool _check_range(uint16_t val) {
    return (val >= ADC_MIN_SAFE && val <= ADC_MAX_SAFE);
}

void sensors_init() {
    // Analog pins default to INPUT, but explicit is safer
    pinMode(PIN_FLEX_THUMB, INPUT);
    pinMode(PIN_FLEX_INDEX, INPUT);
    pinMode(PIN_FLEX_MIDDLE, INPUT);
    pinMode(PIN_FLEX_RING, INPUT);
    pinMode(PIN_FLEX_PINKY, INPUT);
}

bool sensors_read(SensorData* data) {
    data->thumb  = analogRead(PIN_FLEX_THUMB);
    data->index  = analogRead(PIN_FLEX_INDEX);
    data->middle = analogRead(PIN_FLEX_MIDDLE);
    data->ring   = analogRead(PIN_FLEX_RING);
    data->pinky  = analogRead(PIN_FLEX_PINKY);
    
    // Validate ALL five sensors, not just thumb
    data->faults = 0;
    if (!_check_range(data->thumb))  data->faults |= FAULT_THUMB;
    if (!_check_range(data->index))  data->faults |= FAULT_INDEX;
    if (!_check_range(data->middle)) data->faults |= FAULT_MIDDLE;
    if (!_check_range(data->ring))   data->faults |= FAULT_RING;
    if (!_check_range(data->pinky))  data->faults |= FAULT_PINKY;
    
    data->isValid = (data->faults == 0);
    return data->isValid;
}
