# event_info.py

class WidgetMessage:
    """Message string to pass over queue from Widget event to Data process."""
    REFRESH = "GUI_refresh_pads"
    CONNECT = "GUI_connect_pad"
    NEW = "GUI_new_profile"
    REMOVE = "GUI_remove_profile"
    RENAME = "GUI_rename_profile"
    SAVE = "GUI_save_profile"
    SELECT = "GUI_select_profile"
    INIT = "GUI_init_window"
    QUIT = "GUI_quit"
    FRAME_READY = "GUI_frame_ready"
    SENSOR_UPDATE = "GUI_sensor_update"
    VIEW_UPDATED = "GUI_view_updated"
    KEYS = "GUI_keys"
    PUSH_PROFILE = "GUI_push_profile"

class DataProcessMessage:
    """Message string to pass over queue from Data process event to Widget."""
    ALL_PADS = "DP_all_pads"
    PROFILE_NAMES = "DP_profile_init"
    PAD_CONNECTED = "DP_pad_connected"
    FRAME_DATA = "DP_frame_data"
    PROFILE_NEW = "DP_profile_new"
    PROFILE_SAVED = "DP_profile_saved"
    PROFILE_LOADED = "DP_profile_loaded"
    PROFILE_RENAMED = "DP_profile_renamed"
    PROFILE_REMOVED = "DP_profile_removed"
    SENSOR_UPDATED = "DP_sensor_updated"
    PROFILE_PUSHED = "DP_profile_pushed"
