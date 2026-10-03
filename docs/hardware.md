# Hardware Documentation

## Arduino Uno R3
- 2KB SRAM, 32KB Flash.
- Powered via USB from the host computer.

## Flex Sensors
- 5x analog flex sensors.
- Arranged in voltage dividers.
- Connected to A0-A4.

## Servos
- 5x standard PWM servos.
- Controlled via Timer1 (Arduino `Servo` library).
- Connected to Digital Pins 3, 5, 6, 9, 10.

## Pin Mapping
From `firmware/PHIP_firmware/config.h`:

| Component      | Pin |
|----------------|-----|
| Thumb Sensor   | A0  |
| Index Sensor   | A1  |
| Middle Sensor  | A2  |
| Ring Sensor    | A3  |
| Pinky Sensor   | A4  |
| Thumb Servo    | 3   |
| Index Servo    | 5   |
| Middle Servo   | 6   |
| Ring Servo     | 9   |
| Pinky Servo    | 10  |

## Power Architecture
- **Arduino:** Powered exclusively by USB.
- **Servos:** MUST be powered by an external 5V-6V DC power supply capable of supplying peak stall currents for all 5 servos simultaneously.
- **Common Ground:** The GND terminal of the external power supply MUST be connected to the GND pin on the Arduino Uno.

## Physical Testing Procedure
1. Disconnect all servos. Verify flex sensors first in the UI.
2. Connect ONE servo (unloaded). Verify limits and control.
3. Test all five servos unloaded.
4. Mount to mechanical hand. Test with extreme caution, ready to press E-STOP if mechanical binding occurs.
