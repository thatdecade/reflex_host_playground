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
        if pad := ReflexPadInstance(self._info, serial, self._model):
            if self._instance is None and serial in self._serials:
                self._instance = pad
                # Upon first connection, read the current device profile and update it.
                device_profile = self.queue_read_profile()
                ProfileController(self._model).update_device_profile(device_profile)
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

    def queue_read_profile(self) -> None:
        """
        Queues a read profile command (header 0xF1) to the device by writing
        the appropriate packet to the HID write process.
        The device is expected to reply with a profile read response.
        """
        if self._instance is None:
            return
        packet = bytearray(64)
        packet[0] = 0xF1  # Profile read request header
        with self._instance._write.data.get_lock():
            for i in range(64):
                self._instance._write.data[i] = packet[i]
        self._instance._write.event.set()
