
# Re:Flex Interface Document (Packet Formats)

**(TBD) Byte 0: Header Lookup**
* Send: 0x00-0xFF = LED Data
* Received: 0x00-0xFF = Sensor Data

--- 

### LED Data Packet

Each of the 4 panel has 84 LEDs, divided into 21 LED segments.

- **Total Length:** 64 bytes

- **Byte 0 – Header:** *Packed by* `LEDDataHandler.setup_frame_data`
    - **Bits 7–6 (2 bits): Panel Number:**  
        – Value: 0 to 3 (since there are 4 panels)  
        – Stored as: `panel << 6`
    - **Bits 5–4 (2 bits): Segment Number:**  
        – Value: 0 to 3 (since there are 4 segments)  
        – Stored as: `segment << 4`
    - **Bits 3–0 (4 bits): Frame RGB Data:**  
        – Value: 0 to 15 (since there are 16 frame steps)  
        – Stored as: `frame`
- **Bytes 1–63 – LED Color Data:** *Packed by* `LEDDataHandler.get_data_byte`
    - **Byte (1 + 3×i + 0):** Gamma‐corrected **Green** intensity (8 bits)  
    - **Byte (1 + 3×i + 1):** Gamma‐corrected **Red** intensity (8 bits)  
    - **Byte (1 + 3×i + 2):** Gamma‐corrected **Blue** intensity (8 bits)

--- 

### Sensor Data Packet

- **Total Length:** 64 bytes
- **Bytes 0–31 – Sensor Readings:** These 32 bytes hold 16 sensor readings. (each reading is 2 bytes in little‑endian order).
*Unpacked by*  `SensorDataHandler.organise_sensor_data`
  - For sensor reading index *i* (where *i* = 0, 1, …, 15):
    - **Byte (2×i):** Low byte of sensor value  
    - **Byte (2×i + 1):** High byte of sensor value  
  - **Sensor Value =** `byte[2 x i] + (byte[2 x i + 1] << 8`
- **Bytes 32–63:** Not Used.

**Mapping of Sensors:** 
  
Each of the 4 panels has 4 sensors.

- **Sensor Reading Index 0–3:** Left Panel
- **Sensor Reading Index 4–7:** Down Panel
- **Sensor Reading Index 8–11:** Up Panel
- **Sensor Reading Index 12–15:** Right Panel
  
--- 

### Profile Push Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Header `0xF0`
- **Bytes 1–32:** For each of 4 panels × 4 sensors (i.e. 16 sensors total):  
  - 1 byte for the sensor threshold  
  - 1 byte for the sensor hysteresis  
  (Total: 16 × 2 = 32 bytes)
- **Bytes 33–36:** For each of 4 panels, 1 byte representing the panel’s assigned key (ASCII)  
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
