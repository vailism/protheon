# Troubleshooting

### Arduino Not Detected
- **Cause:** Serial port permissions or missing drivers.
- **Fix:** Check USB cable. On macOS, ensure you have authorized the USB accessory. Use the dropdown in the Diagnostics tab to force a connection.

### No Sensor Readings
- **Cause:** Incorrect wiring or mismatched pins.
- **Fix:** Check `config.h` pin definitions. A flex sensor voltage divider usually involves a 10k resistor. Ensure VCC, GND, and the Analog pin are properly seated.

### Servo Jitter
- **Cause:** Insufficient power supply or ground loop.
- **Fix:** Ensure the external power supply is rated for high current (at least 2A per active servo) and that the supply GND is tied to the Arduino GND.

### Checksum Errors
- **Cause:** Noisy serial line or baud rate mismatch.
- **Fix:** Ensure baud rate is strictly `115200`. Check for loose USB connections.

### Timeout (Safe State)
- **Cause:** Python backend crashed or is blocked.
- **Fix:** The Arduino safely halted. Restart the Python application. Ensure the UI thread is not being blocked.
