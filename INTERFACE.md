
# Re:Flex Interface Document (Packet Formats)

### LED Data Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Header that encodes panel, segment, and frame  
- **Bytes 1–63:** LED color data (grouped as 21 LEDs × 3 bytes [Green, Red, Blue] with gamma correction)

### Sensor Data Packet

- **Total Length:** 64 bytes  
- **Content:** First 32 bytes are used to encode 16 sensor readings (each reading is 2 bytes in little‑endian order)  
- **Mapping:** The readings are assigned to sensors based on panel and sensor coordinate arrays in **pad_model.py**

### Profile Push Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Command header `0xF0` (indicates a profile push command)  
- **Bytes 1–32:** For each of 4 panels × 4 sensors (i.e. 16 sensors total):  
  - 1 byte for the sensor threshold  
  - 1 byte for the sensor hysteresis  
  (Total: 16 × 2 = 32 bytes)
- **Bytes 33–36:** For each of 4 panels, 1 byte representing the panel’s assigned key (ASCII)  
- **Bytes 37–63:** Zero padding

### Profile Read Request Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Command header `0xF1` (indicates a profile read request)  
- **Bytes 1–63:** Zero padding

### Profile Read Reply Packet

- **Total Length:** 64 bytes  
- **Byte 0:** Expected to be `0xF1` to indicate a reply  
- **Bytes 1–36:** Same format as the push packet (i.e. sensor calibration and key data)  
- **Bytes 37–63:** Zero padding
