
**2/27/2025 Snapshot Build**

**Description:** Allow storage of profile on the device. Future goal is support of multiple pads, without needing the host app running.

**Status:** Debug of Re:Flex Controller is pending Firmware Integration.

### Summary

* Profile Push Button Added  
* Widget and Data Process Messages  
* Profile Push Implementation  
* Profile Read and Update  
* Config Mode Packets

### Details

- **Profile Push Button Added:**  
  - An arrow symbol button (“Push Profile to RE:Flex”) was added to the profile window in **profile_widget.py**.  
  - Its click signal (`PUSH_PROFILE_CLICKED`) is connected in the GUI hooks (in **gui_widgets.py**) to emit the message `"GUI_push_profile"`.

- **Widget and Data Process Messages:**  
  - A widget message (`WidgetMessage.PUSH_PROFILE`) and corresponding data process message (`DataProcessMessage.PROFILE_PUSHED`) were defined in **event_info.py**.  
  - The `data_requests` mapping was updated (in **gui_widgets.py**) with an empty entry for `"GUI_push_profile"` since no extra data is needed.
  - The **data_sequences.py** mapping now routes `WidgetMessage.PUSH_PROFILE` to `ReflexController.push_profile`.

- **Profile Push Implementation:**  
  - In **reflex_controller.py**, the method `push_profile()` was implemented to package the current profile data into a 64‑byte packet.  
  - The packet uses a header of `0xF0` and encodes for each panel: 32 bytes for sensor calibration (threshold and hysteresis for 4 sensors per panel) and 4 bytes for panel key assignments, with the remaining bytes zero‑padded.
  - Immediately after pushing, the method calls `queue_read_profile()` to send a read request (packet header `0xF1`).

- **Profile Read and Update:**  
  - The method `queue_read_profile()` (in **reflex_controller.py**) sends a 64‑byte packet with header `0xF1` to request the device’s stored profile.
  - When a reply is received (via the `"DP_profile_read_reply"` mapping), the handler `process_read_profile_reply()` (in **reflex_controller.py**) parses the reply and updates the host’s in‑memory “RE:Flex Device” profile.
  - In **profile_controller.py**, the method `update_device_profile()` was added to update the pad model’s profile data in memory without writing to disk.
  - The GUI handler `profile_pushed()` (in **gui_handlers.py**) pops up a confirmation message (using a message box) and updates the profile dropdown to include the “RE:Flex Device” entry.

- **Config Mode Packets:**  
  - **Enter Config Mode Packet:**  
    - A 64-byte packet computed as the SHA‑512 hash of `"REFLEXENTERCONFIG"` is sent before any profile read or push commands.  
    - This packet causes the device to suspend normal operations and accept configuration mode packets.  
  - **Exit Config Mode Packet:**  
    - A 64-byte packet computed as the SHA‑512 hash of `"REFLEXEXITCONFIG"` is now sent after the profile update sequences are complete.  
    - This packet instructs the device to exit configuration mode and resume normal operations.  
  - These packets wrap the profile read and push sequences to ensure that the device safely transitions into and out of configuration mode during profile operations.
