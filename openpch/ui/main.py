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
from kivy.factory import Factory
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.usb_backend import *

openpchkv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openpch.kv")

KV = open(openpchkv, "r").read()

device_backend = DevicesBackend()

class MainScreen(Screen):
    def on_kv_post(self, *args):
        self.refresh_devices()

    def refresh_devices(self):
        device_grid = self.ids.devices_grid
        device_grid.clear_widgets()

        devices = device_backend.list_devices()
        for dev in devices:
            btn = Factory.NeonButton(
                text=dev,
                size_hint_y=None,
                height=80,
                on_release=lambda b, name=dev: self.open_device(name)
            )
            device_grid.add_widget(btn)

    def open_device(self, name:str):
        device_screen = self.manager.get_screen("device")
        device_backend.sel_device = name
        self.manager.current = "device"

class DeviceScreen(Screen):
    selected_device = device_backend.sel_device
    rgb_color = ListProperty([1, 0.2, 0.1, 1])  # default RGBA (kivy floats)
    dpi = NumericProperty(800)
    connected = BooleanProperty(False)
    status_text = StringProperty("Ready")

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
