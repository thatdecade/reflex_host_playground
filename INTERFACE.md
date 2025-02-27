
# Re:Flex Interface Document (Packet Formats)

**Types of Packets:**

- **Normal Operation Packets**  
  - LED Data Packets (to Device)  
  - Sensor Data Packets (from Device)

- **Configuration Mode Packets**
  - Enter Config Mode Packet  
  - Profile Packets (Push, Request, Reply)  
  - Exit Config Mode Packet

> The device must be in configuration mode for any Profile Packets (Push, Request, or Reply) to be accepted.

---

## Normal Operation Packets

### LED Data Packet

Each of the 4 panels drives a fixed array of 84 LEDs divided into 4x 21 LED segments.

- **Total Length:** 64 bytes

- **Byte 0 – Header:** *Packed by* `LEDDataHandler.setup_frame_data`
  - **Bits 7–6 (2 bits): Panel Number**  
    – Value: 0 to 3 (4 panels)  
    – Stored as: `panel << 6`
  - **Bits 5–4 (2 bits): Segment Number**  
    – Value: 0 to 3 (4 segments)  
    – Stored as: `segment << 4`
  - **Bits 3–0 (4 bits): Frame RGB Data**  
    – Value: 0 to 15 (16 frame steps)  
    – Stored as: `frame`
- **Bytes 1–63 – LED Color Data:** *Packed by* `LEDDataHandler.get_data_byte`
  - For each LED (21 LEDs total), the 3-byte group is:  
    - **Byte (1 + 3×i + 0):** Gamma‐corrected **Green** intensity (8 bits)  
    - **Byte (1 + 3×i + 1):** Gamma‐corrected **Red** intensity (8 bits)  
    - **Byte (1 + 3×i + 2):** Gamma‐corrected **Blue** intensity (8 bits)

### Sensor Data Packet

- **Total Length:** 64 bytes
- **Bytes 0–31 – Sensor Readings:** 16 sensor readings, with each reading as 2 bytes in little-endian.
  *Unpacked by* `SensorDataHandler.organise_sensor_data`
  - For sensor reading index *i* (0 - 15):
    - **Byte (2×i):** Low byte of sensor value  
    - **Byte (2×i + 1):** High byte of sensor value  
  - **Sensor Value =** `byte[2 x i] + (byte[2 x i + 1] << 8`
- **Bytes 32–63:** Not Used.

**Mapping of Sensors:**  
Each of the 4 panels has 4 sensors. Total 16 sensors.
  
- **Sensor Reading Index 0–3:** Left Panel
- **Sensor Reading Index 4–7:** Down Panel
- **Sensor Reading Index 8–11:** Up Panel
- **Sensor Reading Index 12–15:** Right Panel

---

## Configuration Mode Packets

Profile packets (Push, Request, and Reply) are only accepted by the device when it is in configuration mode.

### Enter Config Mode Packet

- **Total Length:** 64 bytes  
- **Definition:**  The app sends a 64-byte packet that must exactly equal:
```
  b6da3dc8904aae1587f7ee9913c8bc5f4e616d7b7505c4b36220c9a7841866d1872782b87caae1bf41c001c457d4e1e3d54b5db6a6c16768a615735f43c95ab3
```
- **Purpose:**  When the device receives this exact packet, it suspends normal LED and sensor data transmissions and enters configuration mode.

### Exit Config Mode Packet

- **Total Length:** 64 bytes  
- **Definition:**  The app sends a 64-byte packet that must exactly equal:
```
  7f5455b20d201105e64b9852cf4911475cefae3d39bde6baa12d69b14df3c61d71ffbc33091fd41034e545b0fae189dafc3a32dfe97a8dd6b7238b33bdd65ea6
```
- **Purpose:**  Upon receiving an exact match, the device exits configuration mode and resumes normal operation.

### Profile Push Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Header `0xF0`  
- **Bytes 1–32:** For each of the 4 panels × 4 sensors (16 sensors total):  
  - 1 byte for sensor threshold  
  - 1 byte for sensor hysteresis  
  (Total: 16 × 2 = 32 bytes)
- **Bytes 33–36:** For each of the 4 panels, 1 byte representing the panel’s assigned key (ASCII)  
- **Bytes 37–63:** Not Used

### Profile Read Request Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Header `0xF1`
- **Bytes 1–63:** Not Used

### Profile Read Reply Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Header `0xF1`  
- **Bytes 1–32:** Same format as the push packet: 
  - 1 byte for the sensor threshold  
  - 1 byte for the sensor hysteresis  
  (Total: 16 × 2 = 32 bytes)
- **Bytes 33–36:** For each of 4 panels, 1 byte representing the panel’s assigned key (ASCII)  
- **Bytes 37–63:** Not Used

---

### Generating the Magic Signature

Using Python’s SHA-512, the magic signatures are computed as follows:

```python
import hashlib

def generate_config_magic_packet(string: str) -> bytes:
    return hashlib.sha512(string.encode('ascii')).digest()

# Generate the Enter and Exit Config Magic Packets:
enter_config_magic = generate_config_magic_packet("REFLEXENTERCONFIG")
exit_config_magic  = generate_config_magic_packet("REFLEXEXITCONFIG")
```

These signatures were compared to the pre-compiled LED packets in [preprocessed_led_packets.csv](preprocessed_led_packets.csv).
Ensuring LED traffic will never conflict with config mode packets.
