// ============================================================
// PHIP Firmware — Prosthetic Hand Intelligence Platform
// Target: Arduino Uno R3 (ATmega328P, 2KB SRAM, 32KB Flash)
// ============================================================
// 
// This firmware is responsible ONLY for:
//   1. Reading 5 flex sensors at a fixed rate
//   2. Transmitting telemetry over serial
//   3. Receiving and executing validated servo commands
//   4. Enforcing hardware safety limits at all times
//   5. Entering safe state on communication timeout
//
// All complex processing (filtering, calibration, gesture
// recognition, ML, UI) runs on the host PC.
// ============================================================

#include "config.h"
#include "sensors.h"
#include "servos.h"

// ---- State ----
SensorData currentSensors;
unsigned long lastReadTime = 0;
unsigned long lastCommandTime = 0;  // For communication timeout watchdog
bool eStopActive = false;

// ---- Fixed-size command buffer (NO String class) ----
#define CMD_BUF_SIZE 48
char cmdBuf[CMD_BUF_SIZE];
uint8_t cmdBufIdx = 0;

// ---- Telemetry output buffer ----
char telBuf[128];

// Forward declarations
void processCommand(const char* cmd);
uint8_t calcChecksum(const char* str, int len);

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    // Do NOT use while(!Serial) — it blocks indefinitely on Uno
    // if no USB host is connected, preventing standalone operation.
    delay(100); // Brief stabilization delay
    
    sensors_init();
    servos_init();
    
    lastCommandTime = millis();
    
    Serial.println("SYS|START|PHIP_V2");
}

void loop() {
    unsigned long now = millis();
    
    // =============================================
    // 1. NON-BLOCKING SERIAL COMMAND RECEPTION
    //    Uses fixed char buffer — NO heap allocation
    // =============================================
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (cmdBufIdx > 0) {
                cmdBuf[cmdBufIdx] = '\0';
                processCommand(cmdBuf);
                cmdBufIdx = 0;
            }
        } else {
            if (cmdBufIdx < CMD_BUF_SIZE - 1) {
                cmdBuf[cmdBufIdx++] = c;
            } else {
                // Buffer overflow — discard this malformed packet
                cmdBufIdx = 0;
            }
        }
    }
    
    // =============================================
    // 2. COMMUNICATION TIMEOUT WATCHDOG
    //    If no valid command received in COMMS_TIMEOUT_MS,
    //    enter safe state (stop all servos).
    // =============================================
    if (COMMS_TIMEOUT_MS > 0 && !eStopActive) {
        if (now - lastCommandTime > COMMS_TIMEOUT_MS) {
            servos_stop();
            eStopActive = true;
            Serial.println("SYS|TIMEOUT|SAFE_STATE");
        }
    }
    
    // =============================================
    // 3. TELEMETRY TRANSMISSION at fixed interval
    // =============================================
    if (now - lastReadTime >= SENSOR_READ_DELAY_MS) {
        lastReadTime = now;
        
        bool safe = sensors_read(&currentSensors);
        
        // Status byte: 0 = OK, faults bitmask otherwise
        uint8_t status = currentSensors.faults;
        if (eStopActive) status |= 0x80; // High bit = e-stop active
        
        // Build telemetry packet with ACTUAL servo angles
        int len = snprintf(telBuf, sizeof(telBuf), 
            "TEL|%lu|%u|%u|%u|%u|%u|%d|%d|%d|%d|%d|%u|", 
            now, 
            currentSensors.thumb, currentSensors.index, 
            currentSensors.middle, currentSensors.ring, currentSensors.pinky,
            servos_get_angle(0), servos_get_angle(1), servos_get_angle(2),
            servos_get_angle(3), servos_get_angle(4),
            status);
        
        // XOR checksum over the payload (including trailing |)
        uint8_t chk = calcChecksum(telBuf, len);
        
        Serial.print(telBuf);
        Serial.println(chk);
    }
}

// =============================================
// COMMAND PARSER — zero-allocation
// =============================================
void processCommand(const char* cmd) {
    // Update watchdog timer on ANY received command
    lastCommandTime = millis();
    
    // CMD|STOP|0|0|<checksum>
    if (strncmp(cmd, "CMD|STOP|", 9) == 0) {
        servos_stop();
        eStopActive = true;
        Serial.println("ACK|STOP");
        return;
    }
    
    // CMD|PING|0|0|<checksum>
    if (strncmp(cmd, "CMD|PING|", 9) == 0) {
        if (eStopActive) {
            // PING clears e-stop / timeout state (allows resuming after reconnect)
            eStopActive = false;
        }
        Serial.println("ACK|PING");
        return;
    }
    
    // CMD|SET|<finger>|<angle>|<checksum>
    if (strncmp(cmd, "CMD|SET|", 8) == 0) {
        if (eStopActive) return; // Refuse servo commands during e-stop
        
        // Parse finger index and angle from fixed positions
        // Format after "CMD|SET|": "<digit>|<angle>|<chk>"
        int finger = -1;
        int angle = -1;
        
        // Find delimiters manually (no String class)
        const char* p1 = cmd + 8; // After "CMD|SET|"
        const char* p2 = strchr(p1, '|');
        if (p2) {
            finger = atoi(p1);
            const char* p3 = strchr(p2 + 1, '|');
            if (p3) {
                angle = atoi(p2 + 1);
            }
        }
        
        if (finger >= 0 && finger <= 4 && angle >= 0 && angle <= SERVO_MAX_ANGLE) {
            servos_set(finger, angle);
        }
        return;
    }
    
    // CMD|RELEASE|0|0|<checksum>  — detach servos (power save)
    if (strncmp(cmd, "CMD|RELEASE|", 12) == 0) {
        servos_detach_all();
        Serial.println("ACK|RELEASE");
        return;
    }
    
    // Unknown command — ignore silently (don't waste serial bandwidth)
}

uint8_t calcChecksum(const char* str, int len) {
    uint8_t chk = 0;
    for (int i = 0; i < len; i++) {
        chk ^= (uint8_t)str[i];
    }
    return chk;
}
