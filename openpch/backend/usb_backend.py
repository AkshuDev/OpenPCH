import hid

class DevicesBackend():
    def __init__(self):
        self.sel_device = None

        self.devices = []
        self.devices_name = []

    def list_devices(self) -> list:
        for dev in hid.enumerate():
            self.devices_name.append(dev['product_string'])
            self.devices.append((dev["vendor_id"], dev['product_id'], dev['product_string']))
        return self.devices_name

    def set_rgb(self) -> None:
        pass

    def set_dpi(self) -> None:
        pass

    def save_profile(self) -> None:
        pass
