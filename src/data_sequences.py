# data_sequences.py
from event_info import DataProcessMessage, WidgetMessage
from pad_model import PadModel
from profile_controller import ProfileController
from reflex_controller import ReflexController


class Sequences:
    pad_model = PadModel()
    pad_controller = ReflexController(pad_model)
    profile_controller = ProfileController(pad_model)
    _sensor_delta = None
    _light_delta = None

    receive = {
        WidgetMessage.CONNECT: [
            pad_controller.toggle_pad_connection
        ],
        WidgetMessage.FRAME_READY: [
            pad_model.get_model_data
        ],
        WidgetMessage.INIT: [
            pad_controller.get_all_pads,
            profile_controller.initialise_profile,
            pad_model.get_model_data
        ],
        WidgetMessage.KEYS: [
            profile_controller.handle_keys
        ],
        WidgetMessage.NEW: [
            pad_model.set_default,
            profile_controller.create_new_profile
        ],
        WidgetMessage.QUIT: [
            pad_controller.disconnect_pad
        ],
        WidgetMessage.REFRESH: [
            pad_controller.enumerate_pads,
            pad_controller.get_all_pads
        ],
        WidgetMessage.SENSOR_UPDATE: [
            pad_model.set_sensor
        ],
        WidgetMessage.SAVE: [
            profile_controller.save_user_profile
        ],
        WidgetMessage.SELECT: [
            profile_controller.load_user_profile
        ],
        WidgetMessage.REMOVE: [
            profile_controller.remove_user_profile
        ],
        WidgetMessage.RENAME: [
            profile_controller.rename_user_profile
        ],
        WidgetMessage.VIEW_UPDATED: [
            pad_model.view_updated
        ],
        WidgetMessage.PUSH_PROFILE: [
            pad_controller.push_profile
        ],
        "DP_profile_read_reply": [lambda data: pad_controller.process_read_profile_reply(data)],
    }

    transmit = {
        pad_controller.get_all_pads:
            DataProcessMessage.ALL_PADS,
        pad_controller.toggle_pad_connection:
            DataProcessMessage.PAD_CONNECTED,
        pad_model.get_model_data:
            DataProcessMessage.FRAME_DATA,
        pad_model.set_sensor:
            DataProcessMessage.SENSOR_UPDATED,
        profile_controller.create_new_profile:
            DataProcessMessage.PROFILE_NEW,
        profile_controller.load_user_profile:
            DataProcessMessage.PROFILE_LOADED,
        profile_controller.initialise_profile:
            DataProcessMessage.PROFILE_NAMES,
        profile_controller.remove_user_profile:
            DataProcessMessage.PROFILE_REMOVED,
        profile_controller.rename_user_profile:
            DataProcessMessage.PROFILE_RENAMED,
        profile_controller.save_user_profile:
            DataProcessMessage.PROFILE_SAVED,
        pad_controller.push_profile: 
            DataProcessMessage.PROFILE_PUSHED,
    }

    def handle_pad_data(self) -> bool:
        if not (pad := self.pad_controller.pad):
            return False
        pad.handle_sensor_data()
        if pad._sensors.refreshed:
            self.pad_model.set_baseline(pad.pad_data)
        else:
            self.pad_model.set_sensor_data(pad.pad_data)
        pad.handle_light_data()
        return True
