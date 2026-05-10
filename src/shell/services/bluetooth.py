from fabric.bluetooth import BluetoothClient, BluetoothDevice
from fabric.core import Property
from util.singleton import Singleton
from loguru import logger


class BluetoothService(BluetoothClient, Singleton):
    @Property(bool, default_value=False, flags="readable")
    def is_device_connected(self) -> bool:
        return self.connected_devices != []

    @Property(BluetoothDevice | None, flags="readable")
    def current_device(self) -> BluetoothDevice | None:
        if self.is_device_connected:
            return self.connected_devices[0]
        else:
            return None

    def on_device_removed(self, _, object_path: str):
        # NOTE: The original version of this function causes crashes
        # removing the call to device.close() is the only thing that fixes the crashes for me.
        addr = object_path.split("/")[-1][4:].replace("_", ":")
        if not (device := self._devices.pop(addr, None)):
            return logger.warning(
                f"[Bluetooth] tried to remove a unknown device with the address {addr}"
            )

        logger.info(f"[Bluetooth] Removing device: {addr}")

        self.emit("device-removed", addr)
        if device.connected:
            self.notifier("connected-devices")
        self.notifier("devices")
        return
