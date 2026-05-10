from typing import Callable
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils import bulk_connect, truncate

from services.bluetooth import BluetoothService, BluetoothDevice
import config.icons as Icons
from util.ui import add_hover_cursor


class BluetoothOverview(Box):
    def __init__(self, on_show_connection_settings: Callable = None, **kwargs):
        self.bluetooth_service = BluetoothService.get_instance()

        super().__init__(
            name="bluetooth-overview", spacing=20, orientation="h", **kwargs
        )

        self.power_icon = Label(
            markup=Icons.bluetooth_on
            if self.bluetooth_service.enabled
            else Icons.bluetooth_off,
            style_classes="bluetooth-overview-icon",
        )
        self.power_button_child_box = Box(spacing=10, children=[self.power_icon])
        self.power_button = Button(
            style_classes="bluetooth-overview-button",
            child=self.power_button_child_box,
            on_clicked=lambda *_: self.bluetooth_service.toggle_power(),
        )
        add_hover_cursor(self.power_button)

        self.connection_icon = Label(
            markup=Icons.link
            if self.bluetooth_service.is_device_connected
            else Icons.link_off,
            style_classes="bluetooth-overview-icon",
        )
        self.connection_label = Label(
            label=self.get_connected_device_name(),
            style_classes="bluetooth-overview-label",
        )
        self.connection_child_box = Box(
            spacing=10, children=[self.connection_icon, self.connection_label]
        )
        self.connection_button = Button(
            style_classes="bluetooth-overview-button",
            child=self.connection_child_box,
            on_clicked=on_show_connection_settings,
        )
        add_hover_cursor(self.connection_button)

        self.children = [self.power_button, self.connection_button]

        bulk_connect(
            self.bluetooth_service,
            {
                "notify::enabled": self.on_notify_enabled,
                "notify::state": self.on_notify_state,
                "notify::connected-devices": self.on_notify_connected_devices,
            },
        )

    def on_notify_state(self, *args):
        adapter_state = self.bluetooth_service.state
        sensitive = True if adapter_state == "on" or adapter_state == "off" else False
        self.power_button.set_sensitive(sensitive)

    def on_notify_enabled(self, *args):
        if self.bluetooth_service.enabled:
            icon = Icons.bluetooth_on
        else:
            icon = Icons.bluetooth_off

        self.power_icon = Label(style_classes="bluetooth-overview-icon", markup=icon)

        self.power_button_child_box.children = [
            self.power_icon,
        ]

        self.bluetooth_service.notifier("connected-devices")

    def on_notify_connected_devices(self, *args):
        current_device = self.bluetooth_service.current_device
        if self.bluetooth_service.current_device is not None:
            connection_icon = Icons.link
            connection_label = (
                current_device.name
                if current_device.name is not None
                else current_device.address
            )
        else:
            connection_icon = Icons.link_off
            connection_label = "Disconnected"

        self.connection_label.set_property("label", connection_label)

        self.connection_icon = Label(
            markup=connection_icon,
            style_classes="bluetooth-overview-icon",
        )

        self.connection_child_box.children = [
            self.connection_icon,
            self.connection_label,
        ]

    def get_connected_device_name(self):
        current_device = self.bluetooth_service.current_device
        if current_device is not None:
            name = (
                current_device.name
                if current_device.name is not None
                else current_device.address
            )

            return truncate(name, 15)
        else:
            return "Disconnected"


class BluetoothConnections(Box):
    def __init__(self, on_close: Callable, **kwargs):
        self.bluetooth_service = BluetoothService.get_instance()

        super().__init__(
            name="bluetooth-connections",
            spacing=20,
            style_classes="view-box",
            orientation="h",
            v_expand=True,
            h_align="center",
            **kwargs,
        )

        request_scan_button = Button(
            child=Label(
                markup=Icons.refresh, style_classes="bluetooth-connections-icon"
            ),
            on_clicked=lambda *_: self.bluetooth_service.scan(),
        )
        add_hover_cursor(request_scan_button)

        self.toggle_scan_button = Button(
            child=Label(
                markup=Icons.search
                if self.bluetooth_service.scanning
                else Icons.search_off,
                style_classes="bluetooth-connections-icon",
            ),
            on_clicked=lambda *_: self.bluetooth_service.toggle_scan(),
        )
        add_hover_cursor(self.toggle_scan_button)

        self.bluetooth_devices_list = Box(spacing=20, orientation="v")
        self.bluetooth_devices = ScrolledWindow(
            child=self.bluetooth_devices_list,
            v_expand=True,
            name="bluetooth-devices-scrolled-window",
        )

        back_button = Button(
            child=Label(
                markup=Icons.arrow_right,
                style_classes="bluetooth-connections-icon",
            ),
            on_clicked=on_close,
        )
        add_hover_cursor(back_button)

        self.children = [
            Box(
                spacing=20,
                orientation="v",
                v_expand=True,
                v_align="center",
                children=[
                    request_scan_button,
                    self.toggle_scan_button,
                ],
            ),
            Box(
                spacing=20,
                orientation="v",
                children=[
                    Label("Available Bluetooth Devices"),
                    self.bluetooth_devices,
                ],
            ),
            back_button,
        ]

        bulk_connect(
            self.bluetooth_service,
            {
                "notify::devices": self.on_notify_devices,
                "notify::scanning": self.on_notify_scanning,
            },
        )

    def get_device_elements(self):
        return [BluetoothDeviceElement(device) for device in self.get_sorted_devices()]

    def get_sorted_devices(self):
        def sort_key(device: BluetoothDevice):
            if device.connected:
                return -2
            elif device.trusted:
                return -1
            else:
                return 0

        return sorted(
            [device for device in self.bluetooth_service.devices], key=sort_key
        )

    def on_notify_devices(self, *args):
        self.bluetooth_devices_list.children = self.get_device_elements()

    def on_notify_scanning(self, *args):
        icon = Icons.search if self.bluetooth_service.scanning else Icons.search_off

        self.toggle_scan_button.children = Label(
            markup=icon, style_classes="bluetooth-connections-icon"
        )


class BluetoothDeviceElement(Box):
    bluetooth_service: BluetoothService = BluetoothService.get_instance()

    def __init__(self, device: BluetoothDevice, **kwargs):
        device.connect("changed", lambda *_: self.bluetooth_service.notifier("devices"))

        super().__init__(
            spacing=10,
            orientation="h",
            style_classes="bluetooth-device-element",
            **kwargs,
        )

        connect_button = Button(
            child=Label(
                markup=Icons.link if device.connected else Icons.link_add,
                style_classes="bluetooth-device-element-icon",
            ),
            on_clicked=lambda *_: device.connect_device(
                connect=not device.connected,
                callback=lambda *_: self.bluetooth_service.notifier(
                    "connected-devices"
                ),
            ),
        )
        connect_button.set_sensitive(not device.connecting)
        add_hover_cursor(connect_button)
        self.add(connect_button)

        self.add(
            Label(
                markup=Icons.bluetooth_paired
                if device.paired
                else Icons.bluetooth_unpaired,
                style_classes="bluetooth-device-element-icon",
            )
        )

        device_name = device.name if device.name is not None else device.address
        self.add(
            Label(
                label=device_name,
                style_classes="bluetooth-device-element-label",
                line_wrap="char",
            )
        )
