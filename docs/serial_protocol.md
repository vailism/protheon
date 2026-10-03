# Serial Protocol

## Framing
- Messages are delimited by pipe characters `|`.
- Messages end with an 8-bit XOR checksum followed by a newline `\n`.

## Checksum
The checksum is an 8-bit XOR of all characters in the payload up to and including the final `|`.
```python
chk = 0
for c in payload:
    chk ^= ord(c)
chk &= 0xFF
```

## Arduino → Host (Telemetry)
Format: `TEL|<timestamp>|<t_raw>|<i_raw>|<m_raw>|<r_raw>|<p_raw>|<t_ang>|<i_ang>|<m_ang>|<r_ang>|<p_ang>|<status>|<chk>`

* `t_raw` to `p_raw`: Flex sensor ADC values (0-1023)
* `t_ang` to `p_ang`: Commanded servo angles (0-180)
* `status`: Bitmask of sensor faults. High bit (0x80) indicates E-STOP active.

## Host → Arduino (Commands)

**Command Servo:**
`CMD|SET|<finger_idx>|<angle>|<chk>`

**Emergency Stop:**
`CMD|STOP|0|0|<chk>`

**Watchdog Heartbeat:**
`CMD|PING|0|0|<chk>`

**Release Servos (detach):**
`CMD|RELEASE|0|0|<chk>`

## Watchdog
The Arduino expects a command or PING every 3000ms. If this timeout expires, it halts all servos autonomously.
