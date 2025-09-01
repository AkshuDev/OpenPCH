try:
    from kivy_garden.effectwidget.blur import FXBlurEffect # type: ignore
    BLUR_AVAILABLE = True
except Exception:
    FXBlurEffect = None
    BLUR_AVAILABLE = False


from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ListProperty, ObjectProperty, NumericProperty, BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
import json
import os

openpchkv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openpch.kv")

KV = open(openpchkv, "r").read()

class DeviceBackendMock:
    """Mock backend: replace methods to communicate with real devices (hidapi/pyusb/your lib)."""
    def list_devices(self):
        # Example device entries
        return [
            {"id": "evofox_mouse_01", "name": "EvoFox Gaming Mouse", "type": "mouse"},
            {"id": "example_keyboard_01", "name": "StormKeys TKL", "type": "keyboard"},
        ]

    def connect(self, device_id):
        # attempt connect; return True/False
        return True

    def set_rgb(self, device_id, r, g, b, mode="static"):
        print(f"[backend] set_rgb {device_id} -> ({r},{g},{b}) mode={mode}")

    def set_dpi(self, device_id, dpi):
        print(f"[backend] set_dpi {device_id} -> {dpi}")

    def save_profile(self, device_id, profile):
        print(f"[backend] save_profile {device_id} -> {profile}")

    def load_profile(self, device_id):
        # return a profile dict or None
        return None

device_backend = DeviceBackendMock()

class DeviceListItem(Screen):
    pass

class MainScreen(Screen):
    devices = ListProperty([])
    selected_device = ObjectProperty(None, allownone=True)
    rgb_color = ListProperty([1, 0.2, 0.1, 1])  # default RGBA (kivy floats)
    dpi = NumericProperty(800)
    connected = BooleanProperty(False)
    status_text = StringProperty("Ready")

    def on_pre_enter(self):
        # refresh devices
        Clock.schedule_once(lambda dt: self.refresh_devices(), 0.1)

    def refresh_devices(self):
        self.devices = device_backend.list_devices()
        self.status_text = f"Found {len(self.devices)} device(s)."

    def select_device(self, idx):
        try:
            self.selected_device = self.devices[idx]
            self.status_text = f"Selected {self.selected_device['name']}"
            # try to load saved profile
            profile = device_backend.load_profile(self.selected_device["id"])
            if profile:
                # apply values if present
                if "dpi" in profile:
                    self.dpi = profile["dpi"]
                if "rgb" in profile:
                    r,g,b = profile["rgb"]
                    self.rgb_color = [r/255.0, g/255.0, b/255.0, 1]
                self.status_text += " — loaded profile"
        except Exception as e:
            self.status_text = f"Device selection error: {e}"

    def toggle_connect(self):
        if not self.selected_device:
            self.status_text = "Select a device first."
            return
        if not self.connected:
            ok = device_backend.connect(self.selected_device["id"])
            self.connected = bool(ok)
            self.status_text = "Connected" if ok else "Failed to connect"
        else:
            # mock disconnect
            self.connected = False
            self.status_text = "Disconnected"

    def on_rgb_color(self, instance, value):
        if not self.selected_device:
            return
        # value is [r,g,b,a] 0..1. Convert to 0..255
        r = int(value[0] * 255)
        g = int(value[1] * 255)
        b = int(value[2] * 255)
        device_backend.set_rgb(self.selected_device["id"], r, g, b)
        self.status_text = f"Set RGB to #{r:02X}{g:02X}{b:02X}"

    def on_dpi(self, instance, value):
        if not self.selected_device:
            return
        device_backend.set_dpi(self.selected_device["id"], int(value))
        self.status_text = f"Set DPI to {int(value)}"

    def save_profile(self):
        if not self.selected_device:
            self.status_text = "Select a device first."
            return
        profile = {
            "dpi": int(self.dpi),
            "rgb": [int(self.rgb_color[0]*255),
                    int(self.rgb_color[1]*255),
                    int(self.rgb_color[2]*255)]
        }
        device_backend.save_profile(self.selected_device["id"], profile)
        self.status_text = "Profile saved."

    def export_profile_json(self):
        # show a quick export in device folder
        if not self.selected_device:
            self.status_text = "Select device to export."
            return
        prof = {
            "name": self.selected_device["name"],
            "id": self.selected_device["id"],
            "dpi": int(self.dpi),
            "rgb": [int(self.rgb_color[0]*255),
                    int(self.rgb_color[1]*255),
                    int(self.rgb_color[2]*255)]
        }
        folder = os.path.join(os.getcwd(), "profiles")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{self.selected_device['id']}.json")
        with open(path, "w") as f:
            json.dump(prof, f, indent=2)
        self.status_text = f"Exported profile to {path}"

class OpenPCHApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex("#0b0f14")  # dark background
        self.title = "OpenPCH — Open Peripheral Control Hub"
        return Builder.load_string(KV)

if __name__ == "__main__":
    OpenPCHApp().run()
