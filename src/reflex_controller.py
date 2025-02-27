# reflex_controller.py
from led_data_handler import LEDDataHandler
from pad_model import Coord, PadModel
from sensor_data_handler import SensorDataHandler
from usb_controller import USBDeviceList, HIDReadProcess, HIDWriteProcess
from usb_info import ReflexV2Info


class ReflexPadInstance:
    """API to a connected RE:Flex v2 dance pad."""

    def __init__(self, info: ReflexV2Info, serial: str, model: PadModel):
        self._serial = serial
        self._read = HIDReadProcess(info, serial)
        self._write = HIDWriteProcess(info, serial)
        self._sensors = SensorDataHandler(
            self._read.data, self._read.event
        )
        self._lights = LEDDataHandler(
            self._write.data, self._write.event, model
        )

    def disconnect(self) -> None:
        self._read.terminate()
        self._write.terminate()

    def handle_sensor_data(self) -> None:
        self._sensors.take_sample()

    def handle_light_data(self) -> None:
        self._lights.give_sample()

    @property
    def pad_data(self) -> dict[tuple[Coord, Coord], int]:
        return self._sensors.pad_data

    @property
    def serial(self) -> str:
        return self._serial


class ReflexController:
    """USB controller for RE:Flex v2 dance pads."""
    
    CONNECTED = True
    DISCONNECTED = False

    def __init__(self, model: PadModel):
        self._info = ReflexV2Info()
        self._instance = None
        self._serials = []
        self._model = model
        self.enumerate_pads()

    def enumerate_pads(self) -> None:
        self._serials = USBDeviceList.connected_device_names(self._info)

    def toggle_pad_connection(self, serial: str) -> bool:
        if self._instance:
            return self.disconnect_pad()
        else:
            return self.connect_pad(serial)

    def connect_pad(self, serial: str) -> bool:
        """
          1. After connecting, enter config mode
          2. Request the profile (read)
          3. Exit config mode upon receiving the profile reply.
        """
        if pad := ReflexPadInstance(self._info, serial, self._model):
            if self._instance is None and serial in self._serials:
                self._instance = pad
                # Begin config sequence on connection:
                self.send_enter_config()
                self.queue_read_profile()
                # Exit config will be handled upon receipt of the profile reply.
                return self.CONNECTED
        return self.DISCONNECTED

    def disconnect_pad(self) -> bool:
        if self._instance is None:
            return self.DISCONNECTED
        self._instance.disconnect()
        self._instance = None
        return self.DISCONNECTED

    def get_all_pads(self) -> list[str | None]:
        return self._serials

    @property
    def pad(self) -> ReflexPadInstance | None:
        if self._instance:
            return self._instance
        return None

    def push_profile(self) -> bool:
        """
        Packages the current profile data into a 64-byte packet and sends it
        to the device via the HID write process. The packet format is defined as:
          - Byte 0: Command header (0xF0)
          - Bytes 1-32: For each of 4 panels × 4 sensors: threshold (1 byte) and hysteresis (1 byte)
          - Bytes 33-36: For each of 4 panels: assigned key (ASCII, 1 byte each)
          - Bytes 37-63: Zero padding
        After sending, it queues a read command (header 0xF1) to get the device's profile.
        The reply (when received) will be processed to update the "RE:Flex Device" profile entry.
        """
        if self._instance is None:
            return False

        # Retrieve profile data from the pad model.
        # Expected profile_data structure:
        # { panel_coord: ( { sensor_coord: (threshold, hysteresis), ... }, key ), ... }
        profile_data = self._model.profile_data

        packet = bytearray(64)
        packet[0] = 0xF0  # Profile push command header

        pos = 1
        # For each panel (using order from PadModel.PANELS.coords)
        for panel in PadModel.PANELS.coords:
            panel_profile = profile_data.get(panel, ({}, ' '))
            sensor_data = panel_profile[0]  # { sensor_coord: (threshold, hysteresis) }
            for sensor in PadModel.SENSORS.coords:
                # Use defaults if not set.
                threshold, hysteresis = sensor_data.get(sensor, (30, 5))
                packet[pos] = threshold & 0xFF
                packet[pos + 1] = hysteresis & 0xFF
                pos += 2

        # For each panel, store the assigned key (one ASCII byte each)
        for panel in PadModel.PANELS.coords:
            panel_profile = profile_data.get(panel, ({}, ' '))
            key = panel_profile[1]
            if key:
                packet[pos] = ord(key[0])
            else:
                packet[pos] = 0
            pos += 1

        # Zero pad remaining bytes.
        for i in range(pos, 64):
            packet[i] = 0

        # Send the profile push packet via the HID write process.
        # The HID write process is stored in the _write member of the ReflexPadInstance.
        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()

        # Queue a read profile command (see below).
        self.queue_read_profile()
        return True

    def send_enter_config(self) -> None:
        """Sends the 64-byte Enter Config Mode packet."""
        if self._instance is None:
            return
        packet = bytearray.fromhex(
            "b6da3dc8904aae1587f7ee9913c8bc5f4e616d7b7505c4b36220c9a7841866d1872782b87caae1bf41c001c457d4e1e3d54b5db6a6c16768a615735f43c95ab3"
        )
        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()

    def send_exit_config(self) -> None:
        """Sends the 64-byte Exit Config Mode packet."""
        if self._instance is None:
            return
        packet = bytearray.fromhex(
            "7f5455b20d201105e64b9852cf4911475cefae3d39bde6baa12d69b14df3c61d71ffbc33091fd41034e545b0fae189dafc3a32dfe97a8dd6b7238b33bdd65ea6"
        )
        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()

    def queue_read_profile(self) -> None:
        """Queues a Profile Read Request packet (0xF1)."""
        if self._instance is None:
            return
        packet = bytearray(64)
        packet[0] = 0xF1  # Read request header
        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()

    def push_profile(self) -> bool:
        """
        Sequence for Push Profile:
          1. Enter Config Mode
          2. Send the Profile Push packet (header 0xF0)
          3. Queue a Profile Read Request (to receive updated profile)
          4. (Later, when the read reply is received, Exit Config Mode)
        """
        if self._instance is None:
            return False

        # 1. Enter Config Mode.
        self.send_enter_config()

        # 2. Prepare and send the Profile Push packet.
        packet = bytearray(64)
        packet[0] = 0xF0  # Profile Push command header
        pos = 1
        profile_data = self._model.profile_data  # Expected to be a dict mapping panel coords
        for panel in PadModel.PANELS.coords:
            panel_profile = profile_data.get(panel, ({}, ' '))
            sensor_data = panel_profile[0]  # Dict of sensor data: {sensor_coord: (threshold, hysteresis)}
            for sensor in PadModel.SENSORS.coords:
                threshold, hysteresis = sensor_data.get(sensor, (30, 5))
                packet[pos] = threshold & 0xFF
                packet[pos + 1] = hysteresis & 0xFF
                pos += 2
        for panel in PadModel.PANELS.coords:
            panel_profile = profile_data.get(panel, ({}, ' '))
            key = panel_profile[1]
            packet[pos] = ord(key[0]) if key else 0
            pos += 1
        for i in range(pos, 64):
            packet[i] = 0  # Zero pad the remainder

        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()

        # 3. Queue a Profile Read Request.
        self.queue_read_profile()

        # The Exit Config command will be sent after processing the profile reply.
        return True

    def process_read_profile_reply(self, data: bytearray) -> None:
        """
        Called when the device sends a Profile Read Reply.
        Parses the reply, updates the in-memory (device) profile,
        and then exits configuration mode.
        Expected packet format (64 bytes):
          - Byte 0: Header (0xF1)
          - Bytes 1-32: Sensor thresholds and hysteresis (16 sensors × 2 bytes)
          - Bytes 33-36: Assigned keys (1 byte per panel)
          - Bytes 37-63: Not used
        """
        if not data or data[0] != 0xF1:
            return  # Ignore unexpected packets

        new_profile = {}
        pos = 1
        for panel in PadModel.PANELS.coords:
            sensor_data = {}
            for sensor in PadModel.SENSORS.coords:
                threshold = data[pos]
                hysteresis = data[pos + 1]
                sensor_data[sensor] = (threshold, hysteresis)
                pos += 2
            key_val = chr(data[pos])
            pos += 1
            new_profile[panel] = (sensor_data, key_val)

        # Update the in-memory device profile.
        from profile_controller import ProfileController
        ProfileController(self._model).update_device_profile(new_profile)

        # 4. Exit Config Mode.
        self.send_exit_config()